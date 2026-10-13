#!/usr/bin/env python3
"""Prepare an archived C5G7 candidate for a reproducible 3-D OpenMC tally run.

The archived 3-D geometry builder is preserved except for explicit, checked
patches: it is redirected from the shared 2-D tally to a real 3-D mesh tally,
and its transport budget/seed become configurable through environment variables.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
import zipfile

CANDIDATES = (
    "c5g7-2x2-MMUU",
    "c5g7-2x2-MUMU",
    "c5g7-2x2-MUUM",
    "c5g7-2x2-UMMU",
    "c5g7-2x2-UMUM",
    "c5g7-2x2-UUMM",
)
MESH_DIMENSION = [51, 51, 30]
MESH_LOWER_LEFT_CM = [-32.13, -32.13, -107.1]
MESH_UPPER_RIGHT_CM = [32.13, 32.13, 107.1]
AXIAL_LATTICE_DIMENSION = [3, 3, 10]
AXIAL_PITCH_CM = [21.42, 21.42, 21.42]

TALLY_3D_SOURCE = '''"""Three-dimensional axial mesh tally for the archived C5G7 3-D model."""
import openmc

# X/Y retain the archived 51 x 51 resolution. Z divides the 214.2 cm
# archived axial extent into 30 bins (7.14 cm/bin; three bins per 21.42 cm
# lattice layer). Do not substitute the 2-D [51, 51, 1] tally here.
mesh = openmc.RegularMesh(mesh_id=1)
mesh.dimension = [51, 51, 30]
mesh.lower_left = [-32.13, -32.13, -107.1]
mesh.upper_right = [32.13, 32.13, 107.1]
mesh_filter = openmc.MeshFilter(mesh)

tallies = {}
tallies["Axial Mesh Rates"] = openmc.Tally(tally_id=1, name="axial mesh tally")
tallies["Axial Mesh Rates"].filters = [mesh_filter]
tallies["Axial Mesh Rates"].scores = ["flux", "fission", "nu-fission"]

# Keep a separate global tally for cross-checks, matching the archived model.
tallies["Global Rates"] = openmc.Tally(tally_id=2, name="global tally")
tallies["Global Rates"].scores = ["flux", "fission", "nu-fission"]
'''


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_extract(archive: Path, destination: Path) -> None:
    """Extract a ZIP only when every member resolves inside destination."""
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with zipfile.ZipFile(archive) as zipped:
        for info in zipped.infolist():
            target = (destination / info.filename).resolve()
            if target != root and root not in target.parents:
                raise ValueError(f"Unsafe archive member path: {info.filename}")
        zipped.extractall(destination)


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"Expected exactly one {label} anchor; found {count}")
    return text.replace(old, new, 1)


def patch_builder(builder_path: Path) -> tuple[str, str]:
    """Patch only known anchors and fail closed if upstream source has drifted."""
    original = builder_path.read_text(encoding="utf-8")
    patched = _replace_once(
        original,
        "import openmc\nimport sys\n",
        "import os\nimport openmc\nimport sys\n",
        "import block",
    )
    patched = _replace_once(
        patched,
        "from tally import tallies, mesh",
        "from tally_3d import tallies, mesh",
        "tally import",
    )
    for name, default in (("batches", "20000"), ("inactive", "500"), ("particles", "10000")):
        pattern = rf"(?m)^{name}\s*=\s*{default}\s*$"
        replacement = f'{name} = int(os.environ.get("CBPFR_3D_{name.upper()}", "{default}"))'
        patched, count = re.subn(pattern, replacement, patched)
        if count != 1:
            raise ValueError(f"Expected exactly one default for {name}; found {count}")
    patched = _replace_once(
        patched,
        "settings_file.particles = particles\n",
        "settings_file.particles = particles\n"
        'settings_file.seed = int(os.environ.get("CBPFR_3D_SEED", "640000"))\n',
        "settings seed",
    )
    builder_path.write_text(patched, encoding="utf-8")
    return hashlib.sha256(original.encode("utf-8")).hexdigest(), sha256_file(builder_path)


def prepare_candidate(candidate_root: Path, archive_sha256: str) -> dict:
    model_root = candidate_root / "model"
    builder = model_root / "3d" / "build-xml-3d.py"
    materials = model_root / "materials.py"
    lattices = model_root / "lattices.py"
    surfaces = model_root / "surfaces.py"
    if not all(p.is_file() for p in (builder, materials, lattices, surfaces)):
        raise FileNotFoundError(f"{candidate_root.name}: required archived model sources are incomplete")

    original_builder_sha256, prepared_builder_sha256 = patch_builder(builder)
    tally_path = model_root / "tally_3d.py"
    tally_path.write_text(TALLY_3D_SOURCE, encoding="utf-8")
    candidate_id = candidate_root.name
    signature = candidate_id.removeprefix("c5g7-2x2-")
    if signature not in {name.removeprefix("c5g7-2x2-") for name in CANDIDATES}:
        raise ValueError(f"Unexpected candidate ID: {candidate_id}")

    manifest = {
        "schema_version": 1,
        "candidate_id": candidate_id,
        "layout_signature": signature,
        "status": "prepared_input_not_yet_transport_validated",
        "source": {
            "archive_sha256": archive_sha256,
            "archived_builder_sha256": original_builder_sha256,
            "prepared_builder_sha256": prepared_builder_sha256,
            "upstream_builder_path": "model/3d/build-xml-3d.py",
        },
        "geometry_contract": {
            "lattice_dimension_xyz": AXIAL_LATTICE_DIMENSION,
            "lattice_pitch_cm_xyz": AXIAL_PITCH_CM,
            "mesh_dimension_xyz": MESH_DIMENSION,
            "mesh_lower_left_cm_xyz": MESH_LOWER_LEFT_CM,
            "mesh_upper_right_cm_xyz": MESH_UPPER_RIGHT_CM,
            "mesh_bin_width_cm_xyz": [
                (MESH_UPPER_RIGHT_CM[i] - MESH_LOWER_LEFT_CM[i]) / MESH_DIMENSION[i]
                for i in range(3)
            ],
            "mesh_scores": ["flux", "fission", "nu-fission"],
            "z_bins_per_lattice_layer": 3,
        },
        "inherited_axial_assumptions": {
            "active_lattice_layers": 9,
            "top_reflector_lattice_layers": 1,
            "bottom_z_boundary": "reflective",
            "top_z_boundary": "vacuum",
            "note": (
                "These are properties of the archived builder, not an independent "
                "benchmark sign-off. Review the axial arrangement and boundary conditions "
                "before making benchmark-acceptance claims."
            ),
        },
        "nonclaims": [
            "No transport run has been evidenced by preparing these inputs alone.",
            "The 3-D tally mesh records Monte Carlo estimates; it is not a power-normalized field.",
            "This model does not include burnup, depletion, thermal hydraulics, or time dependence.",
        ],
    }
    manifest_path = candidate_root / "AXIAL_3D_INPUT_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True, help="Verified C5G7 source ZIP")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for extracted/prepared inputs")
    parser.add_argument("--candidate", choices=(*CANDIDATES, "all"), default="c5g7-2x2-UMMU")
    args = parser.parse_args()

    archive = args.archive.resolve()
    output_dir = args.output_dir.resolve()
    if not archive.is_file():
        parser.error(f"Archive does not exist: {archive}")
    archive_sha = sha256_file(archive)
    safe_extract(archive, output_dir)

    selected = CANDIDATES if args.candidate == "all" else (args.candidate,)
    result = []
    for candidate_id in selected:
        matches = list(output_dir.rglob(f"{candidate_id}/model/3d/build-xml-3d.py"))
        if len(matches) != 1:
            raise RuntimeError(
                f"Expected one archived 3-D builder for {candidate_id}; found {len(matches)}"
            )
        candidate_root = matches[0].parents[2]
        result.append(prepare_candidate(candidate_root, archive_sha))

    print(json.dumps({
        "status": "prepared",
        "archive_sha256": archive_sha,
        "prepared_candidates": [item["candidate_id"] for item in result],
        "manifests": [
            str((output_dir / item["candidate_id"] / "AXIAL_3D_INPUT_MANIFEST.json"))
            for item in result
        ],
        "note": "Preparation is not evidence of an OpenMC transport result.",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
