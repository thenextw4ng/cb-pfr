import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReleaseAuthorMetadataTests(unittest.TestCase):
    def test_author_name_is_consistent_across_release_metadata(self):
        expected = "Fahry Bagus Adiputra"

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
        zenodo = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn(f"**Author:** {expected}", readme)
        self.assertIn('given-names: Fahry Bagus', citation)
        self.assertEqual(
            [creator.get("name") for creator in zenodo.get("creators", [])],
            [expected],
        )
        self.assertRegex(
            pyproject,
            r'authors\s*=\s*\[\{\s*name\s*=\s*"Fahry Bagus Adiputra"\s*\}\]',
        )
        self.assertNotIn("Fachry Bagus Adiputra", readme + citation + pyproject)
        self.assertNotIn(
            "Fachry Bagus Adiputra",
            json.dumps(zenodo, ensure_ascii=False),
        )


if __name__ == "__main__":
    unittest.main()
