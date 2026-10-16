"""Regression guard for the CB-PFR HTML workstation's scientific visual contract.

These checks are intentionally lightweight and run with the normal unittest suite.
Browser rendering is covered by tests/browser_visual_regression.cjs in a dedicated CI job.
"""
from __future__ import annotations

import hashlib
import json
import re
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


class WorkstationVisualContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (WEB / "index.html").read_text(encoding="utf-8")
        cls.app_js = (WEB / "app.js").read_text(encoding="utf-8")
        cls.research_js = (WEB / "research_snapshot_ui.js").read_text(encoding="utf-8")
        cls.evidence_js = (WEB / "evidence_control_room.js").read_text(encoding="utf-8")
        cls.styles = (WEB / "styles.css").read_text(encoding="utf-8")
        cls.server = (ROOT / "web_server.py").read_text(encoding="utf-8")
        cls.snapshot = json.loads((WEB / "research_snapshot.json").read_text(encoding="utf-8"))
        cls.geometry = json.loads(
            (ROOT / "evidence" / "c5g7_openmc_geometry_manifest_2026-10-13.json").read_text(encoding="utf-8")
        )
        cls.axial_provenance = json.loads(
            (ROOT / "evidence" / "cbpfr_axial_3d" / "AXIAL_3D_PROVENANCE.json").read_text(encoding="utf-8")
        )

    def test_protected_scientific_sections_remain_present(self):
        required_ids = (
            "overview", "candidates", "physics", "assembly-field", "assembly",
            "spatial", "research-evidence", "evidence-control-room", "integrity",
            "core3dCanvas", "geometryPreview", "meshHeatmap", "meshContour",
            "meshProfile", "meshSurface", "axial3dPlot", "t7PrimaryChart",
            "t2ScenarioTable", "t3RegimeTable", "ecrKpis", "ecrRecordList", "ecrDetail",
        )
        ids = set(re.findall(r'\bid="([^"]+)"', self.html))
        missing = sorted(set(required_ids) - ids)
        self.assertEqual(missing, [], f"Protected workstation UI elements are missing: {missing}")

    def test_all_restored_renderer_and_control_room_assets_are_served(self):
        for asset in (
            "app.js", "research_snapshot_ui.js", "evidence_control_room.js",
            "core_geometry_3d.js", "styles.css", "research_snapshot.json",
        ):
            self.assertIn(f'"/{asset}": WEB_ROOT / "{asset}"', self.server, asset)
        self.assertIn('src="/research_snapshot_ui.js"', self.html)
        self.assertIn('src="/evidence_control_room.js"', self.html)
        self.assertIn('import("/core_geometry_3d.js")', self.html)
        self.assertIn('https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js', self.html)
        self.assertIn("export function createCoreViewer", (WEB / "core_geometry_3d.js").read_text(encoding="utf-8"))

    def test_spatial_evidence_api_contract_is_not_replaced_by_static_server(self):
        for endpoint in (
            "/api/health", "/api/candidates", "/api/model-geometry",
            "/api/assembly", "/api/mesh", "/api/axial-3d", "/api/evidence-registry",
        ):
            self.assertIn(f'if path == "{endpoint}"', self.server, endpoint)
        self.assertIn('type:"surface"', self.app_js)
        self.assertIn('type:"volume"', self.app_js)
        self.assertIn('fetch("/api/mesh"', self.app_js)
        self.assertIn('fetch("/api/axial-3d?score="', self.app_js)
        self.assertIn("read_evidence_registry()", self.server)

    def test_latest_campaign_snapshot_does_not_drift(self):
        self.assertEqual(self.snapshot["snapshot_date"], "2026-10-16")
        latest = self.snapshot["latestC5G7"]
        self.assertEqual(latest["v2a"]["observedRuns"], 1200)
        self.assertEqual(latest["highBudget"]["runs"], 60)
        self.assertEqual(latest["policyReplay"]["decisionBlocks"], 28)
        self.assertEqual(latest["v2a"]["layouts"], 6)
        self.assertEqual(latest["v2a"]["perRunConvergenceCertified"], 0)
        self.assertEqual(len(self.snapshot["paper"]["t7"]["rows"]), 8)
        self.assertEqual(self.snapshot["syntheticBenchmarks"]["t2"]["pools"], 40000)
        self.assertEqual(self.snapshot["syntheticBenchmarks"]["t3"]["pools"], 6000)

    def test_geometry_manifest_still_contains_all_six_layouts(self):
        candidates = self.geometry.get("candidates", [])
        self.assertEqual(len(candidates), 6)
        self.assertEqual(
            {item["layout_signature"] for item in candidates},
            {"MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM"},
        )
        self.assertEqual(self.geometry["core_lattice"]["dimensions"], [3, 3])
        self.assertEqual(self.geometry["pin_geometry"]["dimensions"], [17, 17])

    def test_axial_volume_bytes_match_recorded_provenance(self):
        npz = ROOT / "evidence" / "cbpfr_axial_3d" / "axial_tally_3d.npz"
        self.assertTrue(npz.is_file(), "Recorded axial tally volume disappeared from the repository")
        digest = hashlib.sha256(npz.read_bytes()).hexdigest()
        self.assertEqual(digest, self.axial_provenance["axial_tally_npz_sha256"])
        self.assertEqual(npz.stat().st_size, self.axial_provenance["axial_tally_npz_bytes"])
        self.assertEqual(self.axial_provenance["mesh_dimension_xyz"], [51, 51, 30])

    def test_planar_statepoint_archive_member_remains_available(self):
        archive_path = ROOT / "OpenMC_HDF5_Evidence_2026-10-11.zip"
        self.assertTrue(archive_path.is_file(), "Planar OpenMC evidence archive is missing")
        with zipfile.ZipFile(archive_path) as archive:
            info = archive.getinfo("c5g7-run/2d/statepoint.20000.h5")
            self.assertGreater(info.file_size, 0)

    def test_registry_is_data_backed_and_keeps_limits_separate(self):
        import web_server

        registry = web_server.read_evidence_registry()
        self.assertEqual(registry["mode"], "recorded-evidence-only")
        records = {record["id"]: record for record in registry["records"]}
        self.assertEqual(
            set(records),
            {"candidate-smoke", "v2a-policy-replay", "source-geometry", "planar-mesh", "axial-volume", "synthetic-paper"},
        )
        self.assertIn("RAW RUN TABLE EXTERNAL", records["v2a-policy-replay"]["status"])
        self.assertIn("NOT CERTIFIED", records["v2a-policy-replay"]["limitations"][1])
        self.assertIn("HASH MATCH", records["axial-volume"]["status"])
        self.assertIn("SYNTHETIC EVIDENCE", records["synthetic-paper"]["status"])
        self.assertTrue(registry["summary"]["record_count"] == 6)
        self.assertEqual(registry["summary"]["campaign_observed_runs"], 1200)
        self.assertEqual(registry["summary"]["high_budget_reference_runs"], 60)
        self.assertEqual(registry["summary"]["convergence_certified_runs"], 0)

    def test_evidence_control_room_is_interactive_and_styles_are_scoped(self):
        for feature in ('ecrSearch', 'ecrFilter', 'ecrRefresh', 'ecrRecordList', 'ecrDetail', 'data-ecr-copy'):
            self.assertIn(feature, self.evidence_js)
        for selector in (".ecr-record-card", ".ecr-detail", ".ecr-source-row", "#evidence-control-room .ecr-kpis"):
            self.assertIn(selector, self.styles)
        self.assertIn("aria-selected", self.evidence_js)
        self.assertIn("limit", self.evidence_js.lower())


if __name__ == "__main__":
    unittest.main()
