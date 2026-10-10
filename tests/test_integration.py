import unittest

from cbpfr.integration import rank_candidate_batch, ranking_to_records
from cbpfr.qubo import CoreSpec, build_usmanov_style_qubo, enumerate_feasible_candidates
from cbpfr.ranking import MetricLimit, PhysicalEstimate


class IntegrationAdapterTests(unittest.TestCase):
    def setUp(self):
        self.spec = CoreSpec(
            name="seven_position_toy",
            positions=tuple(f"p{i}" for i in range(7)),
            boundary=frozenset({f"p{i}" for i in range(1, 7)}),
            inner=frozenset({"p0"}),
            edges=tuple((f"p{i}", f"p{1 + (i % 6)}") for i in range(1, 7)),
            inventory=(3, 3, 1),
        )
        self.model = build_usmanov_style_qubo(self.spec)
        self.candidates = enumerate_feasible_candidates(self.model)[:3]
        self.metrics = [
            MetricLimit(
                name="synthetic_response",
                upper=1.0,
                z=1.0,
                scale=1.0,
                weight=1.0,
                uncertainty_kind="synthetic_standard_error",
                units="arbitrary",
                bound_kind="operational_heuristic",
            )
        ]
        self.estimates = {
            c.candidate_id: PhysicalEstimate(c.candidate_id, {"synthetic_response": (0.5, 0.01)})
            for c in self.candidates
        }

    def test_adapter_delegates_to_existing_ranking_methods(self):
        result = rank_candidate_batch(
            self.model, self.candidates, self.estimates, self.metrics,
            {"synthetic_response": 0.02},
        )
        self.assertEqual(set(result), {"qubo_only", "point_estimate", "cb_pfr", "uniform_margin"})
        self.assertTrue(all(len(rows) == len(self.candidates) for rows in result.values()))

    def test_records_are_labeled_and_json_friendly(self):
        result = rank_candidate_batch(
            self.model, self.candidates, self.estimates, self.metrics,
            {"synthetic_response": 0.02},
        )
        records = ranking_to_records(result, data_kind="synthetic")
        self.assertEqual(len(records), 4 * len(self.candidates))
        self.assertTrue(all(row["data_kind"] == "synthetic" for row in records))
        self.assertTrue(all(row["physical_simulation_performed"] is False for row in records))
        self.assertTrue(all("candidate_vector" in row for row in records))

    def test_duplicate_candidate_ids_rejected(self):
        duplicate = [self.candidates[0], self.candidates[0]]
        with self.assertRaisesRegex(ValueError, "unique"):
            rank_candidate_batch(
                self.model, duplicate, self.estimates, self.metrics,
                {"synthetic_response": 0.02},
            )

    def test_estimate_key_mismatch_rejected(self):
        candidate = self.candidates[0]
        mismatched = {"wrong-id": PhysicalEstimate(candidate.candidate_id, {"synthetic_response": (0.5, 0.01)})}
        with self.assertRaisesRegex(ValueError, "does not match"):
            rank_candidate_batch(
                self.model, [candidate], mismatched, self.metrics,
                {"synthetic_response": 0.02},
            )

    def test_invalid_data_kind_rejected(self):
        result = rank_candidate_batch(
            self.model, self.candidates, self.estimates, self.metrics,
            {"synthetic_response": 0.02},
        )
        with self.assertRaisesRegex(ValueError, "data_kind"):
            ranking_to_records(result, data_kind="demo")


if __name__ == "__main__":
    unittest.main()
