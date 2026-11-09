---
title: "Part 3: GRAFT, a Common Language for Programming Model Weights"
author: Vik Dhillon
pubDatetime: 2026-11-08T10:00:00-08:00
slug: graft-common-language-for-programming-model-weights
type: feature
draft: false
description: "What it would take for other people to write grafts too: a definition of the smallest valid graft, a file format, rules for combining grafts and a certificate format. It also reports that the library transfers: a fresh agent compiled a second program, 10-year mortality risk, with held-out error of 1.02 percentage points."
---

_In Part 2, two Claude Opus agents built a set of reusable weight-space surgeries and used them to compile the PhenoAge formula into `Qwen3-0.6B-Longevity`: held-out error 1.52 years, down from 10.63, with the rest of the model essentially untouched. I called that set of surgeries GRAFT. This post asks what it would take for other people to write grafts too. It proposes a definition of the smallest valid graft, a file format for writing one, rules for combining them, and a certificate format for proving they're safe. It also reports whether the library carries over to a second program. It does._

## TL;DR

- **GRAFT transfers.** A fresh agent compiled a second program, 10-year mortality risk, by reusing the library: eight PhenoAge instructions unchanged, three refit, and a new risk curve built from existing opcodes. It needed no new instructions and one scored call, and was done in under 2½ hours. Held-out error is **1.02 percentage points**, against 44.4 for the original model, 8.30 for a constant guess, 6.43 for ridge regression and 1.91 for gradient boosting trained on 750 people. It passes the same side-effect rule.
- **A graft is a weight edit that declares six things:** what model it targets, exactly which weights it touches, what switches it on, what it computes, a measured contract, and a side-effect certificate. Drop any one and it stops being safe to add to someone else's model.
- **The smallest valid graft is two MLP neurons:** one gated `step` pair, 6,144 weights in this model. The smallest graft that changes visible behaviour needs three instructions: switch on, compute, write a token.
- **A universal language is possible; universal weights are not.** The interface (the six fields, file format and certificate) can be model-agnostic. The opcodes are portable within one family of architectures. The actual numbers have to be fitted to each model. That is the same split as source code and binaries, so GRAFT has both: a `.graft` source file is _lowered_ against a specific model into a `.gdelta` (the weights) and a `.gcert` (the test report).
- **Four conformance levels** (reversible, contracted, certified, reproducible). The PhenoAge program meets all four, even though it missed its accuracy bar by 0.024 years. The levels record claims; they don't require success.
- **Provenance:** the agents built PhenoAge without this spec. The supervising Claude session drafted it afterwards at my request, formalising what the agents built and documented. Nobody has yet written a graft from it. That's the invitation at the end.

![Anatomy of a GRAFT](/figures/o6_graft_anatomy.png)
_Figure 1. A: the six fields of a minimal graft, with the values of a real one from the PhenoAge program. B: a portable `.graft` source is lowered against one model into a weight delta and a certificate. C: the four conformance levels._

---

## 1. From one program to a language

Part 2's result was one program. The agents left behind a working library (`isa/`, about a dozen Python modules) and an as-implemented instruction table. But a library only its authors can use is just a codebase. For weight-space programming to be a field rather than a stunt, three things have to be true:

1. **Someone else can write a graft** without reading our code.
2. **Two grafts written by different people can live in one model** without breaking each other.
3. **A reader can check a graft's claims** without trusting its author.

Each of those needs a shared definition. That's what this post proposes. I'll be explicit about which parts are measured and which are design.

## 2. What is the smallest valid graft?

The question sounds pedantic, but it forces the definition. A weight edit is a graft when it declares six fields:

| #   | Field            | What it is                                                                           | Without it                        |
| --- | ---------------- | ------------------------------------------------------------------------------------ | --------------------------------- |
| 1   | **target**       | the model and the sha256 of the exact weights it was fitted against                  | you don't know what it applies to |
| 2   | **sites**        | the exact weight slices it touches, each either replaced (`set`) or added to (`add`) | it can't be undone or audited     |
| 3   | **gate + scope** | the read that switches it on, and the inputs on which it's meant to be on            | it's fine-tuning: a global change |
| 4   | **payload**      | reads → opcode → writes                                                              | it does nothing                   |
| 5   | **contract**     | a measured claim, `{scope} graft {result ± tolerance}`, with the data split          | it's an unchecked claim           |
| 6   | **certificate**  | side-effect bound on a declared probe suite, delta hash, exact undo                  | its risk is unknown               |

