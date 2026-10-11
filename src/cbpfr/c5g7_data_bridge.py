"""External-data bridge for a C5G7 2x2 UO2/MOX layout study.

This is deliberately separate from the legacy Usmanov burnup-state QUBO.
It only ranks layouts when source-attributed, layout-matched measurements exist.
"""
from __future__ import annotations

from dataclasses import dataclass
import csv
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

POSITIONS = ("p00", "p01", "p10", "p11")
MATERIALS = ("UO2", "MOX")
EXPECTED_CANDIDATES = tuple(
    "c5g7-2x2-" + "".join("M" if mask & (1 << i) else "U" for i in range(4))
    for mask in range(16) if mask.bit_count() == 2
)
REQUIRED_COLUMNS = (
    "candidate_id", "benchmark_case", "source_url", "source_kind",
    "keff_mean", "keff_uncertainty", "keff_uncertainty_kind",
)


class ExternalDataError(ValueError):
    """Raised when externally sourced C5G7 data are not auditable or well formed."""


@dataclass(frozen=True)
class LayoutResult:
    candidate_id: str
    benchmark_case: str
    source_url: str
    source_kind: str
    keff_mean: float
    keff_uncertainty: float
    keff_uncertainty_kind: str
    fission_rate_peaking_factor: float | None = None
    fission_rate_peaking_uncertainty: float | None = None
    configuration_hash: str | None = None
    notes: str = ""


@dataclass(frozen=True)
class CandidateAssessment:
    candidate_id: str
    observed_metrics: Mapping[str, tuple[float, float]]
    aggregate_violation: float
    feasible_under_declared_limits: bool
    missing_metrics: tuple[str, ...]


def enumerate_layouts() -> tuple[dict[str, str], ...]:
    """Return all six layouts with exactly two MOX and two UO2 assemblies."""
    layouts = []
    for mox_positions in __import__("itertools").combinations(POSITIONS, 2):
        mox = set(mox_positions)
        layout = {position: ("MOX" if position in mox else "UO2") for position in POSITIONS}
        signature = "".join("M" if layout[position] == "MOX" else "U" for position in POSITIONS)
        layouts.append({"candidate_id": f"c5g7-2x2-{signature}", **layout})
    return tuple(layouts)


