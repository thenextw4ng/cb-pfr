import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "enumerate_c5g7_layouts.py"


class C5G7LayoutEnumerationTests(unittest.TestCase):
    def test_enumerates_six_unique_balanced_layouts_and_marks_reference(self):
        from importlib.util import module_from_spec, spec_from_file_location

        spec = spec_from_file_location("enumerate_c5g7_layouts", SCRIPT)
        module = module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        manifest = module.build_design_space()

        self.assertEqual(manifest["candidate_count"], 6)
        layouts = manifest["candidate_layouts"]
        signatures = {item["candidate_id"] for item in layouts}
        self.assertEqual(len(signatures), 6)
        self.assertEqual(sum(item["is_canonical_reference_arrangement"] for item in layouts), 1)
        for candidate in layouts:
            self.assertEqual(list(candidate["fuel_assembly_layout"].values()).count("UO2"), 2)
            self.assertEqual(list(candidate["fuel_assembly_layout"].values()).count("MOX"), 2)
            self.assertIsNone(candidate["physical_results"])
            self.assertTrue(candidate["requires_transport_evaluation"])

    def test_cli_writes_valid_json_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "design_space.json"
            first = subprocess.run(
                [sys.executable, str(SCRIPT), "--output", str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(data["candidate_count"], 6)

            second = subprocess.run(
                [sys.executable, str(SCRIPT), "--output", str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("refusing to overwrite", second.stderr)

    def test_does_not_create_missing_parent_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "missing" / "design_space.json"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--output", str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.parent.exists())


if __name__ == "__main__":
    unittest.main()
