import math
import unittest

from scripts.evaluate_kritz2_reference import evaluate


class Kritz2ReferenceEvaluatorTests(unittest.TestCase):
    def test_comparison_records_delta_in_pcm_and_does_not_claim_validation(self):
        result = evaluate("2:1-cold", 0.99500, 0.00050, "reflective-pin-cell")
        self.assertAlmostEqual(result["delta_pcm"], 37.0)
        self.assertEqual(result["validation_status"], "NOT_ESTABLISHED")
        self.assertIn("finite-core", result["limitations"][2])

    def test_missing_mox_reference_spread_is_not_invented(self):
        result = evaluate("2:19-cold", 0.9990, 0.0005)
        self.assertIsNone(result["reference_participant_spread"])
        self.assertEqual(result["diagnostic"], "REFERENCE_SPREAD_UNAVAILABLE")
        self.assertIsNone(result["absolute_delta_over_combined_spread"])

    def test_invalid_inputs_rejected(self):
        invalid_cases = [
            (float("nan"), 0.001),
            (1.0, -0.1),
            (1.0, float("inf")),
        ]
        for keff, std in invalid_cases:
            with self.subTest(keff=keff, std=std):
                with self.assertRaises(ValueError):
                    evaluate("2:1-cold", keff, std)


if __name__ == "__main__":
    unittest.main()
