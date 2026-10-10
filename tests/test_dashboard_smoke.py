import unittest

from streamlit.testing.v1 import AppTest


class ReactorQDashboardSmokeTests(unittest.TestCase):
    def test_dashboard_starts_and_exposes_core_tabs(self):
        app = AppTest.from_file("app.py", default_timeout=30).run()
        self.assertEqual(app.exception, [])
        visible_text = "\n".join(element.value for element in app.markdown)
        self.assertIn("ReactorQ Studio", visible_text)
        self.assertIn("synthetic", visible_text.lower())


if __name__ == "__main__":
    unittest.main()
