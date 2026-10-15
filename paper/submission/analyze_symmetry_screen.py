#!/usr/bin/env python3
"""Reproduce the exploratory class-level CB-PFR table and threshold-sensitivity counts.

The default limits are retrospective illustrative settings used only to reproduce
the paper's descriptive workflow. They are not engineering or safety criteria.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path

CLASSES = {
    "S1": ["MMUU", "MUMU"],
    "S2": ["MUUM"],
    "S3": ["UMMU"],
    "S4": ["UMUM", "UUMM"],
}
EXPECTED = {layout for layouts in CLASSES.values() for layout in layouts}
REQUIRED = {
    "layout_signature", "keff_mean", "keff_std_dev",
    "fission_rate_peaking_factor",
}

def read_rows(path: Path) -> list[dict[str, float | str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing columns: {sorted(missing)}")
        rows = list(reader)
    if not rows:
        raise ValueError("input CSV is empty")
    grouped = {layout: [] for layout in EXPECTED}
    for row in rows:
        layout = row["layout_signature"].strip()
        if layout not in EXPECTED:
            raise ValueError(f"unexpected layout label: {layout}")
        item = {
            "layout_signature": layout,
            "k": float(row["keff_mean"]),
            "k_sd": float(row["keff_std_dev"]),
            "F": float(row["fission_rate_peaking_factor"]),
        }
        if not all(value == value and abs(value) != float("inf")
                   for key, value in item.items() if key != "layout_signature"):
            raise ValueError(f"non-finite metric in layout {layout}")
        grouped[layout].append(item)
    if any(not grouped[layout] for layout in EXPECTED):
        raise ValueError("input must contain all six layout labels")
    if any(len(grouped[layout]) != 3 for layout in EXPECTED):
        raise ValueError("expected three independent run records per layout label")
    return rows

def summarize(rows: list[dict[str, str]]) -> dict:
    by_layout = {layout: [] for layout in EXPECTED}
    parsed = []
    for row in rows:
        layout = row["layout_signature"].strip()
        item = {
            "layout_signature": layout,
            "k": float(row["keff_mean"]),
            "k_sd": float(row["keff_std_dev"]),
            "F": float(row["fission_rate_peaking_factor"]),
        }
        by_layout[layout].append(item)
        parsed.append(item)
    classes = []
    for name, layouts in CLASSES.items():
        observations = [item for layout in layouts for item in by_layout[layout]]
        k_values = [item["k"] for item in observations]
        within_sd = [item["k_sd"] for item in observations]
        f_values = [item["F"] for item in observations]
        classes.append({
            "class": name,
            "layouts": layouts,
            "n": len(observations),
            "mean_keff": statistics.mean(k_values),
            "s_k_run": statistics.stdev(k_values),
            "mean_within_run_keff_sd": statistics.mean(within_sd),
            "s_k_star": max(statistics.stdev(k_values), statistics.mean(within_sd)),
            "mean_F": statistics.mean(f_values),
            "s_F": statistics.stdev(f_values),
        })
    return {"rows": parsed, "classes": classes}

def screen(class_rows: list[dict], *, k_min: float, k_max: float,
           f_max: float, z: float, d_k: float, d_f: float) -> list[dict]:
    out = []
    layout_count = 0
    class_count = 0
    for row in class_rows:
        k_low = row["mean_keff"] - z * row["s_k_star"]
        k_high = row["mean_keff"] + z * row["s_k_star"]
        f_high = row["mean_F"] + z * row["s_F"]
        v_k = (max(0.0, k_min-k_low) + max(0.0, k_high-k_max)) / d_k
        v_f = max(0.0, f_high-f_max) / d_f
        passed = k_low >= k_min and k_high <= k_max and f_high <= f_max
        out.append({
            **row, "B_k_minus": k_low, "B_k_plus": k_high,
            "B_F_plus": f_high, "V_k": v_k, "V_F": v_f,
            "V_total": v_k+v_f, "passes": passed,
        })
        if passed:
            class_count += 1
            layout_count += len(row["layouts"])
    return {"classes": out, "passing_classes": class_count,
            "passing_layout_labels": layout_count}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path,
        default=Path("results/cbpfr_physical_feasibility_bridge_2026-10-12.csv"))
    parser.add_argument("--output", type=Path, default=Path("cbpfr_symmetry_screen.json"))
    parser.add_argument("--k-min", type=float, default=1.14)
    parser.add_argument("--k-max", type=float, default=1.21)
    parser.add_argument("--f-max", type=float, default=1.35)
    parser.add_argument("--z", type=float, default=1.0)
    parser.add_argument("--d-k", type=float, default=0.01)
    parser.add_argument("--d-f", type=float, default=0.1)
    parser.add_argument("--sweep", action="store_true",
        help="also reproduce the retrospective Fmax-by-z sensitivity table")
    args = parser.parse_args()
    for name, value in (("k-min", args.k_min), ("k-max", args.k_max),
                        ("f-max", args.f_max), ("z", args.z),
                        ("d-k", args.d_k), ("d-f", args.d_f)):
        if not (value == value and abs(value) != float("inf")):
            parser.error(f"{name} must be finite")
    if not (0 < args.k_min < args.k_max and args.f_max > 0 and args.z >= 0
            and args.d_k > 0 and args.d_f > 0):
        parser.error("invalid limits, width factor, or normalization scales")
    raw = read_rows(args.input)
    data = summarize(raw)
    main_screen = screen(data["classes"], k_min=args.k_min, k_max=args.k_max,
                         f_max=args.f_max, z=args.z, d_k=args.d_k, d_f=args.d_f)
    result = {
        "interpretation": "Retrospective exploratory screen only; thresholds are not engineering or safety criteria.",
        "limits": {"k_min": args.k_min, "k_max": args.k_max, "F_max": args.f_max,
                   "z": args.z, "d_k": args.d_k, "d_F": args.d_f,
                   "weights": "unit weights"},
        "class_summary": data["classes"],
        "screen": main_screen,
    }
    if args.sweep:
        sweep = []
        for f_max in [1.30, 1.32, 1.35, 1.80, 1.82, 1.87, 1.90]:
            row = {"F_max": f_max}
            for z in [0.0, 1.0, 2.0]:
                assessed = screen(data["classes"], k_min=args.k_min, k_max=args.k_max,
                                  f_max=f_max, z=z, d_k=args.d_k, d_f=args.d_f)
                row[f"z_{int(z)}"] = {
                    "passing_layout_labels": assessed["passing_layout_labels"],
                    "passing_symmetry_classes": assessed["passing_classes"],
                }
            sweep.append(row)
        result["retrospective_sensitivity_sweep"] = sweep
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "main_screen_pass_labels": main_screen["passing_layout_labels"],
        "main_screen_pass_classes": main_screen["passing_classes"],
        "thresholds_are_retrospective": True,
    }, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
