---
title: "Weight-Space Programming for Longevity Models"
subtitle: "Can an AI Agent Improve a Biology Model by Editing Its Weights?"
author: Vikram Dhillon
pubDatetime: 2026-11-04T00:00:00.000Z
slug: ai-agent-edits-biology-model-weights
featured: true
draft: false
takeaways:
  - "Claude Opus 5.5 edited the weights of a small aging-biology model directly, with no training, and cut held-out age error from 13.8 to 8.4 years across three rounds."
  - "Round 1 unlocked knowledge the model already had: error fell, but correlation with true age did not move."
  - "Round 2 added new computation, a pooling attention head and five rebuilt neurons, and raised correlation from 0.69 to 0.80. No recalibration of the original model can reach that."
  - "Round 3 pushed the same direction, but its gain was small and not statistically significant on 200 people."
  - "Every edit came from Opus agents, and together they touch about 0.14% of the model's weights."
description: 'Claude Opus 5.5 edits Insilico Medicine''s open aging model directly, with no training. A replication and extension of "Sparks of Weight-Space Programming."'
---

## The short version

We gave **Claude Opus 5.5** read and write access to the raw weights of [`Qwen3-0.6B-Longevity`](https://huggingface.co/insilicomedicine/Qwen3-0.6B-Longevity), a small open model fine-tuned on aging biology. The job was to make it better at estimating a person's **age from a routine blood panel**. It could not train the model with gradient descent. It had to read the weights and activations, decide what to change, and write the change itself. Every number in this table is measured on **200 people the agent never saw**:

|                | What Opus changed                                     | Age error (MAE) | Correlation with true age |
| -------------- | ----------------------------------------------------- | --------------- | ------------------------- |
| Original model | —                                                     | 13.8 years      | 0.69                      |
| **Round 1**    | 10 rows of the output layer                           | 11.8 years      | 0.67                      |
| **Round 2**    | a new pooling attention head and 5 rebuilt neurons    | **8.7 years**   | **0.80**                  |
| **Round 3**    | 3 attention heads rewired to read specific biomarkers | **8.4 years**   | 0.80                      |

The three rounds show three different things:

1. **Round 1 unlocked what the model already knew.** The model's internal age estimate was better than its answers; Opus fixed the read-out. Error dropped, correlation did not change.
2. **Round 2 changed what the model computes.** Opus wrote new circuitry that carries information to the answer that never reached it before. Error dropped by 5.1 years versus the original (95% CI 3.8 to 6.5) and correlation rose. No recalibration of the original model can reach this result.
3. **Round 3 went further in the same direction.** The gain was smaller and not statistically significant on 200 people (−0.3 years, CI −1.0 to +0.4). It is a direction with diminishing returns.

**Every diagnosis, design and weight change in these results was produced by Claude Opus 5.5 agents.** My part was building the sandbox and measuring the results (see Section 3). Along the way, Opus found and fixed a bug that its own round-1 edit had introduced, and that I had missed. A separate Opus agent also identified the model's training domain from the weights alone, without running the model once.

---

## 1. The question

In [_Sparks of Weight-Space Programming_](https://rikiyat.github.io/blog/weight-space-programming/), Takehi, Teoh, Zhang and Khattab showed that a frontier LLM can read and write neural-network weights directly. Their most striking result: given a Python kernel and a budget of forward passes, the LLM found a "looping" direction inside Qwen3.5-0.8B and removed it, raising its MATH-500 score from 7.9 to 48.1. Their control experiment set the limit. On a model that did not loop, the same procedure did nothing. **Editing could remove an obstacle, but it could not add an ability.**

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

**Keeping it honest.**

- **Disjoint data.** Practice rows, dev rows, the 200-person **held-out test set** and LongevityBench's official _mini_ split never overlap. Each round got fresh dev rows.
- **Held-out scoring.** The agents never see test labels. Every result in this post is a held-out number unless it says "dev".
- **Server-side logs.** The sandbox server logged every request the agents made, so their reports could be audited.
- **Exact reproducibility.** Each edit was rebuilt from the agent's saved code and vectors, and reproduced its dev score exactly.
- **Division of labour.** I built the sandbox and the evaluation. **Every edit, vector, index and hyper-parameter came from an Opus agent** (details in Section 3).

## 3. Who did what: where Opus is used and what it contributed

Opus was used as an **autonomous research agent**. Each agent was a fresh Claude Opus 5.5 session with a shell. It talked to the model only through the sandbox, and did all the analysis and editing itself. We ran **four separate agents**:

| Agent                   | What it was given                                                                                                                                                             | What Opus contributed                                                                                                                                                                                                                                                                                                                          |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Round 1 editor**      | The model in a sandbox, 150 labelled practice prompts, 20 dev evaluations, and a one-page task description with **no hints** about what to change                             | Diagnosed the problem (the first digit stuck on 2/3/4; internal age estimate better than the answers). Designed the edit (quadratic prior over the first digit, position gate, end-of-answer guard). Fitted every vector (three ridge regressions and an SVD). Chose all parameters, wrote the code, and decided when to stop (8 evaluations). |
| **Round 2 editor**      | The round-1 model, round 1's code and summary, 750 practice prompts, 15 evaluations; asked for _better information, not recalibration_, with a list of directions to consider | Found the unused information at the biomarker tokens. Found round 1's multiple-choice bug. Designed and built the circuit: chose head 11, value channel 119 and the five least-used neurons, and fitted all their weights. Ran the ablation that separates information from read-out.                                                          |
| **Round 3 editor**      | The round-2 model, rounds 1–2's code and summaries, the same practice prompts, 15 evaluations; brief suggested targeted reading of specific biomarkers                        | Identified Cystatin C, Vitamin E and Albumin as the remaining unused signal. Designed the three fixed-query reader heads (found by discriminant analysis on the existing keys) and their nonlinear decoders. Refit the read-out, ran an ablation, and flagged its own dev-selection risk.                                                      |
| **Blind weight reader** | Two anonymised checkpoints and the tokenizer; **no forward passes allowed**                                                                                                   | Worked out which checkpoint was fine-tuned from which, measured where the weights changed, and identified the training domain, all from arithmetic on the weights.                                                                                                                                                                             |

**What I did (the human side, assisted by a separate Claude session):**

- built the sandbox: weight access, practice data, the `evaluate` budget, automatic revert, edit-size cap and request logging;
- ran the initial probe diagnosis (Section 5) and chose the task, the data splits and the scoring;
- wrote each round's task brief;
- restarted the sandbox when it ran out of memory;
- rebuilt each edit from the agent's saved code and vectors and verified that it reproduced the dev score exactly;
- ran all held-out evaluations and made the figures.

**What I did not do:** choose, write, tune or suggest any specific edit, layer, head, neuron, vector or parameter value. The one manual edit in this post is my own baseline, labelled as such, and it performed worse.

**Where my briefs did steer (so you can judge for yourself):**

- **The diagnosis in Section 5 is mine.** I ran the probes before any agent existed, to decide which task to aim at. The round-1 agent never saw them and found the same gap independently.
- **Round 1's brief** described only the task, the tools and the rules. It contained no hints.
- **Round 2's brief** said the goal was a _better age estimate, not recalibration_. It listed directions worth considering: bring in information from other token positions or layers, implant new computation in neurons or attention heads, control the second digit. Opus chose among them, found the specific unused signal, and designed and fitted the circuit.
- **Round 3's brief** included round 2's results and analysis. It explicitly suggested _targeted_ reading, for example attention that picks out specific biomarker tokens, plus nonlinear features. Opus built essentially that. So round 3's _idea_ was prompted. Opus's contribution there was identifying which three biomarkers, finding the queries that select them, designing the nonlinear decoders, fitting every weight, and evaluating and ablating the result.

**How we know the agents stayed in bounds.** Each agent was told to work only in its own folder and to reach the model only through the sandbox. The sandbox server logged every request independently of the agents' own reports, and those logs match the reports. The one exception is disclosed in Section 10 (Bonus).

## 4. Where the model starts

![Baseline performance](/figures/f02_baselines.png)

The base Qwen3-0.6B is at chance on these tasks. The fine-tuned Longevity model is clearly better: 69% vs 49% at telling which of two people is older, and 69% vs 51% at predicting 10-year survival. But its age estimates are poor: 15.3 years of error on the mini split, barely better than always guessing the median age (17.6).

## 5. Diagnosis: the model knows more than it says

Before running any agent, I checked whether there was a gap between what the network _computes_ and what it _outputs_. _(This diagnosis is mine, not Opus's; the round-1 agent found the same gap on its own.)_ The test was simple: fit a linear probe from the model's internal state to the true age, at every layer.

![Probes](/figures/f03_probes.png)

- **The Longevity model knows age much better than it says.** A probe on its internal state gets about **10.7 years** of error, while the model's own answers have **13.8**. The information appears abruptly around layer 15.
- **The base model knows almost nothing about age.** No layer is much better than guessing the median. **Fine-tuning built the age representation.**
- **Control: mortality.** For 10-year mortality, the probe and the model agree (0.90 vs 0.89). There is no gap and nothing to unlock, so we pointed the agents at age.

## 6. Round 1: unlocking what the model already knows

### What Opus did

![Round 1 search](/figures/f04_trajectory.png)

The round-1 agent first studied the model's answers. It found that the model always answers with two digits and that **the first digit is almost always 2, 3 or 4**, so the model rarely says anyone is over 50.

Its first edit added a _quadratic prior_ over the first digit, centred on the model's own internal age estimate. Dev error dropped from 15.3 to 10.8. Its second attempt **blew up to 30.3**: the change leaked into later digits and produced three-digit ages. Opus diagnosed the leak and added two safeguards:

- a **position gate**, so the edit acts only on the first digit;
- an **end-of-answer guard**, so the model stops after two digits.

Its 7th evaluation was accepted at 9.8. It stopped after 8 of 20 evaluations. The final edit changes **10 rows of the output layer**, 10,240 weights or 0.0014% of the model.

### What it does

![Digit probabilities](/figures/f08_digit_heatmap.png)

Each row of this heatmap is one held-out person, sorted from youngest to oldest. Each column is the probability the model gives to a first digit. The original model (left) spreads its bets over 2, 3 and 4 for everyone. After round 1, the probability follows the true first digit (the orange staircase).

![Tens digit distribution](/figures/f07_tens_digit.png)

> **Opus's contribution in round 1:** the diagnosis (first digit stuck on 2–4), the edit design (quadratic prior, position gate, end-of-answer guard), every fitted vector and parameter, the recovery from its own failed attempt, and the decision to stop at 8 of 20 evaluations.

### The result: better answers, same knowledge

On the held-out set, error fell from **13.8 to 11.8 years** (−2.0, CI −3.7 to −0.3). But two numbers did not move:

- **Correlation** with true age was unchanged (0.69 to 0.67).
- **The best possible rescaling** of the answers was no better than for the original model: 11.1 vs 10.9 years. This is the error left after fitting the best straight-line correction from predicted to true age on the test set itself.

Round 1 corrected the model's habit of guessing too young. It did not make the model rank people better. **It unlocked knowledge the model already had**, the same kind of fix as the original post's looping repair.

> **A cautionary baseline.** Before running Opus, I hand-built a simpler version of the same idea: tilt all digit probabilities toward the model's age estimate. Tuned on the same dev rows, it looked fine (13.2), but on held-out data it made error **worse (16.7)**. Without a position gate it also pushed the second digit toward 0, so 89% of its answers ended in zero and collapsed onto 20, 40 and 80. Opus hit the same failure in one evaluation and engineered around it.

## 7. Round 2: changing what the model computes

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

### The result: the model knows more

![Recalibration vs information](/figures/f13_calibration_vs_information.png)

**This is the key figure.** The light bars are each model's error as answered; the dark bars are the error after the best possible rescaling. For the original model and round 1, rescaling stalls at about 11 years. **Round 2's answers are already well calibrated (8.69 as answered, 8.71 rescaled) and sit more than two years below anything rescaling can reach.** Correlation rose from 0.69 to **0.80** (+0.11, CI +0.06 to +0.16).

Rescaling cannot create information. So round 2's gain means the model's answers now carry more information about a person's age, delivered by circuitry Opus wrote into the weights.

![Predicted vs true age](/figures/f06_scatter.png)

The scatter plots show the same thing: round 2's predictions follow the diagonal across the full age range. It also uses the second digit properly: 56 distinct answers instead of 28, and only 16% of answers end in zero, against 42% for the original model.

## 8. Round 3: pushing the same direction further

### What Opus found and built

A third agent started from the round-2 model, with 80 more fresh dev rows. Its analysis found that most of the information still left unused sits in **three specific biomarkers: Cystatin C** (a well-known kidney and aging marker), **Vitamin E and Albumin**. It also found that their values are readable from the model's own layer-24 states.

So it **rewired three attention heads in layer 24 into "reader" heads**. Each has a fixed query that puts about 99% of its attention on one biomarker's value (89% for Vitamin E). Each decodes a nonlinear age correction from that value and passes it to round 2's digit neurons. It used 5 of 15 evaluations. Dev error went from 7.66 to 7.33.

> **Opus's contribution in round 3:** the brief suggested targeted reading of specific biomarkers; Opus turned that into a working edit by identifying the three biomarkers; designing content-addressed reader heads and their nonlinear decoders; refitting the read-out; the ablation; and an explicit warning that its accepted result carries some dev selection.

### The result: a smaller step, in the same direction

![Progression](/figures/f16_progression.png)

| 200 held-out people | Error (MAE) | Correlation | Error after best rescaling | Error, ages 75–90 |
| ------------------- | ----------- | ----------- | -------------------------- | ----------------- |
| Round 2             | 8.69        | 0.798       | 8.71                       | 13.0              |
| **Round 3**         | **8.38**    | 0.796       | **8.54**                   | **10.3**          |

On the official mini split, error went from 9.87 to **8.89** and correlation from 0.81 to **0.86**.

Round 3 moves nearly every headline number the right way, and it helps the oldest people most. But **its step over round 2 is not statistically significant** (−0.30 years, CI −0.96 to +0.38), and test correlation is flat. Its own ablation credits only part of the dev gain to the new readers. **The direction kept paying off, with clearly diminishing returns.** Round 2 captured the big structural win: getting biomarker evidence to the answer at all. Round 3 refines which biomarkers are read.

## 9. Checking the whole picture

### Held-out error, all versions

![Held-out results](/figures/f05_heldout.png)

| Version          | Test MAE | 95% CI    | Correlation | Best-rescaling MAE | Mini MAE |
| ---------------- | -------- | --------- | ----------- | ------------------ | -------- |
| Original         | 13.82    | 12.4–15.3 | 0.688       | 10.90              | 15.33    |
| My manual edit   | 16.73    | 15.1–18.3 | 0.660       | 11.32              | 15.56    |
| Opus round 1     | 11.79    | 10.6–13.0 | 0.671       | 11.14              | 11.04    |
| Opus round 2     | 8.69     | 7.7–9.7   | 0.798       | 8.71               | 9.87     |
| **Opus round 3** | **8.38** | 7.4–9.5   | 0.796       | **8.54**           | **8.89** |

Each round's dev numbers were also confirmed on dev rows nobody had tuned on:

- round 2's dev set: original 12.75, round 1 10.38, round 2 7.96;
- round 3's dev set: original 13.31, round 1 10.72, round 2 7.66, round 3 7.33.

### Who benefits

![Error by age](/figures/f09_age_bins.png)

The original model is accurate for young people only because it guesses young for everyone. Round 1 traded that away. Rounds 2 and 3 are best in every age band from 30 upward, and round 3 helps the over-75s most. The youngest group (18–30) is still worse than with the original model.

### Side effects: a bug, caught and fixed by Opus

![Multiple choice](/figures/f15_multiple_choice.png)

Round 1's edit had a side effect I missed. On free-form multiple-choice questions, the model started answering with a digit instead of a letter, on **222 of 225** questions. I had checked these tasks only by comparing the probabilities of the option letters, which hid the problem. **The round-2 agent discovered it on its own test prompts and designed its circuit to avoid it.** After round 2, every multiple-choice task matched the original model exactly. Round 3 kept letter answers intact; two tasks changed by one question each, both toward the right answer. Mortality accuracy stayed at 0.875 throughout.

## 10. Bonus: reading a model from its weights alone

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

## 11. How large are these edits?

![Edit size](/figures/f10_footprint_vs_post.png)

All three rounds together change 0.14% of the model's weights. That is between the original post's two headline edits (0.016% for the looping fix, 3.5% for a game-policy repair), though the tasks are not comparable.

## 12. What this shows

1. **Weight-space programming works on a biology model.** With a small evaluation budget and no training, Opus cut held-out age error by 5.4 years (CI 3.9 to 7.0), from 13.8 to 8.4.
2. **It goes beyond unlocking.** Round 1 behaved like the original post's result: it removed an obstacle between what the model knew and what it said. Round 2 is different. Opus built new circuitry, a pooling head and gated neurons, that delivers information the original output path never had. Correlation and the rescaling test show the model genuinely knows more.
3. **Progress in that direction continued, but with diminishing returns.** Round 3 made a smaller, not-yet-significant step in the same direction.
4. **The agent was careful in ways that mattered.** Opus engineered safeguards after a failure, ran its own ablations, flagged its own dev-selection risks, and caught a side effect I had missed.
5. **The division of labour.** I chose the task and, from round 2 on, framed which _kinds_ of improvement to look for. The agents did the discovery, the design and the weight-writing.

## 13. Limitations

- **Small samples, one run per round.** Test is 200 people and mini 45. Round 3's step is within noise.
- **Dev numbers are optimistic.** All dev results were partly selected; only held-out numbers count.
- **Partly read-out.** By Opus's ablations, about a third of round 2's dev gain comes from routed information and the rest from a better read-out. Both are new weights, but only the first is new information.
- **The youngest participants** are still worse off than with the original model.
- **Scope.** These are NHANES blood-panel tasks, in non-thinking mode, on a CPU. A larger evaluation is running in the Colab notebook below. It covers about 3,200 held-out people, all 17 LongevityBench tasks (including DNA methylation and proteomics) and about 24 open-source comparison models.
- **The sandbox shapes the solutions.** I chose the tools; different tools could lead the agent elsewhere.
- **Licences.** The model is CC-BY-ND, so we share the _recipe_ (code and vectors that rebuild each edit from the original weights), not edited weights.

## 14. Reproduce it

- **`opus_weight_edits_longevity.ipynb`** with **`opus_edits_bundle.pt`** (195 KB). The bundle contains only Opus-computed vectors, code, the agents' own summaries and the server logs. The notebook does the following:
  - applies each round's edit exactly;
  - shows the live weight differences;
  - re-checks the dev numbers;
  - runs the large evaluation and the open-model comparisons;
  - exports all figure data.
- **`weight_space_longevity.ipynb`** runs the whole editing loop with an _open_ editor (Qwen3 or Kimi K2).

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