**The smallest thing that can carry all six is one opcode:** a single `step` pair, which is two MLP neurons. In this model that's 6,144 weights (each neuron is a gate row, an up row and a down column of width 1,024).

This isn't hypothetical. The PhenoAge program's first stage, ANCHOR, is three of these pairs. Here is one of them written out as a stand-alone graft, with its real values:

```yaml
graft: 0.1
name: phenoage-anchor-pos40
target:
  model: insilicomedicine/Qwen3-0.6B-Longevity
  weights_sha256: f547df5c82226b524fc44748876685000f34208efe80aeef8f8eb7238b5a5cce
scope:
  kind: template
  question: "What is this participant's PhenoAge (Levine 2018 phenotypic age) in years? Answer with a number."
  positions: [40]
channels:
  - {
      name: eA,
      written_at: L3,
      read_until: L4,
      meaning: "this is the PhenoAge question line",
    }
instructions:
  - id: anchor40
    op: step
    at: { layer: 3, site: mlp, slots: [2761, 78] }
    gate: "kap * (LDA_read40 . x_hat + (b40 - 0.7) * c3)"
    writes: [eA]
    contract:
      claim: "fires at position 40 of every in-scope prompt; stays below threshold on near-miss texts"
      metric: max adversarial detector value
      bound: 0.6
      measured: 0.47
certificate:
  probe_suite: graft-probes-165
  measured_as_part_of: "ANCHOR (3 pairs): removal KL 4e-4"
```

**Components and programs.** That anchor is a _component_: its contract is about the model's internal state ("this direction lights up here and nowhere else"). A _program_'s contract is about what the model says. The smallest program needs three instructions:

1. **switch on** (ANCHOR + FLAG), so it's only on for its question;
2. **compute** something;
3. **EMIT** it as a token.

The simplest is "when asked this exact question, answer with this constant". I call it the **hello graft**. The spec includes a template for it. It hasn't been built yet; it's the obvious first exercise for someone new.

## 3. Can there be a universal language?

Partly. It helps to separate three layers:

| Layer         | What it fixes                                                             | How portable                                                                                                                                                                            |
| ------------- | ------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Interface** | the six fields, the file format, the certificate, the conformance levels  | **Universal.** Nothing in them depends on the model.                                                                                                                                    |
| **Opcodes**   | the elementary operations: a gated switch, a curve segment, a head switch | **Portable within an architecture family.** v0.1 defines them for pre-norm decoder transformers with RMSNorm, gated MLPs and rotary attention, i.e. the Llama, Qwen and Mistral family. |
| **Values**    | every read vector, write vector, neuron slot and threshold                | **Model-specific.** The run's first rule is that placement is empirical: the same edit cost 17× more side effects one layer earlier.                                                    |

So the honest answer is the one compilers settled on decades ago. **The language is portable; the binary isn't.** A `.graft` file says _what_ to compute, _where roughly_ (which layer band, which kind of site) and _what it must guarantee_. A **lowering** pass, run against one specific model, does five things:

1. collects that model's activations on in-scope prompts and on unrelated text;
2. fits every vector in closed form;
3. picks quiet neuron slots;
4. installs everything through a registry that records the original values;
5. measures each contract.

The output is a `.gdelta` (the sparse weight change plus its hash) and a `.gcert` (what was measured).

Two caveats. GRAFT has only ever been lowered on one model, so cross-model portability is a hypothesis. And mixture-of-experts models, state-space models and encoder-decoders are outside v0.1.

## 4. The opcodes, defined

Everything is stated in terms of what every module in this architecture actually reads: the normalised residual `x̂ = γ ⊙ x / rms(x)`.

