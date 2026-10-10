import unittest

from cbpfr.repeatability import summarize_repeated_rankings


class RepeatedRankingSummaryTests(unittest.TestCase):
    def test_top1_frequency_and_topk_overlap(self):
        result = summarize_repeated_rankings(
            [["a", "b", "c"], ["a", "c", "b"], ["b", "a", "c"]],
            top_k=2,
        )
        self.assertEqual(result["run_count"], 3)
        self.assertEqual(result["top1_selection_counts"], {"a": 2, "b": 1})
        self.assertAlmostEqual(result["top1_dominance"], 2 / 3)
        self.assertAlmostEqual(result["mean_pairwise_top_k_jaccard"], 5 / 9)
        self.assertIn("not a global-optimum certificate", result["interpretation"])

    def test_single_run_has_defined_pairwise_overlap(self):
        result = summarize_repeated_rankings([["candidate-1", "candidate-2"]], top_k=2)
        self.assertEqual(result["mean_pairwise_top_k_jaccard"], 1.0)
        self.assertEqual(result["top_k_selection_frequencies"]["candidate-2"], 1.0)

    def test_rejects_empty_input_and_empty_run(self):
        with self.assertRaisesRegex(ValueError, "at least one run"):
            summarize_repeated_rankings([])
        with self.assertRaisesRegex(ValueError, "cannot be empty"):
            summarize_repeated_rankings([[]])

    def test_rejects_duplicate_ids_in_one_run(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            summarize_repeated_rankings([["a", "a"]])

    def test_rejects_invalid_top_k(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            summarize_repeated_rankings([["a"]], top_k=0)


if __name__ == "__main__":
    unittest.main()
