# GRAFT Specification v0.1 (draft)

**GRAFT: Gated Reusable Algorithms For Transformers.** A common format for writing, combining and certifying small algorithms that are written directly into a pretrained transformer's weights.

> **Provenance.** This specification was written _after_ the PhenoAge run, by the supervising Claude session at the project owner's request. It formalises the instruction set the planner and surgeon agents built and documented (`ISA_SPEC.md`, `PRIMITIVES.md`, `isa/`). The PhenoAge program was built **without** this document. Every number below comes from that run's records. Nobody outside the project has yet written a graft from this spec; that is the test that matters (§10).

The key words MUST, SHOULD and MAY are used as in RFC 2119.

---

## 0. What can be universal, and what can't

Three layers, with decreasing portability:

| Layer         | What it fixes                                                                                               | Portability                                                                                                                                                                      |
| ------------- | ----------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Interface** | what every graft must declare (§2), the file format (§4), the certificate (§7), the conformance levels (§8) | **Universal.** Model-agnostic, architecture-agnostic.                                                                                                                            |
| **Opcodes**   | the elementary weight operations (§3)                                                                       | **Portable within an architecture class.** v0.1 defines them for pre-norm decoder transformers with RMSNorm, SiLU-gated MLPs and RoPE attention (the Llama/Qwen/Mistral family). |
| **Values**    | every read vector, write vector, neuron slot and threshold                                                  | **Model-specific.** Produced by _lowering_ (§5), a calibration pass on the target model's own activations.                                                                       |

So a universal _language_ is possible, but universal _weights_ are not. The analogy is source code and binaries: a `.graft` file is portable source; lowering it against a specific model produces a `.gdelta` (the binary) and a `.gcert` (its test report). The same source lowered against two models produces two different deltas.

v0.1 has only been lowered on one model (Qwen3-0.6B). Portability of opcodes across models in the class is a hypothesis.

---

## 1. The abstract machine

