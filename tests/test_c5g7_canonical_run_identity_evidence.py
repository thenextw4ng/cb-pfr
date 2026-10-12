"""Regression checks for the committed canonical C5G7 run-identity evidence."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "c5g7_canonical_high_budget_2026-10-12" / "model_identity_audit.json"


class CanonicalRunIdentityEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_three_runs_have_complete_output_hash_audits(self):
        self.assertEqual(self.data["status"], "INPUT_HASHES_MATCHED_INDEPENDENT_PHYSICS_REVIEW_PENDING")
        self.assertEqual([row["seed"] for row in self.data["runs"]], [720000, 730000, 740000])
        for row in self.data["runs"]:
            self.assertTrue(row["hashes_match_run_manifest"])
            self.assertEqual(row["output_hash_audit"], {
                "expected_file_count": 30,
                "missing_files": 0,
                "mismatched_hashes": 0,
            })
            self.assertEqual(row["raw_hdf5_audit"]["status"], "PASS")
            self.assertEqual(row["raw_hdf5_audit"]["passed_checks"], 22)
            self.assertEqual(row["raw_hdf5_audit"]["failed_checks"], 0)

    def test_common_model_identity_and_scientific_limits_are_explicit(self):
        self.assertEqual(self.data["model"]["openmc_version"], "0.16.0")
        self.assertEqual(
            self.data["model"]["energy_group_boundaries_eV"],
            [0.00001, 0.0635, 10.0, 100.0, 1000.0, 500000.0, 1000000.0, 20000000.0],
        )
        self.assertTrue(self.data["cross_run_checks"]["unique_statepoint_hashes"])
        self.assertTrue(self.data["cross_run_checks"]["common_mgxs_hash"])
        self.assertFalse(self.data["cross_run_checks"]["independent_primary_specification_signoff"])
        self.assertFalse(self.data["cross_run_checks"]["benchmark_compatible_same_quantity_spatial_validation"])
        self.assertFalse(self.data["model"]["model_identity_review"]["physical_fidelity_certified"])


if __name__ == "__main__":
    unittest.main()
