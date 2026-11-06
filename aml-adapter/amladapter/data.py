"""Download and load the two AML cohorts into AnnData with one shared obs schema.

obs columns (both cohorts)
    cohort     'vanGalen' | 'Naldini'
    sample     sequencing sample id
    patient    patient / donor id (the unit for every split and every bootstrap)
    timepoint  as given by the authors (vanGalen: D0, D14, ...; Naldini: DX, D14, D30, REL)
    stage      'dx' | 'post' | 'relapse' | 'healthy'
    malignant  1.0 / 0.0 / NaN
               vanGalen: authors' random-forest call (PredictionRefined; 'unclear' -> NaN)
               Naldini : per-cell NPM1 genotype (MUT -> 1, WT-only -> 0, ND/NoCall -> NaN)
    celltype   vanGalen: 21 annotated states (e.g. HSC-like, GMP-like, Mono, T ...); Naldini: authors' SingleR label
X holds raw UMI counts (float32 CSR); var_names are gene symbols (duplicated symbols summed).
"""
from __future__ import annotations
import gzip
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

GEO_TEXT = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={acc}&targ=all&form=text&view=brief"
VG_SKIP = {"MUTZ3", "OCI-AML3"}                     # cell lines
ND_META_URL = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE185nnn/GSE185991/suppl/GSE185991_Full_Patient_metadata.rds.gz"
ND_STAGE = {"DX": "dx", "D14": "post", "D30": "post", "REL": "relapse", "HD": "healthy"}


# -------------------------------------------------------------------------------------------- downloading
def fetch(url: str, dest: Path, tries: int = 12, verify_gzip: bool = True, pause: float = 0.5) -> bool:
    """Resumable (HTTP Range) download with backoff. Returns False on permanent 401/403/404 or exhaustion."""
    dest = Path(dest)
    if dest.exists():
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    time.sleep(pause)                                  # stay well under NCBI's request-rate limit
    buf, total = bytearray(), None
    for a in range(1, tries + 1):
        try:
            req = urllib.request.Request(url, headers={"Range": f"bytes={len(buf)}-"} if buf else {})
            with urllib.request.urlopen(req, timeout=120) as r:
                if buf and r.status != 206:
                    buf = bytearray()
                cl = r.headers.get("Content-Length")
                total = total or (int(cl) + len(buf) if cl else None)
                while True:
                    c = r.read(1 << 20)
                    if not c:
                        break
                    buf += c
            if total and len(buf) != total:
                raise IOError("short read")
            if verify_gzip and str(dest).endswith(".gz"):
                gzip.decompress(bytes(buf))
            dest.write_bytes(bytes(buf))
            return True
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 404):
                print(f"  permanent HTTP {e.code}: {dest.name}")
                return False
            time.sleep(min(60, 4 * a))
        except Exception:
            time.sleep(min(60, 4 * a))
    print(f"  gave up: {dest.name}")
    return False


def _geo_supplementary(acc: str) -> list[str]:
    with urllib.request.urlopen(GEO_TEXT.format(acc=acc), timeout=180) as r:
        text = r.read().decode()
    return [line.split("=", 1)[1].strip().replace("ftp://", "https://")
            for line in text.splitlines() if re.match(r"!Sample_supplementary_file_\d+ =", line)]


def download_vangalen(root: str | Path) -> dict:
    root = Path(root) / "vangalen"
    man_p = root / "manifest.json"
    if not man_p.exists():
        man = {}
        for url in _geo_supplementary("GSE116256"):
            m = re.match(r"GSM\d+_(.+)\.(dem|anno)\.txt\.gz$", url.rsplit("/", 1)[1])
            if m and m.group(1) not in VG_SKIP:
                man.setdefault(m.group(1), {})[m.group(2)] = url
        man = {k: v for k, v in man.items() if len(v) == 2}
        root.mkdir(parents=True, exist_ok=True)
        man_p.write_text(json.dumps(man))
    man = json.loads(man_p.read_text())
    ok = {s: d for s, d in sorted(man.items())
          if fetch(d["anno"], root / "anno" / f"{s}.anno.txt.gz") and fetch(d["dem"], root / "dem" / f"{s}.dem.txt.gz")}
    print(f"[vanGalen] {len(ok)}/{len(man)} samples available")
    return ok


def download_naldini(root: str | Path) -> dict:
    root = Path(root) / "naldini"
    man_p = root / "manifest.json"
    if not man_p.exists():
        man = {}
        for url in _geo_supplementary("GSE185991"):
            m = re.search(r"GSM\d+_(M\d+)_(barcodes\.tsv|features\.tsv|matrix\.mtx)\.gz$", url)
            if m:
                man.setdefault(m.group(1), {})[m.group(2)] = url
        man = {k: v for k, v in man.items() if len(v) == 3}
        root.mkdir(parents=True, exist_ok=True)
        man_p.write_text(json.dumps(man))
    man = json.loads(man_p.read_text())
    if not fetch(ND_META_URL, root / "Full_Patient_metadata.rds.gz"):
        raise RuntimeError("Naldini metadata (per-cell NPM1 calls) could not be downloaded")
    ok = {s: d for s, d in sorted(man.items())
          if all([fetch(u, root / "mtx" / f"{s}_{p}.gz") for p, u in d.items()])}
    print(f"[Naldini] {len(ok)}/{len(man)} samples available")
    return ok


