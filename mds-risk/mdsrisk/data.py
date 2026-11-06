"""Fetch the IPSS-M cohort (cBioPortal study mds_iwg_2022) and build one row per patient.

Outcomes
    LFS  leukemia-free survival (IPSS-M's primary endpoint): event = AML transformation or death
    OS   overall survival
    AMLt AML transformation, cause-specific: LFS event that precedes death (or with the patient alive);
         death without recorded transformation is censored (competing event)
"""
from __future__ import annotations
import json
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

API = "https://www.cbioportal.org/api"
STUDY = "mds_iwg_2022"


def _req(url, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method="POST" if body is not None else "GET",
                                 headers={"Accept": "application/json", "Content-Type": "application/json"})
    for a in range(5):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.loads(r.read())
        except Exception:
            if a == 4:
                raise
            time.sleep(5 * (a + 1))


def fetch(cache_dir: str | Path = "data") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (clinical one row per sample, driver/passenger mutations). Cached as JSON in cache_dir."""
    cache = Path(cache_dir); cache.mkdir(parents=True, exist_ok=True)
    files = {"SAMPLE": cache / "clin_SAMPLE.json", "PATIENT": cache / "clin_PATIENT.json", "MUT": cache / "mutations.json"}
    for t in ("SAMPLE", "PATIENT"):
        if not files[t].exists():
            files[t].write_text(json.dumps(_req(f"{API}/studies/{STUDY}/clinical-data?clinicalDataType={t}&projection=SUMMARY&pageSize=10000000")))
    if not files["MUT"].exists():
        files["MUT"].write_text(json.dumps(_req(f"{API}/molecular-profiles/{STUDY}_mutations/mutations/fetch?projection=DETAILED",
                                                {"sampleListId": f"{STUDY}_all"})))
    s = pd.DataFrame(json.loads(files["SAMPLE"].read_text())).pivot_table(index=["patientId", "sampleId"], columns="clinicalAttributeId", values="value", aggfunc="first").reset_index()
    p = pd.DataFrame(json.loads(files["PATIENT"].read_text())).pivot_table(index="patientId", columns="clinicalAttributeId", values="value", aggfunc="first").reset_index()
    clin = s.merge(p, on="patientId", suffixes=("", "_p"))
    m = json.loads(files["MUT"].read_text())
    mut = pd.DataFrame([dict(sampleId=x["sampleId"], gene=x["gene"]["hugoGeneSymbol"], driver=x["driverFilter"] == "Putative_Driver",
                             alt=x.get("tumorAltCount"), ref=x.get("tumorRefCount"), type=x["mutationType"], protein=x.get("proteinChange"))
                        for x in m])
    mut["vaf"] = mut.alt / (mut.alt + mut.ref)
    return clin, mut


NUMERIC = ["AGE", "HB", "PLT", "ANC", "WBC", "MONOCYTES", "BM_BLAST", "PB_BLAST", "RINGED_SIDEROBLASTS", "IPSSM_SCORE", "IPSSR_SCORE",
           "LFS_MONTHS", "OS_MONTHS"]


def outcomes(clin: pd.DataFrame) -> pd.DataFrame:
    d = clin.copy()
    for c in NUMERIC:
        if c in d:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    lfs_e = d.LFS_STATUS.astype(str).str.startswith("1")
    os_e = d.OS_STATUS.astype(str).str.startswith("1")
    d["lfs_event"] = np.where(d.LFS_MONTHS.notna(), lfs_e.astype(float), np.nan)
    d["os_event"] = np.where(d.OS_MONTHS.notna(), os_e.astype(float), np.nan)
    # AML transformation (cause-specific): an LFS event that is not the death itself
    same_time = (d.OS_MONTHS - d.LFS_MONTHS).abs() < 1e-6
    amlt = lfs_e & ~(os_e & same_time)
    d["amlt_event"] = np.where(d.LFS_MONTHS.notna(), amlt.astype(float), np.nan)
    d["AMLT_MONTHS"] = d.LFS_MONTHS
    return d


ENDPOINTS = {"LFS": ("LFS_MONTHS", "lfs_event"), "OS": ("OS_MONTHS", "os_event"), "AMLt": ("AMLT_MONTHS", "amlt_event")}
