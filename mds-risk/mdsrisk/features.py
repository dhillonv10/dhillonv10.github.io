"""Feature construction (one row per patient). Missing values stay NaN; models impute inside each training fold."""
from __future__ import annotations
import warnings

import numpy as np
import pandas as pd
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

# genes used by IPSS-M (Bernard et al. 2022): 16 main-effect genes + 15 "residual" genes
IPSSM_MAIN = ["ASXL1", "CBL", "DNMT3A", "ETV6", "EZH2", "FLT3", "IDH2", "KRAS", "NPM1", "NRAS", "RUNX1", "SF3B1", "SRSF2", "TP53", "U2AF1", "MLL_PTD"]
IPSSM_RESIDUAL = ["BCOR", "BCORL1", "CEBPA", "ETNK1", "GATA2", "GNB1", "IDH1", "NF1", "PHF6", "PPM1D", "PRPF8", "PTPN11", "SETBP1", "STAG2", "WT1"]
CYTO_ORDER = {"Very-Good": 0, "Good": 1, "Int": 2, "Poor": 3, "Very-Poor": 4}
ARM_LOSS = {"del5q": {"5q", "5"}, "del7": {"7", "7q"}, "del17p": {"17p", "17"}, "del20q": {"20q", "20"}, "del12p": {"12p", "12"},
            "del11q": {"11q", "11"}, "del13q": {"13q", "13"}, "del18": {"18", "18q"}, "del3p": {"3p", "3"}, "del4q": {"4q", "4"}}
ARM_GAIN = {"gain8": {"8", "8q"}, "gain21": {"21", "21q"}, "gain1q": {"1q"}, "gain9q": {"9q", "9"}}
ARM_UPD = {"upd17p": {"17p"}, "upd4q": {"4q"}, "upd11q": {"11q"}, "upd7q": {"7q"}, "upd1p": {"1p"}, "upd14q": {"14q"}, "upd21q": {"21q"}}
CLINICAL = ["AGE", "HB", "PLT", "ANC", "WBC", "MONOCYTES", "BM_BLAST", "PB_BLAST"]


def _tokens(x):
    return set() if not isinstance(x, str) else {t.strip() for t in x.split(",") if t.strip()}


def build(d: pd.DataFrame, mut: pd.DataFrame, min_gene_freq: float = 0.01, vaf_gene_freq: float = 0.04):
    """Return (X, groups) indexed like d. groups maps a feature-set name to its column list."""
    X = pd.DataFrame(index=d.index)
    for c in CLINICAL:
        X[c] = pd.to_numeric(d[c], errors="coerce")
    X["male"] = (d.SEX == "Male").astype(float)
    X["secondary_MDS"] = np.where(d.MDS_TYPE.isna(), np.nan, (d.MDS_TYPE == "s_t_MDS").astype(float))
    # cytogenetics
    X["cyto_ipssr"] = d.CYTO_IPSSR.map(CYTO_ORDER)
    X["complex_karyotype"] = (d.COMPLEX_KARYOTYPE == "complex").astype(float)
    loss, gain, upd = d.CNACS_CHRARM_LOSS.map(_tokens), d.CNACS_CHRARM_GAIN.map(_tokens), d.CNACS_CHRARM_UPD.map(_tokens)
    for name, arms in ARM_LOSS.items():
        X[name] = loss.map(lambda t: float(bool(t & arms)))
    for name, arms in ARM_GAIN.items():
        X[name] = gain.map(lambda t: float(bool(t & arms)))
    for name, arms in ARM_UPD.items():
        X[name] = upd.map(lambda t: float(bool(t & arms)))
    X["n_cn_events"] = loss.map(len) + gain.map(len) + upd.map(len)
    # mutations (oncogenic / putative driver only, as in IPSS-M)
    sample_of = dict(zip(d.sampleId, d.index))
    drv = mut[mut.driver & mut.sampleId.isin(sample_of)].copy()
    drv["row"] = drv.sampleId.map(sample_of)
    freq = drv.groupby("gene").row.nunique() / len(d)
    genes = sorted(freq[freq >= min_gene_freq].index)
    has = drv.groupby(["row", "gene"]).size().unstack(fill_value=0)
    maxvaf = drv.groupby(["row", "gene"]).vaf.max().unstack()
    sequenced = d.MUTATION_COUNT.notna() | d.sampleId.isin(mut.sampleId)
    for g in genes:
        X[f"mut_{g}"] = has[g].reindex(d.index).fillna(0).clip(upper=1).astype(float) if g in has else 0.0
    for g in sorted(freq[freq >= vaf_gene_freq].index):
        X[f"vaf_{g}"] = maxvaf[g].reindex(d.index).fillna(0.0) if g in maxvaf else 0.0
    X["FLT3_ITD"] = (d.FLT3_ITD == "TRUE").astype(float)
    X["MLL_PTD"] = (d.MLL_PTD == "TRUE").astype(float)
    n_drv = drv.groupby("row").size().reindex(d.index).fillna(0)
    X["n_driver_mutations"] = n_drv
    X["n_mutated_genes"] = drv.groupby("row").gene.nunique().reindex(d.index).fillna(0)
    X["max_vaf_any"] = drv.groupby("row").vaf.max().reindex(d.index).fillna(0)
    # TP53 allelic state (IPSS-M style multi-hit)
    tp = drv[drv.gene == "TP53"].groupby("row")
    n_tp = tp.size().reindex(d.index).fillna(0)
    vaf_tp = tp.vaf.max().reindex(d.index).fillna(0)
    locus = d.CHR_TP53_LOCUS.isin(["del", "cnloh"])
    X["TP53_n_mut"] = n_tp
    X["TP53_locus_loss"] = locus.astype(float)
    X["TP53_multihit"] = ((n_tp >= 2) | ((n_tp >= 1) & locus) | (vaf_tp > 0.55)).astype(float)
    # unsequenced samples: mutation-derived features unknown
    mut_cols = [c for c in X if c.startswith(("mut_", "vaf_", "TP53_")) or c in ("n_driver_mutations", "n_mutated_genes", "max_vaf_any")]
    X.loc[~sequenced.to_numpy(), mut_cols] = np.nan
    groups = {
        "clinical": CLINICAL + ["male", "secondary_MDS"],
        "cytogenetic": ["cyto_ipssr", "complex_karyotype"] + list(ARM_LOSS) + list(ARM_GAIN) + list(ARM_UPD) + ["n_cn_events"],
        "mutation": [c for c in X if c.startswith("mut_")] + ["FLT3_ITD", "MLL_PTD", "n_driver_mutations", "n_mutated_genes"],
        "vaf": [c for c in X if c.startswith("vaf_")] + ["max_vaf_any"],
        "tp53": ["TP53_n_mut", "TP53_locus_loss", "TP53_multihit"],
    }
    groups["all"] = [c for g in groups.values() for c in g]
    groups["all_no_age"] = [c for c in groups["all"] if c != "AGE"]
    return X.astype(float).copy(), groups
