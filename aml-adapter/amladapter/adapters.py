"""Bottleneck adapters for a frozen scGPT TransformerModel.

Each adapter is applied to the output of one transformer layer:
    h -> h + W_up(GELU(W_down(LayerNorm(h))))
W_up is zero-initialised, so a freshly attached adapter set leaves the model's output unchanged.
Adapters are attached with forward hooks, which leaves scGPT's own forward(), decoders and MVC head intact.
PyTorch's fused "fast path" for nn.TransformerEncoder(Layer) is switched off so hooks always run and
numerics are identical between training and inference.
"""
from __future__ import annotations
import json
from pathlib import Path
import torch
from torch import nn


def disable_transformer_fastpath(model: nn.Module | None = None) -> None:
    mha = getattr(torch.backends, "mha", None)
    if mha is not None and hasattr(mha, "set_fastpath_enabled"):
        mha.set_fastpath_enabled(False)
    if model is not None:
        enc = getattr(model, "transformer_encoder", None)
        for attr in ("enable_nested_tensor", "use_nested_tensor"):
            if enc is not None and hasattr(enc, attr):
                setattr(enc, attr, False)


class BottleneckAdapter(nn.Module):
    def __init__(self, d_model: int, bottleneck: int = 64, dropout: float = 0.1):
        super().__init__()
        self.norm = nn.LayerNorm(d_model)
        self.down = nn.Linear(d_model, bottleneck)
        self.act = nn.GELU()
        self.drop = nn.Dropout(dropout)
        self.up = nn.Linear(bottleneck, d_model)
        nn.init.zeros_(self.up.weight)
        nn.init.zeros_(self.up.bias)

    def forward(self, h: torch.Tensor) -> torch.Tensor:
        return h + self.up(self.drop(self.act(self.down(self.norm(h)))))


class AdapterSet(nn.Module):
    """One adapter per transformer layer, attached to a model via forward hooks."""

    def __init__(self, d_model: int, n_layers: int, bottleneck: int = 64, dropout: float = 0.1):
        super().__init__()
        self.config = dict(d_model=d_model, n_layers=n_layers, bottleneck=bottleneck, dropout=dropout)
        self.adapters = nn.ModuleList([BottleneckAdapter(d_model, bottleneck, dropout) for _ in range(n_layers)])
        self._handles: list = []
        self.enabled = True

    def attach(self, model: nn.Module) -> "AdapterSet":
        layers = model.transformer_encoder.layers
        if len(layers) != len(self.adapters):
            raise ValueError(f"model has {len(layers)} layers, adapter set has {len(self.adapters)}")
        self.detach()
        disable_transformer_fastpath(model)
        for layer, ad in zip(layers, self.adapters):
            self._handles.append(layer.register_forward_hook(self._make_hook(ad)))
        return self

    def _make_hook(self, ad: BottleneckAdapter):
        def hook(module, inputs, output):
            if not self.enabled:
                return output
            if not isinstance(output, torch.Tensor) or getattr(output, "is_nested", False):
                raise RuntimeError("adapter received a nested/non-tensor output: transformer fast path is still on")
            if ad.training != module.training:   # adapters are not children of the model: follow its train/eval mode
                ad.train(module.training)
            return ad(output)
        return hook

    def detach(self) -> None:
        for h in self._handles:
            h.remove()
        self._handles = []

    def n_params(self) -> int:
        return sum(p.numel() for p in self.parameters())

    def save(self, path: str | Path, extra: dict | None = None) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"config": self.config, "state_dict": self.state_dict(), "extra": extra or {}}, path)

    @classmethod
    def load(cls, path: str | Path, map_location="cpu") -> "AdapterSet":
        ck = torch.load(path, map_location=map_location, weights_only=False)
        ad = cls(**ck["config"])
        ad.load_state_dict(ck["state_dict"])
        ad.extra = ck.get("extra", {})
        return ad


def freeze(module: nn.Module) -> None:
    for p in module.parameters():
        p.requires_grad_(False)


def attach_new_adapters(model: nn.Module, bottleneck: int = 64, dropout: float = 0.1) -> AdapterSet:
    """Freeze the backbone, create a zero-initialised adapter set on the model's device and attach it."""
    freeze(model)
    d = model.transformer_encoder.layers[0].linear1.in_features
    n = len(model.transformer_encoder.layers)
    dev = next(model.parameters()).device
    ad = AdapterSet(d, n, bottleneck, dropout).to(dev)
    return ad.attach(model)