# ---------------------------------------------------------------------------------------------- helpers
def _count_transcripts(x) -> int:
    """'NPM1.W288fs/913 /// NPM1.W288fs/393' -> 1306 ; NaN -> 0."""
    if not isinstance(x, str):
        return 0
    t = 0
    for p in x.split("///"):
        m = re.search(r"/(\d+)\s*$", p.strip())
        if m:
            t += int(m.group(1))
    return t


def _sum_duplicate_genes(X: sp.csr_matrix, symbols) -> tuple[sp.csr_matrix, np.ndarray]:
    codes, uniq = pd.factorize(pd.Index(np.asarray(symbols, dtype=str)))
    if len(uniq) == len(codes):
        return X, np.asarray(uniq, dtype=str)
    A = sp.csr_matrix((np.ones(len(codes), np.float32), (np.arange(len(codes)), codes)), shape=(len(codes), len(uniq)))
    return (X @ A).tocsr(), np.asarray(uniq, dtype=str)


def _read_10x(prefix: Path):
    bc = pd.read_csv(f"{prefix}_barcodes.tsv.gz", sep="\t", header=None)[0].astype(str).str.replace(r"-1$", "", regex=True)
    ft = pd.read_csv(f"{prefix}_features.tsv.gz", sep="\t", header=None)
    with gzip.open(f"{prefix}_matrix.mtx.gz", "rb") as fh:
        line = fh.readline()
        while line.startswith(b"%"):
            line = fh.readline()
        nr, nc, _ = map(int, line.split())
        df = pd.read_csv(fh, sep=" ", header=None, dtype=np.int32, engine="c")
    M = sp.csr_matrix((df[2].to_numpy(np.float32), (df[1].to_numpy() - 1, df[0].to_numpy() - 1)), shape=(nc, nr))
    return bc.to_numpy(), ft[1].astype(str).to_numpy(), M


# ---------------------------------------------------------------------------------------------- loaders
def load_vangalen(root: str | Path, samples=None, download: bool = True, cache: bool = True):
    import anndata as ad
    base = Path(root) / "vangalen"
    h5 = base / "counts.h5ad"
    if cache and h5.exists() and samples is None:
        return ad.read_h5ad(h5)
    avail = download_vangalen(root) if download else {p.name.split(".anno")[0]: {} for p in sorted((base / "anno").glob("*.anno.txt.gz"))}
    names = sorted(s for s in avail if (samples is None or s in samples) and s not in VG_SKIP)
    obs_l, X_l, genes = [], [], None
    for s in names:
        a = pd.read_csv(base / "anno" / f"{s}.anno.txt.gz", sep="\t", dtype=str)
        dem = pd.read_csv(base / "dem" / f"{s}.dem.txt.gz", sep="\t", index_col=0)
        if dem.index.duplicated().any():
            dem = dem.groupby(level=0).sum()
        if genes is None:
            genes = dem.index
        else:
            dem = dem.reindex(genes, fill_value=0)
        a = a.set_index("Cell").reindex(dem.columns)
        keep = a["CellType"].notna().to_numpy()
        X_l.append(sp.csr_matrix(dem.values.T[keep].astype(np.float32)))
        a = a[keep].copy()
        a["sample"] = s
        obs_l.append(a)
    X = sp.vstack(X_l, format="csr")
    obs = pd.concat(obs_l)
    obs.index = obs.index.astype(str)
    patient = obs["sample"].str.extract(r"^(AML\d+[A-Z]?|BM\d+)")[0]
    day = obs["sample"].str.extract(r"-D(\d+)$")[0].astype(float)
    healthy = patient.str.startswith("BM")
    out = pd.DataFrame(index=obs.index)
    out["cohort"] = "vanGalen"
    out["sample"] = obs["sample"].astype(str)
    out["patient"] = patient.astype(str)
    out["timepoint"] = np.where(healthy, "healthy", "D" + day.fillna(-1).astype(int).astype(str))
    out["stage"] = np.where(healthy, "healthy", np.where(day == 0, "dx", "post"))
    out["malignant"] = obs["PredictionRefined"].map({"malignant": 1.0, "normal": 0.0}).astype(float)
    out["celltype"] = obs["CellType"].astype(str)
    out["mut_reads"] = obs["MutTranscripts"].map(_count_transcripts).astype(int)
    out["wt_reads"] = obs["WtTranscripts"].map(_count_transcripts).astype(int)
    X, sym = _sum_duplicate_genes(X, genes)
    lib = np.asarray(X.sum(1)).ravel() > 0
    adata = ad.AnnData(X[lib], obs=out[lib], var=pd.DataFrame(index=sym))
    if cache and samples is None:
        h5.parent.mkdir(parents=True, exist_ok=True)
        adata.write_h5ad(h5)
    return adata


