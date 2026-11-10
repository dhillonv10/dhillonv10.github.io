---
title: "Part 3: GRAFT Generalizes: A Second Program From the Same Library"
author: Vik Dhillon
pubDatetime: 2026-11-08T10:00:00-08:00
slug: graft-common-language-for-programming-model-weights
type: feature
draft: false
takeaways:
  - "**Does GRAFT generalize?** In the previous post, two Claude Opus agents compiled Levine's PhenoAge formula into `Qwen3-0.6B-Longevity` using a set of reusable weight-space surgeries I called **GRAFT**. Here is a fresh agent took the same library and compiled a second clinical program, **10-year mortality risk**, into the same model."
  - "**It worked, with no new instructions.** Held-out error is **1.02 percentage points** on 2,823 people. That beats a model trained on 750 people (1.91) and the original model (44.4)."
  - "**It took about 2 hours instead of 30,** because the parts and the safety rules already existed. Eight of PhenoAge's instructions were reused unchanged."
description: "A new agent took the PhenoAge library and compiled a second clinical program (10-year mortality risk) into the same model"
---

## Brief results

- **The second program beats a learned model.** Held-out error is **1.02 percentage points** on 2,823 people, against 44.4 for the original model, 8.30 for a constant guess, 6.43 for ridge regression and **1.91 for gradient boosting trained on 750 people**. It passes the same side-effect check as PhenoAge, and the edit rebuilds bit for bit.

- **Most of it was reuse.** Eight of PhenoAge's instructions went in unchanged and three were refit. The one new piece, a steep risk curve, was assembled from existing opcodes. The agent used 1 of its 10 scored calls and had an accepted edit about 2 h 20 min after launch; PhenoAge took two agents about 30 hours.

- **The library is small:**

  - **8 opcodes** (the elementary weight surgeries);
  - **14 instructions** with measured contracts;
  - **8 safety rules** learned from failures.

- **A graft** is a set of weight edits that switches on only for its own input, computes something, writes the result into the model, and is fully accounted for: which weights it touches, how to undo it exactly, and what it does to everything else.

- **Hello world of grafts:** one neuron (3,072 weights) makes the model answer "Hello" to one specific question and leaves everything else alone. Asked _"What is the GRAFT secret word?"_ the original model says "GRASP1" (a gene name); with the graft it says "Hello" in 12 of 12 contexts, including 4 it was never fitted on. Side effects are effectively zero (max KL 0.00000016, no changed answers). It also fires on one near-paraphrase, "…secret phrase?".

- **Combining grafts, honestly:** instructions are combined inside a program (14 in PhenoAge) and reused across programs (PhenoAge → mortality). **Two programs in one model at the same time has not been done yet.**

![GRAFT transfer](/figures/t1_graft_transfer.png)
_Figure 1. The second program. A: held-out error on 2,823 people, scored once. B: error by true risk level. C: what the agent reused, refit or built new, layer by layer. D: the second program against the first._

---

## 1. Was PhenoAge a one-off?

