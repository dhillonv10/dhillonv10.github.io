---
title: "GRAFT-4: compiling programs into a language model's weights"
author: Vik Dhillon
pubDatetime: 2026-11-19T11:00:00-08:00
slug: graft-4-compiling-programs-into-model-weights
type: feature
draft: false
takeaways:
  - "**Compile a short program straight into a model's weights, with no training.** For presence, compare and fetch programs, a verified graft takes about 2 minutes. The hand-built packages in GRAFT-3 took a median of 3.5 hours."
  - "**Grafts leave everything else alone.** A tuned LoRA at the same accuracy changes 10 to 84 unrelated answers on 280 probes. The compiled grafts change none, with a typical maximum KL of 1e-7 to 1e-3."
  - "**One compiler, several models and programs at once.** The same 7 source programs compile for Qwen3-0.6B (7/7), Gemma-3-270M (4/7) and SmolLM2-360M (3/7). Four different programs linked into one model all score 0.97 to 1.00."
  - "**Reuse and self-repair only partly work.** Generating grafts without compiling missed its bar, and the model's self-written patches cut flagged failures but stay below the 0.90 accuracy bar."
description: "A short program, compiled straight into a language model's weights in minutes, with no training and no side effects on unrelated answers."
---

## Summary

GRAFT-3 showed that new abilities can be added to a pretrained model by installing small hand-built "packages" of units. Each package was
built by agents over hours, for one task, on one model. GRAFT-4 set out to make grafts **general** and **fast**: write a short program,
compile it straight into the model's weights with no training, and do that for many tasks, several model families and several programs at
once, in minutes, without changing anything else the model does.

| Goal                    | What we found                                                                                                                                                                                                                                                                                                                                                  |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| General across tasks    | One compiler, five operations (count, presence, queried count, compare, fetch). On Gemma-3-1B: 6/6 presence, 12/12 compare, 9/9 queried count, 4/4 fetch, counting accepted. 37/50 counting variants compiled unattended and passing dev + the probe check (27/50 before one compiler fix, amendment A6). Queried count and fetch counts are best-of-attempts. |
| General across models   | The same 7 source programs: Qwen3-0.6B 7/7, Gemma-3-270M 4/7, SmolLM2-360M 3/7 (Gemma-3-1B is the reference).                                                                                                                                                                                                                                                  |
| General across programs | Four different operations linked into one model, all at 0.97-1.00, side effects clean. Loaded naively they collide (0.34-0.83).                                                                                                                                                                                                                                |
| Fast                    | Program to verified weights in about 2 minutes for presence, compare and fetch (default path 6-6.5 minutes; GRAFT-3: a median of 3.5 hours per hand-built package).                                                                                                                                                                                            |
| Reusable                | Partly. Reuse works at the level of primitives, source programs and removable packages. The plan to generate grafts for new variants without compiling ("drag-and-drop") missed its bar.                                                                                                                                                                       |
| Side effects            | Every graft reported as passing met the rule (max KL ≤ 0.5, at most 1 confident answer change) on 280 probes and 500 held-out prompts (factory variants: probes, plus the held-out set for every fifth); typical max KL 1e-7 to 1e-3. A tuned LoRA at the same accuracy changes 10-84 probe answers and 24-33 held-out answers.                                |
| Self-repair             | The model's own failures trigger a fresh agent to write a patch; a verifier gate installs it or rejects it, in 5-6 minutes. Patches cut the flagged failures but do not reach the 0.90 accuracy bar (patched dev 0.77-0.94).                                                                                                                                   |

## 1. What is a graft?

A graft is a small set of **new** units added to a pretrained model: extra MLP neurons and attention heads that start at zero, so the grown
model is exactly the original model until something is installed. A program says what the new units should compute; the compiler decides
their weights.

Here is a program written by a fresh agent that saw only three unlabeled example prompts and the language reference (its helper definitions, the two word lists and a `find()` that locates the list line, are omitted):

```python
def program(P):
    L = P.slot(find=find)                     # where the list is in the user's message
    R = P.reference("?", ":")                 # a reference token after the list
    P.compare(L.items(where=lambda w: w.lower() in ANIMALS),
              L.items(where=lambda w: w.lower() in COLORS), R)   # "Are there more animals than colors?" -> Yes / No
```