def load_naldini(root: str | Path, samples=None, download: bool = True, cache: bool = True):
    import anndata as ad
    import pyreadr
    base = Path(root) / "naldini"
    h5 = base / "counts.h5ad"
    if cache and h5.exists() and samples is None:
        return ad.read_h5ad(h5)
    if download:
        avail = set(download_naldini(root))
    else:
        avail = {p.name.split("_matrix")[0] for p in (base / "mtx").glob("*_matrix.mtx.gz")}
    rds = base / "Full_Patient_metadata.rds"
    if not rds.exists():
        rds.write_bytes(gzip.decompress((base / "Full_Patient_metadata.rds.gz").read_bytes()))
    meta = pyreadr.read_r(str(rds))[None]
    meta.index = meta.index.astype(str)
    names = sorted(avail & set(meta["orig.ident"].astype(str)))
    if samples is not None:
        names = [s for s in names if s in samples]
    blocks, genes = [], None
    for s in names:
        bc, sym, M = _read_10x(base / "mtx" / s)
        if genes is None:
            genes = sym
        elif not np.array_equal(sym, genes):
            raise ValueError(f"feature order differs in {s}")
        cells = np.array([f"{s}_{b}" for b in bc])
        keep = np.isin(cells, meta.index)
        blocks.append((cells[keep], M[keep]))
    cells = np.concatenate([b[0] for b in blocks])
    X = sp.vstack([b[1] for b in blocks], format="csr")
    m = meta.loc[cells]
    out = pd.DataFrame(index=cells)
    out["cohort"] = "Naldini"
    out["sample"] = m["orig.ident"].astype(str).to_numpy()
    out["patient"] = m["PatientID"].astype(str).to_numpy()
    out["timepoint"] = m["Timepoint"].astype(str).to_numpy()
    out["stage"] = out["timepoint"].map(ND_STAGE).to_numpy()
    out["malignant"] = m["Classification"].astype(str).map({"MUT": 1.0, "WT": 0.0}).astype(float).to_numpy()
    out["celltype"] = m["main_hpca"].astype(str).to_numpy()
    out["mut_reads"] = m["MUT"].fillna(0).astype(int).to_numpy()
    out["wt_reads"] = m["WT"].fillna(0).astype(int).to_numpy()
    X, sym = _sum_duplicate_genes(X, genes)
    lib = np.asarray(X.sum(1)).ravel() > 0
    adata = ad.AnnData(X[lib], obs=out[lib], var=pd.DataFrame(index=sym))
    if cache and samples is None:
        h5.parent.mkdir(parents=True, exist_ok=True)
        adata.write_h5ad(h5)
    return adata


def make_synthetic_cohorts(n_genes: int = 300, seed: int = 0):
    """Two small synthetic cohorts with the real obs schema (for tests and smoke runs). Cohort 2 has a depth shift."""
    import anndata as ad
    r = np.random.default_rng(seed)
    genes = np.array([f"G{i:04d}" for i in range(n_genes)])
    base = r.gamma(0.6, 1.0, n_genes)
    cts = ["HSC-like", "GMP-like", "Mono-like", "HSC", "GMP", "Mono", "T"]
    prog = {"HSC-like": slice(40, 60), "GMP-like": slice(60, 80), "Mono-like": slice(80, 100)}

    def cohort(name, patients, depth):
        rows, mats = [], []
        for p in patients:
            for tp, stage in [("D0", "dx"), ("D21", "post")]:
                for j in range(90):
                    mal = r.random() < (0.75 if stage == "dx" else 0.3)
                    ct = r.choice(cts[:3]) if mal else r.choice(cts[3:])
                    lam = base.copy() * depth
                    if mal:
                        lam[:30] *= 4
                    key = ct if ct in prog else ct + "-like"
                    if key in prog:
                        lam[prog[key]] *= 3
                    if ct == "T":
                        lam[100:120] *= 5
                    mats.append(r.poisson(lam))
                    rows.append(dict(cohort=name, sample=f"{p}-{tp}", patient=p, timepoint=tp, stage=stage,
                                     malignant=float(mal) if r.random() > 0.1 else np.nan, celltype=ct, mut_reads=0, wt_reads=0))
        obs = pd.DataFrame(rows)
        obs.index = [f"{name}_{i}" for i in range(len(obs))]
        return ad.AnnData(sp.csr_matrix(np.array(mats, np.float32)), obs=obs, var=pd.DataFrame(index=genes))

    return cohort("vanGalen", [f"AML{i}" for i in range(1, 9)], 1.0), cohort("Naldini", [f"PT{i:02d}" for i in range(1, 5)], 2.5)
