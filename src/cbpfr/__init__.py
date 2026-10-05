"""CB-PFR: Confidence-Bounded Physical Feasibility Ranking.

A research implementation of a post-optimization candidate selection layer.
The package intentionally does not claim reactor-safety or physical validation.
"""

__version__ = "0.1.0"

from .ranking import MetricLimit, PhysicalEstimate, rank_all_methods, selected_is_conservatively_feasible
from .qubo import Candidate, CoreSpec, QuboModel, build_usmanov_style_qubo, enumerate_feasible_candidates

__all__ = [
    "Candidate", "CoreSpec", "MetricLimit", "PhysicalEstimate", "QuboModel",
    "build_usmanov_style_qubo", "enumerate_feasible_candidates", "rank_all_methods",
    "selected_is_conservatively_feasible",
]
