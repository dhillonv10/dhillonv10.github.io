"""scGPT backbone: checkpoint download/loading, tokenisation and cell embedding.

Uses scgpt==0.2.4's TransformerModel and DataCollator unchanged. The vocabulary is read from the checkpoint's
vocab.json with a small torchtext-free class that keeps the exact token ids.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import torch
from torch.utils.data import DataLoader, Dataset

from .adapters import disable_transformer_fastpath

SPECIAL_TOKENS = ("<pad>", "<cls>", "<eoc>")


class JSONGeneVocab:
    def __init__(self, token_to_id: dict):
        self._stoi = {str(k): int(v) for k, v in token_to_id.items()}
        if sorted(self._stoi.values()) != list(range(len(self._stoi))):
            raise ValueError("vocab ids must be consecutive")

    def __len__(self): return len(self._stoi)
    def __contains__(self, t): return t in self._stoi
    def __getitem__(self, t): return self._stoi[t]
    def append_token(self, t): self._stoi[t] = len(self._stoi)
    def get_stoi(self): return dict(self._stoi)


def download_scgpt(model_dir: str | Path) -> Path:
    from huggingface_hub import snapshot_download
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    if not all((model_dir / f).exists() for f in ("args.json", "vocab.json", "best_model.pt")):
        snapshot_download(repo_id="wanglab/scGPT-human", repo_type="model",
                          allow_patterns=["args.json", "vocab.json", "best_model.pt"], local_dir=str(model_dir))
    return model_dir


def load_scgpt(model_dir: str | Path, device: str = "cpu", pretrained: bool = True, verbose: bool = True):
    """Return (model, vocab, cfg). Mirrors scgpt.tasks.embed_data's construction (non-flash attention)."""
    from scgpt.model import TransformerModel
    from scgpt.utils import load_pretrained
    model_dir = Path(model_dir)
    vocab = JSONGeneVocab(json.loads((model_dir / "vocab.json").read_text()))
    for t in SPECIAL_TOKENS:
        if t not in vocab:
            vocab.append_token(t)
    cfg = json.loads((model_dir / "args.json").read_text())
    cfg.setdefault("mask_value", -1)
    model = TransformerModel(
        ntoken=len(vocab), d_model=cfg["embsize"], nhead=cfg["nheads"], d_hid=cfg["d_hid"], nlayers=cfg["nlayers"],
        nlayers_cls=cfg["n_layers_cls"], n_cls=1, vocab=vocab, dropout=cfg["dropout"], pad_token=cfg["pad_token"],
        pad_value=cfg["pad_value"], do_mvc=True, do_dab=False, use_batch_labels=False, domain_spec_batchnorm=False,
        explicit_zero_prob=False, use_fast_transformer=False, fast_transformer_backend="flash", pre_norm=False)
    if pretrained:
        sd = torch.load(model_dir / "best_model.pt", map_location="cpu", weights_only=False)
        load_pretrained(model, sd, verbose=False)
        sd2 = {k.replace("Wqkv.", "in_proj_"): v for k, v in sd.items()}
        ms = model.state_dict()
        ok = sum(k in sd2 and sd2[k].shape == v.shape for k, v in ms.items())
        if verbose:
            print(f"[scGPT] pretrained tensors loaded: {ok}/{len(ms)}")
        if ok < 0.9 * len(ms):
            raise RuntimeError("most checkpoint tensors failed to load")
    disable_transformer_fastpath(model)
    return model.to(device).eval(), vocab, cfg


def gene_ids_for(var_names, vocab) -> np.ndarray:
    """Vocabulary id per gene, -1 if the gene is not in the vocabulary."""
    return np.array([vocab[g] if g in vocab else -1 for g in map(str, var_names)], dtype=np.int64)


class CellDataset(Dataset):
    """Sparse raw counts (cells x genes, only in-vocabulary genes) -> <cls> + expressed genes and values."""

    def __init__(self, X, gene_ids: np.ndarray, cls_id: int, pad_value: float):
        X = sp.csr_matrix(X)
        if X.shape[1] != len(gene_ids):
            raise ValueError("X columns and gene_ids differ in length")
        if (gene_ids < 0).any():
            raise ValueError("drop out-of-vocabulary genes before building the dataset")
        self.X, self.g, self.cls, self.pv = X, np.asarray(gene_ids), cls_id, pad_value

    def __len__(self):
        return self.X.shape[0]

    def __getitem__(self, i):
        s, e = self.X.indptr[i], self.X.indptr[i + 1]
        genes = np.insert(self.g[self.X.indices[s:e]], 0, self.cls)
        vals = np.insert(self.X.data[s:e].astype(np.float32), 0, self.pv)
        return {"id": i, "genes": torch.from_numpy(genes).long(), "expressions": torch.from_numpy(vals)}


