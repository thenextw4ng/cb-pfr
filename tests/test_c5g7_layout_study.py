"""Offline tests for the C5G7 model preparation adapter."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_c5g7_layout_study import (
    CANONICAL_ASSIGNMENT,
    PINNED_UPSTREAM_COMMIT,
    patch_builder,
    patch_mgxs_energy_boundaries,
    validate_design_space,
    validate_source,
)


class C5G7LayoutStudyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "upstream"
        model = self.source / "c5g7" / "openmc"
        (model / "2d").mkdir(parents=True)
        (self.source / "UPSTREAM_PROVENANCE.json").write_text(json.dumps({
            "source_repository": "https://github.com/mit-crpg/benchmarks.git",
            "source_commit": PINNED_UPSTREAM_COMMIT,
        }), encoding="utf-8")
        self.builder = model / "2d" / "build-xml-2d.py"
        self.builder.write_text(
            CANONICAL_ASSIGNMENT + "\n"
            "batches = 20000\n"
            "inactive = 500\n"
            "particles = 10000\n"
            "settings_file.particles = particles\n"
            "settings_file.entropy_lower_left = [-32.13, -32.13, -1.E50]\n"
            "settings_file.entropy_upper_right = [32.13, 32.13, 1.E50]\n"
            "settings_file.entropy_dimension = [51, 51, 1]\n",
            encoding="utf-8",
        )
        self.materials = model / "materials.py"
        self.materials.write_text(
            "import openmc\nimport numpy as np\n"
            "groups = openmc.mgxs.EnergyGroups(np.logspace(-5, 7, 8))\n"
            "rest = True\n",
            encoding="utf-8",
        )
        self.design = self.root / "design.json"
        candidates = []
        for i, layout in enumerate([
            {"p00":"UO2","p01":"MOX","p10":"MOX","p11":"UO2"},
            {"p00":"MOX","p01":"UO2","p10":"UO2","p11":"MOX"},
            {"p00":"UO2","p01":"UO2","p10":"MOX","p11":"MOX"},
            {"p00":"MOX","p01":"MOX","p10":"UO2","p11":"UO2"},
            {"p00":"UO2","p01":"MOX","p10":"UO2","p11":"MOX"},
            {"p00":"MOX","p01":"UO2","p10":"MOX","p11":"UO2"},
        ]):
            signature = "".join("M" if layout[p] == "MOX" else "U" for p in ("p00","p01","p10","p11"))
            candidates.append({
                "candidate_id": f"c5g7-2x2-{signature}",
                "fuel_assembly_layout": layout,
                "is_canonical_reference_arrangement": layout == {"p00":"UO2","p01":"MOX","p10":"MOX","p11":"UO2"},
            })
        self.design.write_text(json.dumps({
            "design_study_id":"C5G7-2x2-two-UO2-two-MOX-layout-enumeration",
            "fixed_reflector_positions":["p02","p12","p20","p21","p22"],
            "constraints":{"reflector_positions_fixed":True},
            "candidate_layouts":candidates,
        }), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_source_provenance_and_builder_required(self):
        model, revision = validate_source(self.source)
        self.assertEqual(revision, PINNED_UPSTREAM_COMMIT)
        self.assertTrue((model / "2d" / "build-xml-2d.py").is_file())

    def test_design_space_accepts_six_unique_valid_layouts(self):
        self.assertEqual(len(validate_design_space(self.design)["candidate_layouts"]), 6)

    def test_design_space_rejects_wrong_count(self):
        data = json.loads(self.design.read_text())
        data["candidate_layouts"].pop()
        self.design.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "exactly six"):
            validate_design_space(self.design)

    def test_design_space_rejects_reflector_position_drift(self):
        data = json.loads(self.design.read_text())
        data["fixed_reflector_positions"] = ["p02", "p12", "p20", "p21", "p23"]
        self.design.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "fixed_reflector_positions"):
            validate_design_space(self.design)

    def test_design_space_rejects_candidate_id_layout_mismatch(self):
        data = json.loads(self.design.read_text())
        data["candidate_layouts"][0]["candidate_id"] = "c5g7-2x2-MMUU"
        self.design.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "candidate ID/layout signature mismatch"):
            validate_design_space(self.design)

    def test_patch_builder_rejects_invalid_material_instead_of_silently_mapping_to_mox(self):
        layout = {"p00":"UO2","p01":"MOX","p10":"burned","p11":"UO2"}
        original = self.builder.read_text()
        with self.assertRaisesRegex(ValueError, "fuel materials"):
            patch_builder(self.builder, layout, batches=40, inactive=5, particles=200)
        self.assertEqual(self.builder.read_text(), original)

    def test_patch_builder_preserves_all_five_reflector_cells_for_every_layout(self):
        import itertools
        positions = ("p00", "p01", "p10", "p11")
        for mox_positions in itertools.combinations(positions, 2):
            layout = {p: ("MOX" if p in mox_positions else "UO2") for p in positions}
            with tempfile.TemporaryDirectory() as case_dir:
                builder = Path(case_dir) / "build-xml-2d.py"
                nl = chr(10)
                builder.write_text(
                    CANONICAL_ASSIGNMENT + nl
                    + "batches = 20000" + nl
                    + "inactive = 500" + nl
                    + "particles = 10000" + nl
                    + "settings_file.particles = particles" + nl
                    + "settings_file.entropy_lower_left = [-32.13, -32.13, -1.E50]" + nl
                    + "settings_file.entropy_upper_right = [32.13, 32.13, 1.E50]" + nl
                    + "settings_file.entropy_dimension = [51, 51, 1]" + nl,
                    encoding="utf-8",
                )
                patch_builder(builder, layout, batches=40, inactive=5, particles=200)
                text = builder.read_text()
                assignment = next(
                    (line for line in text.splitlines()
                     if line.startswith("lattices['Core'].universes = ")),
                    None,
                )
                self.assertIsNotNone(assignment, text)
                compact = "".join(assignment.split("=", 1)[1].split())
                symbol = {"UO2": "u", "MOX": "m"}
                expected = (
                    f"[[{symbol[layout['p00']]},{symbol[layout['p01']]},w],"
                    f"[{symbol[layout['p10']]},{symbol[layout['p11']]},w],[w,w,w]]"
                )
                self.assertEqual(compact, expected)
                self.assertEqual(compact.count(",w]"), 3)
                self.assertEqual(compact.count("[w,w,w]"), 1)

    def test_patch_uses_standard_c5g7_energy_group_boundaries(self):
        patch_mgxs_energy_boundaries(self.materials)
        text = self.materials.read_text()
        self.assertIn("energy_boundaries = np.array([1.0e-5, 0.0635, 10.0, 100.0, 1000.0, 500000.0, 1000000.0, 20000000.0], dtype=float)", text)
        self.assertIn("OECD/NEA C5G7 standard seven-group energy boundaries", text)
        self.assertIn("groups = openmc.mgxs.EnergyGroups(energy_boundaries)", text)
        self.assertNotIn("np.logspace", text)
        self.assertIn("rest = True", text)

    def test_patch_mgxs_fails_closed_when_upstream_template_changes(self):
        self.materials.write_text("groups = something_else\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "energy-group construction differs"):
            patch_mgxs_energy_boundaries(self.materials)

    def test_patch_changes_only_layout_and_runtime_settings(self):
        layout = {"p00":"MOX","p01":"UO2","p10":"MOX","p11":"UO2"}
        patch_builder(self.builder, layout, batches=40, inactive=5, particles=200)
        text = self.builder.read_text()
        self.assertIn("lattices['Core'].universes = [[m, u, w], [m, u, w], [w, w, w]]", text)
        self.assertIn("batches = 40", text)
        self.assertIn("inactive = 5", text)
        self.assertIn("particles = 200", text)
        self.assertIn("settings_file.seed = 620000", text)
        self.assertIn("entropy_mesh = openmc.RegularMesh()", text)
        self.assertIn("settings_file.entropy_mesh = entropy_mesh", text)
        self.assertNotIn("settings_file.entropy_lower_left", text)
        self.assertNotIn(CANONICAL_ASSIGNMENT, text)

    def test_patch_fails_closed_when_upstream_template_changes(self):
        self.builder.write_text("lattices['Core'].universes = changed\nbatches = 20000\ninactive = 500\nparticles = 10000\n")
        with self.assertRaisesRegex(ValueError, "differs from audited template"):
            patch_builder(self.builder, {"p00":"UO2","p01":"MOX","p10":"MOX","p11":"UO2"}, 40, 5, 200)

    def test_patch_rejects_invalid_inactive_count(self):
        with self.assertRaisesRegex(ValueError, "inactive batches"):
            patch_builder(self.builder, {"p00":"UO2","p01":"MOX","p10":"MOX","p11":"UO2"}, 10, 10, 200)


if __name__ == "__main__":
    unittest.main()
