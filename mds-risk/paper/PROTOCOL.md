# Pre-registered protocol: MDS competing-risks adapter for tabular foundation models

Written and committed **before any result of this benchmark was computed**. The git timestamp of this file is the
registration. Anything not listed here, or changed after results, will be labelled *post hoc* in the paper.

Prior knowledge that motivated it (from `study_results/`, same cohort): IPSS-M+ (XGBoost boosted from the IPSS-M score)
improved AML-transformation discrimination (ΔC +0.022, 95% CI +0.012 to +0.032) but not LFS or OS.

## Hypotheses
- **H1 (primary).** A tabular foundation model (TabPFN v2) equipped with the MDS competing-risks adapter predicts the
  2-year and 5-year cumulative incidence of AML transformation better than IPSS-M.
- **H2.** The same holds within IPSS-M lower-risk patients (Very-Low, Low, Moderate-Low).
- **H3.** The foundation-model backbone matters: with the identical adapter, TabPFN beats a gradient-boosting backbone
  (XGBoost), most clearly when training data are scarce (B4).
- **H4.** Each adapter component matters (ablations): IPSS-M anchoring, the curated input set, and competing-risk targets.

## Data
cBioPortal `mds_iwg_2022` (IWG-PM; Bernard et al., NEJM Evidence 2022). Eligible: patients with an IPSS-M score,
an IPSS-M category, and LFS/OS follow-up (n ≈ 2,393).
**Competing-risks outcome.** The time is LFS_MONTHS, with three possible statuses:
- cause 1, AML transformation: an LFS event that does not coincide with death, or an LFS event while the patient is alive;
- cause 2, death without transformation: an LFS event that coincides with the OS death time;
- 0, censored.

## Inputs
**Curated set (primary; chosen a priori, from IPSS-M's inputs plus clone-size and blood-count information):**
- IPSS-M score.
- Clinical: haemoglobin, platelets, ANC, WBC, monocytes, BM blasts, PB blasts, age, sex, therapy-related MDS.
- Cytogenetics: IPSS-R cytogenetic risk, complex karyotype, del5q, del7, del17p, del20q, gain8, del12p, del11q.
- Genes: mutation status of the 16 IPSS-M main-effect genes (ASXL1, CBL, DNMT3A, ETV6, EZH2, FLT3, IDH2, KRAS,
  NPM1, NRAS, RUNX1, SF3B1, SRSF2, TP53, U2AF1, MLL-PTD), plus FLT3-ITD.
- Residual-gene count: the number of mutated IPSS-M residual genes (BCOR, BCORL1, CEBPA, ETNK1, GATA2, GNB1, IDH1,
  NF1, PHF6, PPM1D, PRPF8, PTPN11, SETBP1, STAG2, WT1).
- TP53 state: multi-hit, TP53 locus loss.
- Clone size: maximum VAF overall, and VAF of TP53, SF3B1, ASXL1, RUNX1, U2AF1, SRSF2, DNMT3A, TET2.
- Burden: number of driver mutations.

**Full set (ablation):** all 102 features in `mdsrisk/features.py`, plus the IPSS-M score.

## Models (each outputs CIF_AML(τ) and CIF_death(τ) for τ = 24 and 60 months)
| ID | Model |
|---|---|
| M0 | IPSS-M category → Aalen–Johansen CIF per category (fitted in the training fold). Its ranking for AUC is the continuous IPSS-M score. |
| M1 | IPSS-R category → Aalen–Johansen CIF per category |
| M2 | IPSS-M+ XGBoost, cause-specific Cox, boosted from the IPSS-M offset (from `study_results`); ranking only |
| M3 | **TabPFN v2 + MDS adapter** (curated inputs, IPSS-M anchoring, competing-risk pseudo-value targets): **primary** |
| M4 | XGBoost + the identical MDS adapter (backbone ablation) |
| M5 | TabPFN v2 + adapter **without** IPSS-M anchoring (anchoring ablation) |
| M6 | TabPFN v2 + adapter with the **full** 102-feature input (input ablation) |
| M7 | TabPFN v2, **all-cause** target: the LFS pseudo-value, used to rank AML risk (competing-risk ablation) |
| M8 | TabICL v2 + the identical MDS adapter (second backbone; secondary) |

**MDS adapter, defined:**
1. **Targets.** In each training fold, jackknife pseudo-observations of the Aalen–Johansen CIF for each cause at τ.
2. **Anchoring.** The baseline is the Aalen–Johansen CIF of the patient's IPSS-M category (training fold); the
   backbone regresses the residual (pseudo-value minus baseline), and the prediction is baseline + residual.
3. **Coherence.** Each CIF is clipped to [0, 1], made monotone across τ (CIF(60) ≥ CIF(24)), and the two causes
   rescaled jointly if CIF_AML + CIF_death > 1.

The backbone is used as released (in-context learning, no weight updates). TabPFN: v2 default regressor checkpoint,
n_estimators = 4. TabICL: v2 regressor checkpoint, default settings. XGBoost: squared-error regression on the same
targets, depth 3, η = 0.03, 300 rounds, subsample 0.8.

## Benchmarks
| ID | Task | Patients | Metric |
|---|---|---|---|
| **B1 (primary)** | AML-transformation CIF at 24 and 60 months | all eligible | cause-specific time-dependent AUC (IPCW) |
| B2 | the same | IPSS-M Very-Low / Low / Moderate-Low only (model trained on all training patients) | AUC |
| B3 | death-without-transformation CIF at 24 and 60 months | all eligible | AUC |
| B4 | B1 at 60 months with 10%, 25%, 50% and 100% of each training fold (stratified subsample, 3 draws) | all eligible | AUC |
| Calibration (all) | | | IPCW Brier score for CIF at τ, and calibration slope |

**Cause-specific AUC at τ** (Blanche et al. 2013, definition 2):
- Cases: T ≤ τ with the cause of interest.
- Controls: T > τ, or T ≤ τ with the competing cause.
- Weights: inverse probability of censoring, from Kaplan–Meier of the censoring distribution.

The **Brier score** is IPCW, with the observed status at τ for the cause of interest.

## Validation and statistics
- **Cross-validation:** 5-fold, stratified by cause; one repeat (CPU budget), with a fixed seed of 0.
- **Out-of-fold predictions:** pooled over folds.
- **Confidence intervals:** 1,000-sample patient bootstrap of the pooled out-of-fold predictions, with paired
  differences against M0 (IPSS-M).
- **H1 is supported** if M3's AUC exceeds M0's at τ = 60 with the 95% CI of the difference above 0 (τ = 24 is a
  co-primary horizon and is reported alongside).
- **H2:** the same comparison within the lower-risk subgroup.
- **H3:** M3 vs M4, at full data and in B4.
- **H4:** M3 vs M5, M6 and M7.
- No multiplicity correction. Every test is listed here, and all of them are reported.
- IPSS-M was fitted on these patients, so M0 has an in-sample advantage; all learned models are out-of-sample.

## Reporting
Every benchmark and model above is reported, including nulls. Deviations from this protocol (e.g. a backbone that cannot
run) are listed explicitly.