def make_collator(vocab, cfg, max_len: int, mlm: bool = False, mlm_probability: float = 0.4):
    from scgpt.data_collator import DataCollator
    return DataCollator(do_padding=True, pad_token_id=vocab[cfg["pad_token"]], pad_value=cfg["pad_value"],
                        do_mlm=mlm, do_binning=True, mlm_probability=mlm_probability, mask_value=cfg["mask_value"],
                        max_length=max_len, sampling=True, keep_first_n_tokens=1)


def seed_everything(seed: int) -> None:
    """scGPT's binning breaks ties with numpy's GLOBAL RNG (scgpt.preprocess._digitize), so embeddings of integer
    counts are random unless numpy is seeded too. Seed numpy, torch and python's random."""
    import random
    random.seed(seed)
    np.random.seed(seed % (2**32))
    torch.manual_seed(seed)


def worker_init(worker_id: int) -> None:
    """Give each DataLoader worker a deterministic numpy seed derived from torch's per-worker seed."""
    np.random.seed(torch.initial_seed() % (2**32))


def autocast(device):
    dev = torch.device(device) if not isinstance(device, torch.device) else device
    return torch.autocast(device_type="cuda", dtype=torch.float16, enabled=dev.type == "cuda")


def cls_embedding(model, gene, expr, pad_id):
    """<cls> token state after the last transformer layer (adapters, if attached, are applied by hooks)."""
    return model._encode(gene, expr, src_key_padding_mask=gene.eq(pad_id))[:, 0, :]


@torch.no_grad()
def embed(model, X, gene_ids, vocab, cfg, max_len=1200, batch_size=32, seed=0, num_workers=0, normalize=True, progress=False):
    """L2-normalised <cls> embeddings (same recipe as scgpt.tasks.embed_data). Deterministic given seed."""
    seed_everything(seed)
    model.eval()
    dev = next(model.parameters()).device
    pad_id = vocab[cfg["pad_token"]]
    ds = CellDataset(X, gene_ids, vocab["<cls>"], cfg["pad_value"])
    dl = DataLoader(ds, batch_size=batch_size, shuffle=False, collate_fn=make_collator(vocab, cfg, max_len),
                    num_workers=num_workers, worker_init_fn=worker_init)
    out = np.zeros((len(ds), cfg["embsize"]), np.float32)
    n = 0
    it = dl
    if progress:
        from tqdm.auto import tqdm
        it = tqdm(dl, desc="embed", leave=False)
    for b in it:
        g = b["gene"].to(dev)
        with autocast(dev):
            h = cls_embedding(model, g, b["expr"].to(dev), pad_id)
        out[n:n + len(h)] = h.float().cpu().numpy()
        n += len(h)
    if not np.isfinite(out).all():
        raise FloatingPointError("non-finite embeddings")
    if normalize:
        out /= np.linalg.norm(out, axis=1, keepdims=True).clip(1e-8)
    return out


def write_tiny_checkpoint(model_dir: str | Path, genes, seed: int = 0) -> Path:
    """Random tiny scGPT checkpoint in the real file format (for tests / smoke runs)."""
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    stoi = {t: i for i, t in enumerate(list(SPECIAL_TOKENS) + [str(g) for g in genes])}
    cfg = dict(embsize=32, nheads=2, d_hid=32, nlayers=2, n_layers_cls=1, dropout=0.1, pad_token="<pad>", pad_value=-2, mask_value=-1)
    (model_dir / "vocab.json").write_text(json.dumps(stoi))
    (model_dir / "args.json").write_text(json.dumps(cfg))
    torch.manual_seed(seed)
    m, _, _ = load_scgpt(model_dir, pretrained=False, verbose=False)
    torch.save(m.state_dict(), model_dir / "best_model.pt")
    return model_dir
