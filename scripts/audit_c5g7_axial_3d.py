#!/usr/bin/env python3
"""Audit generated C5G7 3-D OpenMC XML and export a statepoint mesh summary."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _numbers(parent: ET.Element, tag: str, cast=float) -> list:
    node = parent.find(tag)
    if node is None or not (node.text or "").strip():
        raise ValueError(f"Missing XML field: {tag}")
    return [cast(token) for token in node.text.split()]


def audit_inputs(candidate_root: Path) -> dict:
    model3d = candidate_root / "model" / "3d"
    required = ("geometry.xml", "materials.xml", "settings.xml", "tallies.xml", "mgxs.h5")
    missing = [name for name in required if not (model3d / name).is_file()]
    if missing:
        raise ValueError(f"Missing generated 3-D input files: {missing}")

    geometry = ET.parse(model3d / "geometry.xml").getroot()
    lattices = [node for node in geometry.findall(".//lattice") if node.attrib.get("id") == "201"]
    if len(lattices) != 1:
        raise ValueError(f"Expected exactly one core lattice id 201; found {len(lattices)}")
    lattice = lattices[0]
    dimensions = _numbers(lattice, "dimension", int)
    lower_left = _numbers(lattice, "lower_left")
    pitch = _numbers(lattice, "pitch")
    if dimensions != [3, 3, 10]:
        raise ValueError(f"Unexpected axial core-lattice dimensions: {dimensions}")
    if lower_left != [-32.13, -32.13, -107.1]:
        raise ValueError(f"Unexpected core-lattice lower-left: {lower_left}")
    if pitch != [21.42, 21.42, 21.42]:
        raise ValueError(f"Unexpected core-lattice pitch: {pitch}")

    z_surfaces = {}
    for surface in geometry.findall(".//surface"):
        name = surface.attrib.get("name", "")
        if name in {"Big Core z-min", "Big Core z-max"}:
            coeffs = [float(x) for x in surface.attrib.get("coeffs", "").split()]
            if len(coeffs) != 1:
                raise ValueError(f"Cannot parse axial surface {name}")
            z_surfaces[name] = {"z_cm": coeffs[0], "boundary": surface.attrib.get("boundary", "")}
    expected_surfaces = {
        "Big Core z-min": {"z_cm": -107.1, "boundary": "reflective"},
        "Big Core z-max": {"z_cm": 107.1, "boundary": "vacuum"},
    }
    if z_surfaces != expected_surfaces:
        raise ValueError(f"Unexpected Z-boundary configuration: {z_surfaces}")

    tallies = ET.parse(model3d / "tallies.xml").getroot()
    meshes = [node for node in tallies.findall(".//mesh") if node.attrib.get("id") == "1"]
    if len(meshes) != 1:
        raise ValueError(f"Expected exactly one 3-D regular mesh id 1; found {len(meshes)}")
    mesh = meshes[0]
    mesh_dimension = _numbers(mesh, "dimension", int)
    mesh_lower = _numbers(mesh, "lower_left")
    mesh_upper = _numbers(mesh, "upper_right")
    if mesh_dimension != [51, 51, 30]:
        raise ValueError(f"Mesh is not a true 3-D mesh with expected bins: {mesh_dimension}")
    if mesh_lower != [-32.13, -32.13, -107.1] or mesh_upper != [32.13, 32.13, 107.1]:
        raise ValueError(f"Unexpected mesh physical bounds: {mesh_lower} to {mesh_upper}")

    tally_nodes = [node for node in tallies.findall(".//tally") if node.attrib.get("id") == "1"]
    if len(tally_nodes) != 1:
        raise ValueError(f"Expected exactly one axial mesh tally id 1; found {len(tally_nodes)}")
    score_text = (tally_nodes[0].findtext("scores") or "").split()
    if score_text != ["flux", "fission", "nu-fission"]:
        raise ValueError(f"Unexpected mesh tally scores: {score_text}")

    settings = ET.parse(model3d / "settings.xml").getroot()
    batches = int(settings.findtext("batches", "0"))
    inactive = int(settings.findtext("inactive", "-1"))
    particles = int(settings.findtext("particles", "0"))
    seed_text = settings.findtext("seed")
    if batches <= 0 or inactive < 0 or inactive >= batches or particles <= 0:
        raise ValueError(f"Invalid transport budget: batches={batches}, inactive={inactive}, particles={particles}")
    if seed_text is None:
        raise ValueError("A deterministic seed was not written to settings.xml")

    return {
        "status": "generated_3d_inputs_passed_structural_audit",
        "candidate_id": candidate_root.name,
        "model_files": {
            name: {"bytes": (model3d / name).stat().st_size, "sha256": sha256_file(model3d / name)}
            for name in required
        },
        "core_lattice": {
            "dimension_xyz": dimensions,
            "lower_left_cm_xyz": lower_left,
            "pitch_cm_xyz": pitch,
            "axial_layers": dimensions[2],
            "source_axial_definition": "9 repeated cross-sectional layers + 1 all-reflector top layer",
        },
        "axial_boundaries": z_surfaces,
        "mesh_tally": {
            "dimension_xyz": mesh_dimension,
            "lower_left_cm_xyz": mesh_lower,
            "upper_right_cm_xyz": mesh_upper,
            "bin_width_cm_xyz": [
                (mesh_upper[i] - mesh_lower[i]) / mesh_dimension[i] for i in range(3)
            ],
            "scores": score_text,
            "bin_count": math.prod(mesh_dimension),
        },
        "settings": {
            "batches": batches,
            "inactive": inactive,
            "active_batches": batches - inactive,
            "particles_per_batch": particles,
            "seed": int(seed_text),
            "energy_mode": settings.findtext("energy_mode"),
        },
        "nonclaims": [
            "Structural XML checks are not a transport calculation or benchmark acceptance.",
            "The upstream axial layer pattern and one-sided axial boundary conditions remain assumptions requiring independent review.",
            "Tally values are not absolute-power normalized.",
        ],
    }


def export_statepoint(statepoint: Path, output_dir: Path) -> dict:
    try:
        import h5py
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Statepoint export requires h5py and numpy") from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    with h5py.File(statepoint, "r") as h5:
        mesh_group = h5["tallies/meshes/mesh 1"]
        dims = [int(v) for v in mesh_group["dimension"][()]]
        lower = [float(v) for v in mesh_group["lower_left"][()]]
        upper = [float(v) for v in mesh_group["upper_right"][()]]
        if len(dims) != 3 or dims[2] <= 1:
            raise ValueError(f"Statepoint does not contain a genuinely 3-D mesh: {dims}")
        tally_path = "tallies/tally 1"
        if tally_path not in h5:
            raise ValueError("Statepoint is missing tally 1")
        tally = h5[tally_path]
        score_names = [
            value.decode("utf-8") if isinstance(value, bytes) else str(value)
            for value in tally["score_bins"][()]
        ]
        if score_names != ["flux", "fission", "nu-fission"]:
            raise ValueError(f"Unexpected statepoint score bins: {score_names}")
        raw = np.asarray(tally["results"][()], dtype=np.float64)
        n_realizations = int(tally["n_realizations"][()])
        if raw.shape != (math.prod(dims), len(score_names), 2):
            raise ValueError(f"Unexpected raw tally shape {raw.shape} for mesh {dims}")
        if n_realizations <= 1:
            raise ValueError(f"Not enough active realizations for uncertainty estimates: {n_realizations}")
        sums = raw[:, :, 0]
        sums_sq = raw[:, :, 1]
        means_flat = sums / n_realizations
        variance_of_mean = (sums_sq / n_realizations - means_flat**2) / (n_realizations - 1)
        standard_error_flat = np.sqrt(np.maximum(variance_of_mean, 0.0))
        if not np.isfinite(means_flat).all() or not np.isfinite(standard_error_flat).all():
            raise ValueError("Statepoint tally contains non-finite means or standard errors")
        # OpenMC mesh-filter bins are serialized with X varying fastest; expose
        # a predictable [z, y, x, score] array for scientific plotting.
        nx, ny, nz = dims
        means = means_flat.reshape(nz, ny, nx, len(score_names))
        standard_error = standard_error_flat.reshape(nz, ny, nx, len(score_names))
        relative_error = np.divide(
            100.0 * standard_error,
            np.abs(means),
            out=np.full_like(standard_error, np.nan),
            where=np.abs(means) > 0.0,
        )
        x_centers = lower[0] + (np.arange(nx) + 0.5) * ((upper[0] - lower[0]) / nx)
        y_centers = lower[1] + (np.arange(ny) + 0.5) * ((upper[1] - lower[1]) / ny)
        z_centers = lower[2] + (np.arange(nz) + 0.5) * ((upper[2] - lower[2]) / nz)
        state = {
            "sha256": sha256_file(statepoint),
            "path": str(statepoint),
            "n_batches": int(h5["n_batches"][()]),
            "n_inactive": int(h5["n_inactive"][()]),
            "n_particles": int(h5["n_particles"][()]),
            "n_realizations": n_realizations,
            "seed": int(h5["seed"][()]),
        }

    npz_path = output_dir / "axial_tally_3d.npz"
    np.savez_compressed(
        npz_path,
        mean=means.astype(np.float32),
        standard_error=standard_error.astype(np.float32),
        relative_error_percent=relative_error.astype(np.float32),
        score_names=np.asarray(score_names),
        x_centers_cm=x_centers.astype(np.float32),
        y_centers_cm=y_centers.astype(np.float32),
        z_centers_cm=z_centers.astype(np.float32),
    )
    score_summary = {}
    for idx, score in enumerate(score_names):
        valid = np.isfinite(means[..., idx])
        positive = means[..., idx] > 0
        rel = relative_error[..., idx]
        finite_rel = rel[np.isfinite(rel) & positive]
        score_summary[score] = {
            "finite_bin_count": int(valid.sum()),
            "nonzero_mean_bin_count": int(positive.sum()),
            "mean_of_bin_means": float(np.mean(means[..., idx][valid])),
            "max_bin_mean": float(np.max(means[..., idx][valid])),
            "mean_of_bin_standard_errors": float(np.mean(standard_error[..., idx][valid])),
            "relative_error_percent_median_positive_bins": (
                float(np.median(finite_rel)) if finite_rel.size else None
            ),
            "relative_error_percent_p95_positive_bins": (
                float(np.percentile(finite_rel, 95)) if finite_rel.size else None
            ),
        }
    summary = {
        "schema_version": 1,
        "status": "3d_openmc_statepoint_mesh_exported",
        "statepoint": state,
        "mesh": {
            "dimension_xyz": dims,
            "lower_left_cm_xyz": lower,
            "upper_right_cm_xyz": upper,
            "array_layout": "[z, y, x, score]",
            "array_shape": list(means.shape),
            "bin_count": math.prod(dims),
        },
        "scores": score_names,
        "uncertainty_method": (
            "Standard error reconstructed from OpenMC accumulated sum and sum-of-squares "
            "for each tally bin: sqrt((sum_sq/n - mean^2)/(n-1)); negative roundoff is clipped to zero."
        ),
        "score_summary": score_summary,
        "npz": {"path": str(npz_path), "bytes": npz_path.stat().st_size, "sha256": sha256_file(npz_path)},
        "nonclaims": [
            "Values are source-normalized Monte Carlo tallies, not absolute reactor power.",
            "A successful statepoint export does not establish benchmark agreement or physical validation.",
            "Zero/near-zero bins can have undefined or unstable relative statistical error.",
        ],
    }
    summary_path = output_dir / "AXIAL_3D_STATEPOINT_SUMMARY.json"
    summary_path.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", type=Path, help="Extracted candidate root")
    parser.add_argument("--statepoint", type=Path, help="Optional OpenMC 3-D statepoint to export")
    parser.add_argument("--output-dir", type=Path, help="Where NPZ and statepoint summary should be written")
    parser.add_argument("--summary-out", type=Path, help="Where the input XML audit JSON should be written")
    args = parser.parse_args()

    if args.candidate_root:
        result = audit_inputs(args.candidate_root.resolve())
        serialized = json.dumps(result, indent=2, allow_nan=False) + "\n"
        if args.summary_out:
            args.summary_out.parent.mkdir(parents=True, exist_ok=True)
            args.summary_out.write_text(serialized, encoding="utf-8")
        print(serialized, end="")
    if args.statepoint:
        if not args.output_dir:
            parser.error("--output-dir is required with --statepoint")
        result = export_statepoint(args.statepoint.resolve(), args.output_dir.resolve())
        print(json.dumps(result, indent=2, allow_nan=False))
    if not args.candidate_root and not args.statepoint:
        parser.error("Provide --candidate-root and/or --statepoint")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
