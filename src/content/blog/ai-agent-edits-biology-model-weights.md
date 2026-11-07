---
title: "Weight-Space Programming for Longevity Models"
subtitle: "Can an AI Agent Improve a Biology Model by Editing Its Weights?"
author: Vik Dhillon
pubDatetime: 2026-11-03T19:00:00-08:00
slug: ai-agent-edits-biology-model-weights
featured: true
draft: false
takeaways:
  - "**An AI agent improved a biology model by editing its weights directly, with no training.** Claude Opus 5.5 cut the age-estimation error of Insilico Medicine's `Qwen3-0.6B-Longevity` from 14.2 to 8.7 years."
  - '**It did two different things.** First it *unlocked* what the model already knew (round 1). Then it *wrote new computation* into the network: A pooling attention head, rebuilt neurons and biomarker "reader" heads that carry information the original model never used (rounds 2 and 3).'
  - No rescaling of the original model's answers gets below 11.1 years of error; the edited model reaches 8.7."
  - "**The edited 0.6B model beats all 14 open models we could run, up to 9B parameters,** including Insilico's own 1.7B and 9B longevity models. Most general-purpose models gave no age estimate at all."
description: 'Claude Opus 5.5 edits Insilico Medicine''s open aging model directly, with no training. A replication and extension of "Sparks of Weight-Space Programming."'
stage: budding
audience: "Biologists, clinicians and machine-learning engineers who are curious whether an AI agent can improve a model by editing its weights directly. You don't need to know how transformers work in detail, only roughly what a neural network is and what a held-out test set means."
cover: /covers/weight-space.svg
coverAlt: "A grid of model weights with a few edited rows highlighted"
---

## Brief results

