#!/usr/bin/env python3
"""Audit exact C5G7 input-file hashes against a model identity manifest.

This verifies provenance consistency only. It does not certify physical fidelity
to the OECD/NEA benchmark or replace independent specification review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_GROUPS = [1e-5, 0.0635, 10.0, 100.0, 1000.0, 500000.0, 1000000.0, 20000000.0]
FILE_KEYS = {
    "geometry_xml_sha256": "geometry_xml",
    "materials_xml_sha256": "materials_xml",
    "settings_xml_sha256": "settings_xml",
    "mgxs_hdf5_sha256": "mgxs_hdf5",
    "source_builder_sha256": "source_builder",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit_manifest(manifest_path: Path, inputs: dict[str, Path]) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    model = manifest.get("model", {})
    generated = manifest.get("generated_inputs", {})
    checks: dict[str, bool] = {}
    observed_hashes: dict[str, str] = {}
    errors: list[str] = []

    if manifest.get("schema_version") != "1.0":
        errors.append("unsupported or missing manifest schema_version")
    if model.get("upstream_commit_expected") != "ba41bee54320ada0b4ac39a0dd2ca3c1d090a450":
        errors.append("manifest upstream commit differs from the pinned audited source")
    if model.get("energy_group_boundaries_eV_expected") != EXPECTED_GROUPS:
        errors.append("manifest energy boundaries differ from the declared standard C5G7 group structure")

    for hash_key, arg_key in FILE_KEYS.items():
        path = inputs.get(arg_key)
        expected = generated.get(hash_key)
        if path is None or not path.is_file():
            checks[f"{arg_key}_present"] = False
            errors.append(f"missing exact input file for {arg_key}")
            continue
        observed = sha256(path)
        observed_hashes[hash_key] = observed
        valid_expected = isinstance(expected, str) and len(expected) == 64 and all(
            char in "0123456789abcdef" for char in expected
        )
        checks[f"{arg_key}_hash_matches_manifest"] = valid_expected and observed == expected
        if not checks[f"{arg_key}_hash_matches_manifest"]:
            errors.append(f"{arg_key} SHA-256 missing, malformed, or mismatched")

    review = manifest.get("review", {})
    independently_signed = review.get("independent_signoff") is True
    reviewer_fields_present = all(
        isinstance(review.get(key), str) and review[key].strip()
        for key in ("reviewer", "review_date", "primary_specification_reference")
    )
    review_complete = independently_signed and reviewer_fields_present
    checks["independent_model_identity_review_signed"] = review_complete

    # This tool does not claim that hashes establish physics. Even all matching
    # hashes leave physical review as a separate gate.
    provenance_pass = not errors and all(
        value for key, value in checks.items() if key != "independent_model_identity_review_signed"
    )
    if not provenance_pass:
        status = "FAIL_INPUT_PROVENANCE"
    elif not review_complete:
        status = "INPUT_PROVENANCE_PASS_REVIEW_PENDING"
    else:
        status = "INPUT_PROVENANCE_PASS_REVIEW_RECORDED_PHYSICS_FIDELITY_NOT_CERTIFIED"

    return {
        "schema_version": "1.0",
        "manifest_id": manifest.get("manifest_id"),
        "status": status,
        "provenance_checks": checks,
        "observed_sha256": observed_hashes,
        "errors": errors,
        "independent_signoff_recorded": review_complete,
        "physical_fidelity_certified": False,
        "interpretation": (
            "Hashes verify exact file identity only. They do not prove that the model matches "
            "the primary benchmark specification or that the simulation is physically validated."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--geometry-xml", required=True, type=Path)
    parser.add_argument("--materials-xml", required=True, type=Path)
    parser.add_argument("--settings-xml", required=True, type=Path)
    parser.add_argument("--mgxs-hdf5", required=True, type=Path)
    parser.add_argument("--source-builder", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite existing output: {args.out}")
    try:
        report = audit_manifest(args.manifest, {
            "geometry_xml": args.geometry_xml,
            "materials_xml": args.materials_xml,
            "settings_xml": args.settings_xml,
            "mgxs_hdf5": args.mgxs_hdf5,
            "source_builder": args.source_builder,
        })
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "errors": report["errors"],
                      "out": str(args.out)}, indent=2))
    return 0 if report["status"] != "FAIL_INPUT_PROVENANCE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
