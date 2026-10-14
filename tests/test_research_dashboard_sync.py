"""Runtime contract tests for the Research Dossier candidate-data binding."""
import csv
import math
import statistics
import unittest
from pathlib import Path

import web_server


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "results/c5g7_corrected_group_repeatability_smoke_2026-10-11/fission_objective_repeatability_summary.csv"
RUNS = ROOT / "results/c5g7_corrected_group_repeatability_smoke_2026-10-11/run_level_fission_objective.csv"


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


class ResearchDashboardSyncTests(unittest.TestCase):
    def test_candidate_api_uses_the_dossier_campaign_and_crosschecks_run_level_records(self):
        payload = web_server.read_candidate_evidence()
        metadata, records = payload["metadata"], payload["records"]
        source_rows, run_rows = read_rows(SUMMARY), read_rows(RUNS)

        self.assertEqual(metadata["source"], str(SUMMARY.relative_to(ROOT)))
        self.assertEqual(metadata["run_level_source"], str(RUNS.relative_to(ROOT)))
        self.assertEqual(metadata["campaign_status"], "EXPLORATORY_DESCRIPTIVE_ONLY")
        self.assertEqual(metadata["run_count"], 18)
        self.assertEqual(metadata["layout_count"], 6)
        self.assertEqual(metadata["runs_per_layout"], 3)
        self.assertTrue(metadata["records_validated_against_run_level_data"])
        self.assertTrue(metadata["no_winner_claim"])
        self.assertIn("BLOCKED_NO_DESIGN_SPECIFIC_KEFF_BAND", metadata["acceptance_status"])

        self.assertEqual(len(records), 6)
        self.assertEqual(len(run_rows), 18)
        self.assertEqual({row["layout_signature"] for row in records}, {row["layout_signature"] for row in source_rows})
        self.assertEqual({row["candidate_id"] for row in records}, {row["candidate_id"] for row in source_rows})
        self.assertEqual([row["descriptive_fission_peaking_rank"] for row in records], [1, 2, 3, 4, 5, 6])

        for displayed in records:
            signature = displayed["layout_signature"]
            source = next(row for row in source_rows if row["layout_signature"] == signature)
            linked_runs = [row for row in run_rows if row["layout_signature"] == signature]
            self.assertEqual(displayed["candidate_id"], "c5g7-2x2-" + signature)
            self.assertEqual(displayed["n_runs"], 3)
            self.assertEqual(displayed["group_structure_audit_count"], 3)
            self.assertEqual(displayed["statepoint_hash_count"], 3)
            self.assertEqual(displayed["mgxs_sha256"], metadata["corrected_mgxs_sha256"])
            self.assertEqual(displayed["seed"], " / ".join(row["seed"] for row in linked_runs))
            self.assertTrue(math.isclose(displayed["keff_mean"], float(source["mean_keff"]), rel_tol=1e-12))
            self.assertTrue(math.isclose(displayed["keff_std_dev"], float(source["between_seed_sd_keff"]), rel_tol=1e-12))
            self.assertTrue(math.isclose(displayed["fission_peaking_mean"], float(source["mean_fission_rate_peaking_factor"]), rel_tol=1e-12))
            self.assertTrue(math.isclose(displayed["fission_peaking_sd"], float(source["between_seed_sd_fission_peaking_factor"]), rel_tol=1e-12))

    def test_dashboard_does_not_relabel_the_independent_assembly_proxy_as_paired_candidate_data(self):
        candidate_runs = read_rows(RUNS)
        with web_server.ASSEMBLY_CSV.open("r", encoding="utf-8-sig", newline="") as stream:
            proxy_rows = list(csv.DictReader(stream))
        candidate_seeds = {row["seed"] for row in candidate_runs}
        proxy_seeds = {row["seed"] for row in proxy_rows}
        self.assertTrue(candidate_seeds.isdisjoint(proxy_seeds))
        proxy_payload = web_server.read_assembly_evidence()
        self.assertIn("exploratory smoke evidence", proxy_payload["status_scope"])
        self.assertIn("not absolute power", proxy_payload["status_scope"].lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
