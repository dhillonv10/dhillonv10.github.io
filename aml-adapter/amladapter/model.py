"""Inference API for a trained AML adapter.

    from amladapter.model import AMLAdapterModel
    m = AMLAdapterModel.load("results/aml_adapter_final.pt", scgpt_dir="models/scGPT-human", device="cuda")
    df = m.predict(adata)          # adata.X = raw UMI counts, var_names = gene symbols
    # df columns: malignant_prob, malignant_logit, celltype_pred, celltype_prob ; m.embed(adata) -> adapted embeddings
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import torch

from .adapters import AdapterSet
from .backbone import embed, gene_ids_for, load_scgpt
from .train import TaskHeads, predict


class AMLAdapterModel:
    def __init__(self, model, vocab, cfg, adapters: AdapterSet, heads: TaskHeads, celltypes, max_len: int):
        self.model, self.vocab, self.cfg = model, vocab, cfg
        self.adapters, self.heads, self.celltypes, self.max_len = adapters, heads, list(celltypes), max_len

    @classmethod
    def load(cls, path, scgpt_dir, device="cpu"):
        ck = torch.load(path, map_location="cpu", weights_only=False)
        model, vocab, cfg = load_scgpt(scgpt_dir, device=device, verbose=False)
        ad = AdapterSet(**ck["adapter_config"]); ad.load_state_dict(ck["adapters"]); ad.to(device).attach(model)
        for p in model.parameters():
            p.requires_grad_(False)
        heads = TaskHeads(ck["d_model"], len(ck["celltypes"])); heads.load_state_dict(ck["heads"]); heads.to(device).eval()
        return cls(model, vocab, cfg, ad, heads, ck["celltypes"], ck["max_len"])

    def _inputs(self, adata):
        gid = gene_ids_for(adata.var_names, self.vocab)
        keep = np.flatnonzero(gid >= 0)
        if len(keep) < min(500, 0.5 * adata.n_vars):
            raise ValueError(f"only {len(keep)}/{adata.n_vars} genes match the scGPT vocabulary: are var_names gene symbols?")
        return adata.X[:, keep], gid[keep]

    def predict(self, adata, batch_size=64, seed=0) -> pd.DataFrame:
        X, gid = self._inputs(adata)
        lm, lc, _ = predict(self.model, self.heads, X, gid, self.vocab, self.cfg, max_len=self.max_len, batch_size=batch_size, seed=seed)
        p = np.exp(lc - lc.max(1, keepdims=True)); p /= p.sum(1, keepdims=True)
        return pd.DataFrame(dict(malignant_logit=lm, malignant_prob=1 / (1 + np.exp(-lm)),
                                 celltype_pred=np.array(self.celltypes)[p.argmax(1)], celltype_prob=p.max(1)), index=adata.obs_names)

    def embed(self, adata, batch_size=64, seed=0) -> np.ndarray:
        X, gid = self._inputs(adata)
        return embed(self.model, X, gid, self.vocab, self.cfg, max_len=self.max_len, batch_size=batch_size, seed=seed)
