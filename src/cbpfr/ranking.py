"""Confidence-Bounded Physical Feasibility Ranking (CB-PFR).

This module implements the working paper's operational rule. Its bounds are
not labeled confidence intervals, safety margins, or reactor safety evidence.
The caller supplies units, acceptance limits, uncertainty meanings, and all
metric values explicitly.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Mapping, Sequence
from .qubo import Candidate, QuboModel

@dataclass(frozen=True)
class MetricLimit:
    name: str
    lower: float | None = None
    upper: float | None = None
    z: float = 0.0
    scale: float = 1.0
    weight: float = 1.0
    uncertainty_kind: str = "unspecified"
    units: str = "unspecified"
    bound_kind: str = "operational_heuristic"
    def __post_init__(self) -> None:
        if self.lower is None and self.upper is None:
            raise ValueError(f"metric {self.name} needs a lower and/or upper limit")
        if self.lower is not None and self.upper is not None and self.lower > self.upper:
            raise ValueError(f"metric {self.name} has lower limit above upper limit")
        if self.z < 0 or self.scale <= 0 or self.weight < 0:
            raise ValueError(f"metric {self.name} has invalid z, scale, or weight")
        if not self.uncertainty_kind.strip():
            raise ValueError(f"metric {self.name} must identify uncertainty_kind")
        if self.bound_kind not in {"operational_heuristic", "known_normal_one_sided"}:
            raise ValueError(f"metric {self.name} has unsupported bound_kind; it must not imply an untested confidence claim")

@dataclass(frozen=True)
class PhysicalEstimate:
    candidate_id: str
    values: Mapping[str, tuple[float, float]]

@dataclass(frozen=True)
class MetricAssessment:
    name: str
    mean: float | None
    uncertainty: float | None
    lower_bound: float | None
    upper_bound: float | None
    violation: float
    normalized_violation: float
    passes: bool
    status: str

@dataclass(frozen=True)
class PhysicalAssessment:
    metric_assessments: tuple[MetricAssessment, ...]
    indicator: int
    aggregate_violation: float

@dataclass(frozen=True)
class RankedCandidate:
    method: str
    candidate: Candidate
    input_index: int
    qubo_indicator: int
    qubo_energy: float
    physical: PhysicalAssessment | None
    ranking_key: tuple[float | int, ...]

def _assessment_for_metric(metric: MetricLimit, supplied: tuple[float, float] | None, width_override: float | None) -> MetricAssessment:
    if supplied is None:
        return MetricAssessment(metric.name, None, None, None, None, math.inf, math.inf, False, "missing")
    mean, uncertainty = supplied
    if not (math.isfinite(mean) and math.isfinite(uncertainty)) or uncertainty < 0:
        return MetricAssessment(metric.name, mean, uncertainty, None, None, math.inf, math.inf, False, "nonfinite_or_negative")
    width = metric.z * uncertainty if width_override is None else width_override
    if not math.isfinite(width) or width < 0:
        return MetricAssessment(metric.name, mean, uncertainty, None, None, math.inf, math.inf, False, "invalid_width")
    lower_bound, upper_bound = mean - width, mean + width
    violation = 0.0
    if metric.lower is not None:
        violation += max(0.0, metric.lower - lower_bound)
    if metric.upper is not None:
        violation += max(0.0, upper_bound - metric.upper)
    return MetricAssessment(metric.name, mean, uncertainty, lower_bound, upper_bound, violation, violation / metric.scale, violation == 0.0, "evaluated")

def assess_physical(metrics: Sequence[MetricLimit], estimate: PhysicalEstimate | None, *, uniform_margins: Mapping[str, float] | None = None) -> PhysicalAssessment:
    assessments = []
    for metric in metrics:
        width = None if uniform_margins is None else uniform_margins.get(metric.name)
        assessments.append(_assessment_for_metric(metric, None if estimate is None else estimate.values.get(metric.name), width))
    indicator = int(any(not assessment.passes for assessment in assessments))
    aggregate = sum(metric.weight * assessment.normalized_violation for metric, assessment in zip(metrics, assessments))
    return PhysicalAssessment(tuple(assessments), indicator, aggregate)

def _rank(method: str, model: QuboModel, candidates: Sequence[Candidate], estimates: Mapping[str, PhysicalEstimate], metrics: Sequence[MetricLimit], *, mode: str, uniform_margins: Mapping[str, float] | None = None) -> list[RankedCandidate]:
    ranked = []
    for index, candidate in enumerate(candidates):
        qubo_indicator = int(not model.is_feasible(candidate.vector))
        energy = model.energy(candidate.vector)
        if mode == "qubo":
            physical = None
            key = (qubo_indicator, energy, index)
        else:
            if mode == "point":
                margins = {metric.name: 0.0 for metric in metrics}
            elif mode == "uniform":
                margins = uniform_margins
            elif mode == "cbpfr":
                margins = None
            else:
                raise ValueError(f"unknown ranking mode: {mode}")
            physical = assess_physical(metrics, estimates.get(candidate.candidate_id), uniform_margins=margins)
            key = (qubo_indicator, physical.indicator, physical.aggregate_violation, energy, index)
        ranked.append(RankedCandidate(method, candidate, index, qubo_indicator, energy, physical, key))
    return sorted(ranked, key=lambda item: item.ranking_key)

def rank_all_methods(model: QuboModel, candidates: Sequence[Candidate], estimates: Mapping[str, PhysicalEstimate], metrics: Sequence[MetricLimit], uniform_margins: Mapping[str, float]) -> dict[str, list[RankedCandidate]]:
    if not candidates:
        raise ValueError("candidate pool cannot be empty")
    if not metrics:
        raise ValueError("at least one physical metric must be declared")
    expected = {metric.name for metric in metrics}
    if set(uniform_margins) != expected or any(value < 0 for value in uniform_margins.values()):
        raise ValueError("uniform margins must give one nonnegative value for every metric")
    return {
        "qubo_only": _rank("qubo_only", model, candidates, estimates, metrics, mode="qubo"),
        "point_estimate": _rank("point_estimate", model, candidates, estimates, metrics, mode="point"),
        "cb_pfr": _rank("cb_pfr", model, candidates, estimates, metrics, mode="cbpfr"),
        "uniform_margin": _rank("uniform_margin", model, candidates, estimates, metrics, mode="uniform", uniform_margins=uniform_margins),
    }

def selected_is_conservatively_feasible(result: RankedCandidate) -> bool:
    return result.qubo_indicator == 0 and result.physical is not None and result.physical.indicator == 0
