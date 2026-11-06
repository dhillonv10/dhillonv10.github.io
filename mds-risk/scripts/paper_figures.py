#!/usr/bin/env python
"""Figures for the manuscript, from the outputs of run_paper_bench.py.

    python scripts/paper_figures.py --results paper/results
"""
import argparse, sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mdsrisk.competing import aalen_johansen

plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 9, "axes.titlesize": 10})
BLUE, ORANGE, GREY, GREEN, PURPLE = "#0072B2", "#D55E00", "#888888", "#009E73", "#CC79A7"
SHORT = {"M1": "IPSS-R", "M2": "IPSS-M+ (XGB Cox)", "M3": "TabPFN + adapter", "M4": "XGBoost + adapter",
         "M5": "TabPFN + adapter, no anchor", "M6": "TabPFN + adapter, 102 features", "M7": "TabPFN, all-cause target",
         "M8": "TabICL + adapter"}
LOWER = ("Very-Low", "Low", "Moderate-Low")


def forest(R, out):
    panels = [("B1_AML_60m", "AML transformation, 5 y\nall patients"), ("B2_AML_lower_risk_60m", "AML transformation, 5 y\nIPSS-M lower-risk"),
              ("B3_death_60m", "Death without AML, 5 y\nall patients")]
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True)
    for ax, (key, title) in zip(axes, panels):
        t = pd.read_csv(R / f"{key}.csv").set_index("model")
        ref = t.loc["M0", "auc"]
        ms = [m for m in SHORT if m in t.index][::-1]
        y = np.arange(len(ms))
        d, lo, hi = t.loc[ms, "d_vs_ref"], t.loc[ms, "d_lo"], t.loc[ms, "d_hi"]
        col = [ORANGE if m == "M3" else (BLUE if l > 0 else GREY) for m, l in zip(ms, lo)]
        ax.errorbar(d, y, xerr=[d - lo, hi - d], fmt="none", ecolor=col, lw=1.6)
        ax.scatter(d, y, c=col, s=30, zorder=3)
        ax.axvline(0, color=GREY, lw=1, ls="--")
        ax.set_yticks(y); ax.set_yticklabels([SHORT[m] for m in ms])
        ax.set_title(f"{title}  (IPSS-M AUC {ref:.3f})", loc="left")
        ax.set_xlabel("AUC minus IPSS-M (95% bootstrap CI)")
    fig.tight_layout(); fig.savefig(out / "fig1_forest.png", dpi=200); plt.close(fig)


def learning_curve(R, out):
    t = pd.read_csv(R / "B4_data_efficiency.csv")
    fig, ax = plt.subplots(figsize=(5.2, 3.8))
    for mid, col, lab in (("M3", ORANGE, "TabPFN + adapter"), ("M4", BLUE, "XGBoost + adapter")):
        s = t[t.model == mid].sort_values("fraction")
        ax.errorbar(s.fraction * 100, s.auc_mean, yerr=s.auc_sd, color=col, marker="o", ms=5, lw=1.8, capsize=3, label=lab)
    ipssm = t[t.model == "M0"].auc_mean.iloc[0]
    ax.axhline(ipssm, color=GREY, ls="--", lw=1.2); ax.text(102, ipssm, "IPSS-M", va="center", color=GREY, fontsize=8)
    ax.set_xscale("log"); ax.set_xticks([10, 25, 50, 100]); ax.set_xticklabels(["10%", "25%", "50%", "100%"])
    ax.set_xlabel("share of each training fold used (≈190 to 1,940 patients)"); ax.set_ylabel("AUC, AML transformation at 5 y")
    ax.set_title("Data efficiency (B4)", loc="left"); ax.legend(frameon=False, loc="lower right")
    fig.tight_layout(); fig.savefig(out / "fig2_data_efficiency.png", dpi=200); plt.close(fig)


def lower_risk_curves(R, out):
    z = np.load(R / "oof_risks.npz", allow_pickle=True)
    t, cause, cat = z["t"], z["cause"], z["cat_m"]
    low = np.isin(cat, LOWER)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    grid = np.linspace(0, 96, 97)
    for ax, (mid, title) in zip(axes, (("M0", "IPSS-M score tertiles"), ("M3", "TabPFN + adapter tertiles"))):
        r = z[f"{mid}|1|60.0"][low]
        q = np.quantile(r, [1 / 3, 2 / 3])
        g = np.searchsorted(q, r, side="right")
        for k, (lab, col) in enumerate((("lowest third", BLUE), ("middle third", GREY), ("highest third", ORANGE))):
            m = g == k
            cif = aalen_johansen(t[low][m], cause[low][m], grid, causes=(1,))[0]
            ax.step(grid, cif, where="post", color=col, lw=1.8, label=f"{lab}: {cif[60]*100:.0f}% at 5 y (n={m.sum()})")
        ax.set_title(f"IPSS-M lower-risk patients (n={low.sum()}), split by {title}", loc="left", fontsize=9)
        ax.set_xlabel("months"); ax.legend(frameon=False, fontsize=8, loc="upper left")
    axes[0].set_ylabel("cumulative incidence of AML transformation")
    fig.tight_layout(); fig.savefig(out / "fig3_lower_risk_cif.png", dpi=200); plt.close(fig)


def calibration(R, out):
    z = np.load(R / "oof_risks.npz", allow_pickle=True)
    t, cause = z["t"], z["cause"]
    fig, ax = plt.subplots(figsize=(4.4, 4.2))
    for mid, col, lab in (("M0", GREY, "IPSS-M categories"), ("M3", ORANGE, "TabPFN + adapter"), ("M5", PURPLE, "TabPFN, no anchor")):
        key = f"cif|{mid}|1|60.0"
        if key not in z:
            continue
        p = z[key]
        bins = np.unique(np.quantile(p, np.linspace(0, 1, 11)))
        g = np.clip(np.searchsorted(bins, p, side="right") - 1, 0, len(bins) - 2)
        xs, ys = [], []
        for k in np.unique(g):
            m = g == k
            xs.append(p[m].mean()); ys.append(aalen_johansen(t[m], cause[m], [60.0], causes=(1,))[0, 0])
        ax.plot(xs, ys, marker="o", ms=4, color=col, lw=1.5, label=lab)
    ax.plot([0, 0.8], [0, 0.8], color="#cccccc", lw=1)
    ax.set_xlabel("predicted 5-y AML incidence"); ax.set_ylabel("observed (Aalen–Johansen)")
    ax.set_title("Calibration, deciles of prediction", loc="left"); ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(out / "fig4_calibration.png", dpi=200); plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--results", default="paper/results"); a = ap.parse_args()
    R = Path(a.results); out = R / "figures"; out.mkdir(exist_ok=True)
    forest(R, out); learning_curve(R, out); lower_risk_curves(R, out); calibration(R, out)
    print("figures ->", out)
