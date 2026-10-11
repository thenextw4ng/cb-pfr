import unittest

from scripts.audit_c5g7_mapping_contract import audit_manifest, REQUIRED_FIELDS


class C5G7MappingContractTests(unittest.TestCase):
    def test_current_manifest_fails_closed(self):
        manifest = {"mapping_contract": {field: None for field in REQUIRED_FIELDS}}
        result = audit_manifest(manifest)
        self.assertEqual(result["status"], "NO_DEFENSIBLE_MAPPING_FOUND")
        self.assertEqual(set(result["missing_fields"]), set(REQUIRED_FIELDS))
        self.assertFalse(result["can_claim_physical_mapping"])

    def test_complete_fields_still_do_not_auto_certify_mapping(self):
        contract = {field: {"source": f"traceable-source-{i}"} for i, field in enumerate(REQUIRED_FIELDS)}
        result = audit_manifest({"mapping_contract": contract})
        self.assertEqual(result["status"], "MAPPING_METADATA_PRESENT_PENDING_INDEPENDENT_REVIEW")
        self.assertFalse(result["can_claim_physical_mapping"])

    def test_review_record_does_not_auto_certify_physical_truth(self):
        contract = {field: {"source": f"traceable-source-{i}"} for i, field in enumerate(REQUIRED_FIELDS)}
        contract["independent_review"] = {
            "approved": True,
            "reviewer": "independent reviewer",
            "review_date": "2026-10-11",
            "evidence_manifest_sha256": "a" * 64,
        }
        result = audit_manifest({"mapping_contract": contract})
        self.assertEqual(result["status"], "MAPPING_REVIEW_RECORD_PRESENT_REQUIRES_SCIENTIFIC_REVIEW")
        self.assertFalse(result["can_claim_physical_mapping"])


if __name__ == "__main__":
    unittest.main()
