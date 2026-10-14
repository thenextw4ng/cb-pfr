#!/usr/bin/env python3
"""Repository-side Stage 6 evidence and scientific visualization acceptance checks."""
from __future__ import annotations
import csv
import hashlib
import json
import os
import zipfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYOUTS = {"MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM"}
POSITIONS = ("p00_fission_rate", "p01_fission_rate", "p10_fission_rate", "p11_fission_rate")

def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))

class ScientificVisualAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "web/index.html").read_text(encoding="utf-8")
        cls.js = (ROOT / "web/app.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "web/styles.css").read_text(encoding="utf-8")
        cls.server = (ROOT / "web_server.py").read_text(encoding="utf-8")
        cls.candidates = read_csv(ROOT / "results/c5g7_corrected_group_repeatability_smoke_2026-10-11/fission_objective_repeatability_summary.csv")
        cls.candidate_runs = read_csv(ROOT / "results/c5g7_corrected_group_repeatability_smoke_2026-10-11/run_level_fission_objective.csv")
        cls.campaign = json.loads((ROOT / "results/c5g7_corrected_group_repeatability_smoke_2026-10-11/fission_objective_repeatability.json").read_text(encoding="utf-8"))
        cls.proxy = read_csv(ROOT / "results/c5g7_assembly_fission_proxy_smoke_2026-10-11.csv")
        cls.geometry = json.loads((ROOT / "evidence/c5g7_openmc_geometry_manifest_2026-10-13.json").read_text(encoding="utf-8"))

    def test_corrected_group_candidate_summaries_match_all_18_run_records(self):
        self.assertEqual(self.campaign["status"], "EXPLORATORY_DESCRIPTIVE_ONLY")
        self.assertEqual(self.campaign["run_count"], 18)
        self.assertEqual(self.campaign["round_count"], 3)
        self.assertEqual(self.campaign["candidate_count"], 6)
        self.assertTrue(self.campaign["all_group_structure_audits_passed"])
        self.assertTrue(self.campaign["all_statepoint_hashes_unique"])
        self.assertTrue(self.campaign["all_mgxs_hashes_identical"])
        self.assertTrue(self.campaign["no_winner_claim"])
        self.assertEqual(len(self.candidates), 6)
        self.assertEqual(len(self.candidate_runs), 18)
        self.assertEqual({row["layout_signature"] for row in self.candidates}, LAYOUTS)
        self.assertEqual(len({row["candidate_id"] for row in self.candidates}), 6)
        self.assertEqual(len({row["seed"] for row in self.candidate_runs}), 18)
        self.assertEqual(len({row["statepoint_sha256"] for row in self.candidate_runs}), 18)
        self.assertEqual({row["mgxs_sha256"] for row in self.candidate_runs}, {self.campaign["corrected_mgxs_sha256"]})
        for row in self.candidates:
            signature = row["layout_signature"]
            self.assertEqual(row["candidate_id"], "c5g7-2x2-" + signature)
            self.assertEqual(signature.count("M"), 2)
            self.assertEqual(signature.count("U"), 2)
            self.assertGreater(float(row["mean_keff"]), 0)
            self.assertGreaterEqual(float(row["between_seed_sd_keff"]), 0)
            runs = [item for item in self.candidate_runs if item["layout_signature"] == signature]
            self.assertEqual(len(runs), 3)
            self.assertEqual({item["group_structure_audit"] for item in runs}, {"PASS"})
            keff = [float(item["keff_mean"]) for item in runs]
            peak = [float(item["fission_rate_peaking_factor"]) for item in runs]
            self.assertAlmostEqual(float(row["mean_keff"]), sum(keff) / 3, places=8)
            self.assertAlmostEqual(float(row["between_seed_sd_keff"]), __import__("statistics").stdev(keff), places=8)
            self.assertAlmostEqual(float(row["mean_fission_rate_peaking_factor"]), sum(peak) / 3, places=8)
            self.assertAlmostEqual(float(row["between_seed_sd_fission_peaking_factor"]), __import__("statistics").stdev(peak), places=8)
        self.assertIn("descriptive only", self.html.lower())
        self.assertIn("not a physical-feasibility ranking", self.html.lower())
        self.assertIn("corrected-group", self.html.lower())
        self.assertIn("composition-only", self.html.lower())
        self.assertIn("Research Dossier", self.html)
        self.assertIn("Evidence-Bounded Claims", self.html)
        self.assertIn("A–G Final Closeout", self.html)
        self.assertNotIn("c5g7_layout_smoke_2026-10-10/candidate_summary.csv", self.server)
        self.assertIn("fission_objective_repeatability_summary.csv", self.server)
        self.assertIn("run_level_fission_objective.csv", self.server)

    def test_geometry_has_four_candidate_fuels_five_fixed_reflectors_and_source_pin_dimensions(self):
        g = self.geometry
        self.assertRegex(g["source"]["archive_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(g["core_lattice"]["dimensions"], [3, 3])
        self.assertEqual(g["pin_geometry"]["dimensions"], [17, 17])
        self.assertEqual(g["pin_geometry"]["pitch_cm"], [1.26, 1.26])
        self.assertAlmostEqual(g["pin_geometry"]["pin_radius_cm"], 0.54)
        self.assertEqual(len(g["candidates"]), 6)
        reflector_positions = None
        for candidate in g["candidates"]:
            signature = candidate["layout_signature"]
            grid = candidate["assembly_grid"]
            self.assertEqual("".join([grid[0][0], grid[0][1], grid[1][0], grid[1][1]]), signature)
            self.assertEqual(len(grid), 3)
            self.assertTrue(all(len(row) == 3 for row in grid))
            self.assertEqual(grid[0][2], "R")
            self.assertEqual(grid[1][2], "R")
            self.assertEqual(grid[2], ["R", "R", "R"])
            self.assertEqual(sum(cell == "M" for row in grid for cell in row), 2)
            self.assertEqual(sum(cell == "U" for row in grid for cell in row), 2)
            self.assertEqual(sum(cell == "R" for row in grid for cell in row), 5)
            sites = tuple((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == "R")
            if reflector_positions is None:
                reflector_positions = sites
            self.assertEqual(sites, reflector_positions)
            self.assertTrue(candidate["source_matches_candidate_signature"])
            self.assertEqual(candidate["signature_derived_from_xml"], signature)
            self.assertRegex(candidate["geometry_xml_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(candidate["materials_xml_sha256"], r"^[0-9a-f]{64}$")
        self.assertTrue({"1", "2", "3", "4", "5", "6"}.issubset(g["materials"]["pin_universes"]))
        self.assertIn("renderModelGeometrySvg", self.js)
        self.assertIn('id="coreSelectedPinMap"', self.html)
        self.assertIn("model-geometry", self.server)

    def test_assembly_proxy_is_four_discrete_positions_with_explicit_uncertainty_scope(self):
        self.assertEqual(len(self.proxy), 6)
        self.assertEqual({row["layout_signature"] for row in self.proxy}, LAYOUTS)
        candidate_seeds = {int(row["seed"]) for row in self.candidate_runs}
        proxy_seeds = {int(row["seed"]) for row in self.proxy}
        self.assertTrue(candidate_seeds.isdisjoint(proxy_seeds), "the assembly proxy campaign has independent seeds and is not paired with the corrected-group candidate study")
        for row in self.proxy:
            self.assertEqual(row["status"], "exploratory_smoke_only")
            for field in ("statepoint_sha256", "settings_sha256", "mgxs_sha256"):
                self.assertRegex(row[field], r"^[0-9a-f]{64}$")
            for position in POSITIONS:
                self.assertGreaterEqual(float(row[position]), 0)
        self.assertIn('id="assemblyMap"', self.html)
        self.assertIn('id="assemblyMatrix"', self.html)
        self.assertIn("discrete observations, not a continuous field", self.html)
        self.assertIn("CSV unit not documented", self.html)
        self.assertIn("not absolute power", self.html.lower())
        self.assertIn('colorscale:"Cividis",zmin:scaleMin,zmax:scaleMax,zauto:false', self.js)
        self.assertIn('const colorbar={', self.js)
        self.assertIn('showscale:false', self.js)
        self.assertIn('marker:{symbol:"square-open",size:selectedOutlineSize,color:"#ffffff"', self.js)
        self.assertIn('const materialEdgeColor = {M:"#f4bd62",U:"#55d4df"}', self.js)
        self.assertIn('collapsed by default', self.html)
        self.assertIn('return signature+(isSelected?"  ◂":"");', self.js)
        self.assertNotIn('name:"Selected candidate"', self.js)
        self.assertNotIn('type:"contour"', self.js[self.js.index("/* Assembly-integrated fission-rate proxy:"):])

    def test_spatial_plots_reference_one_recorded_mesh_field_and_coordinate_vectors(self):
        for item in ("meshHeatmap", "meshContour", "meshProfile", "meshSurface"):
            self.assertIn('id="' + item + '"', self.html)
        self.assertIn("function currentField()", self.js)
        self.assertIn('type:"heatmap",x:xs,y:ys,z:z', self.js)
        self.assertIn('type:"contour",x:xs,y:ys,z:z', self.js)
        self.assertIn('type:"surface",x:xs,y:ys,z:z,surfacecolor:z', self.js)
        self.assertIn('const profileY=f.view==="relative_sd"?relativeRow:meanRow', self.js)
        self.assertIn('geometry.coordinates_available===true&&geometry.coordinate_units==="cm"', self.js)
        self.assertIn("Monte Carlo standard error", self.js)
        self.assertIn("Recorded tally mean", self.js)
        self.assertIn("connectgaps:false", self.js)

    def test_true_recorded_axial_volume_and_provenance_are_present(self):
        base = ROOT / "evidence/cbpfr_axial_3d"
        npz_path = base / "axial_tally_3d.npz"
        summary = json.loads((base / "AXIAL_3D_STATEPOINT_SUMMARY.json").read_text(encoding="utf-8"))
        audit = json.loads((base / "AXIAL_3D_INPUT_AUDIT.json").read_text(encoding="utf-8"))
        manifest = json.loads((base / "AXIAL_3D_INPUT_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertTrue(npz_path.is_file())
        self.assertEqual(summary["status"], "3d_openmc_statepoint_mesh_exported")
        self.assertEqual(summary["mesh"]["dimension_xyz"], [51, 51, 30])
        self.assertEqual(summary["mesh"]["bin_count"], 78030)
        state = summary["statepoint"]
        self.assertEqual(state["n_batches"], 7000)
        self.assertEqual(state["n_inactive"], 500)
        self.assertEqual(state["n_particles"], 10000)
        self.assertEqual(state["n_realizations"], 6500)
        self.assertEqual(audit["status"], "generated_3d_inputs_passed_structural_audit")
        self.assertEqual(manifest["layout_signature"], "UMMU")
        self.assertEqual(hashlib.sha256(npz_path.read_bytes()).hexdigest(), summary["npz"]["sha256"])
        for score in ("flux", "fission", "nu-fission"):
            self.assertGreater(summary["score_summary"][score]["finite_bin_count"], 0)
            self.assertGreaterEqual(summary["score_summary"][score]["relative_error_percent_p95_positive_bins"], 0)
        self.assertIn('type:"volume"', self.js)
        self.assertIn("statepoint SHA-256", self.js)
        self.assertIn("input XML audit", self.js)
        self.assertIn("This plot never reuses or extrudes the 2D terrain above.", self.html)
        nonclaims = " ".join(audit.get("nonclaims", [])) + " " + " ".join(str(v) for v in manifest.get("inherited_axial_assumptions", {}).values())
        self.assertTrue("boundary" in nonclaims.lower() or "benchmark" in nonclaims.lower())

    def test_archived_xml_hashes_match_source_manifest_when_archive_supplied(self):
        archive_value = os.environ.get("CBPFR_TEST_ARCHIVE")
        if not archive_value:
            self.skipTest("CBPFR_TEST_ARCHIVE not set; raw XML provenance cross-check requires the archived study ZIP.")
        archive_path = Path(archive_value)
        self.assertTrue(archive_path.is_file(), f"Study archive not found: {archive_path}")
        archive_bytes = archive_path.read_bytes()
        self.assertEqual(
            hashlib.sha256(archive_bytes).hexdigest(),
            self.geometry["source"]["archive_sha256"],
            "Study archive SHA-256 must match the geometry manifest source.",
        )
        with zipfile.ZipFile(archive_path) as archive:
            names = set(archive.namelist())
            self.assertEqual(len(self.geometry["candidates"]), 6)
            checked = set()
            for candidate in self.geometry["candidates"]:
                signature = candidate["layout_signature"]
                self.assertIn(signature, LAYOUTS)
                geometry_member = candidate["source_member"]
                materials_member = geometry_member.rsplit("/", 1)[0] + "/materials.xml"
                self.assertIn(geometry_member, names, f"Missing source geometry XML for {signature}")
                self.assertIn(materials_member, names, f"Missing source materials XML for {signature}")
                geometry_bytes = archive.read(geometry_member)
                materials_bytes = archive.read(materials_member)
                self.assertEqual(
                    hashlib.sha256(geometry_bytes).hexdigest(),
                    candidate["geometry_xml_sha256"],
                    f"Geometry XML SHA-256 mismatch for {signature}",
                )
                self.assertEqual(
                    hashlib.sha256(materials_bytes).hexdigest(),
                    candidate["materials_xml_sha256"],
                    f"Materials XML SHA-256 mismatch for {signature}",
                )
                self.assertIn(b"<geometry", geometry_bytes.lower())
                self.assertIn(b"<materials", materials_bytes.lower())
                checked.add(signature)
            self.assertEqual(checked, LAYOUTS)

    def test_missing_candidate_uncertainty_is_not_encoded_as_zero(self):
        # A missing SD must not look like a perfectly precise measurement in Plotly error bars.
        self.assertIn('array:valid.map(r=>has(r,sdKey)?Number(r[sdKey]):null)', self.js)
        self.assertIn('array:vals.map(r=>has(r,"keff_std_dev")?Number(r.keff_std_dev):null)', self.js)
        self.assertIn("Between-seed sample SD", self.js)
        self.assertIn("fission_peaking_mean", self.js)
        self.assertIn("records_validated_against_run_level_data", self.server)

    def test_responsive_and_provenance_contracts_exist(self):
        for breakpoint in ("680px", "1000px", "1100px", "1120px"):
            self.assertIn("max-width:" + breakpoint, self.css)
        self.assertIn("min-width:0", self.css)
        self.assertIn("overflow-wrap:anywhere", self.css)
        self.assertIn("#assemblyMap,#assemblyMatrix{height:320px}", self.css)
        self.assertIn("Physical validation not established", self.html)
        self.assertIn("No claim of physical feasibility certification", self.html)
        self.assertIn("hash_matches", self.server)
        self.assertIn("statepoint_file_sha256", self.server)


if __name__ == "__main__":
    unittest.main(verbosity=2)
