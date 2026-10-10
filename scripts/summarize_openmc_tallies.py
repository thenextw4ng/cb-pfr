#!/usr/bin/env python3
"""Summarize spatial OpenMC tally means and Monte Carlo uncertainties."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np


def _stats(values: np.ndarray) -> dict:
    finite = values[np.isfinite(values)]
    if not finite.size:
        return {"n": int(values.size), "n_finite": 0}
    return {
        "n": int(values.size),
        "n_finite": int(finite.size),
        "min": float(np.min(finite)),
        "q25": float(np.percentile(finite, 25)),
        "median": float(np.median(finite)),
        "mean": float(np.mean(finite)),
        "q75": float(np.percentile(finite, 75)),
        "q95": float(np.percentile(finite, 95)),
        "q99": float(np.percentile(finite, 99)),
        "max": float(np.max(finite)),
        "n_zero": int(np.count_nonzero(finite == 0.0)),
        "n_positive": int(np.count_nonzero(finite > 0.0)),
        "n_negative": int(np.count_nonzero(finite < 0.0)),
    }


def summarize(audit: dict, rows: list[dict]) -> dict:
    grouped: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        key = (str(row["tally_index"]), str(row["score_name_assuming_score_last"]))
        grouped.setdefault(key, []).append(row)

    tallies = []
    for (tally_index, score), group in sorted(grouped.items(), key=lambda item: (int(item[0][0]), item[0][1])):
        means = np.asarray([float(row["mean"]) for row in group], dtype=float)
        sds = np.asarray([float(row["std_dev"]) for row in group], dtype=float)
        positive = np.isfinite(means) & (means > 0.0) & np.isfinite(sds) & (sds >= 0.0)
        relative = sds[positive] / means[positive]
        tallies.append({
            "tally_index": int(tally_index),
            "tally_id": group[0].get("tally_id"),
            "tally_name": group[0].get("tally_name"),
            "score": score,
            "mean_statistics": _stats(means),
            "std_dev_statistics": _stats(sds),
            "relative_std_dev_on_positive_means": _stats(relative),
            "interpretation_note": (
                "Relative standard deviations are descriptive Monte Carlo uncertainty ratios; "
                "they are not uncertainty in absolute reactor power or a benchmark-validation metric."
            ),
        })

    keff = audit.get("keff") or {}
    mean = keff.get("mean")
    sd = keff.get("std_dev")
    rel = float(sd) / abs(float(mean)) if mean is not None and sd is not None and float(mean) != 0 else None
    return {
        "schema_version": "1.0",
        "statepoint_path": audit.get("statepoint_path"),
        "statepoint_read_success": audit.get("statepoint_read_success"),
        "openmc_version": audit.get("openmc_version"),
        "run_mode": audit.get("run_mode"),
        "n_batches": audit.get("n_batches"),
        "n_inactive": audit.get("n_inactive"),
        "n_particles": audit.get("n_particles"),
        "n_realizations": audit.get("n_realizations"),
        "keff": {
            "mean": mean,
            "std_dev": sd,
            "relative_std_dev": rel,
            "relative_std_dev_percent": rel * 100.0 if rel is not None else None,
        },
        "tally_count": len(audit.get("tallies", [])),
        "tallies": tallies,
        "limitations": [
            "Mesh-bin indices are retained as indices; no reactor orientation or material identity is inferred.",
            "Zero mesh scores are not assigned to a physical region without a verified geometry map.",
            "Flux/fission/nu-fission scores are not automatically absolute thermal power in watts.",
            "Monte Carlo tally uncertainty is distinct from model bias, nuclear-data uncertainty, and benchmark validation.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-json", required=True, type=Path)
    parser.add_argument("--tally-csv", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"output already exists: {args.out}")
    try:
        audit = json.loads(args.audit_json.read_text(encoding="utf-8"))
        with args.tally_csv.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if not audit.get("statepoint_read_success"):
            raise ValueError("statepoint audit does not report a successful read")
        if not rows:
            raise ValueError("tally CSV contains no rows")
        result = summarize(audit, rows)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "output": str(args.out),
        "keff": result["keff"],
        "tally_count": result["tally_count"],
        "score_groups": len(result["tallies"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
