"""Stage 0/1 regression tests for the CB-PFR HTML scientific workstation.

These tests protect the established spatial visualizers and verify that the Evidence
Control Room reports recorded source metadata without merging distinct evidence types.
"""
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


class WorkstationStage0Stage1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (WEB / "index.html").read_text(encoding="utf-8")
        cls.app_js = (WEB / "app.js").read_text(encoding="utf-8")
        cls.core_js = (WEB / "core_geometry_3d.js").read_text(encoding="utf-8")
        cls.ecr_js = (WEB / "evidence_control_room.js").read_text(encoding="utf-8")
        cls.server = (ROOT / "web_server.py").read_text(encoding="utf-8")
        cls.styles = (WEB / "styles.css").read_text(encoding="utf-8")
        cls.snapshot = json.loads((WEB / "research_snapshot.json").read_text(encoding="utf-8"))

    def test_stage0_original_spatial_and_geometry_modules_are_guarded(self):
        for element_id in (
            "core3dCanvas", "geometryPreview", "meshHeatmap", "meshContour",
            "meshProfile", "meshSurface", "axial3dPlot", "axial3dScore",
            "axial3dSlice", "geometryArtifactList",
        ):
            with self.subTest(element_id=element_id):
                self.assertIn(f'id="{element_id}"', self.html)
        self.assertIn('import("/core_geometry_3d.js")', self.html)
        self.assertIn("createCoreViewer", self.core_js)
        self.assertIn('fetch("/api/model-geometry"', self.app_js)
        self.assertIn('fetch("/api/mesh"', self.app_js)
        self.assertIn('fetch("/api/axial-3d?score="', self.app_js)
        self.assertIn('if path == "/api/model-geometry":', self.server)
        self.assertIn('if path == "/api/mesh":', self.server)
        self.assertIn('if path == "/api/axial-3d":', self.server)

    def test_stage0_regression_rules_do_not_allow_fake_spatial_fallbacks(self):
        self.assertIn("No substitute geometry is drawn", self.app_js)
        self.assertIn("No 2-D fallback is used", self.server)
        self.assertIn("no synthetic volume or 2D extrusion", self.app_js)
        self.assertIn("SYNTHETIC METHOD EVIDENCE", self.ecr_js)
        self.assertIn("recorded-evidence-only", self.server)

    def test_stage1_evidence_control_room_is_separate_and_reachable(self):
        self.assertIn('id="evidence-control-room"', self.html)
        self.assertIn('href="#evidence-control-room"', self.html)
        self.assertIn('src="/evidence_control_room.js"', self.html)
        self.assertIn('if path == "/api/evidence-index":', self.server)
        self.assertIn('"/evidence_control_room.js": WEB_ROOT / "evidence_control_room.js"', self.server)
        for source_id in (
            "candidate-study", "core-geometry", "planar-mesh", "axial-volume",
            "assembly-proxy", "latest-replay", "paper-synthetic",
        ):
            with self.subTest(source_id=source_id):
                self.assertIn(f'"{source_id}"', self.server)
                self.assertIn(source_id, self.ecr_js)
        for control_id in ("ecrFilter", "ecrSearch", "ecrRefresh", "ecrDetailBody"):
            self.assertIn(f'id="{control_id}"', self.html)
        self.assertIn("/api/evidence-index", self.ecr_js)
        self.assertIn("SHA-256", self.ecr_js.upper())

    def test_latest_replay_and_synthetic_paper_data_remain_separate(self):
        self.assertEqual(self.snapshot["snapshot_date"], "2026-10-16")
        campaign = self.snapshot["latestC5G7"]
        self.assertEqual(campaign["v2a"]["observedRuns"], 1200)
        self.assertEqual(campaign["highBudget"]["runs"], 60)
        self.assertEqual(campaign["policyReplay"]["decisionBlocks"], 28)
        self.assertEqual(campaign["v2a"]["perRunConvergenceCertified"], 0)
        self.assertEqual(self.snapshot["paper"]["t7"]["regimes"], 8)
        self.assertEqual(self.snapshot["syntheticBenchmarks"]["t2"]["pools"], 40000)
        self.assertEqual(self.snapshot["syntheticBenchmarks"]["t3"]["pools"], 6000)
        self.assertIn("synthetic-method", self.server)
        self.assertIn("OpenMC", self.snapshot["paper"]["scope"])
        self.assertTrue(any("synthetic" in note.lower() for note in self.snapshot["paper"]["t7"]["sourceNotes"]))

    def test_axial_artifact_matches_its_recorded_hash_and_dimensions(self):
        npz_path = ROOT / "evidence" / "cbpfr_axial_3d" / "axial_tally_3d.npz"
        summary_path = ROOT / "evidence" / "cbpfr_axial_3d" / "AXIAL_3D_STATEPOINT_SUMMARY.json"
        self.assertTrue(npz_path.is_file(), "recorded axial volume artifact must remain in the repository")
        self.assertTrue(summary_path.is_file(), "axial provenance sidecar must remain in the repository")
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        actual_sha = hashlib.sha256(npz_path.read_bytes()).hexdigest()
        self.assertEqual(actual_sha, summary["npz"]["sha256"])
        self.assertEqual(npz_path.stat().st_size, summary["npz"]["bytes"])
        self.assertEqual(summary["mesh"]["dimension_xyz"], [51, 51, 30])
        self.assertGreater(summary["mesh"]["dimension_xyz"][2], 1)

    def test_evidence_index_reports_distinct_records_without_claiming_convergence(self):
        import web_server

        result = web_server.read_evidence_index()
        self.assertEqual(result["mode"], "recorded-evidence-only")
        records = {item["id"]: item for item in result["sources"]}
        self.assertTrue({
            "candidate-study", "core-geometry", "planar-mesh", "axial-volume",
            "assembly-proxy", "latest-replay", "paper-synthetic",
        }.issubset(records))
        self.assertFalse(records["latest-replay"]["metadata"]["source_convergence_certified"])
        self.assertEqual(records["latest-replay"]["metadata"]["v2a_observations"], 1200)
        self.assertEqual(records["latest-replay"]["metadata"]["high_budget_runs"], 60)
        self.assertEqual(records["axial-volume"]["metadata"]["dimension_xyz"], [51, 51, 30])
        self.assertNotEqual(records["paper-synthetic"]["evidence_class"], records["latest-replay"]["evidence_class"])
        self.assertIn("not absolute reactor power", records["assembly-proxy"]["summary"].lower())


if __name__ == "__main__":
    unittest.main()
