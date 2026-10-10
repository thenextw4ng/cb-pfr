"""Offline tests for the C5G7 model preparation adapter."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_c5g7_layout_study import (
    CANONICAL_ASSIGNMENT,
    patch_builder,
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
            "source_commit": "a" * 40,
        }), encoding="utf-8")
        self.builder = model / "2d" / "build-xml-2d.py"
        self.builder.write_text(
            CANONICAL_ASSIGNMENT + "\n"
            "batches = 20000\n"
            "inactive = 500\n"
            "particles = 10000\n",
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
            "candidate_layouts":candidates,
        }), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_source_provenance_and_builder_required(self):
        model, revision = validate_source(self.source)
        self.assertEqual(revision, "a" * 40)
        self.assertTrue((model / "2d" / "build-xml-2d.py").is_file())

    def test_design_space_accepts_six_unique_valid_layouts(self):
        self.assertEqual(len(validate_design_space(self.design)["candidate_layouts"]), 6)

    def test_design_space_rejects_wrong_count(self):
        data = json.loads(self.design.read_text())
        data["candidate_layouts"].pop()
        self.design.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "exactly six"):
            validate_design_space(self.design)

    def test_patch_changes_only_layout_and_runtime_settings(self):
        layout = {"p00":"MOX","p01":"UO2","p10":"MOX","p11":"UO2"}
        patch_builder(self.builder, layout, batches=40, inactive=5, particles=200)
        text = self.builder.read_text()
        self.assertIn("lattices['Core'].universes = [[m, u, w], [m, u, w], [w, w, w]]", text)
        self.assertIn("batches = 40", text)
        self.assertIn("inactive = 5", text)
        self.assertIn("particles = 200", text)
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
