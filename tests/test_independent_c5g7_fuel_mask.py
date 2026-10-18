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


def write_synthetic_pinpower(path: Path, duplicate_first: bool = False):
    fields = ["pc", "pr", "assembly", "local_row", "local_col", "norm_power"]
    coords = [(x, y) for y in range(18, 52) for x in range(1, 35)]
    if duplicate_first:
        coords[-1] = coords[-2]
    guide_zero_count = 0
    fuel_i = 0
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for x, y in coords:
            lr, lc = (y - 1) % 17 + 1, (x - 1) % 17 + 1
            instrument = (lr == 9 and lc == 9)
            if instrument:
                value = 1e-5
            elif guide_zero_count < 96:
                value = 0.0
                guide_zero_count += 1
            else:
                value = 0.5 + fuel_i / 10000
                fuel_i += 1
            # Match the independent solver's 3x3 assm_map at the 2x2 fuel block.
            ai, aj = (x - 1) // 17 + 1, (y - 1) // 17 + 1
            assembly = {(1, 3): 1, (2, 3): 2, (1, 2): 3, (2, 2): 4}.get((ai, aj), 0)
            w.writerow({"pc": x, "pr": y, "assembly": assembly,
                        "local_row": lr, "local_col": lc, "norm_power": value})


class IndependentC5G7FuelMaskTests(unittest.TestCase):
    def test_csv_separates_1056_true_fuel_pins_four_instrument_tubes_and_96_guide_bins(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "c5g7_pinpower.csv"
            write_synthetic_pinpower(path)
            values, mask, summary = mod.sn_map(path)
            self.assertEqual(summary["mesh_bin_count"], 1156)
            self.assertEqual(summary["fuel_pin_count"], 1056)
            self.assertEqual(summary["instrument_tube_count"], 4)
            self.assertEqual(summary["zero_power_guide_tube_count"], 96)
            self.assertEqual(summary["excluded_non_fuel_bin_count"], 100)
            self.assertEqual(sum(sum(row) for row in mask), 1056)
            self.assertGreater(summary["min_normalized_fuel_pin_power"], 0.0)
            expected_max = (0.5 + 1055 / 10000) / ((0.5 + (0.5 + 1055 / 10000)) / 2)
            self.assertAlmostEqual(summary["max_normalized_fuel_pin_power"], expected_max, places=10)
            self.assertTrue(summary["solver_csv_normalization_included_instrument_tubes"])
            # Each of the four central instrument positions is excluded even though it has tiny positive fission.
            for y in (26, 43):
                for x in (9, 26):
                    self.assertFalse(mask[y - 18][x - 1])
            self.assertEqual(sum(1 for row in mask for v in row if v), 1056)

    def test_spatial_metrics_ignore_guide_and_instrument_bins(self):
        import numpy as np
        mask = np.zeros((34, 34), dtype=bool)
        # Keep four central instrument positions excluded, and exactly 1056 true fuel pins.
        mask.flat[:1056] = True
        for y in (8, 25):
            for x in (8, 25):
                mask[y, x] = False
        # Fill additional true fuel cells to exactly 1056 after center exclusions.
        if mask.sum() < 1056:
            for idx in range(mask.size):
                y, x = divmod(idx, 34)
                if (y, x) not in {(8,8),(8,25),(25,8),(25,25)} and not mask[y,x]:
                    mask[y,x] = True
                    if mask.sum() == 1056:
                        break
        self.assertEqual(int(mask.sum()), 1056)
        reference = np.zeros((34, 34), dtype=float)
        reference[mask] = np.linspace(0.4, 2.4, 1056)
        openmc = np.zeros((34, 34), dtype=float)
        openmc[mask] = reference[mask] * 1.02
        openmc[~mask] = 1e6
        metrics = mod.compare_spatial_maps([openmc.tolist()], reference.tolist(), mask.tolist())
        self.assertEqual(metrics["comparable_fuel_pin_count"], 1056)
        self.assertEqual(metrics["excluded_non_fuel_mesh_bins"], 100)
        self.assertAlmostEqual(metrics["rms_relative_error_percent"], 2.0, places=8)
        self.assertAlmostEqual(metrics["mean_absolute_relative_error_percent"], 2.0, places=8)
        self.assertAlmostEqual(metrics["max_absolute_relative_error_percent"], 2.0, places=8)

    def test_spatial_metrics_reject_zero_on_matched_fuel_mask(self):
        import numpy as np
        mask = np.zeros((34, 34), dtype=bool)
        mask.flat[:1056] = True
        reference = np.ones((34, 34), dtype=float)
        reference[0, 0] = 0.0
        with self.assertRaisesRegex(ValueError, "finite and positive"):
            mod.compare_spatial_maps([np.ones((34, 34)).tolist()], reference.tolist(), mask.tolist())

    def test_openmc_mesh_extraction_preserves_shared_x_y_coordinate_order(self):
        import h5py
        import numpy as np
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "synthetic-statepoint.h5"
            raw = np.fromfunction(lambda x, y: 1000.0 * y + x + 1.0, (51, 51), dtype=float)
            mask = np.ones((34, 34), dtype=bool)
            for y in (8, 25):
                for x in (8, 25):
                    mask[y, x] = False
            # Leave 96 guide bins outside the central four instrument cells.
            zeros_needed = 96
            for idx in range(mask.size):
                y, x = divmod(idx, 34)
                if (y, x) in {(8,8),(8,25),(25,8),(25,25)}:
                    continue
                if zeros_needed:
                    mask[y, x] = False
                    zeros_needed -= 1
            self.assertEqual(int(mask.sum()), 1056)
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
            self.assertAlmostEqual(got[0, 0], raw[0, 17] / expected_mean, places=10)
            self.assertAlmostEqual(got[0, 33], raw[33, 17] / expected_mean, places=10)
            self.assertAlmostEqual(got[33, 0], raw[0, 50] / expected_mean, places=10)
            self.assertAlmostEqual(got[33, 33], raw[33, 50] / expected_mean, places=10)

    def test_duplicate_pin_coordinates_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "duplicate.csv"
            write_synthetic_pinpower(path, duplicate_first=True)
            with self.assertRaisesRegex(ValueError, "duplicate S_N pin coordinate"):
                mod.sn_map(path)


if __name__ == "__main__":
    unittest.main()
