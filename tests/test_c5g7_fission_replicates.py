import unittest

from scripts.aggregate_c5g7_fission_replicates import (
    ReplicateAggregationError,
    aggregate_reports,
)


def report(seed, sha, pf, keff=1.18):
    return {
        "candidate_id": "c5g7-2x2-UMMU",
        "layout_signature": "UMMU",
        "seed": seed,
        "statepoint_sha256": sha * 64,
        "positions_order": ["p00", "p01", "p10", "p11"],
        "fission_rate_peaking_factor": pf,
        "keff_mean": keff,
        "assembly_integrated_fission_rate": {
            "p00": 4.0 + pf, "p01": 2.0, "p10": 3.0, "p11": 1.0,
        },
    }


class C5G7FissionReplicateTests(unittest.TestCase):
    def test_aggregates_independent_seed_runs(self):
        result = aggregate_reports([report(11, "a", 1.2), report(22, "b", 1.4), report(33, "c", 1.6)])
        self.assertEqual(result["replicate_count"], 3)
        self.assertAlmostEqual(result["fission_rate_peaking_factor"]["mean"], 1.4)
        self.assertAlmostEqual(result["fission_rate_peaking_factor"]["between_seed_sample_sd"], 0.2)
        self.assertAlmostEqual(result["fission_rate_peaking_factor"]["standard_error_of_replicate_mean"], 0.2 / (3 ** 0.5))
        self.assertEqual(result["status"], "REPLICATE_UNCERTAINTY_ESTIMATED")

    def test_rejects_single_run(self):
        with self.assertRaises(ReplicateAggregationError):
            aggregate_reports([report(11, "a", 1.2)])

    def test_rejects_duplicate_seed_or_statepoint(self):
        with self.assertRaises(ReplicateAggregationError):
            aggregate_reports([report(11, "a", 1.2), report(11, "b", 1.4)])
        with self.assertRaises(ReplicateAggregationError):
            aggregate_reports([report(11, "a", 1.2), report(22, "a", 1.4)])

    def test_rejects_missing_provenance_and_nonfinite_values(self):
        item = report(11, "a", 1.2)
        del item["seed"]
        with self.assertRaises(ReplicateAggregationError):
            aggregate_reports([item, report(22, "b", 1.4)])
        with self.assertRaises(ReplicateAggregationError):
            aggregate_reports([report(11, "a", float("nan")), report(22, "b", 1.4)])

    def test_rejects_mixed_candidate_or_layout(self):
        second = report(22, "b", 1.4)
        second["candidate_id"] = "other"
        with self.assertRaises(ReplicateAggregationError):
            aggregate_reports([report(11, "a", 1.2), second])


if __name__ == "__main__":
    unittest.main()
