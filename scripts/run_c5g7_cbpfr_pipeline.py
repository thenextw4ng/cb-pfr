#!/usr/bin/env python3
"""Orchestrate the auditable C5G7 evidence -> CB-PFR -> selector-QUBO workflow.

This command consumes run-level rows from completed OpenMC executions. It does not
launch OpenMC; it verifies their provenance, performs the declared conservative
screen, emits the post-physics selector QUBO, solves it, and writes one integrated
bundle. The four-variable material-placement QUBO and the six-variable selector
QUBO are distinct formulations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

try:
    from scripts.run_c5g7_cbpfr_physical_selection import evaluate, load_and_validate
    from scripts.solve_c5g7_cbpfr_qubo import solve_report
except ModuleNotFoundError:  # direct execution with scripts/ as sys.path[0]
    from run_c5g7_cbpfr_physical_selection import evaluate, load_and_validate
    from solve_c5g7_cbpfr_qubo import solve_report


SCHEMA_VERSION = "cbpfr.c5g7-integrated-pipeline.v1"
LAYOUTS = ("MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM")
POSITIONS = ("p00", "p01", "p10", "p11")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _finite_positive(value: float, name: str) -> None:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")


def run_integrated_pipeline(
    run_level_csv: Path,
    *,
    backend: str = "exact",
    num_reads: int = 100,
    keff_min: float,
    keff_max: float,
    fission_peaking_max: float,
    uncertainty_multiplier: float,
    keff_scale: float,
    fission_peaking_scale: float,
    risk_weight: float,
    min_batches: int,
    min_particles: int,
    min_replicates: int = 3,
) -> dict[str, Any]:
    """Validate OpenMC run evidence, apply CB-PFR, and solve the emitted selector QUBO."""
    raw_bytes = run_level_csv.read_bytes()
    rows, evidence_audit = load_and_validate(
        run_level_csv,
        min_batches=min_batches,
        min_particles=min_particles,
        min_replicates=min_replicates,
    )
    selection = evaluate(
        rows,
        keff_min=keff_min,
        keff_max=keff_max,
        fission_peaking_max=fission_peaking_max,
        uncertainty_multiplier=uncertainty_multiplier,
        keff_scale=keff_scale,
        fission_peaking_scale=fission_peaking_scale,
        risk_weight=risk_weight,
    )
    selection["evidence_audit"] = evidence_audit
    selection["input_csv_sha256"] = sha256_bytes(raw_bytes)

    # A selector solve is permitted only after the physics screen has emitted an
    # accepted one-hot QUBO. The solver's own exact reference is checked again.
    solver_result = None
    if selection.get("winner_selected") is True:
        solver_result = solve_report(selection, backend=backend, num_reads=num_reads)
        if backend == "exact":
            solver_accepted = (
                solver_result.get("matches_exact_reference") is True
                and solver_result.get("candidate_passed_cbpfr_screen") is True
            )
        else:
            solver_accepted = solver_result.get("accepted_selection") is True
    else:
        solver_accepted = False

    candidates = []
    for candidate in selection["candidates"]:
        signature = candidate["layout_signature"]
        layout = {
            position: ("MOX" if material == "M" else "UO2")
            for position, material in zip(POSITIONS, signature)
        }
        candidates.append({
            **candidate,
            "material_layout": layout,
            "layout_encoding": "C5G7-2x2-two-MOX-two-UO2-v1",
            "physical_metric_semantics": {
                "keff": "OpenMC eigenvalue estimate; per-run SD and between-seed spread are kept distinct",
                "fission_rate_peaking_factor": "dimensionless relative fission-rate proxy; not absolute power or a safety metric",
            },
        })

    if selection.get("winner_selected") is not True:
        status = "BLOCKED_NO_CONSERVATIVELY_FEASIBLE_CANDIDATE"
    elif solver_accepted:
        status = "PIPELINE_COMPLETE_SELECTION_REPRODUCED"
    else:
        status = "PHYSICS_SCREEN_COMPLETED_SOLVER_SELECTION_NOT_ACCEPTED"

    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "workflow": {
            "stages": [
                "C5G7 two-MOX material-layout encoding",
                "completed OpenMC run evidence ingestion",
                "run-level provenance and corrected-group audit",
                "repeated-run aggregation and conservative CB-PFR screen",
                "post-physics one-hot selector QUBO construction",
                "solver execution and exact-reference comparison",
            ],
            "openmc_transport_launched_by_this_command": False,
            "input_requires_completed_openmc_evidence": True,
            "all_six_layouts_required": True,
            "material_placement_qubo_is_physics_objective": False,
            "selector_qubo_is_post_physics": True,
        },
        "input": {
            "run_level_csv": str(run_level_csv),
            "run_level_csv_sha256": sha256_bytes(raw_bytes),
            "run_count": evidence_audit["run_count"],
            "layout_count": evidence_audit["layout_count"],
            "mgxs_sha256": evidence_audit["single_mgxs_hash"],
            "common_settings": evidence_audit["common_settings"],
        },
        "formulation_separation": {
            "material_placement_formulation": {
                "formulation_id": "c5g7-2x2-exactly-two-MOX-v1",
                "variables": list(POSITIONS),
                "encoding": "y_i=1 means MOX; y_i=0 means UO2",
                "objective": "A*(sum(y_i)-2)^2",
                "feasible_layout_count": 6,
                "energy_can_rank_physics": False,
            },
            "post_physics_selector_formulation": {
                "formulation_id": "cbpfr-c5g7-post-physics-one-hot-v1",
                "variable_order": (selection.get("qubo") or {}).get("variable_order", []),
                "constructed_only_after_physics_screen": True,
            },
        },
        "evidence_audit": evidence_audit,
        "screening_parameters": selection["limits"],
        "candidates": candidates,
        "cbpfr_selection_report": selection,
        "solver_run": solver_result,
        "decision": {
            "candidate_id": (
                solver_result.get("sampled_candidate_id")
                if solver_accepted and solver_result else None
            ),
            "cbpfr_reference_candidate_id": selection.get("selected_candidate_id"),
            "accepted": solver_accepted,
            "physical_validation_certified": False,
            "reactor_safety_conclusion": False,
            "quantum_advantage_established": False,
            "interpretation": (
                "The integrated bundle verifies the declared software/data path and the selector result. "
                "It does not certify benchmark validity, convergence, physical superiority, or reactor safety. "
                "A QPU claim requires retained provider run evidence; the exact backend is classical."
            ),
        },
        "nonclaims": [
            "The legacy fresh/once_burned/twice_burned QUBO is not mapped to C5G7 UO2/MOX.",
            "The four-variable material-placement QUBO enforces composition count only and does not rank physical outcomes.",
            "A fission-rate peaking proxy is not absolute power.",
            "A smoke-budget run is not benchmark-grade convergence.",
            "A passing pipeline is not physical validation or reactor-safety certification.",
        ],
    }
    canonical = json.dumps(payload, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["bundle_sha256"] = sha256_bytes(canonical)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-level-csv", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--backend", choices=("exact", "ocean-sa", "dwave-qpu"), default="exact")
    parser.add_argument("--num-reads", type=int, default=100)
    parser.add_argument("--keff-min", type=float, required=True)
    parser.add_argument("--keff-max", type=float, required=True)
    parser.add_argument("--fission-peaking-max", type=float, required=True)
    parser.add_argument("--uncertainty-multiplier", type=float, required=True)
    parser.add_argument("--keff-scale", type=float, required=True)
    parser.add_argument("--fission-peaking-scale", type=float, required=True)
    parser.add_argument("--risk-weight", type=float, required=True)
    parser.add_argument("--min-batches", type=int, required=True)
    parser.add_argument("--min-particles", type=int, required=True)
    parser.add_argument("--min-replicates", type=int, default=3)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite existing output: {args.out}")
    if args.num_reads < 1:
        parser.error("--num-reads must be positive")
    try:
        payload = run_integrated_pipeline(
            args.run_level_csv,
            backend=args.backend,
            num_reads=args.num_reads,
            keff_min=args.keff_min,
            keff_max=args.keff_max,
            fission_peaking_max=args.fission_peaking_max,
            uncertainty_multiplier=args.uncertainty_multiplier,
            keff_scale=args.keff_scale,
            fission_peaking_scale=args.fission_peaking_scale,
            risk_weight=args.risk_weight,
            min_batches=args.min_batches,
            min_particles=args.min_particles,
            min_replicates=args.min_replicates,
        )
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "run_count": payload["input"]["run_count"],
        "candidate_count": len(payload["candidates"]),
        "cbpfr_candidate_id": payload["decision"]["cbpfr_reference_candidate_id"],
        "accepted_candidate_id": payload["decision"]["candidate_id"],
        "bundle_sha256": payload["bundle_sha256"],
        "out": str(args.out),
    }, indent=2))
    return 0 if payload["status"] == "PIPELINE_COMPLETE_SELECTION_REPRODUCED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
