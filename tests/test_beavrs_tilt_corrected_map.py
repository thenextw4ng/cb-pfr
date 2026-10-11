import tempfile
import unittest
from pathlib import Path

from scripts.run_beavrs_cycle1_map_validation import (
    load_measurement_values,
    normalize_detector_subset,
)


class BeavrsTiltCorrectedMapTests(unittest.TestCase):
    def test_loads_full_tilt_corrected_map_and_normalizes_instrumented_subset(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "full_tc.csv"
            path.write_text("A1,0.5\nB1,1.0\nC1,1.5\n")
            values = load_measurement_values(path)
            self.assertEqual(len(values), 3)
            subset = normalize_detector_subset({f"A{i}": float(i) for i in range(1, 59)})
            self.assertEqual(len(subset), 58)
            self.assertAlmostEqual(sum(subset.values()) / 58, 1.0)

    def test_rejects_duplicate_or_nonpositive_corrected_map_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text("A1,0.5\nA1,0.6\n")
            with self.assertRaisesRegex(ValueError, "duplicate detector label"):
                load_measurement_values(path)
            path.write_text("A1,0\n")
            with self.assertRaisesRegex(ValueError, "invalid measurement"):
                load_measurement_values(path)

    def test_normalizer_requires_58_instrumented_positions(self):
        with self.assertRaisesRegex(ValueError, "expected 58"):
            normalize_detector_subset({"A1": 1.0})


if __name__ == "__main__":
    unittest.main()
