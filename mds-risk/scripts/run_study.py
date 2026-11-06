#!/usr/bin/env python
"""Run the full study: can models trained on the IPSS-M cohort beat IPSS-M, and when they disagree, who is right?

    python scripts/run_study.py --data data --out results            # ~15-20 min on 4 CPU cores
"""
import argparse, json, pickle, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mdsrisk.data import ENDPOINTS, fetch, outcomes
from mdsrisk.evaluate import cross_validate, paired_bootstrap, reclassification, summarize, IPSSM_CATS, match_categories
from mdsrisk.features import build
from mdsrisk.models import XGBCox, model_zoo

PRIMARY = {"LFS": "IPSS-M+ (no age)", "AMLt": "IPSS-M+ (no age)", "OS": "IPSS-M+ (with age)"}
FINAL_REF = {"LFS": "IPSS-M", "AMLt": "IPSS-M", "OS": "IPSS-M + age"}   # the fair comparator for each primary model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data"); ap.add_argument("--out", default="results")
    ap.add_argument("--repeats", type=int, default=3); ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--boot", type=int, default=1000); ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    out = Path(a.out); (out / "figures").mkdir(parents=True, exist_ok=True); (out / "models").mkdir(exist_ok=True)
    t_start = time.time()
    clin, mut = fetch(a.data)
    d = outcomes(clin).set_index("patientId")
    X, groups = build(d, mut)
    F = X.join(d[["IPSSM_SCORE", "IPSSR_SCORE"]])
    json.dump(groups, open(out / "feature_groups.json", "w"), indent=1)
    summary, recl = {}, {}
    for ep, (tc, ec) in ENDPOINTS.items():
        keep = (d.IPSSM_SCORE.notna() & d.IPSSR_SCORE.notna() & d[tc].notna()).to_numpy()
        Fe, t, e = F[keep], d[tc].to_numpy(float)[keep], d[ec].to_numpy(float)[keep]
        print(f"[{ep}] n={len(t)} events={int(e.sum())}", flush=True)
        cv = cross_validate(Fe, t, e, model_zoo(groups), n_splits=a.folds, repeats=a.repeats, seed=a.seed, log=lambda *x: None)
        mean, sd, per = summarize(cv, t, e)
        per.to_csv(out / f"{ep}_metrics_per_repeat.csv", index=False)
        boot = paired_bootstrap(t, e, {m: v[0] for m, v in cv[0].items()}, refs=("IPSS-M", "IPSS-M + age"), n_boot=a.boot, seed=a.seed)
        tab = mean.join(sd[["harrell_c"]].rename(columns={"harrell_c": "harrell_c_sd_repeats"})).reset_index().merge(boot, on="model")
        tab.to_csv(out / f"{ep}_results.csv", index=False)
        summary[ep] = dict(n=int(len(t)), events=int(e.sum()), table=tab)
        print(tab[["model", "harrell_c", "uno_c_5y", "ibs_6_60m", "dC_vs_IPSS-M", "dC_lo_vs_IPSS-M", "dC_hi_vs_IPSS-M"]].round(3).to_string(index=False), flush=True)
        oof = pd.DataFrame({m: v[0] for m, v in cv[0].items()}, index=Fe.index)
        oof.to_csv(out / f"{ep}_oof_risk_repeat0.csv")
        r = reclassification(t, e, d.loc[keep, "IPSSM"].to_numpy(), Fe.IPSSM_SCORE.to_numpy(), oof[PRIMARY[ep]].to_numpy())
        recl[ep] = r
        r["xtab"].to_csv(out / f"{ep}_reclassification_crosstab.csv"); r["hr"].to_csv(out / f"{ep}_reclassification_hr.csv")
        r["joint"].to_csv(out / f"{ep}_joint_cox.csv"); r["km"].to_csv(out / f"{ep}_reclassification_km.csv", index=False)
        print(f"  reclassified {r['n_reclassified']}/{len(t)}; HRs within IPSS-M categories:\n{r['hr'].round(3).to_string()}", flush=True)
    # final models on all eligible patients + explanations
    shap = {}
    for ep, (tc, ec) in ENDPOINTS.items():
        keep = (d.IPSSM_SCORE.notna() & d[tc].notna()).to_numpy()
        Fe, t, e = F[keep], d[tc].to_numpy(float)[keep], d[ec].to_numpy(float)[keep]
        spec = next(m for m in model_zoo(groups) if m.name == PRIMARY[ep])
        m = spec.fit(Fe, t, e, seed=a.seed)
        risk = m.risk(Fe)
        cats, cuts = match_categories(risk, d.loc[keep, "IPSSM"].fillna("Moderate-Low").to_numpy())
        with open(out / "models" / f"{ep}_ipssm_plus.pkl", "wb") as fh:
            pickle.dump(dict(model=m, endpoint=ep, name=PRIMARY[ep], category_cuts=cuts, categories=IPSSM_CATS,
                             feature_columns=m.cols, n_train=int(len(t)), events=int(e.sum())), fh)
        c = m.contributions(Fe)
        imp = c.abs().mean().sort_values(ascending=False)
        direction = pd.Series({f: np.corrcoef(Fe[f].fillna(Fe[f].median()), c[f])[0, 1] if Fe[f].std() > 0 else 0 for f in imp.index[:20]})
        shap[ep] = pd.DataFrame(dict(mean_abs_contribution=imp.head(20), corr_value_vs_contribution=direction))
        shap[ep].to_csv(out / f"{ep}_feature_contributions.csv")
    figures(summary, recl, shap, out)
    report(summary, recl, shap, out, a, time.time() - t_start)
    print(f"[done] {(time.time()-t_start)/60:.1f} min -> {out/'REPORT.md'}", flush=True)


