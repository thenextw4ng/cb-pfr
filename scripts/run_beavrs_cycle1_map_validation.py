#!/usr/bin/env python3
"""Run a BEAVRS Cycle-1 beginning-of-cycle radial fission-map comparison.

This is a preliminary experimental comparison, not an automatic certification of
physical validation. It compares a tilt-corrected BEAVRS map at the 58 instrumented
assembly labels and explicitly records the SE withdrawal override used to match
the day-0 state. The two maps are normalized over those same 58 positions.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

PITCH_CM = 21.50364
FUEL_BOTTOM_CM = 36.748
FUEL_TOP_CM = 402.508
MESH_N = 15
MEASUREMENT_RAW_REL = Path("measurements/detector_signals/cycle_1/0/radial_measurements_full.csv")
MEASUREMENT_REL = Path("measurements/detector_signals/cycle_1/0/radial_measurements_full_tc.csv")
SUMMARY_REL = Path("measurements/detector_signals/cycle_1/0/summary.csv")
TALLY_NAME = "beavrs_cycle1_day0_assembly_fission_rate"
MODEL_COMMIT = "1ccae04dc3830a5977f08ed7f5f7e1e51ded0d22"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_measurement_values(path: Path) -> dict[str, float]:
    values: dict[str, float] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.reader(handle):
            if len(row) < 2 or not row[0].strip():
                continue
            label = row[0].strip().replace(" ", "")
            value = float(row[1])
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"invalid measurement for {label}: {value}")
            if label in values:
                raise ValueError(f"duplicate detector label {label}")
            values[label] = value
    if not values:
        raise ValueError(f"no measurement values found in {path}")
    return values


def load_measurements(path: Path) -> dict[str, float]:
    values = load_measurement_values(path)
    if len(values) != 58:
        raise ValueError(f"expected 58 instrumented assembly measurements, got {len(values)}")
    mean = sum(values.values()) / len(values)
    return {label: value / mean for label, value in values.items()}


def normalize_detector_subset(values: dict[str, float]) -> dict[str, float]:
    if len(values) != 58:
        raise ValueError(f"expected 58 instrumented detector positions, got {len(values)}")
    mean = sum(values.values()) / len(values)
    if not math.isfinite(mean) or mean <= 0:
        raise ValueError("invalid mean for detector-map normalization")
    return {label: value / mean for label, value in values.items()}


def build_assembly_map(core_template: list[list[str]]) -> dict[str, tuple[int, int]]:
    """Map BEAVRS assembly labels to 1-based OpenMC mesh indices."""
    result: dict[str, tuple[int, int]] = {}
    for row_index, row in enumerate(core_template):
        for col_index, token in enumerate(row):
            match = re.fullmatch(r"([A-Z])_+(\d{1,2})", token)
            if not match:
                continue
            label = f"{match.group(1)}{int(match.group(2))}"
            # BEAVRS has a 15x15 assembly lattice embedded in a 19x19
            # template with two padding rows/columns on each side. Assembly
            # tokens occupy template rows/columns 2..16 (zero-based).
            # OpenMC mesh y indices increase from the lower boundary, while
            # the lattice template is stored from top to bottom.
            if not (2 <= row_index <= 16 and 2 <= col_index <= 16):
                continue
            ix = col_index - 1  # template column 2 -> mesh bin 1
            iy = 17 - row_index  # template row 2 -> mesh bin 15; row 16 -> bin 1
            if label in result:
                raise ValueError(f"duplicate assembly label {label}")
            result[label] = (ix, iy)
    return result


def prepare(args: argparse.Namespace) -> None:
    try:
        import openmc
        from beavrs.builder import BEAVRS
        from beavrs.core import Core
    except ImportError as exc:
        raise RuntimeError(
            "OpenMC and the pinned upstream BEAVRS Python package must be installed"
        ) from exc

    beavrs_root = Path(args.beavrs_root).resolve()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    os.chdir(output)

    # Cycle 1, day 0: measured average boron 975.25 ppm, temperature 558.875 F,
    # all banks withdrawn except D at 213 steps. The Cycle 1 day-0 summary
    # reports shutdown bank E (SE) at 230 steps; override the upstream default
    # 228 to match the state and record the step-width assumption in provenance.
    rcca = {
        "A": 228, "B": 228, "C": 228, "D": 213,
        "SA": 228, "SB": 228, "SC": 228, "SD": 228, "SE": 230,
    }
    builder = BEAVRS(boron_ppm=975.25, is_symmetric=False, is_2d=False, rcca_z=rcca)
    builder.set_params(particles=args.particles, batches=args.batches, inactive=args.inactive)
    builder.model = builder.build_openmc_model()

    mesh = openmc.RegularMesh()
    mesh.dimension = (MESH_N, MESH_N, 1)
    mesh.lower_left = (-7.5 * PITCH_CM, -7.5 * PITCH_CM, FUEL_BOTTOM_CM)
    mesh.upper_right = (7.5 * PITCH_CM, 7.5 * PITCH_CM, FUEL_TOP_CM)
    tally = openmc.Tally(name=TALLY_NAME)
    tally.filters = [openmc.MeshFilter(mesh)]
    tally.scores = ["fission"]
    # OpenMC 0.15.3 serializes meshes referenced by MeshFilter directly in tallies.xml;
    # the upstream BEAVRS helper's legacy Tallies.add_mesh call is not available.
    builder.tally_meshes = []
    builder.tallies = [tally]
    builder.model = builder.build_openmc_model()
    builder.model.settings.seed = args.seed
    builder.model.export_to_xml()
    input_xml_sha256 = {
        name: sha256_file(output / name)
        for name in ("geometry.xml", "materials.xml", "settings.xml", "tallies.xml", "plots.xml", "model.xml")
        if (output / name).is_file()
    }

    assembly_map = build_assembly_map(Core.core_lattice_template)
    instrumented_raw = load_measurement_values(beavrs_root / MEASUREMENT_RAW_REL)
    if len(instrumented_raw) != 58:
        raise ValueError(f"expected 58 raw instrumented labels, got {len(instrumented_raw)}")
    tilt_corrected_all = load_measurement_values(beavrs_root / MEASUREMENT_REL)
    missing_corrected = sorted(set(instrumented_raw) - set(tilt_corrected_all))
    if missing_corrected:
        raise ValueError(f"tilt-corrected map lacks instrumented labels: {missing_corrected}")
    measurements = normalize_detector_subset({label: tilt_corrected_all[label] for label in instrumented_raw})
    missing = sorted(set(measurements) - set(assembly_map))
    if missing:
        raise ValueError(f"measurement labels not present in assembly map: {missing}")
    provenance = {
        "benchmark": "BEAVRS Cycle 1 day 0 radial detector map",
        "upstream_repository": "https://github.com/mit-crpg/BEAVRS",
        "upstream_commit": MODEL_COMMIT,
        "measured_data": str(beavrs_root / MEASUREMENT_REL),
        "measured_data_sha256": sha256_file(beavrs_root / MEASUREMENT_REL),
        "instrumented_positions_source": str(beavrs_root / MEASUREMENT_RAW_REL),
        "instrumented_positions_source_sha256": sha256_file(beavrs_root / MEASUREMENT_RAW_REL),
        "measurement_processing": "Use tilt-corrected full-core map values only at the 58 labels present in the raw instrumented-detector map; renormalize those 58 values to mean 1.",
        "measured_summary": str(beavrs_root / SUMMARY_REL),
        "measured_detector_count": len(measurements),
        "measurement_normalization": "mean over 58 reported normalized detector values = 1",
        "model": {
            "dimension": "full 3-D full-core upstream BEAVRS geometry",
            "boron_ppm": 975.25,
            "temperature_K": 566.483,
            "RCCA_steps_withdrawn": rcca,
            "measured_SE_steps_withdrawn": 230,
            "upstream_default_SE_steps_withdrawn": 228,
            "SE_override": "Set SE to 230 to match the Cycle 1 day-0 summary; this exceeds the generic helper guard and retains the upstream axial step width, so geometry and sensitivity review are required.",
            "fuel_axial_range_cm": [FUEL_BOTTOM_CM, FUEL_TOP_CM],
            "mesh": {
                "dimension": [MESH_N, MESH_N, 1],
                "lower_left_cm": [-7.5 * PITCH_CM, -7.5 * PITCH_CM, FUEL_BOTTOM_CM],
                "upper_right_cm": [7.5 * PITCH_CM, 7.5 * PITCH_CM, FUEL_TOP_CM],
                "score": "fission reaction rate",
            },
            "batches": args.batches,
            "inactive_batches": args.inactive,
            "particles_per_batch": args.particles,
            "seed": args.seed,
            "nuclear_data": os.environ.get("OPENMC_CROSS_SECTIONS", "UNSET"),
        },
        "model_input_sha256": input_xml_sha256,
        "comparison_scope": "exploratory normalized radial-shape comparison; not uncertainty-weighted acceptance",
        "status": "PREPARED_NOT_RUN",
    }
    (output / "beavrs_run_manifest.json").write_text(json.dumps(provenance, indent=2) + "\n")
    (output / "beavrs_measurements_normalized.json").write_text(
        json.dumps(measurements, indent=2) + "\n"
    )
    (output / "beavrs_assembly_mesh_map.json").write_text(
        json.dumps({k: list(v) for k, v in sorted(assembly_map.items())}, indent=2) + "\n"
    )
    print(json.dumps({"prepared": True, "output": str(output), "detectors": len(measurements)}))


def analyze(args: argparse.Namespace) -> None:
    import openmc

    output = Path(args.output).resolve()
    manifest_path = output / "beavrs_run_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    measurements = json.loads((output / "beavrs_measurements_normalized.json").read_text())
    assembly_map = {
        key: tuple(value)
        for key, value in json.loads((output / "beavrs_assembly_mesh_map.json").read_text()).items()
    }
    statepoints = sorted(output.glob("statepoint.*.h5"), key=lambda p: int(re.search(r"statepoint\.(\d+)\.h5$", p.name).group(1)))
    if not statepoints:
        raise FileNotFoundError(f"no OpenMC statepoint found under {output}")
    statepoint_path = statepoints[-1]
    with openmc.StatePoint(statepoint_path) as sp:
        tally = sp.get_tally(name=TALLY_NAME)
        mesh_filter = next(f for f in tally.filters if isinstance(f, openmc.MeshFilter))
        filter_bins = [tuple(int(i) for i in b) for b in mesh_filter.bins]
        raw_mean = tally.mean[:, 0, 0]
        raw_sd = tally.std_dev[:, 0, 0]
        values: dict[str, float] = {}
        tally_sds: dict[str, float] = {}
        for label in measurements:
            ix, iy = assembly_map[label]
            try:
                flat_index = filter_bins.index((ix, iy, 1))
            except ValueError as exc:
                raise ValueError(f"mesh bin {(ix, iy, 1)} missing for detector {label}") from exc
            value = float(raw_mean[flat_index])
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"invalid calculated fission rate for {label}: {value}")
            values[label] = value
            tally_sds[label] = float(raw_sd[flat_index])
        mean = sum(values.values()) / len(values)
        calculated = {label: value / mean for label, value in values.items()}
        residuals = {label: calculated[label] - measurements[label] for label in measurements}
        n = len(residuals)
        rmse = math.sqrt(sum(v * v for v in residuals.values()) / n)
        mae = sum(abs(v) for v in residuals.values()) / n
        mape = 100.0 * sum(abs(residuals[k] / measurements[k]) for k in residuals) / n
        obs = [measurements[k] for k in measurements]
        pred = [calculated[k] for k in measurements]
        obs_mean = sum(obs) / n
        pred_mean = sum(pred) / n
        cov = sum((a - obs_mean) * (b - pred_mean) for a, b in zip(obs, pred))
        denom = math.sqrt(
            sum((a - obs_mean) ** 2 for a in obs) * sum((b - pred_mean) ** 2 for b in pred)
        )
        correlation = cov / denom if denom > 0 else float("nan")
        keff = float(sp.keff.nominal_value)
        keff_sd = float(sp.keff.std_dev)
        statepoint_batches = int(sp.n_batches)
        relative_tally_sd = {label: 100.0 * tally_sds[label] / values[label] for label in values}

    rows = []
    for label in sorted(measurements):
        rows.append({
            "assembly": label,
            "measured_normalized": measurements[label],
            "calculated_normalized": calculated[label],
            "residual_calculated_minus_measured": residuals[label],
            "absolute_relative_error_percent": 100.0 * abs(residuals[label]) / measurements[label],
            "calculated_raw_fission_rate": values[label],
            "calculated_raw_fission_rate_sd": tally_sds[label],
            "raw_tally_relative_statistical_sd_percent": relative_tally_sd[label],
        })
    with (output / "beavrs_cycle1_day0_map_comparison.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    result = {
        "status": "PRELIMINARY_EXPERIMENTAL_COMPARISON",
        "physical_validation_claim": "NOT_ESTABLISHED",
        "benchmark": "BEAVRS Cycle 1 day 0",
        "upstream_commit": MODEL_COMMIT,
        "statepoint": statepoint_path.name,
        "statepoint_sha256": sha256_file(statepoint_path),
        "batches_completed": statepoint_batches,
        "keff": {"mean": keff, "standard_deviation": keff_sd},
        "detector_count": n,
        "metrics": {
            "normalized_map_rmse": rmse,
            "normalized_map_mae": mae,
            "mean_absolute_relative_error_percent": mape,
            "pearson_correlation": correlation,
            "mean_raw_tally_relative_statistical_sd_percent": sum(relative_tally_sd.values()) / len(relative_tally_sd),
            "max_raw_tally_relative_statistical_sd_percent": max(relative_tally_sd.values()),
        },
        "limitations": [
            "Shutdown bank SE is explicitly set to 230 steps to match the Cycle 1 day-0 record, overriding upstream default 228 while retaining its axial step width; geometry and sensitivity review remain necessary.",
            "The tilt-corrected measurement map is a derived reference; uncertainty from tilt correction must be considered. The comparison is normalized shape, not absolute power validation.",
            "Measurement uncertainty and model-form uncertainty are not propagated.",
            "Normalization-induced covariance between detector bins is not propagated; reported tally SDs are raw-bin relative Monte Carlo uncertainties.",
            "No acceptance threshold has been established by the benchmark authors for this exact model setup.",
            "This validates neither the legacy burnup-state QUBO mapping nor CB-PFR ranking effectiveness.",
            "QUBO formulation does not by itself establish quantum-device execution or quantum advantage.",
        ],
        "files": {
            "comparison_csv": "beavrs_cycle1_day0_map_comparison.csv",
            "manifest_json": "beavrs_run_manifest.json",
        },
    }
    (output / "beavrs_cycle1_day0_map_comparison.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, allow_nan=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("prepare", "analyze"), required=True)
    parser.add_argument("--output", default="beavrs-run")
    parser.add_argument("--beavrs-root", default=".")
    parser.add_argument("--batches", type=int, default=500)
    parser.add_argument("--inactive", type=int, default=50)
    parser.add_argument("--particles", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=20261011)
    args = parser.parse_args()
    if args.batches <= 0 or args.particles <= 0 or args.inactive < 0 or args.inactive >= args.batches:
        parser.error("require batches > 0, particles > 0, and 0 <= inactive < batches")
    if args.mode == "prepare":
        prepare(args)
    else:
        analyze(args)


if __name__ == "__main__":
    main()