We gave **Claude Opus 5.5** read and write access to the raw weights of [`Qwen3-0.6B-Longevity`](https://huggingface.co/insilicomedicine/Qwen3-0.6B-Longevity), a small open model fine-tuned on aging biology. The job was to make it better at estimating a person's **age from a routine blood panel**. It could not train the model with gradient descent. It had to read the weights and activations, decide what to change, and write the change itself. All results in this table were evaluated on an independent held-out cohort of **3,191 individuals**, none of whom were included in the agents' development or weight-editing process.

|                | What Opus changed                                     | Age error (MAE) | Correlation with true age |
| -------------- | ----------------------------------------------------- | --------------- | ------------------------- |
| Original model | —                                                     | 14.2 years      | 0.68                      |
| **Round 1**    | 10 rows of the output layer                           | 11.4 years      | 0.70                      |
| **Round 2**    | a new pooling attention head and 5 rebuilt neurons    | **9.1 years**   | **0.79**                  |
| **Round 3**    | 3 attention heads rewired to read specific biomarkers | **8.7 years**   | **0.81**                  |

The three rounds show three different things:

1. **Round 1 mostly unlocked what the model already knew.** The model's internal age estimate was better than its answers; Opus fixed the read-out. Error dropped by 2.8 years; correlation barely moved (+0.016).
2. **Round 2 changed what the model computes.** Opus wrote new circuitry that carries information to the answer that never reached it before. Error dropped by a further 2.4 years (95% CI 2.1 to 2.6) and correlation rose by 0.10. No recalibration of the original model can reach this result.
3. **Round 3 went further in the same direction.** A smaller but clearly significant step: −0.37 years (CI −0.54 to −0.19), correlation +0.015. The direction kept paying off, with diminishing returns.

**Every design and weight change in these results was produced by Claude Opus 5.5 agents.** My part was building the sandbox and measuring the results (see Section 3). Along the way, Opus found and fixed a bug that its own round-1 edit had introduced, and that I had missed. A separate Opus agent also identified the model's training domain from the weights alone, without running the model once.

---

## 1. The question

In [_Sparks of Weight-Space Programming_](https://rikiyat.github.io/blog/weight-space-programming/), Takehi, Teoh, Zhang and Khattab showed that a frontier LLM can read and write neural-network weights directly. Their most striking result: Given a Python kernel and a budget of forward passes, the LLM found a "looping" direction inside Qwen3.5-0.8B and removed it, raising its MATH-500 score from 7.9 to 48.1. Their control experiment set the limit. On a model that did not loop, the same procedure did nothing. **Editing could remove an obstacle, but it could not add an ability.**

We asked two questions:

- **Does this work on a biology model?** Small, open, domain-tuned models are everywhere in biology, and their tasks have objective answers.
- **Can an agent go past removing obstacles, and actually add computation that makes the model better?**

## 2. The setup

**The model.** `Qwen3-0.6B-Longevity` is Insilico Medicine's full fine-tune of Qwen3-0.6B on aging-related multi-omics and clinical data. It accompanies _An open benchmark and language models for AI in aging biology_ (Zhavoronkov et al., _Cell_, 2026).

**The task.** We used the [LongevityBench](https://huggingface.co/datasets/insilicomedicine/longebench) NHANES age task. The model reads a participant's sex, BMI and about 25 blood markers and answers _"How old is this participant?"_ We score mean absolute error (MAE) in years.

**The editing loop.**

![The weight-editing loop](/figures/f01_loop.png)

Each round is a fresh Opus agent. The model is held in a sandbox. Through a Python kernel the agent can:

- read and overwrite any weight tensor;
- run the model on labelled practice examples;
- call **`evaluate`**, which scores its current edit on a small dev set.

An edit is **kept only if dev error improves**; otherwise it is reverted automatically. No optimizer may update the weights, but closed-form analysis (least squares, SVD) is allowed. Edits may touch at most 5% of the weights, and the agent has a fixed budget of evaluations.

## 3. Where was Opus used, and what it contributed

Opus was used as an **autonomous research agent**. Each agent was a fresh Claude Opus 5.5 session with a shell. It talked to the model only through the sandbox, and did all the analysis and editing itself. We ran **four separate agents**:

| Agent                   | What it was given                                                                                                                                                             | What Opus contributed                                                                                                                                                                                                                                                                                                                          |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Round 1 editor**      | The model in a sandbox, 150 labelled practice prompts, 20 dev evaluations, and a one-page task description with **no hints** about what to change                             | Diagnosed the problem (the first digit stuck on 2/3/4; internal age estimate better than the answers). Designed the edit (quadratic prior over the first digit, position gate, end-of-answer guard). Fitted every vector (three ridge regressions and an SVD). Chose all parameters, wrote the code, and decided when to stop (8 evaluations). |
| **Round 2 editor**      | The round-1 model, round 1's code and summary, 750 practice prompts, 15 evaluations; asked for _better information, not recalibration_, with a list of directions to consider | Found the unused information at the biomarker tokens. Found round 1's multiple-choice bug. Designed and built the circuit: chose head 11, value channel 119 and the five least-used neurons, and fitted all their weights. Ran the ablation that separates information from read-out.                                                          |
| **Round 3 editor**      | The round-2 model, rounds 1–2's code and summaries, the same practice prompts, 15 evaluations; brief suggested targeted reading of specific biomarkers                        | Identified Cystatin C, Vitamin E and Albumin as the remaining unused signal. Designed the three fixed-query reader heads (found by discriminant analysis on the existing keys) and their nonlinear decoders. Refit the read-out, ran an ablation, and flagged its own dev-selection risk.                                                      |
| **Blind weight reader** | Two anonymised checkpoints and the tokenizer; **no forward passes allowed**                                                                                                   | Worked out which checkpoint was fine-tuned from which, measured where the weights changed, and identified the training domain, all from arithmetic on the weights.                                                                                                                                                                             |

## 4. Where the model starts

![Baseline performance](/figures/f02_baselines.png)

The base Qwen3-0.6B is at chance on these tasks. The fine-tuned Longevity model is clearly better: 69% vs 49% at telling which of two people is older, and 69% vs 51% at predicting 10-year survival. But its age estimates are poor: 15.3 years of error on the mini split, barely better than always guessing the median age (17.6).

## 5. Finding age-related information in the model's internal representations

Before running any agent, I checked whether there was a gap between what the network _computes_ and what it _outputs_. _(This diagnosis is mine, not Opus's; the round-1 agent found the same gap on its own.)_ The test was simple: fit a linear probe from the model's internal state to the true age, at every layer.

![Probes](/figures/f03_probes.png)

- **The Longevity model knows age much better than it says.** A probe on its internal state gets about **10.7 years** of error (cross-validated on practice prompts), while the model's own answers have about **14 years** on held-out people. The information appears abruptly around layer 15.
- **The base model knows almost nothing about age.** No layer is much better than guessing the median. **Fine-tuning built the age representation.**
- **Control: mortality.** For 10-year mortality, the probe and the model agree (0.90 vs 0.89). There is no gap and nothing to unlock, so we pointed the agents at age.

## 6. Round 1: Unlocking what the model already knows

### What Opus did

![Round 1 search](/figures/f04_trajectory.png)

The round-1 agent first studied the model's answers. It found that the model always answers with two digits and that **the first digit is almost always 2, 3 or 4**, so the model rarely says anyone is over 50.

Its first edit added a _quadratic prior_ over the first digit, centred on the model's own internal age estimate. Dev error dropped from 15.3 to 10.8. Its second attempt **blew up to 30.3**: the change leaked into later digits and produced three-digit ages. Opus diagnosed the leak and added two safeguards:

- a **position gate**, so the edit acts only on the first digit;
- an **end-of-answer guard**, so the model stops after two digits.

Its 7th evaluation was accepted at 9.8. It stopped after 8 of 20 evaluations. The final edit changes **10 rows of the output layer**, 10,240 weights or 0.0014% of the model.

### What it does

![Digit probabilities](/figures/f08_digit_heatmap.png)

Each row of this heatmap is one held-out person, sorted from youngest to oldest. Each column is the probability the model gives to a first digit. The original model (left) spreads its bets over 2, 3 and 4 for everyone. After round 1, the probability follows the true first digit (the orange staircase). Rounds 2 and 3 sharpen it further.

![Tens digit distribution](/figures/f07_tens_digit.png)

> **Opus's contribution in round 1:** the diagnosis (first digit stuck on 2–4), the edit design (quadratic prior, position gate, end-of-answer guard), every fitted vector and parameter, the recovery from its own failed attempt, and the decision to stop at 8 of 20 evaluations.

### The result: better answers, nearly the same knowledge

On the 3,191 held-out people, error fell from **14.2 to 11.4 years** (−2.8, CI −3.2 to −2.3). But the information measures barely moved:

- **Correlation** with true age rose only from 0.681 to 0.697 (+0.016).
- **The best possible rescaling** of the answers improved only from 11.07 to 10.84 years. This is the error left after fitting the best straight-line correction from predicted to true age on the held-out set itself.

Round 1 mostly corrected the model's habit of guessing too young. It did not make the model rank people much better. **It unlocked knowledge the model already had**, the same kind of fix as the original post's looping repair.

> **A cautionary baseline.** Before running Opus, I hand-built a simpler version of the same idea: tilt all digit probabilities toward the model's age estimate. Tuned on the same dev rows, it looked fine (13.2), but on a 200-person test set it made error **worse (16.7, vs 13.8 for the original model on the same people)**. Without a position gate it also pushed the second digit toward 0, so 89% of its answers ended in zero and collapsed onto 20, 40 and 80. Opus hit the same failure in one evaluation and engineered around it.

## 7. Round 2: Changing what the model computes

### The brief

A new Opus agent started from the round-1 model. It got 750 practice examples, 80 fresh dev rows and 15 evaluations. Its brief: make the model's age estimate **better**, not just recalibrated. An honest negative result was acceptable.

### What Opus found

Analysing the practice data before spending any evaluations, it found:

- **Unused information.** The internal states at the **blood-marker tokens** contain age information that never reaches the token where the answer is produced. Combining them with the answer token beats the best probe of the answer token alone (9.0 vs 9.8 years).
- **The second digit was uncontrolled.** Round 1 set only the first digit.
- **Round 1 had a side effect.** Its edit made the model answer some multiple-choice questions with a digit instead of a letter.

### The circuit it built

![Round 2 circuit](/figures/f14_round2_circuit.png)

All the changes are in **layer 27** plus the output rows, 290,783 weights or 0.039% of the model:

1. **A pooling head.** One attention head was rewired to attend _equally to every token_ in the prompt. One of its value channels reads an age signal at each blood-marker token. The head therefore delivers the **average age evidence from all the biomarkers** to the answer position.
2. **Five rebuilt neurons.** The five least-used neurons in the layer were turned into **gated circuits** that fire only when the model is writing an age. They set the first digit, the second digit, and the stop.
3. **New output rows** that pick the digit closest to the circuit's target. They replace round 1's ungated rows.

Opus used **2 of its 15 evaluations**. The full edit scored 7.96 on dev, from 10.38. Its ablation, removing the pooled biomarker signal but keeping everything else, scored 8.72. So routing the biomarker information is worth about 0.76 years on its own.

> **Opus's contribution in round 2:** finding the unused biomarker information and round 1's multiple-choice bug; the circuit design (pooling head, five gated neurons, new output rows); the choice of head 11, channel 119 and the five neurons; every fitted weight; and the ablation showing how much of the gain is new information.

### The result: The model knows more

![Recalibration vs information](/figures/f13_calibration_vs_information.png)

**This is the key figure.** The light bars are each model's error as answered; the dark bars are the error after the best possible rescaling. For the original model and round 1, rescaling stalls at about 11 years. **Round 2's answers are already well calibrated (9.07 as answered, 9.10 rescaled) and sit almost two years below anything rescaling can reach.** Correlation rose from 0.70 to **0.79** (+0.10, CI +0.08 to +0.11).

Rescaling cannot create information. So round 2's gain means the model's answers now carry more information about a person's age, delivered by circuitry Opus wrote into the weights.

![Predicted vs true age](/figures/f06_scatter.png)

The scatter plots show the same thing: round 2's predictions follow the diagonal across the full age range. It also uses the second digit properly: 74 distinct answers instead of 38, and only 18% of answers end in zero, against 42% for the original model.

## 8. Round 3: Pushing the same direction further

### What Opus found and built

A third agent started from the round-2 model, with 80 more fresh dev rows. Its analysis found that most of the information still left unused sits in **three specific biomarkers: Cystatin C** (a well-known kidney and aging marker), **Vitamin E and Albumin**. It also found that their values are readable from the model's own layer-24 states.

So it **rewired three attention heads in layer 24 into "reader" heads**. Each has a fixed query that puts about 99% of its attention on one biomarker's value (89% for Vitamin E). Each decodes a nonlinear age correction from that value and passes it to round 2's digit neurons. It used 5 of 15 evaluations. Dev error went from 7.66 to 7.33.

> **Opus's contribution in round 3:** the brief suggested targeted reading of specific biomarkers; Opus turned that into a working edit by identifying the three biomarkers; designing content-addressed reader heads and their nonlinear decoders; refitting the read-out; the ablation; and an explicit warning that its accepted result carries some dev selection.

### The result: A smaller step, in the same direction

![Progression](/figures/f16_progression.png)

| 3,191 held-out people | Error (MAE) | Correlation | Error after best rescaling | Error, ages 75–90 |
| --------------------- | ----------- | ----------- | -------------------------- | ----------------- |
| Round 2               | 9.07        | 0.792       | 9.10                       | 12.3              |
| **Round 3**           | **8.70**    | **0.807**   | **8.74**                   | **11.4**          |

**Round 3's step over round 2 is statistically significant in both error and correlation:** error −0.37 years (CI −0.54 to −0.19), correlation +0.015 (CI +0.007 to +0.023). Best-rescaling error also improves, 9.10 → 8.74, so it is mostly an information gain. On the official mini split, error went from 9.87 to 8.89 and correlation from 0.81 to 0.86.

_(On our original 200-person test set alone, this step looked like noise: −0.30, CI −0.96 to +0.38. The 3,191-person evaluation resolved it.)_

**The direction kept paying off, with clearly diminishing returns.** Round 2 captured the big structural win: getting biomarker evidence to the answer at all. Round 3 refines which biomarkers are read.

## 9. Checking the whole picture

### Held-out error, all versions

![Held-out results](/figures/f05_heldout.png)

| Version          | Held-out MAE (n=3,191) | 95% CI      | Correlation | Best-rescaling MAE | Mini MAE (n=45) |
| ---------------- | ---------------------- | ----------- | ----------- | ------------------ | --------------- |
| Original         | 14.18                  | 13.80–14.58 | 0.681       | 11.07              | 15.33           |
| Opus round 1     | 11.42                  | 11.12–11.73 | 0.697       | 10.84              | 11.04           |
| Opus round 2     | 9.07                   | 8.84–9.33   | 0.792       | 9.10               | 9.87            |
| **Opus round 3** | **8.70**               | 8.47–8.94   | **0.807**   | **8.74**           | **8.89**        |

Paired, on the same 3,191 people:

- round 1 vs original: −2.76 years (CI −3.20 to −2.30);
- round 2 vs round 1: −2.35 (−2.62 to −2.07);
- round 3 vs round 2: −0.37 (−0.54 to −0.19);
- **all three rounds vs original: −5.48 (−5.86 to −5.10), correlation +0.127 (+0.111 to +0.142)**.

My manual edit was only scored on the 200-person test set (16.7 vs 13.8 for the original).

### Who benefits

![Error by age](/figures/f09_age_bins.png)

The original model is accurate for young people only because it guesses young for everyone. Round 1 traded that away. Rounds 2 and 3 are much better for everyone from 30 upward; round 3 is best for ages 30–60 and the over-75s (12.3 → 11.4 years). Two costs remain:

- the youngest group (18–30) is still worse than with the original model (9.9 vs 5.8);
- round 3 is slightly worse than round 2 for ages 60–75 (9.0 vs 8.0).

### Side effects: a bug, caught and fixed by Opus

![Multiple choice, all tasks](/figures/f19_mc_all_tasks.png)

Round 1's edit had a side effect I missed. On free-form multiple-choice questions, the model started answering with a digit instead of a letter. Across all 13 multiple-choice tasks in LongevityBench's mini split, 27% to 100% of its answers started with a digit, and free-form accuracy fell to near zero on most tasks. I had checked these tasks only by comparing the probabilities of the option letters, which hid the problem. **The round-2 agent discovered it on its own test prompts and designed its circuit to avoid it.** After round 2, every multiple-choice task is back to the original model's accuracy, to within one question, including DNA methylation, gene expression and proteomics tasks the agents never saw. Round 3 keeps this: no task moves by more than one question.

## 10. Does the improvement carry over to other data types?

A model that is better at aging biology should also be better at related tasks. To test this, we ran the edited models on three regression tasks they were never edited for: age from **blood proteins** (Olink proteomics), age from **DNA methylation** (GEO arrays, prompts of 20–30 thousand tokens), and **lifespan change of gene knockouts**.

![Cross-modality](/figures/f17_cross_modality.png)

|          | Blood-panel age (target task, n=3,191) | Protein age (n=40) | DNA-methylation age (n=45) | Lifespan change (n=26) |
| -------- | -------------------------------------- | ------------------ | -------------------------- | ---------------------- |
| Original | 14.2                                   | **6.5** (r 0.79)   | 22.6 (r 0.20)              | 18.4 (r 0.78)          |
| Round 1  | 11.4                                   | 13.4 (r 0.76)      | 25.3 (r 0.38)              | 82.6 (broken output)   |
| Round 2  | 9.1                                    | 21.2 (r 0.13)      | 22.3 (r 0.53)              | 21.8 (r 0.72)          |
| Round 3  | **8.7**                                | 17.1 (r 0.26)      | 22.6 (r 0.53)              | **17.6** (r 0.78)      |

_Errors in years (age) or percentage points (lifespan). Answers are capped at plausible limits (0–100 years for protein age, 0–110 for methylation age, −100% to +200% for lifespan change) so a single malformed answer cannot dominate._

- **Age from proteins: every round makes it worse, badly so for rounds 2 and 3.** The original model is already good at this task, better than at blood panels. But the age circuit Opus built fires on _any_ "how old is this person?" question, while the evidence it routes in was fitted only on blood-panel prompts. On a protein profile that evidence is meaningless, and it overrides the model's own good estimate. Round 2 even produces malformed answers such as "008". Opus fitted its gates to stay off for multiple-choice and chat prompts, but never tested age questions from other data types.
- **Age from DNA methylation: error unchanged, correlation up.** The original model is weak here (22.6 years). Rounds 2 and 3 leave the error the same while correlation rises from 0.20 to 0.53. With 45 people this is suggestive, not conclusive.
- **Lifespan change: broken by round 1, restored by round 2, slightly improved by round 3.** Round 1's ungated rows corrupted the output format ("7.1%99"). Round 2's gating repaired it.
- **Multiple choice on every data type is unchanged** (Section 9).

**What this means.** Opus made the model substantially better at the task it was editing for, and it showed real care about the side effects it tested. But the edits _specialise_ the model: they do not make it a better aging model across data types, and they actively damage one. The fix is clear (include other data types' age questions as negative examples when fitting the gates), but it was not part of these runs.

## 11. How does the edited model compare with other open models?

We ran 24 open models on the same 400 held-out people with the same prompts, on a GPU. Answers were parsed from free text: the first number within the first 16 generated tokens. Answers with no number in that window were scored as a constant guess. Fourteen ran successfully. The other ten could not be scored: five gated models (Llama 3.x and Gemma 3, which need a licence-accepted access token), three that hit a full disk during download (SmolLM3-3B, OLMo-2-7B, Granite-3.3-8B), and two that failed to load (LFM2-1.2B, BioMistral-7B).

![Comparators](/figures/f18_comparators.png)

The figure and table show the models whose answers carry real information about age. Eleven other open models (0.5B to 8B) gave no number within 16 tokens, or answered with no relation to true age, and are not shown; they are described below.

| Model                                      | Size | Gives a number (within 16 tokens) | Age MAE | Correlation |
| ------------------------------------------ | ---- | --------------------------------- | ------- | ----------- |
| **Qwen3-0.6B-Longevity + Opus rounds 1–3** | 0.6B | 100%                              | **9.1** | **0.76**    |
| Insilico Qwen3-1.7B-Longevity              | 2.0B | 98%                               | 16.4    | 0.65        |
| Qwen3-0.6B-Longevity (original)            | 0.6B | 100%                              | 14.3    | 0.64        |
| Insilico longevity-llm (Qwen3.5-9B)        | 9.0B | 100%                              | 19.4    | 0.60        |
| Qwen2.5-1.5B-Instruct                      | 1.5B | 86%                               | 15.4    | 0.16        |

- **General-purpose open models do not do this task, at least not directly.** Seven models of 3–8 billion parameters gave no number within the first 16 tokens in any of the 400 cases. The smaller Qwen models we inspected on CPU typically refused outright (_"The participant's age is not provided in the clinical profile"_). Some larger, wordier models may give a number after a longer preamble, which this protocol does not capture. The small models that do answer show no relationship with true age.
- **Domain fine-tuning creates the ability.** All three Insilico longevity models answer with real signal (correlation 0.60–0.65).
- **Opus's edits make the 0.6B model better than all 14 comparison models on this task:** correlation 0.76 and 9.1 years of error, against 16.4 for Insilico's 3× larger 1.7B model and 19.4 for its 15× larger 9B model. Given Section 10, that claim is specific to blood-panel age.

## 12. Bonus: reading a model from its weights alone

The original post also showed that an LLM can work out what a network was trained on _from its weights alone_. We tried the same thing. A separate Opus agent got two checkpoints with neutral names: the Longevity model and the base Qwen3-0.6B, made identical in format. It was **not allowed to run either model**, only to do arithmetic on the weights.

![Fine-tuning footprint](/figures/f11_finetune_footprint.png)

| Opus's conclusion, from weights only                                                                                                                                                       | Truth                                      |                                        |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------ | -------------------------------------- |
| Checkpoint A is a fine-tune of B (99% confidence). Evidence: 124,377 embedding rows in A are _exactly_ 0.981 × B, the signature of weight decay on tokens that never appeared in training. | Correct                                    | ✅                                     |
| Output layer changed 7.2%, embeddings 4.1%                                                                                                                                                 | 7.1%, 4.0%                                 | ✅                                     |
| Change grows with depth and peaks around layer 25; key projections change most                                                                                                             | Matches the footprint above                | ✅                                     |
| Domain: aging biology. It named epigenetic clocks (Horvath, Hannum, GrimAge) and GrimAge's protein markers (cystatin C, TIMP-1, GDF15...) from which output rows had been trained          | Aging biology over omics and clinical data | ✅ domain (too focused on methylation) |
| Output format: prose explanations                                                                                                                                                          | Short letter and number answers            | ❌                                     |

The forensic trick is elegant. Weight decay shrinks _every_ weight at each step, but training only updates the rows of tokens that actually appear in the data. So the rows that are _not_ pure shrinkage spell out the fine-tuning vocabulary.

> **Opus's contribution here:** the whole analysis: the weight-decay forensics, the row-level vocabulary detector, the weight-difference "logit lens", and every conclusion in the table above.

_Integrity note: during the run the agent's process listing briefly showed another job's command line, which contained the model's name. Its time-stamped logs show it had already reached the aging conclusion from the weights._

## 13. How large are these edits?

![Edit size](/figures/f10_footprint_vs_post.png)

All three rounds together change 0.14% of the model's weights. That is between the original post's two headline edits (0.016% for the looping fix, 3.5% for a game-policy repair), though the tasks are not comparable.

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

The full code for rounds 2 and 3 is printed in the Colab notebook's provenance section.
