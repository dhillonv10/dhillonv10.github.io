"""Survival models with one interface: fit(X, time, event) -> self ; risk(X) -> higher means worse prognosis.

Every tunable model chooses its hyper-parameters by inner K-fold CV on the training patients only, and also returns
inner out-of-fold risks (`self.oof_`) that are used to calibrate survival probabilities without optimism.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from lifelines.utils import concordance_index
from sklearn.model_selection import StratifiedKFold


def cindex(t, e, risk) -> float:
    """Harrell's C (higher risk = shorter survival)."""
    return float(concordance_index(t, -np.asarray(risk), e))


def _inner_folds(t, e, k, seed):
    return list(StratifiedKFold(k, shuffle=True, random_state=seed).split(np.zeros(len(e)), e.astype(int)))


class _Imputer:
    def fit(self, X):
        self.med = np.nanmedian(X, axis=0)
        self.med = np.where(np.isnan(self.med), 0, self.med)
        Xi = np.where(np.isnan(X), self.med, X)
        self.mu, self.sd = Xi.mean(0), Xi.std(0)
        self.sd[self.sd == 0] = 1
        return self

    def __call__(self, X, scale=True):
        Xi = np.where(np.isnan(X), self.med, X)
        return (Xi - self.mu) / self.sd if scale else Xi


class ScoreModel:
    """A published score used as-is (no fitting): IPSS-M or IPSS-R."""
    def __init__(self, name, col):
        self.name, self.cols = name, [col]

    def fit(self, X, t, e, seed=0):
        self.oof_ = X[self.cols[0]].to_numpy(float)
        return self

    def risk(self, X):
        return X[self.cols[0]].to_numpy(float)


class CoxRidge:
    """Low-dimensional Cox model (e.g. IPSS-M score + age), small ridge penalty."""
    def __init__(self, name, cols, penalizer=0.01, inner_k=3):
        self.name, self.cols, self.pen, self.inner_k = name, list(cols), penalizer, inner_k

    def _fit(self, X, t, e):
        from lifelines import CoxPHFitter
        imp = _Imputer().fit(X)
        df = pd.DataFrame(imp(X), columns=[f"x{i}" for i in range(X.shape[1])]); df["T"], df["E"] = t, e
        m = CoxPHFitter(penalizer=self.pen).fit(df, "T", "E")
        return imp, m

    def _risk(self, fitted, X):
        imp, m = fitted
        return imp(X) @ m.params_.to_numpy()

    def fit(self, X, t, e, seed=0):
        A = X[self.cols].to_numpy(float)
        self.oof_ = np.zeros(len(t))
        for a, b in _inner_folds(t, e, self.inner_k, seed):
            self.oof_[b] = self._risk(self._fit(A[a], t[a], e[a]), A[b])
        self.fitted = self._fit(A, t, e)
        return self

    def risk(self, X):
        return self._risk(self.fitted, X[self.cols].to_numpy(float))


class CoxNet:
    """Elastic-net Cox on many features; alpha chosen by inner CV."""
    def __init__(self, name, cols, l1_ratio=0.5, inner_k=3):
        self.name, self.cols, self.l1, self.inner_k = name, list(cols), l1_ratio, inner_k

    @staticmethod
    def _y(t, e):
        from sksurv.util import Surv
        return Surv.from_arrays(e.astype(bool), t)

    def fit(self, X, t, e, seed=0):
        from sksurv.linear_model import CoxnetSurvivalAnalysis
        A = X[self.cols].to_numpy(float)
        imp = _Imputer().fit(A)
        path = CoxnetSurvivalAnalysis(l1_ratio=self.l1, alpha_min_ratio=0.01, n_alphas=30).fit(imp(A), self._y(t, e))
        alphas = path.alphas_
        folds = _inner_folds(t, e, self.inner_k, seed)
        scores = np.zeros((len(folds), len(alphas))); oof = np.zeros((len(t), len(alphas)))
        for i, (a, b) in enumerate(folds):
            ii = _Imputer().fit(A[a])
            m = CoxnetSurvivalAnalysis(l1_ratio=self.l1, alphas=alphas).fit(ii(A[a]), self._y(t[a], e[a]))
            for j, al in enumerate(alphas):
                r = m.predict(ii(A[b]), alpha=al); oof[b, j] = r
                scores[i, j] = cindex(t[b], e[b], r)
        j = int(np.argmax(scores.mean(0)))
        self.alpha, self.oof_ = alphas[j], oof[:, j]
        self.imp = imp
        self.model = CoxnetSurvivalAnalysis(l1_ratio=self.l1, alphas=[self.alpha]).fit(imp(A), self._y(t, e))
        return self

    def risk(self, X):
        return self.model.predict(self.imp(X[self.cols].to_numpy(float)))


