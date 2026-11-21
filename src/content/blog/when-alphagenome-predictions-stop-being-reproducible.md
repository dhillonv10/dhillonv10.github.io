---
title: "When does AlphaGenome 2 stop being reproducible?"
subtitle: "Measuring the smallest predicted effect that survives a meaningless change to the input"
author: Vik Dhillon
pubDatetime: 2026-11-21T09:00:00-08:00
slug: when-alphagenome-predictions-stop-being-reproducible
type: note
draft: false
takeaways:
  - "**There is a floor, and it is measurable without any ground truth.** Shifting the 1 Mb scoring window by 25 kb changes nothing biological, so a prediction that flips direction when you do it was never reading the variant. Below a predicted |log fold change| of 0.01, 29% of directions flip (n=132). Above it, 5 of 218 flip (2.3%, 95% CI 0.9-5.0%), and above 0.05, none of 69 do."
  - "**Report a probability, not a cutoff.** The error rate is a smooth function of effect size, so it can be fitted and calibrated: P(direction is reproducible) reaches 0.90 at |LFC| 0.009 and 0.95 at 0.015, with a Brier score of 0.075 against 0.108 for a flat guess and a worst calibration gap of 0.031."
  - "**Which cell state you condition on is not a detail.** Re-scoring the same variants under the model's built-in cell types reproduced the direction 95% of the time for stem and progenitor cells but only 47% for megakaryocytes, with predicted effects five times smaller."
description: "A ground-truth-free way to find the smallest AlphaGenome 2 prediction worth reporting, and what it leaves usable"
---

## Why this matters before anything else

A hematologist with a germline variant of uncertain significance wants one thing from a sequence model: a direction. Does this change in a promoter or enhancer raise the gene or lower it? That is the question ACMG criteria cannot reach for non-coding variants, and it is the question that decides whether a variant is worth a reporter assay.

A model that answers it is useful. A model that answers it _differently depending on irrelevant details of how you ran it_ is worse than useless, because the answer still looks confident.

So before using AlphaGenome 2 for triage, there is a prior question that has nothing to do with biology: **at what predicted effect size does the model stop saying the same thing twice?** Everything below that size is noise wearing a number, and no amount of clinical framing fixes it.

This note measures that boundary. It needs no ground truth, no held-out labels, and no assumptions about what the right answer is.

## The gap between what was validated and what gets used

AlphaGenome 2 does well on large, literature-anchored variants. Across 17 non-coding variants with an established target gene and direction — TAL1 enhancer insertions, the TERT promoter hotspots, the HBB TATA and CACCC boxes, the GATA2 +9.5 enhancer, the ANKRD26 5′UTR — it called the direction correctly 17 times out of 17 and ranked the correct target gene first 17 times out of 17, from among 8 to 45 competing genes in the window (p = 7.6 × 10⁻⁶ for direction alone).

![Every literature-anchored variant sits far above the floor](/figures/Fig1_validated_regime.webp)

Look at where those variants sit. The smallest is a |log fold change| of 0.054. Most are between 0.1 and 1.2.

Now look at where real variants sit. Scoring every possible single-base change across eight germline predisposition genes gives 5,100 variants, and their median predicted effect is **0.016**.

![The variants a clinic actually sees are 10 to 80 times smaller](/figures/Fig2_where_variants_live.webp)

The validation set and the working set barely overlap. Every claim about the model's accuracy was earned in a regime that contains almost none of the variants anyone will actually look up. That is not a criticism of the validation — those are the variants with known answers — but it means the accuracy figure does not transfer, and nothing published tells you how far down it holds.

## How to find the limit without knowing any answers

The trick is to stop asking whether the model is _right_ and ask whether it is _consistent_.

AlphaGenome 2 scores a variant inside a 1 Mb window of sequence. Where that window is centred is an implementation choice, not biology. Move the centre 25 kb and the variant is still in the window, its gene is still in the window, every regulatory element between them is still in the window. A real effect should not care.

![The perturbation: shift the window, keep the biology](/figures/Fig3_window_shift.webp)

So: score each variant three times, with the window centred on the variant and shifted ±25 kb, and ask how often the **direction** changes. A prediction that cannot survive that is not reading the variant. It is reading the window.

This is a necessary condition, not a sufficient one — a prediction can be perfectly stable and still biologically wrong — but it is the cheapest necessary condition available, and it requires knowing nothing about the truth.

We ran it on 350 variants drawn from all eight genes, stratified across the full range of predicted effect sizes and concentrated where the boundary was expected: 1,050 model calls, about 35 minutes.

## The raw measurement

Plot each variant's predicted effect against how much the three windows disagreed.

![On the dotted line, the noise is the signal](/figures/Fig4_noise_diagonal.webp)

