"""End-to-end orchestration: solver output -> evaluation records -> CB-PFR."""
from __future__ import annotations

from typing import Any, Mapping, Sequence
import math

from .experiment import (
    CandidateEvaluation,
    ExperimentContractError,
    ExperimentSpec,
    bundle_sha256,
    run_ranked_experiment,
)
from .qubo import Candidate, QuboModel
from .ranking import MetricLimit
from .solvers import SolverRun


def run_solver_to_physics_pipeline(
    *,
    spec: ExperimentSpec,
    model: QuboModel,
    solver_run: SolverRun | Mapping[str, Any],
    candidates: Sequence[Candidate],
    evaluations: Sequence[CandidateEvaluation],
    metrics: Sequence[MetricLimit],
    uniform_margins: Mapping[str, float],
) -> dict[str, Any]:
    """Join a real solver-run record to candidate physics evaluations and ranking.

    The solver output is mandatory here. The caller must pass only candidates
    present in that solver run, with unchanged IDs and binary vectors. This
    function still does not run a physics simulator or certify the input model.
    """
    record = solver_run.to_dict() if callable(getattr(solver_run, "to_dict", None)) else solver_run
    if not isinstance(record, Mapping):
        raise ExperimentContractError("solver_run must be a SolverRun or mapping")
    for field in ("solver_name", "solver_class", "variable_count", "solutions"):
        if field not in record:
            raise ExperimentContractError(f"solver_run is missing {field}")
    if record["solver_name"] != spec.optimizer_name:
        raise ExperimentContractError("solver name does not match ExperimentSpec.optimizer_name")
    if record["solver_class"] != spec.optimizer_class:
        raise ExperimentContractError("solver class does not match ExperimentSpec.optimizer_class")
    if record["variable_count"] != model.variable_count:
        raise ExperimentContractError("solver variable count does not match the QUBO model")
    if not isinstance(record["solutions"], (list, tuple)):
        raise ExperimentContractError("solver solutions must be a list")
    solution_vectors: dict[str, tuple[int, ...]] = {}
    for solution in record["solutions"]:
        if not isinstance(solution, Mapping) or not isinstance(solution.get("candidate_id"), str):
            raise ExperimentContractError("each solver solution needs a candidate_id and vector")
        candidate_id = solution["candidate_id"]
        if candidate_id in solution_vectors:
            raise ExperimentContractError("solver output contains duplicate candidate IDs")
        try:
            raw_vector = solution["vector"]
            if not isinstance(raw_vector, (list, tuple)):
                raise TypeError("vector must be a list or tuple")
            if any(isinstance(value, bool) or not isinstance(value, int) or value not in (0, 1) for value in raw_vector):
                raise ValueError("vector entries must be integer 0 or 1")
            vector = tuple(raw_vector)
        except (KeyError, TypeError, ValueError) as exc:
            raise ExperimentContractError("solver solution vector is invalid; expected integer binary values") from exc
        if len(vector) != model.variable_count:
            raise ExperimentContractError("solver solution vector has invalid binary dimension")
        try:
            recomputed_energy = float(model.energy(vector))
            recomputed_violations = model.constraint_violations(vector)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ExperimentContractError("solver solution cannot be evaluated against the QUBO model") from exc
        claimed_energy = solution.get("qubo_energy")
        if isinstance(claimed_energy, bool) or not isinstance(claimed_energy, (int, float)):
            raise ExperimentContractError("solver solution is missing a numeric qubo_energy")
        if not math.isfinite(float(claimed_energy)) or not math.isclose(float(claimed_energy), recomputed_energy, rel_tol=1e-10, abs_tol=1e-10):
            raise ExperimentContractError("solver solution energy does not match the QUBO model")
        if solution.get("feasible") is not model.is_feasible(vector):
            raise ExperimentContractError("solver feasibility flag does not match the QUBO model")
        claimed_violations = solution.get("constraint_violations")
        if not isinstance(claimed_violations, Mapping) or dict(claimed_violations) != recomputed_violations:
            raise ExperimentContractError("solver constraint violations do not match the QUBO model")
        solution_vectors[candidate_id] = vector
    for candidate in candidates:
        if solution_vectors.get(candidate.candidate_id) != tuple(candidate.vector):
            raise ExperimentContractError(
                f"candidate {candidate.candidate_id!r} is not an unchanged solver output"
            )

    bundle = run_ranked_experiment(
        spec=spec,
        model=model,
        candidates=candidates,
        evaluations=evaluations,
        metrics=metrics,
        uniform_margins=uniform_margins,
    )
    bundle["solver_run"] = dict(record)
    bundle["pipeline"] = {
        "stages": ["qubo_solver", "candidate_feasibility", "physics_evaluation", "cb_pfr_ranking"],
        "solver_candidate_join_validated": True,
        "physics_simulator_invoked_by_pipeline": False,
    }
    bundle["decision_bundle_sha256"] = bundle_sha256(bundle)
    return bundle
