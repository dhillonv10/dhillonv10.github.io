---
title: "Repeatable Weight Space Programming"
author: Vik Dhillon
pubDatetime: 2026-11-08T09:00:00-08:00
slug: ai-agent-compiles-clinical-formula-into-weights
type: feature
draft: false
takeaways:
  - "**Repeatable weight-space editing.** In Part 1, Claude Opus edited the weights of Insilico Medicine's `Qwen3-0.6B-Longevity` by hand to estimate age from a blood panel. Here, two Claude Opus agents built a set of reusable weight-space surgeries, which I'm calling **GRAFT**."
  - "**GRAFT compiled Levine's PhenoAge formula into the same model,** with no gradient descent and no human design input."
  - "**Held-out error fell from 10.63 to 1.52 years** on 2,823 people. That beats a model trained on 750 labelled people."
  - "**The rest of the model barely noticed:** its behaviour on unrelated prompts is essentially unchanged."
description: "Two Claude Opus agents built GRAFT, a set of reusable weight-space surgeries, and used it to compile Levine's PhenoAge formula into Qwen3-0.6B-Longevity with no gradient descent and no-human-in-the-loop."
---

## Brief results

- **GRAFT stands for Gated Reusable Algorithms For Transformers.** It's the name I'm giving the set of weight-space surgeries the agents built:

  - **8 opcodes** (gated switches, curve segments, attention-head switches);
  - **14 instructions** with measured contracts: Read a digit exactly, copy it to where it's needed, convert units, take a logarithm, sum ten terms, write the answer as digit tokens;
  - **8 safety rules**, each learned from a failure.

  Every graft is **gated**: It switches on only for its own question and stays off everywhere else.

- **The first GRAFT program is a clinical formula.** PhenoAge (Levine 2018) reads nine blood markers in mixed units plus age from free text, takes ln(CRP) and adds ten weighted terms. The program is 228 lines of library calls. It changes 1,957,862 weights (0.26% of the model), and every value is a closed-form fit.

  | Held-out (2,823 people), PhenoAge MAE   |                                                |
  | --------------------------------------- | ---------------------------------------------- |
  | Original model                          | 10.63 years (it mostly repeats the stated age) |
  | Gradient boosting trained on 750 people | 1.75 years                                     |
  | **Model + GRAFT PhenoAge program**      | **1.52 years** (95% CI 1.47–1.58)              |

- **The edited model beats the learned baseline,** by 0.22 years (95% CI 0.14–0.31), and the original model by 9.1 years.
- **It missed our pre-registered bar of 1.5 by 0.024 years.**
- **Grafts don't break the host.** On 165 unrelated probes, no answer the model had a clear preference on changed (max KL 0.358). Multiple-choice accuracy went from 61 to 63 out of 105. Five near-tie answers did flip.
- **No human designed any of it.** A planner agent and a surgeon agent built the library and the program over 33 hours.
- **It is reproducible bit for bit.** Running the recipe on a fresh copy of the original model reproduces every changed weight (sha256 match).

![GRAFT v0.1](/figures/o5_graft_catalog.png)
_Figure 1. GRAFT v0.1: opcodes compose into instructions with measured contracts; instructions compose into programs._

---

## 1. Where Part 1 left off

