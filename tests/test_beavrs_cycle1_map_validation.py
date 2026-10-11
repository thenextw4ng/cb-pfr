import csv
import tempfile
import unittest
from pathlib import Path

from scripts.run_beavrs_cycle1_map_validation import (
    build_assembly_map,
    load_measurements,
    fahrenheit_to_kelvin,
    update_manifest_analysis,
)


class BeavrsCycle1MapValidationTests(unittest.TestCase):
    def test_analysis_updates_manifest_without_claiming_validation(self):
        manifest = {"status": "PREPARED_NOT_RUN"}
        result = {
            "status": "PRELIMINARY_EXPERIMENTAL_COMPARISON",
            "physical_validation_claim": "NOT_ESTABLISHED",
            "statepoint": "statepoint.500.h5",
            "statepoint_sha256": "abc123",
            "batches_completed": 500,
            "detector_count": 58,
            "keff": {"mean": 1.0, "standard_deviation": 0.001},
            "metrics": {"pearson_correlation": 0.03},
        }
        updated = update_manifest_analysis(manifest, result)
        self.assertEqual(updated["status"], "COMPLETED_PRELIMINARY_ANALYSIS_NOT_VALIDATED")
        self.assertEqual(updated["analysis_result"]["statepoint_sha256"], "abc123")
        self.assertEqual(updated["analysis_result"]["detector_count"], 58)
        self.assertEqual(updated["analysis_result"]["physical_validation_claim"], "NOT_ESTABLISHED")

    def test_cycle1_temperature_conversion_matches_reported_inlet_temperature(self):
        self.assertAlmostEqual(fahrenheit_to_kelvin(558.875), 565.8583333333, places=8)
        with self.assertRaisesRegex(ValueError, "finite"):
            fahrenheit_to_kelvin(float("nan"))

    def test_assembly_map_uses_one_based_mesh_indices_and_reverses_y(self):
        template = [["dummy" for _ in range(19)] for _ in range(19)]
        template[2][8] = "J___1"
        template[16][16] = "A__15"
        mapped = build_assembly_map(template)
        self.assertEqual(mapped["J1"], (7, 15))
        self.assertEqual(mapped["A15"], (15, 1))

    def test_assembly_map_rejects_duplicate_labels(self):
        template = [["dummy" for _ in range(19)] for _ in range(19)]
        template[2][8] = "J___1"
        template[3][9] = "J__1"
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
