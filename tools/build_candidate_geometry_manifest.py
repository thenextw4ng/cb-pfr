#!/usr/bin/env python3
"""Generate CB-PFR's browser geometry manifest from archived OpenMC XML inputs.

No OpenMC transport calculation is executed. Core/pin universe rows, cell names,
material identifiers, pin radius, pitch, boundary conditions, and per-candidate
input hashes are extracted from the archive's geometry.xml and materials.xml.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

EXPECTED_LAYOUTS = {"MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM"}
WORKFLOW_RUN_ID = 38182056526
ARTIFACT_ID = 11719691969


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def floats(value: str) -> list[float]:
    return [float(item) for item in value.split()]


def ints(value: str) -> list[int]:
    return [int(item) for item in value.split()]


def universe_rows(lattice: ET.Element) -> list[list[int]]:
    nx, ny = ints(lattice.findtext("dimension", ""))
    values = ints(lattice.findtext("universes", ""))
    if len(values) != nx * ny:
        raise ValueError(f"Lattice {lattice.get('id')} dimension/value mismatch")
    return [values[offset:offset + nx] for offset in range(0, len(values), nx)]


def build_manifest(archive: Path) -> dict:
    archive_bytes = archive.read_bytes()
    with zipfile.ZipFile(archive) as bundle:
        prefixes = sorted({
            name.split("/")[0]
            for name in bundle.namelist()
            if name.startswith("c5g7-2x2-") and name.endswith("/model/2d/geometry.xml")
        })
        if len(prefixes) != 6:
            raise ValueError(f"Expected six candidate geometry.xml files; found {len(prefixes)}")

        candidates = []
        shared = None
        core = None
        bounds = None
        for prefix in prefixes:
            geometry_path = f"{prefix}/model/2d/geometry.xml"
            materials_path = f"{prefix}/model/2d/materials.xml"
            geometry_bytes = bundle.read(geometry_path)
            materials_bytes = bundle.read(materials_path)
            geometry = ET.fromstring(geometry_bytes)
            materials = ET.fromstring(materials_bytes)
            material_names = {
                str(item.get("id")): item.get("name")
                for item in materials.findall("material")
            }
            cells = geometry.findall("cell")
            lattices = geometry.findall("lattice")

            fill_by_universe = {
                int(cell.get("universe")): cell.get("fill")
                for cell in cells if cell.get("fill") is not None
            }
            assemblies = {
                str(universe_id): {
                    "code": "U" if fill == "101" else "M" if fill == "103" else "R",
                    "lattice_id": int(fill),
                }
                for universe_id, fill in fill_by_universe.items()
                if fill in {"101", "103", "105"}
            }

            core = next((item for item in lattices if item.get("id") == "201"), None)
            if core is None:
                raise ValueError(f"Core lattice 201 missing from {geometry_path}")
            core_grid = universe_rows(core)
            if ints(core.findtext("dimension", "")) != [3, 3] or len(core_grid) != 3 or any(len(row) != 3 for row in core_grid):
                raise ValueError(f"Expected a 3 x 3 core lattice in {geometry_path}")
            layout_rows = ["".join(assemblies[str(uid)]["code"] for uid in row) for row in core_grid]
            signature = "".join(layout_rows[r][c] for r, c in ((0, 0), (0, 1), (1, 0), (1, 1)))
            expected_signature = prefix.rsplit("-", 1)[-1]
            if signature != expected_signature or signature not in EXPECTED_LAYOUTS:
                raise ValueError(f"XML layout {signature} does not match candidate folder {prefix}")
            if layout_rows[0][2] != "R" or layout_rows[1][2] != "R" or layout_rows[2] != "RRR":
                raise ValueError(f"Expected L-shaped water reflector in {geometry_path}")

            pin_lattices = {}
            for lattice in lattices:
                lattice_id = lattice.get("id")
                if lattice_id not in {"101", "103"}:
                    continue
                grid = universe_rows(lattice)
                dimensions = ints(lattice.findtext("dimension", ""))
                if dimensions != [17, 17] or len(grid) != 17 or any(len(row) != 17 for row in grid):
                    raise ValueError(f"Expected 17 x 17 pin lattice {lattice_id} in {geometry_path}")
                pin_lattices[lattice_id] = {
                    "id": int(lattice_id),
                    "name": lattice.get("name"),
                    "dimensions": dimensions,
                    "pitch_cm": floats(lattice.findtext("pitch", "")),
                    "lower_left_cm": floats(lattice.findtext("lower_left", "")),
                    "universe_grid": grid,
                }
            if set(pin_lattices) != {"101", "103"}:
                raise ValueError(f"Missing UO2/MOX pin lattice in {geometry_path}")

            pin_universes = {}
            for cell in cells:
                uid = cell.get("universe")
                if uid not in {"1", "2", "3", "4", "5", "6"} or not cell.get("material") or cell.get("region") != "-1":
                    continue
                moderator = next((
                    other for other in cells
                    if other.get("universe") == uid and other.get("region") == "1" and other.get("material")
                ), None)
                if moderator is None:
                    raise ValueError(f"Pin universe {uid} lacks a moderator region in {geometry_path}")
                material_id = str(cell.get("material"))
                moderator_id = str(moderator.get("material"))
                pin_universes[uid] = {
                    "universe_id": int(uid),
                    "cell_id": int(cell.get("id")),
                    "name": cell.get("name"),
                    "material_id": int(material_id),
                    "material_name": material_names[material_id],
                    "moderator_material_id": int(moderator_id),
                    "moderator_material_name": material_names[moderator_id],
                }
            if set(pin_universes) != {"1", "2", "3", "4", "5", "6"}:
                raise ValueError(f"Incomplete material map in {geometry_path}")

            cylinder = next((item for item in geometry.findall("surface") if item.get("type") == "z-cylinder"), None)
            if cylinder is None:
                raise ValueError(f"Pin cylinder not found in {geometry_path}")
            radius = floats(cylinder.get("coeffs", ""))[-1]
            bounds = []
            for name in ("Core x-min", "Core x-max", "Core y-min", "Core y-max"):
                surface = next((item for item in geometry.findall("surface") if item.get("name") == name), None)
                if surface is None:
                    raise ValueError(f"Core boundary {name} missing in {geometry_path}")
                bounds.append({
                    "name": name, "type": surface.get("type"),
                    "condition": surface.get("boundary"),
                    "coordinate_cm": floats(surface.get("coeffs", ""))[-1],
                })

            current_shared = {
                "assemblies": assemblies,
                "pin_lattices": pin_lattices,
                "pin_universes": pin_universes,
                "materials_by_id": material_names,
                "pin_radius_cm": radius,
                "boundary_conditions": bounds,
            }
            if shared is None:
                shared = current_shared
            else:
                for key, value in current_shared.items():
                    if shared[key] != value:
                        raise ValueError(f"Shared model property {key} differs in {geometry_path}")

            candidates.append({
                "candidate_id": prefix,
                "layout_signature": signature,
                "source_member": geometry_path,
                "geometry_xml_sha256": digest(geometry_bytes),
                "materials_xml_sha256": digest(materials_bytes),
                "source_matches_candidate_signature": True,
                "signature_derived_from_xml": signature,
                "core_universe_grid": core_grid,
            })

    if {item["layout_signature"] for item in candidates} != EXPECTED_LAYOUTS:
        raise ValueError("Expected the six unique fuel layouts exactly once")
    dimensions = ints(core.findtext("dimension", ""))
    return {
        "schema_version": 1,
        "provenance": {
            "source_type": "GitHub Actions artifact containing generated OpenMC inputs",
            "artifact_name": "c5g7-study-640000",
            "workflow_run_id": WORKFLOW_RUN_ID,
            "artifact_id": ARTIFACT_ID,
            "archive_filename": archive.name,
            "archive_sha256": digest(archive_bytes),
            "member_selection": "Per-candidate model/2d/geometry.xml and materials.xml; universe rows, material cells, dimensions, boundary conditions, and hashes read directly from XML.",
            "generator_version": "1.0.0",
        },
        "core_lattice": {
            "id": int(core.get("id")), "name": core.get("name"),
            "dimensions": dimensions, "pitch_cm": floats(core.findtext("pitch", "")),
            "lower_left_cm": floats(core.findtext("lower_left", "")),
        },
        "assemblies": shared["assemblies"],
        "pin_geometry": {
            "dimensions": [17, 17],
            "pitch_cm": shared["pin_lattices"]["101"]["pitch_cm"],
            "pin_radius_cm": shared["pin_radius_cm"],
            "extent_cm": [
                abs(bounds[1]["coordinate_cm"] - bounds[0]["coordinate_cm"]),
                abs(bounds[3]["coordinate_cm"] - bounds[2]["coordinate_cm"]),
            ],
        },
        "pin_lattices": shared["pin_lattices"],
        "materials": {"by_id": shared["materials_by_id"], "pin_universes": shared["pin_universes"]},
        "boundary_conditions": shared["boundary_conditions"],
        "candidates": candidates,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path, help="Downloaded c5g7-study-640000 artifact ZIP")
    parser.add_argument("--output", required=True, type=Path, help="Output path for the JSON geometry manifest")
    args = parser.parse_args()
    if not args.archive.is_file():
        parser.error(f"Archive not found: {args.archive}")
    manifest = build_manifest(args.archive.resolve())
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Generated {output} ({output.stat().st_size} bytes)")
    print("Layouts verified:", ", ".join(item["layout_signature"] for item in manifest["candidates"]))
    print("Archive SHA-256:", manifest["provenance"]["archive_sha256"])
    print("No OpenMC transport calculation was run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
