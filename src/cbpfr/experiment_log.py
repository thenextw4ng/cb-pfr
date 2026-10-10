"""Strict validation for optimizer experiment logs.

This validates record structure and numeric integrity only; it does not verify
that the records came from the claimed optimizer or from physical simulation.
"""
from __future__ import annotations

import json
import math
from typing import Any, Mapping


_ALLOWED_STATUSES = {"completed", "failed", "interrupted", "timeout"}


def _strict_json_value(value: Any, path: str = "parameters") -> None:
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{path} must contain strict-JSON values") from exc
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{path} must contain strict-JSON values")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} keys must be strings for strict-JSON")
            _strict_json_value(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _strict_json_value(item, f"{path}[{index}]")


def _finite_number(value: Any, field: str, *, optional: bool = False) -> float | None:
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{field} must be a finite number")
    return float(value)


def validate_optimizer_run_record(record: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        raise ValueError("run record must be an object")
    required = ("run_id", "optimizer", "optimizer_version", "seed", "parameters",
                "stopping_condition", "run_status", "candidate_records")
    for field in required:
        if field not in record:
            raise ValueError(f"missing required field: {field}")
    out = dict(record)
    for field in ("run_id", "optimizer", "optimizer_version", "stopping_condition"):
        if not isinstance(out[field], str) or not out[field].strip():
            raise ValueError(f"{field} must be a non-empty string")
        out[field] = out[field].strip()
    if isinstance(out["seed"], bool) or not isinstance(out["seed"], int) or out["seed"] < 0:
        raise ValueError("seed must be a non-negative integer")
    if not isinstance(out["parameters"], dict):
        raise ValueError("parameters must be an object")
    _strict_json_value(out["parameters"])
    if out["run_status"] not in _ALLOWED_STATUSES:
        raise ValueError(f"run_status must be one of {sorted(_ALLOWED_STATUSES)}")
    if out["run_status"] != "completed":
        reason = out.get("failure_reason")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("failure_reason is required for failed or interrupted runs")
    candidates = out["candidate_records"]
    if not isinstance(candidates, list):
        raise ValueError("candidate_records must be a list")
    candidate_ids: set[str] = set()
    ranks: set[int] = set()
    normalized_candidates = []
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            raise ValueError("each candidate record must be an object")
        item = dict(candidate)
        for field in ("candidate_id", "rank", "qubo_energy", "feasible"):
            if field not in item:
                raise ValueError(f"candidate record missing required field: {field}")
        cid = item["candidate_id"]
        if not isinstance(cid, str) or not cid.strip():
            raise ValueError("candidate_id must be a non-empty string")
        cid = cid.strip()
        if cid in candidate_ids:
            raise ValueError(f"duplicate candidate_id: {cid}")
        candidate_ids.add(cid)
        item["candidate_id"] = cid
        rank = item["rank"]
        if isinstance(rank, bool) or not isinstance(rank, int) or rank < 1:
            raise ValueError("candidate rank must be a positive integer")
        if rank in ranks:
            raise ValueError(f"duplicate candidate rank: {rank}")
        ranks.add(rank)
        item["qubo_energy"] = _finite_number(item["qubo_energy"], "qubo_energy")
        if not isinstance(item["feasible"], bool):
            raise ValueError("feasible must be boolean")
        if "objective_value" in item:
            item["objective_value"] = _finite_number(item["objective_value"], "objective_value", optional=True)
        normalized_candidates.append(item)
    out["candidate_records"] = sorted(normalized_candidates, key=lambda item: item["rank"])
    physical = out.get("physical_simulation_performed", False)
    if not isinstance(physical, bool):
        raise ValueError("physical_simulation_performed must be boolean")
    out["physical_simulation_performed"] = physical
    if "evidence_kind" in out and not isinstance(out["evidence_kind"], str):
        raise ValueError("evidence_kind must be a string when supplied")
    return out


def validate_experiment_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise ValueError("experiment payload must be an object")
    runs = payload.get("runs")
    if not isinstance(runs, list):
        raise ValueError("runs must be a list")
    normalized_runs = []
    run_ids: set[str] = set()
    for run in runs:
        normalized = validate_optimizer_run_record(run)
        run_id = normalized["run_id"]
        if run_id in run_ids:
            raise ValueError(f"run_id values must be unique: {run_id}")
        run_ids.add(run_id)
        normalized_runs.append(normalized)
    schema_version = payload.get("schema_version", "1.0")
    experiment_id = payload.get("experiment_id", "unspecified")
    if not isinstance(schema_version, str) or not schema_version.strip():
        raise ValueError("schema_version must be a non-empty string")
    if not isinstance(experiment_id, str) or not experiment_id.strip():
        raise ValueError("experiment_id must be a non-empty string")
    result = dict(payload)
    result["schema_version"] = schema_version
    result["experiment_id"] = experiment_id
    result["runs"] = normalized_runs
    return result
