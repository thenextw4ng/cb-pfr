import unittest
from cbpfr.experiment_analysis import summarize_optimizer_experiment


def payload():
    common = {"optimizer": "sampler", "optimizer_version": "1", "parameters": {"reads": 10}, "stopping_condition": "reads"}
    return {"experiment_id": "experiment-1", "runs": [
        {**common, "run_id": "r1", "seed": 1, "run_status": "completed", "candidate_records": [
            {"candidate_id": "A", "candidate_vector": [1, 0], "rank": 1, "qubo_energy": -3.0, "feasible": True, "objective_value": 0.4},
            {"candidate_id": "B", "candidate_vector": [0, 1], "rank": 2, "qubo_energy": -2.0, "feasible": False, "objective_value": 0.2}]},
        {**common, "run_id": "r2", "seed": 2, "run_status": "completed", "candidate_records": [
            {"candidate_id": "B", "candidate_vector": [0, 1], "rank": 1, "qubo_energy": -2.5, "feasible": True, "objective_value": 0.3},
            {"candidate_id": "A", "candidate_vector": [1, 0], "rank": 2, "qubo_energy": -1.5, "feasible": True, "objective_value": 0.4}]},
        {**common, "run_id": "r3", "seed": 3, "run_status": "timeout", "candidate_records": [], "failure_reason": "time limit"}]}


class OptimizerExperimentAnalysisTests(unittest.TestCase):
    def test_reports_failures_feasibility_objective_and_stability(self):
        result = summarize_optimizer_experiment(payload(), top_k=1)
        self.assertEqual(result["run_count"], 3)
        self.assertEqual(result["completed_run_count"], 2)
        self.assertEqual(result["failed_or_interrupted_run_count"], 1)
        self.assertEqual(result["run_status_counts"]["timeout"], 1)
        self.assertAlmostEqual(result["observed_candidate_feasibility_rate"], 3 / 4)
        self.assertEqual(result["best_observed_objective_value"], 0.2)
        self.assertEqual(result["best_observed_feasible_objective_value"], 0.3)
        self.assertEqual(result["ranking_stability"]["run_count"], 2)

    def test_supports_maximization(self):
        result = summarize_optimizer_experiment(payload(), objective_sense="max")
        self.assertEqual(result["best_observed_objective_value"], 0.4)
        self.assertEqual(result["best_observed_feasible_objective_value"], 0.4)

    def test_requires_completed_run(self):
        data = payload()
        data["runs"] = [data["runs"][2]]
        with self.assertRaisesRegex(ValueError, "completed run"):
            summarize_optimizer_experiment(data)

    def test_rejects_unknown_objective_sense(self):
        with self.assertRaisesRegex(ValueError, "objective_sense"):
            summarize_optimizer_experiment(payload(), objective_sense="best")


if __name__ == "__main__":
    unittest.main()
