"""Regression tests for the published C5G7 spatial-shape audit."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_c5g7_spatial_reference.py"
SPEC = importlib.util.spec_from_file_location("audit_c5g7_spatial_reference", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def payload(rates=None):
    return {
        "candidate_id": "c5g7-2x2-UMMU",
        "layout_signature": "UMMU",
        "score": "fission",
        "positions_order": ["p00", "p01", "p10", "p11"],
        "material_by_position": {"p00": "UO2", "p01": "MOX", "p10": "MOX", "p11": "UO2"},
        "mesh_dimension": [51, 51, 1],
        "assembly_integrated_fission_rate": rates or {"p00": 492.8, "p01": 211.7, "p10": 211.7, "p11": 139.8},
    }


class SpatialReferenceAuditTests(unittest.TestCase):
    def test_reference_proportions_pass_independent_of_absolute_scale(self):
        reference_rates = payload()["assembly_integrated_fission_rate"]
        scaled_rates = {key: value * 3.7 for key, value in reference_rates.items()}
        result = MODULE.audit_spatial_reference([payload(), payload(scaled_rates), payload()])
        self.assertEqual(result["status"], "NORMALIZED_SPATIAL_SHAPE_SCREEN_PASS")
        self.assertAlmostEqual(result["maximum_absolute_relative_difference_percent"], 0.0, places=10)

    def test_fails_when_a_position_exceeds_published_reference_uncertainty(self):
        altered = {key: value for key, value in payload()["assembly_integrated_fission_rate"].items()}
        altered["p11"] *= 1.01
        result = MODULE.audit_spatial_reference([payload(altered), payload(altered), payload(altered)])
        self.assertEqual(result["status"], "NORMALIZED_SPATIAL_SHAPE_SCREEN_FAIL")
        self.assertGreater(result["maximum_absolute_relative_difference_percent"], 0.20)

    def test_rejects_wrong_candidate_wrong_mapping_or_nonpositive_rates(self):
        bad = payload()
        bad["candidate_id"] = "c5g7-2x2-MUMU"
        with self.assertRaises(MODULE.SpatialReferenceAuditError):
            MODULE.audit_spatial_reference([bad, payload(), payload()])
        bad = payload()
        bad["material_by_position"] = {"p00": "MOX", "p01": "MOX", "p10": "MOX", "p11": "UO2"}
        with self.assertRaises(MODULE.SpatialReferenceAuditError):
            MODULE.audit_spatial_reference([bad, payload(), payload()])
        bad = payload()
        bad["assembly_integrated_fission_rate"]["p11"] = 0.0
        with self.assertRaises(MODULE.SpatialReferenceAuditError):
            MODULE.audit_spatial_reference([bad, payload(), payload()])

    def test_requires_three_runs(self):
        with self.assertRaises(MODULE.SpatialReferenceAuditError):
            MODULE.audit_spatial_reference([payload(), payload()])


if __name__ == "__main__":
    unittest.main()
