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
        (d / "layout_metadata.json").write_text(json.dumps({
            "layout_signature": "MMUU",
            "upstream_commit": mod.COMMIT,
            "settings": {"cells_per_pin": 16},
            "patched_source_sha256": "a" * 64,
            "compile_flags": "-O3"
        }))
        (d / "sn_solver.log").write_text(
            "C5G7  k_eff  (this solver) =   1.141478\n"
            "Pin power:  fuel pins= 1060  max= 2.0000  min= 0.0000\n"
        )
        path = d / "c5g7_pinpower.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["pc", "pr", "assembly", "norm_power"])
            w.writeheader()
            coords = [(x, y) for y in range(18, 52) for x in range(1, 35)]
            if duplicate_last:
                coords[-1] = coords[-2]
            for idx, (x, y) in enumerate(coords):
                power = 0.0 if idx < 96 else 0.5 + (idx - 96) * (1.5 / 1059)
                assembly = (idx % 4) + 1
                w.writerow({"pc": x, "pr": y, "assembly": assembly, "norm_power": power})
        return d

    def test_positive_fuel_minimum_comes_from_csv_not_console_zero(self):
        with tempfile.TemporaryDirectory() as td:
            d = self.make_bundle(Path(td))
            result = mod.parse_sig_dir(d)
            self.assertEqual(result["status"], "PASS_RUN_ARTIFACTS", result["issues"])
            self.assertEqual(result["mesh_block_bins"], 1156)
            self.assertEqual(result["positive_fuel_pin_bins"], 1060)
            self.assertEqual(result["zero_nonfuel_bins_excluded_from_positive_min"], 96)
            self.assertAlmostEqual(result["min_positive_normalized_pin_power_csv"], 0.5)
            self.assertAlmostEqual(result["max_positive_normalized_pin_power_csv"], 2.0)
            self.assertEqual(result["solver_log_min_over_all_reported_bins"], 0.0)
            self.assertGreater(result["min_positive_normalized_pin_power_csv"], 0.0)

    def test_duplicate_coordinates_are_rejected_and_record_does_not_pass(self):
        with tempfile.TemporaryDirectory() as td:
            d = self.make_bundle(Path(td), duplicate_last=True)
            result = mod.parse_sig_dir(d)
            self.assertEqual(result["status"], "INCOMPLETE_OR_REVIEW")
            self.assertTrue(any("duplicate pin-power coordinate" in issue for issue in result["issues"]))
            self.assertTrue(any("expected 1156 unique bins" in issue for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()
