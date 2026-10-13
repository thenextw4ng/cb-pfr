#!/usr/bin/env python3
"""Extract a compact visualization manifest from archived OpenMC C5G7 geometry XML.

This reads geometry.xml/materials.xml from the six recorded study cases in a GitHub
Actions artifact ZIP. It does not import OpenMC or run neutron transport.
"""
from __future__ import annotations
import argparse, hashlib, json, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

LAYOUTS = ("MUMU", "MMUU", "MUUM", "UMMU", "UUMM", "UMUM")
FILL_CODES = {"101": "U", "103": "M", "105": "R"}

def numeric_grid(text: str) -> list[list[int]]:
    return [[int(v) for v in line.split()] for line in text.strip().splitlines() if line.strip()]

def lattice_record(lattice: ET.Element, include_grid: bool = True) -> dict:
    record = {
        "id": int(lattice.attrib["id"]),
        "name": lattice.attrib.get("name"),
        "dimensions": [int(v) for v in lattice.findtext("dimension", "").split()],
        "lower_left_cm": [float(v) for v in lattice.findtext("lower_left", "").split()],
        "pitch_cm": [float(v) for v in lattice.findtext("pitch", "").split()],
    }
    if include_grid:
        record["universe_grid"] = numeric_grid(lattice.findtext("universes", ""))
    return record

def derive(archive: zipfile.ZipFile, layout: str) -> tuple[dict, ET.Element, bytes]:
    member = f"c5g7-2x2-{layout}/model/2d/geometry.xml"
    raw = archive.read(member)
    root = ET.fromstring(raw)
    lattices = {item.attrib["id"]: item for item in root.findall("lattice")}
    core = lattices.get("201")
    if core is None:
        raise ValueError(f"{member}: missing core lattice id 201")
    core_rec = lattice_record(core)
    cells = root.findall("cell")
    filled_cells = {cell.attrib["universe"]: cell for cell in cells if "fill" in cell.attrib}
    categories = []
    for row in core_rec["universe_grid"]:
        categories.append([
            FILL_CODES.get(filled_cells.get(str(universe), {}).attrib.get("fill", ""), "?")
            for universe in row
        ])
    signature = "".join(categories[r][c] for r in range(2) for c in range(2))
    candidate = {
        "candidate_id": f"c5g7-2x2-{layout}",
        "layout_signature": layout,
        "source_member": member,
        "geometry_xml_sha256": hashlib.sha256(raw).hexdigest(),
        "core_universe_grid": core_rec["universe_grid"],
        "assembly_grid": categories,
        "signature_derived_from_xml": signature,
        "source_matches_candidate_signature": signature == layout,
    }
    return candidate, root, raw

