import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_beavrs_cycle1_map_result import PINNED_BEAVRS_COMMIT, audit_run, sha256_file


class BeavrsResultAuditTests(unittest.TestCase):
    def _make_fixture(self, root: Path) -> None:
        labels = [f"A{i + 1}" for i in range(58)]
        raw = {label: float(i + 1) for i, label in enumerate(labels)}
        mean = sum(raw.values()) / len(raw)
        measured = {label: value / mean for label, value in raw.items()}
        mesh_map = {label: [i % 17 + 1, i // 17 + 1] for i, label in enumerate(labels)}
        (root / "beavrs_measurements_normalized.json").write_text(json.dumps(measured))
        (root / "beavrs_assembly_mesh_map.json").write_text(json.dumps(mesh_map))
        (root / "geometry.xml").write_text("<geometry />\n")
        (root / "statepoint.250.h5").write_bytes(b"test-statepoint-bytes")
        (root / "openmc.log").write_text("Calculation complete.\n")
        (root / "source_provenance.txt").write_text(f"BEAVRS_COMMIT={PINNED_BEAVRS_COMMIT}\n")
        (root / "nuclear_data_archive.sha256").write_text("a" * 64 + "  data.tar.xz\n")
        (root / "cross_sections_xml.sha256").write_text("b" * 64 + "  cross_sections.xml\n")
        crosswalk_path = root / "beavrs_coordinate_crosswalk.csv"
        with crosswalk_path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=[
                "assembly", "template_token", "template_row_index_0based",
                "template_column_index_0based", "mesh_x_index_1based",
                "mesh_y_index_1based", "mesh_center_x_cm", "mesh_center_y_cm",
                "is_instrumented_detector",
            ])
            writer.writeheader()
            for i in range(176):
                label = labels[i] if i < len(labels) else f"X{i + 1}"
                writer.writerow({
                    "assembly": label,
                    "template_token": label,
                    "template_row_index_0based": i // 19,
                    "template_column_index_0based": i % 19,
                    "mesh_x_index_1based": i % 15 + 1,
                    "mesh_y_index_1based": i // 15 % 15 + 1,
                    "mesh_center_x_cm": (i % 15 - 7) * 21.50364,
                    "mesh_center_y_cm": (i // 15 % 15 - 7) * 21.50364,
                    "is_instrumented_detector": label in measured,
                })
        manifest = {
            "upstream_commit": PINNED_BEAVRS_COMMIT,
            "model_input_sha256": {"geometry.xml": sha256_file(root / "geometry.xml")},
            "coordinate_crosswalk": {
                "file": crosswalk_path.name,
                "sha256": sha256_file(crosswalk_path),
                "assembly_rows": 176,
                "instrumented_detector_rows": 58,
            },
        }
        (root / "beavrs_run_manifest.json").write_text(json.dumps(manifest))
        with (root / "beavrs_cycle1_day0_map_comparison.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=[
                "assembly", "measured_normalized", "calculated_normalized",
                "residual_calculated_minus_measured", "absolute_relative_error_percent"
            ])
            writer.writeheader()
            for label in labels:
                value = measured[label]
                writer.writerow({
                    "assembly": label,
                    "measured_normalized": value,
                    "calculated_normalized": value,
                    "residual_calculated_minus_measured": 0.0,
                    "absolute_relative_error_percent": 0.0,
                })
        result = {
            "status": "PRELIMINARY_EXPERIMENTAL_COMPARISON",
            "physical_validation_claim": "NOT_ESTABLISHED",
            "upstream_commit": PINNED_BEAVRS_COMMIT,
            "statepoint": "statepoint.250.h5",
            "statepoint_sha256": sha256_file(root / "statepoint.250.h5"),
            "metrics": {
                "normalized_map_rmse": 0.0,
                "normalized_map_mae": 0.0,
                "mean_absolute_relative_error_percent": 0.0,
                "pearson_correlation": 1.0,
            },
        }
        (root / "beavrs_cycle1_day0_map_comparison.json").write_text(json.dumps(result))

    def test_passes_consistent_fixture_but_never_claims_physical_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_fixture(root)
            result = audit_run(root)
            self.assertEqual(result["status"], "PASS_INTEGRITY_ONLY")
            self.assertEqual(result["physical_validation_claim"], "NOT_ESTABLISHED")
            self.assertEqual(result["failed_checks"], [])

    def test_detects_modified_statepoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_fixture(root)
            (root / "statepoint.250.h5").write_bytes(b"changed")
            result = audit_run(root)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("statepoint_sha256_matches", result["failed_checks"])


if __name__ == "__main__":
    unittest.main()