[Part 2](https://www.opsbug.com/posts/ai-agent-compiles-clinical-formula-into-weights/) ended with one compiled program. The agents had built a library along the way: Number readers, a unit converter, a logarithm, a summing head, a digit writer, and the safety rules that kept them from breaking the rest of the model. But a library that has built one program might just be that program, cut into pieces. The honest test is a second program: Give the library to a fresh agent, give it a new task, and see whether it can pick the right surgeries, apply them, and beat the baselines.

## 2. The test

- **Task:** 10-year mortality risk in percent, from the same blood panels, with Levine's mortality model: `M = 100·(1 − exp(−1.51714·exp(xb)/0.007692696))`. The question wording is new, and the output is a steep nonlinear curve that PhenoAge never needed.
- **Agent:** a fresh Claude Opus agent, working alone (no planner), given the PhenoAge workspace: the library, the PhenoAge program and its fitted vectors, and the run's logs. No human design input.
- **Budget:** 10 scored calls on 200 dev people; the 2,823 held-out people were scored once, by me, after the agent finished.
- **Pre-registered bar:** beat the original model, a constant prediction (8.30) and ridge regression (6.43) on held-out people, and pass the side-effect rule (max KL ≤ 0.5 over 165 unrelated probes, at most one changed answer among probes where the model had a clear preference). Gradient boosting (1.91) was a stretch comparison.

## 3. The result: it generalizes

| Held-out (n = 2,823), scored once                   | MAE (percentage points) | Edited minus comparator (95% CI) |
| --------------------------------------------------- | ----------------------- | -------------------------------- |
| Original model                                      | 44.44                   | −43.42 (−44.39 to −42.52)        |
| Constant guess                                      | 8.30                    | −7.28 (−7.78 to −6.78)           |
| Ridge regression (750 people)                       | 6.43                    | −5.41 (−5.63 to −5.20)           |
| Gradient boosting (750 people, given parsed values) | 1.91                    | **−0.89** (−1.04 to −0.75)       |
| **Model + GRAFT mortality program**                 | **1.02** (0.96–1.08)    |                                  |

Every pre-registered criterion is met, and the stretch comparison too.

![Answers vs truth](/figures/t3_answers_vs_truth.png)
_Figure 2. Each held-out person's true risk against the answer the edited model wrote (left) and gradient boosting's prediction (right)._

- **The original model doesn't know the formula.** It answers "70" or "72" for almost half of all people, whatever their profile.
- **Dev and held-out agree.** Dev MAE was 1.06 on 200 people; the agent had predicted 0.8–1.2 before its one scored call. Held-out came in at 1.02.
- **Every answer is well-formed:** all 2,823 are exactly two digits ("08", "23") followed by a stop. The median error is 0.4 points, and 77% of people are within 1 point.
- **It beats gradient boosting at every risk level, by most where it matters.** For people whose true risk is 50% or more, gradient boosting is off by 15.8 points and the graft by 4.8. A compiled formula extrapolates; a model trained on 750 mostly low-risk people can't. PhenoAge showed the same pattern in its oldest band.
- **Its errors still grow with risk.** At 20–50% risk the error is 3.2 points, and 15 people (0.5%) are off by more than 10. Small errors in the reused PhenoAge read-out get amplified by the steep curve. One visible failure mode in Figure 2 is the flat runs at 29, 39, 49 and 89: when the tens digit comes out one too low, the units digit can't make up the difference and saturates at 9. Those answers carry 28% of the total error.
- **Side effects pass.** Max KL 0.378, one clear answer changed (the limit is one), five near-ties flipped; multiple-choice accuracy went from 61 to 65 out of 105. An independent re-check on a fresh copy of the model reproduces these numbers exactly.
- **Reproducible.** Rebuilding the edit from the agent's recipe reproduces all 2,043,878 changed weights bit for bit.

## 4. Why it was fast: the library did most of the work

![Containment](/figures/t2_containment.png)
_Figure 3. A: every side-effect check the mortality agent ran, from its first full program (max KL 18, 33 answers changed) to the accepted edit 65 minutes later; hollow circles are partial installs used to locate the leak. B: the same "make it safe" phase for both programs on one clock: 8½ hours for PhenoAge, while the library was still being written; about one hour for mortality._

The agent's first complete version worked within about an hour of its first sandbox call. Its first full install leaked badly (max KL 18), and it found the leak in minutes by installing the program up to each stage in turn, the bisection trick PhenoAge had learned. It then hit two of the documented safety rules again (a gate open at position 0, and a gating read with too little margin on unrelated text) and fixed both within the hour, because the fixes were written down. One scored call, then it stopped on its own.

What it reused, refit and built:

| Layer   | Instruction                                    | In the mortality program                                                 |
| ------- | ---------------------------------------------- | ------------------------------------------------------------------------ |
| L3      | ANCHOR (spot the question)                     | **refit** on the new question wording, same 3 neuron pairs               |
| L4      | FLAG (switch on for this prompt only)          | **refit**: key offset re-centred on the new anchor                       |
| L4      | FB (on/off signal for the rest of the prompt)  | reused unchanged                                                         |
| L6–L7   | PINS (label every digit and marker)            | reused unchanged                                                         |
| L9      | SHIFT, BITS (move digits; exact binary digits) | reused unchanged                                                         |
| L10–L11 | AFFINE, LOG_PWL (per-marker years; ln(CRP))    | reused unchanged                                                         |
| L12     | SUM_POOL (add the ten terms)                   | reused unchanged                                                         |
| L12     | GATED_Z (tens/units targets)                   | **refit** reads                                                          |
| L13     | the risk curve                                 | **new**, built from 10 `kink` opcodes and 2 `step` opcodes               |
| L14     | EMIT + stop (write two digits, then end)       | instruction reused, moved one layer; stop step new, from a `step` opcode |

## 5. The library: Repeatable _surgeries_

Everything above was assembled from a small set of parts. They come in three levels, like a processor's instruction set.

**Opcodes** are the elementary surgeries. Each one is a specific, small weight edit with an exact mathematical effect.

| Opcode                   | What it does                                                                        | Weights it touches           | Used in                                            |
| ------------------------ | ----------------------------------------------------------------------------------- | ---------------------------- | -------------------------------------------------- |
| `step`                   | a gated switch: writes a fixed vector times a read when its gate is on, ~0 when off | 2 MLP neurons                | both programs                                      |
| `gated_linear`           | "if this token is marker _k_, write _w_ × its value"                                | 2 MLP neurons                | both                                               |
| `kink`                   | one ReLU-like segment; chains of kinks draw curves (ln, exp)                        | 1 MLP neuron                 | both (ln in PhenoAge, the risk curve in mortality) |
| `keyswitch` / `qswitch`  | redirect an attention head's keys or queries, only when a private signal is present | 128 rows, added on top       | both                                               |
| `vtake` / `vadd`         | take over or add to one value channel of an attention head                          | 1 value row + output columns | both                                               |
| `head_take` / `group_kv` | replace a whole head                                                                | 128 rows                     | built, never needed                                |

**Instructions** are opcodes composed into useful operations, each with a **measured contract**: What it guarantees, how precisely, and at what side-effect cost. These are the _"surgeries"_ an agent picks from.

| Instruction       | Built from                            | Contract (as measured in PhenoAge)                                         | Mortality                   |
| ----------------- | ------------------------------------- | -------------------------------------------------------------------------- | --------------------------- |
| ANCHOR            | `step` pairs on fixed question tokens | fires only on the question line                                            | refit                       |
| FLAG              | `keyswitch` + `vtake`                 | every later token "knows" this is the target question (0.998 attention)    | refit                       |
| FB                | `step` (norm-tracking)                | a clean on/off signal for the rest of the prompt                           | reused                      |
| PINS              | conjunction `step`s                   | every digit, marker and answer slot labelled; 0 wrong in 327,000 tokens    | reused                      |
| SHIFT             | `keyswitch` + `qswitch`               | a marker's digits copied onto it (99.99% of attention on the right digit)  | reused                      |
| BITS              | `step`s                               | exact binary digits, ≤ 1 error in 798 on rare digits                       | reused                      |
| AFFINE            | `gated_linear`                        | each marker's contribution, unit conversion folded in (sd 0.04–0.28 years) | reused                      |
| LOG_PWL           | 12 `kink`s                            | ln(x) to sd 0.22 years                                                     | reused                      |
| SUM_POOL          | `qswitch` + `keyswitch`               | one head adds all markers at the answer (weights within 0.8% of equal)     | reused                      |
| POOL_VTAKE        | `vtake`                               | carries the sum to the answer slot, gain-limited for safety                | reused                      |
| GATED_Z           | `gated_linear` + `step`               | tens and units targets at the two answer positions                         | refit                       |
| EMIT              | `kink`s + `step`                      | writes the digit token whose number is closest to the target               | reused (moved)              |
| ANSWER-ZERO guard | constant read                         | keeps answer-only gates shut everywhere else                               | refit, with EMIT            |
| DIGIT-AUGMENT     | refit procedure                       | decoders refit on rare digits (30-year misses → 0)                         | reused (its refit decoders) |

**Programs** are instructions in order, layer by layer: PhenoAge (14 instructions, 1.96 M weights) and mortality (2.04 M weights). Counted the way the mortality agent reported its program's stages, it reused 8 unchanged (FB, PINS, the marker labels, SHIFT, BITS, AFFINE, LOG_PWL, SUM_POOL), refit 3 (ANCHOR, FLAG, GATED_Z) and added one curve plus a stop step.

![The GRAFT library](/figures/o5_graft_catalog.png)
_Figure 4. The library on one page: opcodes compose into instructions with measured contracts; instructions compose into programs. Both programs are compiled._

The library also includes **eight safety rules**, each learned from a failure in the PhenoAge run, and the mortality agent re-used several of them directly: placement is empirical (choose neurons, then let the side-effect check decide); switch attention heads, never remove them; every write is tiny, dominant or scaled with the token; guard every read that gates a large write; never tune on the test probes; treat the first token of a prompt as its own case; subtract an old edit before re-installing it; one configuration per install.

## 6. What is a graft?

A **graft** is a set of weight edits in a pretrained model with four properties:

1. **Gated.** It switches on only for its own input (a specific question, a specific token). Everywhere else its neurons output essentially zero. Without a gate, a weight edit is fine-tuning: it changes the model everywhere.
2. **It computes something.** It reads information already in the model's internal state, transforms it (a sum, a logarithm, a lookup), and writes the result back where later layers, or the output, will use it.
3. **Accounted for.** The exact weights it touches are listed, it can be undone exactly by writing the originals back, and it rebuilds bit for bit from its recipe.
4. **Measured.** Each graft carries a measured claim about what it computes, and a measurement of what it does to everything else (here: 165 unrelated probes, before and after).

Every value in a graft comes from a closed-form fit (least squares, linear discriminants, linear programs, eigenvectors) or a measurement. Nothing is trained by gradient descent.

## 7. Anatomy of a graft

A graft is made of five parts. Here they are for the smallest real one, the hello-world graft from §8, which is a single MLP neuron:

| Part        | What it is                           | In the hello-world graft                                                                                            |
| ----------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| **Site**    | the exact weights edited             | neuron 2097 of the last layer (layer 27): its gate row, up row and down column; 3,072 weights                       |
| **Gate**    | the read that decides when it fires  | a linear detector on the last layer's input, fit to tell this one question apart from every token of unrelated text |
| **Read**    | what it takes from the model's state | a constant read (≈ 1 on every token), so how much the neuron writes is set by the gate alone                        |
| **Compute** | the nonlinearity                     | the neuron's own SiLU: ≈ 0 when the gate is negative, linear when positive (the `kink` opcode)                      |
| **Write**   | where the result goes                | the direction that raises the logit of "Hello", sized to dominate the last layer's output                           |

Bigger grafts are the same parts, more of them, and wired together: PhenoAge's PINS gate on the output of ANCHOR and FLAG, SUM_POOL reads what AFFINE wrote, and EMIT reads what SUM_POOL wrote.

![Anatomy of the hello-world graft](/figures/h1_hello_graft.png)
_Figure 5. The hello-world graft. A: its anatomy, one neuron. B: the gate value on the target question versus every token of held-out unrelated text. C: what the model answers before and after._

## 8. Hello world of grafts

The smallest graft that visibly changes behaviour: when asked _"What is the GRAFT secret word?"_, the model answers **"Hello"**. Everything else should stay the same. I built it (the supervising Claude session) to illustrate the anatomy; the agents did not build it, and it follows the same rules they did.

**How it was built** (closed-form fits only):

1. Collect the last layer's input at the answer position for the question in 8 contexts (no system prompt, three system prompts, two earlier conversation turns, and combinations), and at every token of about 95 unrelated prompts (other benchmark questions, PhenoAge prompts) and 23 short questions, 7 of them near-misses ("What is the secret word?", "What is the GRAFT password?", "What is the GRAFT secret number?", and so on). That is about 57,000 negative tokens.
2. Fit a linear detector for "this is the secret-word question" (shrinkage linear discriminant analysis) and a constant read (ridge regression).
3. Pick the least-used neuron in the last layer (neuron 2097) and overwrite its three weight vectors: gate row = the detector, up row = the constant read, down column = a push toward the token "Hello", sized to dominate the output there.

**What it does** (Figure 5; run on a Colab GPU):

| Test                                                        | Original model     | With the graft                                                                                    |
| ----------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------- |
| _"What is the GRAFT secret word?"_ in the 8 fitted contexts | "GRASP1"           | **"Hello, I am…"** (8 / 8)                                                                        |
| The same question in 4 contexts it was never fitted on      | "GRASP1", "GRASP." | **"Hello…"** (4 / 4)                                                                              |
| 8 held-out near-miss questions                              | various            | 7 unchanged, word for word; 1 changed (below)                                                     |
| Gate on 14,913 held-out tokens of unrelated text            |                    | open on 1 token (the near-miss below); median gate value −307, against +17 to +29 on the question |
| Side effects on 165 unrelated probes                        |                    | max KL 0.00000016; 0 changed answers; multiple-choice 61 → 61 / 105                               |

**The one leak is the lesson.** _"What is the GRAFT secret phrase?"_ also gets "Hello" (gate value +3.4, just over the threshold), while "…secret code?", "…secret word in French?", "Is there a GRAFT secret word?" and five other near-misses stay exactly as they were. A gate is a detector, and it is only as specific as the near-misses it was shown: "secret phrase" was not among them, and it sits closer to the target than anything that was. That is the same lesson the PhenoAge run learned at scale (rule: guard every read that gates a large write), here in one neuron.

**A first attempt was weaker, and is worth reporting.** I first used the question _"What is the GRAFT hello-world reply?"_. It worked (12 / 12, side effects near zero), but the original model already answered "HELLO-World!", so the before/after showed little, and the gate also fired on "…hello-world **program**?". Switching to a question the model would never answer with "Hello", and adding near-miss questions to the negatives, fixed both.

## 9. Combining grafts: what was actually done

"Combining" has meant three different things, and only two of them have been done.

1. **Combining instructions inside one program: done.** PhenoAge is 14 instructions installed in sequence, each reading what earlier ones wrote. They were written at different times and re-installed hundreds of times during the run, which is where the rules for combining came from:
   - **Each replaced neuron has one owner.** A second instruction claiming the same neuron is an error.
   - **Additive edits stack, and can double up.** Re-installing an instruction on weights that already contain it applies its additive part twice unless the old copy is subtracted first. This bug happened.
   - **Side effects don't add up neatly.** Removing 10 neurons from one layer cost a max KL of 0.11; removing 24 cost 0.55. Every combination has to be measured again.
2. **Reusing instructions across programs: done.** The mortality program reused 8 of PhenoAge's instructions unchanged, refit 3, and built one new curve from existing opcodes (§4). This is the result of this post.
3. **Two programs in one model at the same time: not done yet.** The mortality edit is a separate edit of the original model. It reuses PhenoAge's neurons and refits its question detector, so the mortality model answers mortality but no longer PhenoAge. Running both side by side, each gated by its own question, is the next experiment, and the ownership and re-measurement rules above are what it will need.

## 10. What this shows, and what it doesn't

**It shows:**

- A library of weight surgeries built for one task carried over to a second task, with no new instructions, and the second program beat a learned model.
- The second program was about 15× cheaper to build, because the parts and the safety rules already existed.
- The smallest unit is genuinely small: one gated neuron installed a new answer without measurably disturbing the rest of the model, though its gate also caught one close paraphrase.

**It doesn't show (yet):**

- **A different kind of task.** Mortality reuses PhenoAge's inputs and readers, which is why it was fast. A task with different inputs would reuse less.
- **A different model.** Everything so far is on one model, `Qwen3-0.6B-Longevity`.
- **Reliability.** One second program, one agent run.
- **Paraphrases.** Both programs switch on for an exact question wording.
