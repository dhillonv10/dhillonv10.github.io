"""End-to-end: synthetic cohorts + tiny random scGPT through every task, method, metric and the shipped model."""
import numpy as np, pandas as pd
from amladapter.data import make_synthetic_cohorts
from amladapter.backbone import write_tiny_checkpoint
from amladapter.benchmark import Benchmark, make_config
from amladapter.model import AMLAdapterModel


def test_benchmark_end_to_end(tmp_path):
    vg, nd = make_synthetic_cohorts()
    ck = write_tiny_checkpoint(tmp_path / "ck", vg.var_names)
    cfg = make_config("smoke", out_dir=str(tmp_path / "out"), scgpt_dir=str(ck), n_boot=50, task_steps=200)
    tables = Benchmark(cfg, vg, nd, log=lambda *a: None).run()
    for k in ("T1_AUROC", "T2_AUROC", "T3_macroF1", "PROMISE"):
        assert k in tables and len(tables[k])
    variants = set(tables["T2_AUROC"].variant)
    assert {"HVG-LR", "PCA-LR", "scGPT-frozen", "scGPT+SSL", "scGPT+task", "scGPT+SSL+task", "scGPT+SSL(+tgt)", "scGPT+SSL+task(+tgt)"} <= variants
    t1 = tables["T1_AUROC"].set_index("variant").estimate
    assert t1["HVG-LR"] > 0.9                       # synthetic signal is easy for expression baselines
    assert t1["scGPT+task"] > 0.6                   # the end-to-end adapter path learns (not stuck at chance)
    assert (tmp_path / "out" / "REPORT.md").exists() and (tmp_path / "out" / "RECOMMENDED_MODEL.txt").exists()
    m = AMLAdapterModel.load(tmp_path / "out" / "aml_adapter_final.pt", ck)
    df = m.predict(nd[:50])
    assert list(df.columns) == ["malignant_logit", "malignant_prob", "celltype_pred", "celltype_prob"]
    assert len(df) == 50 and df.malignant_prob.between(0, 1).all()
    assert m.embed(nd[:10]).shape == (10, 32)
