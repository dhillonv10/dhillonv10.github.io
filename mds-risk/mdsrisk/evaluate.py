"""Cross-validation, metrics, paired bootstrap against IPSS-M, reclassification analysis, explanations."""
from __future__ import annotations
import copy
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

from .models import cindex

TIME_GRID = np.arange(6, 61, 3, dtype=float)      # months, for calibrated survival / integrated Brier score
AUC_TIMES = (12.0, 36.0, 60.0)
IPSSM_CATS = ["Very-Low", "Low", "Moderate-Low", "Moderate-High", "High", "Very-High"]


def _surv(t, e):
    from sksurv.util import Surv
    return Surv.from_arrays(np.asarray(e).astype(bool), np.asarray(t, float))


def calibrated_survival(train_risk, t, e, test_risk, times=TIME_GRID):
    """S(t | risk) from a one-covariate Cox model fitted on INNER out-of-fold training risks (no optimism)."""
    from lifelines import CoxPHFitter
    mu, sd = np.mean(train_risk), np.std(train_risk) or 1.0
    df = pd.DataFrame(dict(r=(train_risk - mu) / sd, T=t, E=e))
    m = CoxPHFitter(penalizer=1e-4).fit(df, "T", "E")
    sf = m.predict_survival_function(pd.DataFrame(dict(r=(np.asarray(test_risk) - mu) / sd)), times=times)
    return sf.to_numpy().T                              # (n_test, n_times)


def cross_validate(F, t, e, models, n_splits=5, repeats=3, seed=0, log=print):
    """Outer repeated stratified K-fold. Returns {repeat: {model: (risk, surv)}} with out-of-fold predictions."""
    out = {}
    for r in range(repeats):
        skf = StratifiedKFold(n_splits, shuffle=True, random_state=seed + r)
        res = {m.name: [np.zeros(len(t)), np.zeros((len(t), len(TIME_GRID)))] for m in models}
        for k, (a, b) in enumerate(skf.split(np.zeros(len(e)), e.astype(int))):
            for m0 in models:
                m = copy.deepcopy(m0).fit(F.iloc[a], t[a], e[a], seed=seed + 97 * r + k)
                risk = m.risk(F.iloc[b])
                res[m.name][0][b] = risk
                res[m.name][1][b] = calibrated_survival(m.oof_, t[a], e[a], risk)
            log(f"    repeat {r} fold {k} done")
        out[r] = {k_: tuple(v) for k_, v in res.items()}
    return out


def metrics(t, e, risk, surv, t_all, e_all):
    from sksurv.metrics import concordance_index_ipcw, cumulative_dynamic_auc, integrated_brier_score
    y_all, y = _surv(t_all, e_all), _surv(t, e)
    out = dict(harrell_c=cindex(t, e, risk))
    out["uno_c_5y"] = float(concordance_index_ipcw(y_all, y, risk, tau=60.0)[0])
    auc, _ = cumulative_dynamic_auc(y_all, y, risk, np.array(AUC_TIMES))
    for tt, a in zip(AUC_TIMES, auc):
        out[f"auc_{int(tt)}m"] = float(a)
    out["ibs_6_60m"] = float(integrated_brier_score(y_all, y, surv, TIME_GRID))
    return out


def summarize(cv, t, e):
    rows = []
    for r, res in cv.items():
        for name, (risk, surv) in res.items():
            rows.append(dict(repeat=r, model=name, **metrics(t, e, risk, surv, t, e)))
    df = pd.DataFrame(rows)
    mean = df.drop(columns="repeat").groupby("model", sort=False).mean()
    sd = df.drop(columns="repeat").groupby("model", sort=False).std()
    return mean, sd, df


def paired_bootstrap(t, e, risks: dict, refs=("IPSS-M",), n_boot=1000, seed=0):
    """Harrell's C with 95% CI, and paired differences vs reference models, resampling patients."""
    rng = np.random.default_rng(seed)
    n = len(t)
    idx = rng.integers(0, n, size=(n_boot, n))
    boot = {m: np.array([cindex(t[i], e[i], r[i]) for i in idx]) for m, r in risks.items()}
    rows = []
    for m, r in risks.items():
        row = dict(model=m, c=cindex(t, e, r), c_lo=np.percentile(boot[m], 2.5), c_hi=np.percentile(boot[m], 97.5))
        for ref in refs:
            if ref in boot:
                d = boot[m] - boot[ref]
                row[f"dC_vs_{ref}"] = row["c"] - cindex(t, e, risks[ref])
                row[f"dC_lo_vs_{ref}"], row[f"dC_hi_vs_{ref}"] = np.percentile(d, 2.5), np.percentile(d, 97.5)
        rows.append(row)
    return pd.DataFrame(rows)


def match_categories(score, reference_cats, order=IPSSM_CATS):
    """Cut a continuous score into categories with the SAME sizes as the reference categories."""
    ref = pd.Categorical(reference_cats, categories=order, ordered=True)
    props = pd.Series(ref).value_counts(normalize=True).reindex(order).fillna(0).to_numpy()
    cuts = np.quantile(score, np.cumsum(props)[:-1])
    return pd.Categorical(np.array(order)[np.searchsorted(cuts, score, side="right")], categories=order, ordered=True), cuts


def reclassification(t, e, ipssm_cat, ipssm_score, new_score):
    """Does the new model's re-sorting WITHIN IPSS-M categories carry outcome information?"""
    from lifelines import CoxPHFitter, KaplanMeierFitter
    new_cat, cuts = match_categories(new_score, ipssm_cat)
    old = pd.Categorical(ipssm_cat, categories=IPSSM_CATS, ordered=True)
    shift = new_cat.codes - old.codes
    direction = np.where(shift > 0, "up", np.where(shift < 0, "down", "same"))
    xtab = pd.crosstab(pd.Series(old, name="IPSS-M"), pd.Series(new_cat, name="new model"))
    df = pd.DataFrame(dict(T=t, E=e, cat=old.astype(str), up=(direction == "up").astype(float), down=(direction == "down").astype(float)))
    strat = CoxPHFitter().fit(df[["T", "E", "cat", "up", "down"]], "T", "E", strata=["cat"])
    hr = strat.summary[["exp(coef)", "exp(coef) lower 95%", "exp(coef) upper 95%", "p"]].rename(index={"up": "moved up vs same", "down": "moved down vs same"})
    z = lambda x: (x - np.mean(x)) / np.std(x)
    both = CoxPHFitter().fit(pd.DataFrame(dict(T=t, E=e, ipssm=z(ipssm_score), new=z(new_score))), "T", "E")
    joint = both.summary[["exp(coef)", "exp(coef) lower 95%", "exp(coef) upper 95%", "p"]]
    km_rows = []
    for c in IPSSM_CATS:
        for d in ("down", "same", "up"):
            m = (old == c) & (direction == d)
            if m.sum() < 10:
                continue
            k = KaplanMeierFitter().fit(t[m], e[m])
            km_rows.append(dict(ipssm=c, direction=d, n=int(m.sum()), events=int(e[m].sum()),
                                lfs_3y=float(k.predict(36.0)), lfs_5y=float(k.predict(60.0))))
    return dict(xtab=xtab, hr=hr, joint=joint, km=pd.DataFrame(km_rows), new_cat=new_cat, direction=direction,
                n_reclassified=int((direction != "same").sum()), cuts=cuts)