The dotted diagonal is where disagreement equals the effect itself. Points near it are being driven entirely by window position. Every direction flip (the red crosses) sits on or near that line, and they are concentrated at small effect sizes. Above a predicted |LFC| of about 0.015, the cloud pulls away from the diagonal and the crosses stop.

## The floor

Binning by effect size turns that into a number.

![Below 0.01 the direction is close to a coin flip; above it, it is not](/figures/Fig5_flip_rate.webp)

| predicted \|LFC\| | n   | directions that flip | 95% interval |
| ----------------- | --- | -------------------- | ------------ |
| below 0.01        | 132 | **28.8%**            | 21.6 – 36.9% |
| 0.01 – 0.02       | 63  | 4.8%                 | 1.4 – 12.2%  |
| 0.02 – 0.03       | 42  | 2.4%                 | 0.3 – 10.6%  |
| 0.03 – 0.05       | 44  | 2.3%                 | 0.3 – 10.1%  |
| 0.05 – 0.075      | 25  | 0%                   | 0 – 9.5%     |
| 0.075 – 0.10      | 13  | 0%                   | 0 – 17.3%    |
| 0.10 – 0.20       | 20  | 0%                   | 0 – 11.7%    |
| above 0.20        | 11  | 0%                   | 0 – 20.0%    |

Pooled, that is **5 flips in 218 variants above 0.01** (2.3%, 95% CI 0.9 – 5.0%) and **0 flips in 69 variants above 0.05** (0 – 3.6%).

The bottom bin is the result that carries weight: 132 variants, a 29% flip rate, and a median disagreement that is 0.97 times the size of the effect being reported. Those predictions are not small-but-real. They are noise.

## A probability, not a cutoff

A hard threshold would say a variant at 0.0149 is unreportable and one at 0.0151 is fine. That is obviously false, and the data do not support it: the error rate is a smooth function of effect size. So fit it.

![A probability, not a cutoff](/figures/Fig6_probability.webp)

A logistic model on log₁₀|LFC| gives a per-variant **P(direction is reproducible)**:

| predicted \|LFC\| | P(direction holds) |
| ----------------- | ------------------ |
| 0.005             | 0.79 [0.73 – 0.86] |
| 0.010             | 0.92 [0.88 – 0.95] |
| 0.015             | 0.95 [0.93 – 0.98] |
| 0.030             | 0.98 [0.97 – 0.99] |
| 0.050             | 0.99 [0.98 – 1.00] |

P reaches 0.90 at |LFC| 0.009, 0.95 at 0.015 and 0.98 at 0.028. The threshold becomes the reader's choice: a transplant decision can demand 0.95, an assay shortlist can work at 0.80.

A fitted probability is only worth reporting if it is calibrated, so check it before using it.

![The probability means what it says](/figures/Fig7_calibration.webp)

Brier score 0.075 against 0.108 for always predicting the base rate, a 30% improvement, with the largest gap between predicted and observed at 0.031 across five bins. It is honest to one decimal place, which is all anyone should quote.

**What this number is not.** It is the probability that the _direction is reproducible_, not the probability that the variant is pathogenic. These are different quantities and conflating them would be the fastest way to misuse everything here.

## The same boundary, found twice

The measurement above was the second run. An earlier, independent experiment used a different set of 150 variants and scored every one in a single cell state rather than its own.

![Two independent experiments, the same boundary](/figures/Fig8_replication.webp)

Different variants, different cell-state handling, same boundary in the same place. The first run also put the sub-0.01 flip rate near 30% and found no flips above 0.05.

## A second limit, which caught us out

While setting the experiment up, fresh scores failed to match the values recorded in the original scan. Chasing that down produced an unplanned finding.

The original scan conditioned the model on single-cell RNA profiles from public bone-marrow datasets. The fresh scores used the model's own built-in reference cell types. Both are defensible choices. They do not give the same answer.

![The same variant, two reasonable choices of cell state](/figures/Fig9_conditioning.webp)

| cell state        | n   | directions that agree | median size ratio |
| ----------------- | --- | --------------------- | ----------------- |
| stem / progenitor | 76  | **95%**               | 0.88              |
| monocyte          | 132 | 78%                   | 0.29              |
| megakaryocyte     | 142 | **47%**               | 0.19              |

For stem and progenitor cells the two approaches are interchangeable. For megakaryocytes they are not, and the reason connects straight back to the floor: under the built-in megakaryocyte condition the model produces almost nothing for these loci. The median predicted effect is 0.011 and 59% of the variants fall below the floor. Predictions below the floor carry no directional content, so agreement with any fixed set of signs should sit near 50%, and it does — 47%, unchanged at every effect size including the largest.

