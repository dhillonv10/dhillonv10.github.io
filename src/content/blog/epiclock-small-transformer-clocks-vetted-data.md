---
title: "EpiClock: A model-family of epigenetic clocks"
author: Vik Dhillon
pubDatetime: 2026-11-20T09:00:00-08:00
slug: epiclock-small-transformer-clocks-vetted-data
type: note
draft: false
takeaways:
  - "**Clean data does most of the work.** Fewer than a quarter of 45,280 public methylation profiles passed the audit, leaving 25,765 with a known age. 257 exact copies of test samples were found and removed."
  - "**Small transformer clocks match a tuned linear model.** On 2,830 healthy people from 40 unseen studies the median error is about 3.4 years, ahead of the published clocks (4.2 to 8.4 years) and level with an elastic net (3.27). Size, from 2 to 48 million parameters, made no measurable difference."
  - "**Most of the remaining error is shared by whole studies.** About half of the squared error is a shift common to a study, which points to differences in how labs measure and process samples."
description: "Five small transformer-based epigenetic clocks."
---

An epigenetic clock reads a person's age from DNA methylation in a blood sample. I trained a family of five small transformer clocks and put most of the effort into the part that usually gets the least: the data.

The models are on Hugging Face: [huggingface.co/dhillonv10/epiclock](https://huggingface.co/dhillonv10/epiclock)

## Curated training data

Public methylation data is messy. Before training, every profile went through an audit, and anything that failed was left out, with the reason recorded: cancer, other disease, cell cultures, or no health annotation at all. Of the 45,280 profiles in the starting bundle, fewer than a quarter passed. The final training set is 25,765 profiles with a known age, plus 11,526 without one for pre-training, on a panel of 9,098 methylation sites.

The audit also caught something easy to miss. 257 profiles in a standard training set were exact copies of samples in the test set. They were removed, so the test below is a real one: 2,830 healthy people from 40 studies the models never saw.

Does the cleaning matter? I checked by adding non-cancer disease profiles back in. A linear ridge clock got 0.77 years worse. The transformer was not hurt by the same data, so the benefit of clean data is clearest for the simpler model.

## How the models work

Each methylation site (CpG) is a token: a learned identity, its place in the genome, and its measured value. A sample is a random subset of its sites. The models are first pre-trained without labels, by hiding a quarter of the sites and reconstructing them, and then fine-tuned to predict age. The age output is a linear clock plus a correction learned by the transformer.

## Results

![Age error of every model on the held-out healthy controls](/figures/epi_fig1_model_comparison.webp)

All five models are off by about 3.4 years in the median. That is ahead of the published clocks run on the same samples: Horvath's two clocks score 4.2 and 5.4 years, and Lin, PhenoAge and Hannum score between 7.6 and 8.4. The published clocks are at a disadvantage here, because they were run on a reduced panel of sites.

The family is level with an elastic net, a well-tuned linear model trained on the same vetted data, which scores 3.27 years against 3.34 for the best transformer. For predicting age in healthy blood the problem is close to linear, and good data does most of the work.

![EpiClock-L predicted age against chronological age](/figures/epi_fig2_predicted_vs_true.webp)

Study by study, EpiClock-L has a lower error than Horvath V2 in 22 of the 36 studies with at least ten healthy controls.

![Per-study error of EpiClock-L against Horvath V2](/figures/epi_fig4_per_study.webp)

## Smaller models perform comparably to larger counterparts

The family runs from 2 million to 48 million parameters, and size made no measurable difference on the test set.

![Model size against error](/figures/epi_fig3_model_size.webp)

The smallest and the largest model also give nearly the same answer for each person: their predictions correlate at 0.999 and differ by half a year in the median.

![Predictions of the smallest and largest model](/figures/epi_fig10_family_agreement.webp)

## Where the error comes from

**The study.** This is the data story again, seen from the other side. Each held-out study has its own shift: most are within a couple of years, a few are off by five to ten, and two are far out. About half of the squared error is a shift shared by a whole study, which points to differences in how labs measure and process samples, not to errors on individual people.

![Per-study offsets](/figures/epi_fig7_study_offsets.webp)

**Age.** Every clock gets less accurate with age. EpiClock-L and the elastic net track each other closely across age groups; Horvath V2 is worse in most groups and reaches 6.7 years in people over 80.

![Error by age group](/figures/epi_fig5_error_by_age.webp)

**Direction.** EpiClock-L is close to unbiased under 40. It reads people in their 40s and 50s two to three years old, and people over 70 about three years young.

![Signed error by age group](/figures/epi_fig6_bias_by_age.webp)

## Under the hood

Pre-training and fine-tuning behaved as expected for all five sizes. On the validation studies the larger models reached a slightly lower error, about 0.1 years; that advantage did not carry over to the test set.

![Training curves](/figures/epi_fig8_training_curves.webp)

Taking the base model apart, pre-training was worth about 0.18 years and the transformer's correction about 0.13 years, while the genome-context inputs added nothing. All of these are small, and their intervals include zero.

![What each ingredient added](/figures/epi_fig9_ingredients.webp)

Weights, code, the full evaluation report and the data audit are in the repository.
