# A competing-risks adapter lets tabular foundation models predict leukemic transformation in myelodysplastic syndromes

*Draft. Numbers marked ⟨…⟩ are filled from `paper/results/` after the pre-registered run.*

## Abstract
**Background.** The Molecular International Prognostic Scoring System (IPSS-M) is the reference prognostic model for
myelodysplastic syndromes (MDS). It was fitted to leukemia-free survival, a composite of death and transformation to
acute myeloid leukemia (AML). Tabular foundation models (TFMs) such as TabPFN predict well on small clinical tables, but
they do not handle censored or competing-risk outcomes.
**Methods.** We designed an MDS adapter that lets an unmodified TFM predict cause-specific cumulative incidence. It has
three parts: jackknife pseudo-observation targets for each competing cause and horizon, anchoring on the IPSS-M category
incidence, and a coherence step. In the IPSS-M derivation cohort (cBioPortal `mds_iwg_2022`, n = 2,428 with IPSS-M and
follow-up; 437 transformations, 799 deaths without transformation), we pre-registered four benchmarks and compared
TabPFN v2 and TabICL v2 with the adapter against IPSS-M, IPSS-R, gradient boosting and ablations, using 5-fold
cross-validation.
**Results.** ⟨…⟩
**Conclusions.** ⟨…⟩

## 1 Introduction
- IPSS-M (Bernard et al., 2022) combines haemoglobin, platelets, marrow blasts, IPSS-R cytogenetics and 31 genes in a Cox
  model for leukemia-free survival. It improved discrimination over IPSS-R and has been independently validated.
- Treatment decisions in lower-risk MDS hinge on the risk of **transformation**, not of death from other causes. A score
  fitted to the composite endpoint mixes the two, and most composite events are deaths.
- Machine-learning MDS models (random survival forests: Nazha et al., 2021; the Spanish MDS group's AIPSS-MDS and molecular
  follow-up) were trained from scratch on single cohorts, and their gains were reported against IPSS-R or IPSS-M on
  different data.
- TFMs (TabPFN, Hollmann et al., 2025; TabICL) are pretrained on synthetic tasks and predict by in-context learning. They
  are strong when data are scarce, but have no survival or competing-risk interface.
- **Contribution:**
  1. A backbone-agnostic competing-risks adapter for TFMs.
  2. A pre-registered, clinically motivated benchmark on the IPSS-M cohort.
  3. Evidence on whether the TFM backbone, IPSS-M anchoring, curated inputs or competing-risk targets drive any gain.

## 2 Methods
**Cohort.** cBioPortal `mds_iwg_2022`: 3,323 treatment-naive MDS samples profiled with a 152-gene panel. Eligibility:
an IPSS-M score and category and LFS follow-up (n = 2,428).

**Outcome.** Time is LFS in months.
- Cause 1, AML transformation: an LFS event that does not coincide with death, or an LFS event in a living patient
  (n = 437).
- Cause 2, death without transformation (n = 799).
- Censored (n = 1,192).

**Inputs.**
- *Curated set (50 variables, pre-specified):*
  - IPSS-M score.
  - Haemoglobin, platelets, ANC, WBC, monocytes, marrow and blood blasts, age, sex, therapy-related MDS.
  - IPSS-R cytogenetic risk, complex karyotype, and seven copy-number arm events.
  - 15 IPSS-M main-effect genes, MLL-PTD, FLT3-ITD, and the residual-gene count.
  - TP53 multi-hit and locus loss.
  - Maximum VAF and the VAF of eight genes.
  - Driver count.
- *Full set:* 102 engineered features (ablation).

**MDS adapter.** For each training fold and each cause k ∈ {AML, death} and horizon τ ∈ {24, 60} months:
1. *Pseudo-observations* of the Aalen–Johansen cumulative incidence F_k(τ): θ_i = n·F̂_k(τ) − (n−1)·F̂_k^(−i)(τ). These turn
   censored competing-risk data into a regression target whose conditional mean is F_k(τ | x) under independent censoring.
2. *Anchoring*: the backbone regresses θ_i − B_k(τ | IPSS-M category), where B is the Aalen–Johansen incidence of the
   patient's IPSS-M category in the training fold. The prediction is B + residual.
3. *Coherence*: clip to [0, 1], enforce F_k(60) ≥ F_k(24), and rescale if F_AML + F_death > 1.

**Backbones.**
- TabPFN v2: default regressor checkpoint, 4 ensemble members, no fine-tuning.
- TabICL v2: regressor checkpoint, default settings.
- XGBoost: depth 3, η = 0.03, 300 trees, as a non-foundation backbone with the identical adapter.

**Comparators.**
- IPSS-M: the continuous score for ranking; category incidence for calibration.
- IPSS-R.
- IPSS-M+: a cause-specific gradient-boosted Cox model that uses the IPSS-M score as an offset.

**Ablations.** No anchoring; the full feature set; an all-cause (LFS) target.

**Benchmarks (pre-registered, `paper/PROTOCOL.md`).**
- B1: transformation incidence at 2 and 5 years, all patients.
- B2: the same, within IPSS-M lower-risk patients.
- B3: death without transformation.
- B4: data efficiency at 10–100% of the training data.

**Metrics.**
- Cause-specific time-dependent AUC: Blanche definition 2, inverse-probability-of-censoring weighted.
- IPCW Brier score.
- 95% CIs from 1,000 patient bootstraps of pooled out-of-fold predictions, with paired differences against IPSS-M.
- IPSS-M is evaluated in-sample (it was derived on this cohort), so the comparisons are conservative.

## 3 Results
⟨B1 table and figure⟩ ⟨B2⟩ ⟨B3⟩ ⟨B4 curve⟩ ⟨ablations⟩ ⟨calibration⟩

## 4 Discussion
⟨…⟩

**Limitations.**
- Single cohort, internal cross-validation; external replication is required.
- The transformation date is derived from LFS and OS times.
- Treatment (hypomethylating agents, transplant) is not modelled.
- One cross-validation repeat (CPU budget).
- The IPSS-M score is an input, so IPSS-M must be computed first.

**Code and data availability.**
- Data: public, cBioPortal `mds_iwg_2022`.
- Code, protocol (committed before results) and outputs: `mds-risk/` in this repository.
- TabPFN v2 weights: Prior Labs (Hugging Face `Prior-Labs/TabPFN-v2-reg`, Prior Labs licence).
- TabICL v2 weights: `jingang/TabICL` (BSD-3).

## References
1. Bernard E, et al. Molecular International Prognostic Scoring System for Myelodysplastic Syndromes. *NEJM Evidence* 2022.
2. Greenberg PL, et al. Revised International Prognostic Scoring System for MDS. *Blood* 2012.
3. Nazha A, et al. Personalized prediction model to risk stratify patients with MDS. *J Clin Oncol* 2021.
4. Mosquera Orgueira A, et al. Machine learning improves risk stratification in myelodysplastic neoplasms (Spanish Group of MDS). 2023.
5. Bernard E, et al. Molecular taxonomy of myelodysplastic syndromes and its clinical implications. *Blood* 2024.
6. Hollmann N, et al. Accurate predictions on small data with a tabular foundation model. *Nature* 2025.
7. Qu J, et al. TabICL: a tabular foundation model for in-context learning on large data. *ICML* 2025.
8. Andersen PK, Perme MP. Pseudo-observations in survival analysis. *Stat Methods Med Res* 2010.
9. Blanche P, Dartigues JF, Jacqmin-Gadda H. Estimating and comparing time-dependent areas under ROC curves for censored event times with competing risks. *Stat Med* 2013.
