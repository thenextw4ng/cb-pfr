#!/usr/bin/env python3
"""Independent integrity audit for a completed BEAVRS map-comparison artifact.

This verifies reproducibility and internal consistency only. It deliberately
never changes physical_validation_claim from NOT_ESTABLISHED.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

PINNED_BEAVRS_COMMIT = "1ccae04dc3830a5977f08ed7f5f7e1e51ded0d22"
EXPECTED_DETECTORS = 58


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit_run(run_dir: Path) -> dict:
    run_dir = run_dir.resolve()
    manifest = json.loads((run_dir / "beavrs_run_manifest.json").read_text(encoding="utf-8"))
    result = json.loads((run_dir / "beavrs_cycle1_day0_map_comparison.json").read_text(encoding="utf-8"))
    measured = json.loads((run_dir / "beavrs_measurements_normalized.json").read_text(encoding="utf-8"))
    assembly_map = json.loads((run_dir / "beavrs_assembly_mesh_map.json").read_text(encoding="utf-8"))
    checks: dict[str, bool] = {}

    checks["pinned_upstream_commit"] = (
        manifest.get("upstream_commit") == PINNED_BEAVRS_COMMIT
        and result.get("upstream_commit") == PINNED_BEAVRS_COMMIT
    )
    checks["explicit_nonvalidation_claim"] = result.get("physical_validation_claim") == "NOT_ESTABLISHED"
    checks["exactly_58_unique_measurements"] = len(measured) == EXPECTED_DETECTORS and len(set(measured)) == EXPECTED_DETECTORS
    checks["all_measurements_have_mesh_bins"] = set(measured).issubset(assembly_map)

    crosswalk_info = manifest.get("coordinate_crosswalk", {})
    crosswalk_path = run_dir / str(crosswalk_info.get("file", "beavrs_coordinate_crosswalk.csv"))
    checks["coordinate_crosswalk_exists"] = crosswalk_path.is_file()
    crosswalk_rows: list[dict[str, str]] = []
    if crosswalk_path.is_file():
        with crosswalk_path.open(newline="", encoding="utf-8-sig") as handle:
            crosswalk_rows = list(csv.DictReader(handle))
        crosswalk_labels = [row.get("assembly", "") for row in crosswalk_rows]
        instrumented_labels = {
            row.get("assembly", "") for row in crosswalk_rows
            if row.get("is_instrumented_detector", "").strip().lower() == "true"
        }
        valid_bins = True
        for row in crosswalk_rows:
            try:
                ix = int(row["mesh_x_index_1based"])
                iy = int(row["mesh_y_index_1based"])
                x_cm = float(row["mesh_center_x_cm"])
                y_cm = float(row["mesh_center_y_cm"])
            except (KeyError, TypeError, ValueError):
                valid_bins = False
                break
            if not (1 <= ix <= 15 and 1 <= iy <= 15 and math.isfinite(x_cm) and math.isfinite(y_cm)):
                valid_bins = False
                break
        checks["coordinate_crosswalk_sha256_matches"] = (
            bool(crosswalk_info.get("sha256"))
            and sha256_file(crosswalk_path) == crosswalk_info.get("sha256")
        )
        checks["coordinate_crosswalk_has_176_unique_assemblies"] = (
            len(crosswalk_rows) == 176
            and len(set(crosswalk_labels)) == 176
            and all(crosswalk_labels)
        )
        checks["coordinate_crosswalk_has_58_instrumented_labels"] = (
            len(instrumented_labels) == EXPECTED_DETECTORS
            and instrumented_labels == set(measured)
        )
        checks["coordinate_crosswalk_bins_are_valid"] = valid_bins
        checks["coordinate_crosswalk_counts_match_manifest"] = (
            crosswalk_info.get("assembly_rows") == len(crosswalk_rows)
            and crosswalk_info.get("instrumented_detector_rows") == len(instrumented_labels)
        )
    else:
        checks.update({
            "coordinate_crosswalk_sha256_matches": False,
            "coordinate_crosswalk_has_176_unique_assemblies": False,
            "coordinate_crosswalk_has_58_instrumented_labels": False,
            "coordinate_crosswalk_bins_are_valid": False,
            "coordinate_crosswalk_counts_match_manifest": False,
        })

    checks["all_model_input_hashes_present"] = bool(manifest.get("model_input_sha256"))
    for name, expected_hash in manifest.get("model_input_sha256", {}).items():
        path = run_dir / name
        checks[f"input_hash:{name}"] = path.is_file() and sha256_file(path) == expected_hash

    statepoint = run_dir / str(result.get("statepoint", ""))
    checks["statepoint_exists"] = statepoint.is_file()
    if statepoint.is_file():
        checks["statepoint_sha256_matches"] = sha256_file(statepoint) == result.get("statepoint_sha256")
    else:
        checks["statepoint_sha256_matches"] = False

    rows = []
    with (run_dir / "beavrs_cycle1_day0_map_comparison.csv").open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    labels = [row["assembly"] for row in rows]
    checks["comparison_has_58_unique_assemblies"] = len(rows) == EXPECTED_DETECTORS and len(set(labels)) == EXPECTED_DETECTORS
    checks["comparison_labels_match_measurements"] = set(labels) == set(measured)

    calculated: dict[str, float] = {}
    residuals: dict[str, float] = {}
    row_values_valid = True
    for row in rows:
        label = row["assembly"]
        try:
            obs = float(row["measured_normalized"])
            pred = float(row["calculated_normalized"])
            residual = float(row["residual_calculated_minus_measured"])
            abs_rel = float(row["absolute_relative_error_percent"])
        except (KeyError, TypeError, ValueError):
            row_values_valid = False
            break
        if not all(math.isfinite(v) for v in (obs, pred, residual, abs_rel)) or obs <= 0 or pred <= 0:
            row_values_valid = False
            break
        if abs((pred - obs) - residual) > 1e-10:
            row_values_valid = False
            break
        if abs(100.0 * abs(residual) / obs - abs_rel) > 1e-8:
            row_values_valid = False
            break
        calculated[label] = pred
        residuals[label] = residual
    checks["finite_rows_and_residual_arithmetic"] = row_values_valid and len(residuals) == EXPECTED_DETECTORS
    checks["normalized_measured_mean_is_one"] = (
        len(measured) == EXPECTED_DETECTORS
        and abs(sum(float(v) for v in measured.values()) / len(measured) - 1.0) < 1e-10
    )
    checks["normalized_calculated_mean_is_one"] = (
        len(calculated) == EXPECTED_DETECTORS
        and abs(sum(calculated.values()) / len(calculated) - 1.0) < 1e-8
    )

    if row_values_valid and len(residuals) == EXPECTED_DETECTORS:
        n = len(residuals)
        rmse = math.sqrt(sum(v * v for v in residuals.values()) / n)
        mae = sum(abs(v) for v in residuals.values()) / n
        mape = 100.0 * sum(abs(residuals[k] / float(measured[k])) for k in residuals) / n
        obs = [float(measured[k]) for k in measured]
        pred = [calculated[k] for k in measured]
        obs_mean = sum(obs) / n
        pred_mean = sum(pred) / n
        cov = sum((a - obs_mean) * (b - pred_mean) for a, b in zip(obs, pred))
        denom = math.sqrt(sum((a - obs_mean) ** 2 for a in obs) * sum((b - pred_mean) ** 2 for b in pred))
        corr = cov / denom if denom > 0 else float("nan")
        reported = result.get("metrics", {})
        checks["reported_rmse_recomputed"] = math.isfinite(rmse) and abs(rmse - float(reported.get("normalized_map_rmse", float("nan")))) < 1e-9
        checks["reported_mae_recomputed"] = math.isfinite(mae) and abs(mae - float(reported.get("normalized_map_mae", float("nan")))) < 1e-9
        checks["reported_mape_recomputed"] = math.isfinite(mape) and abs(mape - float(reported.get("mean_absolute_relative_error_percent", float("nan")))) < 1e-7
        checks["reported_correlation_recomputed"] = math.isfinite(corr) and abs(corr - float(reported.get("pearson_correlation", float("nan")))) < 1e-8
    else:
        checks.update({
            "reported_rmse_recomputed": False,
            "reported_mae_recomputed": False,
            "reported_mape_recomputed": False,
            "reported_correlation_recomputed": False,
        })

    checks["openmc_log_present"] = (run_dir / "openmc.log").is_file()
    checks["source_provenance_present"] = (run_dir / "source_provenance.txt").is_file()
    checks["nuclear_data_hash_records_present"] = (
        (run_dir / "nuclear_data_archive.sha256").is_file()
        and (run_dir / "cross_sections_xml.sha256").is_file()
    )
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "schema_version": "1.0",
        "audit": "BEAVRS_CYCLE1_MAP_ARTIFACT_INTEGRITY",
        "status": "PASS_INTEGRITY_ONLY" if not failed else "FAIL",
        "physical_validation_claim": "NOT_ESTABLISHED",
        "checks": checks,
        "failed_checks": failed,
        "detector_count": len(measured),
        "run_dir": str(run_dir),
        "interpretation": (
            "A passing audit verifies file provenance and arithmetic consistency. It does not establish "
            "benchmark acceptance, measurement-uncertainty agreement, model adequacy, or CB-PFR effectiveness."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    try:
        result = audit_run(args.run_dir)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    output = args.out or (args.run_dir / "beavrs_integrity_audit.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "failed_checks": result["failed_checks"]}, indent=2))
    return 0 if result["status"] == "PASS_INTEGRITY_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
