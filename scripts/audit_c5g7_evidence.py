#!/usr/bin/env python3
"""End-to-end integrity gate for a completed six-layout C5G7 OpenMC study.

This validates run artifacts and provenance. It does not certify C5G7 benchmark
accuracy, convergence, a QUBO/material mapping, or reactor-safety performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

EXPECTED_REFLECTORS = ("p02", "p12", "p20", "p21", "p22")
POSITIONS = ("p00", "p01", "p10", "p11")
EXPECTED_REFERENCE = {"p00": "UO2", "p01": "MOX", "p10": "MOX", "p11": "UO2"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def expected_lattice(layout: dict[str, str]) -> str:
    symbol = {"UO2": "u", "MOX": "m"}
    rows = []
    for row in range(2):
        rows.append("[{}, {}, w]".format(
            symbol[layout[f"p{row}0"]], symbol[layout[f"p{row}1"]]
        ))
    rows.append("[w, w, w]")
    return "lattices['Core'].universes = [" + ", ".join(rows) + "]"


def validate_design(design: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if tuple(design.get("fixed_reflector_positions", ())) != EXPECTED_REFLECTORS:
        errors.append("design manifest does not preserve the exact five reflector positions")
    if (design.get("constraints") or {}).get("reflector_positions_fixed") is not True:
        errors.append("design manifest does not declare reflector_positions_fixed=true")
    candidates = design.get("candidate_layouts")
    if not isinstance(candidates, list) or len(candidates) != 6:
        errors.append("design manifest must contain exactly six candidates")
        return errors
    ids, signatures, reference_count = set(), set(), 0
    for item in candidates:
        cid = item.get("candidate_id")
        layout = item.get("fuel_assembly_layout")
        if not isinstance(layout, dict) or set(layout) != set(POSITIONS):
            errors.append(f"{cid}: layout must define exactly {POSITIONS}")
            continue
        if any(v not in ("UO2", "MOX") for v in layout.values()):
            errors.append(f"{cid}: unknown fuel material")
            continue
        signature = "".join("M" if layout[p] == "MOX" else "U" for p in POSITIONS)
        if sorted(layout.values()) != ["MOX", "MOX", "UO2", "UO2"]:
            errors.append(f"{cid}: expected two UO2 and two MOX assemblies")
        if cid != f"c5g7-2x2-{signature}":
            errors.append(f"{cid}: candidate ID does not match layout signature {signature}")
        if cid in ids or signature in signatures:
            errors.append(f"{cid}: duplicate candidate ID or layout signature")
        ids.add(cid)
        signatures.add(signature)
        is_reference = layout == EXPECTED_REFERENCE
        reference_count += int(is_reference)
        if bool(item.get("is_canonical_reference_arrangement")) != is_reference:
            errors.append(f"{cid}: canonical-reference flag disagrees with layout")
    if len(signatures) != 6:
        errors.append("design manifest does not enumerate six unique two-UO2/two-MOX layouts")
    if reference_count != 1:
        errors.append("design manifest must contain exactly one canonical reference arrangement")
    return errors


def audit_study(study_path: Path, design_path: Path, raw_audit_path: Path) -> dict[str, Any]:
    study = json.loads(study_path.read_text(encoding="utf-8"))
    design = json.loads(design_path.read_text(encoding="utf-8"))
    raw_audit = json.loads(raw_audit_path.read_text(encoding="utf-8"))
    root = study_path.resolve().parent
    errors: list[str] = []
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, actual: Any, expected: Any) -> None:
        checks.append({"name": name, "status": "PASS" if passed else "FAIL",
                       "actual": actual, "expected": expected})
        if not passed:
            errors.append(name)

    design_errors = validate_design(design)
    check("design_contract_valid", not design_errors, design_errors, "six valid layouts and fixed reflector contract")
    check("design_sha256_matches_study", study.get("design_space_sha256") == sha256(design_path),
          study.get("design_space_sha256"), sha256(design_path))
    check("study_mode_is_run", study.get("mode") == "run", study.get("mode"), "run")
    check("study_status_completed", study.get("status") == "all_runs_completed_needs_independent_validation",
          study.get("status"), "all_runs_completed_needs_independent_validation")
    check("raw_hdf5_audit_passed", raw_audit.get("status") == "PASS",
          raw_audit.get("status"), "PASS")
    cases = study.get("cases")
    check("six_case_records", isinstance(cases, list) and len(cases) == 6,
          len(cases) if isinstance(cases, list) else None, 6)
    if not isinstance(cases, list) or len(cases) != 6:
        cases = cases if isinstance(cases, list) else []

    settings_profile = study.get("settings") or {}
    expected_seed_set, statepoint_hashes, mgxs_hashes, candidate_ids = [], [], [], []
    per_candidate: list[dict[str, Any]] = []
    required_base_files = ("build.log", "openmc.log", "model/2d/settings.xml",
                           "model/2d/materials.xml", "model/2d/geometry.xml",
                           "model/2d/mgxs.h5", "model/2d/build-xml-2d.py")

    for case in cases:
        cid = str(case.get("candidate_id", "<missing-id>"))
        candidate_ids.append(cid)
        case_dir = root / cid
        local_errors: list[str] = []

        def local_check(name: str, passed: bool, actual: Any = None, expected: Any = True) -> None:
            if not passed:
                local_errors.append(name)
                errors.append(f"{cid}:{name}")

        local_check("case_completed", case.get("status") == "completed")
        local_check("physical_result_completed", (case.get("physical_results") or {}).get("status") == "completed")
        result_path = case_dir / "CASE_RESULT.json"
        local_check("case_result_exists", result_path.is_file())
        case_result = {}
        if result_path.is_file():
            try:
                case_result = json.loads(result_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                local_check("case_result_json_valid", False)
        local_check("case_result_identity_matches", case_result.get("candidate_id") == cid)
        local_check("case_result_manifest_matches_summary",
                    case_result.get("output_hashes_after_run") == case.get("output_hashes_after_run"))

        physical = case.get("physical_results") or {}
        command_records = physical.get("commands") or []
        local_check("both_commands_recorded", len(command_records) == 2)
        local_check("all_commands_succeeded",
                    len(command_records) == 2 and all(c.get("returncode") == 0 for c in command_records))

        hashes = case.get("output_hashes_after_run") or {}
        local_check("output_hash_manifest_nonempty", isinstance(hashes, dict) and bool(hashes))
        for rel in required_base_files:
            local_check("required_file:" + rel, (case_dir / rel).is_file())
            local_check("required_hash:" + rel, rel in hashes)
        statepoint_rel = physical.get("statepoint")
        statepoint_path = case_dir / statepoint_rel if isinstance(statepoint_rel, str) else None
        local_check("statepoint_path_recorded", statepoint_path is not None)
        if statepoint_path is not None:
            local_check("statepoint_exists", statepoint_path.is_file())
            local_check("statepoint_in_manifest", statepoint_rel in hashes)

        for rel, expected_hash in hashes.items():
            rel_path = Path(rel)
            if rel_path.is_absolute() or ".." in rel_path.parts:
                local_check("manifest_path_safe:" + rel, False)
                continue
            file_path = case_dir / rel_path
            local_check("manifest_file_exists:" + rel, file_path.is_file())
            if file_path.is_file():
                local_check("manifest_hash_matches:" + rel, sha256(file_path) == expected_hash)
        for rel in required_base_files:
            file_path = case_dir / rel
            if file_path.is_file() and file_path.stat().st_size == 0:
                local_check("nonempty_file:" + rel, False)

        settings_path = case_dir / "model/2d/settings.xml"
        seed_value = None
        if settings_path.is_file():
            try:
                settings = ET.parse(settings_path).getroot()
                seed_text = settings.findtext("seed")
                seed_value = int(seed_text) if seed_text is not None else None
                expected_profile = {
                    "batches": str(settings_profile.get("batches")),
                    "inactive": str(settings_profile.get("inactive")),
                    "particles": str(settings_profile.get("particles")),
                }
                actual_profile = {k: settings.findtext(k) for k in expected_profile}
                local_check("settings_profile_matches_study", actual_profile == expected_profile)
                local_check("settings_seed_matches_case", seed_value == case.get("seed"))
            except (ET.ParseError, TypeError, ValueError):
                local_check("settings_xml_parseable", False)
        expected_seed_set.append(seed_value)
        if seed_value is not None:
            local_check("seed_nonnegative", seed_value >= 0)

        layout = case.get("layout")
        builder_path = case_dir / "model/2d/build-xml-2d.py"
        if isinstance(layout, dict) and builder_path.is_file():
            source = builder_path.read_text(encoding="utf-8")
            matches = [line.strip() for line in source.splitlines()
                       if line.strip().startswith("lattices['Core'].universes = ")]
            local_check("exactly_one_generated_lattice_assignment", len(matches) == 1)
            if len(matches) == 1:
                local_check("five_reflector_cells_preserved_in_generated_builder",
                            re.sub(r"\s+", "", matches[0]) == re.sub(r"\s+", "", expected_lattice(layout)))
        else:
            local_check("layout_and_builder_available", False)

        state_hash = sha256(statepoint_path) if statepoint_path is not None and statepoint_path.is_file() else None
        statepoint_hashes.append(state_hash)
        mgxs_hash = sha256(case_dir / "model/2d/mgxs.h5") if (case_dir / "model/2d/mgxs.h5").is_file() else None
        mgxs_hashes.append(mgxs_hash)
        expected_seed_set[-1] = seed_value
        per_candidate.append({
            "candidate_id": cid, "seed": seed_value, "statepoint": statepoint_rel,
            "statepoint_sha256": state_hash, "mgxs_sha256": mgxs_hash,
            "status": "PASS" if not local_errors else "FAIL",
            "failed_checks": local_errors,
            "keff_mean": physical.get("keff_mean"),
            "keff_std_dev": physical.get("keff_std_dev"),
            "fission_analysis_status": "requires separate tally objective analysis",
        })

    check("unique_candidate_ids", len(set(candidate_ids)) == 6, candidate_ids, "six unique IDs")
    check("unique_seeds", len(set(expected_seed_set)) == 6 and None not in expected_seed_set,
          expected_seed_set, "six distinct parsed settings seeds")
    check("unique_statepoint_hashes", len(set(statepoint_hashes)) == 6 and None not in statepoint_hashes,
          statepoint_hashes, "six distinct statepoint hashes")
    check("one_shared_mgxs_hash", len(set(mgxs_hashes)) == 1 and None not in mgxs_hashes,
          mgxs_hashes, "one shared non-empty MGXS hash")
    check("raw_audit_candidate_ids_match",
          set(r.get("candidate_id") for r in raw_audit.get("candidates", [])) == set(candidate_ids),
          [r.get("candidate_id") for r in raw_audit.get("candidates", [])], candidate_ids)
    raw_candidates = {r.get("candidate_id"): r for r in raw_audit.get("candidates", [])}
    for row in per_candidate:
        raw_row = raw_candidates.get(row["candidate_id"], {})
        check("raw_audit_pass:" + row["candidate_id"], raw_row.get("status") == "PASS",
              raw_row.get("status"), "PASS")
        check("raw_audit_statepoint_hash_matches:" + row["candidate_id"],
              raw_row.get("statepoint_sha256") == row["statepoint_sha256"],
              raw_row.get("statepoint_sha256"), row["statepoint_sha256"])

    report = {
        "schema_version": "1.0",
        "audit_type": "c5g7_completed_run_integrity",
        "status": "PASS" if not errors else "FAIL",
        "study_summary": str(study_path),
        "design_space": str(design_path),
        "raw_hdf5_audit": str(raw_audit_path),
        "candidate_count": len(cases),
        "check_count": len(checks),
        "passed_count": sum(c["status"] == "PASS" for c in checks),
        "failed_count": sum(c["status"] == "FAIL" for c in checks),
        "failed_checks": errors,
        "checks": checks,
        "candidates": per_candidate,
        "scientific_limits": [
            "PASS means run provenance, required files, hashes, seeds, generated lattice assignment, and raw-HDF5 audit agree.",
            "PASS does not establish benchmark-grade convergence or official C5G7 benchmark acceptance.",
            "Fission-rate peaking is a relative proxy, not absolute power; uncertainty and objective analysis must be reported separately.",
            "The legacy fresh/once_burned/twice_burned QUBO remains unmapped to UO2/MOX.",
            "No reactor-safety or physical-superiority claim follows from this integrity audit."
        ]
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-summary", required=True, type=Path)
    parser.add_argument("--design-space", required=True, type=Path)
    parser.add_argument("--raw-audit", required=True, type=Path,
                        help="PASS report from audit_c5g7_smoke_statepoints.py")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite existing output: {args.out}")
    try:
        report = audit_study(args.study_summary, args.design_space, args.raw_audit)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "candidate_count": report["candidate_count"],
                      "passed": report["passed_count"], "failed": report["failed_count"],
                      "failed_checks": report["failed_checks"], "report": str(args.out)}, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
