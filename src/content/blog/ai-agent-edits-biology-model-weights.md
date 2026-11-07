---
title: "Exploring Weight-Space Programming for Longevity Models"
subtitle: "Can an AI Agent Improve a Biology Model by Editing Its Weights?"
author: Vik Dhillon
pubDatetime: 2026-11-03T19:00:00-08:00
slug: ai-agent-edits-biology-model-weights
type: feature
draft: false
takeaways:
  - "**An AI agent improved a biology model by editing its weights directly, with no training.** Over five rounds, Claude Opus 5.5 cut the age-estimation error of Insilico Medicine's `Qwen3-0.6B-Longevity` from **14.2 to 8.25 years**."
  - "**The edited model now ties a tuned classical model.** Gradient boosting, tuned and trained on the same 750 people the agents could use, scores 8.20 years. The difference is +0.05 years (95% CI −0.13 to +0.23): A statistical tie. The edited model is significantly better than a ridge regression and an additive spline model, and level with default gradient boosting."
  - 'The agent *unlocked* what the model already knew (round 1). Then it *wrote new computation* into the network: a pooling attention head, gated neurons, biomarker "reader" heads and finally a per-marker age circuit over every item in the blood panel (rounds 2 to 5).'
  - "**Nothing else broke along the way.** After round 2 fixed a bug that round 1 introduced, multiple-choice answers stayed at the original model's accuracy through round 5. The edited 0.6B model also beats every other open model we could run, including Insilico's own 1.7B and 9B longevity models."
description: 'Over five rounds, Claude Opus 5.5 edits Insilico Medicine''s open aging model directly, with no training, until it ties a tuned classical model trained on the same data. A replication and extension of "Sparks of Weight-Space Programming."'
---

## Brief results

