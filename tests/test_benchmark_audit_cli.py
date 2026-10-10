import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BenchmarkAuditCliTests(unittest.TestCase):
    def test_checked_in_manifest_reports_blocked_and_preserves_blockers(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "gate.json"
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/audit_benchmark_manifest.py"),
                 "--input", str(ROOT / "config/benchmarks/c5g7_manifest.json"),
                 "--output", str(output)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["audit"]["status"], "blocked")
            self.assertTrue(any("required_state_to_material_map" in b for b in report["audit"]["blockers"]))
            self.assertIn("Structural gate status only", report["audit"]["claim_boundary"])

    def test_cli_refuses_to_overwrite_existing_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "gate.json"
            output.write_text('{"preserve": true}', encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/audit_benchmark_manifest.py"),
                 "--input", str(ROOT / "config/benchmarks/c5g7_manifest.json"),
                 "--output", str(output)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), {"preserve": True})


if __name__ == "__main__":
    unittest.main()
