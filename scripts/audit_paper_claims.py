#!/usr/bin/env python3
"""Build a fail-closed traceability audit for the ReactorQ/Eureka and CB-PFR claims.

This report separates software execution evidence from physical validation.
It never upgrades missing evidence into a PASS and never invents reactor limits.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def build_report(root: Path) -> dict[str, Any]:
    results = root / "results"
    repeatability = _read_json(results / "c5g7_repeatability_reexecution_2026-10-11.json")
    canonical_partial = _read_json(results / "c5g7_canonical_partial_2026-10-11.json")
    recorded_audit = _read_json(results / "recorded_results_audit.json")

    with (results / "main_results.csv").open(newline="", encoding="utf-8") as handle:
        synthetic_rows = list(csv.DictReader(handle))
    synthetic_by_method = {row["method"]: row for row in synthetic_rows}
    expected_rates = {
        "qubo_only": 0.857,
        "point_estimate": 0.933,
        "cb_pfr": 0.976,
        "uniform_margin": 0.966,
    }
    synthetic_ok = (
        set(synthetic_by_method) == set(expected_rates)
        and all(int(synthetic_by_method[m]["trials"]) == 1000 for m in expected_rates)
        and all(abs(float(synthetic_by_method[m]["selected_true_feasibility_rate"]) - rate) < 1e-12
                for m, rate in expected_rates.items())
        and all(row["experiment_domain"] == "synthetic_known_normal_model" for row in synthetic_rows)
        and all(row["physical_validation"] == "not_performed" for row in synthetic_rows)
    )

    with (results / "benchmark_comparison.csv").open(newline="", encoding="utf-8") as handle:
        comparisons = list(csv.DictReader(handle))
    keff_screen_recorded = any(
        row.get("metric") == "k_eff"
        and row.get("comparison_status", "").startswith("NUMERICAL_SCREEN_ONLY")
        for row in comparisons
    )
    unlike_power_blocked = any(
        row.get("metric") == "assembly_integrated_fission_rate_peaking_factor"
        and row.get("comparison_status") == "BLOCKED_NOT_COMPARABLE_OBSERVABLE"
        for row in comparisons
    )

    candidates = repeatability.get("candidates", [])
    all_six_layouts_have_three_runs = (
        repeatability.get("run_count") == 18
        and repeatability.get("candidate_count") == 6
        and repeatability.get("round_count") == 3
        and len(candidates) == 6
        and all(row.get("n_runs") == 3 for row in candidates)
    )
    transport_evidence_integrity = (
        all_six_layouts_have_three_runs
        and repeatability.get("all_group_structure_audits_passed") is True
        and repeatability.get("all_statepoint_hashes_unique") is True
        and repeatability.get("all_mgxs_hashes_identical") is True
        and repeatability.get("all_spatial_mapping_checks_passed") is True
    )

    completed = canonical_partial.get("completed_cases", [])
    incomplete = canonical_partial.get("incomplete_cases", [])
    high_budget_incomplete = (
        len(completed) == 2
        and len(incomplete) == 1
        and all(case.get("raw_hdf5_audit", {}).get("status") == "PASS" for case in completed)
        and all(case.get("entropy_box_warning_count", 0) > 0 for case in completed)
    )

    claims = {
        "c5g7_two_uo2_two_mox_qubo_cardinality": {
            "status": "PASS_SOFTWARE_FORMULATION_ONLY",
            "evidence": "src/cbpfr/c5g7_design_qubo.py and tests/test_c5g7_design_qubo.py",
            "meaning": "The separate four-position layout QUBO has six feasible assignments; this is not the Usmanov burnup-state model.",
        },
        "openmc_transport_execution": {
            "status": "PASS_EXECUTION_ONLY" if transport_evidence_integrity else "EVIDENCE_INTEGRITY_REVIEW_REQUIRED",
            "evidence": repeatability.get("workflow_url"),
            "meaning": "18 exploratory transport runs cover six layouts and three seeds per layout; execution does not establish benchmark acceptance.",
        },
        "keff_reference_comparison": {
            "status": "SCREEN_ONLY" if keff_screen_recorded else "NOT_ESTABLISHED",
            "evidence": "results/benchmark_comparison.csv",
            "meaning": "The recorded values are low-budget numerical screens, not accepted benchmark validation.",
        },
        "flux_distribution_output": {
            "status": "NOT_ESTABLISHED",
            "evidence": "The preserved analysis establishes k_eff and an assembly-integrated fission-rate proxy; a reviewed flux-distribution result is not evidenced by this claim audit.",
        },
        "power_peaking_comparison": {
            "status": "BLOCKED_NONCOMPARABLE_OBSERVABLES" if unlike_power_blocked else "NOT_ESTABLISHED",
            "evidence": "results/benchmark_comparison.csv",
            "meaning": "The local assembly-integrated fission-rate proxy is not the published maximum normalized pin power.",
        },
        "repeated_quantum_annealing_frequency_and_hamming_analysis": {
            "status": "NOT_RUN",
            "meaning": "Three independent transport seeds per layout are not repeated quantum-annealing optimizer runs. No actual quantum-annealing hardware execution or optimizer-sample frequency/Hamming-distance evidence is present in the checked artifacts.",
        },
        "usmanov_burnup_state_to_c5g7_material_mapping": {
            "status": "BLOCKED_NO_DEFENSIBLE_MAPPING_FOUND",
            "meaning": "Fresh/once-burned/twice-burned states cannot be silently mapped to UO2/MOX labels without documented depletion/material definitions and independent review.",
        },
        "benchmark_grade_convergence": {
            "status": "BLOCKED_INCOMPLETE_HIGH_BUDGET_RUN" if high_budget_incomplete else "REQUIRES_REVIEW",
            "evidence": "results/c5g7_canonical_partial_2026-10-11.json",
            "meaning": "The high-budget run was cancelled after two seeds; both completed runs retained entropy-box warnings and the aggregate gate was skipped.",
        },
        "experimental_physical_validation": {
            "status": "NOT_ESTABLISHED",
            "meaning": "A computational C5G7 reference is not a physical-reactor experiment, and no comparable experiment with uncertainty provenance is evidenced.",
        },
        "cbpfr_software_and_synthetic_benchmark": {
            "status": "PASS_REPRODUCIBLE_AGGREGATE" if synthetic_ok and recorded_audit.get("rows") == 4000 else "REPRODUCTION_CHECK_FAILED",
            "evidence": "results/main_results.csv, results/per_seed_results.csv, results/recorded_results_audit.json and the CI synthetic-reproduction step",
            "meaning": "The recorded 1,000-trial synthetic aggregate is reproducible by the repository's CI protocol; it is not physical validation and the audit records that an independent full rerun was not performed.",
            "selected_true_feasibility_rates": {
                method: float(row["selected_true_feasibility_rate"])
                for method, row in synthetic_by_method.items()
            },
        },
        "cbpfr_physical_validation": {
            "status": "BLOCKED",
            "meaning": "CB-PFR physical validation requires a defensible material mapping, source-comparable metrics, and predeclared physically justified limits; synthetic limits do not supply these.",
        },
    }
    blockers = [name for name, item in claims.items()
                if item["status"].startswith(("BLOCKED", "NOT_", "SCREEN_ONLY", "PASS_EXECUTION_ONLY",
                                              "PASS_SOFTWARE_FORMULATION_ONLY",
                                              "BLOCKED_NONCOMPARABLE", "BLOCKED_INCOMPLETE"))]
    return {
        "schema_version": "1.0",
        "audit_status": "AUDIT_COMPLETE_WITH_OPEN_SCIENTIFIC_BLOCKERS",
        "audit_scope": [
            "EUREKA/ReactoQ claims stated in the supplied project paper",
            "CB-PFR working-paper implementation and evidence claims",
        ],
        "evidence_integrity_checks": {
            "18_run_six_layout_three_seed_summary_consistent": all_six_layouts_have_three_runs,
            "transport_artifact_audits_consistent": transport_evidence_integrity,
            "keff_screen_recorded": keff_screen_recorded,
            "unlike_power_observable_blocked": unlike_power_blocked,
            "synthetic_aggregate_consistent": synthetic_ok,
            "high_budget_incomplete_state_preserved": high_budget_incomplete,
        },
        "claims": claims,
        "open_claim_count": len(blockers),
        "interpretation": (
            "This audit closes the evidence inventory, not the open scientific claims. "
            "Do not state that all paper claims are physically validated. The unclosed items "
            "require genuine solver runs, reviewed model identity, convergence evidence, "
            "source-comparable observables, and/or independent scientific review."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        report = build_report(args.root)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        parser.error(f"claim audit could not be completed: {exc}")
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        if args.out.exists():
            parser.error(f"refusing to overwrite existing output: {args.out}")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    print(json.dumps({
        "audit_status": report["audit_status"],
        "open_claim_count": report["open_claim_count"],
        "evidence_integrity_checks": report["evidence_integrity_checks"],
    }, indent=2))
    return 0 if all(report["evidence_integrity_checks"].values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
