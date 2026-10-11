import unittest

from scripts.analyze_solver_benchmark import analyze_rows, _repetitions_for_target


class SolverBenchmarkTests(unittest.TestCase):
    def test_tts_uses_success_rate_and_setup_cost(self):
        rows = [
            {"instance_id": "toy", "method": "classical", "trial_id": "1", "success": "1",
             "per_attempt_wall_time_s": "2", "one_time_setup_s": "3", "anneal_time_s": "0.1"},
            {"instance_id": "toy", "method": "classical", "trial_id": "2", "success": "1",
             "per_attempt_wall_time_s": "2", "one_time_setup_s": "3", "anneal_time_s": "0.1"},
            {"instance_id": "toy", "method": "classical", "trial_id": "3", "success": "0",
             "per_attempt_wall_time_s": "2", "one_time_setup_s": "3", "anneal_time_s": "0.1"},
        ]
        result = analyze_rows(rows)[0]
        self.assertEqual(result["trials"], 3)
        self.assertEqual(result["successes"], 2)
        self.assertEqual(result["tts_target_wall_s"], 3 + 5 * 2)
        self.assertAlmostEqual(result["tts_target_device_anneal_s"], 0.5)

    def test_zero_success_is_infinite_tts(self):
        self.assertIsNone(_repetitions_for_target(0.0, 0.99))
        rows = [
            {"instance_id": "toy", "method": "x", "trial_id": "1", "success": "0",
             "per_attempt_wall_time_s": "1"}
        ]
        self.assertEqual(analyze_rows(rows)[0]["tts_target_wall_s"], "inf")

    def test_duplicate_trial_is_rejected(self):
        row = {"instance_id": "toy", "method": "x", "trial_id": "1", "success": "1",
               "per_attempt_wall_time_s": "1"}
        with self.assertRaisesRegex(ValueError, "duplicate trial key"):
            analyze_rows([row, row])

    def test_setup_must_be_constant_per_method_and_instance(self):
        rows = [
            {"instance_id": "toy", "method": "x", "trial_id": "1", "success": "1",
             "per_attempt_wall_time_s": "1", "one_time_setup_s": "1"},
            {"instance_id": "toy", "method": "x", "trial_id": "2", "success": "1",
             "per_attempt_wall_time_s": "1", "one_time_setup_s": "2"},
        ]
        with self.assertRaisesRegex(ValueError, "must be constant"):
            analyze_rows(rows)

    def test_confidence_interval_contains_observed_rate(self):
        rows = [
            {"instance_id": "toy", "method": "x", "trial_id": str(i), "success": str(int(i <= 7)),
             "per_attempt_wall_time_s": "1"}
            for i in range(1, 11)
        ]
        result = analyze_rows(rows)[0]
        self.assertLessEqual(result["success_probability_wilson95_low"], 0.7)
        self.assertGreaterEqual(result["success_probability_wilson95_high"], 0.7)


if __name__ == "__main__":
    unittest.main()
