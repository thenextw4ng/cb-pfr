#!/usr/bin/env python3
"""Run a BEAVRS Cycle-1 beginning-of-cycle radial fission-map comparison.

This is a preliminary experimental comparison, not an automatic certification of
physical validation. The BEAVRS builder's default bank-E insertion differs from
the archived Cycle-1 day-0 measurement (228 vs 230 steps withdrawn); that
mismatch is explicitly recorded in the output. The measured detector map is
normalized, so the calculated fission rates are normalized over the same 58
instrumented assembly positions before comparison.
"""
from __future__ import annotations

import argparse
import csv
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
MESH_N = 17
MEASUREMENT_REL = Path("measurements/detector_signals/cycle_1/0/radial_measurements_full.csv")
SUMMARY_REL = Path("measurements/detector_signals/cycle_1/0/summary.csv")
TALLY_NAME = "beavrs_cycle1_day0_assembly_fission_rate"
MODEL_COMMIT = "1ccae04dc3830a5977f08ed7f5f7e1e51ded0d22"


def load_measurements(path: Path) -> dict[str, float]:
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
    if len(values) != 58:
        raise ValueError(f"expected 58 instrumented assembly measurements, got {len(values)}")
    mean = sum(values.values()) / len(values)
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
            # The 17x17 mesh covers template rows/columns 1..17. OpenMC mesh
            # y indices increase from the lower boundary; the lattice template
            # is stored from top to bottom.
            if not (1 <= row_index <= 17 and 1 <= col_index <= 17):
                continue
            ix = col_index  # 1-based; col_index 1 maps to first mesh bin
            iy = 18 - row_index  # row 1 -> bin 17; row 17 -> bin 1
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
    # all banks withdrawn except D at 213 steps. Upstream bank E default is 228
    # while the measurement reports 230; we retain the supported upstream value
    # and record this as a model-to-measurement mismatch rather than extrapolate.
    rcca = {
        "A": 228, "B": 228, "C": 228, "D": 213,
        "SA": 228, "SB": 228, "SC": 228, "SD": 228, "SE": 228,
    }
    builder = BEAVRS(boron_ppm=975.25, is_symmetric=False, is_2d=False, rcca_z=rcca)
    builder.set_params(particles=args.particles, batches=args.batches, inactive=args.inactive)
    builder.model = builder.build_openmc_model()

    mesh = openmc.RegularMesh()
    mesh.dimension = (MESH_N, MESH_N, 1)
    mesh.lower_left = (-8 * PITCH_CM, -8 * PITCH_CM, FUEL_BOTTOM_CM)
    mesh.upper_right = (8 * PITCH_CM, 8 * PITCH_CM, FUEL_TOP_CM)
    tally = openmc.Tally(name=TALLY_NAME)
    tally.filters = [openmc.MeshFilter(mesh)]
    tally.scores = ["fission"]
    builder.tally_meshes = [mesh]
    builder.tallies = [tally]
    builder.model = builder.build_openmc_model()
    builder.model.settings.seed = args.seed
    builder.model.export_to_xml()

    assembly_map = build_assembly_map(Core.core_lattice_template)
    measurements = load_measurements(beavrs_root / MEASUREMENT_REL)
    missing = sorted(set(measurements) - set(assembly_map))
    if missing:
        raise ValueError(f"measurement labels not present in assembly map: {missing}")
    provenance = {
        "benchmark": "BEAVRS Cycle 1 day 0 radial detector map",
        "upstream_repository": "https://github.com/mit-crpg/BEAVRS",
        "upstream_commit": MODEL_COMMIT,
        "measured_data": str(beavrs_root / MEASUREMENT_REL),
        "measured_summary": str(beavrs_root / SUMMARY_REL),
        "measured_detector_count": len(measurements),
        "measurement_normalization": "mean over 58 reported normalized detector values = 1",
        "model": {
            "dimension": "full 3-D full-core upstream BEAVRS geometry",
            "boron_ppm": 975.25,
            "temperature_K": 566.483,
            "RCCA_steps_withdrawn": rcca,
            "measured_RCCE_steps_withdrawn": 230,
            "upstream_model_RCCE_steps_withdrawn": 228,
            "known_mismatch": "Bank E insertion differs by 2 reported steps; upstream builder range is 0..228.",
            "fuel_axial_range_cm": [FUEL_BOTTOM_CM, FUEL_TOP_CM],
            "mesh": {
                "dimension": [MESH_N, MESH_N, 1],
                "lower_left_cm": [-8 * PITCH_CM, -8 * PITCH_CM, FUEL_BOTTOM_CM],
                "upper_right_cm": [8 * PITCH_CM, 8 * PITCH_CM, FUEL_TOP_CM],
                "score": "fission reaction rate",
            },
            "batches": args.batches,
            "inactive_batches": args.inactive,
            "particles_per_batch": args.particles,
            "seed": args.seed,
            "nuclear_data": os.environ.get("OPENMC_CROSS_SECTIONS", "UNSET"),
        },
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
        values: dict[str, float] = {}
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

    rows = []
    for label in sorted(measurements):
        rows.append({
            "assembly": label,
            "measured_normalized": measurements[label],
            "calculated_normalized": calculated[label],
            "residual_calculated_minus_measured": residuals[label],
            "absolute_relative_error_percent": 100.0 * abs(residuals[label]) / measurements[label],
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
        "statepoint_sha256": __import__("hashlib").sha256(statepoint_path.read_bytes()).hexdigest(),
        "batches_completed": statepoint_batches,
        "keff": {"mean": keff, "standard_deviation": keff_sd},
        "detector_count": n,
        "metrics": {
            "normalized_map_rmse": rmse,
            "normalized_map_mae": mae,
            "mean_absolute_relative_error_percent": mape,
            "pearson_correlation": correlation,
        },
        "limitations": [
            "BEAVRS upstream model uses bank E withdrawn 228 steps; Cycle 1 day-0 measurements report 230.",
            "The measurement map has been normalized; this is a shape comparison, not absolute power validation.",
            "This run does not propagate measurement uncertainty or model-form uncertainty.",
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
    parser.add_argument("--batches", type=int, default=250)
    parser.add_argument("--inactive", type=int, default=30)
    parser.add_argument("--particles", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20261011)
    args = parser.parse_args()
    if args.batches <= 0 or args.particles <= 0 or args.inactive < 0 or args.inactive >= args.batches:
        parser.error("require batches > particles > 0 and 0 <= inactive < batches")
    if args.mode == "prepare":
        prepare(args)
    else:
        analyze(args)


if __name__ == "__main__":
    main()
