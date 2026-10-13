import json
import math
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "config" / "benchmarks" / "c5g7_canonical_confirmation_profile.json"


class CanonicalConfirmationProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))

    def test_profile_declares_canonical_only_and_standard_groups(self):
        profile = self.profile
        self.assertEqual(profile["status"], "EXECUTED_NUMERICAL_SCREEN_PASS_VALIDATION_BLOCKED")
        self.assertEqual(profile["execution"]["run_count"], 3)
        self.assertEqual(profile["execution"]["physical_validation_status"], "BLOCKED")
        self.assertEqual(profile["model"]["candidate_id"], "c5g7-2x2-UMMU")
        self.assertEqual(profile["model"]["layout_signature"], "UMMU")
        self.assertEqual(
            profile["model"]["energy_group_boundaries_eV"],
            [1e-5, 0.0635, 10, 100, 1000, 500000, 1000000, 20000000],
        )

    def test_budget_arithmetic_is_exact(self):
        compute = self.profile["compute"]
        self.assertEqual(compute["active_batches"], compute["batches_total"] - compute["inactive_batches"])
        self.assertEqual(compute["nominal_histories_per_run"],
                         compute["batches_total"] * compute["particles_per_batch"])
        self.assertEqual(compute["nominal_active_histories_per_run"],
                         compute["active_batches"] * compute["particles_per_batch"])
        self.assertEqual(compute["nominal_histories_total"],
                         compute["nominal_histories_per_run"] * compute["runs"])
        self.assertEqual(compute["nominal_active_histories_total"],
                         compute["nominal_active_histories_per_run"] * compute["runs"])
        self.assertEqual(compute["runs"], len(compute["independent_seed_bases"]))
        self.assertEqual(len(set(compute["independent_seed_bases"])), compute["runs"])
        self.assertLess(compute["inactive_batches"], compute["batches_total"])

    def test_planning_estimate_is_consistent_but_not_a_claim(self):
        rationale = self.profile["planning_rationale"]
        previous = rationale["previous_profile"]
        compute = self.profile["compute"]
        ratio = compute["nominal_active_histories_per_run"] / previous["nominal_active_histories_per_run"]
        expected_sd = previous["observed_mean_within_run_keff_sd_pcm_approx"] / math.sqrt(ratio)
        self.assertAlmostEqual(ratio, rationale["active_histories_multiplier_approx"], places=7)
        self.assertAlmostEqual(expected_sd, rationale["idealized_expected_within_run_sd_pcm_approx"], places=2)
        self.assertIn("not a guarantee", rationale["caveat"].lower())

    def test_profile_does_not_claim_official_acceptance(self):
        self.assertFalse(self.profile["predeclared_project_screens"]["official_benchmark_acceptance"])
        nonclaims = self.profile["decision_policy"]["never"]
        self.assertTrue(any("safety" in item.lower() for item in nonclaims))
        self.assertTrue(any("winner" in item.lower() for item in nonclaims))
        self.assertTrue(any("convergence" in item.lower() for item in nonclaims))


if __name__ == "__main__":
    unittest.main()
