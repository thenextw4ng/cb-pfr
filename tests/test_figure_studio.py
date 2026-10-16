"""Source/data contract tests for reproducible figure exports."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


class FigureStudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (WEB / "index.html").read_text(encoding="utf-8")
        cls.js = (WEB / "figure_studio.js").read_text(encoding="utf-8")
        cls.css = (WEB / "styles.css").read_text(encoding="utf-8")
        cls.server = (ROOT / "web_server.py").read_text(encoding="utf-8")
        cls.snapshot = json.loads((WEB / "research_snapshot.json").read_text(encoding="utf-8"))

    def test_figure_studio_controls_and_static_route_are_present(self):
        for element_id in (
            "figure-studio", "figureStudioTarget", "figureStudioCaption",
            "figureStudioExportPng", "figureStudioExportCsv",
            "figureStudioExportJson", "figureStudioCopyCaption",
            "figureCompareA", "figureCompareB", "figureStudioRenderComparison",
            "figureComparePreviewA", "figureComparePreviewB",
        ):
            with self.subTest(element_id=element_id):
                self.assertIn(f'id="{element_id}"', self.html)
        self.assertIn('src="/figure_studio.js"', self.html)
        self.assertIn('"/figure_studio.js": WEB_ROOT / "figure_studio.js"', self.server)

    def test_json_csv_png_contract_contains_trace_data_and_reproducibility_fingerprints(self):
        for token in (
            "cbpfr-figure-reproducibility-v1", "flattenTraceData", "makeCsv",
            "visualization_config_sha256", "exported_data_sha256", "source_hashes",
            "trace_data", "png_export_pixels", "figureStudioCaption",
            "not recorded", "SHA-256", "workflow_run_id", "seed",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.js)
        self.assertIn("const OUT_W=2400,OUT_H=1600", self.js)
        self.assertIn("Download data CSV", self.html)
        self.assertIn("Download reproducibility JSON", self.html)
        self.assertIn("Export high-resolution PNG", self.html)

    def test_stage2_and_stage3_sources_are_in_figure_catalog(self):
        for figure_id in (
            "meshHeatmap", "meshContour", "meshProfile", "meshSurface",
            "axial3dPlot", "axialSectionPlot", "axialLineProfilePlot",
            "cmpV2aFChart", "cmpV2aKChart", "cmpPolicyMatchChart",
            "cmpPolicyRegretChart", "cmpT7Chart", "cmpT7bChart",
        ):
            with self.subTest(figure_id=figure_id):
                self.assertIn(f'["{figure_id}"', self.js)

    def test_wide_paper_tables_are_contained_on_mobile(self):
        self.assertIn(".table-scroller,", self.css)
        self.assertIn("min-width:0", self.css)
        self.assertIn("max-width:100%", self.css)
        self.assertIn("overflow-x:auto", self.css)
        self.assertIn("@media(max-width:680px)", self.css)

    def test_synthetic_and_recorded_openmc_evidence_stay_separate(self):
        synthetic_pos = self.js.index('if(id.startsWith("cmpT7"))')
        openmc_pos = self.js.index('}else if(id.startsWith("cmp"))', synthetic_pos)
        self.assertLess(synthetic_pos, openmc_pos)
        self.assertIn("Synthetic T7/T7b method comparison", self.js)
        self.assertIn("Source convergence is not certified", self.js)
        self.assertEqual(self.snapshot["paper"]["source_sha256"], "55645d738af26bfe9d4ad9eae4ca8f7ab2c83f02da36e6f4ca825e7d9c34ac9b")
        self.assertEqual(self.snapshot["latestC5G7"]["workflowRun"], 38853860378)
        self.assertEqual(self.snapshot["latestC5G7"]["v2a"]["perRunConvergenceCertified"], 0)

    def test_geometry_and_voxel_export_contracts_do_not_fabricate_seeds_or_coordinates(self):
        self.assertIn('"geometryPreview","Selected core geometry · source SVG"', self.js)
        self.assertIn('"core3dCanvas","Selected core geometry · Three.js canvas"', self.js)
        self.assertIn("geometryCsvRows", self.js)
        self.assertIn("raw_tally_mean", self.js)
        self.assertIn("x_center_cm", self.js)
        self.assertIn("individual seed IDs are not embedded in this plot payload", self.js)
        self.assertIn("toDataURL", self.js)


if __name__ == "__main__":
    unittest.main()