| Term                 | Meaning                                                                                                                                                                            |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| residual `x`         | the per-token state vector (width `d`) that every layer reads from and adds to                                                                                                     |
| normalised state `x̂` | `γ ⊙ x / rms(x)`: what every module actually reads                                                                                                                                 |
| **read**             | a covector `r` on `x̂`. Physically it _is_ a weight row (gate/up row of an MLP neuron; q/k/v row of a head). Value `r·x̂`.                                                           |
| **write**            | a raw residual vector. Physically a weight column (MLP down column; attention output column). A write `w` is read at later layers as roughly `γ ⊙ w / ‖x‖ · √d`.                   |
| **site**             | a declared weight slice: one MLP neuron (its gate row, up row, down column), the q rows of one head, the k or v rows of one kv-group, one value channel, the o columns of one head |
| **channel**          | a named residual direction that carries one quantity between layers (the graft's private "variable")                                                                               |
| **CONST**            | a read with `c·x̂ ≈ 1` on the token population of interest; biases are folded in as `b·c`                                                                                           |
| **scope**            | the set of inputs (and token positions) on which a graft is meant to be ON                                                                                                         |

**Site modes.**

- `set`: the slice is replaced. Exclusive: only one owner per slice.
- `add`: the original is kept and a delta is stacked on it (also called DUAL). Several owners MAY add to one slice; each owner's delta is stored separately so it can be replaced or removed.

**Write regimes.** Every write MUST declare one:

- `perturbative`: at most ~5% of `‖x‖` at the written token;
- `dominant`: at least ~3× `‖x‖`. The written token's later state becomes deterministic, so later reads of it are exact (a **pin**);
- `norm-tracking`: scaled with `‖x‖`, so the downstream read is stable across tokens.

Constant writes in the middle band are forbidden. They change the token's norm by an amount that varies across tokens, which moves every later threshold (rule A3).

---

## 2. The minimal GRAFT

A **graft** is a weight edit that declares six fields. Drop any one and you lose a property that makes it safe to add to someone else's model:

| #   | Field           | What it is                                                                                              | Without it                                |
| --- | --------------- | ------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| 1   | **target**      | model id + sha256 of the base weights it applies to                                                     | you don't know what it was fitted against |
| 2   | **sites**       | the exact weight slices it touches, with mode `set`/`add`                                               | it can't be undone or audited             |
| 3   | **gate**        | the read(s) that switch it on, and its declared **scope**                                               | it is fine-tuning: a global change        |
| 4   | **payload**     | reads → opcode(s) → writes, into named channels or the output                                           | it does nothing                           |
| 5   | **contract**    | a measurable claim: `{scope} graft {postcondition ± tolerance}`, with the data split it was measured on | it's an unchecked claim                   |
| 6   | **certificate** | side-effect bound on a declared probe suite + delta hash + exact undo                                   | its risk is unknown                       |

**The smallest valid graft is one opcode instance carrying all six fields.** In practice that is a single `step` pair: two MLP neurons, `6d` scalars (6,144 in Qwen3-0.6B). One of the three ANCHOR pairs of the PhenoAge program is exactly this (`examples/anchor.graft.yaml`).

**Components and programs.**

- A **component** graft's contract is about an internal channel, e.g. "channel `eA` > 0.6 at token ' ' of the question line, < 0.47 on every adversarial text."
- A **program**'s contract is about the model's output, e.g. "the answer equals round(PhenoAge) within 1.5 years MAE."

**The minimal program.** A visible behaviour change needs at least three instructions:

1. a gate (ANCHOR + FLAG), so it is ON only for its question;
2. a payload;
3. an EMIT, to write a token.

The smallest is "answer this exact question with this constant": ANCHOR, FLAG, EMIT(constant). This "hello graft" has not been built yet; it is the suggested first exercise (§10).

---

## 3. Opcodes (v0.1)

Counts are scalars touched, with `d` = model width and `d_h` = head dimension. "Neuron" means one MLP neuron (gate row + up row + down column = `3d`).

| Opcode                                    | Semantics                                                                                                                       | Sites                                                    |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `step(L, pair, gate, const, up, down, A)` | `down·[silu(g + A·c) − silu(g)]/A · (up·x̂)` with `g = gate·x̂`. For `g ≫ 0`: `down·(c·x̂)(up·x̂)`; for `g ≪ 0`: 0. A gated switch. | 2 neurons, `set`                                         |
| `gated_linear`                            | `step` with `up` = a linear read: writes `down × value` only when the gate is on                                                | 2 neurons, `set`                                         |
| `kink(L, j, gate, up, down)`              | `down·silu(g)·(up·x̂) ≈ s·relu(r − t)·e`. One piecewise-linear segment; chains draw curves (ln, exp)                             | 1 neuron, `set`                                          |
| `keyswitch(L, g, Δ, r)`                   | `k(g) += Δ·(r·x̂)`, rank 1. Redirects a head's keys only where the private read `r` is on                                        | `d_h` k rows, `add`                                      |
| `qswitch(L, h, Δ, r)`                     | `q(h) += Δ·(r·x̂)`                                                                                                               | `d_h` q rows, `add`                                      |
| `vtake(L, g, ch, vrow, ocols)`            | value channel `ch` of kv-group `g` := `vrow`; the o columns of its heads := `ocols`                                             | 1 v row + o columns, `set`                               |
| `vadd`                                    | additive version of `vtake`                                                                                                     | same, `add`                                              |
| `head_take`, `group_kv`                   | replace a whole head / kv-group                                                                                                 | `d_h` rows/cols, `set` (defined, discouraged by rule A2) |

**Design routines.** These are closed-form, offline fits that produce the vectors opcodes consume. They are part of the library but not part of the format: any method MAY be used, as long as lowering is deterministic and recorded.

- `fit_const`: ridge.
- `minvar_read`: a private read with minimal background variance.
- `quiet_dirs` and null-space directions: eigenproblems.
- `pos_design` / `pos_design_mass`: an LP and an exponentiated-gradient fit over RoPE plane energies, for exact positional attention.
- Linear-SVM conjunction detectors.

---

## 4. The `.graft` file

YAML. One file declares a program (or a component) and everything a lowering tool and a reviewer need.

```yaml
graft: 0.1
name: <program name>
version: <semver>
summary: <one line>

target:
  arch_class: prenorm-rmsnorm-gatedmlp-rope   # v0.1's only class
  model: <hub id>                             # optional for portable sources
  weights_sha256: <hash>                      # REQUIRED once lowered

scope:
  kind: template            # v0.1: gates anchor on fixed question wording
  question: "<the exact question line>"
  positions: after_anchor   # which tokens the graft may be ON at

imports:                    # other grafts/instructions this one builds on
  - {from: <graft>@<version>, use: <instruction>, status: REUSED | REFIT | NEW}

channels:                   # the symbol table: one writer per channel
  - {name: <id>, written_at: L<n>, read_until: L<m>, regime: dominant | perturbative | norm-tracking, meaning: "<what it carries>"}

instructions:
  - id: <unique id>
    op: <instruction or opcode name>
    at: {layer: <n>, site: mlp | attn, slots: auto | [explicit]}
    gate: <channel or read expression>
    reads: [<channels / model features>]
    writes: [<channels> | output]
    params: {<name>: <value>}
    contract:
      claim: "<postcondition>"
      split: <practice | dev | held-out>
      metric: <name>
      bound: <value>
      measured: <value>          # filled by lowering
    side_effects: {max_kl_alone: <value>}   # optional per-instruction measurement

certificate:
  probe_suite: <suite id + sha256>
  rule: "<side-effect rule>"
  file: <program>.gcert
```

**Contracts are Hoare triples measured on data.** Read `{scope} instruction {claim within bound}`. Every contract MUST name the split it was measured on. Held-out claims MUST be scored once.

---

## 5. Lowering: `.graft` → `.gdelta` + `.gcert`

A lowering tool MUST, for each instruction in order:

1. **Calibrate.** Collect normalised states at the needed layers on in-scope prompts _and_ on a background set of out-of-scope text.
2. **Fit.** Compute reads and writes with a deterministic method (seeded, data hashed).
3. **Allocate.** Choose slots. Default: lowest natural usage in the layer, then verified by the side-effect oracle (rule A1).
4. **Install** through a registry that enforces ownership (§6) and records the original of every touched slice.
5. **Measure** the contract and write `measured`.

It then measures the whole program's contract and the side-effect suite and emits:

- **`.gdelta`**: `{tensor_name: (indices, new_values)}`. Hash = sha256 over tensor names in sorted order; for each, the name bytes then the fp32 bytes of the new values.
- **`.gcert`**: §7.

Lowering MUST be reproducible: re-running it on a fresh copy of the target weights MUST give the same `.gdelta` hash (conformance G3).

---

## 6. Composition and linking

Programs are built from instructions, and later programs from earlier ones. A **linker** (any tool that installs more than one graft) MUST check:

1. **Slot ownership.** A `set` slice has exactly one owner; a second `set` on it is a link error. `add` slices stack, one delta per owner.
2. **Channel table.** Each channel has one writer. Every reader of a channel sits at a later layer than its writer, and no later than `read_until`. Two grafts claiming the same channel name are renamed or rejected.
3. **Regimes.** A channel's declared regime holds at every write.
4. **Stacking on an accepted base.** When re-installing onto weights that already contain accepted grafts, `add` deltas of those grafts MUST be subtracted first, or they apply twice (rule A7). `set` slices re-install identically.
5. **Re-certification.** Every combination is a new program and MUST be re-certified. Side effects are not additive: removal damage was super-additive in the run (rule A1).

**Imports.** An instruction reused by a new program declares its status:

- `REUSED`: same values.
- `REFIT`: same instruction and slots, new fit.
- `NEW`.

The mortality program is the first real example. Its layer map reuses PINS, SHIFT, BITS, AFFINE, LOG_PWL and SUM_POOL unchanged, refits ANCHOR and GATED_Z, and adds one new curve stage.

---

## 7. The certificate (`.gcert`)

JSON. Required fields:

| Field          | Content                                                                                                           |
| -------------- | ----------------------------------------------------------------------------------------------------------------- |
| `target`       | model id, base weight sha256, architecture class, `d`, layers                                                     |
| `delta`        | format, sha256 + rule, changed scalars, tensors, by layer, by kind                                                |
| `resources`    | replaced neurons per layer, attention switches, value channels taken                                              |
| `undo`         | method; whether it is exact                                                                                       |
| `side_effects` | probe suite id + reference hash, rule, max KL, confident flips, near-tie flips, pass/fail, the strict-rule result |
| `contracts`    | program contract: claim, split, metric, bound, measured, CI, pass/fail, comparators                               |
| `reproduction` | how the recipe rebuilds the delta; rebuilt hash; match                                                            |
| `conformance`  | levels met (§8)                                                                                                   |

A certificate records outcomes; it does not require success. `examples/phenoage.gcert.json` records a program that **missed** its 1.5-year bar by 0.024 and is still fully conformant.

**Default side-effect rule (from the PhenoAge run).** Max KL ≤ 0.5 over the suite, and at most one top-1 change among probes where the original model's top-1/top-2 logit gap is ≥ 0.15 nats. The strict count, which includes near-ties, MUST also be reported.

v0.1's suite is 165 probes: 105 multiple-choice, 40 age questions and 20 chat. That is small. A shared community suite is an open item (§10).

---

## 8. Conformance levels

| Level  | Name         | Requires                                                                        |
| ------ | ------------ | ------------------------------------------------------------------------------- |
| **G0** | Reversible   | declared sites; `.gdelta` with hash; exact undo                                 |
| **G1** | Contracted   | G0 + every instruction and the program carry a measured contract with its split |
| **G2** | Certified    | G1 + a side-effect certificate on a declared probe suite                        |
| **G3** | Reproducible | G2 + lowering rebuilds the delta bit-exactly from the base weights              |

PhenoAge E3 is **G3**: 1,957,862 changed scalars, sha256 `96c61417…`, rebuilt bit-exactly in a separate process.

---

## 9. Authoring rules (normative)

These are the PhenoAge run's eight safety rules, restated as requirements. Each one was learned from a failure; the run's log has the evidence.

- **A1 Placement is empirical.** Authors MUST verify slot choices with the real side-effect suite, not a proxy. The same 24-neuron edit cost max KL 0.553 in layer 5 and 0.033 in layer 6. To find culprits, bisect a slot set by halves and swap slots.
- **A2 Switch heads; don't remove them.** Attention edits SHOULD be `add` (key/query switches on private reads). Head replacement is discouraged.
- **A3 Write regimes.** Every write MUST be perturbative, dominant or norm-tracking (§1). A leak's damage is set by its size, not its direction: re-choosing a leaking write's direction to be 37× less read downstream did not reduce its side effects.
- **A4 Guard gating reads.** A read that gates a large write MUST either be a designed read of a code that only exists in scope (a pin or indicator), or carry an explicit guard term. Regression-fitted reads reached O(1–10) on unrelated text.
- **A5 Don't fit on the test probes.** Directions MUST NOT be tuned on the certificate's probe suite. In the run, a direction tuned to be quiet on a proxy probe set looked 3× quieter there but made the real side-effect KL 2.3× worse.
- **A6 Position 0 is its own class.** CONST reads are about −0.1 at the attention-sink position, so threshold gates are _open_ there. Every up-read MUST be exactly 0 at position 0.
- **A7 Subtract before re-install.** See §6.4.
- **A8 One configuration per install,** and never terminate the host process from installer code.

---

## 10. Known limits of v0.1 and open items

- **One model.** Lowered only on Qwen3-0.6B. Cross-model portability is untested.
- **Template scope only.** Gates anchor on the exact wording of the question line; paraphrases are out of scope and untested. Semantic scope ("any question asking for PhenoAge") needs new gate instructions.
- **Empirical, not formal.** Contracts and certificates are measured on data, not proved. A certificate is only as good as its probe suite.
- **Small probe suite.** 165 probes. A shared, larger suite (and a held-back private one) would make certificates comparable across authors.
- **Composition.** The linker rules are necessary, not sufficient. Two independently written grafts in one model have not been tested.
- **Architectures.** No MoE (routing would need a gate opcode), no state-space models, no encoder-decoders.
- **First third-party test.** Someone other than the original agents writes a graft from this spec alone. Suggested exercise: the "hello graft" (§2), then a second clinical formula.

---

## Files

| File                           | What                                                               |
| ------------------------------ | ------------------------------------------------------------------ |
| `GRAFT_SPEC.md`                | this document                                                      |
| `examples/anchor.graft.yaml`   | the minimal graft: one `step` pair from the PhenoAge program       |
| `examples/phenoage.graft.yaml` | the PhenoAge program in `.graft` form, with measured contracts     |
| `examples/phenoage.gcert.json` | its certificate, generated from the run's records (`make_cert.py`) |
| `examples/hello.graft.yaml`    | template for the minimal program (not yet built)                   |
