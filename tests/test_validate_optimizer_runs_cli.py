import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "validate_optimizer_runs.py"


class ValidateOptimizerRunsCliTests(unittest.TestCase):
    def test_cli_validates_and_writes_normalized_run_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "experiment.json"
            output = root / "normalized.json"
            payload = {
                "schema_version": "1.0",
                "experiment_id": "stage2-test",
                "runs": [{
                    "run_id": "seed-1",
                    "optimizer": "test_sampler",
                    "optimizer_version": "0.1",
                    "seed": 1,
                    "parameters": {"reads": 50},
                    "stopping_condition": "reads_exhausted",
                    "run_status": "completed",
                    "candidate_records": [
                        {"candidate_id": "A", "rank": 1, "qubo_energy": -1.0, "feasible": True}
                    ],
                }],
            }
            source.write_text(json.dumps(payload), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(source), "--output", str(output)],
                cwd=REPO_ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            normalized = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(normalized["runs"][0]["optimizer"], "test_sampler")
            self.assertEqual(normalized["runs"][0]["candidate_records"][0]["candidate_id"], "A")
            self.assertFalse(normalized["runs"][0]["physical_simulation_performed"])

    def test_cli_rejects_invalid_records_and_does_not_write_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "experiment.json"
            output = root / "normalized.json"
            source.write_text(json.dumps({"runs": [{"run_id": "incomplete"}]}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(source), "--output", str(output)],
                cwd=REPO_ROOT, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
