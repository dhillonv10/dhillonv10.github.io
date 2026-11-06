# A competing-risks adapter lets tabular foundation models predict leukemic transformation in myelodysplastic syndromes

*Draft. All numbers come from `paper/results/` (the pre-registered run). Protocol: `paper/PROTOCOL.md`, committed before any result (git c1af781).*

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
**Results.** The primary model (TabPFN + adapter) predicted 5-year AML transformation better than IPSS-M: AUC 0.777 vs
0.746, Δ +0.030 (95% CI +0.017 to +0.044). At 2 years the gain was +0.015 (+0.002 to +0.027). Among IPSS-M lower-risk
patients, where IPSS-M discriminates poorly (AUC 0.614), the gain was +0.076 (+0.026 to +0.132): the model's top third had
an 18% 5-year transformation incidence against 6% in the other two thirds. Competing-risk targets were essential; an
all-cause target did not beat IPSS-M. A foundation backbone outperformed gradient boosting only when training data were
scarce: +0.036 (+0.021 to +0.054) with 10% of the data, and no difference at ≥50%. Contrary to our pre-registered
expectation, anchoring on IPSS-M categories reduced performance. The same adapter without anchoring reached AUC 0.794
overall and 0.748 in lower-risk patients.
**Conclusions.** Turning censored competing-risk outcomes into pseudo-observation targets is enough for an off-the-shelf
TFM to predict leukemic transformation better than IPSS-M in its derivation cohort, with the largest gain in lower-risk
disease. TFMs mainly add value in small cohorts. External validation is needed.

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
**Cohort.** 2,428 patients: 437 transformations, 799 deaths without transformation, 1,192 censored. In the lower-risk
subgroup (IPSS-M Very-Low, Low or Moderate-Low; n = 1,377) there were 64 transformations by 2 years and 97 by 5 years.

**B1: AML transformation, all patients (primary).** Five-year AUC with 95% CI; Δ is the paired difference from IPSS-M.

| Model | AUC (95% CI) | Δ vs IPSS-M (95% CI) |
|---|---|---|
| IPSS-R | 0.684 (0.653–0.718) | −0.062 (−0.082 to −0.041) |
| IPSS-M | 0.746 (0.720–0.773) | — |
| IPSS-M+ (XGB cause-specific Cox) | 0.782 (0.758–0.806) | +0.035 (+0.022 to +0.049) |
| **TabPFN + adapter (primary)** | **0.777 (0.749–0.802)** | **+0.030 (+0.018 to +0.044)** |
| TabICL + adapter | 0.782 (0.755–0.806) | +0.035 (+0.016 to +0.053) |
| XGBoost + adapter | 0.776 (0.751–0.802) | +0.030 (+0.010 to +0.052) |
| TabPFN, no anchoring | 0.794 (0.768–0.817) | +0.047 (+0.029 to +0.065) |

At 2 years: IPSS-M 0.780; TabPFN + adapter 0.794, Δ +0.015 (+0.002 to +0.027). **H1 is supported at both horizons.**

**B2: transformation within IPSS-M lower-risk patients.**
- At 5 years, IPSS-M discriminated poorly (AUC 0.614). TabPFN + adapter reached 0.690, Δ **+0.076 (+0.026 to +0.132)**.
  **H2 is supported at 5 years.**
- At 2 years (64 events): Δ +0.039 (−0.027 to +0.112), not significant.
- Variants with the largest gains: no anchoring 0.748 (+0.134); IPSS-M+ 0.730 (+0.116).
- Clinically (Fig. 3), the TabPFN + adapter top third of lower-risk patients had an 18% 5-year incidence, against 6% in
  each of the other two thirds. IPSS-M score tertiles separated 14% / 9% / 7%.

**B3: death without transformation.** At 5 years: IPSS-M 0.628, TabPFN + adapter 0.717, Δ +0.089 (+0.067 to +0.113).
Part of this gain is expected, because the adapter's inputs include age and IPSS-M deliberately excludes it.

