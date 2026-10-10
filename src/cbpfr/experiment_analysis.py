"""Summaries for recorded optimizer experiments, including failures and objective quality."""
from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from .experiment_log import validate_experiment_payload
from .repeatability import summarize_repeated_rankings


def summarize_optimizer_experiment(
    payload: Mapping[str, Any], *, top_k: int = 1, objective_sense: str = "min"
) -> dict[str, Any]:
    """Summarize run reliability, feasibility, objective quality, and ranking stability.

    Objective values are not inferred from QUBO energy. Failed runs remain in
    reliability counts and are excluded from ranking stability by definition.
    """
    if objective_sense not in {"min", "max"}:
        raise ValueError("objective_sense must be 'min' or 'max'")
    normalized = validate_experiment_payload(payload)
    runs = normalized["runs"]
    statuses = Counter(run["run_status"] for run in runs)
    completed = [run for run in runs if run["run_status"] == "completed"]
    if not completed:
        raise ValueError("at least one completed run is required for ranking stability analysis")

    rankings = [
        [candidate["candidate_id"] for candidate in sorted(run["candidate_records"], key=lambda item: item["rank"])]
        for run in completed
    ]
    stability = summarize_repeated_rankings(rankings, top_k=top_k)
    candidate_count = feasible_count = 0
    all_objectives: list[float] = []
    feasible_objectives: list[float] = []
    per_run: list[dict[str, Any]] = []
    for run in runs:
        candidates = run["candidate_records"]
        feasible = [c for c in candidates if c["feasible"]]
        objectives = [c["objective_value"] for c in candidates if c.get("objective_value") is not None]
        feasible_obj = [c["objective_value"] for c in feasible if c.get("objective_value") is not None]
        candidate_count += len(candidates)
        feasible_count += len(feasible)
        all_objectives.extend(objectives)
        feasible_objectives.extend(feasible_obj)
        choose = min if objective_sense == "min" else max
        per_run.append({
            "run_id": run["run_id"],
            "run_status": run["run_status"],
            "candidate_count": len(candidates),
            "feasible_candidate_count": len(feasible),
            "best_objective_value": choose(objectives) if objectives else None,
            "best_feasible_objective_value": choose(feasible_obj) if feasible_obj else None,
            "failure_reason": run.get("failure_reason"),
        })
    choose = min if objective_sense == "min" else max
    return {
        "schema_version": normalized["schema_version"],
        "experiment_id": normalized["experiment_id"],
        "run_count": len(runs),
        "completed_run_count": len(completed),
        "failed_or_interrupted_run_count": len(runs) - len(completed),
        "run_status_counts": dict(sorted(statuses.items())),
        "candidate_record_count": candidate_count,
        "feasible_candidate_count": feasible_count,
        "observed_candidate_feasibility_rate": feasible_count / candidate_count if candidate_count else None,
        "objective_sense": objective_sense,
        "best_observed_objective_value": choose(all_objectives) if all_objectives else None,
        "best_observed_feasible_objective_value": choose(feasible_objectives) if feasible_objectives else None,
        "per_run": per_run,
        "ranking_stability": stability,
        "interpretation": "descriptive results only; not proof of global optimality, statistical confidence, or physical validity",
    }
