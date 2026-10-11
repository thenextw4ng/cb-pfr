import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class C5G7ObjectiveProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads((ROOT / "config/benchmarks/c5g7_objective_protocol.json").read_text())

    def test_not_official_acceptance(self):
        self.assertFalse(self.protocol["is_official_oecd_acceptance"])

    def test_legacy_burnup_mapping_remains_blocked(self):
        mapping = self.protocol["legacy_burnup_qubo_mapping"]
        self.assertEqual(mapping["status"], "NO_DEFENSIBLE_MAPPING_FOUND")
        self.assertTrue(mapping["required_evidence_before_mapping"])
        self.assertIn("Do not map", mapping["prohibition"])

    def test_six_layout_objective_is_explicit_but_not_finally_approved(self):
        study = self.protocol["tracks"]["six_layout_design_study"]
        objective = study["decision_objective_template"]
        self.assertEqual(objective["direction"], "minimize")
        self.assertIn("F_fission", objective["formula"])
        self.assertIn("NOT_YET_APPROVED", objective["objective_status"])
        self.assertIn("BLOCKED", study["uncertainty_and_ranking"]["current_status"])

    def test_canonical_screen_requires_physical_review(self):
        screen = self.protocol["tracks"]["canonical_benchmark_verification"]
        gates = screen["project_screening_gates"]
        self.assertTrue(gates["model_identity_review_required"])
        self.assertTrue(gates["spatial_reference_comparison_required"])
        self.assertFalse(self.protocol["is_official_oecd_acceptance"])


if __name__ == "__main__":
    unittest.main()