**B4: data efficiency (H3).** TabPFN minus XGBoost with the identical adapter:
- 10% of each training fold (≈190 patients): **+0.036 (+0.021 to +0.054)**.
- 25%: +0.017 (−0.003 to +0.034).
- 50%: 0.000 (−0.019 to +0.016).
- 100%: 0.000 (−0.016 to +0.014).

TabPFN + adapter matched IPSS-M with 25% of the data (≈485 patients) and exceeded it with 50% (+0.011, +0.001 to +0.022)
(Fig. 2). **H3 holds only in the small-data regime.**

**Ablations (H4).** Paired differences, TabPFN + adapter minus each variant, AML at 5 years:
- All-cause target: **+0.039 (+0.022 to +0.054)**. Competing-risk targets are needed; the all-cause variant did not beat
  IPSS-M (Δ −0.008).
- Full 102-feature input: +0.008 (+0.003 to +0.013). The curated input helps.
- No IPSS-M anchoring: **−0.017 (−0.028 to −0.006)**. Anchoring hurt, against our pre-registered expectation, and did so
  consistently: in lower-risk patients −0.058 (−0.093 to −0.024), for death at 5 years −0.015 (−0.026 to −0.005).
- TabICL instead of TabPFN: −0.005 (−0.017 to +0.007). The adapter is backbone-agnostic.

**Calibration.** 5-year IPCW Brier score for AML: TabPFN + adapter 0.143, no anchoring 0.140, IPSS-M categories 0.150.
For death: 0.209, 0.203 and 0.230 respectively. Predicted and observed incidence agreed across deciles (Fig. 4).

![](results/figures/fig1_forest.png)
![](results/figures/fig2_data_efficiency.png)
![](results/figures/fig3_lower_risk_cif.png)
![](results/figures/fig4_calibration.png)

## 4 Discussion
- **Main finding.** A simple output adapter, pseudo-observations of cause-specific cumulative incidence, lets an
  unmodified tabular foundation model predict leukemic transformation better than IPSS-M. The largest gain is in IPSS-M
  lower-risk patients, the group in which predicting transformation drives decisions about early disease-modifying
  therapy, and the group in which IPSS-M discriminates least.
- **Why.** IPSS-M targets leukemia-free survival, where most events are deaths. Modelling transformation and death as
  separate causes is what produced the gain. Collapsing them again (the all-cause ablation) removed it, and a
  cause-specific gradient-boosted Cox model gained about as much. **The competing-risk formulation, not the foundation
  model itself, is the main ingredient.**
- **Where foundation models help.** With the full cohort, TabPFN, TabICL and XGBoost were indistinguishable. TabPFN's
  advantage appeared with about 190 training patients, the size of a typical single-centre MDS cohort. That supports
  TFMs as a way for small centres to build local transformation models.
- **A negative pre-registered result.** We expected IPSS-M anchoring to help; it hurt. The IPSS-M score was still an input
  in the unanchored model, so the backbone could use it freely. Forcing predictions around six category-level baselines
  appears to constrain rather than regularise. We report the anchored model as primary because it was pre-registered.
  The unanchored variant (AUC 0.794 overall; 0.748 in lower-risk patients) should be the default in future work, which
  any replication should treat as a new, pre-specified choice.
- **Relation to prior work.** IPSS-M+ (gradient boosting from the IPSS-M offset; our earlier analysis) performed similarly
  to the adapter models at full data. The two approaches agree that IPSS-M leaves transformation-specific signal
  unexploited. The molecular-taxonomy interactions reported not to improve IPSS-M address a different question
  (composite endpoints).


**Limitations.**
- Single cohort, internal cross-validation; external replication is required.
- The transformation date is derived from LFS and OS times.
- Treatment (hypomethylating agents, transplant) is not modelled.
- One cross-validation repeat (CPU budget). Bootstrap CIs reflect patient sampling, not fold-assignment variability.
- Gains on death without transformation partly reflect age, which IPSS-M excludes by design.
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
