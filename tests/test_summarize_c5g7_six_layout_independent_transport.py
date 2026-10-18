import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "summarize_c5g7_six_layout_independent_transport.py"
spec = importlib.util.spec_from_file_location("summarize_c5g7_six_layout_independent_transport", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class SixLayoutTransportSummaryTests(unittest.TestCase):
    def make_bundle(self, root: Path, duplicate_last: bool = False) -> Path:
        d = root / "MMUU"
        d.mkdir()
        source = d / "patched_c5g7_transport.f90"
        source.write_text(
            "! Synthetic, test-only layout source for MMUU\n"
            "core(1,3) = 2\n"
            "core(2,3) = 2\n"
            "core(1,2) = 1\n"
            "core(2,2) = 1\n"
            "core(3,3) = 0\n"
            "core(3,2) = 0\n"
            "core(1,1) = 0\n"
            "core(2,1) = 0\n"
            "core(3,1) = 0\n"
            "tol = 1.0e-5_dp\n"
            "maxout = 800\n",
            encoding="utf-8"
        )
        (d / "layout_metadata.json").write_text(json.dumps({
            "layout_signature": "MMUU",
            "upstream_commit": mod.COMMIT,
            "settings": {
                "cells_per_pin": 16,
                "azimuthal_directions": 24,
                "polar_directions": 4,
                "inner_passes": 3,
                "openmp_threads": 4
            },
            "patched_source_sha256": mod.sha(source),
            "compile_flags": "-O3 -march=native -fopenmp -ffree-line-length-none"
        }))
        (d / "sn_solver.log").write_text(
            "outer   20   k =   1.141478   |dk| =  1.0E-06   |dFd| =  1.0E-06\n"
            "C5G7  k_eff  (this solver) =   1.141478\n"
            "Pin power:  fuel pins= 1060  max= 2.0000  min= 0.0000\n"
        )
        path = d / "c5g7_pinpower.csv"
        fields = ["pc", "pr", "assembly", "local_row", "local_col", "norm_power"]
        coords = [(x, y) for y in range(18, 52) for x in range(1, 35)]
        if duplicate_last:
            coords[-1] = coords[-2]
        guide_zero_count = 0
        fuel_i = 0
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for x, y in coords:
                lr, lc = (y - 1) % 17 + 1, (x - 1) % 17 + 1
                if lr == 9 and lc == 9:
                    power = 1e-5  # Central instrument tube: positive, but not fuel.
                elif guide_zero_count < 96:
                    power = 0.0
                    guide_zero_count += 1
                else:
                    power = 0.5 + fuel_i * (1.5 / 1055)
                    fuel_i += 1
                ai, aj = (x - 1) // 17 + 1, (y - 1) // 17 + 1
                assembly = {(1, 3): 1, (2, 3): 2, (1, 2): 3, (2, 2): 4}.get((ai, aj), 0)
                w.writerow({"pc": x, "pr": y, "assembly": assembly,
                            "local_row": lr, "local_col": lc, "norm_power": power})
        return d

    def test_fuel_extrema_exclude_four_instrument_tubes_and_renormalize_true_fuel(self):
        with tempfile.TemporaryDirectory() as td:
            d = self.make_bundle(Path(td))
            result = mod.parse_sig_dir(d)
            self.assertEqual(result["status"], "PASS_RUN_ARTIFACTS", result["issues"])
            self.assertEqual(result["mesh_block_bins"], 1156)
            self.assertEqual(result["true_fuel_pin_bins"], 1056)
            self.assertEqual(result["instrument_tube_bins"], 4)
            self.assertEqual(result["zero_power_guide_tube_bins"], 96)
            self.assertEqual(result["excluded_non_fuel_mesh_bins"], 100)
            self.assertAlmostEqual(result["raw_solver_csv_min_true_fuel_pin_power"], 0.5)
            self.assertAlmostEqual(result["raw_solver_csv_max_true_fuel_pin_power"], 2.0)
            self.assertAlmostEqual(result["min_normalized_fuel_pin_power"], 0.4)
            self.assertAlmostEqual(result["max_normalized_fuel_pin_power"], 1.6)
            self.assertAlmostEqual(result["solver_csv_true_fuel_mean_before_renormalization"], 1.25)
            self.assertEqual(result["solver_log_min_over_all_reported_bins"], 0.0)

    def test_duplicate_coordinates_are_rejected_and_record_does_not_pass(self):
        with tempfile.TemporaryDirectory() as td:
            d = self.make_bundle(Path(td), duplicate_last=True)
            result = mod.parse_sig_dir(d)
            self.assertEqual(result["status"], "INCOMPLETE_OR_REVIEW")
            self.assertTrue(any("duplicate pin-power coordinate" in issue for issue in result["issues"]))
            self.assertTrue(any("expected 1156 unique bins" in issue for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()
