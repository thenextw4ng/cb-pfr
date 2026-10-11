import unittest
import numpy as np

from scripts.analyze_c5g7_assembly_fission import AssemblyTallyError, summarize_assembly_rates


class C5G7AssemblyFissionTests(unittest.TestCase):
    def test_uniform_mesh_gives_unit_peaking_factor(self):
        result = summarize_assembly_rates(np.ones((51, 51)), "UMMU")
        self.assertAlmostEqual(result["fission_rate_peaking_factor"], 1.0)
        self.assertEqual(set(result["assembly_integrated_fission_rate"]), {"p00", "p01", "p10", "p11"})
        self.assertEqual(result["uncertainty_status"], "not_propagated_for_correlated_mesh_bins; estimate across independent statepoints instead")

    def test_blocks_map_to_four_distinct_fuel_assemblies(self):
        mesh = np.zeros((51, 51))
        mesh[0:17, 34:51] = 1.0
        mesh[17:34, 34:51] = 2.0
        mesh[0:17, 17:34] = 3.0
        mesh[17:34, 17:34] = 4.0
        result = summarize_assembly_rates(mesh, "UMMU")
        rates = result["assembly_integrated_fission_rate"]
        self.assertEqual(rates, {"p00": 289.0, "p01": 578.0, "p10": 867.0, "p11": 1156.0})
        self.assertAlmostEqual(result["fission_rate_peaking_factor"], 4.0 / 2.5)

    def test_rejects_invalid_layout_signature(self):
        with self.assertRaises(AssemblyTallyError):
            summarize_assembly_rates(np.ones((51, 51)), "UUUU")

    def test_rejects_wrong_mesh_shape(self):
        with self.assertRaises(AssemblyTallyError):
            summarize_assembly_rates(np.ones((50, 51)), "UMMU")


if __name__ == "__main__":
    unittest.main()
