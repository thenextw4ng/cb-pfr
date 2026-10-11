import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_c5g7_layout_selection_qubo.py"
SPEC = importlib.util.spec_from_file_location("selection_qubo", PATH)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def row(cid="a", layout="UMMU", keff=1.18, sd=0.001, runs=3):
    return {"candidate_id": cid, "layout_signature": layout, "mean_keff": keff,
            "between_seed_sd_keff": sd, "mean_fission_rate_peaking_factor": 1.2,
            "between_seed_sd_fission_peaking_factor": 0.02, "n_runs": runs}


class SelectionQuboTests(unittest.TestCase):
    def test_refuses_selection_without_feasible_candidate(self):
        result = MOD.build_qubo([row(keff=1.3)], 1.17, 1.20)
        self.assertEqual(result["status"], "NO_FEASIBLE_CANDIDATE")
        with self.assertRaises(ValueError):
            MOD.evaluate_energy(result, [1])

    def test_requires_three_runs(self):
        with self.assertRaisesRegex(ValueError, "three independent runs"):
            MOD.build_qubo([row(runs=2)], 1.17, 1.20)

    def test_rejects_duplicate_layouts(self):
        with self.assertRaisesRegex(ValueError, "duplicate layout_signature"):
            MOD.build_qubo([row("a"), row("b")], 1.17, 1.20)

    def test_rejects_nonfinite_bounds(self):
        with self.assertRaises(ValueError):
            MOD.build_qubo([row()], float("nan"), 1.2)

    def test_rejects_boolean_bits(self):
        result = MOD.build_qubo([row()], 1.17, 1.20)
        with self.assertRaisesRegex(ValueError, "integer binary"):
            MOD.evaluate_energy(result, [True])


if __name__ == "__main__":
    unittest.main()