We gave **Claude Opus 5.5** read and write access to the raw weights of [`Qwen3-0.6B-Longevity`](https://huggingface.co/insilicomedicine/Qwen3-0.6B-Longevity), a small open model fine-tuned on aging biology. The job was to make it better at estimating a person's **age from a routine blood panel**. It could not train the model with gradient descent. It had to read the weights and activations, decide what to change, and write the change itself.

|                                                                | What Opus changed                                     | Age error (MAE) | Correlation with true age |
| -------------------------------------------------------------- | ----------------------------------------------------- | --------------- | ------------------------- |
| Original model                                                 | —                                                     | 14.16 years     | 0.686                     |
| **Round 1**                                                    | 10 rows of the output layer                           | 11.39 years     | 0.705                     |
| **Round 2**                                                    | a new pooling attention head and 5 rebuilt neurons    | 9.05 years      | 0.797                     |
| **Round 3**                                                    | 3 attention heads rewired to read specific biomarkers | 8.66 years      | 0.814                     |
| **Rounds 4–5**                                                 | a per-marker age circuit over all 29 profile items    | **8.25 years**  | **0.833**                 |
| _Reference: tuned gradient boosting, same 750 training people_ | —                                                     | _8.20 years_    | _0.832_                   |

![Age error after each round](/figures/p1_rounds_mae.png)
_Figure P1 (performance). Held-out age error after each round, with 95% confidence intervals. The orange band is tuned gradient boosting trained on the same 750 people._

The five rounds show three different things:

1. **Round 1 mostly unlocked what the model already knew.** The model's internal age estimate was better than its answers; Opus fixed the read-out. Error dropped by 2.8 years; correlation barely moved.
2. **Rounds 2 and 3 changed what the model computes.** Opus wrote new circuitry that carries biomarker information to the answer that never reached it before. Error dropped by a further 2.7 years.
3. **Rounds 4 and 5 closed the gap to classical machine learning.** I asked Opus to beat a tuned gradient-boosting model. It built a circuit that turns every blood marker into an age contribution and adds them up inside the network. Error fell another 0.41 years (CI −0.53 to −0.29), to a statistical tie with the classical model.

**Every design and weight change in these results was produced by Claude Opus 5.5 agents.**

## 1. The question

In [_Sparks of Weight-Space Programming_](https://rikiyat.github.io/blog/weight-space-programming/), Takehi, Teoh, Zhang and Khattab showed that a frontier LLM can read and write neural-network weights directly. Their most striking result: given a Python kernel and a budget of forward passes, the LLM found a "looping" direction inside Qwen3.5-0.8B and removed it, raising its MATH-500 score from 7.9 to 48.1. Their control experiment set the limit. On a model that did not loop, the same procedure did nothing. **Editing could remove an obstacle, but it could not add an ability.**

We asked three questions:

- **Does this work on a biology model?** Small, open, domain-tuned models are everywhere in biology, and their tasks have objective answers.
- **Can an agent go past removing obstacles, and actually add computation that makes the model better?**
- **How far can it go?** Specifically, can an edited language model match a classical machine-learning model trained on the same data?

## 2. The setup

**The model.** `Qwen3-0.6B-Longevity` is Insilico Medicine's full fine-tune of Qwen3-0.6B on aging-related multi-omics and clinical data. It accompanies _An open benchmark and language models for AI in aging biology_ (Zhavoronkov et al., _Cell_, 2026).

**The task.** We used the [LongevityBench](https://huggingface.co/datasets/insilicomedicine/longebench) NHANES age task. The model reads a participant's sex, BMI and up to 28 blood markers and answers _"How old is this participant?"_ We score mean absolute error (MAE) in years.

**The editing loop.** Each round is an Opus agent with a shell. The model is held in a sandbox. Through a Python kernel the agent can:

- read and overwrite any weight tensor;
- run the model on labelled practice examples;
- call **`evaluate`**, which scores its current edit on a dev set.

An edit is **kept only if dev error improves**; otherwise it is reverted automatically. No optimizer may update the weights, but closed-form analysis (least squares, SVD, discriminant analysis) is allowed. Edits may touch at most 5% of the weights, and the agent has a fixed budget of evaluations.

## 3.What did Opus contribute

Opus was used as an **autonomous research agent**. Each agent was a Claude Opus 5.5 session with a shell. It talked to the model only through the sandbox, and did all the analysis and editing itself.

| Agent                   | What it was given                                                                                                                                                                                                                                                 | What Opus contributed                                                                                                                                                                                                                                                                                                                                                                                                         |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Round 1 editor**      | The model in a sandbox, 150 labelled practice prompts, 20 dev evaluations, and a one-page task description with **no hints** about what to change                                                                                                                 | Diagnosed the problem (the first digit stuck on 2/3/4; internal age estimate better than the answers). Designed the edit (quadratic prior over the first digit, position gate, end-of-answer guard). Fitted every vector, chose all parameters, wrote the code, and decided when to stop (8 evaluations).                                                                                                                     |
| **Round 2 editor**      | The round-1 model, round 1's code and summary, 750 practice prompts, 15 evaluations; asked for _better information, not recalibration_, with a list of directions to consider                                                                                     | Found the unused information at the biomarker tokens. Found round 1's multiple-choice bug. Designed and built the circuit: chose head 11, value channel 119 and the five least-used neurons, and fitted all their weights. Ran the ablation that separates information from read-out.                                                                                                                                         |
| **Round 3 editor**      | The round-2 model, rounds 1–2's code and summaries, the same practice prompts, 15 evaluations; brief suggested targeted reading of specific biomarkers                                                                                                            | Identified Cystatin C, Vitamin E and Albumin as the remaining unused signal. Designed the three fixed-query reader heads and their nonlinear decoders. Refit the read-out, ran an ablation, and flagged its own dev-selection risk.                                                                                                                                                                                           |
| **Rounds 4–5 editor**   | The round-3 model, all earlier code and summaries, the same 750 practice prompts, a fresh 400-person dev set, 12 evaluations (round 4) plus a continuation; the goal was to **beat a tuned gradient-boosting model**, with its scores given. **No design hints.** | Found that rounds 1–3 used only 3 of the 29 profile items, and that whether Cystatin C was measured at all is a strong age signal. Designed and built the per-marker age circuit (58 gated neurons, a summing head, a refit read-out, a digit-bias correction). Ran the ablations. Found and fixed its own bug (an edit applied twice). After a server crash, rebuilt its accepted edit exactly from its own derivation code. |
| **Blind weight reader** | Two anonymised checkpoints and the tokenizer; **no forward passes allowed**                                                                                                                                                                                       | Worked out which checkpoint was fine-tuned from which, measured where the weights changed, and identified the training domain, all from arithmetic on the weights.                                                                                                                                                                                                                                                            |
## 4. Where the model starts

The fine-tuned Longevity model is clearly better than the base Qwen3-0.6B at aging tasks. It gets 69% vs 49% at telling which of two people is older, and 69% vs 51% at predicting 10-year survival. But its age estimates are poor: 14.2 years of error on held-out people, mostly because it guesses young for everyone (average bias −11.3 years).

## 5. Finding age-related information in the model's internal representations

Before running any agent, I checked whether there was a gap between what the network _computes_ and what it _outputs_. A linear probe from the model's internal state to the true age gets about **10.7 years** of error on practice prompts, against about **14 years** for the model's own answers. The age information appears abruptly around layer 15. The base model's internal states know almost nothing about age, so **fine-tuning built the age representation**. The model was not using all of it.

## 6. Round 1: Unlocking what the model already knows

The round-1 agent first studied the model's answers. It found that the model always answers with two digits and that **the first digit is almost always 2, 3 or 4**, so the model rarely says anyone is over 50.

Its first edit added a _quadratic prior_ over the first digit, centred on the model's own internal age estimate. Dev error dropped from 15.3 to 10.8. Its second attempt **blew up to 30.3**: the change leaked into later digits and produced three-digit ages. Opus diagnosed the leak and added two safeguards:

- a **position gate**, so the edit acts only on the first digit;
- an **end-of-answer guard**, so the model stops after two digits.

Its 7th evaluation was accepted at 9.8. It stopped after 8 of 20 evaluations. The final edit changes **10 rows of the output layer**: 10,240 weights, or 0.0014% of the model.

> **Opus's contribution in round 1:** the diagnosis (first digit stuck on 2–4), the edit design (quadratic prior, position gate, end-of-answer guard), every fitted vector and parameter, the recovery from its own failed attempt, and the decision to stop at 8 of 20 evaluations.

**The result: Better answers, nearly the same knowledge.** Error fell from **14.16 to 11.39 years** (−2.77, CI −3.25 to −2.27), but correlation rose only by 0.02, and the best possible rescaling of the answers improved only from 11.12 to 10.82 years. Round 1 corrected the model's habit of guessing too young (bias −11.3 → +3.9 years). **It unlocked knowledge the model already had**, the same kind of fix as the original post's looping repair.

## 7. Round 2: Changing what the model computes

A new Opus agent started from the round-1 model, with 750 practice examples, 80 fresh dev rows and 15 evaluations. Its brief: Make the age estimate **better**, not just recalibrated.

**What Opus found.** The internal states at the **blood-marker tokens** contain age information that never reaches the token where the answer is produced. It also found that round 1 had a side effect: the model now answered some multiple-choice questions with a digit instead of a letter.

**The circuit it built.** All the changes are in **layer 27** plus the output rows, 290,813 weights or 0.039% of the model:

1. **A pooling head.** One attention head was rewired to attend equally to every token. One of its value channels reads an age signal at each blood-marker token, so the head delivers the **average age evidence from all the biomarkers** to the answer position.
2. **Five rebuilt neurons.** The five least-used neurons in the layer were turned into **gated circuits** that fire only when the model is writing an age. They set the first digit, the second digit, and the stop.
3. **New output rows** that replace round 1's ungated rows.

Opus used **2 of its 15 evaluations**: the full edit scored 7.96 on dev, from 10.38. Its ablation, with the pooled biomarker signal removed, scored 8.72.

> **Opus's contribution in round 2:** finding the unused biomarker information and round 1's multiple-choice bug; the circuit design; the choice of head, channel and neurons; every fitted weight; and the ablation showing how much of the gain is new information.

**The result: the model knows more.** Error fell to **9.05 years** (−2.34 vs round 1, CI −2.62 to −2.05) and correlation rose by 0.09. Round 2's answers are already well calibrated (9.05 as answered, 9.07 after the best rescaling), almost two years below anything rescaling the original model can reach (Figure D1).

## 8. Round 3: Pushing the same direction further

A third agent found that most of the information still unused sits in **three specific biomarkers: Cystatin C** (a well-known kidney and aging marker), **Vitamin E and Albumin**. It **rewired three attention heads in layer 24 into "reader" heads**. Each has a fixed query that puts about 99% of its attention on one biomarker's value and decodes a nonlinear age correction from it. Dev error went from 7.66 to 7.33 in 5 of 15 evaluations.

> **Opus's contribution in round 3:** the brief suggested targeted reading; Opus identified the three biomarkers, designed the content-addressed reader heads and their nonlinear decoders, refit the read-out, ran the ablation, and warned that its accepted result carries some dev selection.

**The result:** error **8.66 years**, a smaller but significant step (−0.39 vs round 2, CI −0.57 to −0.21; correlation +0.017).

## 9. Rounds 4 and 5: closing the gap to classical machine learning

After round 3, I wanted to see how the edited model compared with a conventional baseline. I trained a tuned gradient-boosting model on the same 750 participants available to the agents, using their blood measurements directly. It achieved a held-out MAE of **8.20 years**, outperforming round 3's **8.66 years**. That gave me a new benchmark—and the next agent a more ambitious objective: **beat it.**

The round-4 agent started from the round-3 model, with the same 750 practice people, a fresh **400-person dev set** and 12 evaluations. Its brief gave the baseline's scores and the rules: no gradient descent, every prediction computed inside the model by weights it wrote, multiple-choice and chat answers unchanged

### What Opus found

Analyzing the practice data before spending any evaluations, it found:

- **Rounds 1–3 used only 3 of the 29 profile items.** Everything else in the panel was still unused.
- **Missing values are information.** Whether Cystatin C was measured at all is a strong age signal: the mean age is about 60 when it is present and about 39 when it is absent.
- **A per-marker model would beat the baseline on practice data.** Adding up one learned age curve per marker scored 8.06 (cross-validated), against 8.29 for gradient boosting.

### The circuit it built

The edit changes **593,887 weights** (0.079% of the model), in layers 26–27 and the digit rows:

1. **29 gated neuron pairs (layer 26).** The 58 least-used neurons became 29 pairs. Each pair fires only on _its own_ marker's value token, and writes that marker's age contribution, read off a fitted curve, into an unused direction of the hidden state. A missing marker contributes zero.
2. **A summing head (layer 27).** One attention head attends almost evenly to every marker-value token and adds the contributions up at the answer position.
3. **A refit read-out.** It combines the summed marker signal with the model's own internal age estimate and blends in round 3's read-out.
4. **A digit-bias correction.** Opus found that the model's digit preferences pulled tens digits 6 and 7 down to 5 and 6, and removed that bias.

Round 4's accepted edit scored **8.56 on dev**, against **8.54** for the baseline on the same 400 people.

**Round 5** was a continuation by the same agent. The sandbox ran out of memory and lost the accepted edit before it was saved, so Opus rebuilt it from its own derivation code. The rebuild reproduced the dev score (8.55). It then tested one more variant (8.62, rejected) and stopped. _(After this, I made the sandbox save every accepted edit to disk.)_

> **Opus's contribution in rounds 4–5:** finding the 26 unused profile items and the missing-value signal; the per-marker circuit design (gated neuron pairs, summing head, refit read-out, digit-bias correction); every curve, neuron choice and fitted weight; the ablations; catching its own bug (an edit file that applied a correction twice); and rebuilding the accepted edit exactly after the crash.

### The result: a tie with tuned gradient boosting

Held-out error fell to **8.25 years** (−0.41 vs round 3, CI −0.53 to −0.29), with correlation 0.833. The new information is real computation: with the marker circuit switched off, dev error is 9.76 instead of 8.55 (Figure D4). Against tuned gradient boosting, the difference is **+0.05 years (95% CI −0.13 to +0.23), a statistical tie**. It is level with default gradient boosting (−0.12, CI −0.30 to +0.07) and significantly better than the additive spline model (−0.32, CI −0.47 to −0.18).

## 10. Checking the whole picture

### Performance

![Predicted vs true age](/figures/p2_scatter.png)
_Figure P2 (performance). Predicted vs true age for the original model and after rounds 4–5, on the 2,791 held-out people._

The original model's answers form flat bands: it uses a few favourite numbers and guesses young for everyone. After five rounds, the predictions follow the diagonal across the full age range. The model gives 75 distinct answers instead of 38, and only 6% end in zero, against 43% for the original.

![Closing the gap to gradient boosting](/figures/p3_gap_to_gbm.png)
_Figure P3 (performance). Extra error relative to tuned gradient boosting on the same people, with 95% CIs. Each round narrows the gap; rounds 4–5 close it._

![Error by age band](/figures/p4_age_bands.png)
_Figure P4 (performance). Error by age band, for each round and for tuned gradient boosting._

**Who benefits.** The original model is accurate only for the youngest people, because it guesses young for everyone; error for the over-75s is 25.5 years. After rounds 4–5, error is 6.9–10.5 years in every band. That is within a year of tuned gradient boosting in every band, and better than it for the 18–30s (9.1 vs 9.6) and the over-75s (10.5 vs 10.7). The youngest group is still worse off than with the original model (9.1 vs 5.7).

### Diagnostics

![Calibration vs information](/figures/d1_calibration_vs_information.png)
_Figure D1 (diagnostic). Each round's error as answered (circles) and after the best possible straight-line rescaling of its answers (diamonds)._

**This is the key diagnostic.** Rescaling cannot create information. For the original model and round 1, rescaling stalls at about 11 years. From round 2 on, the answers are already well calibrated, and the error after rescaling keeps falling (9.07 → 8.68 → 8.27). The gains in rounds 2–5 are information the model did not use before.

![Bias by age](/figures/d2_bias_by_age.png)
_Figure D2 (diagnostic). Mean answer for each tenth of people, sorted by true age. The dashed line is a perfect answer._

The original model is biased young at every age (−11.3 years on average). Round 1 overcorrected (+3.9). From round 3 on, the answers follow the diagonal through the middle of the age range, with the remaining bias at the extremes (average bias after rounds 4–5: −0.04 years).

![Ablations](/figures/d4_ablations.png)
_Figure D4 (diagnostic). Ablations run by the agents on their own dev sets: the same edit with the new information switched off._

![Side effects](/figures/d5_side_effects.png)
_Figure D5 (diagnostic). Accuracy and answer format on the five NHANES multiple-choice tasks (225 questions) for every round._

**Side effects: A bug, caught and fixed by Opus.** Round 1's edit had a side effect I missed. On free-form multiple-choice questions, the model started answering with a digit instead of a letter, and accuracy fell to near zero. **The round-2 agent discovered it on its own test prompts and designed its circuit to avoid it.** From round 2 on, multiple-choice accuracy is back at the original model's level (55.1% → 55.1%, 56.0%, 55.6%). Every answer starts with a letter again. On the round-4 agent's own 54 probe prompts (multiple choice and chat), no top answer changed.

## 11. How does the edited model compare?

### Against classical machine learning

![Classical baselines](/figures/c1_classical_baselines.png)
_Figure C1 (comparison). The edited model against classical models trained on the same 750 people, on the 2,791 held-out people (95% CIs). The grey bar is a data-rich reference trained on ~4.4× more people._

| 2,791 held-out people                               | Age error (MAE) | 95% CI      | Correlation |
| --------------------------------------------------- | --------------- | ----------- | ----------- |
| Ridge regression                                    | 9.87            | 9.60–10.13  | 0.764       |
| Additive spline model                               | 8.57            | 8.34–8.81   | 0.822       |
| Gradient boosting (default)                         | 8.37            | 8.13–8.61   | 0.825       |
| Gradient boosting (tuned by cross-validation)       | 8.20            | 7.95–8.44   | 0.832       |
| **Opus-edited LLM (rounds 4–5)**                    | **8.25**        | 8.01–8.49   | **0.833**   |
| _Gradient boosting, ~3,300 people (reference only)_ | _7.74_          | _7.51–7.97_ | _0.853_     |

The edited language model sits with the best classical models trained on the same data. A classical model with ~4× more training people is better still, which shows where the remaining limit is: **the amount of labelled data, not the edits.**

![Learning curve](/figures/c2_learning_curve.png)
_Figure C2 (comparison). Error of gradient boosting trained on N of the 750 practice people (orange; shaded = range over 10 random subsets), with each version of the edited model as a dashed line._

**What the edits are worth in labelled data.** The original model's answers (14.2) are worse than gradient boosting trained on just 50 people (11.1); even after the best possible rescaling (11.1), its knowledge of age is worth only about 50 labelled people. Round 1 sits at that level. Round 3 matches gradient boosting trained on ~400 people. After rounds 4–5, the edited model matches gradient boosting trained on all 750.

### Against other open language models

![Other open models](/figures/c3_open_models.png)
_Figure C3 (comparison). Open language models on the same 200 held-out people (the part of the earlier 400-person comparison set that stayed held out)._

We ran 24 open models with the same prompts on a GPU, reading the first number in the first 16 generated tokens. On the 200 people that stayed held out:

| Model                                      | Size | Age MAE | Correlation |
| ------------------------------------------ | ---- | ------- | ----------- |
| **Qwen3-0.6B-Longevity + Opus rounds 1–5** | 0.6B | **8.3** | **0.81**    |
| Qwen3-0.6B-Longevity (original)            | 0.6B | 13.8    | 0.69        |
| Qwen2.5-1.5B-Instruct                      | 1.5B | 15.2    | 0.20        |
| Insilico Qwen3-1.7B-Longevity              | 2.0B | 15.8    | 0.71        |
| Insilico longevity-llm (Qwen3.5-9B)        | 9.0B | 18.9    | 0.67        |

Eleven other open models (Qwen3-0.6B to 8B, Qwen2.5-0.5B to 7B, Phi-3.5-mini, Phi-4-mini, Mistral-7B, SmolLM2-1.7B) gave no usable age answers (correlation ≤ 0.05; most gave no number at all). Ten more could not be run (gated, disk or load failures). **Domain fine-tuning creates the ability; Opus's edits make the 0.6B model better than every model we could score**, including Insilico's 3× larger 1.7B model and 15× larger 9B model.

### Against other data types (rounds 1–3)

We also ran rounds 1–3 on three regression tasks they were never edited for: age from **blood proteins** (Olink), age from **DNA methylation**, and **lifespan change of gene knockouts**. These were not re-run for rounds 4–5.

|          | Protein age (n=40) | DNA-methylation age (n=45) | Lifespan change (n=26) |
| -------- | ------------------ | -------------------------- | ---------------------- |
| Original | **6.5** (r 0.79)   | 22.6 (r 0.20)              | 18.4 (r 0.78)          |
| Round 1  | 13.4 (r 0.76)      | 25.3 (r 0.38)              | 82.6 (broken output)   |
| Round 2  | 21.2 (r 0.13)      | 22.3 (r 0.53)              | 21.8 (r 0.72)          |
| Round 3  | 17.1 (r 0.26)      | 22.6 (r 0.53)              | **17.6** (r 0.78)      |

The age circuit fires on _any_ "how old is this person?" question, but the evidence it routes in was fitted only on blood panels. On a protein profile that evidence is meaningless and overrides the model's own good estimate. **Opus built a specialist.** Generality has to be part of what an agent is asked to protect.

## 12. Bonus: reading a model from its weights alone

The original post also showed that an LLM can work out what a network was trained on _from its weights alone_. We tried the same thing. A separate Opus agent got two checkpoints with neutral names: the Longevity model and the base Qwen3-0.6B. It was **not allowed to run either model**, only to do arithmetic on the weights.

| Opus's conclusion, from weights only                                                                                                                                                       | Truth                                      |                                        |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------ | -------------------------------------- |
| Checkpoint A is a fine-tune of B (99% confidence). Evidence: 124,377 embedding rows in A are _exactly_ 0.981 × B, the signature of weight decay on tokens that never appeared in training. | Correct                                    | ✅                                     |
| Output layer changed 7.2%, embeddings 4.1%                                                                                                                                                 | 7.1%, 4.0%                                 | ✅                                     |
| Change grows with depth and peaks around layer 25; key projections change most                                                                                                             | Correct                                    | ✅                                     |
| Domain: aging biology. It named epigenetic clocks and GrimAge's protein markers (cystatin C, TIMP-1, GDF15...)                                                                             | Aging biology over omics and clinical data | ✅ domain (too focused on methylation) |
| Output format: prose explanations                                                                                                                                                          | Short letter and number answers            | ❌                                     |

> **Opus's contribution here:** Weight-decay forensics, the row-level vocabulary detector, the weight-difference "logit lens", and every conclusion in the table above.

## 13. How large are these edits?

![What Opus changed](/figures/d3_what_changed.png)
_Figure D3 (diagnostic). Weights changed in each round, and where in the network._

All five rounds together change **1,659,871 of 751,632,384 weights (0.22%)**, with no gradient descent at any point. Each round reused or replaced parts of the previous ones, so the per-round counts add up to slightly more than the total.

## 14. What this shows (and what it doesn't)

1. **Weight-space programming works on a biology model.** With small evaluation budgets and no training, Opus cut held-out age error by 5.9 years (CI 5.5 to 6.3), from 14.2 to 8.25, on 2,791 people no agent saw.
2. **It goes beyond unlocking.** Round 1 removed an obstacle between what the model knew and what it said. Rounds 2–5 built new circuitry that delivers information the original output path never had.
3. **It reached the level of a tuned classical model, but not past it.** The edited model ties gradient boosting trained on the same 750 people. The remaining limit is the data: with ~4× more people, gradient boosting gets to 7.74.
4. **The gains are specific to the target task.** The age circuit makes age prediction from proteomics worse.
5. **The agent was careful in ways that mattered.** Opus engineered safeguards after failures, ran its own ablations, flagged its own dev-selection risks, caught a side effect I had missed and a bug of its own, and rebuilt its work exactly after a crash.

---

### Appendix: evaluation logs (recorded by the sandbox server)

**Round 1** (40 dev rows; start 15.30)

| #   | What Opus tried                      | Dev MAE      | Kept? |
| --- | ------------------------------------ | ------------ | ----- |
| 1   | Quadratic digit prior                | 10.80        | ✅    |
| 2   | Stronger shift (three-digit blow-up) | 30.27        | ✗     |
| 3   | + end-of-answer guard                | 10.93        | ✗     |
| 4   | Lower-noise read-out                 | 11.03        | ✗     |
| 5–6 | Strength and offset variants         | 10.82, 11.30 | ✗     |
| 7   | k = 2, offset −4                     | **9.78**     | ✅    |
| 8   | Further variant                      | 10.18        | ✗     |

**Round 2** (80 fresh dev rows; start 10.38)

| #   | What Opus tried                                | Dev MAE  | Corr  | Kept? |
| --- | ---------------------------------------------- | -------- | ----- | ----- |
| 1   | Pooling head + gated neurons + new output rows | **7.96** | 0.845 | ✅    |
| 2   | Ablation: no pooled biomarker signal           | 8.72     | 0.826 | ✗     |

**Round 3** (80 fresh dev rows; start 7.66)

| #   | What Opus tried                         | Dev MAE  | Corr  | Kept?            |
| --- | --------------------------------------- | -------- | ----- | ---------------- |
| 1   | Cystatin C reader only                  | 7.58     | 0.836 | ✗ (below margin) |
| 2   | Three readers                           | 7.69     | 0.829 | ✗                |
| 3   | Three readers, quieter write directions | 7.56     | 0.839 | ✗                |
| 4   | + decode-bias correction                | **7.33** | 0.838 | ✅               |
| 5   | Ablation: readers off                   | 7.50     | 0.844 | ✗                |

**Rounds 4–5** (400 fresh dev rows; start 9.00; tuned gradient boosting on the same rows: 8.54)

| #    | What Opus tried                                                            | Dev MAE  | Corr  | Kept?            |
| ---- | -------------------------------------------------------------------------- | -------- | ----- | ---------------- |
| R4-1 | Per-marker circuit over 29 items, summing head, refit read-out             | 8.63     | 0.785 | ✅               |
| R4-2 | Mixed curve shapes, digit-bias correction                                  | 8.64     | 0.787 | ✗                |
| R4-3 | Marker signal only, no LM term (ablation)                                  | 8.80     | 0.781 | ✗                |
| R4-4 | + round-3 read-out mixed in                                                | 8.58     | 0.785 | ✗ (below margin) |
| R4-5 | + value-augmented decoders                                                 | **8.56** | 0.784 | ✅               |
| R4-6 | Larger round-3 mix (correction applied twice, Opus's bug; found and fixed) | 10.56    | —     | ✗                |
| R4-7 | Ablation: marker circuit off                                               | 9.76     | 0.705 | ✗                |
| R4-8 | Larger round-3 mix, applied correctly                                      | 8.63     | 0.781 | ✗                |
| R5-1 | Rebuild of R4-5 after the crash                                            | **8.55** | 0.785 | ✅               |
| R5-2 | Decoders trained with markers deleted                                      | 8.62     | 0.781 | ✗                |

### Appendix: Round 1's edit, verbatim as Opus wrote it

```python
k=float(PARAMS.get('k',2.0)); off=float(PARAMS.get('off',-4.0)); g=float(PARAMS.get('g',1.2)); beta=float(PARAMS.get('beta',20.0))
dig=[tok.convert_tokens_to_ids(str(d)) for d in range(10)]; eos=tok.convert_tokens_to_ids('<|im_end|>')
with torch.no_grad():
    W=P['lm_head.weight']
    c=D['c'].to(W.dtype); v=D['v'].to(W.dtype); m=float(D['m'])
    a=g*v+(1-g)*m*c-off*c   # a.h = target age (years) at the first answer position
    for d in range(10):
        W[dig[d]]=D['W0'][d] + k*(2*d*a/10.0 - d*d*c)
    W[eos]=D['Weos0'] + beta*D['q'].to(W.dtype)
```
