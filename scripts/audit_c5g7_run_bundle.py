#!/usr/bin/env python3
"""Audit one or more extracted P4/P5 C5G7 artifact bundles without accepting physics."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

STANDARD_EDGES = [1e-5, 0.0635, 10.0, 100.0, 1000.0, 500000.0, 1000000.0, 20000000.0]
EXPECTED_MESH = [51, 51, 1]

def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def scalar(value):
    try:
        return value.item()
    except AttributeError:
        return value

def normalized_version(value) -> str | None:
    if value is None:
        return None
    try:
        return ".".join(str(int(v)) for v in value)
    except (TypeError, ValueError):
        return str(value)

def check_hash_map(root: Path, hashes: dict) -> dict:
    missing, mismatches, checked = [], [], 0
    for rel, expected in sorted(hashes.items()):
        path = root / rel
        if not path.is_file():
            missing.append(rel)
            continue
        actual = sha256(path)
        checked += 1
        if actual != expected:
            mismatches.append({"path": rel, "expected": expected, "actual": actual})
    return {"declared_count": len(hashes), "checked_count": checked,
            "missing": missing, "mismatches": mismatches,
            "pass": not missing and not mismatches and checked == len(hashes)}

def read_geometry_layout(geometry_path: Path) -> dict:
    root = ET.parse(geometry_path).getroot()
    lattice = next((x for x in root.findall("lattice")
                    if x.get("name") == "3x3 core lattice"), None)
    if lattice is None:
        raise ValueError("3x3 core lattice not found in generated geometry.xml")
    dims = [int(v) for v in (lattice.findtext("dimension") or "").split()]
    values = [int(v) for v in (lattice.findtext("universes") or "").split()]
    if dims != [3, 3] or len(values) != 9:
        raise ValueError(f"unexpected core lattice dimensions/content: dims={dims}, values={len(values)}")
    rows = [values[i:i+3] for i in range(0, 9, 3)]
    universe_to_material = {}
    for cell in root.findall("cell"):
        name = cell.get("name", "")
        universe = cell.get("universe")
        if not universe:
            continue
        if name == "UO2 Unrodded Assembly":
            universe_to_material[int(universe)] = "UO2"
        elif name == "MOX Unrodded Assembly":
            universe_to_material[int(universe)] = "MOX"
        elif name in {"Water Unrodded Assembly", "Reflector Unrodded Assembly"}:
            universe_to_material[int(universe)] = "REFLECTOR"
    try:
        mapped = [[universe_to_material[v] for v in row] for row in rows]
    except KeyError as exc:
        raise ValueError(f"root lattice references unknown assembly universe {exc.args[0]}") from exc
    return {"dimensions": dims, "universe_rows_top_to_bottom": rows,
            "material_rows_top_to_bottom": mapped,
            "fuel_positions_signature": "".join([
                "M" if mapped[0][0] == "MOX" else "U" if mapped[0][0] == "UO2" else "?",
                "M" if mapped[0][1] == "MOX" else "U" if mapped[0][1] == "UO2" else "?",
                "M" if mapped[1][0] == "MOX" else "U" if mapped[1][0] == "UO2" else "?",
                "M" if mapped[1][1] == "MOX" else "U" if mapped[1][1] == "UO2" else "?",
            ]),
            "reflector_positions_fixed": (mapped[0][2] == "REFLECTOR" and
                                          mapped[1][2] == "REFLECTOR" and
                                          mapped[2] == ["REFLECTOR"] * 3)}

def audit_one(study_path: Path) -> dict:
    issues, metadata_gaps = [], []
    study_root = study_path.parent
    summary = load_json(study_path)
    if not summary:
        return {"study_summary": str(study_path), "status": "INCOMPLETE", "issues": ["STUDY_SUMMARY.json missing or invalid"]}
    cases = summary.get("cases", [])
    if len(cases) != 1:
        issues.append(f"expected one candidate case per P4/P5 artifact, found {len(cases)}")
    case = cases[0] if cases else {}
    candidate = str(case.get("candidate_id", ""))
    case_root = study_root / candidate
    case_json_path = case_root / "CASE_RESULT.json"
    result = load_json(case_json_path)
    if not result:
        issues.append("CASE_RESULT.json missing or invalid")
    physical = result.get("physical_results") or case.get("physical_results") or {}
    seed = case.get("seed", result.get("seed"))
    phase = str(summary.get("study_id", ""))
    run_audit = load_json(study_root / "analysis" / "p45_run_audit.json")
    raw_audit = load_json(study_root / "analysis" / "raw_hdf5_audit.json")
    fission = load_json(case_root / "analysis" / "assembly_fission.json")
    convergence = load_json(case_root / "analysis" / "source_convergence.json")

    input_hash_audit = check_hash_map(case_root, result.get("input_hashes") or {})
    output_hash_audit = check_hash_map(case_root, result.get("output_hashes_after_run") or {})
    if not input_hash_audit["pass"]:
        issues.append("one or more declared input hashes are missing or mismatched")
    if not output_hash_audit["pass"]:
        issues.append("one or more declared post-run output hashes are missing or mismatched")
    if case.get("status") != "completed" or result.get("status") != "completed":
        issues.append(f"transport case status is not completed: summary={case.get('status')} result={result.get('status')}")

    statepoint_rel = physical.get("statepoint")
    sp = case_root / statepoint_rel if isinstance(statepoint_rel, str) else None
    if sp is None or not sp.is_file():
        issues.append("declared statepoint missing")
        sp_meta = {}
        statepoint_hash = None
    else:
        statepoint_hash = sha256(sp)
        try:
            import h5py
            with h5py.File(sp, "r") as h5:
                ver = normalized_version(h5.attrs.get("openmc_version"))
                mode = scalar(h5["energy_mode"][()]) if "energy_mode" in h5 else None
                if isinstance(mode, bytes):
                    mode = mode.decode("utf-8", errors="replace")
                batches = int(scalar(h5["n_batches"][()]))
                inactive = int(scalar(h5["n_inactive"][()]))
                particles = int(scalar(h5["n_particles"][()]))
                mesh_dims = [int(x) for x in h5["tallies/meshes/mesh 1/dimension"][()]]
                scores_raw = h5["tallies/tally 1/score_bins"][()]
                scores = [x.decode("utf-8", errors="replace") if isinstance(x, bytes) else str(x) for x in scores_raw]
                has_tally_results = "results" in h5["tallies/tally 1"]
            sp_meta = {"openmc_version": ver, "energy_mode": mode, "batches": batches,
                       "inactive": inactive, "particles": particles, "mesh_dimensions": mesh_dims,
                       "mesh_tally_scores": scores, "mesh_tally_results_present": has_tally_results}
        except Exception as exc:
            sp_meta = {}
            issues.append(f"cannot read statepoint metadata: {type(exc).__name__}: {exc}")
        if run_audit.get("statepoint_sha256") and run_audit.get("statepoint_sha256") != statepoint_hash:
            issues.append("p45_run_audit statepoint hash does not match statepoint file")
        if physical.get("mgxs_sha256_after_transport") and run_audit.get("mgxs_sha256") != physical.get("mgxs_sha256_after_transport"):
            issues.append("p45_run_audit MGXS hash differs from CASE_RESULT")
        if sp_meta.get("mesh_dimensions") != EXPECTED_MESH:
            issues.append(f"unexpected mesh dimensions: {sp_meta.get('mesh_dimensions')}")
        if not {"fission", "flux", "nu-fission"}.issubset(set(sp_meta.get("mesh_tally_scores", []))):
            issues.append("mesh tally lacks expected flux/fission/nu-fission scores")
        settings = summary.get("settings") or {}
        for key, actual in (("batches", sp_meta.get("batches")), ("inactive", sp_meta.get("inactive")),
                            ("particles", sp_meta.get("particles"))):
            if settings.get(key) != actual:
                issues.append(f"{key} mismatch: summary={settings.get(key)}, statepoint={actual}")
        if sp_meta.get("energy_mode") != "multi-group":
            issues.append(f"unexpected energy mode: {sp_meta.get('energy_mode')}")
        if sp_meta.get("openmc_version") is None:
            issues.append("OpenMC version missing from statepoint attributes")
        if run_audit.get("openmc_version") is None and sp_meta.get("openmc_version"):
            metadata_gaps.append("legacy p45_run_audit.openmc_version is null; recovered version from statepoint metadata")
        elif run_audit.get("openmc_version") and run_audit.get("openmc_version") != sp_meta.get("openmc_version"):
            issues.append("OpenMC version in p45_run_audit differs from statepoint attribute")

    mgxs = case_root / "model" / "2d" / "mgxs.h5"
    if not mgxs.is_file():
        issues.append("generated MGXS HDF5 is missing")
        mgxs_edges = []
        mgxs_hash = None
    else:
        mgxs_hash = sha256(mgxs)
        try:
            import h5py
            with h5py.File(mgxs, "r") as h5:
                mgxs_edges = [float(x) for x in h5.attrs.get("group structure", [])]
        except Exception as exc:
            mgxs_edges = []
            issues.append(f"cannot read MGXS group structure: {type(exc).__name__}: {exc}")
        if mgxs_hash != physical.get("mgxs_sha256_after_transport"):
            issues.append("generated MGXS SHA-256 does not match CASE_RESULT post-transport hash")
        if len(mgxs_edges) != len(STANDARD_EDGES) or any(not math.isclose(a, b, rel_tol=0, abs_tol=1e-12) for a,b in zip(mgxs_edges, STANDARD_EDGES)):
            issues.append(f"MGXS energy edges differ from standard C5G7 edges: {mgxs_edges}")
        if physical.get("mgxs_group_structure_audit") != "PASS":
            issues.append(f"run's MGXS group-structure audit is {physical.get('mgxs_group_structure_audit')}")

    geometry = case_root / "model" / "2d" / "geometry.xml"
    try:
        geo = read_geometry_layout(geometry)
        layout = result.get("layout") or {}
        expected_sig = "".join("M" if layout.get(k) == "MOX" else "U" if layout.get(k) == "UO2" else "?" for k in ("p00","p01","p10","p11"))
        if geo["fuel_positions_signature"] != expected_sig:
            issues.append(f"generated geometry layout {geo['fuel_positions_signature']} does not match declared layout {expected_sig}")
        if not geo["reflector_positions_fixed"]:
            issues.append("generated root lattice does not show the five fixed reflector positions")
    except Exception as exc:
        geo = {}
        issues.append(f"cannot reconstruct generated geometry layout: {type(exc).__name__}: {exc}")

    batch_run = {
        "candidate_id": candidate,
        "layout_signature": candidate.removeprefix("c5g7-2x2-"),
        "seed": seed,
        "phase": run_audit.get("phase"),
        "run_settings": summary.get("settings"),
        "openmc_version_from_statepoint": sp_meta.get("openmc_version"),
        "statepoint_sha256": statepoint_hash,
        "statepoint": sp_meta,
        "raw_hdf5_audit": {"status": raw_audit.get("status"), "check_count": raw_audit.get("check_count"),
                           "passed_count": raw_audit.get("passed_count"), "failed_count": raw_audit.get("failed_count")},
        "input_hash_audit": input_hash_audit,
        "post_run_output_hash_audit": output_hash_audit,
        "mgxs": {"sha256": mgxs_hash, "group_structure_audit": physical.get("mgxs_group_structure_audit"),
                 "energy_edges_eV": mgxs_edges, "standard_c5g7_edges_pass": len(mgxs_edges) == len(STANDARD_EDGES) and
                 all(math.isclose(a,b,rel_tol=0,abs_tol=1e-12) for a,b in zip(mgxs_edges,STANDARD_EDGES))},
        "geometry_mapping": geo,
        "keff_mean": physical.get("keff_mean"),
        "keff_std_dev_within_run": physical.get("keff_std_dev"),
        "fission_rate_peaking_proxy": fission.get("fission_rate_peaking_factor"),
        "source_convergence": {
            "status": convergence.get("status"),
            "automatic_convergence_claim": convergence.get("automatic_convergence_claim"),
            "k_generation_second_minus_first_half_pcm": convergence.get("k_generation_second_minus_first_half_pcm"),
            "k_generation_first_quarter_mean": (convergence.get("k_generation") or {}).get("first_quarter_mean"),
            "k_generation_last_quarter_mean": (convergence.get("k_generation") or {}).get("last_quarter_mean"),
            "entropy_last_minus_first_quarter_mean": (convergence.get("entropy") or {}).get("last_minus_first_quarter_mean")
        },
        "legacy_run_audit_openmc_version": run_audit.get("openmc_version"),
        "metadata_gaps": metadata_gaps,
        "issues": issues,
        "integrity_status": "PASS" if not issues and raw_audit.get("status") == "PASS" else "FAIL_OR_INCOMPLETE",
        "convergence_status": convergence.get("status", "MISSING"),
        "physical_validation_status": "NOT_ESTABLISHED",
        "official_benchmark_acceptance": False,
        "interpretation": "Artifact/input integrity is a prerequisite, not evidence by itself of convergence, model validity, benchmark acceptance, reactor safety, or a physically best layout."
    }
    if batch_run["raw_hdf5_audit"]["status"] != "PASS":
        batch_run["issues"].append("raw HDF5 audit is not PASS")
        batch_run["integrity_status"] = "FAIL_OR_INCOMPLETE"
    if batch_run["source_convergence"]["status"] not in {"PASS", "CONVERGENCE_REVIEW_PASSED"}:
        batch_run["convergence_status"] = "REVIEW_REQUIRED"
    return batch_run

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bundle-root", type=Path, required=True, help="Extracted GitHub artifact root")
    p.add_argument("--out", type=Path, required=True, help="Output JSON path (must not exist)")
    a = p.parse_args()
    if a.out.exists():
        p.error(f"refusing to overwrite existing output: {a.out}")
    rows = [audit_one(x) for x in sorted(a.bundle_root.rglob("STUDY_SUMMARY.json"))]
    issues = []
    if not rows:
        issues.append("no STUDY_SUMMARY.json files found under bundle root")
    integrity_passes = sum(x["integrity_status"] == "PASS" for x in rows)
    report = {
        "schema_version": "1.0",
        "audit_id": "CBPFR-P45-ARTIFACT-BUNDLE-AUDIT-2026-10-18",
        "bundle_root": str(a.bundle_root),
        "record_count": len(rows),
        "integrity_pass_count": integrity_passes,
        "incomplete_or_fail_count": len(rows)-integrity_passes,
        "all_input_output_hashes_and_hdf5_pass": bool(rows) and integrity_passes == len(rows),
        "physical_validation_status": "NOT_ESTABLISHED",
        "records": rows,
        "issues": issues,
        "nonclaims": [
            "This script verifies provenance, file hashes, generated geometry/material mapping, group structure and statepoint metadata.",
            "The script does not certify convergence or establish physical benchmark acceptance.",
            "A passed artifact audit does not certify physical suitability, safety, or a best design."
        ]
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in {"records"}}, indent=2))
    return 0 if report["all_input_output_hashes_and_hdf5_pass"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
