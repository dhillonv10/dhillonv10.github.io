import numpy as np, scipy.sparse as sp, torch, pytest
from amladapter.backbone import write_tiny_checkpoint, load_scgpt, embed, gene_ids_for
from amladapter.adapters import attach_new_adapters, AdapterSet
from amladapter.train import train_ssl, train_supervised, TaskHeads, predict

GENES = [f"G{i:03d}" for i in range(80)]

@pytest.fixture(scope="module")
def tiny(tmp_path_factory):
    d = write_tiny_checkpoint(tmp_path_factory.mktemp("ck"), GENES)
    rng = np.random.default_rng(0)
    X = sp.csr_matrix(rng.poisson(1.0, size=(40, len(GENES))).astype(np.float32))
    return d, X

def _fresh(d):
    m, v, c = load_scgpt(d, pretrained=True, verbose=False)
    return m, v, c, gene_ids_for(GENES, v)

def test_identity_at_init_and_effect_after_change(tiny):
    d, X = tiny
    m, v, c, gid = _fresh(d)
    e0 = embed(m, X, gid, v, c, max_len=64, normalize=False)
    ad = attach_new_adapters(m, bottleneck=8)
    e1 = embed(m, X, gid, v, c, max_len=64, normalize=False)
    assert np.allclose(e0, e1, atol=1e-6), "zero-init adapters must not change outputs"
    with torch.no_grad():
        for a in ad.adapters: a.up.weight.normal_(0, 0.5)
    e2 = embed(m, X, gid, v, c, max_len=64, normalize=False)     # eval + no_grad path
    assert np.abs(e2 - e0).max() > 1e-3, "adapters had no effect in inference mode (fast path bypass?)"
    ad.enabled = False
    e3 = embed(m, X, gid, v, c, max_len=64, normalize=False)
    assert np.allclose(e0, e3, atol=1e-6), "disabling adapters must restore the base model"

def test_only_adapters_train_and_roundtrip(tiny, tmp_path):
    d, X = tiny
    m, v, c, gid = _fresh(d)
    base = {k: t.clone() for k, t in m.state_dict().items()}
    ad = attach_new_adapters(m, bottleneck=8)
    r = train_ssl(m, ad, X, gid, v, c, steps=5, lr=1e-2, batch=4, max_len=64, log_every=0, n_val=8)
    for k, t in m.state_dict().items():
        assert torch.equal(t, base[k]), f"backbone tensor changed: {k}"
    assert any(a.up.weight.abs().sum() > 0 for a in ad.adapters), "adapters did not update"
    ad.save(tmp_path / "a.pt", extra={"x": 1})
    e_before = embed(m, X, gid, v, c, max_len=64)
    ad.detach()
    m2, v2, c2, _ = _fresh(d)
    AdapterSet.load(tmp_path / "a.pt").attach(m2)
    assert np.allclose(e_before, embed(m2, X, gid, v2, c2, max_len=64), atol=1e-5)

def test_supervised_learns_separable_signal(tiny):
    d, _ = tiny
    rng = np.random.default_rng(1)
    lam = np.full(len(GENES), 0.8); n = 120
    y = (rng.random(n) < 0.5).astype(np.float32)
    M = np.stack([rng.poisson(lam * (np.r_[np.full(10, 6.0), np.ones(len(GENES) - 10)] if yi else 1)) for yi in y]).astype(np.float32)
    X = sp.csr_matrix(M)
    m, v, c, gid = _fresh(d)
    ad = attach_new_adapters(m, bottleneck=16)
    heads = TaskHeads(c["embsize"], n_celltypes=2)
    yct = y.astype(int)                      # learnable cell-type labels (random ones would only add noise)
    train_supervised(m, ad, heads, X, gid, v, c, y, yct, steps=200, lr=2e-2, batch=16, max_len=64, log_every=0)
    lm, lc, emb = predict(m, heads, X, gid, v, c, max_len=64)
    from sklearn.metrics import roc_auc_score
    assert lc.shape == (n, 2) and emb.shape == (n, c["embsize"])
    assert roc_auc_score(y, lm) > 0.8
