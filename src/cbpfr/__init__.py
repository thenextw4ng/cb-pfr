"""CB-PFR: Confidence-Bounded Physical Feasibility Ranking.

A research implementation of a post-optimization candidate selection layer.
The package intentionally does not claim reactor-safety or physical validation.
"""

__version__ = "0.2.0"

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

__all__ = [
    "Candidate", "CandidateEvaluation", "CoreSpec", "EvaluationProvenance",
    "ExperimentContractError", "ExperimentSpec", "MetricLimit", "MetricObservation",
    "PhysicalEstimate", "QuboModel", "build_usmanov_style_qubo",
    "enumerate_feasible_candidates", "rank_all_methods", "run_ranked_experiment",
    "selected_is_conservatively_feasible", "bundle_sha256",
]
