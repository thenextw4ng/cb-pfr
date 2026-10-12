#!/usr/bin/env python3
"""Extract OpenMC batch-wise k-generation and Shannon-entropy convergence diagnostics.

The script deliberately reports diagnostics rather than automatically certifying
source convergence: thresholds must be justified and traces reviewed.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def slope_per_1000(values: list[float]) -> float:
    """Ordinary least-squares slope against batch index, scaled per 1000 batches."""
    n = len(values)
    if n < 2:
        return 0.0
    xbar = (n - 1) / 2.0
    ybar = mean(values)
    denominator = sum((i - xbar) ** 2 for i in range(n))
    slope = sum((i - xbar) * (value - ybar) for i, value in enumerate(values)) / denominator
    return slope * 1000.0


def summarize_trace(values: list[float], inactive: int, *, label: str) -> dict:
    if not values or not all(math.isfinite(v) for v in values):
        raise ValueError(f"{label} trace must contain finite values")
    if inactive < 0 or inactive >= len(values):
        raise ValueError(f"inactive batch count {inactive} is incompatible with {label} trace length {len(values)}")
    active = values[inactive:]
    if len(active) < 4:
        raise ValueError(f"need at least four active values for {label} diagnostics")
    quarter = max(1, len(active) // 4)
    first_quarter = active[:quarter]
    last_quarter = active[-quarter:]
    half = len(active) // 2
    first_half = active[:half]
    second_half = active[half:]
    return {
        "trace_length": len(values),
        "active_trace_length": len(active),
        "active_mean": mean(active),
        "active_min": min(active),
        "active_max": max(active),
        "first_quarter_mean": mean(first_quarter),
        "last_quarter_mean": mean(last_quarter),
        "last_minus_first_quarter_mean": mean(last_quarter) - mean(first_quarter),
        "ols_slope_per_1000_active_batches": slope_per_1000(active),
        "first_half_mean": mean(first_half),
        "second_half_mean": mean(second_half),
        "second_minus_first_half_mean": mean(second_half) - mean(first_half),
    }


def summarize_inactive(values: list[float], inactive: int, *, label: str) -> dict:
    """Summarize the pre-tally interval separately; do not discard it."""
    segment = values[:inactive]
    if not segment:
        return {"status": "NO_INACTIVE_BATCHES", "trace_length": 0}
    if not all(math.isfinite(v) for v in segment):
        raise ValueError(f"{label} inactive trace must contain finite values")
    quarter = max(1, len(segment) // 4)
    half = max(1, len(segment) // 2)
    first_quarter = segment[:quarter]
    last_quarter = segment[-quarter:]
    first_half = segment[:half]
    second_half = segment[half:] or segment[-1:]
    return {
        "status": "DESCRIPTIVE_ONLY",
        "trace_length": len(segment),
        "mean": mean(segment),
        "first_quarter_mean": mean(first_quarter),
        "last_quarter_mean": mean(last_quarter),
        "last_minus_first_quarter_mean": mean(last_quarter) - mean(first_quarter),
        "first_half_mean": mean(first_half),
        "second_half_mean": mean(second_half),
        "second_minus_first_half_mean": mean(second_half) - mean(first_half),
        "ols_slope_per_1000_inactive_batches": slope_per_1000(segment),
    }


def analyze_traces(k_generation: list[float], entropy: list[float], inactive: int,
                   n_batches: int | None = None) -> dict:
    if not k_generation:
        raise ValueError("statepoint has no k_generation trace")
    if not entropy:
        return {
            "schema_version": "1.1",
            "status": "FAIL_MISSING_ENTROPY_TRACE",
            "inactive_batches": inactive,
            "inactive_k_generation": summarize_inactive(k_generation, inactive, label="k_generation"),
            "inactive_entropy": None,
            "k_generation": summarize_trace(k_generation, inactive, label="k_generation"),
            "entropy": None,
            "automatic_convergence_claim": False,
            "interpretation": "The statepoint has no Shannon-entropy trace; source convergence is not assessed.",
        }
    k = summarize_trace(k_generation, inactive, label="k_generation")
    h = summarize_trace(entropy, inactive, label="entropy")
    k_half_delta_pcm = h.get("second_minus_first_half_mean")  # overwritten below for clarity
    k_active = k_generation[inactive:]
    k_half = len(k_active) // 2
    k_half_delta_pcm = (mean(k_active[k_half:]) - mean(k_active[:k_half])) * 1e5
    return {
        "schema_version": "1.1",
        "status": "DIAGNOSTIC_REVIEW_REQUIRED",
        "n_batches_metadata": n_batches,
        "inactive_batches": inactive,
        "inactive_k_generation": summarize_inactive(k_generation, inactive, label="k_generation"),
        "inactive_entropy": summarize_inactive(entropy, inactive, label="entropy"),
        "k_generation": k,
        "entropy": h,
        "k_generation_second_minus_first_half_pcm": k_half_delta_pcm,
        "automatic_convergence_claim": False,
        "interpretation": (
            "These are descriptive source/eigenvalue convergence diagnostics. Review the inactive-interval "
            "entropy before active tally accumulation and inspect the full active traces against declared "
            "tolerances; a flat scalar mean or small window difference alone does not prove source convergence."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--statepoint", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-csv", type=Path, required=True)
    args = parser.parse_args()
    if args.out_json.exists() or args.out_csv.exists():
        parser.error("refusing to overwrite existing output files")
    try:
        import openmc  # type: ignore
        with openmc.StatePoint(args.statepoint) as sp:
            k = [float(v) for v in sp.k_generation]
            h = [float(v) for v in sp.entropy] if sp.entropy is not None else []
            report = analyze_traces(k, h, int(sp.n_inactive), int(sp.n_batches))
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_csv.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
        with args.out_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["batch_index_1based", "active", "k_generation", "shannon_entropy"])
            for i in range(max(len(k), len(h))):
                writer.writerow([i + 1, i >= int(report["inactive_batches"]),
                                 k[i] if i < len(k) else "",
                                 h[i] if i < len(h) else ""])
    except (OSError, ValueError, KeyError, ImportError) as exc:
        parser.error(str(exc))
    print(json.dumps({"status": report["status"], "statepoint": str(args.statepoint),
                      "out_json": str(args.out_json), "out_csv": str(args.out_csv)}, indent=2))
    return 0 if report["status"] == "DIAGNOSTIC_REVIEW_REQUIRED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
