import csv
import tempfile
import unittest
from pathlib import Path

from scripts.run_beavrs_cycle1_map_validation import (
    build_assembly_map,
    load_measurements,
)


class BeavrsCycle1MapValidationTests(unittest.TestCase):
    def test_assembly_map_uses_one_based_mesh_indices_and_reverses_y(self):
        template = [["dummy" for _ in range(19)] for _ in range(19)]
        template[1][8] = "J___1"
        template[17][17] = "A__15"
        mapped = build_assembly_map(template)
        self.assertEqual(mapped["J1"], (8, 17))
        self.assertEqual(mapped["A15"], (17, 1))

    def test_assembly_map_rejects_duplicate_labels(self):
        template = [["dummy" for _ in range(19)] for _ in range(19)]
        template[1][8] = "J___1"
        template[2][9] = "J__1"
        with self.assertRaisesRegex(ValueError, "duplicate assembly label"):
            build_assembly_map(template)

    def test_measurements_require_exactly_58_positive_finite_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "map.csv"
            with path.open("w", newline="") as handle:
                writer = csv.writer(handle)
                for i in range(58):
                    writer.writerow([f"A{i + 1}", i + 1])
            values = load_measurements(path)
            self.assertEqual(len(values), 58)
            self.assertAlmostEqual(sum(values.values()) / len(values), 1.0)

    def test_measurements_reject_duplicate_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "map.csv"
            path.write_text("A1,1.0\nA1,1.1\n")
            with self.assertRaisesRegex(ValueError, "duplicate detector label"):
                load_measurements(path)


if __name__ == "__main__":
    unittest.main()
