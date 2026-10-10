"""Tests for strict OpenMC baseline-summary comparison."""
import unittest

from scripts.compare_openmc_baseline import compare_records


def fixture():
    audit = {
        "statepoint_read_success": True,
        "n_batches": 20000,
        "n_inactive": 500,
        "n_particles": 10000,
        "n_realizations": 19500,
        "run_mode": "eigenvalue",
        "energy_mode": "multi-group",
        "keff": {"mean": 1.186394144702191, "std_dev": 5.6113408647969484e-05},
        "tallies": [{
            "id": 10,
            "scores": ["flux", "fission", "nu-fission"],
            "filters": [{"type": "MeshFilter", "mesh_dimension": [51, 51, 1]}],
            "mean_finite": True,
            "std_dev_finite": True,
        }],
    }
    baseline = {
        "n_batches": 20000,
        "n_inactive": 500,
        "n_particles": 10000,
        "n_realizations": 19500,
        "run_mode": "eigenvalue",
        "energy_mode": "multi-group",
        "keff_mean": 1.186394144702191,
        "keff_std_dev": 5.6113408647969484e-05,
        "tally_mesh_dimension": [51, 51, 1],
        "tally_scores": ["flux", "fission", "nu-fission"],
    }
    return audit, baseline


class CompareOpenMCBaselineTests(unittest.TestCase):
    def test_matching_export_passes(self):
        audit, baseline = fixture()
        result = compare_records(audit, baseline)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["failed_count"], 0)

    def test_keff_mismatch_fails_closed(self):
        audit, baseline = fixture()
        audit["keff"]["mean"] = 1.19
        result = compare_records(audit, baseline)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("keff_mean", result["failed_checks"])

    def test_wrong_mesh_fails_closed(self):
        audit, baseline = fixture()
        audit["tallies"][0]["filters"][0]["mesh_dimension"] = [50, 51, 1]
        result = compare_records(audit, baseline)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("mesh_tally_present", result["failed_checks"])

    def test_missing_baseline_metadata_fails_closed(self):
        audit, baseline = fixture()
        del baseline["n_realizations"]
        result = compare_records(audit, baseline)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("metadata:n_realizations", result["failed_checks"])

    def test_nonfinite_value_fails(self):
        audit, baseline = fixture()
        audit["keff"]["std_dev"] = float("nan")
        result = compare_records(audit, baseline)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("keff_std_dev", result["failed_checks"])


if __name__ == "__main__":
    unittest.main()
