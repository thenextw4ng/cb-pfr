"""CB-PFR: Confidence-Bounded Physical Feasibility Ranking.

A research implementation of a post-optimization candidate selection layer.
The package intentionally does not claim reactor-safety or physical validation.
"""

__version__ = "0.3.0"

from .ranking import MetricLimit, PhysicalEstimate, rank_all_methods, selected_is_conservatively_feasible
from .qubo import Candidate, CoreSpec, QuboModel, build_usmanov_style_qubo, enumerate_feasible_candidates
from .experiment import (
    CandidateEvaluation,
    EvaluationProvenance,
    ExperimentContractError,
    ExperimentSpec,
    MetricObservation,
    bundle_sha256,
    run_ranked_experiment,
)
from .solvers import (
    SolverContractError,
    SolverRun,
    SolverSolution,
    candidates_from_solver_run,
    model_to_upper_triangular_qubo,
    solve_exact,
    solve_with_ocean_sampler,
)
from .pipeline import run_solver_to_physics_pipeline

__all__ = [
    "Candidate", "CandidateEvaluation", "CoreSpec", "EvaluationProvenance",
    "ExperimentContractError", "ExperimentSpec", "MetricLimit", "MetricObservation",
    "PhysicalEstimate", "QuboModel", "SolverContractError", "SolverRun",
    "SolverSolution", "build_usmanov_style_qubo", "bundle_sha256",
    "candidates_from_solver_run", "enumerate_feasible_candidates",
    "model_to_upper_triangular_qubo", "rank_all_methods", "run_ranked_experiment",
    "run_solver_to_physics_pipeline", "selected_is_conservatively_feasible",
    "solve_exact", "solve_with_ocean_sampler",
]
