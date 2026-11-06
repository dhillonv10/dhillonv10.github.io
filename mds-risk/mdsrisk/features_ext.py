"""Information IPSS-M does not use: parsed karyotype (ISCN), mutation hotspots, clonal architecture, WHO subtype, ring sideroblasts."""
from __future__ import annotations
import re
import numpy as np
import pandas as pd

SECONDARY_TYPE = ["SRSF2", "SF3B1", "U2AF1", "ZRSR2", "ASXL1", "EZH2", "BCOR", "STAG2"]     # Lindsley et al. 2015
RAS_PATHWAY = ["NRAS", "KRAS", "CBL", "PTPN11", "NF1", "BRAF", "RIT1"]
TF_GENES = ["RUNX1", "ETV6", "GATA2", "CEBPA", "WT1", "PHF6", "IKZF1"]
DOMINANT = ["SF3B1", "TET2", "ASXL1", "DNMT3A", "SRSF2", "TP53", "RUNX1", "U2AF1", "ZRSR2", "STAG2", "EZH2", "IDH2"]
WHO = ["MDS-SLD", "MDS-MLD", "MDS-RS-SLD", "MDS-RS-MLD", "MDS-del5q", "MDS-EB1", "MDS-EB2", "MDS-U", "CMML", "MDS/MPN-RS-T",
       "MDS/MPN-U", "aCML", "AML"]
TRUNCATING = {"Nonsense_Mutation", "Frame_Shift_Del", "Frame_Shift_Ins", "Splice_Site"}


def parse_karyotype(s: str) -> dict:
    """ISCN string -> abnormality counts and specific lesions. Returns NaNs for missing/uninterpretable karyotypes."""
    keys = ["n_abn", "n_clones_abn", "n_monosomy", "n_structural", "monosomal_karyotype", "abn_minus7_7q", "abn_5q", "abn_3q26",
            "abn_17p_i17q", "abn_plus8", "abn_20q", "abn_minusY", "abn_11q23", "abn_plus19", "abn_plus21", "abn_marker",
            "abn_hypodiploid", "karyo_normal"]
    out = dict.fromkeys(keys, np.nan)
    if not isinstance(s, str) or not s.strip():
        return out
    s = s.lower().replace(" ", "")
    clones = [c for c in s.split("/") if c]
    abn = set()
    abn_clones = 0
    modal = []
    for c in clones:
        c = re.sub(r"\[\d+\]$", "", c)
        toks = [t for t in re.split(r",(?![^()]*\))", c) if t]
        if toks and re.match(r"^\d{2}(~\d{2})?$", toks[0]):
            modal.append(int(toks[0][:2])); toks = toks[1:]
        toks = [t for t in toks if t not in ("xx", "xy", "x", "y", "idem", "sl", "sdl1", "sdl2") and not t.startswith("idem")]
        toks = [t for t in toks if not re.match(r"^(xx|xy)$", t)]
        if toks:
            abn_clones += 1
            abn.update(toks)
    out = {k: 0.0 for k in keys}
    out["n_abn"] = float(len(abn)); out["n_clones_abn"] = float(abn_clones)
    mono = [t for t in abn if re.match(r"^-(\d{1,2})(c)?$", t)]
    struct = [t for t in abn if re.match(r"^(del|t|inv|i|der|dup|add|ins|r|idic|dic|ider)\(", t)]
    out["n_monosomy"], out["n_structural"] = float(len(mono)), float(len(struct))
    out["monosomal_karyotype"] = float(len(mono) >= 2 or (len(mono) >= 1 and len(struct) >= 1))
    j = " ".join(abn)
    out["abn_minus7_7q"] = float(bool(re.search(r"(^|\s)-7(\s|$)|del\(7\)|i\(7\)\(p10\)", j)))
    out["abn_5q"] = float(bool(re.search(r"(^|\s)-5(\s|$)|del\(5\)", j)))
    out["abn_3q26"] = float(bool(re.search(r"inv\(3\)\(q21q26|t\(3;3\)|t\(3;\d+\)\(q26|t\(\d+;3\)\(\w+;q26", j)))
    out["abn_17p_i17q"] = float(bool(re.search(r"i\(17\)\(q10\)|del\(17\)\(p|(^|\s)-17(\s|$)", j)))
    out["abn_plus8"] = float(bool(re.search(r"(^|\s)\+8(\s|$)", j)))
    out["abn_20q"] = float(bool(re.search(r"del\(20\)\(q", j)))
    out["abn_minusY"] = float(bool(re.search(r"(^|\s)-y(\s|$)", j)))
    out["abn_11q23"] = float(bool(re.search(r"11\)\(\w*q23|\(11;\w+\)\(q23|;11\)\(\w+;q23", j)))
    out["abn_plus19"] = float(bool(re.search(r"(^|\s)\+19(\s|$)", j)))
    out["abn_plus21"] = float(bool(re.search(r"(^|\s)\+21(\s|$)", j)))
    out["abn_marker"] = float(bool(re.search(r"mar", j)))
    out["abn_hypodiploid"] = float(bool(modal) and min(modal) < 46)
    out["karyo_normal"] = float(len(abn) == 0)
    return out


