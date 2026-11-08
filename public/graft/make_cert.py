"""Build examples/phenoage.gcert.json from the run's records (delta file, held-out results, replication result)."""
import json, re, collections, hashlib, torch
torch.set_num_threads(1)
S = "/tmp/claude-0/-home-user/920fe012-e383-5e78-b2e1-3d227e5fa950/scratchpad"
F = f"{S}/isa_phenoage/final"
d = torch.load(f"{F}/colab/delta/weight_delta_vs_unedited.pt", map_location="cpu")
per_layer, per_kind, per_tensor = collections.Counter(), collections.Counter(), {}
h = hashlib.sha256()
for k in sorted(d):
    idx, val = d[k]; n = val.numel()
    per_tensor[k] = n; per_layer[int(re.search(r"layers\.(\d+)", k).group(1))] += n; per_kind[k.split(".")[-2]] += n
    h.update(k.encode()); h.update(val.to(torch.float32).numpy().tobytes())
HR = json.load(open(f"{F}/heldout_results.json")); RP = json.load(open(f"{F}/replicate/replication_result.json"))
recorded = open(f"{F}/colab/delta/DELTA_SHA256.txt").read().split()[0]
cert = {
  "graft_cert_version": "0.1",
  "program": "phenoage", "source": "phenoage.graft.yaml", "edit_id": "E3 (sandbox snapshot 1108-125512_evaluate3)",
  "target": {"model": "insilicomedicine/Qwen3-0.6B-Longevity", "weights_sha256": "f547df5c82226b524fc44748876685000f34208efe80aeef8f8eb7238b5a5cce",
             "arch_class": "pre-norm decoder; RMSNorm; SiLU-gated MLP; RoPE GQA attention", "d_model": 1024, "layers": 28, "mlp_width": 3072},
  "delta": {"format": "gdelta-v0.1: {tensor_name: (int32 [n,2] indices, fp32 [n] new values)}", "file": "weight_delta_vs_unedited.pt",
            "sha256_rule": "sha256 over tensor names in sorted order; for each, name bytes then fp32 bytes of the new values",
            "sha256": h.hexdigest(), "sha256_recorded_in_run": recorded, "sha256_match": h.hexdigest() == recorded,
            "changed_scalars": sum(per_tensor.values()), "fraction_of_model": "0.26%", "tensors": len(per_tensor),
            "by_layer": {str(k): v for k, v in sorted(per_layer.items())}, "by_kind": dict(per_kind)},
  "resources": {"replaced_mlp_neurons": {"L3": 6, "L4": 2, "L6": 26, "L7": 28, "L9": 30, "L10": 30, "L11": 12, "L12": 8, "L13": 24, "total": 166},
                "attention_switches_additive": ["L4 kv-group 3 (flag)", "L9 q-heads 0-4 / kv-groups 0-2 (shift)", "L12 q-head 0 / kv-group 0 (sum)"],
                "value_channels_taken": ["L4 g3 ch89", "L12 g0 ch14"]},
  "undo": {"method": "write back the original values at the recorded indices (Registry.restore)", "exact": True},
  "side_effects": {"suite": "graft-probes-165 (105 multiple-choice, 40 LB-0038 age, 20 chat)",
                   "suite_reference_sha256": "aa23334ac8cda335b79b844cf7e18c30a804c4b217830918b65c3c0b90caeb59",
                   "rule": "max KL <= 0.5 and <= 1 top-1 change among probes with top1-top2 gap >= 0.15 nats",
                   "max_kl": 0.358, "confident_flips": 0, "near_tie_flips": 5, "mc_accuracy": {"original": "61/105", "edited": "63/105"},
                   "pass": True, "strict_rule_pass": False,
                   "independent_recheck": "rebuilt from recipe outside the sandbox: max KL 0.3583, 0 confident flips"},
  "contracts": {
    "program": {"claim": "PhenoAge answer within the pre-registered bar", "split": "held-out, n = %d, scored once" % HR["n"],
                "metric": "MAE (years)", "bound": HR["pre_registered_bar"], "measured": round(HR["mae"], 3),
                "ci95": [round(x, 3) for x in HR["mae_ci"]], "pass": HR["meets_bar"],
                "comparators": {"original_model": round(HR["vs_unedited_llm"]["baseline_mae"], 2),
                                "gbm_750_labels": round(HR["vs_gbm750"]["baseline_mae"], 2), "copy_stated_age": round(HR["vs_copy_age"]["baseline_mae"], 2)}},
    "instructions": "per-instruction contracts and measured values: see phenoage.graft.yaml"},
  "reproduction": {"recipe": "isa/ library + phenoage_program.py + 44 fitted vector files", "rebuilt_sha256": RP["sha256"], "match": RP["match"]},
  "conformance": {"G0_reversible": True, "G1_contracted": True, "G2_certified": True, "G3_reproducible": True, "level": "G3",
                  "note": "conformance says the claims are recorded and checkable; it does not say the program met its target (it missed 1.5 by 0.024)"}}
json.dump(cert, open(f"{S}/isa_phenoage/writeup/graft_spec/examples/phenoage.gcert.json", "w"), indent=1)
print(h.hexdigest(), cert["delta"]["sha256_match"], cert["delta"]["changed_scalars"], cert["delta"]["by_layer"], cert["delta"]["by_kind"])
