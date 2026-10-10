import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "analyze_repeatability.py"


class RepeatabilityCliTests(unittest.TestCase):
    def test_cli_writes_summary_from_recorded_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "runs.json"
            output = root / "summary.json"
            source.write_text(json.dumps({
                "evidence_kind": "synthetic_test",
                "top_k": 2,
                "runs": [
                    {"run_id": "r1", "candidate_ids_ranked": ["A", "B", "C"]},
                    {"run_id": "r2", "candidate_ids_ranked": ["A", "C", "B"]},
                    {"run_id": "r3", "candidate_ids_ranked": ["B", "A", "C"]},
                ],
            }), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(source), "--output", str(output)],
                cwd=REPO_ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["run_ids"], ["r1", "r2", "r3"])
            self.assertEqual(payload["summary"]["run_count"], 3)
            self.assertEqual(payload["evidence_kind"], "synthetic_test")
            self.assertIs(payload["physical_simulation_performed"], False)

    def test_cli_does_not_overwrite_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "runs.json"
            output = root / "summary.json"
            source.write_text(json.dumps({"runs": [{"run_id": "r1", "candidate_ids_ranked": ["A"]}]}), encoding="utf-8")
            output.write_text("keep-me", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(source), "--output", str(output)],
                cwd=REPO_ROOT, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "keep-me")


if __name__ == "__main__":
    unittest.main()