def _hot(protein, gene, pattern):
    return gene + "_" + pattern


def build_ext(d: pd.DataFrame, mut: pd.DataFrame) -> pd.DataFrame:
    E = pd.DataFrame([parse_karyotype(s) for s in d.CYTOGENETICS], index=d.index)
    E["ring_sideroblasts"] = pd.to_numeric(d.RINGED_SIDEROBLASTS, errors="coerce")
    for w in WHO:
        E[f"who_{w}"] = np.where(d.WHO_2016.isna(), np.nan, (d.WHO_2016 == w).astype(float))
    sample_of = dict(zip(d.sampleId, d.index))
    m = mut[mut.driver & mut.sampleId.isin(sample_of)].copy()
    m["row"] = m.sampleId.map(sample_of)
    p = m.protein.fillna("").astype(str)
    hot = {
        "SF3B1_K700E": (m.gene == "SF3B1") & p.str.startswith("K700"),
        "SF3B1_nonK700E": (m.gene == "SF3B1") & ~p.str.startswith("K700"),
        "U2AF1_S34": (m.gene == "U2AF1") & p.str.startswith("S34"),
        "U2AF1_Q157": (m.gene == "U2AF1") & p.str.startswith("Q157"),
        "SRSF2_P95": (m.gene == "SRSF2") & p.str.startswith("P95"),
        "IDH1_R132": (m.gene == "IDH1") & p.str.startswith("R132"),
        "IDH2_R140": (m.gene == "IDH2") & p.str.startswith("R140"),
        "IDH2_R172": (m.gene == "IDH2") & p.str.startswith("R172"),
        "RAS_G12_G13": m.gene.isin(["NRAS", "KRAS"]) & p.str.match(r"^G1[23]"),
        "RAS_Q61": m.gene.isin(["NRAS", "KRAS"]) & p.str.startswith("Q61"),
        "DNMT3A_R882": (m.gene == "DNMT3A") & p.str.startswith("R882"),
        "TP53_truncating": (m.gene == "TP53") & m.type.isin(TRUNCATING),
        "TP53_missense": (m.gene == "TP53") & (m.type == "Missense_Mutation"),
        "ASXL1_truncating": (m.gene == "ASXL1") & m.type.isin(TRUNCATING),
        "RUNX1_truncating": (m.gene == "RUNX1") & m.type.isin(TRUNCATING),
        "EZH2_truncating": (m.gene == "EZH2") & m.type.isin(TRUNCATING),
    }
    for k, msk in hot.items():
        E[f"hot_{k}"] = m[msk].groupby("row").size().reindex(d.index).fillna(0).clip(upper=1)
    for name, genes in (("n_secondary_type", SECONDARY_TYPE), ("n_ras_pathway", RAS_PATHWAY), ("n_tf_genes", TF_GENES)):
        E[name] = m[m.gene.isin(genes)].groupby("row").gene.nunique().reindex(d.index).fillna(0)
    top = m.sort_values("vaf", ascending=False).drop_duplicates("row").set_index("row")
    dom = top.gene.reindex(d.index)
    for g in DOMINANT:
        E[f"dominant_{g}"] = (dom == g).astype(float)
    E["dominant_vaf"] = top.vaf.reindex(d.index).fillna(0)
    second = m.sort_values("vaf", ascending=False).groupby("row").vaf.apply(lambda v: v.iloc[1] if len(v) > 1 else 0.0)
    E["subclone_vaf_gap"] = E["dominant_vaf"] - second.reindex(d.index).fillna(0)
    sequenced = d.MUTATION_COUNT.notna() | d.sampleId.isin(mut.sampleId)
    mcols = [c for c in E if c.startswith(("hot_", "dominant_", "n_secondary", "n_ras", "n_tf", "subclone"))]
    E.loc[~sequenced.to_numpy(), mcols] = np.nan
    return E.astype(float)
