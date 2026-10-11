#!/usr/bin/env python3
"""Optional D-Wave QPU runner for a frozen QUBO JSON instance.

This script requires dwave-system and a valid DWAVE_API_TOKEN environment
variable. It records one independent sampler call per trial. Each trial is a
batch of --num-reads samples, so success probability is per batch, not per
individual read. Wall time includes embedding, remote communication, sampling,
and result retrieval. The separately recorded anneal-time sum is only the
configured annealing duration multiplied by reads; it is not end-to-end time.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import time
from pathlib import Path
from typing import Any


def load_problem(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("problem JSON must be an object")
    variables = data.get("variables")
    linear = data.get("linear")
    quadratic = data.get("quadratic")
    target = data.get("target_energy")
    if not isinstance(variables, list) or not variables or len(set(variables)) != len(variables):
        raise ValueError("variables must be a nonempty list of unique names")
    if any(not isinstance(v, str) or not v for v in variables):
        raise ValueError("each variable must be a nonempty string")
    if not isinstance(linear, dict) or not isinstance(quadratic, list):
        raise ValueError("linear must be an object and quadratic must be a list")
    if isinstance(target, bool) or not isinstance(target, (int, float)) or not math.isfinite(target):
        raise ValueError("target_energy must be a finite number")
    allowed = set(variables)
    for name, bias in linear.items():
        if name not in allowed:
            raise ValueError(f"linear term uses undeclared variable {name!r}")
        if isinstance(bias, bool) or not isinstance(bias, (int, float)) or not math.isfinite(bias):
            raise ValueError(f"invalid linear bias for {name!r}")
    for term in quadratic:
        if not isinstance(term, list) or len(term) != 3:
            raise ValueError("each quadratic term must be [variable_a, variable_b, bias]")
        u, v, bias = term
        if u not in allowed or v not in allowed:
            raise ValueError(f"quadratic term uses undeclared variable: {term!r}")
        if isinstance(bias, bool) or not isinstance(bias, (int, float)) or not math.isfinite(bias):
            raise ValueError(f"invalid quadratic bias: {term!r}")
    offset = data.get("offset", 0.0)
    if isinstance(offset, bool) or not isinstance(offset, (int, float)) or not math.isfinite(offset):
        raise ValueError("offset must be a finite number")
    return data


def build_qubo(data: dict[str, Any]) -> dict[tuple[str, str], float]:
    qubo: dict[tuple[str, str], float] = {}
    for name, bias in data["linear"].items():
        qubo[(name, name)] = qubo.get((name, name), 0.0) + float(bias)
    for u, v, bias in data["quadratic"]:
        key = (u, v)
        qubo[key] = qubo.get(key, 0.0) + float(bias)
    # Constant offsets do not change the minimizing sample. The caller's
    # target_energy is expressed in the full energy convention, so add the
    # offset back when testing success below.
    return qubo


def run(problem_path: Path, output_csv: Path, metadata_path: Path, *, num_reads: int,
        num_trials: int, annealing_time_us: int | None, solver: str | None) -> None:
    if not os.environ.get("DWAVE_API_TOKEN"):
        raise RuntimeError("DWAVE_API_TOKEN is missing; no QPU job was submitted")
    data = load_problem(problem_path)
    qubo = build_qubo(data)
    try:
        from dwave.system import DWaveSampler, EmbeddingComposite
    except ImportError as exc:
        raise RuntimeError("Install optional dependency with: pip install dwave-system") from exc

    setup_start = time.perf_counter()
    sampler_args: dict[str, Any] = {"token": os.environ["DWAVE_API_TOKEN"]}
    if solver:
        sampler_args["solver"] = solver
    sampler = DWaveSampler(**sampler_args)
    composite = EmbeddingComposite(sampler)
    setup_s = time.perf_counter() - setup_start
    rows: list[dict[str, Any]] = []
    trial_metadata: list[dict[str, Any]] = []
    sample_kwargs: dict[str, Any] = {"num_reads": num_reads}
    if annealing_time_us is not None:
        sample_kwargs["annealing_time"] = annealing_time_us

    for trial in range(1, num_trials + 1):
        start = time.perf_counter()
        response = composite.sample_qubo(qubo, **sample_kwargs)
        wall_s = time.perf_counter() - start
        best = response.first
        best_energy = float(best.energy) + float(data.get("offset", 0.0))
        success = best_energy <= float(data["target_energy"]) + float(data.get("energy_tolerance", 1e-9))
        anneal_s = "" if annealing_time_us is None else annealing_time_us * num_reads / 1_000_000.0
        rows.append({
            "instance_id": str(data.get("instance_id", problem_path.stem)),
            "method": "dwave_qpu",
            "trial_id": str(trial),
            "success": int(success),
            "per_attempt_wall_time_s": f"{wall_s:.12g}",
            "one_time_setup_s": f"{setup_s:.12g}",
            "anneal_time_s": "" if anneal_s == "" else f"{anneal_s:.12g}",
            "objective_value": f"{best_energy:.16g}",
        })
        trial_metadata.append({
            "trial_id": trial,
            "best_energy_including_offset": best_energy,
            "target_energy": float(data["target_energy"]),
            "success": success,
            "best_sample": {str(k): int(v) for k, v in best.sample.items()},
            "wall_time_s": wall_s,
            "response_info": dict(response.info),
        })

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    metadata = {
        "status": "QPU_RUN_COMPLETED",
        "instance_id": str(data.get("instance_id", problem_path.stem)),
        "problem_sha256": hashlib.sha256(problem_path.read_bytes()).hexdigest(),
        "solver_id": getattr(sampler, "solver", {}).get("id") if isinstance(getattr(sampler, "solver", None), dict) else str(getattr(sampler, "solver", "unknown")),
        "num_reads_per_trial": num_reads,
        "num_trials": num_trials,
        "annealing_time_us_per_read": annealing_time_us,
        "one_time_setup_s": setup_s,
        "target_energy_including_offset": float(data["target_energy"]),
        "energy_tolerance": float(data.get("energy_tolerance", 1e-9)),
        "success_definition": "best returned energy including offset <= target_energy + energy_tolerance",
        "timing_warning": "Per-attempt wall time includes embedding, remote communication, sampling, and result retrieval. Configured anneal-time sum excludes all such overhead.",
        "trials": trial_metadata,
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Completed {num_trials} D-Wave sampler calls for {metadata['instance_id']}.")
    print(f"Run-level CSV: {output_csv}")
    print(f"Audit metadata: {metadata_path}")
    print("A QPU execution is not, by itself, evidence of quantum advantage.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--problem", required=True, type=Path, help="Frozen QUBO JSON")
    parser.add_argument("--output-csv", required=True, type=Path, help="Run-level CSV output")
    parser.add_argument("--metadata-json", required=True, type=Path, help="Audit metadata JSON output")
    parser.add_argument("--num-reads", type=int, default=1000, help="Reads per independent sampler call")
    parser.add_argument("--num-trials", type=int, default=30, help="Independent sampler calls")
    parser.add_argument("--annealing-time-us", type=int, default=None, help="Optional anneal duration per read")
    parser.add_argument("--solver", default=None, help="Optional exact D-Wave solver identifier")
    args = parser.parse_args()
    if args.num_reads < 1 or args.num_trials < 1:
        parser.error("--num-reads and --num-trials must be positive")
    if args.annealing_time_us is not None and args.annealing_time_us < 1:
        parser.error("--annealing-time-us must be positive")
    if args.output_csv.resolve() == args.metadata_json.resolve():
        parser.error("CSV and JSON outputs must be different paths")
    try:
        run(args.problem, args.output_csv, args.metadata_json,
            num_reads=args.num_reads, num_trials=args.num_trials,
            annealing_time_us=args.annealing_time_us, solver=args.solver)
    except (ValueError, RuntimeError, OSError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
