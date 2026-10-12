import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


PAGE_PATH = str(Path(__file__).resolve().parents[1] / "pages" / "06_High_Budget_Evidence.py")


class HighBudgetEvidenceDashboardTests(unittest.TestCase):
    def test_high_budget_page_loads_and_audits_archived_runs(self):
        app = AppTest.from_file(PAGE_PATH, default_timeout=30).run()
        self.assertEqual(app.exception, [])
        visible = "\n".join(element.value for element in app.markdown) + "\n" + "\n".join(element.value for element in app.title)
        self.assertIn("High-Budget Study Inspector", visible)
        self.assertIn("Interpretation boundary", visible)
        self.assertTrue(any("Candidate comparison" in tab.label for tab in app.tabs))
        self.assertTrue(any("Run-level inspection" in tab.label for tab in app.tabs))
        self.assertTrue(any("Provenance & limits" in tab.label for tab in app.tabs))
        self.assertTrue(any("18 unique run records" in element.value for element in app.success))

    def test_archived_evidence_has_expected_shape_and_no_winner_claim(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("high_budget_page", PAGE_PATH)
        module = importlib.util.module_from_spec(spec)
        # Execute only the pure helper definitions, not the Streamlit page body.
        source = Path(PAGE_PATH).read_text(encoding="utf-8")
        prefix = source.split('st.set_page_config(', 1)[0]
        namespace = {"__file__": PAGE_PATH}
        exec(compile(prefix, PAGE_PATH, "exec"), namespace)
        payload, runs, issues = namespace["load_and_audit"](namespace["EVIDENCE_PATH"])
        self.assertEqual(issues, [])
        self.assertEqual(len(runs), 18)
        self.assertEqual(runs["layout_signature"].nunique(), 6)
        self.assertFalse(payload["physical_validation_certified"])
        self.assertFalse(payload["winner_selected"])
        summary = namespace["summarize_runs"](runs)
        self.assertEqual(set(summary["layout_signature"]), {"MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM"})
        self.assertTrue((summary["n_runs"] == 3).all())


if __name__ == "__main__":
    unittest.main()