class RSF:
    """Random survival forest (median imputation)."""
    def __init__(self, name, cols, n_estimators=300, min_samples_leaf=20, inner_k=3, n_jobs=4):
        self.name, self.cols, self.n, self.leaf, self.inner_k, self.n_jobs = name, list(cols), n_estimators, min_samples_leaf, inner_k, n_jobs

    def _fit(self, A, t, e, seed):
        from sksurv.ensemble import RandomSurvivalForest
        imp = _Imputer().fit(A)
        m = RandomSurvivalForest(n_estimators=self.n, min_samples_leaf=self.leaf, max_features="sqrt", n_jobs=self.n_jobs,
                                 random_state=seed).fit(imp(A, scale=False), CoxNet._y(t, e))
        return imp, m

    def fit(self, X, t, e, seed=0):
        A = X[self.cols].to_numpy(float)
        self.oof_ = np.zeros(len(t))
        for a, b in _inner_folds(t, e, self.inner_k, seed):
            imp, m = self._fit(A[a], t[a], e[a], seed)
            self.oof_[b] = np.log1p(m.predict(imp(A[b], scale=False)))
        self.imp, self.model = self._fit(A, t, e, seed)
        return self

    def risk(self, X):
        # forest output is a summed cumulative hazard; log puts it on a log-hazard-like scale for calibration
        return np.log1p(self.model.predict(self.imp(X[self.cols].to_numpy(float), scale=False)))


class XGBCox:
    """Gradient-boosted Cox model (xgboost, survival:cox). Depth and number of rounds chosen by inner CV.

    offset_col: boost FROM an existing score. The score enters as a fixed log-hazard offset (b * score, b fitted on
    the training patients), and the trees learn only corrections to it: "IPSS-M+"."""
    ROUNDS = (25, 50, 100, 200, 300, 500, 800)

    def __init__(self, name, cols, offset_col=None, depths=(2, 3), eta=0.03, inner_k=3, nthread=4):
        self.name, self.cols, self.offset_col = name, list(cols), offset_col
        self.depths, self.eta, self.inner_k, self.nthread = depths, eta, inner_k, nthread

    def _offset(self, X, t=None, e=None):
        if self.offset_col is None:
            return None
        s = X[self.offset_col].to_numpy(float)
        if t is not None:
            from lifelines import CoxPHFitter
            df = pd.DataFrame(dict(s=s, T=t, E=e))
            self.b = float(CoxPHFitter().fit(df, "T", "E").params_["s"])
        return self.b * s

    def _dm(self, A, t=None, e=None, off=None):
        import xgboost as xgb
        y = None if t is None else np.where(e.astype(bool), t, -t)
        dm = xgb.DMatrix(A, label=y, missing=np.nan)
        if off is not None:
            dm.set_base_margin(off)
        return dm

    def _params(self, depth, seed):
        return dict(objective="survival:cox", eta=self.eta, max_depth=depth, subsample=0.8, colsample_bytree=0.8,
                    min_child_weight=5, reg_lambda=1.0, nthread=self.nthread, seed=seed, verbosity=0)

    def fit(self, X, t, e, seed=0):
        import xgboost as xgb
        A = X[self.cols].to_numpy(float)
        folds = _inner_folds(t, e, self.inner_k, seed)
        grid = [(d, r) for d in self.depths for r in self.ROUNDS]
        scores = {g: [] for g in grid}; oof = {g: np.zeros(len(t)) for g in grid}
        for a, b in folds:
            Xa, Xb = X.iloc[a], X.iloc[b]
            off_a = self._offset(Xa, t[a], e[a]); off_b = self._offset(Xb)
            for d in self.depths:
                bst = xgb.train(self._params(d, seed), self._dm(A[a], t[a], e[a], off_a), num_boost_round=max(self.ROUNDS))
                for r in self.ROUNDS:
                    p = bst.predict(self._dm(A[b], off=off_b), output_margin=True, iteration_range=(0, r))
                    oof[(d, r)][b] = p
                    scores[(d, r)].append(cindex(t[b], e[b], p))
        self.depth, self.rounds = max(grid, key=lambda g: np.mean(scores[g]))
        self.inner_scores = {f"d{g[0]}_r{g[1]}": float(np.mean(v)) for g, v in scores.items()}
        self.oof_ = oof[(self.depth, self.rounds)]
        off = self._offset(X, t, e)
        self.booster = xgb.train(self._params(self.depth, seed), self._dm(A, t, e, off), num_boost_round=self.rounds)
        return self

    def risk(self, X):
        return self.booster.predict(self._dm(X[self.cols].to_numpy(float), off=self._offset(X)), output_margin=True)

    def contributions(self, X) -> pd.DataFrame:
        """Per-feature contributions (TreeSHAP) to the log-hazard, on top of the offset."""
        c = self.booster.predict(self._dm(X[self.cols].to_numpy(float), off=self._offset(X)), pred_contribs=True)
        return pd.DataFrame(c[:, :-1], columns=self.cols, index=X.index)


def model_zoo(groups: dict) -> list:
    allf, noage = groups["all"], groups["all_no_age"]
    return [
        ScoreModel("IPSS-R", "IPSSR_SCORE"),
        ScoreModel("IPSS-M", "IPSSM_SCORE"),
        CoxRidge("IPSS-M + age", ["IPSSM_SCORE", "AGE"]),
        CoxNet("CoxNet (all features)", allf),
        RSF("RSF (all features)", allf),
        XGBCox("XGBoost (all features)", allf),
        XGBCox("IPSS-M+ (no age)", noage, offset_col="IPSSM_SCORE", eta=0.02),
        XGBCox("IPSS-M+ (with age)", allf, offset_col="IPSSM_SCORE", eta=0.02),
    ]
