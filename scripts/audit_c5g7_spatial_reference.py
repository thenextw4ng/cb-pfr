#!/usr/bin/env python3
"""Audit normalized four-assembly fission-rate shape against published 2-D C5G7 data.

This is a reproducible spatial-shape screen, not absolute-power normalization,
full benchmark acceptance, or reactor-safety validation.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean, stdev

POSITIONS = ("p00", "p01", "p10", "p11")
REFERENCE_POWER = {"p00": 492.8, "p01": 211.7, "p10": 211.7, "p11": 139.8}
REFERENCE_RELATIVE_UNCERTAINTY_PERCENT = {
    "p00": 0.10,
    "p01": 0.18,
    "p10": 0.18,
    "p11": 0.20,
}
EXPECTED_MATERIALS = {"p00": "UO2", "p01": "MOX", "p10": "MOX", "p11": "UO2"}


class SpatialReferenceAuditError(ValueError):
    """Raised when the inputs do not satisfy the spatial-reference contract."""


def _validate_run(payload: dict, source: str) -> dict[str, float]:
    if payload.get("candidate_id") != "c5g7-2x2-UMMU":
        raise SpatialReferenceAuditError(f"{source}: expected canonical candidate c5g7-2x2-UMMU")
    if payload.get("layout_signature") != "UMMU":
        raise SpatialReferenceAuditError(f"{source}: expected UMMU layout signature")
    if payload.get("score") != "fission":
        raise SpatialReferenceAuditError(f"{source}: only the recorded fission score is accepted")
    if payload.get("positions_order") != list(POSITIONS):
        raise SpatialReferenceAuditError(f"{source}: position order must be {list(POSITIONS)}")
    if payload.get("material_by_position") != EXPECTED_MATERIALS:
        raise SpatialReferenceAuditError(f"{source}: material-to-position mapping does not match UMMU contract")
    if payload.get("mesh_dimension") != [51, 51, 1]:
        raise SpatialReferenceAuditError(f"{source}: expected a 51x51x1 mesh")
    rates = payload.get("assembly_integrated_fission_rate")
    if not isinstance(rates, dict) or set(rates) != set(POSITIONS):
        raise SpatialReferenceAuditError(f"{source}: integrated fission rates must exist for all four positions")
    result: dict[str, float] = {}
    for position in POSITIONS:
        value = rates[position]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise SpatialReferenceAuditError(f"{source}: {position} fission rate must be finite and positive")
        result[position] = float(value)
    return result


def audit_spatial_reference(payloads: list[dict], sources: list[str] | None = None) -> dict:
    if len(payloads) < 3:
        raise SpatialReferenceAuditError("at least three independent run-level tally records are required")
    sources = sources or [f"run_{i + 1}" for i in range(len(payloads))]
    if len(sources) != len(payloads):
        raise SpatialReferenceAuditError("source labels and run payloads must have matching lengths")
    rates_by_run = [_validate_run(payload, source) for payload, source in zip(payloads, sources)]

    # Average the run-level integrated rates first, then normalize across the
    # four fuel assemblies, matching the comparison documented in the A-G report.
    mean_rates = {p: mean(run[p] for run in rates_by_run) for p in POSITIONS}
    total_mean_rate = sum(mean_rates.values())
    observed = {p: mean_rates[p] / total_mean_rate for p in POSITIONS}
    total_reference = sum(REFERENCE_POWER.values())
    reference = {p: REFERENCE_POWER[p] / total_reference for p in POSITIONS}

    per_position = {}
    for p in POSITIONS:
        per_run_fraction = [run[p] / sum(run.values()) for run in rates_by_run]
        relative_difference = (observed[p] / reference[p] - 1.0) * 100.0
        reference_uncertainty = REFERENCE_RELATIVE_UNCERTAINTY_PERCENT[p]
        per_position[p] = {
            "material": EXPECTED_MATERIALS[p],
            "mean_integrated_fission_rate": mean_rates[p],
            "observed_normalized_fraction": observed[p],
            "reference_normalized_fraction": reference[p],
            "relative_difference_percent": relative_difference,
            "published_reference_relative_uncertainty_percent": reference_uncertainty,
            "within_published_reference_uncertainty": abs(relative_difference) <= reference_uncertainty,
            "between_run_fraction_sd": stdev(per_run_fraction),
            "between_run_fraction_standard_error": stdev(per_run_fraction) / math.sqrt(len(per_run_fraction)),
        }
    passed = all(item["within_published_reference_uncertainty"] for item in per_position.values())
    return {
        "schema_version": "1.0",
        "status": "NORMALIZED_SPATIAL_SHAPE_SCREEN_PASS" if passed else "NORMALIZED_SPATIAL_SHAPE_SCREEN_FAIL",
        "run_count": len(payloads),
        "candidate_id": "c5g7-2x2-UMMU",
        "layout_signature": "UMMU",
        "score": "fission",
        "reference": {
            "source": "Song et al., Frontiers in Energy Research (2020), Table 1",
            "url": "https://doi.org/10.3389/fenrg.2020.00124",
            "assembly_power_values": REFERENCE_POWER,
            "relative_uncertainty_percent": REFERENCE_RELATIVE_UNCERTAINTY_PERCENT,
            "position_mapping": {
                "p00": "inner UO2 assembly",
                "p01": "MOX assembly",
                "p10": "MOX assembly",
                "p11": "outer UO2 assembly",
            },
        },
        "maximum_absolute_relative_difference_percent": max(abs(x["relative_difference_percent"]) for x in per_position.values()),
        "positions": per_position,
        "interpretation": (
            "Normalized assembly fission-rate fractions are compared with published normalized C5G7 assembly-power fractions. "
            "This is a spatial-shape screen only; the fission tally is not absolute power in watts."
        ),
        "nonclaims": [
            "not absolute power normalization in watts",
            "not flux validation",
            "not official OECD/NEA benchmark acceptance",
            "not source-convergence certification",
            "not reactor-safety certification",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-json", action="append", required=True, type=Path,
                        help="run-level assembly_fission.json; repeat at least three times")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite existing output: {args.out}")
    try:
        payloads = [json.loads(path.read_text(encoding="utf-8")) for path in args.run_json]
        report = audit_spatial_reference(payloads, [str(path) for path in args.run_json])
    except (OSError, json.JSONDecodeError, SpatialReferenceAuditError) as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "maximum_absolute_relative_difference_percent": report["maximum_absolute_relative_difference_percent"],
        "out": str(args.out),
    }, indent=2))
    return 0 if report["status"] == "NORMALIZED_SPATIAL_SHAPE_SCREEN_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
