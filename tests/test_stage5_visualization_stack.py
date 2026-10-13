from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
STYLES = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")
CORE_3D = (ROOT / "web" / "core_geometry_3d.js").read_text(encoding="utf-8")
DOCS = (ROOT / "docs" / "CBPFR_VISUALIZATION_STACK.md").read_text(encoding="utf-8")


class TargetedVisualizationStackTests(unittest.TestCase):
    def test_plotly_is_the_version_pinned_numeric_chart_engine(self):
        self.assertIn("https://cdn.plot.ly/plotly-2.35.2.min.js", INDEX)
        self.assertIn("plotly.js-dist-min@2.35.2/plotly.min.js", INDEX)
        self.assertIn("Plotly.react(", APP)
        self.assertIn("cbpfr-plotly-failed", INDEX + APP)
        self.assertIn("plotlyStackStatus", INDEX + APP)

    def test_geometry_has_a_source_derived_native_svg_path(self):
        self.assertIn("function renderModelGeometrySvg(", APP)
        self.assertIn("model-geometry-svg", APP)
        self.assertIn('id="coreView2d"', INDEX)
        self.assertIn('id="geometryPreview"', INDEX)
        self.assertIn("2D FALLBACK", APP)
        self.assertIn("svgStackStatus", INDEX + APP)

    def test_existing_three_module_remains_optional_and_has_failure_path(self):
        self.assertIn('import("three")', INDEX)
        self.assertIn('import("/core_geometry_3d.js")', INDEX)
        self.assertIn("cbpfr-core3d-failed", INDEX + APP)
        self.assertIn("threeStackStatus", INDEX + APP)
        self.assertIn("renderer.dispose()", CORE_3D)

    def test_vtkjs_is_not_added_as_a_runtime_dependency(self):
        runtime = " ".join((INDEX, APP, CORE_3D)).lower()
        self.assertNotIn("@kitware/vtk.js", runtime)
        self.assertNotIn("vtk.js/build", runtime)
        self.assertNotIn("from 'vtk.js'", runtime)
        self.assertNotIn('from "vtk.js"', runtime)

    def test_renderer_status_strip_is_responsive_and_keeps_category_colors_separate(self):
        for status_id in ("plotlyStackStatus", "svgStackStatus", "threeStackStatus", "vtkStackStatus"):
            self.assertIn(f'id="{status_id}"', INDEX)
        self.assertIn(".renderer-stack-strip", STYLES)
        self.assertIn("@media(max-width:600px)", STYLES)
        self.assertIn('colorscale:"Cividis"', APP)
        self.assertIn('const materialEdgeColor = {M:"#f4bd62",U:"#55d4df"};', APP)
        self.assertIn("No contour, smoothing, or interpolation", DOCS)
        self.assertIn("51 × 51 × 30", DOCS)


if __name__ == "__main__":
    unittest.main()
