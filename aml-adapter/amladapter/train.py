"""Training loops: self-supervised AML adaptation and supervised task adapters (backbone always frozen)."""
from __future__ import annotations
import math
import time
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset, RandomSampler, WeightedRandomSampler

from .backbone import CellDataset, autocast, cls_embedding, make_collator, seed_everything, worker_init


# ----------------------------------------------------------------------------------------------- utilities
def _scheduler(opt, steps: int, warmup_frac: float = 0.05, floor: float = 0.1):
    warm = max(1, int(warmup_frac * steps))
    def f(s):
        if s < warm:
            return (s + 1) / warm
        return floor + (1 - floor) * 0.5 * (1 + math.cos(math.pi * (s - warm) / max(1, steps - warm)))
    return torch.optim.lr_scheduler.LambdaLR(opt, f)


def _sampler(n_items: int, n_draws: int, seed: int, weights=None):
    gen = torch.Generator().manual_seed(seed)
    if weights is None:
        return RandomSampler(range(n_items), replacement=True, num_samples=n_draws, generator=gen)
    return WeightedRandomSampler(torch.as_tensor(weights, dtype=torch.double), num_samples=n_draws, replacement=True, generator=gen)


class RandMaskCollator:
    """scGPT pretraining drew the mask ratio from {0.25, 0.5, 0.75}; do the same per batch."""
    def __init__(self, base, ratios):
        self.base, self.ratios = base, tuple(ratios)

    def __call__(self, ex):
        self.base.mlm_probability = float(self.ratios[int(torch.randint(len(self.ratios), (1,)))])
        return self.base(ex)


def _masked_loss(model, b, dev, pad_id, mask_value):
    from scgpt.loss import masked_mse_loss
    g, tgt, masked = b["gene"].to(dev), b["expr"].to(dev), b["masked_expr"].to(dev)
    with autocast(dev):
        o = model(g, masked, src_key_padding_mask=g.eq(pad_id), MVC=True)
    pos = masked.eq(mask_value)
    return (masked_mse_loss(o["mlm_output"].float(), tgt.float(), pos)
            + masked_mse_loss(o["mvc_output"].float(), tgt.float(), pos))


@torch.no_grad()
def masked_eval_loss(model, X, gene_ids, vocab, cfg, max_len, batch=16, seed=1234, mask_ratio=0.5):
    """Fixed-seed masked-expression loss (GEP+GEPC) on given cells: used to check that SSL adaptation learns."""
    seed_everything(seed)
    was = model.training
    model.eval()
    dev = next(model.parameters()).device
    ds = CellDataset(X, gene_ids, vocab["<cls>"], cfg["pad_value"])
    dl = DataLoader(ds, batch_size=batch, shuffle=False, collate_fn=make_collator(vocab, cfg, max_len, mlm=True, mlm_probability=mask_ratio))
    vals = [_masked_loss(model, b, dev, vocab[cfg["pad_token"]], cfg["mask_value"]).item() for b in dl]
    model.train(was)
    return float(np.mean(vals))