The honest reading is narrow. This does not say which answer is right — there is no ground truth here either. It says that **a predicted effect is a property of the variant and the cell state together**, that the two are not separable, and that a published score is not reproducible unless the exact conditioning is recorded alongside it. Ours was not, which is why this took a day to work out. It also says that a cell state can be a dead end for a given locus: if the built-in condition puts every prediction under the floor, no amount of care in reading those predictions will recover a signal.

## Why a floor is necessary, not just tidy

Without one, three things go wrong, and all three are invisible.

**Small effects get interpreted.** Forty-eight per cent of the 5,100 variants fall below the floor. Reporting a direction for any of them is reporting a coin flip in the typography of a result.

**Absence of effect gets interpreted.** This is the worse failure. A near-zero score looks like evidence that a variant does nothing through transcription — a genuinely useful negative, if it were real. It is not: near zero is exactly where the model is least reproducible. The floor forbids the negative claim as firmly as the positive one.

**Rankings get built on sand.** Sort 600 variants by predicted effect and the top of the list is fine while the middle is arbitrary. Without a floor there is nothing marking where the list stops meaning anything.

## What is left standing, and for whom

![Reliability is not uniform across genes](/figures/Fig10_scope.webp)

Two practical qualifications sit alongside the floor.

**Reliability is not uniform across genes.** Above the floor, GATA2, DDX41, RUNX1, CEBPA and ETV6 showed no flips at all in this sample; TERT 2.6%, ANKRD26 3.7%, TP53 7.3%. The sample sizes per gene are 13 to 41, so these intervals are wide, but TP53 deserves more caution than the others and is the one worth re-testing at depth.

**The floor does not spare the variants you care about.** Of ClinVar pathogenic and likely-pathogenic non-coding variants in these genes, 77% clear the floor; of variants of uncertain significance, 77%; of benign and likely-benign, 64%. So roughly a quarter of the clinically labelled variants here cannot be given a direction at all. That is a real limit on coverage, and it is better to know it than to paper over it.

What remains is a defensible instrument with a stated operating range:

1. For a non-coding variant whose predicted effect clears |LFC| ≈ 0.015, AlphaGenome 2 gives a direction that is reproducible with P ≥ 0.95 under a perturbation it should not care about.
2. Below that, it gives nothing — including no evidence of absence.
3. The prediction belongs to a (variant, cell state) pair, and quoting it without the cell state is quoting half a result.
4. None of this is evidence of pathogenicity. It is a filter on which predictions are even worth discussing.

For a clinician, the usable form is narrow and real: given a variant already under consideration, the model can say which direction to expect and in which cell type to assay it, provided the predicted effect clears the floor. That is experiment design, not classification, and it is worth having.

## Methods in brief

- **Model:** AlphaGenome 2 via the public API, 1 Mb context, gene-level expression change as a natural-log fold change (`RNA_SEQ` recommended scorer, gene-masked mean difference).
- **Perturbation:** each variant scored at window centres of 0 and ±25 kb relative to the variant, holding the variant, gene and scorer fixed. A "flip" is any disagreement in sign across the three.
- **Sample:** 350 variants over 8 germline predisposition genes (ANKRD26, CEBPA, DDX41, ETV6, GATA2, RUNX1, TERT, TP53), stratified across effect-size bands and concentrated near the boundary; each scored in the cell state that drove its original call. 1,050 model calls.
- **Replication run:** an independent 150 variants scored in a single reference cell state (hematopoietic multipotent progenitor), 450 calls.
- **Intervals:** Jeffreys 95% intervals throughout, which behave sensibly at zero events.
- **Probability model:** logistic regression of direction-held on log₁₀|LFC|, 1,200-sample bootstrap for intervals, calibration assessed in five quantile bins with the Brier score against a base-rate predictor.
- **Cell-state comparison:** fresh scores under the model's built-in reference conditions versus the values recorded in the earlier custom-conditioned scan, matched variant by variant.

## Limits of this note

- It measures **reproducibility, not correctness**. A stable prediction can still be biologically wrong. The claim is only that an unstable one cannot be right.
- The floor was measured on scores computed under **built-in reference cell types**. The same perturbation has not been run on custom-conditioned scores. The mechanism is sequence-context handling rather than conditioning, so it should transfer, but that is an expectation and not a measurement.
- ±25 kb is **one** perturbation. Others — sequence context length, scorer choice, reference genome build — would each give their own floor, and the true operating floor is the worst of them.
- Eight genes, all myeloid predisposition loci, promoters and one enhancer. Other sequence classes may behave differently.
- The per-gene flip rates rest on 13 to 41 variants each and should be read as a flag for follow-up rather than a measurement.
