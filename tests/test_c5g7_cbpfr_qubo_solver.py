import unittest

from scripts.solve_c5g7_cbpfr_qubo import exact_selector_reference, solve_report


def _valid_report():
    ids = [
        "c5g7-2x2-MMUU", "c5g7-2x2-MUMU", "c5g7-2x2-MUUM",
        "c5g7-2x2-UMMU", "c5g7-2x2-UMUM", "c5g7-2x2-UUMM",
    ]
    scores = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    feasible = [True, True, False, True, False, True]
    penalty = 2.0
    matrix = [[0.0] * 6 for _ in range(6)]
    for i in range(6):
        matrix[i][i] = scores[i] + (0.0 if feasible[i] else penalty) - penalty
        for j in range(i + 1, 6):
            matrix[i][j] = 2.0 * penalty
    reference = exact_selector_reference(matrix, penalty, ids)
    return {
        "winner_selected": True,
        "selected_candidate_id": reference["candidate_id"],
        "candidates": [
            {"candidate_id": candidate_id, "conservatively_feasible": feasible[i]}
            for i, candidate_id in enumerate(ids)
        ],
        "qubo": {
            "variable_order": ids,
            "matrix_upper_triangular": matrix,
            "offset": penalty,
        },
    }


class C5G7SelectorSolverTests(unittest.TestCase):
    def test_exact_backend_reproduces_unique_one_hot_reference(self):
        report = _valid_report()
        result = solve_report(report, backend="exact")
        self.assertEqual(result["status"], "EXACT_REFERENCE_PASS")
        self.assertEqual(result["sampled_candidate_id"], report["selected_candidate_id"])
        self.assertTrue(result["one_hot_valid"])
        self.assertTrue(result["candidate_passed_cbpfr_screen"])
        self.assertEqual(result["exact_reference"]["states_enumerated"], 64)

    def test_refuses_selection_report_without_accepted_winner(self):
        report = _valid_report()
        report["winner_selected"] = False
        with self.assertRaisesRegex(ValueError, "no accepted CB-PFR selection QUBO"):
            solve_report(report, backend="exact")

    def test_rejects_report_if_claimed_winner_disagrees_with_qubo(self):
        report = _valid_report()
        report["selected_candidate_id"] = "c5g7-2x2-UUMM"
        with self.assertRaisesRegex(ValueError, "does not match exact QUBO minimizer"):
            solve_report(report, backend="exact")


if __name__ == "__main__":
    unittest.main()
