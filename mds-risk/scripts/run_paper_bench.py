#!/usr/bin/env python
"""Run the pre-registered benchmark (paper/PROTOCOL.md). Resumable: every (model, fold) result is cached.

    python scripts/run_paper_bench.py --data data --out paper/results --tabpfn-ckpt <path to tabpfn-v2-regressor-v2_default.ckpt>
"""
import argparse, json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sklearn.model_selection import StratifiedKFold
from mdsrisk.data import fetch, outcomes
from mdsrisk.features import build, curated
from mdsrisk.competing import auc_cr, brier_cr, cif_by_group
from mdsrisk.models import XGBCox
from mdsrisk.tfm_adapter import MDSAdapter, TabICLBackbone, TabPFNBackbone, XGBBackbone, cr_outcome

TAUS = (24.0, 60.0)
CAUSES = (1, 2)
LOWER = ("Very-Low", "Low", "Moderate-Low")
FRACTIONS = (0.10, 0.25, 0.50)
N_DRAWS = 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data"); ap.add_argument("--out", default="paper/results")
    ap.add_argument("--tabpfn-ckpt", required=True); ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--skip", nargs="*", default=[], help="model ids to skip (reported as protocol deviations)")
    a = ap.parse_args()
    out = Path(a.out); cache = out / "cache"; cache.mkdir(parents=True, exist_ok=True)
    clin, mut = fetch(a.data)
    d = outcomes(clin).set_index("patientId")
    X, groups = build(d, mut)
    C = curated(d, mut, X)
    full = X.join(d[["IPSSM_SCORE"]])
    elig = (d.IPSSM_SCORE.notna() & d.IPSSM.notna() & d.LFS_MONTHS.notna()).to_numpy()
    d, C, full = d[elig], C[elig], full[elig]
    t, cause = cr_outcome(d)
    cat_m = d.IPSSM.astype(str).to_numpy()
    cat_r = d.IPSSR.fillna("missing").astype(str).to_numpy()
    ipssr_score = d.IPSSR_SCORE.fillna(d.IPSSR_SCORE.median()).to_numpy(float)
    print(f"eligible n={len(t)}  AML={int((cause==1).sum())}  death={int((cause==2).sum())}  censored={int((cause==0).sum())}"
          f"  (IPSS-R missing: {int(d.IPSSR_SCORE.isna().sum())}, set to median for M1)", flush=True)
    folds = list(StratifiedKFold(5, shuffle=True, random_state=0).split(np.zeros(len(t)), cause))
    ck = a.tabpfn_ckpt
    curated_cols, full_cols = list(C.columns), list(full.columns)
    full_F = full.copy()
    specs = {
        "M3": ("TabPFN + MDS adapter", lambda: MDSAdapter(TabPFNBackbone(ck), curated_cols, anchor=True), "C"),
        "M4": ("XGBoost + MDS adapter", lambda: MDSAdapter(XGBBackbone(), curated_cols, anchor=True), "C"),
        "M5": ("TabPFN + adapter, no IPSS-M anchor", lambda: MDSAdapter(TabPFNBackbone(ck), curated_cols, anchor=False), "C"),
        "M6": ("TabPFN + adapter, full 102 features", lambda: MDSAdapter(TabPFNBackbone(ck), full_cols, anchor=True), "F"),
        "M7": ("TabPFN + adapter, all-cause target", lambda: MDSAdapter(TabPFNBackbone(ck), curated_cols, anchor=True, all_cause=True), "C"),
        "M8": ("TabICL + MDS adapter", lambda: MDSAdapter(TabICLBackbone(), curated_cols, anchor=True), "C"),
    }
    names = {"M0": "IPSS-M", "M1": "IPSS-R", "M2": "IPSS-M+ XGBoost (cause-specific Cox)", **{k: v[0] for k, v in specs.items()}}
    # out-of-fold containers: risk[(model, cause, tau)] and cif[(model, cause, tau)]
    risk, cif = {}, {}
    def put(store, key, idx, vals):
        store.setdefault(key, np.full(len(t), np.nan))[idx] = vals
    t0 = time.time()
    for k, (tr, te) in enumerate(folds):
        # M0 / M1: published scores for ranking, category Aalen-Johansen for CIF
        bm = cif_by_group(t[tr], cause[tr], cat_m[tr], cat_m[te], TAUS, CAUSES)
        br = cif_by_group(t[tr], cause[tr], cat_r[tr], cat_r[te], TAUS, CAUSES)
        for i, c_ in enumerate(CAUSES):
            for j, tau in enumerate(TAUS):
                put(risk, ("M0", c_, tau), te, d.IPSSM_SCORE.to_numpy(float)[te]); put(cif, ("M0", c_, tau), te, bm[:, i, j])
                put(risk, ("M1", c_, tau), te, ipssr_score[te]); put(cif, ("M1", c_, tau), te, br[:, i, j])
        # M2: cause-specific gradient-boosted Cox from the IPSS-M offset (ranking only)
        f = cache / f"M2_fold{k}.npz"
        if not f.exists():
            r_ = {}
            for c_ in CAUSES:
                m = XGBCox("M2", groups["all"], offset_col="IPSSM_SCORE", eta=0.02).fit(full_F.iloc[tr], t[tr], (cause[tr] == c_).astype(float), seed=k)
                r_[f"c{c_}"] = m.risk(full_F.iloc[te])
            np.savez(f, **r_)
        z = np.load(f)
        for c_ in CAUSES:
            for tau in TAUS:
                put(risk, ("M2", c_, tau), te, z[f"c{c_}"])
        # adapter models
        for mid, (_, make, fs) in specs.items():
            if mid in a.skip:
                continue
            f = cache / f"{mid}_fold{k}.npz"
            if not f.exists():
                tt = time.time()
                F = C if fs == "C" else full_F
                pred = make().fit_predict(F.iloc[tr], t[tr], cause[tr], cat_m[tr], F.iloc[te], cat_m[te])
                np.savez(f, **{f"c{c_}_t{int(tau)}": v for (c_, tau), v in pred.items()})
                print(f"  fold {k} {mid} done in {(time.time()-tt)/60:.1f} min (elapsed {(time.time()-t0)/60:.0f} min)", flush=True)
            z = np.load(f)
            for c_ in CAUSES:
                for tau in TAUS:
                    v = z[f"c{c_}_t{int(tau)}"]
                    put(risk, (mid, c_, tau), te, v)
                    if mid != "M7":
                        put(cif, (mid, c_, tau), te, v)
        # B4: data efficiency, AML at 60 months, M3 and M4 on subsamples of the training fold
        for mid in ("M3", "M4"):
            if mid in a.skip:
                continue
            for frac in FRACTIONS:
                for r in range(N_DRAWS):
                    f = cache / f"B4_{mid}_f{int(frac*100)}_d{r}_fold{k}.npz"
                    if not f.exists():
                        rng = np.random.default_rng(1000 * r + k)
                        sub = np.concatenate([rng.choice(tr[cause[tr] == c_], size=max(2, int(round(frac * (cause[tr] == c_).sum()))), replace=False)
                                              for c_ in (0, 1, 2)])
                        ad = specs[mid][1]()
                        ad.taus, ad.causes = (60.0,), (1, 2)
                        pred = ad.fit_predict(C.iloc[sub], t[sub], cause[sub], cat_m[sub], C.iloc[te], cat_m[te])
                        np.savez(f, aml60=pred[(1, 60.0)])
                    put(risk, (f"B4_{mid}_{int(frac*100)}_d{r}", 1, 60.0), te, np.load(f)["aml60"])
        print(f"[fold {k}] complete ({(time.time()-t0)/60:.0f} min)", flush=True)
    evaluate(risk, cif, names, t, cause, cat_m, out, a.boot, a.skip)
    print(f"[done] {(time.time()-t0)/60:.1f} min", flush=True)


