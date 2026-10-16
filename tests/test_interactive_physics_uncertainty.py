"""Regression guards for the interactive axial tally and uncertainty analysis labs."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


class InteractivePhysicsUncertaintyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (WEB / "index.html").read_text(encoding="utf-8")
        cls.app = (WEB / "app.js").read_text(encoding="utf-8")
        cls.axial = (WEB / "axial_investigation.js").read_text(encoding="utf-8")
        cls.comparison = (WEB / "uncertainty_analysis.js").read_text(encoding="utf-8")
        cls.server = (ROOT / "web_server.py").read_text(encoding="utf-8")
        cls.snapshot = json.loads((WEB / "research_snapshot.json").read_text(encoding="utf-8"))

    def test_stage2_views_are_connected_to_the_recorded_3d_array(self):
        for element_id in (
            "axialInvestigationStatus", "axialPlaneSelect", "axialPlaneIndex",
            "axialSectionPlot", "axialProfileAxis", "axialProfileFixedA",
            "axialProfileFixedB", "axialLineProfilePlot", "axialVoxelReadout",
        ):
            with self.subTest(element_id=element_id):
                self.assertIn(f'id="{element_id}"', self.html)
        self.assertIn('src="/axial_investigation.js"', self.html)
        self.assertIn('"/axial_investigation.js": WEB_ROOT / "axial_investigation.js"', self.server)
        self.assertIn('window.CBPFRAxial3DData=payload;', self.app)
        self.assertIn('cbpfr-axial3d-updated', self.app)
        for token in ("mean[k][j][i]", "standard_error", "relative_error_percent", '"XY"', '"XZ"', '"YZ"', "plotly_hover", "plotly_click"):
            with self.subTest(token=token):
                self.assertIn(token, self.axial)
        self.assertIn("customVoxel(i,j,k)", self.axial)
        self.assertIn("No values are interpolated between voxels", self.html)

    def test_stage2_line_profile_uses_raw_means_with_log_axis(self):
        self.assertIn('type:currentView()==="mean"?"log":"linear"', self.axial)
        self.assertIn('values.push(currentView()==="relative_error"?rse[k][fj][fi]:(mean[k][fj][fi]>0?mean[k][fj][fi]:null))', self.axial)
        self.assertIn("Monte Carlo standard error", self.axial)

    def test_stage3_charts_are_bound_to_recorded_summary_and_paper_fields(self):
        for element_id in (
            "uncertainty-lab", "cmpOpenMCMetric", "cmpV2aFChart", "cmpV2aKChart",
            "cmpPolicyMatchChart", "cmpPolicyRegretChart", "cmpT7Endpoint",
            "cmpT7Chart", "cmpT7bChart",
        ):
            with self.subTest(element_id=element_id):
                self.assertIn(f'id="{element_id}"', self.html)
        self.assertIn('src="/uncertainty_analysis.js"', self.html)
        self.assertIn('"/uncertainty_analysis.js": WEB_ROOT / "uncertainty_analysis.js"', self.server)
        for token in (
            "v2aLayoutSummary", "meanF", "sdF", "meanK", "sdK",
            "ciRegretDifferenceVsPoint", "pairedMatched95", "pointPrimary",
            "cbZ1Primary", "adaptiveCBPrimary",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.comparison)
        self.assertIn("synthetic method evidence", self.comparison.lower())
        self.assertIn("match-rate CIs are absent", self.comparison)

    def test_stage3_respects_sample_sizes_and_convergence_boundary(self):
        latest = self.snapshot["latestC5G7"]
        self.assertEqual(latest["v2a"]["observedRuns"], 1200)
        self.assertEqual(latest["highBudget"]["runs"], 60)
        self.assertEqual(latest["policyReplay"]["decisionBlocks"], 28)
        self.assertEqual(latest["v2a"]["perRunConvergenceCertified"], 0)
        self.assertEqual(self.snapshot["paper"]["t7"]["regimes"], 8)
        self.assertEqual(len(self.snapshot["paper"]["t7"]["pairedMatched95"]), 8)
        self.assertTrue(any("synthetic" in line.lower() for line in self.snapshot["paper"]["t7"]["sourceNotes"]))

    def test_existing_geometry_and_surface_mounts_are_not_replaced(self):
        for element_id in ("core3dCanvas", "geometryPreview", "meshSurface", "axial3dPlot", "research-evidence", "evidence-control-room"):
            with self.subTest(element_id=element_id):
                self.assertIn(f'id="{element_id}"', self.html)
        self.assertIn('fetch("/api/model-geometry"', self.app)
        self.assertIn('fetch("/api/mesh"', self.app)


if __name__ == "__main__":
    unittest.main()
