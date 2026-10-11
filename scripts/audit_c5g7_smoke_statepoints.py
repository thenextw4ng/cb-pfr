#!/usr/bin/env python3
"""Fail-closed raw-HDF5 audit for the six C5G7 smoke-run statepoints."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").rstrip("\x00")
    if hasattr(value, "item"):
        try:
            return _text(value.item())
        except (TypeError, ValueError):
            pass
    return str(value)


def _close(actual: Any, expected: Any, *, abs_tol: float = 1e-12) -> bool:
    try:
        a, e = float(actual), float(expected)
    except (TypeError, ValueError):
        return False
    return math.isfinite(a) and math.isfinite(e) and math.isclose(
        a, e, rel_tol=0.0, abs_tol=abs_tol
    )


def audit_candidate(root: Path, case: dict[str, Any], expected_settings: dict[str, Any]) -> dict[str, Any]:
    try:
        import h5py
    except ImportError as exc:
        raise RuntimeError("h5py is required to audit raw statepoint files") from exc

    candidate_id = case.get("candidate_id")
    case_dir = root / str(candidate_id)
    physical_hint = case.get("physical_results") or {}
    statepoint_rel = physical_hint.get("statepoint")
    statepoint = case_dir / statepoint_rel if isinstance(statepoint_rel, str) and statepoint_rel else case_dir / "model/2d/statepoint.100.h5"
    settings_path = case_dir / "model/2d/settings.xml"
    result_path = case_dir / "CASE_RESULT.json"
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, actual: Any, expected: Any) -> None:
        checks.append({
            "name": name,
            "status": "PASS" if passed else "FAIL",
            "actual": actual,
            "expected": expected,
        })

    if not result_path.is_file() or not settings_path.is_file() or not statepoint.is_file():
        for missing, path in (("case_result_exists", result_path),
                              ("settings_exists", settings_path),
                              ("statepoint_exists", statepoint)):
            add(missing, path.is_file(), path.is_file(), True)
        return {
            "candidate_id": candidate_id,
            "status": "FAIL",
            "checks": checks,
            "failed_checks": [c["name"] for c in checks if c["status"] == "FAIL"],
        }

    case_result = json.loads(result_path.read_text(encoding="utf-8"))
    physical = case_result.get("physical_results") or {}
    settings = ET.parse(settings_path).getroot()
    settings_values = {
        "run_mode": settings.findtext("run_mode"),
        "energy_mode": settings.findtext("energy_mode"),
        "batches": settings.findtext("batches"),
        "inactive": settings.findtext("inactive"),
        "particles": settings.findtext("particles"),
        "seed": settings.findtext("seed"),
    }
    statepoint_hash = sha256(statepoint)
    settings_hash = sha256(settings_path)
    mgxs_path = case_dir / "model/2d/mgxs.h5"
    mgxs_hash = sha256(mgxs_path) if mgxs_path.is_file() else None

    with h5py.File(statepoint, "r") as handle:
        if "k_combined" not in handle:
            raise ValueError(f"{candidate_id}: statepoint lacks k_combined")
        k = handle["k_combined"][()]
        k_mean, k_sd = float(k[0]), float(k[1])
        metadata = {
            "n_batches": int(handle["n_batches"][()]),
            "n_inactive": int(handle["n_inactive"][()]),
            "n_particles": int(handle["n_particles"][()]),
            "n_realizations": int(handle["n_realizations"][()]),
            "run_mode": _text(handle["run_mode"][()]),
            "energy_mode": _text(handle["energy_mode"][()]),
        }
        meshes = []
        if "tallies/meshes" in handle:
            for name, mesh in handle["tallies/meshes"].items():
                if "dimension" in mesh:
                    meshes.append({"name": name, "dimension": [int(v) for v in mesh["dimension"][()]]})
        tallies = []
        if "tallies" in handle:
            for name, tally in handle["tallies"].items():
                if name.startswith("tally ") and hasattr(tally, "keys"):
                    scores = [_text(v) for v in tally["score_bins"][()]] if "score_bins" in tally else []
                    tallies.append({"name": name, "scores": scores})

    add("case_result_candidate_id", case_result.get("candidate_id") == candidate_id,
        case_result.get("candidate_id"), candidate_id)
    add("case_status_completed", physical.get("status") == "completed",
        physical.get("status"), "completed")
    add("settings_seed_matches_manifest", settings_values["seed"] == str(case.get("seed")),
        settings_values["seed"], str(case.get("seed")))
    expected_profile = {
        "run_mode": "eigenvalue",
        "energy_mode": "multi-group",
        "batches": str(expected_settings.get("batches")),
        "inactive": str(expected_settings.get("inactive")),
        "particles": str(expected_settings.get("particles")),
        "seed": str(case.get("seed")),
    }
    add("settings_profile", settings_values == expected_profile, settings_values, expected_profile)

    expected_hashes = case.get("output_hashes_after_run") or {}
    add("statepoint_hash_matches_run_manifest",
        expected_hashes.get(str(Path(statepoint_rel))) == statepoint_hash,
        statepoint_hash, expected_hashes.get(str(Path(statepoint_rel))))
    add("settings_hash_matches_run_manifest",
        expected_hashes.get("model/2d/settings.xml") == settings_hash,
        settings_hash, expected_hashes.get("model/2d/settings.xml"))
    add("mgxs_hash_matches_before_and_after",
        mgxs_hash is not None
        and mgxs_hash == physical.get("mgxs_sha256_before_transport")
        and mgxs_hash == physical.get("mgxs_sha256_after_transport"),
        {"actual": mgxs_hash, "before": physical.get("mgxs_sha256_before_transport"),
         "after": physical.get("mgxs_sha256_after_transport")},
        "all hashes identical")

    add("keff_mean_matches_openmc_api",
        _close(k_mean, physical.get("keff_mean")),
        k_mean, physical.get("keff_mean"))
    add("keff_std_dev_matches_openmc_api",
        _close(k_sd, physical.get("keff_std_dev")),
        k_sd, physical.get("keff_std_dev"))
    expected_metadata = {
        "n_batches": int(expected_settings["batches"]),
        "n_inactive": int(expected_settings["inactive"]),
        "n_particles": int(expected_settings["particles"]),
        "n_realizations": int(expected_settings["batches"]) - int(expected_settings["inactive"]),
    }
    for key, expected in expected_metadata.items():
        add(f"metadata:{key}", metadata[key] == expected, metadata[key], expected)
    add("metadata:run_mode", metadata["run_mode"] == "eigenvalue", metadata["run_mode"], "eigenvalue")
    add("metadata:energy_mode", metadata["energy_mode"] == "multi-group", metadata["energy_mode"], "multi-group")
    add("expected_mesh_present", any(m["dimension"] == [51, 51, 1] for m in meshes),
        meshes, [51, 51, 1])
    expected_scores = {"flux", "fission", "nu-fission"}
    add("expected_scores_present", any(set(t["scores"]) == expected_scores for t in tallies),
        tallies, sorted(expected_scores))
    add("no_preexisting_files_mutated", not physical.get("mutated_preexisting_files"),
        physical.get("mutated_preexisting_files"), {})

    failed = [c["name"] for c in checks if c["status"] != "PASS"]
    return {
        "candidate_id": candidate_id,
        "layout": case.get("layout"),
        "seed": case.get("seed"),
        "status": "PASS" if not failed else "FAIL",
        "statepoint_sha256": statepoint_hash,
        "settings_sha256": settings_hash,
        "mgxs_sha256": mgxs_hash,
        "keff_mean_raw_hdf5": k_mean,
        "keff_std_dev_raw_hdf5": k_sd,
        "metadata": metadata,
        "mesh_dimensions": meshes,
        "tallies": tallies,
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "failed_checks": failed,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-summary", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--expected-candidates", type=int, default=6, help="expected candidate count; default is six-layout smoke study")
    args = parser.parse_args()
    if args.expected_candidates < 1:
        parser.error("--expected-candidates must be at least 1")
    if args.out.exists():
        parser.error(f"output already exists: {args.out}")
    try:
        study = json.loads(args.study_summary.read_text(encoding="utf-8"))
        root = args.study_summary.parent
        cases = study.get("cases")
        if not isinstance(cases, list) or len(cases) != args.expected_candidates:
            raise ValueError(f"expected exactly {args.expected_candidates} candidate cases in STUDY_SUMMARY.json")
        results = [audit_candidate(root, case, study.get("settings", {})) for case in cases]
        ids = [r.get("candidate_id") for r in results]
        seeds = [r.get("seed") for r in results]
        statepoint_hashes = [r.get("statepoint_sha256") for r in results]
        mgxs_hashes = {r.get("mgxs_sha256") for r in results}
        aggregate_checks = [
            {"name": "unique_candidate_ids", "status": "PASS" if len(set(ids)) == args.expected_candidates else "FAIL",
             "actual": ids, "expected": f"{args.expected_candidates} unique IDs"},
            {"name": "unique_seeds", "status": "PASS" if len(set(seeds)) == args.expected_candidates else "FAIL",
             "actual": seeds, "expected": f"{args.expected_candidates} unique seeds"},
            {"name": "unique_statepoint_hashes", "status": "PASS" if len(set(statepoint_hashes)) == args.expected_candidates else "FAIL",
             "actual": statepoint_hashes, "expected": f"{args.expected_candidates} unique statepoint hashes"},
            {"name": "shared_mgxs_hash", "status": "PASS" if len(mgxs_hashes) == 1 and None not in mgxs_hashes else "FAIL",
             "actual": sorted(str(v) for v in mgxs_hashes), "expected": "one non-empty common MGXS hash"},
        ]
        all_checks = [c for r in results for c in r.get("checks", [])] + aggregate_checks
        failed = [c["name"] for c in all_checks if c["status"] != "PASS"]
        report = {
            "schema_version": "1.0",
            "status": "PASS" if not failed and all(r["status"] == "PASS" for r in results) else "FAIL",
            "study_id": study.get("study_id"),
            "upstream_commit": study.get("upstream_commit"),
            "candidate_count": len(results),
            "check_count": len(all_checks),
            "passed_count": len(all_checks) - len(failed),
            "failed_count": len(failed),
            "failed_checks": failed,
            "aggregate_checks": aggregate_checks,
            "candidates": results,
            "interpretation": (
                "PASS means raw HDF5 metadata/scalars agree with the recorded OpenMC API output and "
                "the explicit smoke-run settings/manifests. It does not establish benchmark correctness, "
                "same-layout repeatability, a QUBO-to-material mapping, or reactor safety."
            ),
        }
    except (OSError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"], "candidate_count": report["candidate_count"],
        "passed": report["passed_count"], "failed": report["failed_count"],
        "failed_checks": report["failed_checks"], "report": str(args.out)
    }, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
