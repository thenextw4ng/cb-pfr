import copy
import unittest

from cbpfr.benchmark import audit_benchmark_manifest


def blocked_manifest():
    import json
    from pathlib import Path
    return json.loads((Path(__file__).resolve().parents[1] / "config/benchmarks/c5g7_manifest.json").read_text(encoding="utf-8"))


class BenchmarkManifestTests(unittest.TestCase):
    def test_c5g7_manifest_is_sourced_but_mapping_gate_stays_blocked(self):
        report = audit_benchmark_manifest(blocked_manifest())
        self.assertEqual(report["benchmark_id"], "OECD-NEA-C5G7")
        self.assertEqual(report["status"], "blocked")
        self.assertGreaterEqual(report["primary_source_count"], 2)
        self.assertTrue(any("required_state_to_material_map" in item for item in report["blockers"]))
        self.assertTrue(any("openmc_baseline_run_verified" in item for item in report["blockers"]))

    def test_missing_source_citation_fails_schema_validation(self):
        manifest = blocked_manifest()
        manifest["primary_sources"] = []
        with self.assertRaisesRegex(ValueError, "primary_sources"):
            audit_benchmark_manifest(manifest)

    def test_no_single_boolean_can_override_missing_mapping_evidence(self):
        manifest = blocked_manifest()
        manifest["implementation_status"].update({
            "model_inputs_bundled": True,
            "cross_sections_bundled": True,
            "reference_values_transcribed_and_reviewed": True,
            "openmc_baseline_run_verified": True,
            "candidate_mapping_status": "validated",
        })
        report = audit_benchmark_manifest(manifest)
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(any("required_state_to_material_map" in item for item in report["blockers"]))

    def test_complete_structural_manifest_can_pass_gate(self):
        manifest = blocked_manifest()
        manifest["implementation_status"].update({
            "model_inputs_bundled": True,
            "cross_sections_bundled": True,
            "reference_values_transcribed_and_reviewed": True,
            "openmc_baseline_run_verified": True,
            "candidate_mapping_status": "validated",
        })
        manifest["declared_scope"]["boundary_conditions"] = "documented case-specific boundary conditions"
        manifest["declared_scope"]["material_compositions"] = "exact primary-specification compositions with provenance"
        manifest["mapping_contract"].update({
            "required_position_map": {"p0": "documented benchmark position"},
            "required_state_to_material_map": {"state-A": "material-ID-1"},
            "required_material_compositions_source": "primary benchmark source section/table",
            "required_cross_section_provenance": "library/version/checksum/source",
            "required_reference_comparison_protocol": "predeclared metrics and tolerances",
        })
        self.assertEqual(audit_benchmark_manifest(manifest)["status"], "ready_for_baseline_run")

    def test_invalid_source_url_rejected(self):
        manifest = blocked_manifest()
        manifest["primary_sources"][0]["url"] = "http://example.com"
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            audit_benchmark_manifest(manifest)


if __name__ == "__main__":
    unittest.main()
