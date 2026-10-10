import unittest

from cbpfr.experiment_log import validate_experiment_payload, validate_optimizer_run_record


def valid_run(run_id="run-1"):
    return {
        "run_id": run_id, "optimizer": "simulated_annealing", "optimizer_version": "1.2.0",
        "seed": 17, "parameters": {"reads": 100, "sweeps": 500},
        "stopping_condition": "reads_exhausted", "run_status": "completed",
        "candidate_records": [
            {"candidate_id": "A", "candidate_vector": [1, 0, 1], "rank": 1, "qubo_energy": -2.5, "feasible": True, "objective_value": -2.5},
            {"candidate_id": "B", "candidate_vector": [0, 1, 0], "rank": 2, "qubo_energy": -1.0, "feasible": False, "objective_value": -1.0},
        ],
        "evidence_kind": "synthetic_test", "physical_simulation_performed": False,
    }


class OptimizerRunLogTests(unittest.TestCase):
    def test_valid_run_preserves_settings_and_candidate_metrics(self):
        normalized = validate_optimizer_run_record(valid_run())
        self.assertEqual(normalized["seed"], 17)
        self.assertEqual(normalized["parameters"]["reads"], 100)
        self.assertEqual(normalized["candidate_records"][0]["rank"], 1)

    def test_failed_run_requires_failure_reason(self):
        run = valid_run()
        run.update(run_status="failed", candidate_records=[])
        with self.assertRaisesRegex(ValueError, "failure_reason"):
            validate_optimizer_run_record(run)
        run["failure_reason"] = "sampler timeout"
        self.assertEqual(validate_optimizer_run_record(run)["run_status"], "failed")

    def test_rejects_duplicate_run_ids(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            validate_experiment_payload({"runs": [valid_run("same"), valid_run("same")]})

    def test_rejects_duplicate_ids_vectors_and_ranks(self):
        run = valid_run()
        run["candidate_records"][1]["candidate_id"] = "A"
        with self.assertRaisesRegex(ValueError, "duplicate candidate_id"):
            validate_optimizer_run_record(run)
        run = valid_run()
        run["candidate_records"][1]["candidate_vector"] = [1, 0, 1]
        with self.assertRaisesRegex(ValueError, "duplicate candidate vector"):
            validate_optimizer_run_record(run)
        run = valid_run()
        run["candidate_records"][1]["rank"] = 1
        with self.assertRaisesRegex(ValueError, "duplicate candidate rank"):
            validate_optimizer_run_record(run)

    def test_rejects_nonfinite_energy_and_objective(self):
        for field, value in (("qubo_energy", float("nan")), ("objective_value", float("inf"))):
            run = valid_run()
            run["candidate_records"][0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "finite"):
                validate_optimizer_run_record(run)

    def test_rejects_invalid_seed_settings_and_vector(self):
        run = valid_run()
        run["seed"] = True
        with self.assertRaisesRegex(ValueError, "seed"):
            validate_optimizer_run_record(run)
        run = valid_run()
        run["parameters"] = {"temperature": float("nan")}
        with self.assertRaisesRegex(ValueError, "strict-JSON"):
            validate_optimizer_run_record(run)
        run = valid_run()
        run["candidate_records"][0]["candidate_vector"] = [0, 2]
        with self.assertRaisesRegex(ValueError, "0/1"):
            validate_optimizer_run_record(run)


    def test_rejects_candidate_identity_drift_across_runs(self):
        first, second = valid_run("r1"), valid_run("r2")
        second["candidate_records"][0]["candidate_vector"] = [0, 0, 1]
        with self.assertRaisesRegex(ValueError, "different vectors across runs"):
            validate_experiment_payload({"runs": [first, second]})

    def test_rejects_inconsistent_vector_lengths(self):
        first, second = valid_run("r1"), valid_run("r2")
        second["candidate_records"].append({"candidate_id": "C", "candidate_vector": [1, 1], "rank": 3, "qubo_energy": -0.2, "feasible": True})
        with self.assertRaisesRegex(ValueError, "length must be consistent"):
            validate_experiment_payload({"runs": [first, second]})

    def test_rejects_missing_provenance_fields(self):
        run = valid_run()
        del run["optimizer_version"]
        with self.assertRaisesRegex(ValueError, "optimizer_version"):
            validate_optimizer_run_record(run)


if __name__ == "__main__":
    unittest.main()
