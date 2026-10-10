"""Summaries for recorded optimizer experiments, including failed runs and quality."""
from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence

from .experiment_log import validate_experiment_payload
from .repeatability import summarize_repeated_rankings


def summarize_optimizer_experiment(
    payload: Mapping[str, Any], *, top_k: int = 1, objective_sense: str = "min"
) -> dict[str, Any]:
    """Summarize run reliability, feasibility, objective quality, and selection stability.

    Objective values are compared only within the supplied experiment and only
    when present. A candidate's objective_value is not inferred from QUBO energy.
    """
    if objective_sense not in {"min", "max"}:
        raise ValueError("objective_sense must be 'min' or 'max'")
    normalized = validate_experiment_payload(payload)
    runs = normalized["runs"]
    statuses = Counter(run["run_status"] for run in runs)
    completed = [run for run in runs if run["run_status"] == "completed"]
    if not completed:
        raise ValueError("at least one completed run is required for ranking stability analysis")

    ordered_rankings = [
        [candidate["candidate_id"] for candidate in sorted(run["candidate_records"], key=lambda item: item["rank"])]
        for run in completed
    ]
    stability = summarize_repeated_rankings(ordered_rankings, top_k=top_k)

    candidate_count = 0
    feasible_count = 0
    objective_values: list[float] = []
    feasible_objective_values: list[float] = []
    per_run: list[dict[str, Any]] = []
    for run in runs:
        candidates = run["candidate_records"]
        candidate_count += len(candidates)
        feasible = [candidate for candidate in candidates if candidate["feasible"]]
        feasible_count += len(feasible)
        all_objectives = [candidate["objective_value"] for candidate in candidates if candidate.get("objective_value") is not None]
        feasible_objectives = [candidate["objective_value"] for candidate in feasible if candidate.get("objective_value") is not None]
        objective_values.extend(all_objectives)
        feasible_objective_values.extend(feasible_objectives)
        per_run.append({
            "run_id": run["run_id"],
            "run_status": run["run_status"],
            "candidate_count": len(candidates),
            "feasible_candidate_count": len(feasible),
            "best_objective_value": (min(all_objectives) if objective_sense == "min" else max(all_objectives)) if all_objectives else None,
            "best_feasible_objective_value": (min(feasible_objectives) if objective_sense == "min" else max(feasible_objectives)) if feasible_objectives else None,
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
        "best_observed_objective_value": choose(objective_values) if objective_values else None,
        "best_observed_feasible_objective_value": choose(feasible_objective_values) if feasible_objective_values else None,
        "per_run": per_run,
        "ranking_stability": stability,
        "interpretation": (
            "descriptive results from supplied run records; not proof of global optimality, "
            "statistical confidence, or physical validity"
        ),
    }