- A **read** is a vector dotted with `x̂`, which is physically a weight row.
- A **write** is a vector added to the residual, which is physically a weight column.

| Opcode                   | What it does                                                                                                                  | Weights                      |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| `step`                   | a gated switch: `≈ down × (up·x̂)` when the gate read is on, exactly ~0 when off                                               | 2 neurons, replaced          |
| `gated_linear`           | `step` whose output is a linear read: "if this is marker _k_, write _w_ × value"                                              | 2 neurons, replaced          |
| `kink`                   | one ReLU-like segment; chains of kinks draw curves like ln and exp                                                            | 1 neuron, replaced           |
| `keyswitch` / `qswitch`  | add a rank-1 change to a head's keys or queries that is only active on a private signal; elsewhere the head behaves naturally | 128 rows, added              |
| `vtake` / `vadd`         | take over (or add to) one value channel of an attention head                                                                  | 1 value row + output columns |
| `head_take` / `group_kv` | replace a whole head (defined, discouraged)                                                                                   | 128 rows                     |

The **design routines** that produce the vectors are part of the library, not the format:

- ridge regression for constant reads;
- minimum-variance private reads;
- eigenproblems for quiet directions;
- linear programs over rotary-embedding planes for exact positional attention;
- linear SVMs for detectors.

The spec only requires that lowering be deterministic and recorded. Anyone may bring a better fitting method.

## 5. Writing a program

A `.graft` file is YAML. Besides the six fields, it has two things that make composition work:

- **Channels** are a symbol table. Each named residual direction (a flag, a digit code, a running sum) has one writer, a layer range in which it may be read, and a declared **write regime**:

  - _perturbative_: tiny;
  - _dominant_: so large that the token's later state is fixed;
  - _norm-tracking_: scaled with the token.

  The regime rule is the hardest-won lesson of Part 2. A leak's damage is set by its size, not its direction, because every write changes the token's norm and every later layer rescales by it.

- **Contracts on every instruction,** each naming the data split it was measured on.

Here is an excerpt from the PhenoAge program rewritten in this format:

```yaml
channels:
  - {
      name: FB,
      written_at: L4,
      read_until: L13,
      regime: norm-tracking,
      meaning: "flag: ~1 after the question, exactly 0 elsewhere",
    }
  - {
      name: PIN,
      written_at: L6,
      read_until: L13,
      regime: dominant,
      meaning: "code per digit, space, dot",
    }
  - {
      name: Y,
      written_at: L10,
      read_until: L12,
      meaning: "each marker's PhenoAge term in years",
    }

instructions:
  - id: pins
    op: PINS
    at: { layer: 6, site: mlp, pairs: 13 }
    gate: "svm(token kind) AND FB"
    writes: [PIN]
    contract:
      {
        claim: "each digit token carries its code; nothing else does",
        split: held-out practice,
        metric: wrong pins,
        bound: 0,
        measured: "0 of 327k tokens",
      }
  - id: log_pwl
    op: kink
    at: { layer: 11, site: mlp, neurons: 12 }
    writes: [Y]
    contract:
      {
        claim: "Y_crp = coefficient * ln(CRP)",
        metric: error sd (years),
        measured: "0.22-0.26",
      }

program_contract:
  claim: "first number in the answer = PhenoAge"
  split: held-out (n = 2,823), scored once
  metric: MAE (years)
  bound: 1.5
  measured: 1.524 # missed the bar by 0.024
```

The full file declares all 14 instructions with their layers, slot counts and measured contracts. The PhenoAge program itself was written as 228 lines of Python, not in this format. The `.graft` version is a faithful transcription, made afterwards.

## 6. Combining grafts

The Part 2 run already ran into every composition problem in miniature, because its 14 instructions were written at different times and re-installed hundreds of times. The library's registry enforced some rules; others were learned by breaking them. The spec makes them requirements for any tool that installs more than one graft:

