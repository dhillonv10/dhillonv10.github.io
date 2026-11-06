"""Benchmark: tasks T1-T3, methods, metrics, patient-level bootstrap, report.

Tasks
-----
T1  malignant vs normal, within van Galen, patient-held-out K-fold.          primary metric: AUROC
T2  cross-cohort, cross-platform transfer: train on ALL van Galen (Seq-Well),
    test on Naldini (10x) against per-cell NPM1 GENOTYPE (MUT vs WT-only).
    Naldini labels are never used for training or model selection.          primary metric: AUROC
    (also: AUROC within day-14/30 post-induction cells, FPR at 90% sensitivity)
T3  AML cell-state annotation (21 van Galen states), patient-held-out.       primary metric: macro-F1

Methods (all scored by the same probe unless stated)
-------
HVG-LR          log-normalised top-variance genes -> logistic regression
PCA-LR          the same, compressed to 50 PCs
scGPT-frozen    original scGPT <cls> embedding -> logistic regression
scGPT+SSL       scGPT + AML adapter trained self-supervised (masked expression, no labels) -> logistic regression
scGPT+task      scGPT + AML adapter (zero-init) trained end-to-end with task heads (no probe)
scGPT+SSL+task  the same, but the adapter starts from the SSL adapter
T2 only, when cfg.t2_target_ssl:
scGPT+SSL(+tgt) / scGPT+SSL+task(+tgt): the SSL stage also sees UNLABELLED Naldini cells (unsupervised domain adaptation)

The shipped model (aml_adapter_final.pt) is whichever of scGPT+task / scGPT+SSL+task scores better on van Galen
cross-validation (T1, then T3); the Naldini test set never influences that choice.

"Promise" (fixed in advance): a scGPT adapter variant beats BOTH scGPT-frozen and the best of HVG-LR/PCA-LR on the
task's primary metric, with the 95% patient-bootstrap CI of each paired difference above 0.
"""
from __future__ import annotations
import copy
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import f1_score, roc_auc_score

from .adapters import AdapterSet, attach_new_adapters
from .backbone import embed, gene_ids_for, load_scgpt
from .baselines import ExpressionEncoder, Probe, cap_per_group
from .train import TaskHeads, predict, train_ssl, train_supervised

CONVENTIONAL = ("HVG-LR", "PCA-LR")


# ------------------------------------------------------------------------------------------------- config
@dataclass
class BenchConfig:
    out_dir: str = "results"
    scgpt_dir: str = "models/scGPT-human"
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    tasks: tuple = ("T1", "T2", "T3")
    seed: int = 42
    # scGPT / adapter
    max_len: int = 1200
    batch: int = 16
    accum: int = 1
    eval_batch: int = 64
    num_workers: int = 2
    bottleneck: int = 64
    ssl_steps: int = 2000
    ssl_lr: float = 1e-3
    task_steps: int = 1500
    task_lr: float = 1e-3
    adapt_cap: int = 1500            # max cells per sample in an SSL corpus
    t2_target_ssl: bool = True
    # evaluation
    n_folds: int = 4
    n_hvg: int = 3000
    n_pcs: int = 50
    probe_cap: int = 300             # max training cells per (sample, label) for probes
    C_grid: tuple = (0.01, 0.1, 1.0)
    target_tpr: float = 0.90
    n_boot: int = 1000
    eval_cap: int | None = None      # optional cap of cells per sample (CPU mini runs)
    min_celltype_cells: int = 30     # T3: classes with fewer training cells are dropped
    extra: dict = field(default_factory=dict)