In [Part 1](https://www.opsbug.com/posts/ai-agent-edits-biology-model-weights/), Claude Opus edited this same model's weights over five rounds to estimate chronological age from a blood panel. It ended in a tie with tuned gradient boosting, at 8.25 years against 8.20. Each round was a bespoke surgery (for instance, a pooling head, some rebuilt neurons). The edits worked, but nothing carried over from one round to the next.

Two things changed my mind about what to try next:

1. **The task had no program to compile.** Chronological age from a blood panel is a statistical guess with an information ceiling, and 750 labels already reach it.
2. **Programmers don't write machine code by hand each time.** They use instruction sets and libraries. If weight edits can be turned into reusable primitives with clean interfaces and known side effects, each new capability gets cheaper than the last.

So this time, I asked the agents for an **instruction set**: Reusable surgeries with clean interfaces. And I chose a task with an exact answer to test it on

## 2. GRAFT (Gated Reusable Algorithms For Transformers)

In surgery, a graft is tissue you transplant so it becomes part of the host. Here, a **graft** is a small algorithm written directly into a model's weights: A handful of MLP neurons and attention-head edits that reads something from the prompt, computes on it, and writes the result back into the model's internal state. Three properties make it a graft rather than an ordinary weight edit:

- **Gated.** It fires only on its own question. Everywhere else its neurons output almost exactly zero, which is what lets you add it without damaging the host.
- **Accounted for.** It records exactly which weights it touches, so it can be undone exactly and rebuilt bit for bit.
- **Contracted.** Each piece comes with a measured promise: what it computes, how precisely, and at what side-effect cost.

GRAFT is organized like a programming language. **Opcodes** are the machine instructions, each a few neurons or one head switch: A gated switch (`step`), a gated linear term, a single curve segment (`kink`), and switches that redirect an attention head's keys, queries or values. **Instructions** compose opcodes into useful operations with measured contracts. **Programs** compose instructions into a capability. PhenoAge is the first program.

### The instructions the PhenoAge program uses

| Instruction    | What it guarantees                                                   | Measured                                                |
| -------------- | -------------------------------------------------------------------- | ------------------------------------------------------- |
| ANCHOR + FLAG  | the graft is ON for this question and OFF for any other prompt       | 0.998 mean attention to the anchor; alone, max KL 0.019 |
| PINS           | every digit, marker and answer slot is tagged with a code            | 0 wrong codes in 327,000 held-out tokens                |
| SHIFT          | a marker's digits are copied onto the token that ends its value      | 99.99% of attention on the right digit                  |
| BITS           | exact binary digits, written so they don't disturb the token's scale | ≤ 1 error in 798 on rare digits after refit             |
| AFFINE         | each marker's contribution in years, with unit conversion folded in  | error sd 0.04–0.28 years per marker                     |
| LOG_PWL        | ln(x) as 12 kinks                                                    | error sd 0.22 years                                     |
| SUM_POOL       | one head adds all markers at the answer position                     | marker weights within 0.8% of equal                     |
| GATED_Z + EMIT | the sum is written out as digit tokens                               | written digit = rounded target                          |

**Reused vs new.** Six pieces came from the previous experiment: The gated `step` pair, gated-linear terms, the positional-head design, quiet directions, constant reads and removal scans. Everything else was discovered during this run.

## 3. The first GRAFT program: PhenoAge

**Why PhenoAge.** It's a published formula that predicts mortality-adjusted "phenotypic age" from nine blood markers plus age. After its Gompertz transform cancels, it is a weighted sum of albumin, creatinine, glucose, **ln(CRP)**, lymphocyte %, MCV, RDW, ALP, WBC and age. It has an exact answer, so any remaining error is engineering error, measurable and fixable. The prompts are real NHANES profiles in free text, with **mixed units**. The original model doesn't know how to compute it.

**The program** (`phenoage_program.py`, 228 lines) is a sequence of GRAFT calls:

![The compiled program](/figures/o2_compiled_program.png)
_Figure 2. The PhenoAge program: seven stages, each a composition of GRAFT instructions._

### Watching it run on one person

![The circuit on one person](/figures/o3_circuit_on_one_person.png)
_Figure 3. The graft running on held-out person #68 (age 52, US units). Columns are real prompt tokens; rows are edited layers._

Reading the figure from the bottom:

1. **Switch on (layers 3–4).** The anchor recognises the question wording, and the flag makes every later token "know" this is a PhenoAge prompt.
2. **Label every token (layers 6–7).** Digits, decimal points, marker names and answer slots each get a code.
3. **Move the digits (layer 9).** Five heads copy 4, 3, 0 onto the semicolon that ends the albumin entry, where they become exact bits.
4. **Do the arithmetic (layers 10–11).** 4.30 g/dL is converted to 43 g/L inside the weights and turned into years. CRP goes through a 12-kink logarithm.
5. **Add it up (layer 12).** One head sums ten contributions at the answer slots, giving 48.3.
6. **Write the answer (layer 13).** The model writes '4', then '8'. The true PhenoAge is 48.3.

![The arithmetic and the contracts](/figures/o4_circuit_arithmetic_and_contracts.png)
_Figure 4. A: the arithmetic for person #68, from the population average through each marker's contribution to the answer. B: every instruction's measured contract._

![The footprint](/figures/d9_edit_footprint.png)
_Figure 5. What the graft physically changed: 166 MLP neurons and 8 attention heads (2 flag, 5 shift, 1 summing), all in layers 3–13. Layers 14–27 are untouched._

## 4. How it was built

Everything below was fixed **before** either agent started, and frozen with sha256 hashes:

- **Data:** 3,973 NHANES participants. 750 for practice (fit anything), 400 for dev (20 budgeted measurements) and 2,823 held out (scored once, at the very end).
- **Success bar:** held-out MAE ≤ 1.5 years.
- **Side-effect rule:** max KL ≤ 0.5 over 165 unrelated probes, and at most one changed answer among probes where the model had a clear preference.
- **Method:** no gradient descent. Only closed-form fits (ridge, linear SVMs, linear programs, eigenproblems).

**Two Claude Opus agents:**

- **The planner** had no access to the model. It designed the library spec and the program, simulated error budgets, predicted outcomes and reviewed results.
- **The surgeon** was the only one that touched weights. It implemented and tested each graft, and measured everything.

They talked only through files, which a supervisor (me, operating a Claude Code session) relayed mechanically.

![Run timeline](/figures/c5_run_timeline.png)
_Figure 6. 33 hours: relayed planner versions, surgeon reports, server side-effect checks and the three budgeted calls. Dashed lines mark human process amendments._

**Hours 0–22: building the instructions.** Every reader instruction (digit capture, transport, marker recognition, bit decoding) came back with zero errors on held-out practice data.

**Hour 22: the first end-to-end test.** I added one process rule (amendment A3): Stop adding components, generate answers, measure. The first measurement scored **dev MAE 1.32**, already better than gradient boosting. But the graft wasn't gated properly: it changed the model's answers on all 165 probes.

**Hours 22–31: making the graft safe.** This is where most of the safety rules came from.

![Side-effect journey](/figures/d6_side_effect_journey.png)
_Figure 7. Every free server side-effect check during the run. Many red marks are deliberate bisections. Stars mark the two accepted edits._

Each leak was traced to its root cause and fixed there:

- **The logarithm's reads fired on unrelated text.** Fixed with designed, guarded reads.
- **Two probes flipped because of where neurons sat, not what they computed.** Swapping 4 neurons in layer 9 and 30 in layer 10 cleared them.
- **The summing head leaked noise from ordinary tokens.** Two direction-based fixes failed on the real probes, which is how rule 3 was learned; cutting its gain to a third worked.
- **The attention sink at position 0** opened every gate (rule 6).

**First accepted edit: dev 1.58.**

**Hours 31–33: precision.** A blood value printed as "18.00" was read as 10.0, a rare digit the decoders had barely seen. The surgeon generated synthetic numbers with every digit redrawn and refit the decoders. That fixed the 30-year misses.

**Second accepted edit: dev 1.38.** The surgeon then tried one more lever, failed its pre-agreed cost test and stopped, with 17 of its 20 measurements unused.

**The two-agent loop worked best when it was tight.** After a rule requiring them to keep each other informed (amendment A6), the planner produced 17 versions in six hours.

- It diagnosed that two stubborn flips came from neuron placement.
- It designed the experiment that located the summing-head leak.
- It logged a prediction before every check.

Its own scorecard: Accuracy predictions held up, while both of its side-effect predictions failed. That is why the library treats side effects as something you **measure, not simulate**.

## 5. Results

![The error ladder](/figures/p5_error_ladder.png)
_Figure 8. Held-out error, and a zoom on the pre-registered bar._

| Held-out (n = 2,823), scored once                   | MAE (years)          | Edited minus comparator (95% CI) |
| --------------------------------------------------- | -------------------- | -------------------------------- |
| Original model                                      | 10.63                | **−9.10** (−9.39 to −8.80)       |
| Copy the stated age                                 | 7.88                 | −6.36 (−6.52 to −6.19)           |
| Gradient boosting (750 people, given parsed values) | 1.75                 | **−0.22** (−0.31 to −0.14)       |
| **Model + GRAFT PhenoAge program**                  | **1.52** (1.47–1.58) |                                  |
| _Pre-registered bar_                                | _1.5_                | _missed by 0.024_                |

![The journey](/figures/p8_mae_journey.png)
_Figure 9. From 10.5 to about 1.5 years: every budgeted call, then the single held-out score._

![Answers vs truth](/figures/p6_scatter_heldout.png)
_Figure 10. Each model's own answers against true PhenoAge, on held-out people._

**What the original model was doing.** On 52.9% of held-out people it simply repeated the stated age; its answers correlate more with age (0.85) than with PhenoAge (0.81). With the graft, the answer equals the stated age only 3.1% of the time. The model computes the formula instead of echoing an input.

![Worked examples](/figures/p9_worked_examples.png)
_Figure 11. Worked examples: each model's own answer._

![Within x years](/figures/p7_error_cdf.png)
_Figure 12. Share of held-out people within x years: 41% within 1 year, 72% within 2 and 99.4% within 5._

![Where the errors are](/figures/d7_where_errors_are.png)
_Figure 13. Left: in the oldest band (PhenoAge ≥ 75), gradient boosting's error jumps to 3.75 while the graft stays at 1.85. A compiled formula extrapolates beyond its training data; a learned model can't. Right: the only two 30+ year misses are both aged 83–84, about the size of the age term (likely an occasional age read-out failure; not verified)._

![Paired comparisons](/figures/c4_paired_comparisons.png)
_Figure 14. Paired differences on the same 2,823 people._

**Safety.** No answer the model had a clear preference on changed. Max KL was 0.358 (limit 0.5), and multiple-choice accuracy went from 61 to 63 out of 105. Five near-tie probes, where the model was close to a coin flip, did flip. The strict rule, which counts those, would fail.

## 6. What each graft is worth

![Ablations](/figures/d8_ablations.png)
_Figure 15. Six controlled comparisons from the run._

- **A. Accuracy ablations.**
  - **The rare-digit refit is worth 0.20 years on dev.** It removes the 30-year misses.
  - **Zeroing the logarithm stage gives 3.36.** That overstates CRP's value, because it also removes the stage's mean. The planner's fair estimate is +0.35 (not run).
- **B. The price of safety.** At the safe summing gain, the answer-slot reads are about twice as noisy: 0.12 vs 0.06 tens units, and 1.4 vs 1.0 years.
- **C. Leaks are about size.** The switches alone are clean. The value channel leaks in proportion to its gain. Re-choosing its direction, whether tuned on probes or chosen to be 37× less read downstream, did not help.
- **D. Only some refits are safe.** The units and tens decoders were adopted. The tenths decoders leaked and were left out (worth at most 0.02).
- **E. Same edit, different layer.** Layer 5 costs 0.553, layer 6 only 0.033.
- **F. Placement fixes.** Slot swaps removed every clear-answer change. The last lever was stopped by its cost test.

## 7. What the failures taught

The run produced eight rules. They are now part of the library, and most were paid for in hours.

1. **Placement is empirical.** The same 24-neuron edit costs KL 0.553 in layer 5 and 0.033 in layer 6. Bisect on the real side-effect check, and swap slots.
2. **Switch attention heads; never remove them.**
3. **A write is either tiny, dominant or norm-tracking.** A leak's damage depends on its **size**, not its direction: any write changes the token's norm, and every later layer rescales by it.
4. **Every read that gates a big write is either a designed read of a code that only exists on the graft's own prompts, or carries a guard.** Regression-fitted reads fire on unrelated text.
5. **Never tune directions on the probes you test with.** They overfit.
6. **Position 0, the attention sink, is a token class of its own.** Every gate reads as "on" there.
7. **When stacking grafts on an accepted edit, subtract the additive parts first,** or they are applied twice.
8. **One configuration per install.** (Also: never `raise SystemExit` in the sandbox kernel. It stopped the server three times.)

## 8. Reproducibility

- **Bit-exact rebuild.** Running the recipe (GRAFT library + `phenoage_program.py` + 44 fitted vector files) on a freshly loaded original model, in a separate process, reproduces all **1,957,862 changed weights** (sha256 `96c61417…` = the sandbox snapshot).
- **Side effects reproduce independently,** outside the sandbox: max KL 0.3583, no clear changes.
- **Official scoring** uses the same scorer as the sandbox and reproduces its predictions exactly.
- **A Colab notebook** [attached](/assets/phenoage_colab_bundle.zip) downloads the original model, rebuilds the graft from its recipe, checks the hash, and scores dev, held-out and the 165 probes.

## 9. Next steps

**So far, we showed:**

- **Weight edits can be packaged as a library.** GRAFT has opcodes, instructions with measured contracts, and safety rules learned from failures. A short program of library calls compiled a real clinical formula into a pretrained model's weights.
- **The compiled program is accurate:** Better than learning the same mapping from 750 labelled people, and better at the extremes, where learned models can't extrapolate.
- **It is gated:** The rest of the model barely notices it.
- **Autonomous agents can build all of this,** with humans setting goals and process.

**Pending:**

- **That the bar was met.** 1.524 is 0.024 above it.
- **That GRAFT generalises.** A library proves itself on its second program, not its first. That test is coming up (Part 3).
- **That grafts beat code.** PhenoAge is linear after ln(CRP); a parser plus the formula is exact. The point is that the computation now lives inside the model, verifiably, without tools.

**Next:**

- **Part 3: GRAFT as a specification.** What the smallest valid graft is, a common file format so other people can write grafts, how grafts combine, and what a side-effect certificate must contain. Plus the transfer test: A fresh agent compiling a second program, 10-year mortality risk from the same blood panel, using only GRAFT.
---

### Appendix: Every budgeted call (3 of 20 used)

| Call        | Configuration                 | Dev MAE | Side effects                        | Outcome              |
| ----------- | ----------------------------- | ------- | ----------------------------------- | -------------------- |
| M1 measure  | first end-to-end program      | 1.32    | max KL 40.2, all 165 probes changed | measured only        |
| E2 evaluate | leaks fixed, summing gain cut | 1.58    | max KL 0.358, 0 clear changes       | accepted             |
| E3 evaluate | + rare-digit decoders         | 1.38    | max KL 0.358, 0 clear changes       | **accepted (final)** |