1. **Slot ownership.** A replaced slice has exactly one owner, and a second claim is an error. Additive slices stack, with one delta per owner, so each can be removed.
2. **Channel table.** One writer per channel. Readers sit after the writer and within the declared range.
3. **Regimes hold at every write.**
4. **Subtract before re-installing.** When stacking onto weights that already contain an accepted graft, remove that graft's additive parts first, or they're applied twice. (This bug happened.)
5. **Every combination is re-certified.** Side effects don't add up. In the run, removing 10 neurons from one layer cost a max KL of 0.11, and removing 24 cost 0.55.

**Reuse is declared.** When one program builds on another, each instruction is marked `REUSED` (same weights), `REFIT` (same instruction and slots, fitted again) or `NEW`. The mortality program in §9 is the first real case:

| Layer   | Instruction          | Status in the mortality program                                         |
| ------- | -------------------- | ----------------------------------------------------------------------- |
| L3      | ANCHOR               | REFIT: same 3 neuron pairs, detectors refit on the new question wording |
| L4      | FLAG, FB             | REUSED (FLAG's key offset re-centred on the new anchors)                |
| L6–L7   | PINS                 | REUSED unchanged                                                        |
| L9      | SHIFT, BITS          | REUSED unchanged                                                        |
| L10–L11 | AFFINE, LOG_PWL      | REUSED unchanged                                                        |
| L12     | SUM_POOL             | REUSED unchanged                                                        |
| L12     | GATED_Z              | REFIT reads                                                             |
| L13     | exp curve from kinks | NEW composition of existing opcodes                                     |
| L14     | EMIT                 | REUSED instruction, moved one layer                                     |

_(The agent's final program, accepted edit E1.)_

## 7. The certificate

A `.gcert` is a JSON file that lets a reader check a graft's claims without trusting its author. I generated the one for PhenoAge directly from the run's records. Highlights:

| Field            | PhenoAge E3                                                                                                                                                                            |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| target           | `Qwen3-0.6B-Longevity`, weights sha256 `f547df5c…`                                                                                                                                     |
| delta            | 1,957,862 changed weights (0.26%), 36 tensors, sha256 `96c61417…` (recomputed from the delta file; matches the run's record)                                                           |
| resources        | 166 replaced MLP neurons in layers 3–13; additive switches on 6 query heads and 5 key groups; 2 value channels                                                                         |
| undo             | exact: originals written back at the recorded indices                                                                                                                                  |
| side effects     | 165-probe suite: max KL 0.358 (limit 0.5), 0 confident answer changes, 5 near-tie changes; multiple-choice 61 → 63 / 105; **passes** the pre-registered rule, **fails** the strict one |
| program contract | held-out MAE 1.524 (95% CI 1.47–1.58) vs bar 1.5: **missed**; comparators: original model 10.63, gradient boosting 1.75                                                                |
| reproduction     | recipe rebuilds the delta in a separate process: sha256 match                                                                                                                          |

**Two design choices matter.**

- **The certificate records failures as readily as successes.** A format that only has room for passing results invites cherry-picking.
- **The side-effect rule reports two numbers.** One is the pre-registered rule: max KL ≤ 0.5, and at most one changed answer among probes where the model had a clear preference. The other is the strict count, which includes coin-flip answers. Both are reported, always.

## 8. Conformance levels

| Level  | Name         | Requires                                                             |
| ------ | ------------ | -------------------------------------------------------------------- |
| **G0** | Reversible   | sites declared, delta hashed, exact undo                             |
| **G1** | Contracted   | G0 + a measured contract on every instruction and on the program     |
| **G2** | Certified    | G1 + a side-effect certificate on a declared probe suite             |
| **G3** | Reproducible | G2 + the recipe rebuilds the delta bit for bit from the base weights |

PhenoAge is G3. That is a statement about how checkable it is, not how good it is. It missed its bar, and the certificate says so.

**Eight authoring rules** come with the levels. They are Part 2's safety rules restated as requirements:

- verify placement on the real side-effect suite;
- switch heads, never remove them;
- every write is tiny, dominant or norm-tracking;
- guard every read that gates a large write;
- never tune on the certificate's probes;
- zero every read at position 0;
- subtract before re-installing;
- one configuration per install.

Each one was paid for with a failure in the run, and the spec links each to its evidence.

## 9. Does GRAFT transfer? The second program

A library proves itself on its second program. The test I set up is deliberately basic: **can a fresh agent take GRAFT, pick surgeries from it, apply them to a new task, and beat the baseline?**

- **Task:** 10-year mortality risk in percent, from the same blood panel, using Levine's mortality model: `M = 100·(1 − exp(−1.51714·exp(xb)/0.007692696))`. The question wording is new, and the output is a steep nonlinear curve that PhenoAge never needed.
- **Agent:** a fresh Claude Opus surgeon with the GRAFT library, the accepted PhenoAge edit as a starting point, and no human design input.
- **Pre-registered bar:**
  - primary: beat the original model, a constant prediction (MAE 8.30) and ridge regression (6.43) on held-out people, and pass the same side-effect rule;
  - stretch: gradient boosting (1.91).

The agent was given the PhenoAge workspace: the library, the PhenoAge program and its fitted vectors, and the run's logs. It was not given this spec, which didn't exist yet. It ran alone, with no planner, and with 10 scored calls.

**Result: it transfers, and it clears every bar.**

![GRAFT transfer](/figures/t1_graft_transfer.png)
_Figure 2. A: held-out error on 2,823 people, scored once. B: error by true risk level. C: what the agent reused, refit or built new, layer by layer. D: the second program against the first._

| Held-out (n = 2,823), scored once                   | MAE (percentage points) | Edited minus comparator (95% CI) |
| --------------------------------------------------- | ----------------------- | -------------------------------- |
| Original model                                      | 44.44                   | −43.42 (−44.39 to −42.52)        |
| Constant guess                                      | 8.30                    | −7.28 (−7.78 to −6.78)           |
| Ridge regression (750 people)                       | 6.43                    | −5.41 (−5.63 to −5.20)           |
| Gradient boosting (750 people, given parsed values) | 1.91                    | **−0.89** (−1.04 to −0.75)       |
| **Model + GRAFT mortality program**                 | **1.02** (0.96–1.08)    |                                  |

![Answers vs truth](/figures/t3_answers_vs_truth.png)
_Figure 3. Each held-out person's true risk against the answer the edited model wrote (left) and gradient boosting's prediction (right)._

The original model doesn't know the formula. On held-out its error is 44.4 points (the edit is better by 43.4, 95% CI 42.5–44.4), because it answers "70" or "72" for almost half of all people, whatever their profile.

- **Dev and held-out agree.** Dev MAE was 1.06 on 200 people, and the agent had predicted 0.8–1.2 before the call. Held-out came in at 1.02.
- **Every answer is well-formed.** All 2,823 answers are exactly two digits ("08", "23") followed by a stop; none is unparsable or runs on. The median error is 0.4 points, and 77% of people are within 1 point.
- **It beats gradient boosting at every risk level, by most where it matters.** For people whose true risk is 50% or more, gradient boosting is off by 15.8 points and the graft by 4.8. A compiled formula extrapolates; a model trained on 750 people, most of them at low risk, can't. This is the same pattern as PhenoAge's oldest band.
- **Its errors still grow with risk.** At 20–50% risk the error is 3.2 points, and 15 people (0.5%) are off by more than 10. The cause is the steep curve: small errors in the PhenoAge read-out it reuses get amplified. You can see one failure mode in Figure 3 as flat runs at 29, 39, 49 and 89. When the tens digit comes out one too low, the units digit can't make up the difference and saturates at 9. Half of all answers of 19 or more end in 9 (216 of 434), and those answers carry 28% of the total error. A wider units range, or emitting the answer as one curve read rather than tens-then-units, is the obvious fix. Whole-number answers also add about 0.26 points of rounding error; the agent's suggested decimal digit is worth an estimated 0.1–0.15.
- **Side effects pass the pre-registered rule.** Max KL is 0.378 (limit 0.5). One answer the model had a clear preference on changed (probe 48, the limit is 1), and five near-ties flipped. Multiple-choice accuracy went from 61 to 65 out of 105. As with PhenoAge, the strict count fails. An independent re-check outside the sandbox, applying the saved weight change to a fresh copy of the model, reproduces these numbers exactly.
- **Reproducible.** Rebuilding the edit from the agent's recipe on a fresh copy of the original model reproduces all 2,043,878 changed weights bit for bit (sha256 `c1efad32…`).

**What it cost:**

- The agent's first end-to-end version worked within about an hour of its first sandbox call. It found its leaks with the same bisection trick PhenoAge used, and had an accepted edit about 2 h 20 min after launch (not counting a 41-minute pause of its sandbox).
- It used 1 of its 10 scored calls, then stopped on its own.
- PhenoAge, by comparison, took two agents about 30 hours and three scored calls.

![Containment](/figures/t2_containment.png)
_Figure 4. A: every side-effect check the mortality agent ran, from its first full program (max KL 18, 33 answers changed) to the accepted edit 65 minutes later; hollow circles are partial installs used to locate the leak. B: the same containment phase for both programs, on one clock. PhenoAge took 8½ hours, while the library was still being written; mortality took about one._

Most of that difference is the library, and Figure 4 shows where it pays off. The digit readers, unit conversions, logarithm and summing head were already built, contracted and safe. The agent's work was a new question detector, a new curve and a new output stage. It also ran into two of the documented safety rules again: a gate that opened at position 0 (rule A6) and a gating read with too little margin on unrelated text (rule A4). It fixed both within the hour, because the fixes were already written down.

**What it doesn't show.**

- **It isn't a stack.** The mortality edit is a separate program on the original model: it reuses PhenoAge's neuron slots and refits its question detector, so this model answers mortality but no longer PhenoAge. Putting both programs in one model is the next test, and the linker rules in §6 are written for it.
- **It's the same panel and the same family of formula.** The reused readers are why it was fast. A program needing different inputs, like eGFR, would reuse less.
- **One run, one agent.** It shows the library can transfer, not how reliably.

## 10. What v0.1 doesn't do

- **One model.** Lowered only on Qwen3-0.6B.
- **Exact-wording gates.** The graft switches on for a fixed question line. Paraphrases are out of scope and untested. "Any question asking for PhenoAge" needs new gate instructions.
- **Measured, not proved.** Contracts and certificates are empirical. A certificate is only as good as its probe suite, and 165 probes is small.
- **Composition across authors is untested.** The linker rules are necessary, not sufficient.
- **Architectures.** No mixture-of-experts, state-space models or encoder-decoders yet.

## 11. An invitation

The spec, the example files, the PhenoAge certificate and a reproducibility package for both programs are attached. The most useful thing anyone could do with them:

1. **Write a hello graft** from the template, on any model in the Llama/Qwen/Mistral family, and publish its `.gcert`.
2. **Compile a second clinical formula** (eGFR, MELD, FIB-4) and report which instructions you reused, refit or wrote new.
3. **Break a certificate.** Find a prompt the PhenoAge graft changes that the 165 probes missed.

If GRAFT is useful, it'll be because someone other than the agents that built it could use it.

---

### Files

| File                                                                  | What                                                                |
| --------------------------------------------------------------------- | ------------------------------------------------------------------- |
| [`GRAFT_SPEC.md`](/graft/GRAFT_SPEC.md)                               | the v0.1 specification (normative)                                  |
| [`examples/anchor.graft.yaml`](/graft/examples/anchor.graft.yaml)     | the minimal graft: one `step` pair from PhenoAge, real values       |
| [`examples/phenoage.graft.yaml`](/graft/examples/phenoage.graft.yaml) | the full PhenoAge program in `.graft` form, with measured contracts |
| [`examples/phenoage.gcert.json`](/graft/examples/phenoage.gcert.json) | its certificate, generated from the run's records                   |
| [`examples/hello.graft.yaml`](/graft/examples/hello.graft.yaml)       | template for the minimal program (not yet built)                    |
| [`make_cert.py`](/graft/make_cert.py)                                 | regenerates the certificate from the records                        |
