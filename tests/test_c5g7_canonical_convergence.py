import unittest
from scripts.analyze_c5g7_canonical_convergence import evaluate_runs


def run(seed, keff=1.18655, sd=0.00005, mgxs="170cc799f496e952465583bb078b2a88eae0f09886a821fd7ee8999d1eb93216"):
    return {
        "round": f"seed_{seed}", "candidate_id": "c5g7-2x2-UMMU",
        "layout_signature": "UMMU", "seed": seed,
        "batches": 7000, "inactive": 100, "particles_per_batch": 10000, "threads": 1,
        "keff_mean": keff, "keff_std_dev": sd,
        "statepoint_sha256": f"statepoint-{seed}", "settings_sha256": f"settings-{seed}",
        "mgxs_sha256": mgxs, "raw_hdf5_audit": "PASS",
    }


class CanonicalConvergenceTests(unittest.TestCase):
    def test_passing_scalar_screen_still_not_official_acceptance(self):
        rows = [run(720000, keff=1.18654), run(730000, keff=1.18656), run(740000, keff=1.18655)]
        result = evaluate_runs(rows)
        self.assertEqual(result["status"], "NUMERICAL_SCREEN_PASS_FULL_BENCHMARK_STILL_BLOCKED")
        self.assertFalse(result["is_official_benchmark_acceptance"])
        self.assertTrue(result["metrics"]["numerical_screen_pass"])

    def test_high_per_run_uncertainty_fails_screen(self):
        rows = [run(720000, sd=0.0002), run(730000, sd=0.0002), run(740000, sd=0.0002)]
        result = evaluate_runs(rows)
        self.assertEqual(result["status"], "FAIL_OR_INCOMPLETE_NUMERICAL_SCREEN")
        self.assertFalse(result["metrics"]["numerical_screen_pass"])

    def test_wrong_mgxs_fails_data_identity(self):
        rows = [run(720000), run(730000), run(740000, mgxs="wrong")]
        result = evaluate_runs(rows)
        self.assertEqual(result["status"], "FAIL_DATA_INTEGRITY_OR_MODEL_IDENTITY")

    def test_duplicate_seeds_fail_data_integrity(self):
        rows = [run(720000), run(720000), run(740000)]
        result = evaluate_runs(rows)
        self.assertEqual(result["status"], "FAIL_DATA_INTEGRITY_OR_MODEL_IDENTITY")


if __name__ == "__main__":
    unittest.main()
