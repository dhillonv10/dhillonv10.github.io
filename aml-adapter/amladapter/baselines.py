"""Conventional baselines and the shared linear probe.

Every representation (HVG expression, PCA, frozen scGPT, SSL-adapted scGPT) is scored with the SAME probe:
standardise -> logistic regression, with C chosen by inner patient-grouped cross-validation on training patients.
"""
from __future__ import annotations
import numpy as np
import scipy.sparse as sp
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler


def lognorm(X, target: float = 1e4) -> sp.csr_matrix:
    X = sp.csr_matrix(X, dtype=np.float32)
    lib = np.asarray(X.sum(1)).ravel()
    Y = (sp.diags((target / np.maximum(lib, 1)).astype(np.float32)) @ X).tocsr()
    Y.data = np.log1p(Y.data)
    return Y


class ExpressionEncoder:
    """log1p(CP10k) -> top-n variance genes (chosen on training cells) -> optional PCA. Fit on training cells only."""

    def __init__(self, n_hvg: int = 3000, n_pcs: int | None = None, max_fit_cells: int = 20000, seed: int = 0):
        self.n_hvg, self.n_pcs, self.max_fit_cells, self.seed = n_hvg, n_pcs, max_fit_cells, seed

    def fit(self, X):
        r = np.random.default_rng(self.seed)
        rows = r.choice(X.shape[0], size=min(X.shape[0], self.max_fit_cells), replace=False)
        Y = lognorm(X[rows])
        mu = np.asarray(Y.mean(0)).ravel()
        var = np.asarray(Y.power(2).mean(0)).ravel() - mu ** 2
        self.hvg = np.sort(np.argsort(var)[-min(self.n_hvg, Y.shape[1]):])
        D = Y[:, self.hvg].toarray()
        self.center = D.mean(0)
        if self.n_pcs:
            k = min(self.n_pcs, D.shape[0] - 1, D.shape[1] - 1)
            self.pca = PCA(n_components=k, random_state=self.seed).fit(D - self.center)
        return self

    def transform(self, X) -> np.ndarray:
        D = lognorm(X)[:, self.hvg].toarray() - self.center
        return (self.pca.transform(D) if self.n_pcs else D).astype(np.float32)


class Probe:
    """StandardScaler + LogisticRegression; C picked by inner GroupKFold on patients.
    kind='binary' -> decision_function scores; kind='multiclass' -> class predictions (+ probabilities)."""

    def __init__(self, kind: str = "binary", C_grid=(0.01, 0.1, 1.0), inner_folds: int = 3, max_iter: int = 2000):
        self.kind, self.C_grid, self.inner_folds, self.max_iter = kind, tuple(C_grid), inner_folds, max_iter

    def _lr(self, C):
        return LogisticRegression(C=C, class_weight="balanced", max_iter=self.max_iter)

    def _score(self, y, s):
        if self.kind == "binary":
            return roc_auc_score(y, s) if len(np.unique(y)) == 2 else np.nan
        return f1_score(y, s, average="macro")

    def fit(self, Z, y, groups):
        Z = np.asarray(Z, np.float32); y = np.asarray(y); groups = np.asarray(groups)
        self.scaler = StandardScaler().fit(Z)
        A = self.scaler.transform(Z)
        n_g = len(np.unique(groups))
        self.inner_scores = {}
        if len(self.C_grid) > 1 and n_g >= 3:
            for C in self.C_grid:
                pred = np.empty(len(y), dtype=float if self.kind == "binary" else y.dtype)
                ok = np.zeros(len(y), bool)
                for a, b in GroupKFold(n_splits=min(self.inner_folds, n_g)).split(A, y, groups):
                    if len(np.unique(y[a])) < 2:
                        continue
                    m = self._lr(C).fit(A[a], y[a])
                    pred[b] = m.decision_function(A[b]) if self.kind == "binary" else m.predict(A[b])
                    ok[b] = True
                self.inner_scores[C] = self._score(y[ok], pred[ok]) if ok.any() else np.nan
            self.C = max(self.inner_scores, key=lambda c: -np.inf if np.isnan(self.inner_scores[c]) else self.inner_scores[c])
        else:
            self.C = self.C_grid[len(self.C_grid) // 2]
        self.model = self._lr(self.C).fit(A, y)
        return self

    def decision(self, Z):
        return self.model.decision_function(self.scaler.transform(np.asarray(Z, np.float32)))

    def predict(self, Z):
        return self.model.predict(self.scaler.transform(np.asarray(Z, np.float32)))


def cap_per_group(keys: np.ndarray, cap: int, seed: int = 0) -> np.ndarray:
    """Indices with at most `cap` items per key (e.g. per sample x label), so one huge sample cannot dominate."""
    r = np.random.default_rng(seed)
    keys = np.asarray(keys)
    out = []
    for k in np.unique(keys):
        idx = np.flatnonzero(keys == k)
        out.extend(r.permutation(idx)[:cap])
    return np.sort(np.array(out, dtype=np.int64))
