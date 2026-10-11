#!/usr/bin/env python3
"""Solve an emitted C5G7 CB-PFR one-hot selector QUBO with exact or Ocean backends.

Input must be a completed report from run_c5g7_cbpfr_physical_selection.py.
If no candidate passed the declared conservative screen, this tool refuses to
run. Ocean simulated annealing is classical; the QPU backend requires D-Wave
credentials and retained provider run metadata. Every stochastic result is
checked against an exact enumeration reference of the six-variable selector.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import time
from pathlib import Path
from typing import Any


def exact_selector_reference(matrix: list[list[float]], offset: float, variable_order: list[str]) -> dict[str, Any]:
    n = len(variable_order)
    if n != 6 or len(matrix) != n or any(len(row) != n for row in matrix):
        raise ValueError("expected a 6x6 selector QUBO and six candidate IDs")
    states = []
    for bits in itertools.product((0, 1), repeat=n):
        energy = offset + sum(matrix[i][i] * bits[i] for i in range(n)) + sum(
            matrix[i][j] * bits[i] * bits[j] for i in range(n) for j in range(i + 1, n)
        )
        states.append((float(energy), bits))
    best = min(energy for energy, _ in states)
    minimizers = [bits for energy, bits in states if math.isclose(energy, best, rel_tol=0.0, abs_tol=1e-10)]
    if len(minimizers) != 1 or sum(minimizers[0]) != 1:
        raise ValueError("selector QUBO must have one unique one-hot global minimizer")
    bits = minimizers[0]
    return {
        "energy": best,
        "bits": list(bits),
        "candidate_id": variable_order[bits.index(1)],
        "states_enumerated": len(states),
        "unique_one_hot_minimizer": True,
    }


def solve_report(report: dict[str, Any], *, backend: str, num_reads: int = 100) -> dict[str, Any]:
    if report.get("winner_selected") is not True or not isinstance(report.get("qubo"), dict):
        raise ValueError("input report has no accepted CB-PFR selection QUBO; refusing to optimize an unaccepted design")
    qubo = report["qubo"]
    variable_order = qubo.get("variable_order")
    matrix = qubo.get("matrix_upper_triangular")
    offset = qubo.get("offset")
    if not isinstance(variable_order, list) or not isinstance(matrix, list) or not isinstance(offset, (int, float)):
        raise ValueError("report is missing variable_order, matrix_upper_triangular, or offset")
    reference = exact_selector_reference(matrix, float(offset), variable_order)
    expected_id = report.get("selected_candidate_id")
    if reference["candidate_id"] != expected_id:
        raise ValueError("reported selected candidate does not match exact QUBO minimizer")
    feasible_ids = {
        item["candidate_id"] for item in report.get("candidates", [])
        if item.get("conservatively_feasible") is True
    }
    if expected_id not in feasible_ids:
        raise ValueError("exact QUBO minimizer is not marked conservatively feasible in the input report")
    if isinstance(num_reads, bool) or not isinstance(num_reads, int) or num_reads < 1:
        raise ValueError("num_reads must be a positive integer")

    if backend == "exact":
        return {
            "schema_version": "cbpfr.selector-solver-run.v1",
            "status": "EXACT_REFERENCE_PASS",
            "solver_name": "Exact binary enumeration",
            "solver_class": "classical_exact",
            "solver_backend": "built-in-python",
            "num_reads_requested": 2 ** len(variable_order),
            "elapsed_seconds": 0.0,
            "exact_reference": reference,
            "sampled_candidate_id": reference["candidate_id"],
            "sampled_bits": reference["bits"],
            "sampled_energy": reference["energy"],
            "matches_exact_reference": True,
            "one_hot_valid": True,
            "candidate_passed_cbpfr_screen": True,
            "qpu_run_metadata": None,
        }

    if backend not in {"ocean-sa", "dwave-qpu"}:
        raise ValueError("backend must be exact, ocean-sa, or dwave-qpu")
    if backend == "ocean-sa":
        try:
            import dimod
        except ImportError as exc:
            raise ValueError("ocean-sa requires the optional dwave-ocean-sdk package") from exc
        sampler = dimod.SimulatedAnnealingSampler()
        solver_class = "classical_simulated_annealing"
        solver_name = "D-Wave Ocean SimulatedAnnealingSampler"
    else:
        try:
            from dwave.system import DWaveSampler, EmbeddingComposite
        except ImportError as exc:
            raise ValueError("dwave-qpu requires the optional dwave-ocean-sdk package") from exc
        sampler = EmbeddingComposite(DWaveSampler())
        solver_class = "quantum_annealer"
        solver_name = "D-Wave quantum annealer via EmbeddingComposite"

    n = len(variable_order)
    q_dict = {
        (i, j): float(matrix[i][j])
        for i in range(n) for j in range(i, n)
        if float(matrix[i][j]) != 0.0
    }
    started = time.perf_counter()
    samples = sampler.sample_qubo(q_dict, num_reads=num_reads)
    elapsed = time.perf_counter() - started
    rows = []
    for row in samples.data(fields=["sample", "energy", "num_occurrences"]):
        bits = [int(row.sample[i]) for i in range(n)]
        candidate_id = variable_order[bits.index(1)] if sum(bits) == 1 else None
        full_energy = float(row.energy) + float(offset)
        rows.append({
            "bits": bits,
            "candidate_id": candidate_id,
            "sampler_energy_without_offset": float(row.energy),
            "recomputed_energy_with_offset": full_energy,
            "num_occurrences": int(row.num_occurrences),
            "one_hot_valid": sum(bits) == 1,
            "candidate_passed_cbpfr_screen": candidate_id in feasible_ids if candidate_id else False,
        })
    if not rows:
        raise ValueError("sampler returned no samples")
    # Preserve the sampler's actual lowest-energy sample; do not silently
    # promote a higher-energy feasible sample over an invalid ground sample.
    rows.sort(key=lambda item: item["sampler_energy_without_offset"])
    best = rows[0]
    exact_match = best["candidate_id"] == reference["candidate_id"] and best["one_hot_valid"]
    accepted = exact_match and best["candidate_passed_cbpfr_screen"]
    info = getattr(samples, "info", {}) or {}
    return {
        "schema_version": "cbpfr.selector-solver-run.v1",
        "status": "SAMPLER_RECOVERED_EXACT_REFERENCE" if accepted else "SAMPLER_DID_NOT_RECOVER_EXACT_REFERENCE",
        "solver_name": solver_name,
        "solver_class": solver_class,
        "solver_backend": type(sampler).__module__ + "." + type(sampler).__qualname__,
        "num_reads_requested": num_reads,
        "elapsed_seconds": elapsed,
        "exact_reference": reference,
        "sampled_candidate_id": best["candidate_id"],
        "sampled_bits": best["bits"],
        "sampled_energy": best["recomputed_energy_with_offset"],
        "matches_exact_reference": exact_match,
        "one_hot_valid": best["one_hot_valid"],
        "candidate_passed_cbpfr_screen": best["candidate_passed_cbpfr_screen"],
        "accepted_selection": accepted,
        "returned_samples": rows,
        "qpu_run_metadata": info if backend == "dwave-qpu" else None,
        "scientific_note": (
            "A sampler match to exact enumeration validates this small selector solve only. "
            "It does not establish quantum advantage, reactor safety, or physical-model validity."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection-report", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--backend", choices=("exact", "ocean-sa", "dwave-qpu"), default="exact")
    parser.add_argument("--num-reads", type=int, default=100)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite existing output: {args.out}")
    try:
        report = json.loads(args.selection_report.read_text(encoding="utf-8"))
        result = solve_report(report, backend=args.backend, num_reads=args.num_reads)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    result["input_selection_report"] = str(args.selection_report)
    result["input_selection_report_sha256"] = hashlib.sha256(args.selection_report.read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "solver_class": result["solver_class"],
        "sampled_candidate_id": result["sampled_candidate_id"],
        "matches_exact_reference": result["matches_exact_reference"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
