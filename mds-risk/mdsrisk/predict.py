"""Score new patients with a trained IPSS-M+ model.

Inputs use the cBioPortal `mds_iwg_2022` column names (see README, "Input format"):
    clinical : one row per patient: sampleId, AGE, SEX, HB, PLT, ANC, WBC, MONOCYTES, BM_BLAST, PB_BLAST, MDS_TYPE,
               CYTO_IPSSR, COMPLEX_KARYOTYPE, CNACS_CHRARM_LOSS/GAIN/UPD, CHR_TP53_LOCUS, FLT3_ITD, MLL_PTD,
               IPSSM_SCORE (from the official IPSS-M calculator), MUTATION_COUNT (any non-empty value = sequenced)
    mutations: one row per oncogenic mutation: sampleId, gene, vaf (0-1)
Missing clinical values are allowed (imputed); unknown genes are ignored.

    from mdsrisk.predict import load, score
    m = load("results/models/LFS_ipssm_plus.pkl")
    out = score(m, clinical_df, mutations_df)     # columns: risk, category, ipssm_score
"""
from __future__ import annotations
import pickle
import numpy as np
import pandas as pd

from .features import build


def load(path):
    with open(path, "rb") as fh:
        return pickle.load(fh)


def score(bundle, clinical: pd.DataFrame, mutations: pd.DataFrame) -> pd.DataFrame:
    d = clinical.copy()
    for c in ("SEX", "MDS_TYPE", "CYTO_IPSSR", "COMPLEX_KARYOTYPE", "CNACS_CHRARM_LOSS", "CNACS_CHRARM_GAIN", "CNACS_CHRARM_UPD",
              "CHR_TP53_LOCUS", "FLT3_ITD", "MLL_PTD", "MUTATION_COUNT"):
        if c not in d:
            d[c] = np.nan
    mut = mutations.copy()
    mut["driver"] = mut.get("driver", True)
    mut["vaf"] = pd.to_numeric(mut["vaf"], errors="coerce")
    X, _ = build(d, mut, min_gene_freq=0.0, vaf_gene_freq=0.0)
    cols = bundle["feature_columns"]
    F = X.reindex(columns=cols)
    gene_cols = [c for c in cols if c.startswith(("mut_", "vaf_")) and c not in X]
    sequenced = d.MUTATION_COUNT.notna() | d.sampleId.isin(mut.sampleId)
    F.loc[sequenced.to_numpy(), gene_cols] = 0.0          # sequenced but gene not mutated
    F["IPSSM_SCORE"] = pd.to_numeric(d["IPSSM_SCORE"], errors="coerce")
    if F.IPSSM_SCORE.isna().any():
        raise ValueError("IPSSM_SCORE is required for every patient (IPSS-M+ starts from it)")
    risk = bundle["model"].risk(F)
    cats = np.array(bundle["categories"])[np.searchsorted(bundle["category_cuts"], risk, side="right")]
    return pd.DataFrame(dict(risk=risk, category=cats, ipssm_score=F.IPSSM_SCORE), index=d.index)
