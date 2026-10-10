"""Fail-closed audit for benchmark provenance and QUBO-to-physics mapping."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

_REQUIRED_TOP_LEVEL = (
    "schema_version", "benchmark_id", "benchmark_title", "benchmark_role",
    "evidence_status", "primary_sources", "declared_scope", "implementation_status",
    "mapping_contract", "explicit_nonclaims",
)


def audit_benchmark_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Report readiness gates without interpreting absent mapping evidence as success.

    This is a structural/provenance checklist, not an independent validation of
    source URLs, benchmark data, nuclear data, or physical correctness.
    """
    if not isinstance(manifest, Mapping):
        raise ValueError("benchmark manifest must be a JSON object")
    missing = [key for key in _REQUIRED_TOP_LEVEL if key not in manifest]
    if missing:
        raise ValueError(f"benchmark manifest missing required fields: {', '.join(missing)}")
    for key in ("benchmark_id", "benchmark_title", "benchmark_role", "evidence_status"):
        if not isinstance(manifest[key], str) or not manifest[key].strip():
            raise ValueError(f"{key} must be a non-empty string")
    sources = manifest["primary_sources"]
    if not isinstance(sources, list) or not sources:
        raise ValueError("primary_sources must be a non-empty array")
    for index, source in enumerate(sources):
        if not isinstance(source, Mapping):
            raise ValueError(f"primary_sources[{index}] must be an object")
        for key in ("organization", "title", "url", "source_role"):
            if not isinstance(source.get(key), str) or not source[key].strip():
                raise ValueError(f"primary_sources[{index}].{key} must be a non-empty string")
        if not source["url"].startswith("https://"):
            raise ValueError(f"primary_sources[{index}].url must use HTTPS")

    scope = manifest["declared_scope"]
    implementation = manifest["implementation_status"]
    mapping = manifest["mapping_contract"]
    if not isinstance(scope, Mapping) or not isinstance(implementation, Mapping) or not isinstance(mapping, Mapping):
        raise ValueError("declared_scope, implementation_status, and mapping_contract must be objects")

    blockers: list[str] = []
    for key in (
        "model_inputs_bundled", "cross_sections_bundled",
        "reference_values_transcribed_and_reviewed", "openmc_baseline_run_verified",
    ):
        if implementation.get(key) is not True:
            blockers.append(f"implementation_status.{key} is not true")
    for key in (
        "required_position_map", "required_state_to_material_map",
        "required_material_compositions_source", "required_cross_section_provenance",
        "required_reference_comparison_protocol",
    ):
        value = mapping.get(key)
        if value is None or value == {} or value == [] or value == "":
            blockers.append(f"mapping_contract.{key} is missing")
    if implementation.get("candidate_mapping_status") != "validated":
        blockers.append("implementation_status.candidate_mapping_status is not validated")
    if not scope.get("boundary_conditions"):
        blockers.append("declared_scope.boundary_conditions is not specified")
    if not scope.get("material_compositions"):
        blockers.append("declared_scope.material_compositions is not specified")
    if not isinstance(manifest["explicit_nonclaims"], list) or not manifest["explicit_nonclaims"]:
        raise ValueError("explicit_nonclaims must be a non-empty array")

    return {
        "benchmark_id": manifest["benchmark_id"],
        "evidence_status": manifest["evidence_status"],
        "status": "ready_for_baseline_run" if not blockers else "blocked",
        "blockers": blockers,
        "primary_source_count": len(sources),
        "claim_boundary": (
            "Structural gate status only. A ready manifest is not proof of source accuracy, "
            "convergence, physical correctness, or validation."
        ),
    }
