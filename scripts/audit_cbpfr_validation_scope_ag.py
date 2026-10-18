#!/usr/bin/env python3
"""Machine-check exact QUBO/layout invariants and emit a fail-closed A-G status snapshot.

This checker deliberately does not infer physical validation from passing code tests.
It only evaluates deterministic design-space/QUBO invariants and records the remaining
human/model/benchmark blockers from the versioned validation protocol.
"""
from __future__ import annotations
import importlib.util
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cbpfr.c5g7_design_qubo import (  # noqa: E402
    enumerate_feasible_assignments, qubo_energy, vector_from_assignment
)

def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}

def layout_manifest() -> dict:
    path = ROOT / "scripts" / "enumerate_c5g7_layouts.py"
    spec = importlib.util.spec_from_file_location("enumerate_c5g7_layouts", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_design_space()

def main() -> int:
    qman = layout_manifest()
    assignments = enumerate_feasible_assignments()
    signatures = sorted("".join("M" if v == "MOX" else "U" for v in item.values())
                        for item in assignments)
    energies = [float(qubo_energy(vector_from_assignment(item))) for item in assignments]
    invalid = [bits for bits in itertools.product((0, 1), repeat=4) if sum(bits) != 2]
    invalid_energies = [float(qubo_energy(bits)) for bits in invalid]
    layouts_ok = (
        len(assignments) == 6 and len(set(signatures)) == 6
        and all(list(item.values()).count("MOX") == 2
                and list(item.values()).count("UO2") == 2 for item in assignments)
        and qman.get("candidate_count") == 6
        and all(item.get("physical_results") is None
                and item.get("requires_transport_evaluation") is True
                for item in qman.get("candidate_layouts", []))
    )
    qubo_ok = (
        len(energies) == 6 and all(abs(e) < 1e-12 for e in energies)
        and len(invalid_energies) == 10 and all(e > 0 for e in invalid_energies)
        and len(set(energies)) == 1
    )
    protocol = load_json(ROOT / "config" / "benchmarks" / "c5g7_validation_protocol.json")
    beavrs = load_json(ROOT / "config" / "benchmarks" / "beavrs_validation_manifest.json")
    # A successful algorithmic audit is only a software sub-gate of the wider scientific contract.
    gates = {
        "A_model_identity_fidelity": {
            "status": "BLOCKED_REQUIRES_PRIMARY_SPECIFICATION_REVIEW",
            "reason": "The pinned model and generated inputs still require independent fidelity review; numerical matching does not prove model identity."
        },
        "B_geometry_tally_spatial_mapping": {
            "status": "BLOCKED_REQUIRES_INDEPENDENT_MAPPING_AND_REFERENCE_REVIEW",
            "reason": "Mesh-to-physical-region and cross-code comparisons must be shown like-for-like; normalized fission-rate shape is not absolute power."
        },
        "C_qubo_design_space": {
            "status": "PASS" if (layouts_ok and qubo_ok) else "FAIL",
            "reason": "Exhaustive four-bit check: six exactly-two-MOX assignments have equal zero penalty; ten invalid cardinalities have positive penalty."
                if (layouts_ok and qubo_ok) else "One or more exact enumeration/QUBO invariants failed.",
            "physical_decision_subgate": "BLOCKED_PREDECLARED_PHYSICAL_OBJECTIVE_AND_ACCEPTANCE_RULE"
        },
        "D_run_integrity_reproducibility_convergence": {
            "status": "IN_PROGRESS_REQUIRES_RUN_ARTIFACT_AUDIT_AND_STATIONARITY_REVIEW",
            "reason": "P4/P5 OpenMC campaign and independent S_N runs are executing; workflow success alone does not certify source/eigenvalue stationarity."
        },
        "E_experimental_or_trusted_benchmark_validation": {
            "status": "NOT_ESTABLISHED",
            "reason": "The previous BEAVRS map comparison was poor; the current C5G7 independent-solver discrepancy requires model/mapping investigation. No reactor-safety acceptance criterion is asserted."
        },
        "F_fail_closed_evidence_pipeline": {
            "status": "SOFTWARE_SUBGATE_UNDER_AUTOMATED_TEST",
            "reason": "This workflow checks exact algorithmic invariants and targeted tests; it cannot promote unresolved physical gates to PASS."
        },
        "G_synthesis_bounded_claims_release": {
            "status": "BLOCKED_ON_APPLICABLE_A_TO_F_GATES",
            "reason": "Until physical gates pass, only a domain-bounded screening/ranking claim is permitted."
        }
    }
    checks = {
        "six_unique_layouts": len(assignments) == 6 and len(set(signatures)) == 6,
        "two_mox_two_uo2_each": all(list(item.values()).count("MOX") == 2 and
                                    list(item.values()).count("UO2") == 2 for item in assignments),
        "all_feasible_qubo_penalties_equal_zero": len(energies) == 6 and all(abs(e) < 1e-12 for e in energies),
        "all_invalid_cardinality_penalties_positive": len(invalid_energies) == 10 and all(e > 0 for e in invalid_energies),
        "layout_manifest_requires_transport_evaluation": layouts_ok,
        "qubo_matrix_matches_direct_energy": qubo_ok,
        "protocol_does_not_claim_official_acceptance": protocol.get("status") != "PHYSICAL_VALIDATION_PASS",
        "beavrs_manifest_not_physically_validated": beavrs.get("overall_status") != "PHYSICALLY_VALIDATED",
    }
    out = {
        "schema_version": "1.0",
        "audit_id": "CBPFR-A-G-foundation-audit-2026-10-18",
        "scope": "deterministic software/design-space sub-gates only; not a physical-validation decision",
        "checks": checks,
        "all_deterministic_checks_pass": all(checks.values()),
        "candidate_signatures": signatures,
        "feasible_qubo_energies": energies,
        "invalid_cardinality_vectors_checked": len(invalid),
        "invalid_cardinality_energies": invalid_energies,
        "gate_status": gates,
        "overall_physical_validation_status": "NOT_ESTABLISHED",
        "manifest_statuses_observed": {
            "c5g7_validation_protocol": protocol.get("status", "MISSING"),
            "beavrs_validation_manifest": beavrs.get("overall_status", "MISSING"),
        },
        "nonclaims": [
            "No reactor-safety claim or universal physical-best claim.",
            "No physical-validation inference from CI/test success.",
            "C5G7 canonical-reference agreement does not automatically validate all six layout variants.",
            "A deterministic S_N cross-code run is not experimental validation."
        ]
    }
    outdir = ROOT / "ag-foundation-audit"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "cbpfr_ag_foundation_audit.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0 if all(checks.values()) else 1

if __name__ == "__main__":
    raise SystemExit(main())
