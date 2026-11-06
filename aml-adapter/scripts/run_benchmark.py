#!/usr/bin/env python
"""Run the AML adapter benchmark.

  python scripts/run_benchmark.py --profile full --data-root data --out results/full          # GPU (Colab)
  python scripts/run_benchmark.py --profile cpu-mini --data-root data --out results/mini      # CPU pipeline check
  python scripts/run_benchmark.py --profile smoke --out results/smoke                         # synthetic, ~2 min
"""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from amladapter.benchmark import Benchmark, make_config
from amladapter.backbone import download_scgpt, write_tiny_checkpoint


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="full", choices=["smoke", "cpu-mini", "full"])
    ap.add_argument("--data-root", default="data")
    ap.add_argument("--scgpt-dir", default="models/scGPT-human")
    ap.add_argument("--out", default=None)
    ap.add_argument("--tasks", default="T1,T2,T3")
    ap.add_argument("--set", nargs="*", default=[], help="config overrides, e.g. ssl_steps=500 device=cpu")
    a = ap.parse_args()
    over = {}
    for kv in a.set:
        k, v = kv.split("=", 1)
        try:
            over[k] = json.loads(v)
        except json.JSONDecodeError:
            over[k] = v
    out = a.out or f"results/{a.profile}"
    if a.profile == "smoke":
        from amladapter.data import make_synthetic_cohorts
        vg, nd = make_synthetic_cohorts()
        scgpt_dir = write_tiny_checkpoint(Path(out) / "tiny_scgpt", vg.var_names)
    else:
        from amladapter.data import load_naldini, load_vangalen
        vg = load_vangalen(a.data_root)
        nd = load_naldini(a.data_root) if "T2" in a.tasks else None
        scgpt_dir = download_scgpt(a.scgpt_dir)
    cfg = make_config(a.profile, out_dir=out, scgpt_dir=str(scgpt_dir), tasks=tuple(a.tasks.split(",")), **over)
    Benchmark(cfg, vg, nd).run()


if __name__ == "__main__":
    main()
