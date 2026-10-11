import unittest

from scripts.audit_c5g7_spatial_mapping import expected_lattice, parse_lattice_rows


class C5G7SpatialMappingTests(unittest.TestCase):
    def test_canonical_layout_matches_top_down_core_lattice(self):
        layout = {"p00": "UO2", "p01": "MOX", "p10": "MOX", "p11": "UO2"}
        text = "lattices['Core'].universes = [[u, m, w], [m, u, w], [w, w, w]]"
        self.assertEqual(parse_lattice_rows(text), expected_lattice(layout))

    def test_row_column_orientation_is_explicit(self):
        layout = {"p00": "MOX", "p01": "MOX", "p10": "UO2", "p11": "UO2"}
        self.assertEqual(
            expected_lattice(layout),
            [["m", "m", "w"], ["u", "u", "w"], ["w", "w", "w"]],
        )

    def test_rejects_invalid_material_count(self):
        with self.assertRaises(ValueError):
            expected_lattice({"p00": "UO2", "p01": "UO2", "p10": "UO2", "p11": "MOX"})

    def test_rejects_unrecognized_lattice_assignment(self):
        with self.assertRaises(ValueError):
            parse_lattice_rows("lattices['Core'].universes = [[u, m], [m, u]]")


if __name__ == "__main__":
    unittest.main()
