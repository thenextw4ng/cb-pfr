import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")


class ReactorQDashboardSmokeTests(unittest.TestCase):
    def test_dashboard_starts_and_exposes_core_tabs(self):
        app = AppTest.from_file(APP_PATH, default_timeout=30).run()
        self.assertEqual(app.exception, [])
        visible_text = "\n".join(element.value for element in app.markdown)
        self.assertIn("ReactorQ Studio", visible_text)
        self.assertIn("synthetic", visible_text.lower())
        tab_labels = [element.label for element in app.tabs]
        self.assertIn("Repeatability", tab_labels)

    def test_repeatability_tab_analyzes_prefilled_demo_runs(self):
        app = AppTest.from_file(APP_PATH, default_timeout=30).run()
        analyze_button = next(
            button for button in app.button
            if button.label == "Analyze repeatability"
        )
        analyze_button.click().run()
        self.assertEqual(app.exception, [])
        # AppTest collects metrics from all tabs, not only the active tab.
        self.assertGreaterEqual(len(app.metric), 3)
        self.assertTrue(any(
            button.label == "Download repeatability summary JSON"
            for button in app.get("download_button")
        ))

    def test_repeatability_tab_reports_invalid_json_without_crashing(self):
        app = AppTest.from_file(APP_PATH, default_timeout=30).run()
        app.text_area[0].set_value("{invalid json")
        analyze_button = next(
            button for button in app.button
            if button.label == "Analyze repeatability"
        )
        analyze_button.click().run()
        self.assertEqual(app.exception, [])
        self.assertTrue(any("Could not analyze rankings" in element.value for element in app.error))


if __name__ == "__main__":
    unittest.main()