PROFILES = {
    # synthetic data + tiny random backbone: checks the plumbing in ~1-2 minutes on CPU
    "smoke": dict(max_len=256, batch=16, eval_batch=32, num_workers=0, bottleneck=8, ssl_steps=20, task_steps=200,
                  n_folds=3, n_hvg=200, n_pcs=10, probe_cap=60, n_boot=100, adapt_cap=200, ssl_lr=5e-3, task_lr=1e-2),
    # REAL data + REAL scGPT on a CPU: heavily subsampled, short sequences, few steps. Verifies the pipeline end to end;
    # the numbers are NOT a result.
    "cpu-mini": dict(max_len=256, batch=8, eval_batch=32, num_workers=0, bottleneck=32, ssl_steps=60, task_steps=80,
                     n_folds=3, n_hvg=2000, n_pcs=30, probe_cap=40, n_boot=200, adapt_cap=40, eval_cap=40,
                     t2_target_ssl=False),
    # the real experiment, sized for one Colab T4/L4 (~3-4 h with all tasks and the target-SSL variants)
    "full": dict(),
}


def make_config(profile: str = "full", **overrides) -> BenchConfig:
    cfg = BenchConfig(**{**PROFILES[profile], **overrides})
    cfg.extra["profile"] = profile
    return cfg


# ------------------------------------------------------------------------------------------------ helpers
def greedy_patient_folds(obs: pd.DataFrame, k: int, seed: int = 0) -> list[list[str]]:
    """Balance folds by labelled-cell count; healthy donors and patients are spread across folds."""
    w = obs.groupby("patient").size().sort_values(ascending=False)
    r = np.random.default_rng(seed)
    order = list(w.index)
    # deterministic shuffle among equal weights, then greedy
    order = sorted(order, key=lambda p: (-w[p], r.random()))
    folds, load = [[] for _ in range(k)], np.zeros(k)
    for p in order:
        i = int(np.argmin(load)); folds[i].append(p); load[i] += w[p]
    return [sorted(f) for f in folds]


def subsample_per_sample(obs: pd.DataFrame, cap: int | None, seed: int) -> np.ndarray:
    if cap is None:
        return np.arange(len(obs))
    return cap_per_group(obs["sample"].to_numpy(), cap, seed)


def fpr_at_tpr(y, s, tpr=0.9) -> float:
    y = np.asarray(y); s = np.asarray(s)
    if len(np.unique(y)) < 2:
        return np.nan
    thr = np.quantile(s[y == 1], 1 - tpr)
    return float((s[y == 0] >= thr).mean())


def _auc(y, s):
    return roc_auc_score(y, s) if len(np.unique(y)) == 2 else np.nan


def patient_bootstrap(df: pd.DataFrame, metric, variants, n_boot: int, seed: int, ref: str | None = None):
    """Point estimate + 95% CI per variant, and paired differences vs `ref`, resampling PATIENTS with replacement."""
    r = np.random.default_rng(seed)
    pats = sorted(df.patient.unique())
    by = {v: {p: g for p, g in df[df.variant == v].groupby("patient")} for v in variants}
    draws = r.integers(0, len(pats), size=(n_boot, len(pats)))
    rows, boots = [], {}
    for v in variants:
        point = metric(df[df.variant == v])
        b = []
        for d in draws:
            parts = [by[v][pats[i]] for i in d if pats[i] in by[v]]
            b.append(metric(pd.concat(parts)) if parts else np.nan)
        boots[v] = np.array(b, float)
        rows.append(dict(variant=v, estimate=point, ci_lo=np.nanpercentile(boots[v], 2.5), ci_hi=np.nanpercentile(boots[v], 97.5)))
    out = pd.DataFrame(rows)
    if ref is not None and ref in boots:
        for i, v in enumerate(out.variant):
            d = boots[v] - boots[ref]
            out.loc[i, f"diff_vs_{ref}"] = out.loc[i, "estimate"] - out.loc[out.variant == ref, "estimate"].iloc[0]
            out.loc[i, f"diff_lo_vs_{ref}"] = np.nanpercentile(d, 2.5)
            out.loc[i, f"diff_hi_vs_{ref}"] = np.nanpercentile(d, 97.5)
    return out, boots