Compiling this program installs about 216,000 new non-zero weights (216,028 for the family compile of this variant, `results/packages/compare.animals-colors.K1.json`):

- **Markers** (layers 20-22) tag the tokens the program selects. Three chained layers each re-check the tag.
- An **answer flag** (layer 22) fires only at the position where the model is about to answer.
- A **new attention head** (layer 23) reads the tagged tokens: it counts them, compares two counts or copies one.
- **Read-out units** (layer 24) turn the head's output into the answer tokens.

Every unit is a gated pair that writes exactly zero unless its gate opens. That is why a graft can be inspected unit by unit and removed
bit-exactly. The fits are closed-form (SVM, ridge, least squares on the model's own activations). There are no gradient steps.

**Pass rule** (pre-registered, unchanged all week):

- dev accuracy ≥ 0.90
- on 280 probe prompts and on 500 held-out safety prompts that the compiler never sees: max KL ≤ 0.5 and at most 1 confident answer change

The test split is scored only after a graft passes (four logged re-scores are listed in section 11).

## 2. Can a graft teach a model something new?

![Figure F1](/figures/g4_F1_unedited_vs_graft.webp)
_Figure F1. Unedited Gemma-3-1B against the same model with a compiled graft, one row per program family._

The question comes from _Sparks of Weight-Space Programming_: can an edit add an ability the model never had, rather than uncover one it
had? On these tasks the unedited model is near zero or at chance:

| Task                                      | Unedited                                     | With graft | Test                          |
| ----------------------------------------- | -------------------------------------------- | ---------- | ----------------------------- |
| Count the list items (P3)                 | 0.00 (0.45 with five examples in the prompt) | 0.95       | 0.955 (unseen lengths: 0.445) |
| Queried count, list first (C3)            | 0.13-0.21                                    | 0.93-0.95  | 0.925-0.95                    |
| Compare two counts (12 variants)          | 0.42-0.53                                    | 0.98-1.00  | 0.985-1.00                    |
| Presence, any X in the list? (6 variants) | 0.37-0.62                                    | 0.99-1.00  | 0.995-1.00                    |
| Last item of the list (F3)                | 0.61                                         | 0.90       | 0.865                         |

- On every task in the table the unedited model is at zero or chance level, and the graft passes. (The other fetch variants started at 0.87-0.98, so we do not count them as new abilities.)
- Each is verified on a held-out test split, with side effects measured on prompts that have nothing to do with the task.

## 3. Grafting vs fine-tuning

![Figure F2](/figures/g4_F2_lora_vs_graft_side_effects.webp)
_Figure F2. Unrelated answers changed by a strong LoRA vs a graft at the same accuracy._

A fair comparison needs a strong fine-tuning baseline, so we gave LoRA every advantage we could:

- 18 configurations per task, including KL anchoring and replay.
- One configuration per task, selected by the fewest answer changes on LoRA's own Alpaca validation set.

**Side effects at matched accuracy:**

| Task               | LoRA dev | LoRA: probe / held-out answers changed | Graft dev                                     | Graft: changed |
| ------------------ | -------- | -------------------------------------- | --------------------------------------------- | -------------- |
| Count (P3)         | 0.93     | 10 / 27                                | 0.95                                          | 0 / 0          |
| Count animals (T6) | 0.92     | 33 / 24                                | 0.90 (few-shot compile, 64 unlabeled prompts) | 0 / 0          |
| Presence (Q1)      | 0.99     | 84 / 33 (probe max KL 10.7)            | 1.00                                          | 0 / 0          |

- The best-tuned LoRA fails the side-effect rule on all three tasks.
- The grafts change no unrelated answers. Their largest KL is 0.002.

**Unseen list lengths:** on P3 the graft scores 0.445 and the LoRA 0.175.

**Why the difference:** fine-tuning moves existing weights that every prompt uses. A graft adds units that stay closed unless their
trigger appears.

## 4. One program, four models

![Figure F3](/figures/g4_F3_write_once_four_backends.webp)
_Figure F3. The same 7 source programs compiled for four models from three families._

"Write once, compile to every model":

- The source programs, data, splits, scorer and pass rule are identical across models.
- The compiler's model constants change: norms, activation, head layout, which layers hold markers.
- Each port also needed one or two model-specific fixes, listed below. For Qwen3, that was a stop unit and a larger emit size.

| Model        | Family        | Pass                                                                |
| ------------ | ------------- | ------------------------------------------------------------------- |
| Gemma-3-1B   | Gemma         | reference                                                           |
| Qwen3-0.6B   | Qwen          | 7/7 (P3 0.00 -> 0.99, test 0.995, unseen lengths 0.725)             |
| Gemma-3-270M | Gemma (small) | 4/7 (best of two declared settings; 3/7 at the best single setting) |
| SmolLM2-360M | Llama-type    | 3/7                                                                 |

- **Gemma-3-270M** is the size on which _Sparks_ saw no gain. There, counting goes from 0.00 to 0.91, and presence from 0.50 to 1.00
  (test 0.995-1.00). It took two fixes specific to that size:

  - a smaller output scale for the count head
  - read-out negatives recaptured with the head installed

  Three counting programs stay below the bar (best 0.62-0.88) because the count head isn't precise enough at that size.

- **SmolLM2** needed a Llama-specific fix: its chat template inserts a system prompt, so the position-0 attention sink our count head relied
  on is not usable. With that fixed, three programs pass:

  - number words 0.00 → 0.94
  - digits 0.00 → 0.99
  - presence Q2 0.41 → 1.00 (test 0.99; held-out max KL 0.44, close to the 0.5 limit)

  Two more are accurate but fail side effects: count fruits 0.98 and presence Q1 1.00. Two counting programs are below the bar (0.85-0.86).
  The side-effect failures have a clear cause (section 7): on SmolLM2 the marker units separate their targets from everything else with
  almost no margin. Adding chat negatives (attempt 4) and raw-text negatives (attempt 5) did not fix it, and attempt 5 made presence Q1
  fail the probes. The fix needs a trigger that reads the instruction, not more negatives.

## 5. The compiler

### 5a. From parts to a compiler

GRAFT-3 built a library of parts: token markers, a counting head, a fetch head, threshold bits, emit units, guards. Builder agents
assembled them by hand for each task. GRAFT-4 treats those parts as an **instruction set**. A small language (glang) exposes them, and a
compiler lowers each instruction to measured parts.

| GRAFT-3 part           | glang instruction                      | What changed in GRAFT-4                                                                               |
| ---------------------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Token markers          | `L.items(where=...)`, `P.slot(...)`    | Chained over three layers (L20-22); one layer in turbo mode; a reference token R shares the key image |
| Counting head          | `P.count(...)` (RASP `selector_width`) | New head reads n/(n+1) and 1/(n+1); "sink parking" keeps it silent elsewhere                          |
| Fetch head             | `P.fetch(L.item("first" / "last"))`    | One copy head plus a one-hot decoder per vocabulary word; soft read-out for "last"                    |
| AND-gated units        | `P.compare(...)`, queried count        | Compare gates on count A minus count B; queried count ANDs threshold bits with a query code           |
| Threshold bits + emit  | `answer="digit"` / `"yes_no"`          | Telescoping digit emits; Yes/No units                                                                 |
| Guards, BOS correction | (automatic)                            | Every unit carries a flag guard and a BOS correction                                                  |
| —                      | (new)                                  | Exact answer flag, query-code units, stop unit, linker namespaces                                     |

### 5b. What compiles today

Five operations and three answer types:

| Operation     | Example                                                             | Gemma-3-1B                                          |
| ------------- | ------------------------------------------------------------------- | --------------------------------------------------- |
| count         | "How many items are in the list?"                                   | P3 accepted; 37/50 factory variants (probe-checked) |
| presence      | "Is there an animal in the list?"                                   | 6/6                                                 |
| queried count | "How many times does 'cat' appear?" (question first, or list first) | 6/6 + 3/3 (list first took 23 attempts)             |
| compare       | "More animals than colors?"                                         | 12/12                                               |
| fetch         | "Which comes first / last?"                                         | 4/4                                                 |

**What doesn't compile yet:**

- Multi-token outputs (writing the k-th output token at the k-th step). Reverse, sort and Dyck completion were planned and dropped in
  amendment A2.
- Counting is precise to about 6 on Gemma-3-1B (the threshold bits), and less on the 270M.
- The list-first queried count (C3) took 23 attempts.

### 5c. Reusing grafts

**The original plan for reuse: "drag-and-drop".**

1. Compile many variants of one family.
2. Train a generator that writes the graft for a new, never-compiled variant in under a minute.

It missed its pre-registered bar:

- 0/22 strict.
- 10/22 ignoring the 60-second rule.
- Full compiles of the same 22 held-out variants pass 19/22 (post hoc), so the compiler covers them; the shortcut does not.

**Where reuse does work, at three levels:**

- **Primitives.** Each part is measured once, and every program uses the same parts.
- **Source.** One program compiles to four models (section 4). Fresh agents that saw only three unlabeled prompts wrote the intended program
  37 times out of 38, and 20 of those 38 compile label-free into passing grafts. A decompiler reads grafts back into programs. Round
  trips: 19/23 as pre-registered, 21/23 with a declared output-kind fix, 23/23 with a post hoc settings-matched recompile. Queried-count
  grafts were not decompiled.
- **Packages.** A compiled graft is saved as a content-hashed package (base hash + graft hash). Applying it and removing it restores
  every weight bit-exactly (3/3).

**What is not reusable yet:**

- A package compiled for one model does not install on another.
- Stacking packages needs the linker to recompile with the others' prompts as negatives.

Binary reuse across models is a GRAFT-5 item.

### 5d. Running many programs together

![Figure F6](/figures/g4_F6_mixed_stack.webp)
_Figure F6. Four instruction types linked into one model vs loaded side by side._

The linker gives each program its own address space: key images, flag dimensions, code dimensions and heads. Each program is compiled with
the other programs' prompts as negatives.

| Program  | Loaded naively | Linked |
| -------- | -------------- | ------ |
| Count    | 0.34           | 0.97   |
| Presence | 0.50           | 1.00   |
| Compare  | 0.50           | 0.99   |
| Fetch    | 0.83           | 1.00   |

- **Linked stack side effects:** held-out max KL 2.8e-4, 0 answers changed. This was attempt 2; attempt 1 failed on held-out max KL
  (2.05, 1 change) and passed after 300 chat negatives were added.
- **Same-family stack** (four counting programs): 0.97 / 1.00 / 1.00 / 0.98 linked, vs 0.50 / 0.88 / 0.99 / 0.10 naive.

## 6. Speed

![Figure F13](/figures/g4_F13_time_per_ability.webp)
_Figure F13. Time to add one verified ability. GRAFT-3 builder agents took a median of 3.5 h (range 3.1-25 h, 7 passed packages, package opened to accepted; shared pre-op time excluded, outages included). GRAFT-4 compile + full check takes a median of 6.4 min, and turbo + fast check 2.2 min._

![Figure F4](/figures/g4_F4_speed.webp)
_Figure F4. Program to verified weights for each program, default vs turbo + fast check._

**Two costs dominate:** fitting the markers, and checking side effects on 780 prompts.

![Figure F8](/figures/g4_F8_compile_stages.webp)
_Figure F8. Where compile time goes. The default compile spends about half its time on three layers of marker fits (87-106 s)._

Turbo:

- uses one marker layer at three times the write size
- replaces the SVM with a closed-form class-balanced ridge plus one hard-negative round
- shares one activation capture

Compile drops from 169-200 s to 83-100 s.

![Figure F9](/figures/g4_F9_fast_verify.webp)
_Figure F9. Side-effect check, full vs fast._

- The full check runs all 780 prompts through the model (194-206 s).
- The fast check caches the base model's activations once. It screens every graft unit's gate against the cache, and runs the real model
  only on prompts where a unit could open, plus a 40-prompt sample. That takes 35-60 s.
- It reached the same pass/fail decision as the full check 4/4 times. All four were passing grafts, so it has not yet been tested on a
  failing one. Every reported result was still checked in full.

![Figure F10](/figures/g4_F10_speed_vs_accuracy.webp)
_Figure F10. Speed vs accuracy. Turbo keeps presence, compare and fetch at 1.00, but counting drops from 0.98 to 0.84: counting needs the chained markers. The fast path is for families that tolerate one marker layer._

![Figure F11](/figures/g4_F11_plain_english_compile.webp)
_Figure F11. Examples → program → weights. Programs written by agents from three unlabeled prompts compile from 64 unlabeled prompts in 1-3 minutes for most families. Queried count takes 43-58 minutes and does not pass in this label-free mode._

![Figure F12](/figures/g4_F12_selfpatch_timeline.webp)
_Figure F12. Self-patching timeline per fix. Each fix takes 5-6 minutes: the agent about 40 s, the compile 75-120 s, the gate about 200 s. With the fast check as the gate, this would be about 2.5 minutes per fix (not yet run inside the loop)._

**End to end:** program → verified weights in 119-137 s for presence, compare and fetch (turbo compile + fast check), down from 355-389 s.
The agent call (examples → program) adds about 20-40 s.

## 7. Side effects

A graft is only useful if it changes nothing else, so side effects are the main safety measure. We measured them on every graft
reported here; factory variants were checked on the probes, plus the held-out set for every fifth.

**How we measure:**

- Next-token KL and _confident_ answer changes on 280 probe prompts, plus 500 held-out prompts.
- The held-out set mixes math word problems, multiple-choice questions, open chat and raw text, plus 100 digit near-misses.
- The compiler never sees the held-out set. We used it for pass/fail and for the indices of changed answers, and the pre-registered unit
  audit counted where units fire on it.
- In one early case (presence Q3) we read which held-out prompts flipped. Every later diagnosis used separate data: SVAMP, Alpaca,
  near-miss sets.

**Pass:** max KL ≤ 0.5 and at most one confident change.

![Figure F7](/figures/g4_F7_controls.webp)
_Figure F7. Real graft vs random graft of the same size and norm, the control borrowed from DAWE._

|                                    | Dev       | Probe answers changed | Held-out answers changed |
| ---------------------------------- | --------- | --------------------- | ------------------------ |
| Real graft (P3, presence, compare) | 0.95-1.00 | 0                     | 0                        |
| Random graft, same size and norm   | 0.00-0.50 | 106-121               | 208-233                  |
| Constant answer                    | 0.25-0.50 |                       |                          |

**Side-effect failures were the main engineering problem.** Each one was diagnosed on separate data (except Q3, above):

| Failure                                      | Cause                                                                                                                                                                    | Fix                                                                                                                                                                                                                                                                                                           |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Presence Q3 failed held-out safety (KL 12.1) | A short generic question taught the flag "a question about animals"                                                                                                      | A bank of Alpaca chat prompts as negatives (a source disjoint from the held-out set)                                                                                                                                                                                                                          |
| C3 queried count leaked (attempt 18)         | A guard capped at 300 units let off-target prompts through                                                                                                               | Full guard                                                                                                                                                                                                                                                                                                    |
| C3 and the mixed stack: held-out max KL 2-14 | Chat-style prompts unlike any negative                                                                                                                                   | Plus 300-600 Alpaca chat negatives fixed C3 animals, C3 fruits and the mixed stack; colors.C3 also needed near-miss and prose negatives (passed at attempt 23)                                                                                                                                                |
| Gemma-3-270M counting: KL up to 8            | Count-head output scale too large for the small model                                                                                                                    | Scale 300 → 15-30, read-out negatives recaptured with the head installed                                                                                                                                                                                                                                      |
| SmolLM2: held-out KL 0.9-2.9                 | Raw-text lists containing the program's words (a recipe that lists "apple") open the first marker layer; SmolLM2 has no BOS token, and every negative was chat-formatted | Not fixed. Raw-text negatives (attempt 5) did not help: every marker layer separates its targets from the negatives with almost no margin (highest off-target score about +1 vs on-target 44-56), so unseen text near such a list still crosses. It needs a trigger conditioned on the instruction (GRAFT-5). |
| Self-patches broke each other                | Two near-identical templates (digits vs number words)                                                                                                                    | Cross-patch negatives + a suite gate                                                                                                                                                                                                                                                                          |

## 8. How to build reliable grafts

What we would tell someone building their own:

1. **Fix the pass rule before compiling.** Write it down, including the side-effect sets, and never change it mid-run. Score the test
   split once.
2. **Negatives are the program.** Most failures were units opening on the wrong prompts. Use four kinds of negatives:

   - other programs' prompts
   - generic chat
   - near-miss prompts
   - raw text (the format your users actually send)

   A held-out set from different sources tells you when the banks are not enough.

3. **Calibrate the checker with controls.** A random edit of the same size and norm should fail badly, and it does (106-121 flips). A
   constant answer sets the floor.
4. **Check what the fit uses.** A label-shuffle test: P3 and presence compile to the same accuracy with shuffled build answers. For P3
   that is 0.98 vs 0.98, with 0.98 answer agreement; for presence 1.00 vs 1.00. So the program, not the labels, carries the computation.
5. **Round-trip it.** Decompile the graft back to a program and recompile: 19/23 as pre-registered, 23/23 after two fixes, one of them
   post hoc.
6. **Audit the units with someone else.** An independent judge read the unit audit and found real problems, which we report as written:
   - marker units sharing a surface trigger (possessive apostrophes, prices)
   - broad firing on digits
   - several unused units
7. **Ship packages, not edits.** A content hash for the base and for the graft, plus a bit-exact removal test.
8. **Gate the whole suite.** When grafts stack, re-run every installed graft's tests at each install.

## 9. Self-patching: the model fixes its own mistakes

![Figure F5](/figures/g4_F5_selfpatch_rounds.webp)
_Figure F5. User-flagged wrong answers per round. (Time per fix: Figure F12, section 6.)_

**The loop:**

1. The model serves a stream of prompts.
2. Simulated users flag its wrong answers.
3. A monitor clusters the flags; 5 or more flags make a report.
4. A **fresh agent** reads only the report and writes a glang patch plus regression tests.
5. The compiler builds the patch label-free.
6. A gate checks the regression tests, the probes and the held-out safety set.
7. If the gate passes, the patch is installed as a package.

**v0:** all three agent-written patches passed the gate. In the next round, flags fell for number words (22 → 6) and body parts (19 → 15),
but **rose** for digits (21 → 24). The two patches had nearly identical templates and interfered.

**v1** adds two things:

- each patch is compiled with the other reports' prompts as negatives
- a suite gate re-runs every installed patch's tests at each install

Body parts and number words installed (suite 10/10). The digits patch was **rejected** by the gate (own regression 2/5) and removed
bit-exactly. In round 3:

| Pattern           | Flags                                   |
| ----------------- | --------------------------------------- |
| Body parts        | under the reporting threshold (from 19) |
| Number words      | 5 (from 22)                             |
| Digits, unpatched | 23                                      |

Nothing that was installed broke.

**The patches fix part of a failure, not all of it.**

- Patched dev accuracy was 0.77-0.83 in v1 (0.78-0.94 in v0), below the 0.90 bar used everywhere else.
- The gate checks regression tests and side effects, not dev accuracy.
- Flag counts are noisy: a never-patched pattern (count animals) went from 16 to 7 flags between rounds.

**Limits:** the user flags are simulated from the data's answers, and the digits failure is still open.

## 10. What we learned from others' work

**DSPy weight-space programming (Breunig, cmpnd.ai).** This post made the case that an optimizer can treat weights as a programmable
surface, and it showed a full writer loop with real costs attached. Two things stayed with us.

- **Accounting.** We report compile seconds for every graft and the agent time for the plain-English arm.
- **Candour about the method.** The strongest edits there were, underneath, ridge regressions inside the writer's kernel. We took that
  as a design principle rather than a caveat: GRAFT is closed-form fitting from the start, we say so up front, and a label-shuffle test
  checks what the fits actually use.

**Sparks of Weight-Space Programming (Takehi, Teoh, Zhang, Khattab).** The sharpest question we inherited is theirs: an edit might remove an
obstacle that hid an ability, but can it add one the model never had? We built every experiment around that question.

- Every table reports the unedited model, which is at zero or chance level on our tasks.
- We followed their lead in testing small models, including the Gemma-3-270M on which they saw no gain. There, four of seven compiled
  programs pass once two size-specific issues were fixed.

Their skepticism is the reason our results come with held-out tests and side-effect checks rather than demos.

**Weight-Space Reading (Kocabay, suayptalha/wsr).** This harness taught us to think about where a write actually lands. Post-sublayer
norms rescale whatever you add, so amplitudes have to be designed in effective-gain coordinates, which is exactly the failure we kept
measuring before adopting it. It also gave us habits we kept:

- calibrate the checker with null and near-null edits
- ship a manifest of what each edit touches
- describe model families by roles (MLP output, attention output, pre-norm input) so a compiler can be ported

Those role-based constants are how one compiler now targets four models in three families (section 4).

**Interpretable weight-space programming (Mehta et al.).** This paper showed how far transparency can go when small transformers are built
from scratch. It set the bar for evidence: rebuild from a text bottleneck, and audit the units with an independent judge. We asked what
those tests look like when the program is written into a large pretrained model instead.

- **The program is the text bottleneck,** at 4-25 lines. Fresh agents wrote the intended program 37 times out of 38 from three unlabeled
  example prompts alone, and 20 of the 38 compile label-free into passing grafts (presence 6/6, compare 3/3).
- **A decompiler reads grafts back into programs.**
- **An independent judge audited the units** and found real issues, which we report as written.

Their open problem, programming deep representations without backpropagation, is the one we are trying to chip at by reusing the
pretrained model's own representations.

**DAWE ("data → weight edit", bandr.ai).** DAWE showed a practical, agent-guided edit repairing a fine-tuned model after a format change.
It gave us two engineering ideas that we adopted directly:

- **Controls:** a random edit of the same size and norm, and a constant baseline. Our random graft scores 0.00-0.50 and changes 106-121
  probe answers; the real graft changes none.
- **Patches:** content-hashed packages that can be applied and removed. Ours restore the base weights bit-exactly.

Their edits change existing rows; GRAFT adds new units that are an exact no-op until installed. That is a complement to their repair
setting, not a replacement for it.

## 11. Limits

- **Small instruction set:** five operations, single-token answers, counts precise to about 6.
- **Turbo and counting:** turbo hurts counting (0.84), so the 2-minute path is for presence, compare and fetch.
- **Drag-and-drop missed:** generating grafts without compiling missed its bar (0/22 strict).
- **Small models:** Gemma-3-270M passes 4/7 and SmolLM2-360M 3/7. On SmolLM2 two accurate programs fail side effects because the
  markers have no margin.
- **Hard case:** queried count with the list first took 23 attempts; in label-free mode it does not pass.
- **Self-patching:** simulated user flags; one failure cluster unpatched.
- **Test re-scoring (four logged cases):**

  - P3: amendment A1; a queue bug scored the first test on a model state that never passed dev.
  - Fetch F1 and F4: scored again after a read-out change.
  - Presence Q2 on Gemma-3-270M: scored twice by mistake.

  Each is in LOG.md; the ledger lists the scores.

- **Not ported:** queried count C1 and compare K1 were named in the port pre-registration (if their Gemma compiles passed) and were not
  ported.
- **Self-patches:** they reduce flagged failures but stay below the 0.90 accuracy bar.
- **Scale:** everything ran on 4 CPU cores, with 0.27-1B models.

## 12. What's next

**GRAFT-5** (starts Monday 11-23):

- **A standard library of linked programs.** A capacity curve from 4 to 32 programs, an automatic namespace allocator and a shared
  dispatcher.
- **Self-patching v1+**, with the fast check as the gate.
- **A weight-space critic.** It predicts from the weight change alone whether an edit will harm the model, so many candidate surgeries can
  run in parallel and only the best gets verified.
- **The turbo path made mature.**

**GRAFT-5.5:** programs that call other programs.

- Inside one forward pass, through typed residual "registers" (compare(count(A), count(B)) from separately compiled modules).
- Then through the output stream: one program writes tokens that the next one reads.

## Appendix

- Methods: grown models, unit types, compiler stages, verifier.
- Amendments and deviations (AMENDMENTS.md A1-A12).
- The full ledger (`results/LEDGER.csv`).