def figures(summary, recl, shap, out):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 9})
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True)
    for ax, (ep, s) in zip(axes, summary.items()):
        t = s["table"].set_index("model")
        models = [m for m in t.index if m != "IPSS-M"]
        y = np.arange(len(models))
        d, lo, hi = t.loc[models, "dC_vs_IPSS-M"], t.loc[models, "dC_lo_vs_IPSS-M"], t.loc[models, "dC_hi_vs_IPSS-M"]
        col = ["#D55E00" if l > 0 else "#56B4E9" if h < 0 else "#555555" for l, h in zip(lo, hi)]
        ax.errorbar(d, y, xerr=[d - lo, hi - d], fmt="none", ecolor=col, lw=1.5)
        ax.scatter(d, y, c=col, s=28, zorder=3)
        ax.axvline(0, color="#999999", lw=1, ls="--")
        ax.set_yticks(y); ax.set_yticklabels(models); ax.set_title(f"{ep}  (n={s['n']}, events={s['events']})", loc="left")
        ax.set_xlabel("C-index minus IPSS-M (95% bootstrap CI)")
    fig.tight_layout(); fig.savefig(out / "figures" / "cindex_vs_ipssm.png", dpi=180); plt.close(fig)
    for ep, r in recl.items():
        km = r["km"]
        fig, ax = plt.subplots(figsize=(8.5, 3.8))
        colors = {"down": "#56B4E9", "same": "#999999", "up": "#D55E00"}
        xs = {c: i for i, c in enumerate(IPSSM_CATS)}
        off = {"down": -0.25, "same": 0.0, "up": 0.25}
        for dirn in ("down", "same", "up"):
            k = km[km.direction == dirn]
            ax.bar([xs[c] + off[dirn] for c in k.ipssm], 1 - k.lfs_3y, width=0.24, color=colors[dirn], label=f"model moved {dirn}" if dirn != "same" else "same category")
        ax.set_xticks(range(6)); ax.set_xticklabels(IPSSM_CATS)
        ax.set_ylabel(f"{ep} event probability by 3 years (KM)"); ax.set_xlabel("IPSS-M category")
        ax.set_title(f"{ep}: within each IPSS-M category, patients the model moves up vs down", loc="left"); ax.legend(frameon=False)
        fig.tight_layout(); fig.savefig(out / "figures" / f"{ep}_reclassification.png", dpi=180); plt.close(fig)
    fig, axes = plt.subplots(1, len(shap), figsize=(5 * len(shap), 4.6))
    for ax, (ep, s) in zip(np.atleast_1d(axes), shap.items()):
        s = s.head(12).iloc[::-1]
        ax.barh(s.index, s.mean_abs_contribution, color=["#D55E00" if v > 0 else "#56B4E9" for v in s.corr_value_vs_contribution])
        ax.set_title(f"{ep}: corrections IPSS-M+ makes on top of IPSS-M", loc="left", fontsize=9)
        ax.set_xlabel("mean |contribution| to log-hazard\n(orange: higher value -> higher risk)")
    fig.tight_layout(); fig.savefig(out / "figures" / "feature_contributions.png", dpi=180); plt.close(fig)


