"""Competing-risks tools: Aalen-Johansen CIF, jackknife pseudo-observations, IPCW time-dependent AUC and Brier score.

cause coding: 0 = censored, 1 = cause of interest (e.g. AML transformation), 2 = competing cause (death without AML).
"""
from __future__ import annotations
import numpy as np


def aalen_johansen(t, cause, taus, causes=(1, 2)):
    """CIF_k(tau) for each cause k (Aalen-Johansen; all-cause KM for S(t-)). Returns array (len(causes), len(taus))."""
    t = np.asarray(t, float); c = np.asarray(cause, int)
    o = np.argsort(t, kind="mergesort"); t, c = t[o], c[o]
    ut, idx = np.unique(t, return_index=True)
    n = len(t)
    at_risk = n - idx
    d = np.zeros((len(causes), len(ut)))
    for j, k in enumerate(causes):
        d[j] = np.add.reduceat((c == k).astype(float), idx)
    d_all = np.add.reduceat((c > 0).astype(float), idx)
    S = np.cumprod(1 - d_all / at_risk)
    S_prev = np.concatenate([[1.0], S[:-1]])
    cif = np.cumsum(S_prev * d / at_risk, axis=1)              # (causes, unique times)
    pos = np.searchsorted(ut, np.asarray(taus, float), side="right") - 1
    out = np.where(pos[None, :] >= 0, cif[:, np.clip(pos, 0, None)], 0.0)
    return out


def pseudo_values(t, cause, taus, causes=(1, 2)):
    """Jackknife pseudo-observations theta_i = n*theta - (n-1)*theta_(-i). Shape (n, len(causes), len(taus))."""
    t = np.asarray(t, float); c = np.asarray(cause, int); n = len(t)
    full = aalen_johansen(t, c, taus, causes)
    pv = np.empty((n, len(causes), len(taus)))
    mask = np.ones(n, bool)
    for i in range(n):
        mask[i] = False
        pv[i] = n * full - (n - 1) * aalen_johansen(t[mask], c[mask], taus, causes)
        mask[i] = True
    return pv


def cif_by_group(t, cause, groups, new_groups, taus, causes=(1, 2), min_n=20):
    """Aalen-Johansen CIF per group (falls back to the pooled CIF for small or unseen groups)."""
    groups = np.asarray(groups).astype(str); new_groups = np.asarray(new_groups).astype(str)
    pooled = aalen_johansen(t, cause, taus, causes)
    table = {g: (aalen_johansen(t[groups == g], cause[groups == g], taus, causes) if (groups == g).sum() >= min_n else pooled)
             for g in np.unique(groups)}
    return np.stack([table.get(g, pooled) for g in new_groups])     # (n_new, causes, taus)


def _censoring_survival(t, cause):
    """Kaplan-Meier of the censoring distribution, G(s-) evaluated via a step function."""
    t = np.asarray(t, float); cens = (np.asarray(cause) == 0).astype(float)
    o = np.argsort(t, kind="mergesort"); ts, cs = t[o], cens[o]
    ut, idx = np.unique(ts, return_index=True)
    at_risk = len(ts) - idx
    dc = np.add.reduceat(cs, idx)
    G = np.cumprod(1 - dc / at_risk)

    def G_left(s):  # G(s-)
        pos = np.searchsorted(ut, s, side="left") - 1
        return np.where(pos >= 0, G[np.clip(pos, 0, None)], 1.0)
    return G_left


def auc_cr(t, cause, risk, tau, k=1):
    """Cause-specific cumulative/dynamic AUC at tau, Blanche et al. 2013 definition 2 (competing events are controls)."""
    t = np.asarray(t, float); c = np.asarray(cause, int); r = np.asarray(risk, float)
    G = _censoring_survival(t, c)
    case = (t <= tau) & (c == k)
    ctrl_late = t > tau
    ctrl_comp = (t <= tau) & (c > 0) & (c != k)
    w_case = 1.0 / np.maximum(G(t[case]), 1e-8)
    w_ctrl = np.concatenate([np.full(ctrl_late.sum(), 1.0 / max(float(G(np.array([tau]))[0]), 1e-8)),
                             1.0 / np.maximum(G(t[ctrl_comp]), 1e-8)])
    r_case, r_ctrl = r[case], np.concatenate([r[ctrl_late], r[ctrl_comp]])
    if len(r_case) == 0 or len(r_ctrl) == 0:
        return np.nan
    o = np.argsort(r_ctrl); rc, wc = r_ctrl[o], w_ctrl[o]
    cw = np.concatenate([[0.0], np.cumsum(wc)])
    lo = np.searchsorted(rc, r_case, side="left"); hi = np.searchsorted(rc, r_case, side="right")
    num = np.sum(w_case * (cw[lo] + 0.5 * (cw[hi] - cw[lo])))
    return float(num / (w_case.sum() * wc.sum()))


def brier_cr(t, cause, pred_cif, tau, k=1):
    """IPCW Brier score for the predicted CIF of cause k at tau."""
    t = np.asarray(t, float); c = np.asarray(cause, int); p = np.asarray(pred_cif, float)
    G = _censoring_survival(t, c)
    event_by_tau = (t <= tau) & (c > 0)
    y = ((t <= tau) & (c == k)).astype(float)
    w = np.where(event_by_tau, 1.0 / np.maximum(G(t), 1e-8), np.where(t > tau, 1.0 / max(float(G(np.array([tau]))[0]), 1e-8), 0.0))
    return float(np.sum(w * (y - p) ** 2) / len(t))
