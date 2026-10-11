import unittest

from scripts.compare_c5g7_reference import compare


class C5G7ReferenceComparisonTests(unittest.TestCase):
    def setUp(self):
        self.sim = {
            "candidate_id": "c5g7-2x2-UMMU",
            "keff_mean": 1.1728029349321403,
            "keff_std_dev": 0.019472323678449033,
            "fission_rate_peaking_factor": 1.942932842839654,
            "n_batches": 20,
            "n_inactive": 5,
            "n_particles": 100,
        }
        self.ref = {
            "candidate_id": "c5g7-2x2-UMMU",
            "keff_mean": "1.18655",
            "keff_uncertainty": "0.000095",
            "notes": "Published max pin power is 2.498",
        }

    def test_keff_difference_and_relative_difference_are_explicit(self):
        rows = compare(self.sim, self.ref)
        keff = rows[0]
        self.assertEqual(keff["metric"], "k_eff")
        self.assertAlmostEqual(float(keff["absolute_difference"]), -0.0137470650678597)
        self.assertAlmostEqual(float(keff["relative_difference_percent"]), 100 * (self.sim["keff_mean"] - 1.18655) / 1.18655)
        self.assertEqual(keff["comparison_status"], "NUMERICAL_SCREEN_ONLY_MODEL_IDENTITY_BLOCKED_LOW_STAT")

    def test_aggregate_summary_uses_standard_error_of_seed_mean(self):
        summary = {
            "workflow_run_id": 38112597526,
            "settings": {"batches": 100, "inactive_batches": 10, "particles_per_batch": 1000},
            "candidates": [{
                "candidate_id": "c5g7-2x2-UMMU",
                "n_runs": 3,
                "mean_keff": 1.1861026314460645,
                "between_seed_sd_keff": 0.0038633985032438967,
                "mean_fission_rate_peaking_factor": 1.8861131573187928,
            }],
        }
        rows = compare(summary, self.ref)
        self.assertAlmostEqual(float(rows[0]["simulation_standard_uncertainty"]), 0.0038633985032438967 / (3 ** 0.5))
        self.assertEqual(rows[0]["comparison_status"], "NUMERICAL_SCREEN_ONLY_MODEL_IDENTITY_BLOCKED_SMOKE_BUDGET")
        self.assertIn("38112597526", rows[0]["notes"])

    def test_pin_power_is_not_miscompared_to_assembly_peaking_factor(self):
        rows = compare(self.sim, self.ref)
        row = rows[1]
        self.assertEqual(row["comparison_status"], "BLOCKED_NOT_COMPARABLE_OBSERVABLE")
        self.assertEqual(row["reference_value"], "")
        self.assertEqual(row["absolute_difference"], "")

    def test_candidate_identity_must_match(self):
        with self.assertRaises(ValueError):
            compare(self.sim, {**self.ref, "candidate_id": "different"})

    def test_invalid_uncertainty_is_rejected(self):
        with self.assertRaises(ValueError):
            compare(self.sim, {**self.ref, "keff_uncertainty": "-1"})


if __name__ == "__main__":
    unittest.main()
