"""MDS competing-risks adapter for tabular foundation models (and any sklearn-style regressor).

    adapter = MDSAdapter(backbone=TabPFNBackbone(ckpt), features=CURATED, anchor=True)
    adapter.fit(F_train, time, cause, ipssm_category)
    cif = adapter.predict(F_test, ipssm_category_test)   # cif[(cause, tau)] -> array

1. Targets: jackknife pseudo-observations of the Aalen-Johansen cumulative incidence of each cause at each horizon.
2. Anchoring (prior): baseline = Aalen-Johansen CIF of the patient's IPSS-M category; the backbone learns the residual.
3. Coherence: clip to [0, 1], monotone in tau, and CIF_1 + CIF_2 <= 1.
The backbone is used as released (in-context learning, no weight updates)."""
from __future__ import annotations
import numpy as np

from .competing import aalen_johansen, cif_by_group, pseudo_values


class TabPFNBackbone:
    def __init__(self, model_path, n_estimators=4, seed=0):
        self.model_path, self.n_estimators, self.seed = model_path, n_estimators, seed

    def fit_predict(self, Xtr, y, Xte):
        from tabpfn import TabPFNRegressor
        m = TabPFNRegressor(model_path=self.model_path, device="cpu", n_estimators=self.n_estimators,
                            ignore_pretraining_limits=True, random_state=self.seed)
        return m.fit(Xtr, y).predict(Xte)


class TabICLBackbone:
    def __init__(self, seed=0):
        self.seed = seed

    def fit_predict(self, Xtr, y, Xte):
        from tabicl import TabICLRegressor
        return TabICLRegressor(device="cpu", random_state=self.seed).fit(Xtr, y).predict(Xte)


class XGBBackbone:
    def __init__(self, seed=0):
        self.seed = seed

    def fit_predict(self, Xtr, y, Xte):
        import xgboost as xgb
        m = xgb.XGBRegressor(max_depth=3, learning_rate=0.03, n_estimators=300, subsample=0.8, colsample_bytree=0.8,
                             min_child_weight=5, random_state=self.seed, n_jobs=4)
        return m.fit(Xtr, y).predict(Xte)


class MDSAdapter:
    def __init__(self, backbone, features, anchor=True, taus=(24.0, 60.0), causes=(1, 2), all_cause=False):
        self.backbone, self.features, self.anchor = backbone, list(features), anchor
        self.taus, self.causes, self.all_cause = tuple(taus), tuple(causes), all_cause

    def fit_predict(self, F_tr, t, cause, cat_tr, F_te, cat_te):
        t = np.asarray(t, float); cause = np.asarray(cause, int)
        Xtr, Xte = F_tr[self.features].to_numpy(float), F_te[self.features].to_numpy(float)
        if self.all_cause:                                   # ablation: one target, any event (LFS), no cause split
            c_any = (cause > 0).astype(int)
            pv = pseudo_values(t, c_any, self.taus, causes=(1,))
            base_tr = cif_by_group(t, c_any, cat_tr, cat_tr, self.taus, causes=(1,))
            base_te = cif_by_group(t, c_any, cat_tr, cat_te, self.taus, causes=(1,))
            out = {}
            for j, tau in enumerate(self.taus):
                y = pv[:, 0, j] - (base_tr[:, 0, j] if self.anchor else 0)
                p = self.backbone.fit_predict(Xtr, y, Xte) + (base_te[:, 0, j] if self.anchor else 0)
                for k in self.causes:
                    out[(k, tau)] = np.clip(p, 0, 1)
            return out
        pv = pseudo_values(t, cause, self.taus, self.causes)         # (n, causes, taus)
        base_tr = cif_by_group(t, cause, cat_tr, cat_tr, self.taus, self.causes)
        base_te = cif_by_group(t, cause, cat_tr, cat_te, self.taus, self.causes)
        pred = np.zeros((len(Xte), len(self.causes), len(self.taus)))
        for i, k in enumerate(self.causes):
            for j, tau in enumerate(self.taus):
                y = pv[:, i, j] - (base_tr[:, i, j] if self.anchor else 0.0)
                pred[:, i, j] = self.backbone.fit_predict(Xtr, y, Xte) + (base_te[:, i, j] if self.anchor else 0.0)
        pred = coherent(pred)
        return {(k, tau): pred[:, i, j] for i, k in enumerate(self.causes) for j, tau in enumerate(self.taus)}


def coherent(pred):
    """pred (n, causes, taus): clip to [0,1], monotone non-decreasing over taus, causes summing to <= 1."""
    p = np.clip(pred, 0.0, 1.0)
    p = np.maximum.accumulate(p, axis=2)
    tot = p.sum(axis=1, keepdims=True)
    return np.where(tot > 1.0, p / np.maximum(tot, 1e-12), p)


def cr_outcome(d):
    """time = LFS months; cause 1 = AML transformation, 2 = death without transformation, 0 = censored."""
    t = d.LFS_MONTHS.to_numpy(float)
    aml = d.amlt_event.to_numpy(float) == 1
    any_ev = d.lfs_event.to_numpy(float) == 1
    cause = np.where(aml, 1, np.where(any_ev, 2, 0))
    return t, cause
