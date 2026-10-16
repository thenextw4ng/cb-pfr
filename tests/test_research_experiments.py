import contextlib
import csv
import importlib.util
import io
import json
import math
import random
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class ResearchExperimentTests(unittest.TestCase):
    def test_convergence_slope_and_defaults(self):
        m = load_script("analyze_c5g7_convergence_study")
        self.assertAlmostEqual(m.slope_per_1000([0, 1, 2, 3]), 1000.0)
        self.assertEqual(m.DEFAULTS["minimum_active_batches"], 100)

    def test_incremental_qubo_energy(self):
        m = load_script("run_classical_vs_qubo_benchmark")
        ins = m.Instance(10, 1234)
        x = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
        count = sum(x)
        delta, _, dc = ins.flip_delta(x, 2, count)
        y = x.copy()
        y[2] = 1 - y[2]
        self.assertAlmostEqual(ins.energy(x) + delta, ins.energy(y))
        self.assertEqual(dc, -1)

    def test_equal_budget_policy_smoke_on_synthetic_contract_fixture(self):
        m = load_script("run_equal_budget_c5g7_selection")
        sigs = list(m.SIGS)
        stage = {"UMMU": "P1", "MUUM": "P2", "MMUU": "P3", "UMUM": "P3", "MUMU": "P4", "UUMM": "P4"}
        rng = random.Random(20261016)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            low_path, high_path, out = root / "low.csv", root / "high.csv", root / "out"
            with low_path.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["replicate", "signature", "batches", "inactive", "particles", "F_fission"])
                w.writeheader()
                for rep in range(1, 201):
                    for idx, sig in enumerate(sigs):
                        score = 1.10 + idx * 0.004 + 0.001 * math.sin(rep / 4.0) + rng.gauss(0, 0.001)
                        w.writerow({"replicate": rep, "signature": sig, "batches": 800, "inactive": 500,
                                    "particles": 2000, "F_fission": score})
            with high_path.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["stage", "signature", "replicate", "batches", "inactive", "particles", "F_fission"])
                w.writeheader()
                for idx, sig in enumerate(sigs):
                    for rep in range(1, 11):
                        score = 1.10 + idx * 0.004 + 0.0005 * math.sin(rep) + rng.gauss(0, 0.0003)
                        w.writerow({"stage": stage[sig], "signature": sig, "replicate": rep, "batches": 10000,
                                    "inactive": 1000, "particles": 10000, "F_fission": score})
            argv = ["run_equal_budget_c5g7_selection", "--v2a-csv", str(low_path), "--high-budget-csv", str(high_path), "--outdir", str(out)]
            with mock.patch.object(sys, "argv", argv):
                with contextlib.redirect_stdout(io.StringIO()):
                    rc = m.main()
            self.assertEqual(rc, 0)
            report = json.loads((out / "equal_budget_policy_report.json").read_text())
            self.assertEqual(report["status"], "COMPLETED_OFFLINE_REPLAY")
            self.assertEqual(report["v2a_rows"], 1200)
            self.assertEqual(report["high_budget_rows"], 60)
            self.assertEqual(report["budget_run_equivalents"], 18)
            self.assertEqual(report["new_openmc_runs"], 0)
            self.assertEqual(len(report["summary"]), 4)

if __name__ == "__main__":
    unittest.main()
