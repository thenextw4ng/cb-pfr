import unittest
from scripts.analyze_c5g7_canonical_convergence import C5G7_GROUP_BOUNDARIES, evaluate_runs


def run(seed, keff=1.18655, sd=0.00005, mgxs="corrected-c5g7-mgxs-hash", edges=C5G7_GROUP_BOUNDARIES):
    return {
        "round": f"seed_{seed}", "candidate_id": "c5g7-2x2-UMMU",
        "layout_signature": "UMMU", "seed": seed,
        "batches": 7000, "inactive": 100, "particles_per_batch": 10000, "threads": 1,
        "keff_mean": keff, "keff_std_dev": sd,
        "statepoint_sha256": f"statepoint-{seed}", "settings_sha256": f"settings-{seed}",
        "mgxs_sha256": mgxs, "mgxs_energy_group_boundaries": list(edges),
        "mgxs_group_structure_audit": "PASS",
        "source_convergence": {"status": "DIAGNOSTIC_REVIEW_REQUIRED", "entropy": {"active_mean": 2.0}},
        "raw_hdf5_audit": "PASS",
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

    def test_inconsistent_mgxs_hashes_fail_data_identity(self):
        rows = [run(720000), run(730000), run(740000, mgxs="different")]
        result = evaluate_runs(rows)
        self.assertEqual(result["status"], "FAIL_DATA_INTEGRITY_OR_MODEL_IDENTITY")

    def test_nonstandard_energy_group_structure_fails_closed(self):
        wrong_edges = (1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1.0, 1e3, 1e7)
        rows = [run(720000), run(730000), run(740000, edges=wrong_edges)]
        result = evaluate_runs(rows)
        self.assertEqual(result["status"], "FAIL_DATA_INTEGRITY_OR_MODEL_IDENTITY")
        self.assertFalse(result["global_checks"]["standard_c5g7_energy_group_structure"])

    def test_duplicate_seeds_fail_data_integrity(self):
        rows = [run(720000), run(720000), run(740000)]
        result = evaluate_runs(rows)
        self.assertEqual(result["status"], "FAIL_DATA_INTEGRITY_OR_MODEL_IDENTITY")


if __name__ == "__main__":
    unittest.main()
