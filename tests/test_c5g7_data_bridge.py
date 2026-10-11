import csv
import tempfile
import unittest
from pathlib import Path

from cbpfr.c5g7_data_bridge import (
    EXPECTED_CANDIDATES, ExternalDataError, assess_cbpfr_limits,
    build_one_hot_selection_qubo, coverage_report, load_external_results,
)


def write_csv(path: Path, candidate_ids):
    fields = [
        "candidate_id", "benchmark_case", "source_url", "source_kind",
        "keff_mean", "keff_uncertainty", "keff_uncertainty_kind",
        "fission_rate_peaking_factor", "fission_rate_peaking_uncertainty",
        "configuration_hash", "notes",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, candidate_id in enumerate(candidate_ids):
            writer.writerow({
                "candidate_id": candidate_id, "benchmark_case": "C5G7-2D-2x2-explicit-layout",
                "source_url": "https://example.org/paper-or-data", "source_kind": "published_reference",
                "keff_mean": 1.0 + index / 1000, "keff_uncertainty": 0.0001,
                "keff_uncertainty_kind": "reported Monte Carlo standard deviation",
                "fission_rate_peaking_factor": 1.2 + index / 100,
                "fission_rate_peaking_uncertainty": 0.01,
            })


class TestC5G7DataBridge(unittest.TestCase):
    def test_partial_data_is_not_ranked(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.csv"
            write_csv(path, EXPECTED_CANDIDATES[:1])
            rows = load_external_results(path)
            report = coverage_report(rows)
            self.assertEqual(report["status"], "incomplete_external_coverage")
            self.assertFalse(report["physical_ranking_allowed"])
            with self.assertRaises(ExternalDataError):
                build_one_hot_selection_qubo(rows, objective_column="keff_mean")

    def test_complete_data_builds_separate_qubo(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.csv"
            write_csv(path, EXPECTED_CANDIDATES)
            rows = load_external_results(path)
            model = build_one_hot_selection_qubo(rows, objective_column="fission_rate_peaking_factor", direction="min")
            self.assertTrue(model["not_the_legacy_usmanov_burnup_qubo"])
            self.assertEqual(len(model["candidate_ids"]), 6)
            self.assertEqual(model["minimum_energy_candidate_id"], EXPECTED_CANDIDATES[0])

    def test_limits_are_explicit_and_missing_values_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.csv"
            write_csv(path, EXPECTED_CANDIDATES)
            rows = load_external_results(path)
            limits = [{
                "name": "keff", "value_attribute": "keff_mean",
                "uncertainty_attribute": "keff_uncertainty",
                "lower": 0.99, "upper": 1.01, "z": 2, "scale": 0.01,
            }]
            assessed = assess_cbpfr_limits(rows, limits)
            self.assertEqual(len(assessed), 6)
            self.assertTrue(all(item.feasible_under_declared_limits for item in assessed))
            self.assertTrue(all(not item.missing_metrics for item in assessed))

    def test_duplicate_candidate_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.csv"
            write_csv(path, [EXPECTED_CANDIDATES[0], EXPECTED_CANDIDATES[0]])
            with self.assertRaises(ExternalDataError):
                load_external_results(path)


if __name__ == "__main__":
    unittest.main()
