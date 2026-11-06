# AML adapter for scGPT

A small, trainable **AML adapter** on top of a frozen single-cell foundation model (**scGPT whole-human**), plus a
benchmark that decides, with numbers fixed in advance, whether the adapter is worth anything.

```
raw UMI counts ──► scGPT tokeniser (genes + binned expression)
                    │
                    ▼
        ┌────────────────────────────┐
        │ scGPT transformer layer 1  │  frozen (51M parameters, never updated)
        └────────────┬───────────────┘
                     ▼
              AML adapter 1          h + W_up·GELU(W_down·LN(h))   trainable, zero-initialised
                     ▼
                    ...  × 12 layers
                     ▼
              <cls> cell state ──► heads: P(malignant), AML cell state (21 classes)
```

* **~0.8M trainable parameters** (1.6% of scGPT). The backbone and the checkpoint stay untouched; an adapter file is ~3 MB.
* **Zero-initialised**: before training, the adapted model gives exactly the original scGPT output (tested).
* Two ways to train it:
  1. **SSL**: self-supervised, on *unlabelled* AML cells, with scGPT's own masked-expression objective (GEP + GEPC).
  2. **task**: supervised, with a malignancy head and a cell-state head (losses balanced so neither swamps the other),
     either from zero (`scGPT+task`) or starting from the SSL adapter (`scGPT+SSL+task`).

## The tasks, and why each one

You asked me to define tasks where an AML adapter could show promise. These three use only public data with real
labels, evaluate on held-out *patients*, and each asks a different question.

| | Task | Data | Label | Why it is a good test | Primary metric |
|---|---|---|---|---|---|
| **T1** | Malignant vs normal cell | van Galen 2019 (GSE116256; 16 AML + 5 healthy marrows, diagnosis and post-treatment) | authors' malignant/normal call | the basic job; patient-held-out K-fold | AUROC |
| **T2** | **Cross-cohort, cross-platform transfer** | train on **all** van Galen (Seq-Well), test on **Naldini 2023** (GSE185991; 10 NPM1-mutant AML patients, 10x Genomics, diagnosis, day 14/30 after induction, relapse) | **per-cell NPM1 genotype** (mutant reads vs wild-type-only reads) | the strongest test: a different lab, platform and labelling method, and genotype truth that no model ever trains on; also scored *after induction*, where regenerating normal marrow mimics leukemia | AUROC (also: AUROC on day-14/30 cells, false-positive rate at 90% sensitivity) |
| **T3** | AML cell-state annotation | van Galen | 21 states: malignant HSC-like / Prog-like / GMP-like / ProMono-like / Mono-like / cDC-like and normal counterparts, T, NK, B, erythroid ... | the task on which general foundation models are reported to struggle in AML | macro-F1 |

**Where I expect the adapter could show promise:** T2. Foundation-model representations are meant to be more
platform-robust than gene-expression baselines, and the adapter can also be adapted, without labels, to the target
cohort (`(+tgt)` variants: unsupervised domain adaptation). T1 is likely to be hard to beat because expression baselines
are strong there. T3 tests whether adaptation recovers AML-specific states that frozen models blur.

### Methods compared (same splits, same probe)

| Method | What it is |
|---|---|
| `HVG-LR` | log-normalised top-3,000 variance genes → logistic regression |
| `PCA-LR` | the same, compressed to 50 PCs |
| `scGPT-frozen` | original scGPT cell embedding → logistic regression |
| `scGPT+SSL` | scGPT + SSL-trained AML adapter → logistic regression |
| `scGPT+task` | scGPT + supervised AML adapter with heads (end to end) |
| `scGPT+SSL+task` | the same, starting from the SSL adapter |
| `…(+tgt)` (T2) | SSL also sees **unlabelled** Naldini cells (no Naldini labels are used anywhere) |

Every logistic regression uses the same probe: standardise, then choose C by inner cross-validation grouped by patient.
Expression baselines (HVG/PCA) are fitted on training patients only. Each SSL adapter in T1/T3 is trained on that fold's
training patients only.

### What counts as "promise" (fixed before any result)

On a task's primary metric, an adapter variant must beat **both** `scGPT-frozen` and the better of `HVG-LR`/`PCA-LR`,
with the **95% patient-bootstrap CI of each paired difference above 0**. The `PROMISE` table in the report applies this
rule mechanically. If no variant passes anywhere, the adapter has not shown promise on these tasks, and the report says so.

