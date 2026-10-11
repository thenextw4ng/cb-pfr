import csv
import tempfile
import unittest
from pathlib import Path
from scripts.audit_c5g7_corrected_objective import analyze

class CorrectedObjectiveAuditTests(unittest.TestCase):
    def test_committed_corrected_smoke_data_integrity_and_fail_closed_decision(self):
        path=Path("results/c5g7_corrected_group_repeatability_smoke_2026-10-11/run_level_fission_objective.csv")
        report=analyze(path)
        self.assertEqual(report["status"],"EVIDENCE_INTEGRITY_PASS_DESIGN_SELECTION_BLOCKED")
        self.assertEqual(report["run_count"],18)
        self.assertEqual(report["layout_count"],6)
        self.assertFalse(report["decision"]["winner_selected"])
        self.assertTrue(all(r["fission_peaking"]["ci95_low"] < r["fission_peaking"]["ci95_high"] for r in report["candidate_summaries"]))

    def test_duplicate_statepoint_is_not_silently_accepted(self):
        source=Path("results/c5g7_corrected_group_repeatability_smoke_2026-10-11/run_level_fission_objective.csv")
        with source.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f)); fields=rows[0].keys()
        rows[1]["statepoint_sha256"]=rows[0]["statepoint_sha256"]
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"runs.csv"; out=Path(td)/"out.json"
            with path.open("w",newline="",encoding="utf-8") as f:
                writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
            report=analyze(path)
            self.assertEqual(report["status"],"EVIDENCE_INCOMPLETE")
            self.assertFalse(report["checks"]["unique_statepoint_hashes"])

if __name__=="__main__": unittest.main()
