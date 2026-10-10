#!/usr/bin/env python3
"""Compare an OpenMC StatePoint API export against a recorded baseline summary.

The comparison is deliberately fail-closed. A match verifies consistency between
two records; it does not validate the benchmark model or the QUBO-to-physics map.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


SCALAR_FIELDS = {
    "n_batches": "n_batches",
    "n_inactive": "n_inactive",
    "n_particles": "n_particles",
    "n_realizations": "n_realizations",
    "run_mode": "run_mode",
    "energy_mode": "energy_mode",
}


def _close(actual: Any, expected: Any, *, rel_tol: float = 1e-8,
           abs_tol: float = 1e-12) -> bool:
    try:
        a, e = float(actual), float(expected)
    except (TypeError, ValueError):
        return False
    return math.isfinite(a) and math.isfinite(e) and math.isclose(
        a, e, rel_tol=rel_tol, abs_tol=abs_tol
    )


def compare_records(audit: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    """Return individual checks and a strict overall status."""
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, actual: Any, expected: Any, detail: str = "") -> None:
        checks.append({
            "name": name,
            "status": "PASS" if passed else "FAIL",
            "actual": actual,
            "expected": expected,
            "detail": detail,
        })

    read_ok = audit.get("statepoint_read_success") is True
    add("statepoint_read_success", read_ok, audit.get("statepoint_read_success"), True)

    for expected_key, audit_key in SCALAR_FIELDS.items():
        expected = baseline.get(expected_key)
        if expected is None:
            add(f"metadata:{expected_key}", False, audit.get(audit_key), None,
                "Baseline field is missing; comparison cannot pass.")
            continue
        actual = audit.get(audit_key)
        if isinstance(expected, (int, float)) and not isinstance(expected, bool):
            passed = _close(actual, expected)
        else:
            passed = actual == expected
        add(f"metadata:{expected_key}", passed, actual, expected)

    expected_keff = baseline.get("keff_mean")
    actual_keff = (audit.get("keff") or {}).get("mean")
    add("keff_mean", _close(actual_keff, expected_keff, rel_tol=1e-10, abs_tol=1e-12),
        actual_keff, expected_keff)

    expected_sd = baseline.get("keff_std_dev")
    actual_sd = (audit.get("keff") or {}).get("std_dev")
    add("keff_std_dev", _close(actual_sd, expected_sd, rel_tol=1e-8, abs_tol=1e-12),
        actual_sd, expected_sd)

    expected_scores = baseline.get("tally_scores")
    expected_mesh = baseline.get("tally_mesh_dimension")
    matching_tally = None
    if isinstance(audit.get("tallies"), list):
        for tally in audit["tallies"]:
            scores = tally.get("scores", [])
            filters = tally.get("filters", [])
            mesh_dims = [
                f.get("mesh_dimension") for f in filters
                if f.get("mesh_dimension") is not None
            ]
            score_ok = isinstance(expected_scores, list) and set(scores) == set(expected_scores)
            mesh_ok = isinstance(expected_mesh, list) and expected_mesh in mesh_dims
            if score_ok and mesh_ok:
                matching_tally = tally
                break

    if matching_tally is not None:
        add("mesh_tally_present", True, matching_tally.get("id"), "tally with expected scores and mesh")
        add("mesh_dimension", True, expected_mesh, expected_mesh)
        add("tally_scores", True, matching_tally.get("scores"), expected_scores)
        add("tally_means_finite", matching_tally.get("mean_finite") is True,
            matching_tally.get("mean_finite"), True)
        add("tally_std_devs_finite", matching_tally.get("std_dev_finite") is True,
            matching_tally.get("std_dev_finite"), True)
    else:
        add("mesh_tally_present", False, None,
            {"mesh_dimension": expected_mesh, "scores": expected_scores},
            "No single tally matched both the expected mesh dimension and complete score set.")

    failed = [item["name"] for item in checks if item["status"] != "PASS"]
    return {
        "schema_version": "1.0",
        "status": "PASS" if not failed else "FAIL",
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "failed_checks": failed,
        "checks": checks,
        "interpretation": (
            "PASS means the machine-derived statepoint export agrees with the recorded "
            "summary for the checked fields. It does not establish benchmark correctness, "
            "candidate identity, QUBO-to-material mapping, or physical validation."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", required=True, type=Path,
                        help="statepoint_audit.json generated by audit_openmc_statepoint.py")
    parser.add_argument("--baseline", required=True, type=Path,
                        help="recorded result_summary.json")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    if args.out.exists():
        parser.error(f"output already exists: {args.out}")
    try:
        audit = json.loads(args.audit.read_text(encoding="utf-8"))
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(f"could not read valid JSON input: {exc}")

    result = compare_records(audit, baseline)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "passed": result["passed_count"],
        "failed": result["failed_count"],
        "failed_checks": result["failed_checks"],
        "report": str(args.out),
    }, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
