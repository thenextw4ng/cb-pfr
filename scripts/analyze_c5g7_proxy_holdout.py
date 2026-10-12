#!/usr/bin/env python3
"""Exploratory leave-one-round-out audit of C5G7 fission-rate proxy ranking.

This is a descriptive stability check, not a physical acceptance test or a test
of CB-PFR superiority. It deliberately does not set or infer physical thresholds.
"""
from __future__ import annotations
import argparse, csv, json, math
from pathlib import Path

EXPECTED = {"MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM"}
REQUIRED = {"round", "layout_signature", "seed", "fission_rate_peaking_factor",
            "statepoint_sha256", "mgxs_sha256", "group_structure_audit",
            "batches", "inactive", "particles_per_batch", "threads"}

def analyze(path: Path) -> dict:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"missing required columns: {sorted(missing)}")
        rows = list(reader)
    if len(rows) != 18:
        raise ValueError(f"expected exactly 18 rows, got {len(rows)}")
    if {r["layout_signature"] for r in rows} != EXPECTED:
        raise ValueError("expected the six declared layouts")
    rounds = sorted({int(r["round"]) for r in rows})
    if len(rounds) != 3:
        raise ValueError(f"expected three seed rounds, got {rounds}")
    if len({r["statepoint_sha256"] for r in rows}) != 18:
        raise ValueError("statepoint hashes are not unique")
    if len({r["seed"] for r in rows}) != 18:
        raise ValueError("seed values are not unique")
    if len({r["mgxs_sha256"] for r in rows}) != 1:
        raise ValueError("MGXS hashes differ")
    settings = {(r["batches"], r["inactive"], r["particles_per_batch"], r["threads"]) for r in rows}
    if len(settings) != 1:
        raise ValueError("run settings differ")
    if any(r["group_structure_audit"] != "PASS" for r in rows):
        raise ValueError("group structure audit did not pass")
    values = {}
    for r in rows:
        value = float(r["fission_rate_peaking_factor"])
        if not math.isfinite(value) or value <= 0:
            raise ValueError("proxy values must be finite and positive")
        values[(int(r["round"]), r["layout_signature"])] = value
    folds = []
    for held in rounds:
        train = {layout: sum(values[(rnd, layout)] for rnd in rounds if rnd != held) / 2 for layout in EXPECTED}
        test = {layout: values[(held, layout)] for layout in EXPECTED}
        chosen, best = min(train, key=train.get), min(test, key=test.get)
        folds.append({
            "held_out_round": held,
            "training_rounds": [x for x in rounds if x != held],
            "selected_by_training_mean_proxy": chosen,
            "held_out_proxy_for_selected": test[chosen],
            "held_out_best_proxy_layout": best,
            "held_out_best_proxy": test[best],
            "descriptive_regret": test[chosen] - test[best],
            "selected_matches_held_out_proxy_minimum": chosen == best,
        })
    return {
        "schema_version": "cbpfr.c5g7-proxy-holdout.v1",
        "input_csv": str(path),
        "method": "Leave one seed round out; select by mean proxy in two rounds and evaluate in held-out round.",
        "checks": {"exactly_18_runs": True, "six_layouts": True, "three_rounds": True,
                   "unique_seeds": True, "unique_statepoint_hashes": True, "single_mgxs_hash": True,
                   "common_settings": True, "group_structure_pass": True},
        "folds": folds,
        "all_folds_same_selected_layout": len({f["selected_by_training_mean_proxy"] for f in folds}) == 1,
        "all_selected_match_heldout_proxy_minimum": all(f["selected_matches_held_out_proxy_minimum"] for f in folds),
        "interpretation": "Descriptive ranking stability for this proxy and six-layout sample only. The same proxy is used for selection and evaluation; only three rounds exist. This is not an independent physical truth test, not CB-PFR superiority evidence, and not physical validation."
    }

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    if a.out.exists():
        p.error(f"refusing to overwrite existing output: {a.out}")
    report = analyze(a.input)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "DESCRIPTIVE_ONLY", "folds": len(report["folds"]),
                      "selected_layouts": [f["selected_by_training_mean_proxy"] for f in report["folds"]],
                      "out": str(a.out)}, indent=2))

if __name__ == "__main__":
    main()
