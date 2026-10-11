import unittest
from itertools import product

from cbpfr.c5g7_design_qubo import (
    C5G7DesignError,
    assignment_from_vector,
    enumerate_feasible_assignments,
    qubo_energy,
    upper_triangular_qubo,
    vector_from_assignment,
)


class C5G7DesignQuboTests(unittest.TestCase):
    def test_exactly_six_feasible_assignments(self):
        layouts = enumerate_feasible_assignments()
        self.assertEqual(len(layouts), 6)
        self.assertEqual(len({tuple(x.values()) for x in layouts}), 6)
        for layout in layouts:
            self.assertEqual(sum(v == "MOX" for v in layout.values()), 2)
            self.assertEqual(vector_from_assignment(layout).count(1), 2)

    def test_penalty_is_zero_only_for_two_mox(self):
        for vector in product((0, 1), repeat=4):
            expected = (sum(vector) - 2) ** 2
            self.assertEqual(qubo_energy(vector), expected)
            if sum(vector) == 2:
                self.assertEqual(qubo_energy(vector), 0.0)
            else:
                self.assertGreater(qubo_energy(vector), 0.0)

    def test_matrix_expansion_matches_direct_penalty(self):
        q = upper_triangular_qubo()
        for vector in product((0, 1), repeat=4):
            expanded = 4.0 + sum(q[i][i] * vector[i] for i in range(4))
            expanded += sum(q[i][j] * vector[i] * vector[j]
                            for i in range(4) for j in range(i + 1, 4))
            self.assertEqual(expanded, qubo_energy(vector))

    def test_decoder_rejects_wrong_cardinality(self):
        with self.assertRaises(C5G7DesignError):
            assignment_from_vector((1, 1, 1, 0))

    def test_decoder_rejects_nonbinary(self):
        with self.assertRaises(C5G7DesignError):
            assignment_from_vector((1, 1, 0, 2))

    def test_assignment_roundtrip(self):
        for layout in enumerate_feasible_assignments():
            self.assertEqual(assignment_from_vector(vector_from_assignment(layout)), layout)


if __name__ == "__main__":
    unittest.main()