def load_external_results(path: str | Path) -> dict[str, LayoutResult]:
    """Load one source-attributed aggregate row per layout; never infer missing values."""
    path = Path(path)
    if not path.is_file():
        raise ExternalDataError(f"result CSV not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or ())
        missing = sorted(set(REQUIRED_COLUMNS) - columns)
        if missing:
            raise ExternalDataError(f"CSV is missing required columns: {', '.join(missing)}")
        results: dict[str, LayoutResult] = {}
        for line_number, row in enumerate(reader, start=2):
            candidate_id = (row.get("candidate_id") or "").strip()
            if candidate_id not in EXPECTED_CANDIDATES:
                raise ExternalDataError(f"line {line_number}: unknown candidate_id {candidate_id!r}")
            if candidate_id in results:
                raise ExternalDataError(
                    f"line {line_number}: duplicate candidate {candidate_id}; provide one documented aggregate row per layout"
                )
            source_url = (row.get("source_url") or "").strip()
            source_kind = (row.get("source_kind") or "").strip()
            benchmark_case = (row.get("benchmark_case") or "").strip()
            uncertainty_kind = (row.get("keff_uncertainty_kind") or "").strip()
            if not source_url.startswith(("https://", "http://")):
                raise ExternalDataError(f"line {line_number}: source_url must be an HTTP(S) citation")
            if not source_kind or not benchmark_case or not uncertainty_kind:
                raise ExternalDataError(f"line {line_number}: source_kind, benchmark_case, and uncertainty kind are required")
            try:
                keff = float(row["keff_mean"])
                keff_u = float(row["keff_uncertainty"])
            except (TypeError, ValueError) as exc:
                raise ExternalDataError(f"line {line_number}: keff mean/uncertainty must be numeric") from exc
            if not math.isfinite(keff) or not math.isfinite(keff_u) or keff_u < 0:
                raise ExternalDataError(f"line {line_number}: keff mean must be finite and uncertainty nonnegative")
            peak = _optional_float(row.get("fission_rate_peaking_factor"), line_number, "fission_rate_peaking_factor")
            peak_u = _optional_float(row.get("fission_rate_peaking_uncertainty"), line_number, "fission_rate_peaking_uncertainty")
            if peak_u is not None and peak_u < 0:
                raise ExternalDataError(f"line {line_number}: peaking uncertainty cannot be negative")
            results[candidate_id] = LayoutResult(
                candidate_id=candidate_id, benchmark_case=benchmark_case,
                source_url=source_url, source_kind=source_kind,
                keff_mean=keff, keff_uncertainty=keff_u,
                keff_uncertainty_kind=uncertainty_kind,
                fission_rate_peaking_factor=peak,
                fission_rate_peaking_uncertainty=peak_u,
                configuration_hash=(row.get("configuration_hash") or "").strip() or None,
                notes=(row.get("notes") or "").strip(),
            )
    benchmark_cases = {item.benchmark_case for item in results.values()}
    if len(benchmark_cases) > 1:
        raise ExternalDataError(
            "rows use different benchmark_case labels; do not combine incomparable cases in one ranking"
        )
    return results


def _optional_float(value: str | None, line_number: int, name: str) -> float | None:
    if value is None or not value.strip():
        return None
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ExternalDataError(f"line {line_number}: {name} must be numeric when supplied") from exc
    if not math.isfinite(parsed):
        raise ExternalDataError(f"line {line_number}: {name} must be finite")
    return parsed


def coverage_report(results: Mapping[str, LayoutResult]) -> dict[str, Any]:
    expected = set(EXPECTED_CANDIDATES)
    supplied = set(results)
    missing = sorted(expected - supplied)
    return {
        "status": "complete" if not missing else "incomplete_external_coverage",
        "expected_candidate_count": len(expected),
        "observed_candidate_count": len(supplied),
        "missing_candidate_ids": missing,
        "physical_ranking_allowed": not missing,
        "note": (
            "All six layouts have source-attributed rows."
            if not missing else
            "Do not rank all layouts: external data do not cover every candidate. Missing candidates are not imputed."
        ),
    }


def build_one_hot_selection_qubo(
    results: Mapping[str, LayoutResult],
    *,
    objective_column: str,
    direction: str = "min",
) -> dict[str, Any]:
    """Build a one-hot QUBO over the six layout candidates using a declared observed metric.

    This is a C5G7 layout-selector QUBO, not the legacy Usmanov burnup-state QUBO.
    A complete six-candidate dataset is required. The objective metric is normalized
    to [0,1]; the one-hot penalty is 2, so infeasible multi-hot/zero-hot assignments
    cannot beat a feasible candidate under this bounded objective.
    """
    report = coverage_report(results)
    if report["status"] != "complete":
        raise ExternalDataError("cannot build a physical-data objective QUBO: " + report["note"])
    if direction not in {"min", "max"}:
        raise ExternalDataError("direction must be 'min' or 'max'")
    allowed = {"keff_mean", "fission_rate_peaking_factor"}
    if objective_column not in allowed:
        raise ExternalDataError(f"objective_column must be one of {sorted(allowed)}")
    values = []
    for candidate_id in EXPECTED_CANDIDATES:
        row = results[candidate_id]
        value = getattr(row, objective_column)
        if value is None:
            raise ExternalDataError(f"{candidate_id} has no value for objective {objective_column}")
        values.append(float(value))
    signed = values if direction == "min" else [-v for v in values]
    low, high = min(signed), max(signed)
    normalized = [0.0 if high == low else (v - low) / (high - low) for v in signed]
    penalty = 2.0
    # E(y) = sum_i normalized_i*y_i + P*(sum_i y_i - 1)^2
    # Q diagonal = normalized_i - P; Q off-diagonal = 2P; offset = P.
    q = []
    for i, objective in enumerate(normalized):
        row = []
        for j in range(len(normalized)):
            if i == j:
                row.append(objective - penalty)
            elif i < j:
                row.append(2.0 * penalty)
            else:
                row.append(0.0)
        q.append(row)
    return {
        "formulation": "C5G7_external_data_one_hot_layout_selector",
        "not_the_legacy_usmanov_burnup_qubo": True,
        "objective_column": objective_column,
        "direction": direction,
        "normalization": {"raw_min": min(values), "raw_max": max(values), "mapping": "linear to [0,1]; constant metric maps to 0"},
        "candidate_ids": list(EXPECTED_CANDIDATES),
        "raw_objective_values": values,
        "normalized_objective_values": normalized,
        "qubo_matrix_upper_triangle": q,
        "constant_offset": penalty,
        "one_hot_penalty": penalty,
        "minimum_energy_candidate_id": EXPECTED_CANDIDATES[normalized.index(min(normalized))],
        "evidence_status": "data-derived only; validity depends on source comparability and declared metric",
    }


def assess_cbpfr_limits(
    results: Mapping[str, LayoutResult],
    metrics: Sequence[Mapping[str, Any]],
) -> tuple[CandidateAssessment, ...]:
    """Apply CB-PFR-style uncertainty-expanded limits supplied explicitly by the researcher.

    Each metric config requires name, value_attribute, uncertainty_attribute, scale, and
    optional lower/upper/z/weight. This routine does not invent acceptance limits.
    """
    if not metrics:
        raise ExternalDataError("at least one explicitly configured physical metric limit is required")
    assessments = []
    for candidate_id in EXPECTED_CANDIDATES:
        row = results.get(candidate_id)
        observed: dict[str, tuple[float, float]] = {}
        missing = []
        aggregate = 0.0
        passes = True
        for metric in metrics:
            name = str(metric["name"])
            if metric.get("lower") is None and metric.get("upper") is None:
                raise ExternalDataError(f"metric {name}: at least one explicit lower/upper limit is required")
            value_attr = str(metric["value_attribute"])
            uncertainty_attr = str(metric["uncertainty_attribute"])
            value = None if row is None else getattr(row, value_attr, None)
            uncertainty = None if row is None else getattr(row, uncertainty_attr, None)
            if value is None or uncertainty is None:
                missing.append(name)
                passes = False
                aggregate = math.inf
                continue
            value, uncertainty = float(value), float(uncertainty)
            if not math.isfinite(value) or not math.isfinite(uncertainty) or uncertainty < 0:
                raise ExternalDataError(f"{candidate_id}: invalid metric data for {name}")
            observed[name] = (value, uncertainty)
            z = float(metric.get("z", 0.0))
            scale = float(metric["scale"])
            weight = float(metric.get("weight", 1.0))
            if z < 0 or scale <= 0 or weight < 0:
                raise ExternalDataError(f"metric {name}: z must be >=0, scale >0, weight >=0")
            lower_bound, upper_bound = value - z * uncertainty, value + z * uncertainty
            violation = 0.0
            lower, upper = metric.get("lower"), metric.get("upper")
            if lower is not None:
                violation += max(0.0, float(lower) - lower_bound)
            if upper is not None:
                violation += max(0.0, upper_bound - float(upper))
            aggregate += weight * violation / scale
            if violation > 0:
                passes = False
        assessments.append(CandidateAssessment(candidate_id, observed, aggregate, passes, tuple(missing)))
    return tuple(assessments)
