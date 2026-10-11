import unittest
from scripts.audit_c5g7_validation_gates import audit_rows, PRODUCTION_MGXS_SHA256


def row(cid, sig, seed, keff=1.18655, sd=0.00001):
    return {
        "candidate_id": cid, "layout_signature": sig, "_seed": seed,
        "_batches": 2000, "_inactive": 100, "_particles": 5000,
        "_keff": keff, "_sd": sd, "seed": str(seed),
        "statepoint_sha256": f"statepoint-{seed}", "settings_sha256": "same-settings",
        "mgxs_sha256": PRODUCTION_MGXS_SHA256, "raw_hdf5_audit": "PASS"
    }


class C5G7ValidationGateTests(unittest.TestCase):
    def test_scalar_screen_cannot_pass_while_model_identity_blocked(self):
        rows = []
        for sig, offset in (("UMMU", 0.0), ("MMUU", 0.0001)):
            for seed in range(3):
                rows.append(row(f"candidate-{sig}", sig, seed + (0 if sig == "UMMU" else 10),
                                1.18655 + offset + seed * 1e-7))
        result = audit_rows(rows)
        self.assertEqual(result["status"], "BLOCKED_MODEL_IDENTITY_REVIEW")
        self.assertFalse(result["is_official_benchmark_acceptance"])
        noncanonical = next(c for c in result["candidates"] if c["layout_signature"] == "MMUU")
        self.assertIsNone(noncanonical["keff_reference_screen_pass"])
        self.assertEqual(noncanonical["noncanonical_reference_comparison"], "descriptive_only")

    def test_inconsistent_settings_fail_closed(self):
        rows = [row("canonical", "UMMU", seed) for seed in range(3)]
        rows[2]["_particles"] = 10000
        result = audit_rows(rows)
        self.assertEqual(result["status"], "FAIL_DATA_INTEGRITY_OR_COMMON_SETTINGS")

    def test_duplicate_statepoint_hash_fails_global_integrity(self):
        rows = [row("canonical", "UMMU", seed) for seed in range(3)]
        rows[2]["statepoint_sha256"] = rows[0]["statepoint_sha256"]
        result = audit_rows(rows)
        self.assertEqual(result["status"], "FAIL_DATA_INTEGRITY_OR_COMMON_SETTINGS")

    def test_wrong_mgxs_hash_fails_global_integrity(self):
        rows = [row("canonical", "UMMU", seed) for seed in range(3)]
        rows[1]["mgxs_sha256"] = "not-production-mgxs"
        result = audit_rows(rows)
        self.assertEqual(result["status"], "FAIL_DATA_INTEGRITY_OR_COMMON_SETTINGS")
        self.assertFalse(result["global_checks"]["mgxs_byte_identical_to_production"])

    def test_review_flags_do_not_override_failed_scalar_screen(self):
        rows = [row("canonical", "UMMU", seed, keff=1.19, sd=0.0002) for seed in range(3)]
        result = audit_rows(rows, model_identity_reviewed=True, tally_reference_reviewed=True)
        self.assertEqual(result["status"], "FAIL_OR_INCOMPLETE_CANONICAL_KEFF_SCREEN")


if __name__ == "__main__":
    unittest.main()
