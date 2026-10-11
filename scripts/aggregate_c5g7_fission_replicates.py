#!/usr/bin/env python3
"""Aggregate assembly-fission metrics across independent OpenMC statepoints.

This estimates between-seed variability of per-run nonlinear metrics. It does
not infer covariance between mesh bins from one statepoint, and it does not
replace OpenMC's within-run tally uncertainty or model/data uncertainty.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, stdev
from typing import Any, Sequence


class ReplicateAggregationError(ValueError):
    """Invalid or insufficient independent replicate evidence."""


def _finite_number(value: Any, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ReplicateAggregationError(f"{label} must be numeric") from exc
    if not math.isfinite(result):
        raise ReplicateAggregationError(f"{label} must be finite")
    return result


def aggregate_reports(reports: Sequence[dict[str, Any]]) -> dict[str, Any]:
    if len(reports) < 2:
        raise ReplicateAggregationError("at least two independent statepoint reports are required")
    candidate_ids = {r.get("candidate_id") for r in reports}
    layouts = {r.get("layout_signature") for r in reports}
    if len(candidate_ids) != 1 or None in candidate_ids:
        raise ReplicateAggregationError("all reports must have the same non-empty candidate_id")
    if len(layouts) != 1 or None in layouts:
        raise ReplicateAggregationError("all reports must have the same non-empty layout_signature")

    seeds = [r.get("seed") for r in reports]
    if any(isinstance(seed, bool) or not isinstance(seed, int) for seed in seeds):
        raise ReplicateAggregationError("every report must include an integer seed from its statepoint")
    if len(set(seeds)) != len(seeds):
        raise ReplicateAggregationError("replicate seeds must be unique")
    hashes = [r.get("statepoint_sha256") for r in reports]
    if any(not isinstance(h, str) or len(h) != 64 for h in hashes):
        raise ReplicateAggregationError("every report must include a 64-character statepoint_sha256")
    if len(set(hashes)) != len(hashes):
        raise ReplicateAggregationError("replicate statepoint hashes must be unique")

    scalar_names = ("fission_rate_peaking_factor", "keff_mean")
    scalar_results: dict[str, dict[str, float]] = {}
    for name in scalar_names:
        values = [_finite_number(r.get(name), f"{name} in report {i}") for i, r in enumerate(reports)]
        if name == "fission_rate_peaking_factor" and any(v <= 0 for v in values):
            raise ReplicateAggregationError("peaking factors must be positive")
        scalar_results[name] = {
            "mean": mean(values),
            "between_seed_sample_sd": stdev(values),
            "standard_error_of_replicate_mean": stdev(values) / math.sqrt(len(values)),
            "replicate_values": values,
        }

    position_order = reports[0].get("positions_order")
    if not isinstance(position_order, list) or not position_order:
        raise ReplicateAggregationError("positions_order is required for assembly aggregation")
    assembly_by_position: dict[str, dict[str, float]] = {}
    for position in position_order:
        values = []
        for i, report in enumerate(reports):
            rates = report.get("assembly_integrated_fission_rate")
            if not isinstance(rates, dict) or position not in rates:
                raise ReplicateAggregationError(f"report {i} lacks assembly rate for {position}")
            value = _finite_number(rates[position], f"assembly rate {position} in report {i}")
            if value <= 0:
                raise ReplicateAggregationError(f"assembly rate {position} must be positive")
            values.append(value)
        assembly_by_position[position] = {
            "mean": mean(values),
            "between_seed_sample_sd": stdev(values),
            "standard_error_of_replicate_mean": stdev(values) / math.sqrt(len(values)),
        }

    return {
        "schema_version": "1.0",
        "status": "REPLICATE_UNCERTAINTY_ESTIMATED",
        "candidate_id": next(iter(candidate_ids)),
        "layout_signature": next(iter(layouts)),
        "replicate_count": len(reports),
        "seeds": seeds,
        "statepoint_sha256": hashes,
        "keff": scalar_results["keff_mean"],
        "fission_rate_peaking_factor": scalar_results["fission_rate_peaking_factor"],
        "assembly_integrated_fission_rate": assembly_by_position,
        "uncertainty_interpretation": (
            "Between-seed sample SD and standard error of the replicate mean. Each nonlinear "
            "peaking factor is calculated within one statepoint before aggregation, preserving "
            "within-statepoint bin dependence. This does not include nuclear-data/model bias and "
            "does not replace the per-statepoint tally uncertainty."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", nargs="+", required=True, type=Path,
                        help="per-statepoint assembly_fission.json reports from distinct seeds")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite existing output: {args.out}")
    try:
        reports = [json.loads(path.read_text(encoding="utf-8")) for path in args.inputs]
        result = aggregate_reports(reports)
    except (OSError, json.JSONDecodeError, ReplicateAggregationError) as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "candidate_id", "replicate_count", "seeds")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
