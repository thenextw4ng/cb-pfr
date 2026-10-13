"""Synthetic contract tests for the C5G7 mesh-to-assembly tally reducer.

These tests verify array indexing and arithmetic. They do NOT independently
validate the physical orientation of the generated OpenMC geometry; that
requires a source-model/geometry review and compatible benchmark data.
"""
import importlib.util
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_c5g7_assembly_fission.py"
SPEC = importlib.util.spec_from_file_location("analyze_c5g7_assembly_fission", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class AssemblyFissionMappingTests(unittest.TestCase):
    def _mesh_with_block_values(self):
        mesh = np.zeros((51, 51), dtype=float)
        # Blocks match the script's declared (x, y) slices. Distinct constants
        # make accidental block swaps visible in the resulting integrated rates.
        mesh[0:17, 34:51] = 1.0    # p00
        mesh[17:34, 34:51] = 2.0   # p01
        mesh[0:17, 17:34] = 3.0    # p10
        mesh[17:34, 17:34] = 4.0   # p11
        return mesh

    def test_block_mapping_and_integrated_rates_are_explicit(self):
        result = MODULE.summarize_assembly_rates(self._mesh_with_block_values(), "UMMU")
        expected = {"p00": 289.0, "p01": 578.0, "p10": 867.0, "p11": 1156.0}
        self.assertEqual(result["assembly_integrated_fission_rate"], expected)
        self.assertEqual(result["positions_order"], ["p00", "p01", "p10", "p11"])
        self.assertAlmostEqual(result["fission_rate_peaking_factor"], 4.0 / 2.5)

    def test_reflector_and_nonfuel_bins_do_not_enter_four_fuel_sums(self):
        mesh = self._mesh_with_block_values()
        before = MODULE.summarize_assembly_rates(mesh, "UMMU")
        # Add large values only outside the four fuel blocks. If slices are
        # accidentally widened, the integrated assembly rates will change.
        mask = np.ones((51, 51), dtype=bool)
        mask[0:34, 34:51] = False
        mask[0:34, 17:34] = False
        mesh[mask] = 1.0e6
        after = MODULE.summarize_assembly_rates(mesh, "UMMU")
        self.assertEqual(before["assembly_integrated_fission_rate"],
                         after["assembly_integrated_fission_rate"])

    def test_layout_materials_follow_declared_position_order(self):
        result = MODULE.summarize_assembly_rates(self._mesh_with_block_values(), "UMMU")
        self.assertEqual(result["material_by_position"], {
            "p00": "UO2", "p01": "MOX", "p10": "MOX", "p11": "UO2"
        })

    def test_rejects_bad_shape_nonfinite_negative_and_wrong_material_count(self):
        with self.assertRaises(MODULE.AssemblyTallyError):
            MODULE.summarize_assembly_rates(np.zeros((50, 51)), "UMMU")
        bad = self._mesh_with_block_values()
        bad[0, 0] = np.nan
        with self.assertRaises(MODULE.AssemblyTallyError):
            MODULE.summarize_assembly_rates(bad, "UMMU")
        bad = self._mesh_with_block_values()
        bad[0, 0] = -1.0
        with self.assertRaises(MODULE.AssemblyTallyError):
            MODULE.summarize_assembly_rates(bad, "UMMU")
        with self.assertRaises(MODULE.AssemblyTallyError):
            MODULE.summarize_assembly_rates(self._mesh_with_block_values(), "MMMM")

    def test_rejects_empty_or_zero_fuel_block(self):
        mesh = self._mesh_with_block_values()
        mesh[17:34, 17:34] = 0.0
        with self.assertRaises(MODULE.AssemblyTallyError):
            MODULE.summarize_assembly_rates(mesh, "UMMU")


if __name__ == "__main__":
    unittest.main()
