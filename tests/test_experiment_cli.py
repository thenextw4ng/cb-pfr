import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ExperimentCliTests(unittest.TestCase):
    def test_validate_then_analyze_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source, validated, summary = base / "runs.json", base / "validated.json", base / "summary.json"
            payload = {"experiment_id": "cli-test", "runs": [
                {"run_id": "r1", "optimizer": "test", "optimizer_version": "0.1", "seed": 1,
                 "parameters": {"reads": 10}, "stopping_condition": "reads", "run_status": "completed",
                 "candidate_records": [
                    {"candidate_id": "A", "candidate_vector": [1, 0], "rank": 1, "qubo_energy": -1.0, "feasible": True, "objective_value": 0.5},
                    {"candidate_id": "B", "candidate_vector": [0, 1], "rank": 2, "qubo_energy": -0.5, "feasible": False, "objective_value": 0.8}]},
                {"run_id": "r2", "optimizer": "test", "optimizer_version": "0.1", "seed": 2,
                 "parameters": {"reads": 10}, "stopping_condition": "reads", "run_status": "completed",
                 "candidate_records": [
                    {"candidate_id": "B", "candidate_vector": [0, 1], "rank": 1, "qubo_energy": -0.8, "feasible": True, "objective_value": 0.6},
                    {"candidate_id": "A", "candidate_vector": [1, 0], "rank": 2, "qubo_energy": -0.4, "feasible": True, "objective_value": 0.5}]}
            ]}
            source.write_text(json.dumps(payload), encoding="utf-8")
            validate = subprocess.run([sys.executable, str(ROOT/"scripts/validate_optimizer_runs.py"), "--input", str(source), "--output", str(validated)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(validate.returncode, 0, validate.stderr)
            analyze = subprocess.run([sys.executable, str(ROOT/"scripts/analyze_optimizer_experiment.py"), "--input", str(validated), "--output", str(summary), "--top-k", "1"], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(analyze.returncode, 0, analyze.stderr)
            report = json.loads(summary.read_text())
            self.assertEqual(report["summary"]["run_count"], 2)
            self.assertEqual(report["summary"]["best_observed_objective_value"], 0.5)
            self.assertEqual(report["summary"]["ranking_stability"]["run_count"], 2)

    def test_invalid_records_do_not_create_validated_file(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory)/"bad.json", Path(directory)/"out.json"
            source.write_text('{"runs":[{"run_id":"incomplete"}]}', encoding="utf-8")
            result = subprocess.run([sys.executable, str(ROOT/"scripts/validate_optimizer_runs.py"), "--input", str(source), "--output", str(output)], cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