def build_manifest(archive_path: Path, artifact_name: str, run_id: int, artifact_id: int) -> dict:
    with zipfile.ZipFile(archive_path) as archive:
        parsed = {layout: derive(archive, layout) for layout in LAYOUTS}
        first = parsed["UMMU"][1]
        materials_member = "c5g7-2x2-UMMU/model/2d/materials.xml"
        materials_root = ET.fromstring(archive.read(materials_member))
        material_names = {m.attrib["id"]: m.attrib.get("name", "Material " + m.attrib["id"]) for m in materials_root.findall("material")}
        pin_materials = {}
        for cell in first.findall("cell"):
            universe, material = cell.attrib.get("universe"), cell.attrib.get("material")
            if cell.attrib.get("region") == "-1" and universe in ("1","2","3","4","5","6") and material:
                pin_materials[universe] = {"name": cell.attrib.get("name"), "material_id": material, "material_name": material_names.get(material, "Material " + material)}
        if set(pin_materials) != set(("1","2","3","4","5","6")):
            raise ValueError("Could not resolve all six pin material universes from geometry.xml.")
        surfaces = {surface.attrib["id"]: surface.attrib for surface in first.findall("surface")}
        cylinder = next((s for s in first.findall("surface") if s.attrib.get("type") == "z-cylinder"), None)
        if cylinder is None:
            raise ValueError("Pin-cell z-cylinder is missing from the archived geometry XML.")
        boundaries = []
        for sid in ("2", "3", "4", "5"):
            surface = surfaces[sid]
            boundaries.append({
                "surface_id": int(sid), "name": surface.get("name"), "type": surface.get("type"),
                "condition": surface.get("boundary"),
                "coordinate_cm": float(surface.get("coeffs", "0").split()[0]),
            })
        lattices = {item.attrib["id"]: item for item in first.findall("lattice")}
        assembly_by_universe = {}
        for cell in first.findall("cell"):
            fill = cell.attrib.get("fill")
            if fill in FILL_CODES:
                assembly_by_universe[cell.attrib["universe"]] = {
                    "universe_id": int(cell.attrib["universe"]),
                    "cell_id": int(cell.attrib["id"]),
                    "name": cell.attrib.get("name"),
                    "lattice_id": int(fill),
                    "lattice_name": lattices[fill].attrib.get("name"),
                    "code": FILL_CODES[fill],
                }
        if set(assembly_by_universe) != set(("9","11","13")):
            raise ValueError("Could not resolve the UO2, MOX, and reflector assembly universes.")
        for layout, (candidate, _, _) in parsed.items():
            if not candidate["source_matches_candidate_signature"]:
                raise ValueError(f"{layout}: the source core lattice disagrees with its layout signature.")
        return {
            "schema_version": 1,
            "model_id": "OECD/NEA C5G7 two-dimensional 2x2 assembly study",
            "source": {
                "repository": "thenextw4ng/cb-pfr",
                "workflow_run_id": run_id,
                "artifact_id": artifact_id,
                "artifact_name": artifact_name,
                "archive_file": archive_path.name,
                "source_member_pattern": "c5g7-2x2-{LAYOUT}/model/2d/geometry.xml",
                "interpretation": "Geometry-only input definitions from an archived GitHub Actions screening/smoke study. This manifest is not a transport calculation result.",
            },
            "materials": {
                "by_id": material_names,
                "pin_universes": pin_materials,
                "moderator_material_id": "7",
                "moderator_name": material_names.get("7", "Water"),
            },
            "pin_geometry": {
                "pitch_cm": [float(v) for v in lattices["101"].findtext("pitch", "").split()],
                "lower_left_cm": [float(v) for v in lattices["101"].findtext("lower_left", "").split()],
                "pin_radius_cm": float(cylinder["coeffs"].split()[-1]),
                "dimensions": [int(v) for v in lattices["101"].findtext("dimension", "").split()],
            },
            "boundary_conditions": boundaries,
            "assemblies": assembly_by_universe,
            "core_lattice": {k:v for k,v in lattice_record(lattices["201"], False).items()},
            "reflector_lattice": lattice_record(lattices["105"]),
            "pin_lattices": {"101": lattice_record(lattices["101"]), "103": lattice_record(lattices["103"])},
            "candidates": [parsed[layout][0] for layout in LAYOUTS],
        }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-zip", required=True, type=Path, help="Downloaded c5g7-study artifact ZIP")
    parser.add_argument("--output", required=True, type=Path, help="Output JSON manifest path")
    parser.add_argument("--artifact-name", default="c5g7-study-640000")
    parser.add_argument("--workflow-run-id", type=int, default=38182056526)
    parser.add_argument("--artifact-id", type=int, default=11719691969)
    args = parser.parse_args()
    manifest = build_manifest(args.artifact_zip.expanduser().resolve(), args.artifact_name, args.workflow_run_id, args.artifact_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.output} from six archived geometry.xml files.")
    for candidate in manifest["candidates"]:
        print(f"{candidate['layout_signature']}: source SHA-256 {candidate['geometry_xml_sha256']} · signature match={candidate['source_matches_candidate_signature']}")
    print("No OpenMC transport run was executed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
