#!/usr/bin/env python
"""Headroom test: how much does information IPSS-M ignores (full karyotype, hotspots, clonal structure, WHO, RS%) add?
Exploratory (NOT pre-registered). 5-fold CV, same folds for every model."""
import sys, copy, time
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sklearn.model_selection import StratifiedKFold
from mdsrisk.data import fetch, outcomes, ENDPOINTS
from mdsrisk.features import build
from mdsrisk.features_ext import build_ext
from mdsrisk.models import XGBCox, CoxNet, cindex
from mdsrisk.competing import auc_cr
from mdsrisk.tfm_adapter import cr_outcome

data = sys.argv[1]; out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
clin, mut = fetch(data); d = outcomes(clin).set_index("patientId")
X, g = build(d, mut); E = build_ext(d, mut)
F = X.join(E).join(d[["IPSSM_SCORE", "IPSSR_SCORE"]])
base, ext = g["all"], g["all"] + list(E.columns)
elig = (d.IPSSM_SCORE.notna() & d.IPSSM.notna() & d.LFS_MONTHS.notna() & d.OS_MONTHS.notna()).to_numpy()
d, F = d[elig], F[elig]
t_cr, cause = cr_outcome(d)
lower = d.IPSSM.isin(["Very-Low", "Low", "Moderate-Low"]).to_numpy()
folds = list(StratifiedKFold(5, shuffle=True, random_state=0).split(np.zeros(len(d)), cause))
specs = {
    "IPSS-M+ (102 features)": lambda: XGBCox("a", base, offset_col="IPSSM_SCORE", eta=0.02),
    "IPSS-M+ (+65 new features)": lambda: XGBCox("b", ext, offset_col="IPSSM_SCORE", eta=0.02),
    "XGBoost scratch (+new)": lambda: XGBCox("c", ext),
    "CoxNet (+new)": lambda: CoxNet("d", ext),
}
ep = {"LFS": (d.LFS_MONTHS.to_numpy(float), d.lfs_event.to_numpy(float)),
      "OS": (d.OS_MONTHS.to_numpy(float), d.os_event.to_numpy(float)),
      "AMLt (cause-specific)": (t_cr, (cause == 1).astype(float)),
      "death w/o AML (cause-specific)": (t_cr, (cause == 2).astype(float))}
oof = {(e, m): np.zeros(len(d)) for e in ep for m in specs}
t0 = time.time()
for k, (tr, te) in enumerate(folds):
    for e, (t, ev) in ep.items():
        for m, mk in specs.items():
            oof[(e, m)][te] = mk().fit(F.iloc[tr], t[tr], ev[tr], seed=k).risk(F.iloc[te])
    print(f"fold {k} ({(time.time()-t0)/60:.1f} min)", flush=True)
def rank(x): return pd.Series(x).rank().to_numpy() / len(x)
rows = []
for e, (t, ev) in ep.items():
    ens = np.mean([rank(oof[(e, m)]) for m in specs], axis=0)
    risks = {"IPSS-M": d.IPSSM_SCORE.to_numpy(float), **{m: oof[(e, m)] for m in specs}, "Ensemble (rank mean)": ens}
    for m, r in risks.items():
        row = dict(endpoint=e, model=m, C=cindex(t, ev, r))
        if e.startswith("AMLt"):
            row["AUC_AML_5y_all"] = auc_cr(t_cr, cause, r, 60.0, 1)
            row["AUC_AML_5y_lowerrisk"] = auc_cr(t_cr[lower], cause[lower], r[lower], 60.0, 1)
        if e.startswith("death"):
            row["AUC_death_5y_all"] = auc_cr(t_cr, cause, r, 60.0, 2)
        rows.append(row)
R = pd.DataFrame(rows); R.to_csv(out / "headroom.csv", index=False)
print(R.round(3).to_string(index=False))