# ------------------------------------------------------------------------------------------------- runner
class Benchmark:
    def __init__(self, cfg: BenchConfig, vg, nd=None, log=print):
        self.cfg, self.log = cfg, log
        self.out = Path(cfg.out_dir); self.out.mkdir(parents=True, exist_ok=True)
        (self.out / "adapters").mkdir(exist_ok=True)
        self.dev = torch.device(cfg.device)
        if "T2" in cfg.tasks and nd is None:
            raise ValueError("T2 needs the Naldini cohort")
        # one shared gene space: genes measured in both cohorts (if T2), restricted to scGPT's vocabulary for scGPT
        if nd is not None:
            common = vg.var_names.intersection(nd.var_names)
            vg, nd = vg[:, common].copy(), nd[:, common].copy()
        self.model, self.vocab, self.mcfg = load_scgpt(cfg.scgpt_dir, device=cfg.device)
        gid = gene_ids_for(vg.var_names, self.vocab)
        self.in_vocab = np.flatnonzero(gid >= 0)
        self.gene_ids = gid[self.in_vocab]
        self.log(f"[genes] shared space {vg.n_vars:,}; in scGPT vocabulary {len(self.in_vocab):,}")
        # optional per-sample cap for CPU runs
        keep = subsample_per_sample(vg.obs, cfg.eval_cap, cfg.seed)
        self.vg = vg[keep].copy()
        if nd is not None:
            if cfg.eval_cap is not None:                      # CPU mini runs: labelled cells only, capped per sample
                nd = nd[nd.obs.malignant.notna().to_numpy()]
            self.nd = nd[subsample_per_sample(nd.obs, cfg.eval_cap, cfg.seed)].copy()
        else:
            self.nd = None
        self.log(f"[cells] vanGalen {self.vg.n_obs:,} ({self.vg.obs.patient.nunique()} patients)"
                 + (f" | Naldini {self.nd.n_obs:,} ({self.nd.obs.patient.nunique()} patients)" if self.nd is not None else ""))
        ct_counts = self.vg.obs.celltype.value_counts()
        self.celltypes = sorted(ct_counts[ct_counts >= cfg.min_celltype_cells].index)
        self.ct_index = {c: i for i, c in enumerate(self.celltypes)}
        self.preds = []          # list of DataFrames (one row per cell x variant x task)
        self.logs = {}

    # ---------------------------------------------------------------- scGPT helpers
    def _Xv(self, ad):
        return ad.X[:, self.in_vocab]

    def _embed(self, ad):
        c = self.cfg
        return embed(self.model, self._Xv(ad), self.gene_ids, self.vocab, self.mcfg, max_len=c.max_len,
                     batch_size=c.eval_batch, seed=c.seed, num_workers=c.num_workers)

    def _ssl_corpus(self, ads, seed):
        import anndata as ad
        parts = [a[cap_per_group(a.obs["sample"].to_numpy(), self.cfg.adapt_cap, seed)] for a in ads]
        return ad.concat(parts) if len(parts) > 1 else parts[0]

    def _new_adapters(self, init: AdapterSet | None = None) -> AdapterSet:
        ad = attach_new_adapters(self.model, self.cfg.bottleneck)
        if init is not None:
            ad.load_state_dict(init.state_dict())
        return ad

    def _ssl(self, corpus, seed, label) -> AdapterSet:
        c = self.cfg
        ad = self._new_adapters()
        self.logs[label] = train_ssl(self.model, ad, self._Xv(corpus), self.gene_ids, self.vocab, self.mcfg, steps=c.ssl_steps,
                                     lr=c.ssl_lr, batch=c.batch, accum=c.accum, max_len=c.max_len, seed=seed,
                                     num_workers=c.num_workers, label=label)
        self.logs[label].pop("train_loss", None)
        return ad

    def _task(self, train_ad, init: AdapterSet, seed, label):
        c = self.cfg
        ad = self._new_adapters(init)
        heads = TaskHeads(self.mcfg["embsize"], len(self.celltypes)).to(self.dev)
        obs = train_ad.obs
        y_ct = obs.celltype.map(self.ct_index).fillna(-1).astype(int).to_numpy()
        n_s = obs.groupby("sample")["sample"].transform("size").to_numpy()
        self.logs[label] = train_supervised(self.model, ad, heads, self._Xv(train_ad), self.gene_ids, self.vocab, self.mcfg,
                                            obs.malignant.to_numpy(), y_ct, steps=c.task_steps, lr=c.task_lr, batch=c.batch,
                                            accum=c.accum, max_len=c.max_len, seed=seed, num_workers=c.num_workers,
                                            sample_weights=1.0 / np.sqrt(n_s), label=label)
        self.logs[label].pop("train_loss", None)
        return ad, heads

    def _predict_task(self, heads, ad_eval):
        c = self.cfg
        lm, lc, _ = predict(self.model, heads, self._Xv(ad_eval), self.gene_ids, self.vocab, self.mcfg, max_len=c.max_len,
                            batch_size=c.eval_batch, seed=c.seed, num_workers=c.num_workers)
        return lm, np.array(self.celltypes)[lc.argmax(1)]

    # ---------------------------------------------------------------- probe helpers
    def _probe_rows(self, obs_tr, Z_tr, obs_te, Z_te, variant, fold, task_set):
        """Fit T1 (binary) and/or T3 (multiclass) probes on training rows; return prediction rows for test rows."""
        c, rows = self.cfg, []
        g = obs_tr.patient.to_numpy()
        res = pd.DataFrame(index=obs_te.index)
        if "mal" in task_set:
            lab = obs_tr.malignant.notna().to_numpy()
            idx = np.flatnonzero(lab)
            idx = idx[cap_per_group((obs_tr["sample"].astype(str) + "|" + obs_tr.malignant.astype(str)).to_numpy()[idx], c.probe_cap, c.seed)]
            p = Probe("binary", c.C_grid).fit(Z_tr[idx], obs_tr.malignant.to_numpy()[idx].astype(int), g[idx])
            res["mal_score"] = p.decision(Z_te)
        if "ct" in task_set:
            lab = obs_tr.celltype.isin(self.celltypes).to_numpy()
            idx = np.flatnonzero(lab)
            idx = idx[cap_per_group((obs_tr["sample"].astype(str) + "|" + obs_tr.celltype.astype(str)).to_numpy()[idx], c.probe_cap, c.seed)]
            p = Probe("multiclass", c.C_grid).fit(Z_tr[idx], obs_tr.celltype.to_numpy()[idx], g[idx])
            res["ct_pred"] = p.predict(Z_te)
        res["variant"], res["fold"] = variant, fold
        return res

    # ---------------------------------------------------------------- within-cohort: T1 + T3
    def run_within(self):
        c = self.cfg
        task_set = ({"mal"} if "T1" in c.tasks else set()) | ({"ct"} if "T3" in c.tasks else set())
        if not task_set:
            return
        vg = self.vg
        folds = greedy_patient_folds(vg.obs, c.n_folds, c.seed)
        json.dump(folds, open(self.out / "folds_vanGalen.json", "w"), indent=1)
        self.log(f"[within] folds: {folds}")
        Z0 = self._embed(vg)
        for k, test_p in enumerate(folds):
            t0 = time.time()
            te = vg.obs.patient.isin(test_p).to_numpy(); tr = ~te
            tr_ad, te_ad = vg[tr], vg[te]
            obs_tr, obs_te = tr_ad.obs, te_ad.obs
            rows = []
            for name, npcs in (("HVG-LR", None), ("PCA-LR", c.n_pcs)):
                enc = ExpressionEncoder(c.n_hvg, npcs, seed=c.seed).fit(tr_ad.X)
                rows.append(self._probe_rows(obs_tr, enc.transform(tr_ad.X), obs_te, enc.transform(te_ad.X), name, k, task_set))
            rows.append(self._probe_rows(obs_tr, Z0[tr], obs_te, Z0[te], "scGPT-frozen", k, task_set))
            ssl = self._ssl(self._ssl_corpus([tr_ad], c.seed + k), c.seed + k, f"ssl_fold{k}")
            Zk = self._embed(vg)
            rows.append(self._probe_rows(obs_tr, Zk[tr], obs_te, Zk[te], "scGPT+SSL", k, task_set))
            ssl.save(self.out / "adapters" / f"ssl_fold{k}.pt", extra=dict(test_patients=test_p))
            ssl.detach()
            for vname, init in (("scGPT+task", None), ("scGPT+SSL+task", ssl)):
                task_ad, heads = self._task(tr_ad, init, c.seed + k, f"{vname}_fold{k}")
                lm, ctp = self._predict_task(heads, te_ad)
                rows.append(pd.DataFrame(dict(mal_score=lm, ct_pred=ctp, variant=vname, fold=k), index=obs_te.index))
                task_ad.detach()
            for r in rows:
                self.preds.append(r.join(obs_te[["patient", "sample", "stage", "malignant", "celltype"]]).assign(cohort="vanGalen"))
            self.log(f"[within] fold {k} done in {(time.time()-t0)/60:.1f} min")
            self._save_preds()

    # ---------------------------------------------------------------- cross-cohort: T2
    def run_cross(self):
        c = self.cfg
        if "T2" not in c.tasks:
            return
        vg, nd = self.vg, self.nd
        ev = nd[nd.obs.malignant.notna().to_numpy()]
        rows = []
        for name, npcs in (("HVG-LR", None), ("PCA-LR", c.n_pcs)):
            enc = ExpressionEncoder(c.n_hvg, npcs, seed=c.seed).fit(vg.X)
            rows.append(self._probe_rows(vg.obs, enc.transform(vg.X), ev.obs, enc.transform(ev.X), name, -1, {"mal"}))
        rows.append(self._probe_rows(vg.obs, self._embed(vg), ev.obs, self._embed(ev), "scGPT-frozen", -1, {"mal"}))
        settings = [("", [vg])] + ([("(+tgt)", [vg, nd])] if c.t2_target_ssl else [])
        for tag, corpora in settings:
            ssl = self._ssl(self._ssl_corpus(corpora, c.seed + 100), c.seed + 100, f"ssl_all{tag}")
            rows.append(self._probe_rows(vg.obs, self._embed(vg), ev.obs, self._embed(ev), f"scGPT+SSL{tag}", -1, {"mal"}))
            ssl.save(self.out / "adapters" / f"ssl_all{tag or ''}.pt".replace("(+tgt)", "_tgt"))
            ssl.detach()
            inits = [("scGPT+task", None), ("scGPT+SSL+task", ssl)] if tag == "" else [("scGPT+SSL+task", ssl)]
            for vname, init in inits:
                task_ad, heads = self._task(vg, init, c.seed + 200, f"{vname}_all{tag}")
                lm, _ = self._predict_task(heads, ev)
                rows.append(pd.DataFrame(dict(mal_score=lm, variant=f"{vname}{tag}", fold=-1), index=ev.obs.index))
                if tag == "":    # trained on ALL van Galen patients: these are the shippable models
                    self.save_model(task_ad, heads, self.out / f"aml_adapter_{'ssl_task' if init is not None else 'task'}.pt")
                task_ad.detach()
        for r in rows:
            self.preds.append(r.join(ev.obs[["patient", "sample", "stage", "malignant", "celltype"]]).assign(cohort="Naldini"))
        self._save_preds()

    def save_model(self, adapters: AdapterSet, heads: TaskHeads, path: Path):
        torch.save(dict(adapter_config=adapters.config, adapters=adapters.state_dict(), heads=heads.state_dict(),
                        celltypes=self.celltypes, d_model=self.mcfg["embsize"], max_len=self.cfg.max_len,
                        trained_on="van Galen 2019 (all patients)", bench_config=asdict(self.cfg)), path)
        self.log(f"[model] saved shipped AML adapter -> {path}")

    def _save_preds(self):
        pd.concat(self.preds).to_csv(self.out / "predictions.csv.gz")

    # ---------------------------------------------------------------- metrics + report
    def evaluate(self):
        c = self.cfg
        P = pd.concat(self.preds)
        P.index.name = "cell"
        tables = {}
        vg = P[P.cohort == "vanGalen"]
        if "T1" in c.tasks and len(vg):
            d = vg[vg.malignant.notna()]
            V = list(d.variant.unique())
            tables["T1_AUROC"] = patient_bootstrap(d, lambda x: _auc(x.malignant, x.mal_score), V, c.n_boot, c.seed, "scGPT-frozen")[0]
            post = d[d.stage == "post"]
            tables["T1_AUROC_post"] = patient_bootstrap(post, lambda x: _auc(x.malignant, x.mal_score), V, c.n_boot, c.seed, "scGPT-frozen")[0]
            tables["T1_balanced_acc"] = pd.DataFrame([dict(variant=v, estimate=0.5 * ((g.mal_score[g.malignant == 1] > 0).mean()
                                                                                    + (g.mal_score[g.malignant == 0] <= 0).mean()))
                                                      for v, g in d.groupby("variant")])
        if "T3" in c.tasks and len(vg):
            d = vg[vg.celltype.isin(self.celltypes)]
            V = list(d.variant.unique())
            f1 = lambda x: f1_score(x.celltype, x.ct_pred, average="macro", labels=sorted(x.celltype.unique()))
            tables["T3_macroF1"] = patient_bootstrap(d, f1, V, c.n_boot, c.seed, "scGPT-frozen")[0]
            mal_states = [t for t in self.celltypes if t.endswith("-like")]
            dm = d[d.celltype.isin(mal_states)]
            if len(dm):
                tables["T3_macroF1_malignant_states"] = patient_bootstrap(dm, f1, V, c.n_boot, c.seed, "scGPT-frozen")[0]
            per = []
            for v, g in d.groupby("variant"):
                s = f1_score(g.celltype, g.ct_pred, average=None, labels=self.celltypes, zero_division=0)
                per.append(pd.Series(s, index=self.celltypes, name=v))
            tables["T3_per_class_F1"] = pd.DataFrame(per).T.reset_index().rename(columns={"index": "celltype"})
        nd = P[P.cohort == "Naldini"]
        if "T2" in c.tasks and len(nd):
            V = list(nd.variant.unique())
            tables["T2_AUROC"] = patient_bootstrap(nd, lambda x: _auc(x.malignant, x.mal_score), V, c.n_boot, c.seed, "scGPT-frozen")[0]
            post = nd[nd.stage == "post"]
            tables["T2_AUROC_post"] = patient_bootstrap(post, lambda x: _auc(x.malignant, x.mal_score), V, c.n_boot, c.seed, "scGPT-frozen")[0]
            tables["T2_FPR_at_TPR90"] = patient_bootstrap(nd, lambda x: fpr_at_tpr(x.malignant, x.mal_score, c.target_tpr), V, c.n_boot, c.seed, "scGPT-frozen")[0]
            tables["T2_FPR_at_TPR90_post"] = patient_bootstrap(post, lambda x: fpr_at_tpr(x.malignant, x.mal_score, c.target_tpr), V, c.n_boot, c.seed, "scGPT-frozen")[0]
            tables["T2_counts"] = nd[nd.variant == V[0]].groupby(["stage", "malignant"]).size().rename("cells").reset_index()
        # promise check vs best conventional, paired
        verdicts = []
        for key, metric, data, higher in (("T1_AUROC", lambda x: _auc(x.malignant, x.mal_score), vg[vg.malignant.notna()] if len(vg) else vg, True),
                                          ("T2_AUROC", lambda x: _auc(x.malignant, x.mal_score), nd, True),
                                          ("T3_macroF1", lambda x: f1_score(x.celltype, x.ct_pred, average="macro", labels=sorted(x.celltype.unique())),
                                           vg[vg.celltype.isin(self.celltypes)] if len(vg) else vg, True)):
            if key not in tables:
                continue
            t = tables[key]
            conv = t[t.variant.isin(CONVENTIONAL)]
            if conv.empty:
                continue
            best_conv = conv.sort_values("estimate", ascending=not higher).variant.iloc[0]
            ref_tab, _ = patient_bootstrap(data, metric, list(t.variant), c.n_boot, c.seed + 1, best_conv)
            for v in [x for x in t.variant if x.startswith("scGPT+")]:
                rf = t[t.variant == v].iloc[0]; rc = ref_tab[ref_tab.variant == v].iloc[0]
                verdicts.append(dict(task=key, variant=v, estimate=rf.estimate,
                                     vs_frozen=rf["diff_vs_scGPT-frozen"], vs_frozen_lo=rf["diff_lo_vs_scGPT-frozen"],
                                     best_conventional=best_conv, vs_conv=rc[f"diff_vs_{best_conv}"], vs_conv_lo=rc[f"diff_lo_vs_{best_conv}"],
                                     promise=bool(rf["diff_lo_vs_scGPT-frozen"] > 0 and rc[f"diff_lo_vs_{best_conv}"] > 0)))
        tables["PROMISE"] = pd.DataFrame(verdicts)
        self.recommend(tables)
        for k, t in tables.items():
            t.to_csv(self.out / f"{k}.csv", index=False)
        json.dump(self.logs, open(self.out / "training_logs.json", "w"), indent=1, default=float)
        self.write_report(tables)
        return tables

    def recommend(self, tables):
        """Pick the model to ship using ONLY within-van-Galen cross-validation (T1 AUROC, then T3 macro-F1),
        never the Naldini test set. Copies it to aml_adapter_final.pt."""
        import shutil
        cand = {"scGPT+task": "aml_adapter_task.pt", "scGPT+SSL+task": "aml_adapter_ssl_task.pt"}
        score = {}
        for v in cand:
            t1 = tables.get("T1_AUROC"); t3 = tables.get("T3_macroF1")
            a = t1.set_index("variant").estimate.get(v, np.nan) if t1 is not None else np.nan
            b = t3.set_index("variant").estimate.get(v, np.nan) if t3 is not None else np.nan
            score[v] = (np.nan_to_num(a, nan=-1), np.nan_to_num(b, nan=-1))
        best = max(score, key=score.get)
        src = self.out / cand[best]
        if src.exists():
            shutil.copy(src, self.out / "aml_adapter_final.pt")
            (self.out / "RECOMMENDED_MODEL.txt").write_text(
                f"{best} -> aml_adapter_final.pt (chosen on van Galen cross-validation: T1 AUROC, T3 macro-F1 = {score[best]})\n")
            self.log(f"[model] recommended {best}; copied to aml_adapter_final.pt")

    def write_report(self, tables):
        c = self.cfg
        lines = [f"# AML adapter benchmark ({c.extra.get('profile', 'custom')} profile)", ""]
        if c.extra.get("profile") in ("smoke", "cpu-mini"):
            lines += [f"> **{c.extra['profile']} run: pipeline check only. These numbers are not a result.**", ""]
        lines += ["Primary metrics: T1 AUROC (van Galen, patient-held-out), T2 AUROC (Naldini NPM1 genotype, trained on van Galen only), "
                  "T3 macro-F1 (van Galen cell states). 95% CIs resample patients.", ""]
        for k, t in tables.items():
            if t is None or t.empty:
                continue
            lines += [f"## {k}", "", t.round(3).to_markdown(index=False), ""]
        lines += ["## Training logs (SSL held-out masked loss should fall)", "", "```", json.dumps(self.logs, indent=1, default=float), "```", ""]
        (self.out / "REPORT.md").write_text("\n".join(lines))
        self.log(f"[report] {self.out / 'REPORT.md'}")

    def run(self):
        t0 = time.time()
        self.run_within()
        self.run_cross()
        tables = self.evaluate()
        self.log(f"[done] {(time.time()-t0)/60:.1f} min")
        return tables