# ------------------------------------------------------------------------------------------ self-supervised
def train_ssl(model, adapters, X, gene_ids, vocab, cfg, *, steps, lr=1e-3, batch=16, accum=1, max_len=1200,
              mask_ratios=(0.25, 0.5, 0.75), seed=0, num_workers=0, n_val=128, log_every=100, sample_weights=None, label="ssl"):
    """Masked gene-expression modelling on UNLABELLED AML cells. Only adapter parameters are updated.

    Returns a dict with the held-out masked loss before/after (cells held out from the training set given here)."""
    seed_everything(seed)
    rng = np.random.default_rng(seed)
    dev = next(model.parameters()).device
    pad_id = vocab[cfg["pad_token"]]
    perm = rng.permutation(X.shape[0])
    n_val = min(n_val, max(4, X.shape[0] // 10))
    val_idx, tr_idx = perm[:n_val], perm[n_val:]
    Xv, Xt = X[val_idx], X[tr_idx]
    w = None if sample_weights is None else np.asarray(sample_weights)[tr_idx]
    ds = CellDataset(Xt, gene_ids, vocab["<cls>"], cfg["pad_value"])
    col = RandMaskCollator(make_collator(vocab, cfg, max_len, mlm=True), mask_ratios)
    dl = DataLoader(ds, batch_size=batch, sampler=_sampler(len(ds), steps * accum * batch, seed, w), collate_fn=col,
                    num_workers=num_workers, drop_last=True, worker_init_fn=worker_init)
    params = [p for p in adapters.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=lr, weight_decay=0.01)
    sched = _scheduler(opt, steps)
    scaler = torch.amp.GradScaler("cuda", enabled=dev.type == "cuda")
    adapters.enabled = True
    loss0 = masked_eval_loss(model, Xv, gene_ids, vocab, cfg, max_len)
    model.train(); adapters.train()
    hist, t0, micro, step = [], time.time(), 0, 0
    for b in dl:
        loss = _masked_loss(model, b, dev, pad_id, cfg["mask_value"])
        scaler.scale(loss / accum).backward()
        micro += 1
        if micro % accum:
            continue
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        scaler.step(opt); scaler.update(); opt.zero_grad(set_to_none=True); sched.step(); step += 1
        hist.append(loss.item())
        if log_every and step % log_every == 0:
            print(f"  [{label}] step {step}/{steps} loss {np.mean(hist[-log_every:]):.4f} ({(time.time()-t0)/60:.1f} min)", flush=True)
    model.eval(); adapters.eval()
    loss1 = masked_eval_loss(model, Xv, gene_ids, vocab, cfg, max_len)
    print(f"  [{label}] held-out masked loss {loss0:.4f} -> {loss1:.4f} ({steps} steps, {(time.time()-t0)/60:.1f} min)", flush=True)
    return dict(label=label, heldout_loss_before=loss0, heldout_loss_after=loss1, train_loss=hist, minutes=(time.time() - t0) / 60)


# --------------------------------------------------------------------------------------------- supervised
class TaskHeads(nn.Module):
    """Malignancy logit and (optional) cell-type logits from the <cls> state.

    BatchNorm standardises each feature ACROSS cells (as the linear probes' StandardScaler does); a per-cell
    LayerNorm would leave small between-cell differences in the <cls> state hard to learn from."""
    def __init__(self, d_model: int, n_celltypes: int = 0, dropout: float = 0.1):
        super().__init__()
        self.norm = nn.BatchNorm1d(d_model)
        self.drop = nn.Dropout(dropout)
        self.mal = nn.Linear(d_model, 1)
        self.ct = nn.Linear(d_model, n_celltypes) if n_celltypes else None

    def forward(self, h):
        z = self.drop(self.norm(h))
        return self.mal(z).squeeze(-1), (self.ct(z) if self.ct is not None else None)


class _LabelledDS(Dataset):
    def __init__(self, base: CellDataset, y_mal, y_ct):
        self.base, self.y_mal, self.y_ct = base, np.asarray(y_mal, np.float32), np.asarray(y_ct, np.int64)

    def __len__(self):
        return len(self.base)

    def __getitem__(self, i):
        d = self.base[i]
        d["y_mal"], d["y_ct"] = float(self.y_mal[i]), int(self.y_ct[i])
        return d


class _LabelCollate:
    def __init__(self, base):
        self.base = base

    def __call__(self, ex):
        out = self.base(ex)
        out["y_mal"] = torch.tensor([e["y_mal"] for e in ex], dtype=torch.float32)
        out["y_ct"] = torch.tensor([e["y_ct"] for e in ex], dtype=torch.long)
        return out


def train_supervised(model, adapters, heads, X, gene_ids, vocab, cfg, y_mal, y_ct, *, steps, lr=1e-3, batch=16, accum=1,
                     max_len=1200, seed=0, num_workers=0, sample_weights=None, ct_weight=None, log_every=100, label="task"):
    """Train adapters + heads with BCE (malignant, NaN = unlabelled) and CE (cell type, -1 = unlabelled).

    ct_weight=None balances the two losses at chance level: CE starts at ln(C), BCE at ln(2), so the cell-type
    loss is scaled by ln(2)/ln(C) and cannot swamp the malignancy signal in the shared adapters."""
    seed_everything(seed)
    dev = next(model.parameters()).device
    pad_id = vocab[cfg["pad_token"]]
    y_mal = np.asarray(y_mal, np.float32)
    y_ct = np.asarray(y_ct, np.int64)
    known = np.isfinite(y_mal)
    pos = float((y_mal[known] == 1).sum()); neg = float((y_mal[known] == 0).sum())
    pos_weight = torch.tensor([neg / max(pos, 1.0)], device=dev)
    ct_w = None
    if heads.ct is not None:
        cnt = np.bincount(y_ct[y_ct >= 0], minlength=heads.ct.out_features).astype(float)
        cw = np.where(cnt > 0, 1.0 / np.sqrt(np.maximum(cnt, 1)), 0.0)
        cw = cw / cw[cnt > 0].mean()
        ct_w = torch.tensor(cw, dtype=torch.float32, device=dev)
        if ct_weight is None:
            ct_weight = math.log(2) / math.log(max(int((cnt > 0).sum()), 2))
    ds = _LabelledDS(CellDataset(X, gene_ids, vocab["<cls>"], cfg["pad_value"]), np.where(known, y_mal, -1.0), y_ct)
    dl = DataLoader(ds, batch_size=batch, sampler=_sampler(len(ds), steps * accum * batch, seed, sample_weights),
                    collate_fn=_LabelCollate(make_collator(vocab, cfg, max_len)), num_workers=num_workers, drop_last=True, worker_init_fn=worker_init)
    params = [p for p in list(adapters.parameters()) + list(heads.parameters()) if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=lr, weight_decay=0.01)
    sched = _scheduler(opt, steps)
    scaler = torch.amp.GradScaler("cuda", enabled=dev.type == "cuda")
    bce = nn.BCEWithLogitsLoss(pos_weight=pos_weight, reduction="sum")
    ce = nn.CrossEntropyLoss(weight=ct_w, ignore_index=-1, reduction="sum")
    adapters.enabled = True
    model.train(); adapters.train(); heads.train()
    hist, t0, micro, step = [], time.time(), 0, 0
    for b in dl:
        g = b["gene"].to(dev)
        ym, yc = b["y_mal"].to(dev), b["y_ct"].to(dev)
        with autocast(dev):
            h = cls_embedding(model, g, b["expr"].to(dev), pad_id)
        lm, lc = heads(h.float())
        m = ym >= 0
        loss = bce(lm[m], ym[m]) / max(int(m.sum()), 1)
        if lc is not None and (yc >= 0).any():
            loss = loss + ct_weight * ce(lc, yc) / max(int((yc >= 0).sum()), 1)
        scaler.scale(loss / accum).backward()
        micro += 1
        if micro % accum:
            continue
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        scaler.step(opt); scaler.update(); opt.zero_grad(set_to_none=True); sched.step(); step += 1
        hist.append(loss.item())
        if log_every and step % log_every == 0:
            print(f"  [{label}] step {step}/{steps} loss {np.mean(hist[-log_every:]):.4f} ({(time.time()-t0)/60:.1f} min)", flush=True)
    model.eval(); adapters.eval(); heads.eval()
    print(f"  [{label}] done: {steps} steps, final loss {np.mean(hist[-max(1, len(hist)//10):]):.4f}, {(time.time()-t0)/60:.1f} min", flush=True)
    return dict(label=label, train_loss=hist, minutes=(time.time() - t0) / 60)


@torch.no_grad()
def predict(model, heads, X, gene_ids, vocab, cfg, max_len=1200, batch_size=32, seed=0, num_workers=0):
    """Return (malignancy logits, cell-type logits or None, L2-normalised <cls> embeddings)."""
    seed_everything(seed)
    model.eval(); heads.eval()
    dev = next(model.parameters()).device
    pad_id = vocab[cfg["pad_token"]]
    ds = CellDataset(X, gene_ids, vocab["<cls>"], cfg["pad_value"])
    dl = DataLoader(ds, batch_size=batch_size, shuffle=False, collate_fn=make_collator(vocab, cfg, max_len), num_workers=num_workers,
                    worker_init_fn=worker_init)
    mal, cts, embs = [], [], []
    for b in dl:
        g = b["gene"].to(dev)
        with autocast(dev):
            h = cls_embedding(model, g, b["expr"].to(dev), pad_id)
        lm, lc = heads(h.float())
        mal.append(lm.float().cpu().numpy())
        if lc is not None:
            cts.append(lc.float().cpu().numpy())
        e = h.float().cpu().numpy()
        embs.append(e / np.linalg.norm(e, axis=1, keepdims=True).clip(1e-8))
    return np.concatenate(mal), (np.concatenate(cts) if cts else None), np.concatenate(embs)
