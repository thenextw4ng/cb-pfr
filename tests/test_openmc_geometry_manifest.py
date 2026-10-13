#!/usr/bin/env python3
"""Validation checks for the XML-derived C5G7 geometry manifest; standard library only."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "evidence" / "c5g7_openmc_geometry_manifest_2026-10-13.json"
LAYOUTS = ("MUMU", "MMUU", "MUUM", "UMMU", "UUMM", "UMUM")
FILL_CODES = {"101": "U", "103": "M", "105": "R"}
# Canonical hashes of integer universe grids, calculated directly from the six original geometry.xml files.
EXPECTED_PIN_GRID_SHA256 = {
    "101": "76ab78e63639ee7624672c13d908c75369b625fc509ed39e5f170e9d834c8fe5",
    "103": "9b2d993f83ba81f714032b20bd9a66025821c2da69d2829ad5ae8dd2826a8267",
}
EXPECTED_CORE_GRID_SHA256 = {
    "MUMU": "a7bff16bc5df326ea7ba7f99fa35c05591a79b921ababf9030d9d990013c1c74",
    "MMUU": "6dea82503f68e6f48d0e80e6995e3039d763246823f462a5675e1166327a49f9",
    "MUUM": "ef813d41e4f4c577c1cc0bbfe370d6f7da4f5056987f53c4767143c80769ce3a",
    "UMMU": "50cf49c57d34ee26431bd2c75a705e1dc21b2bb6dae05f3758b6d7b57f05d826",
    "UUMM": "f276dcb648b3ab0aaf82097a3b6447aab5f21d6c27d43c0ae812211e4ee946d4",
    "UMUM": "063fddf321e2f3b148e09f235081ffb631b9547942257d02657ef280d3f9018f",
}

def grid_sha256(grid):
    canonical = json.dumps(grid, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()

def parse_universe_grid(text):
    return [[int(value) for value in line.split()] for line in text.strip().splitlines() if line.strip()]

class OpenMCGeometryManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_manifest_has_all_six_unique_candidate_sources(self):
        self.assertEqual(self.manifest["schema_version"], 1)
        self.assertEqual([c["layout_signature"] for c in self.manifest["candidates"]], list(LAYOUTS))
        self.assertRegex(self.manifest["source"].get("archive_sha256", ""), r"^[0-9a-f]{64}$")
        ids = [c["candidate_id"] for c in self.manifest["candidates"]]
        self.assertEqual(len(set(ids)), 6)
        for candidate in self.manifest["candidates"]:
            self.assertEqual(candidate["candidate_id"], "c5g7-2x2-" + candidate["layout_signature"])
            self.assertRegex(candidate["geometry_xml_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(candidate.get("materials_xml_sha256", ""), r"^[0-9a-f]{64}$")
            self.assertTrue(candidate["source_matches_candidate_signature"])
            self.assertEqual(candidate["signature_derived_from_xml"], candidate["layout_signature"])

    def test_candidate_core_lattices_match_signatures_and_reflector_footprint(self):
        core = self.manifest["core_lattice"]
        self.assertEqual(core["id"], 201)
        self.assertEqual(core["dimensions"], [3, 3])
        self.assertEqual(core["lower_left_cm"], [-32.13, -32.13])
        self.assertEqual(core["pitch_cm"], [21.42, 21.42])
        assemblies = self.manifest["assemblies"]
        self.assertEqual({value["code"] for value in assemblies.values()}, {"U", "M", "R"})
        for candidate in self.manifest["candidates"]:
            universe_grid = candidate["core_universe_grid"]
            category_grid = candidate["assembly_grid"]
            self.assertEqual(len(universe_grid), 3)
            self.assertTrue(all(len(row) == 3 for row in universe_grid))
            self.assertEqual(grid_sha256(universe_grid), EXPECTED_CORE_GRID_SHA256[candidate["layout_signature"]])
            expected = [[assemblies[str(uid)]["code"] for uid in row] for row in universe_grid]
            self.assertEqual(category_grid, expected)
            self.assertEqual("".join(category_grid[r][c] for r in range(2) for c in range(2)), candidate["layout_signature"])
            self.assertEqual(sum(code == "R" for row in category_grid for code in row), 5)
            self.assertEqual(sum(code == "U" for row in category_grid for code in row), 2)
            self.assertEqual(sum(code == "M" for row in category_grid for code in row), 2)

    def test_pin_material_lattices_are_complete_17_by_17_xml_universe_maps(self):
        geometry = self.manifest["pin_geometry"]
        self.assertEqual(geometry["dimensions"], [17, 17])
        self.assertEqual(geometry["pitch_cm"], [1.26, 1.26])
        self.assertAlmostEqual(geometry["pin_radius_cm"], 0.54)
        self.assertEqual(set(self.manifest["pin_lattices"]), {"101", "103"})
        known = set(self.manifest["materials"]["pin_universes"])
        for lattice_id, lattice in self.manifest["pin_lattices"].items():
            self.assertEqual(lattice["dimensions"], [17, 17])
            grid = lattice["universe_grid"]
            self.assertEqual(grid_sha256(grid), EXPECTED_PIN_GRID_SHA256[lattice_id])
            self.assertEqual(len(grid), 17)
            self.assertTrue(all(len(row) == 17 for row in grid))
            self.assertTrue({str(value) for row in grid for value in row}.issubset(known))

    def test_boundary_conditions_are_explicit_and_source_named(self):
        boundaries = {item["name"]: item for item in self.manifest["boundary_conditions"]}
        self.assertEqual(boundaries["Core x-min"]["condition"], "reflective")
        self.assertEqual(boundaries["Core x-max"]["condition"], "vacuum")
        self.assertEqual(boundaries["Core y-min"]["condition"], "vacuum")
        self.assertEqual(boundaries["Core y-max"]["condition"], "reflective")
        self.assertEqual(boundaries["Core x-min"]["coordinate_cm"], -32.13)
        self.assertEqual(boundaries["Core x-max"]["coordinate_cm"], 32.13)
        self.assertEqual(boundaries["Core y-min"]["coordinate_cm"], -32.13)
        self.assertEqual(boundaries["Core y-max"]["coordinate_cm"], 32.13)

    def test_manifest_matches_original_xml_in_source_archive_when_supplied(self):
        archive_path = os.environ.get("CBPFR_OPENMC_GEOMETRY_ARCHIVE")
        if not archive_path:
            self.skipTest("Set CBPFR_OPENMC_GEOMETRY_ARCHIVE to verify byte-for-byte source hashes and XML values.")
        archive_bytes = Path(archive_path).read_bytes()
        self.assertEqual(hashlib.sha256(archive_bytes).hexdigest(), self.manifest["source"]["archive_sha256"])
        with zipfile.ZipFile(archive_path) as archive:
            for candidate in self.manifest["candidates"]:
                raw = archive.read(candidate["source_member"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), candidate["geometry_xml_sha256"])
                root = ET.fromstring(raw)
                lattices = {item.attrib["id"]: item for item in root.findall("lattice")}
                actual_core = parse_universe_grid(lattices["201"].findtext("universes", ""))
                self.assertEqual(actual_core, candidate["core_universe_grid"])
                for lattice_id in ("101", "103"):
                    actual_pins = parse_universe_grid(lattices[lattice_id].findtext("universes", ""))
                    self.assertEqual(actual_pins, self.manifest["pin_lattices"][lattice_id]["universe_grid"])
                material_member = candidate["source_member"].replace("geometry.xml", "materials.xml")
                material_bytes = archive.read(material_member)
                self.assertEqual(hashlib.sha256(material_bytes).hexdigest(), candidate["materials_xml_sha256"])
                material_root = ET.fromstring(material_bytes)
                names = {m.attrib["id"]: m.attrib.get("name") for m in material_root.findall("material")}
                self.assertEqual(names, self.manifest["materials"]["by_id"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
