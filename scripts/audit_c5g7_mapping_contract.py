#!/usr/bin/env python3
"""Fail-closed audit of the legacy burnup-state QUBO -> physical material mapping.

A complete-looking manifest is not physical validation. This tool reports
whether required provenance fields are present and requires an explicit
independent-review record before the mapping can be marked reviewed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = (
    "required_position_map",
    "required_state_to_material_map",
    "required_material_compositions_source",
    "required_cross_section_provenance",
    "required_reference_comparison_protocol",
)


def present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def audit_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    contract = manifest.get("mapping_contract")
    if not isinstance(contract, dict):
        return {
            "schema_version": "1.0",
            "status": "NO_DEFENSIBLE_MAPPING_FOUND",
            "missing_fields": ["mapping_contract"],
            "independent_review_passed": False,
            "can_claim_physical_mapping": False,
        }
    missing = [field for field in REQUIRED_FIELDS if not present(contract.get(field))]
    review = contract.get("independent_review")
    review_ok = (
        isinstance(review, dict)
        and review.get("approved") is True
        and present(review.get("reviewer"))
        and present(review.get("review_date"))
        and present(review.get("evidence_manifest_sha256"))
    )
    if missing:
        status = "NO_DEFENSIBLE_MAPPING_FOUND"
    elif not review_ok:
        status = "MAPPING_METADATA_PRESENT_PENDING_INDEPENDENT_REVIEW"
    else:
        status = "MAPPING_REVIEW_RECORD_PRESENT_REQUIRES_SCIENTIFIC_REVIEW"
    return {
        "schema_version": "1.0",
        "status": status,
        "mapping_contract_fields_present": [field for field in REQUIRED_FIELDS if field not in missing],
        "missing_fields": missing,
        "independent_review_passed": review_ok,
        "can_claim_physical_mapping": False,
        "interpretation": (
            "This tool checks provenance completeness only. It never certifies that a material mapping "
            "is physically valid; that conclusion requires review of the source data, depletion/material "
            "definitions, cross sections, and intended physical meaning."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(f"cannot read valid manifest: {exc}")
    if not isinstance(manifest, dict):
        parser.error("manifest root must be a JSON object")
    report = audit_manifest(manifest)
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        if args.out.exists():
            parser.error(f"refusing to overwrite existing output: {args.out}")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if report["status"] != "NO_DEFENSIBLE_MAPPING_FOUND" else 2


if __name__ == "__main__":
    raise SystemExit(main())
