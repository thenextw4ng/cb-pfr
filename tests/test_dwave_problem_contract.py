import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_dwave_qubo_benchmark import build_qubo, load_problem


class DWaveProblemContractTests(unittest.TestCase):
    def test_load_and_build_qubo_with_offset_separated(self):
        data = {
            "instance_id": "toy",
            "variables": ["a", "b"],
            "linear": {"a": 1.0, "b": -2.0},
            "quadratic": [["a", "b", 3.0]],
            "offset": 4.0,
            "target_energy": 2.0,
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "problem.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            loaded = load_problem(path)
        qubo = build_qubo(loaded)
        self.assertEqual(qubo[("a", "a")], 1.0)
        self.assertEqual(qubo[("b", "b")], -2.0)
        self.assertEqual(qubo[("a", "b")], 3.0)
        self.assertEqual(loaded["offset"], 4.0)

    def test_rejects_undeclared_quadratic_variable(self):
        data = {
            "variables": ["a"],
            "linear": {},
            "quadratic": [["a", "b", 1.0]],
            "target_energy": 0.0,
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "undeclared variable"):
                load_problem(path)

    def test_rejects_nonfinite_target(self):
        data = {
            "variables": ["a"],
            "linear": {},
            "quadratic": [],
            "target_energy": float("inf"),
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "finite number"):
                load_problem(path)


if __name__ == "__main__":
    unittest.main()
