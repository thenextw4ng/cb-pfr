import unittest

from scripts.build_c5g7_layout_selection_qubo import build_qubo, evaluate_energy


def candidate(cid, keff, keff_sd, fpeak, fpeak_sd):
    return {
        "candidate_id": cid,
        "layout_signature": cid,
        "mean_keff": keff,
        "between_seed_sd_keff": keff_sd,
        "mean_fission_rate_peaking_factor": fpeak,
        "between_seed_sd_fission_peaking_factor": fpeak_sd,
        "n_runs": 3,
    }


class C5G7LayoutSelectionQuboTests(unittest.TestCase):
    def test_one_hot_qubo_selects_lowest_score_among_feasible_candidates(self):
        rows = [
            candidate("A", 1.185, 0.001, 1.30, 0.02),
            candidate("B", 1.186, 0.001, 1.40, 0.01),
            candidate("C", 1.205, 0.001, 1.10, 0.02),
        ]
        report = build_qubo(rows, 1.18, 1.19, uncertainty_multiplier=1.0, risk_weight=1.0)
        self.assertEqual(report["status"], "READY_FOR_EXTERNAL_QUBO_SOLVER")
        self.assertEqual(report["feasible_candidate_count"], 2)
        self.assertAlmostEqual(evaluate_energy(report, [1, 0, 0]), 1.32)
        self.assertAlmostEqual(evaluate_energy(report, [0, 1, 0]), 1.41)
        self.assertGreater(evaluate_energy(report, [0, 0, 1]), evaluate_energy(report, [1, 0, 0]))
        self.assertGreater(evaluate_energy(report, [1, 1, 0]), evaluate_energy(report, [1, 0, 0]))
        self.assertGreater(evaluate_energy(report, [0, 0, 0]), evaluate_energy(report, [1, 0, 0]))

    def test_no_feasible_candidate_fails_closed(self):
        rows = [candidate("A", 1.14, 0.002, 1.3, 0.02)]
        report = build_qubo(rows, 1.18, 1.19)
        self.assertEqual(report["status"], "NO_FEASIBLE_CANDIDATE")
        self.assertEqual(report["qubo_terms"], [])
        with self.assertRaises(ValueError):
            evaluate_energy(report, [1])

    def test_rejects_invalid_band_and_negative_weights(self):
        rows = [candidate("A", 1.185, 0.001, 1.3, 0.02)]
        with self.assertRaises(ValueError):
            build_qubo(rows, 1.19, 1.18)
        with self.assertRaises(ValueError):
            build_qubo(rows, 1.18, 1.19, risk_weight=-1)


if __name__ == "__main__":
    unittest.main()