def _boot_auc(t, cause, risks, tau, k, ref, n_boot, seed=0):
    rng = np.random.default_rng(seed)
    n = len(t)
    idx = [rng.integers(0, n, n) for _ in range(n_boot)]
    rows = []
    ref_b = np.array([auc_cr(t[i], cause[i], risks[ref][i], tau, k) for i in idx])
    for m, r in risks.items():
        b = ref_b if m == ref else np.array([auc_cr(t[i], cause[i], r[i], tau, k) for i in idx])
        est = auc_cr(t, cause, r, tau, k)
        d_ = b - ref_b
        rows.append(dict(model=m, auc=est, lo=np.nanpercentile(b, 2.5), hi=np.nanpercentile(b, 97.5),
                         d_vs_ref=est - auc_cr(t, cause, risks[ref], tau, k), d_lo=np.nanpercentile(d_, 2.5), d_hi=np.nanpercentile(d_, 97.5)))
    return pd.DataFrame(rows)


def evaluate(risk, cif, names, t, cause, cat_m, out, n_boot, skip):
    ids = ["M0", "M1", "M2"] + [m for m in ("M3", "M4", "M5", "M6", "M7", "M8") if m not in skip]
    tables = {}
    lower = np.isin(cat_m, LOWER)
    for bench, k, mask in (("B1_AML", 1, np.ones(len(t), bool)), ("B2_AML_lower_risk", 1, lower), ("B3_death", 2, np.ones(len(t), bool))):
        for tau in TAUS:
            rs = {m: risk[(m, k, tau)][mask] for m in ids}
            tab = _boot_auc(t[mask], cause[mask], rs, tau, k, "M0", n_boot)
            tab.insert(1, "name", tab.model.map(names))
            tab["n"], tab["cases"] = int(mask.sum()), int(((t[mask] <= tau) & (cause[mask] == k)).sum())
            tables[f"{bench}_{int(tau)}m"] = tab
    rows = []
    for m in ids:
        for k in CAUSES:
            for tau in TAUS:
                if (m, k, tau) in cif:
                    rows.append(dict(model=m, name=names[m], cause="AML" if k == 1 else "death", tau=tau,
                                     brier=brier_cr(t, cause, cif[(m, k, tau)], tau, k),
                                     mean_pred=float(np.nanmean(cif[(m, k, tau)]))))
    tables["calibration_brier"] = pd.DataFrame(rows)
    b4 = []
    for mid in ("M3", "M4"):
        if mid in skip:
            continue
        for frac in FRACTIONS:
            aucs = [auc_cr(t, cause, risk[(f"B4_{mid}_{int(frac*100)}_d{r}", 1, 60.0)], 60.0, 1) for r in range(N_DRAWS)]
            b4.append(dict(model=mid, name=names[mid], fraction=frac, auc_mean=np.mean(aucs), auc_sd=np.std(aucs)))
        b4.append(dict(model=mid, name=names[mid], fraction=1.0, auc_mean=auc_cr(t, cause, risk[(mid, 1, 60.0)], 60.0, 1), auc_sd=0.0))
    b4.append(dict(model="M0", name="IPSS-M (no training)", fraction=np.nan, auc_mean=auc_cr(t, cause, risk[("M0", 1, 60.0)], 60.0, 1), auc_sd=0.0))
    tables["B4_data_efficiency"] = pd.DataFrame(b4)
    # protocol H3/H4: paired differences of the primary model M3 against the backbone and adapter ablations
    rows = []
    for task, k, tau, mask in (("AML 60m, all", 1, 60.0, np.ones(len(t), bool)), ("AML 24m, all", 1, 24.0, np.ones(len(t), bool)),
                               ("AML 60m, lower-risk", 1, 60.0, lower), ("death 60m, all", 2, 60.0, np.ones(len(t), bool))):
        rs = {m: risk[(m, k, tau)][mask] for m in ids}
        tab = _boot_auc(t[mask], cause[mask], rs, tau, k, "M3", n_boot, seed=1)
        for _, r in tab[tab.model != "M3"].iterrows():
            rows.append(dict(task=task, comparison=f"M3 minus {r.model} ({names[r.model]})", diff=-r.d_vs_ref, lo=-r.d_hi, hi=-r.d_lo))
    tables["H3_H4_paired_vs_M3"] = pd.DataFrame(rows)
    # B4 with paired bootstrap: TabPFN minus XGBoost at each training fraction (draws averaged)
    rows = []
    if "M3" not in skip and "M4" not in skip:
        rng = np.random.default_rng(2)
        idx = [rng.integers(0, len(t), len(t)) for _ in range(n_boot)]
        for frac in FRACTIONS + (1.0,):
            def keys(mid):
                return [(mid, 1, 60.0)] if frac == 1.0 else [(f"B4_{mid}_{int(frac*100)}_d{r}", 1, 60.0) for r in range(N_DRAWS)]
            f = lambda mid, ii: np.mean([auc_cr(t[ii], cause[ii], risk[kk][ii], 60.0, 1) for kk in keys(mid)])
            all_i = np.arange(len(t))
            d0 = f("M3", all_i) - f("M4", all_i)
            db = np.array([f("M3", ii) - f("M4", ii) for ii in idx[:200]])
            dm = np.array([f("M3", ii) - auc_cr(t[ii], cause[ii], risk[("M0", 1, 60.0)][ii], 60.0, 1) for ii in idx[:200]])
            rows.append(dict(fraction=frac, tabpfn_minus_xgb=d0, lo=np.percentile(db, 2.5), hi=np.percentile(db, 97.5),
                             tabpfn_minus_ipssm=f("M3", all_i) - auc_cr(t, cause, risk[("M0", 1, 60.0)], 60.0, 1),
                             lo_ipssm=np.percentile(dm, 2.5), hi_ipssm=np.percentile(dm, 97.5)))
    tables["B4_paired"] = pd.DataFrame(rows)
    np.savez_compressed(out / "oof_risks.npz", **{"|".join(map(str, k_)): v for k_, v in risk.items()},
                        **{"cif|" + "|".join(map(str, k_)): v for k_, v in cif.items()}, t=t, cause=cause, cat_m=cat_m)
    for k_, v in tables.items():
        v.to_csv(out / f"{k_}.csv", index=False)
    lines = ["# Benchmark results (protocol: paper/PROTOCOL.md)", ""]
    for k_, v in tables.items():
        lines += [f"## {k_}", "", v.round(3).to_markdown(index=False), ""]
    (out / "RESULTS.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
