import unittest
from scripts.audit_c5g7_source_convergence import analyze_traces


class C5G7SourceConvergenceTests(unittest.TestCase):
    def test_stable_synthetic_traces_are_diagnostic_not_certified(self):
        k = [1.1, 1.2, 1.18, 1.19, 1.186, 1.187, 1.185, 1.186]
        h = [2.0, 2.2, 2.1, 2.15, 2.14, 2.13, 2.14, 2.14]
        result = analyze_traces(k, h, inactive=2, n_batches=8)
        self.assertEqual(result["status"], "DIAGNOSTIC_REVIEW_REQUIRED")
        self.assertFalse(result["automatic_convergence_claim"])
        self.assertEqual(result["k_generation"]["active_trace_length"], 6)
        self.assertIn("last_minus_first_quarter_mean", result["entropy"])
        self.assertEqual(result["inactive_entropy"]["trace_length"], 2)
        self.assertIn("last_minus_first_quarter_mean", result["inactive_entropy"])
        self.assertIn("inactive_k_generation", result)
        self.assertFalse(result["automatic_convergence_claim"])

    def test_missing_entropy_fails_source_assessment(self):
        result = analyze_traces([1.0, 1.1, 1.0, 1.01, 1.0], [], inactive=1)
        self.assertEqual(result["status"], "FAIL_MISSING_ENTROPY_TRACE")
        self.assertIsNone(result["entropy"])

    def test_nonfinite_trace_rejected(self):
        with self.assertRaises(ValueError):
            analyze_traces([1.0, float("nan"), 1.0, 1.0], [2.0, 2.0, 2.0, 2.0], inactive=0)

    def test_invalid_inactive_count_rejected(self):
        with self.assertRaises(ValueError):
            analyze_traces([1.0, 1.0, 1.0], [2.0, 2.0, 2.0], inactive=3)


if __name__ == "__main__":
    unittest.main()