### Labels and their limits (read before interpreting)

* van Galen's malignant/normal call comes from the authors' expression-based classifier, trained on mutation-detected
  cells. Expression models agreeing with it is partly circular. That is why T2 matters: its truth is genotype.
* Naldini's genotype is single-locus (NPM1). A wild-type-only call can, rarely, be a leukemic cell that dropped its
  mutant read. At diagnosis this happens in <1% of genotyped cells in most patients, but more in two (PT06, PT07, which
  carry real residual normal cells). Healthy-donor matrices for Naldini were not deposited.
* T3 cell states are the authors' annotations (also classifier-derived for the malignant states).
* Day 14/30 samples include persistent disease, not only remission marrow. Nothing here is a clinical MRD assay.
* van Galen cells are shallow (Seq-Well); Naldini cells are deeper (10x). scGPT reads at most `max_len` = 1,200 genes
  per cell, sampled at random beyond that (scGPT's standard behaviour).

## Running it

### Colab (recommended: one T4/L4 GPU)
Open `notebooks/AML_Adapter_Colab.ipynb`. It installs the dependencies, downloads both cohorts and scGPT, runs the
benchmark (`--profile full`, about 3-4 h with every variant), and loads the trained adapter for prediction.
Everything is written to Google Drive, and downloads and caches resume.

### Command line
```bash
pip install -r requirements.txt
python scripts/run_benchmark.py --profile smoke --out results/smoke                      # synthetic, ~2 min, CPU
python scripts/run_benchmark.py --profile full  --data-root data --out results/full      # GPU
python scripts/run_benchmark.py --profile full  --tasks T2 --set t2_target_ssl=false     # one task, fewer variants
```
`--set key=value` overrides any field of `BenchConfig` (e.g. `ssl_steps=4000 bottleneck=128 max_len=2048`).

Profiles: `smoke` (synthetic data, tiny random backbone: plumbing only), `cpu-mini` (real data and real scGPT on a CPU,
40 cells per sample, short sequences, few steps: a pipeline check, not a result), `full` (the experiment).

### Outputs (`--out` directory)
`REPORT.md` (all tables), `PROMISE.csv`, `T1_*.csv`, `T2_*.csv`, `T3_*.csv`, `predictions.csv.gz` (every cell × method),
`training_logs.json` (the SSL held-out masked loss should fall), `adapters/*.pt`, `aml_adapter_task.pt`,
`aml_adapter_ssl_task.pt`, and **`aml_adapter_final.pt`**: the shipped model. It is the better of the two on van Galen
cross-validation; the Naldini test set never influences the choice.

### Using the trained model
```python
from amladapter.model import AMLAdapterModel
m = AMLAdapterModel.load("results/full/aml_adapter_final.pt", scgpt_dir="models/scGPT-human", device="cuda")
pred = m.predict(adata)   # adata.X = raw UMI counts, var_names = gene symbols
# -> malignant_prob, malignant_logit, celltype_pred, celltype_prob (one row per cell)
emb = m.embed(adata)      # AML-adapted 512-d cell embeddings for clustering / UMAP / your own classifiers
```

## Package layout
```
amladapter/
  data.py       download + load both cohorts into one AnnData schema (resumable, rate-limited GEO downloads)
  backbone.py   scGPT loading, tokenisation, deterministic embedding
  adapters.py   bottleneck adapters attached by forward hooks (backbone frozen, zero-init)
  train.py      SSL (masked expression) and supervised task training; prediction
  baselines.py  HVG/PCA encoders and the shared patient-grouped logistic-regression probe
  benchmark.py  tasks, splits, methods, metrics, patient bootstrap, PROMISE rule, report, model selection
  model.py      inference API for a trained adapter
scripts/run_benchmark.py
tests/          adapter guarantees + an end-to-end synthetic benchmark (pytest)
```

## Implementation notes that affect results
* **scGPT embeddings are random unless numpy is seeded.** scGPT's expression binning breaks ties between equal counts
  with numpy's global random generator. Integer UMI counts are full of ties, so the same cell can embed differently on
  two runs. All inference here seeds numpy (also inside DataLoader workers), so results are reproducible.
* PyTorch's fused transformer "fast path" is switched off so adapters always run, with identical numerics in training
  and inference.
* The task head standardises the `<cls>` state across cells (BatchNorm), mirroring the probe's StandardScaler.