def report(summary, recl, shap, out, a, secs):
    L = ["# Can a model trained on the IPSS-M cohort beat IPSS-M?", "",
         f"Data: cBioPortal `mds_iwg_2022` (IWG-PM; Bernard et al., NEJM Evidence 2022). {a.repeats}x repeated {a.folds}-fold cross-validation; "
         f"95% CIs from {a.boot} patient bootstrap resamples of the out-of-fold predictions (repeat 0). Runtime {secs/60:.0f} min.", "",
         "IPSS-M's coefficients were fitted on these same patients, so it is evaluated **in-sample** while every other model is "
         "evaluated **out-of-sample**: any gain shown here is conservative.", "",
         "**Pre-specified rule:** a model is better than its comparator only if the 95% CI of the C-index difference lies above 0. "
         "Primary comparisons: LFS and AMLt, IPSS-M+ (no age) vs IPSS-M; OS, IPSS-M+ (with age) vs IPSS-M + age.", ""]
    for ep, s in summary.items():
        t = s["table"]
        prim, ref = PRIMARY[ep], FINAL_REF[ep]
        r = t.set_index("model").loc[prim]
        col = f"dC_lo_vs_{ref}"
        verdict = "BETTER" if r[col] > 0 else ("WORSE" if r[f"dC_hi_vs_{ref}"] < 0 else "NOT DISTINGUISHABLE")
        L += [f"## {ep} (n = {s['n']}, events = {s['events']})", "",
              f"**Primary: {prim} vs {ref}: ΔC = {r[f'dC_vs_{ref}']:+.3f} (95% CI {r[col]:+.3f} to {r[f'dC_hi_vs_{ref}']:+.3f}) → {verdict}**", "",
              t[["model", "harrell_c", "c_lo", "c_hi", "uno_c_5y", "auc_12m", "auc_36m", "auc_60m", "ibs_6_60m",
                 "dC_vs_IPSS-M", "dC_lo_vs_IPSS-M", "dC_hi_vs_IPSS-M"]].round(3).to_markdown(index=False), "",
              "Lower integrated Brier score (ibs) = better calibrated survival probabilities.", ""]
        rr = recl[ep]
        L += [f"### Reclassification by {prim} ({rr['n_reclassified']} of {s['n']} patients change IPSS-M category)", "",
              "Hazard ratios WITHIN IPSS-M categories (stratified Cox): do patients the model moves up do worse, and those it moves down do better?", "",
              rr["hr"].round(3).to_markdown(), "",
              "Both scores in one Cox model (standardised): does the new score add information beyond IPSS-M?", "",
              rr["joint"].round(3).to_markdown(), "", rr["km"].round(3).to_markdown(index=False), "",
              f"![]({'figures/' + ep + '_reclassification.png'})", ""]
    L += ["## What IPSS-M+ corrects (final models, mean |TreeSHAP| contribution on top of IPSS-M)", ""]
    for ep, s in shap.items():
        L += [f"### {ep}", "", s.round(4).to_markdown(), ""]
    L += ["![](figures/cindex_vs_ipssm.png)", "", "![](figures/feature_contributions.png)", ""]
    (out / "REPORT.md").write_text("\n".join(L))


if __name__ == "__main__":
    main()
