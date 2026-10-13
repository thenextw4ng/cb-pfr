"""Versioned, provenance-aware contract for optimizer-to-physics experiments.

This module connects candidate-generation/QUBO outputs to CB-PFR without
silently converting one formulation into another or presenting synthetic data
as simulator output. It is an orchestration/data-contract layer; it does not
run OpenMC or establish physical validity.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
import re
from typing import Any, Mapping, Sequence

from .qubo import Candidate, QuboModel
from .ranking import MetricLimit, PhysicalEstimate, RankedCandidate
from .integration import rank_candidate_batch, ranking_to_records

SCHEMA_VERSION = "cbpfr.experiment.v1"
SOURCE_KINDS = {
    "synthetic",
    "mock",
    "openmc_statepoint",
    "experimental_measurement",
    "benchmark_reference",
}
OPTIMIZER_CLASSES = {
    "classical_exact",
    "classical_heuristic",
    "classical_simulated_annealing",
    "classical_simulated_quantum_annealing",
    "quantum_annealer",
    "external",
}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ExperimentContractError(ValueError):
    """Raised when experiment inputs are ambiguous or internally inconsistent."""


@dataclass(frozen=True)
class ExperimentSpec:
    """Identity of a run; formulation identity is explicit and never inferred."""

    experiment_id: str
    formulation_id: str
    candidate_encoding_id: str
    optimizer_name: str
    optimizer_class: str
    code_revision: str
    notes: str = ""

    def __post_init__(self) -> None:
        for name in ("experiment_id", "formulation_id", "candidate_encoding_id",
                     "optimizer_name", "code_revision"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ExperimentContractError(f"{name} must be a non-empty string")
        if self.optimizer_class not in OPTIMIZER_CLASSES:
            raise ExperimentContractError(
                f"optimizer_class must be one of {sorted(OPTIMIZER_CLASSES)}"
            )


@dataclass(frozen=True)
class EvaluationProvenance:
    """Traceability fields for one candidate's downstream evaluation."""

    source_kind: str
    source_reference: str
    source_sha256: str | None = None
    model_id: str | None = None
    model_revision: str | None = None
    seed: int | None = None
    settings: Mapping[str, Any] = field(default_factory=dict)
    uncertainty_note: str = "unspecified"

    def __post_init__(self) -> None:
        if self.source_kind not in SOURCE_KINDS:
            raise ExperimentContractError(
                f"unsupported source_kind {self.source_kind!r}; expected one of {sorted(SOURCE_KINDS)}"
            )
        if not isinstance(self.source_reference, str) or not self.source_reference.strip():
            raise ExperimentContractError("source_reference must be a non-empty string")
        if self.source_sha256 is not None and not _SHA256.fullmatch(self.source_sha256):
            raise ExperimentContractError("source_sha256 must be a 64-character lowercase SHA-256")
        if self.seed is not None and (isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0):
            raise ExperimentContractError("seed must be a nonnegative integer when supplied")
        if self.source_kind == "openmc_statepoint":
            if not self.source_sha256:
                raise ExperimentContractError("OpenMC statepoint provenance requires source_sha256")
            if not self.model_id or not self.model_revision:
                raise ExperimentContractError("OpenMC statepoint provenance requires model_id and model_revision")
            if self.seed is None:
                raise ExperimentContractError("OpenMC statepoint provenance requires an explicit seed")


@dataclass(frozen=True)
class MetricObservation:
    """A metric mean and uncertainty with explicit units and uncertainty semantics."""

    mean: float
    uncertainty: float
    units: str
    uncertainty_kind: str

    def __post_init__(self) -> None:
        if not math.isfinite(self.mean):
            raise ExperimentContractError("metric mean must be finite")
        if not math.isfinite(self.uncertainty) or self.uncertainty < 0:
            raise ExperimentContractError("metric uncertainty must be finite and nonnegative")
        if not isinstance(self.units, str) or not self.units.strip() or self.units == "unspecified":
            raise ExperimentContractError("metric units must be explicit")
        if not isinstance(self.uncertainty_kind, str) or not self.uncertainty_kind.strip() or self.uncertainty_kind == "unspecified":
            raise ExperimentContractError("uncertainty_kind must be explicit")


@dataclass(frozen=True)
class CandidateEvaluation:
    candidate_id: str
    metrics: Mapping[str, MetricObservation]
    provenance: EvaluationProvenance

    def __post_init__(self) -> None:
        if not isinstance(self.candidate_id, str) or not self.candidate_id.strip():
            raise ExperimentContractError("candidate_id must be a non-empty string")
        if not self.metrics:
            raise ExperimentContractError(f"{self.candidate_id}: at least one metric observation is required")
        if any(not isinstance(name, str) or not name.strip() for name in self.metrics):
            raise ExperimentContractError("metric names must be non-empty strings")
        if any(not isinstance(value, MetricObservation) for value in self.metrics.values()):
            raise ExperimentContractError("metrics values must be MetricObservation instances")


def _json_safe(value: Any) -> Any:
    """Convert nested dataclasses/mappings into strict JSON-compatible values."""
    if hasattr(value, "__dataclass_fields__"):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise ExperimentContractError(f"unsupported JSON value type: {type(value).__name__}")


