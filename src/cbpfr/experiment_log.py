"""Validation helpers for auditable repeated optimizer-run records."""
from __future__ import annotations

import json
import math
from typing import Any, Mapping

REQUIRED_RUN_FIELDS = (
    "run_id", "optimizer", "optimizer_version", "seed", "parameters",
    "stopping_condition", "run_status", "candidate_records",
)


def validate_optimizer_run_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one run's provenance and candidate records.

    Candidate vectors are stable binary identities; objective values are kept
    separate from QUBO energy. This validates structure, not provenance truth.
    """
    if not isinstance(record, Mapping):
        raise ValueError("run record must be an object")
    missing = [field for field in REQUIRED_RUN_FIELDS if field not in record]
    if missing:
        raise ValueError(f"run record missing required fields: {', '.join(missing)}")
    for field in ("run_id", "optimizer", "optimizer_version", "stopping_condition"):
        if not isinstance(record[field], str) or not record[field].strip():
            raise ValueError(f"{field} must be a non-empty string")
    seed = record["seed"]
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
        raise ValueError("seed must be an integer or null when unseeded")
    if not isinstance(record["parameters"], Mapping):
        raise ValueError("parameters must be an object")
    try:
        json.dumps(record["parameters"], allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"parameters must be strict-JSON serializable: {exc}") from exc
    status = record["run_status"]
    if status not in {"completed", "failed", "cancelled", "timeout"}:
        raise ValueError("run_status must be completed, failed, cancelled, or timeout")
    candidates = record["candidate_records"]
    if not isinstance(candidates, list):
        raise ValueError("candidate_records must be an array")
    if status == "completed" and not candidates:
        raise ValueError("completed run must contain at least one candidate record")
    if status != "completed" and not (isinstance(record.get("failure_reason"), str) and record["failure_reason"].strip()):
        raise ValueError("non-completed run must include a non-empty failure_reason")

    ids: set[str] = set()
    vectors: set[tuple[int, ...]] = set()
    ranks: set[int] = set()
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, Mapping):
            raise ValueError(f"candidate_records[{index}] must be an object")
        for field in ("candidate_id", "candidate_vector", "rank", "qubo_energy", "feasible"):
            if field not in candidate:
                raise ValueError(f"candidate_records[{index}] missing {field}")
        cid = candidate["candidate_id"]
        if not isinstance(cid, str) or not cid.strip():
            raise ValueError(f"candidate_records[{index}].candidate_id must be a non-empty string")
        if cid in ids:
            raise ValueError(f"duplicate candidate_id in run: {cid}")
        ids.add(cid)
        vector = candidate["candidate_vector"]
        if not isinstance(vector, list) or not vector:
            raise ValueError(f"candidate_records[{index}].candidate_vector must be a non-empty array")
        if any(isinstance(v, bool) or not isinstance(v, int) or v not in (0, 1) for v in vector):
            raise ValueError(f"candidate_records[{index}].candidate_vector must contain only integer 0/1 values")
        vector_key = tuple(vector)
        if vector_key in vectors:
            raise ValueError(f"duplicate candidate vector in run: {cid}")
        vectors.add(vector_key)
        rank = candidate["rank"]
        if isinstance(rank, bool) or not isinstance(rank, int) or rank < 1:
            raise ValueError(f"candidate_records[{index}].rank must be a positive integer")
        if rank in ranks:
            raise ValueError(f"duplicate candidate rank in run: {rank}")
        ranks.add(rank)
        energy = candidate["qubo_energy"]
        if isinstance(energy, bool) or not isinstance(energy, (int, float)) or not math.isfinite(energy):
            raise ValueError(f"candidate_records[{index}].qubo_energy must be finite")
        if not isinstance(candidate["feasible"], bool):
            raise ValueError(f"candidate_records[{index}].feasible must be boolean")
        objective = candidate.get("objective_value")
        if objective is not None and (
            isinstance(objective, bool) or not isinstance(objective, (int, float)) or not math.isfinite(objective)
        ):
            raise ValueError(f"candidate_records[{index}].objective_value must be finite or null")

    normalized = dict(record)
    normalized["candidate_records"] = [dict(candidate) for candidate in candidates]
    normalized.setdefault("failure_reason", None)
    normalized.setdefault("evidence_kind", "unspecified")
    normalized.setdefault("physical_simulation_performed", False)
    if not isinstance(normalized["evidence_kind"], str) or not normalized["evidence_kind"].strip():
        raise ValueError("evidence_kind must be a non-empty string")
    if not isinstance(normalized["physical_simulation_performed"], bool):
        raise ValueError("physical_simulation_performed must be boolean")
    return normalized


def validate_experiment_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a collection of run records and require unique run IDs."""
    if not isinstance(payload, Mapping):
        raise ValueError("experiment input must be a JSON object")
    runs = payload.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("experiment input must contain a non-empty runs array")
    normalized = [validate_optimizer_run_record(run) for run in runs]
    ids = [run["run_id"] for run in normalized]
    if len(set(ids)) != len(ids):
        raise ValueError("run_id values must be unique")
    experiment_id = payload.get("experiment_id", "unspecified")
    if not isinstance(experiment_id, str) or not experiment_id.strip():
        raise ValueError("experiment_id must be a non-empty string")
    return {
        "schema_version": str(payload.get("schema_version", "1.0")),
        "experiment_id": experiment_id,
        "experiment_description": payload.get("experiment_description", ""),
        "runs": normalized,
    }
