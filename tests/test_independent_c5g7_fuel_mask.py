import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "compare_c5g7_independent_crosscheck.py"
spec = importlib.util.spec_from_file_location("independent_c5g7_crosscheck", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class IndependentC5G7FuelMaskTests(unittest.TestCase):
    def test_csv_distinguishes_1060_fuel_pins_from_96_zero_nonfuel_bins(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "c5g7_pinpower.csv"
            positive = 0
            with path.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["pc", "pr", "norm_power"])
                w.writeheader()
                for y in range(18, 52):
                    for x in range(1, 35):
                        # 96 known non-fuel bins are zero; the rest are fuel.
                        value = 0.0 if positive >= 1060 else 0.5 + positive / 10000
                        if value > 0:
                            positive += 1
                        w.writerow({"pc": x, "pr": y, "norm_power": value})
            values, mask, summary = mod.sn_map(path)
            self.assertEqual(summary["mesh_bin_count"], 1156)
            self.assertEqual(summary["fuel_pin_count"], 1060)
            self.assertEqual(summary["non_fuel_bin_count"], 96)
            self.assertEqual(sum(sum(row) for row in mask), 1060)
            self.assertGreater(summary["min_normalized_fuel_pin_power"], 0.0)
            self.assertAlmostEqual(summary["max_normalized_fuel_pin_power"], 0.5 + 1059 / 10000)

    def test_spatial_metrics_ignore_nonfuel_zero_bins(self):
        import numpy as np
        mask = np.zeros((34, 34), dtype=bool)
        mask.flat[:1060] = True
        reference = np.zeros((34, 34), dtype=float)
        reference[mask] = np.linspace(0.4, 2.4, 1060)
        openmc = np.zeros((34, 34), dtype=float)
        openmc[mask] = reference[mask] * 1.02
        # Deliberately make non-fuel bins wildly different: they must be excluded.
        openmc[~mask] = 1e6
        metrics = mod.compare_spatial_maps([openmc.tolist()], reference.tolist(), mask.tolist())
        self.assertEqual(metrics["comparable_fuel_pin_count"], 1060)
        self.assertEqual(metrics["excluded_non_fuel_mesh_bins"], 96)
        self.assertAlmostEqual(metrics["rms_relative_error_percent"], 2.0, places=8)
        self.assertAlmostEqual(metrics["mean_absolute_relative_error_percent"], 2.0, places=8)
        self.assertAlmostEqual(metrics["max_absolute_relative_error_percent"], 2.0, places=8)

    def test_spatial_metrics_reject_zero_on_matched_fuel_mask(self):
        import numpy as np
        mask = np.zeros((34, 34), dtype=bool)
        mask.flat[:1060] = True
        reference = np.ones((34, 34), dtype=float)
        reference[0, 0] = 0.0
        with self.assertRaisesRegex(ValueError, "finite and positive"):
            mod.compare_spatial_maps([np.ones((34, 34)).tolist()], reference.tolist(), mask.tolist())

    def test_openmc_mesh_extraction_preserves_shared_x_y_coordinate_order(self):
        import h5py
        import numpy as np
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "synthetic-statepoint.h5"
            # Deliberately asymmetric mesh values expose transpose/reflection errors.
            raw = np.fromfunction(lambda x, y: 1000.0 * y + x + 1.0, (51, 51), dtype=float)
            mask = np.zeros((34, 34), dtype=bool)
            mask.flat[:1060] = True
            fuel_values = raw[0:34, 17:51].T[mask]
            expected_mean = float(fuel_values.mean())
            with h5py.File(path, "w") as handle:
                meshes = handle.create_group("tallies/meshes")
                mesh = meshes.create_group("mesh 1")
                mesh.create_dataset("dimension", data=np.array([51, 51, 1], dtype=np.int32))
                tally = handle.create_group("tallies/tally 1")
                tally.create_dataset("score_bins", data=np.array([b"fission"]))
                tally.create_dataset("results", data=raw.flatten(order="F")[:, None, None])
            got = np.asarray(mod.openmc_map(path, mask), dtype=float)
            self.assertEqual(got.shape, (34, 34))
            # Row 0 maps y-bin 18; row 33 maps y-bin 51. Columns map x-bins 1..34.
            self.assertAlmostEqual(got[0, 0], raw[0, 17] / expected_mean, places=10)
            self.assertAlmostEqual(got[0, 33], raw[33, 17] / expected_mean, places=10)
            self.assertAlmostEqual(got[33, 0], raw[0, 50] / expected_mean, places=10)
            self.assertAlmostEqual(got[33, 33], raw[33, 50] / expected_mean, places=10)

    def test_duplicate_pin_coordinates_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "duplicate.csv"
            with path.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["pc", "pr", "norm_power"])
                w.writeheader()
                w.writerow({"pc": 1, "pr": 18, "norm_power": 1.0})
                w.writerow({"pc": 1, "pr": 18, "norm_power": 1.0})
            with self.assertRaisesRegex(ValueError, "duplicate S_N pin coordinate"):
                mod.sn_map(path)


if __name__ == "__main__":
    unittest.main()