def _to_estimates(
    candidates: Sequence[Candidate],
    evaluations: Sequence[CandidateEvaluation],
    limits: Sequence[MetricLimit],
) -> tuple[dict[str, PhysicalEstimate], dict[str, CandidateEvaluation], str]:
    candidate_ids = [candidate.candidate_id for candidate in candidates]
    if not candidate_ids or any(not item.strip() for item in candidate_ids):
        raise ExperimentContractError("candidate batch must have non-empty IDs")
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ExperimentContractError("candidate IDs must be unique")
    if not evaluations:
        raise ExperimentContractError("evaluation batch cannot be empty")
    eval_ids = [item.candidate_id for item in evaluations]
    if len(eval_ids) != len(set(eval_ids)):
        raise ExperimentContractError("duplicate evaluation records for a candidate are not allowed")
    if set(eval_ids) != set(candidate_ids):
        missing = sorted(set(candidate_ids) - set(eval_ids))
        unexpected = sorted(set(eval_ids) - set(candidate_ids))
        raise ExperimentContractError(
            f"candidate/evaluation IDs must match exactly; missing={missing}, unexpected={unexpected}"
        )
    if not limits:
        raise ExperimentContractError("at least one metric limit is required")
    metric_names = [metric.name for metric in limits]
    if len(metric_names) != len(set(metric_names)):
        raise ExperimentContractError("metric limit names must be unique")
    expected_metrics = set(metric_names)
    if any(metric.units == "unspecified" for metric in limits):
        raise ExperimentContractError("all metric limits must declare units before ranking")
    source_kinds = {item.provenance.source_kind for item in evaluations}
    if len(source_kinds) != 1:
        raise ExperimentContractError(
            "do not mix source kinds in one comparison; analyze synthetic, simulated, and experimental evidence separately"
        )
    evaluation_by_id = {item.candidate_id: item for item in evaluations}
    estimates: dict[str, PhysicalEstimate] = {}
    for candidate_id in candidate_ids:
        evaluation = evaluation_by_id[candidate_id]
        if set(evaluation.metrics) != expected_metrics:
            raise ExperimentContractError(
                f"{candidate_id}: metric names must exactly match limits; "
                f"missing={sorted(expected_metrics - set(evaluation.metrics))}, "
                f"unexpected={sorted(set(evaluation.metrics) - expected_metrics)}"
            )
        values: dict[str, tuple[float, float]] = {}
        for limit in limits:
            observation = evaluation.metrics[limit.name]
            if observation.units != limit.units:
                raise ExperimentContractError(
                    f"{candidate_id}/{limit.name}: units {observation.units!r} do not match limit units {limit.units!r}"
                )
            if observation.uncertainty_kind != limit.uncertainty_kind:
                raise ExperimentContractError(
                    f"{candidate_id}/{limit.name}: uncertainty kind {observation.uncertainty_kind!r} "
                    f"does not match declared limit kind {limit.uncertainty_kind!r}"
                )
            values[limit.name] = (observation.mean, observation.uncertainty)
        estimates[candidate_id] = PhysicalEstimate(candidate_id, values)
    return estimates, evaluation_by_id, next(iter(source_kinds))


def run_ranked_experiment(
    *,
    spec: ExperimentSpec,
    model: QuboModel,
    candidates: Sequence[Candidate],
    evaluations: Sequence[CandidateEvaluation],
    metrics: Sequence[MetricLimit],
    uniform_margins: Mapping[str, float],
) -> dict[str, Any]:
    """Validate the full candidate -> evaluation -> CB-PFR contract and return an audit bundle.

    All candidates must have exactly one complete evaluation record. A source kind
    cannot be mixed within a comparison. The function does not claim the supplied
    observations are physically valid; provenance and the caller's scientific
    acceptance protocol remain essential.
    """
    estimates, evaluation_by_id, source_kind = _to_estimates(candidates, evaluations, metrics)
    rankings = rank_candidate_batch(model, candidates, estimates, metrics, uniform_margins)
    ranking_records = ranking_to_records(
        rankings,
        data_kind="synthetic" if source_kind in {"synthetic", "mock"} else "physical",
    )
    for record in ranking_records:
        provenance = evaluation_by_id[record["candidate_id"]].provenance
        record["source_kind"] = source_kind
        record["evaluation_provenance"] = _json_safe(provenance)
        record["physical_simulation_performed"] = source_kind == "openmc_statepoint"
        record["experimental_measurement_used"] = source_kind == "experimental_measurement"
        record["benchmark_reference_used"] = source_kind == "benchmark_reference"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "experiment": _json_safe(spec),
        "formulation": {
            "formulation_id": spec.formulation_id,
            "candidate_encoding_id": spec.candidate_encoding_id,
            "qubo_model_name": model.spec.name,
            "qubo_variable_count": model.variable_count,
            "candidate_count": len(candidates),
            "qubo_feasible_count": sum(model.is_feasible(candidate.vector) for candidate in candidates),
        },
        "evidence": {
            "source_kind": source_kind,
            "source_record_count": len(evaluations),
            "physical_simulation_performed": source_kind == "openmc_statepoint",
            "physical_validation_established": False,
            "note": (
                "Pipeline output does not itself establish model validity, benchmark acceptance, "
                "physical superiority, reactor safety, or quantum advantage."
            ),
        },
        "metric_limits": [_json_safe(metric) for metric in metrics],
        "evaluation_records": [
            {
                "candidate_id": evaluation.candidate_id,
                "metrics": _json_safe(evaluation.metrics),
                "provenance": _json_safe(evaluation.provenance),
            }
            for evaluation in evaluations
        ],
        "rankings": ranking_records,
    }
    # Strict JSON serialization catches accidental non-serializable metadata.
    json.dumps(payload, allow_nan=False, sort_keys=True)
    return payload


def bundle_sha256(bundle: Mapping[str, Any]) -> str:
    """Return a stable SHA-256 for a JSON-compatible bundle (excluding no fields)."""
    encoded = json.dumps(bundle, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
