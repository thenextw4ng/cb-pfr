import unittest
from pathlib import Path

from scripts.audit_paper_claims import build_report


class PaperClaimAuditTests(unittest.TestCase):
    def test_audit_preserves_scientific_blockers(self):
        root = Path(__file__).resolve().parents[1]
        report = build_report(root)
        self.assertEqual(report["audit_status"], "AUDIT_COMPLETE_WITH_OPEN_SCIENTIFIC_BLOCKERS")
        self.assertTrue(all(report["evidence_integrity_checks"].values()))
        claims = report["claims"]
        self.assertEqual(claims["repeated_quantum_annealing_frequency_and_hamming_analysis"]["status"], "NOT_RUN")
        self.assertEqual(claims["usmanov_burnup_state_to_c5g7_material_mapping"]["status"], "BLOCKED_NO_DEFENSIBLE_MAPPING_FOUND")
        self.assertEqual(claims["experimental_physical_validation"]["status"], "NOT_ESTABLISHED")
        self.assertEqual(claims["cbpfr_software_and_synthetic_benchmark"]["status"], "PASS_REPRODUCIBLE_AGGREGATE")
        self.assertEqual(claims["cbpfr_physical_validation"]["status"], "BLOCKED")

    def test_synthetic_results_are_never_labeled_physical(self):
        root = Path(__file__).resolve().parents[1]
        report = build_report(root)
        claim = report["claims"]["cbpfr_software_and_synthetic_benchmark"]
        self.assertEqual(claim["selected_true_feasibility_rates"]["cb_pfr"], 0.976)
        self.assertIn("not physical validation", claim["meaning"])


if __name__ == "__main__":
    unittest.main()
