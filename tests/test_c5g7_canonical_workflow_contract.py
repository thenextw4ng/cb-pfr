"""Regression tests for the canonical C5G7 GitHub Actions workflow contract."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "c5g7-canonical-convergence.yml"


class CanonicalWorkflowContractTests(unittest.TestCase):
    def test_inactive_batch_input_and_environment_fallback_agree(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('inactive:\n        description: "Inactive batches per run"\n        required: true\n        default: "500"', text)
        self.assertIn("INACTIVE: ${{ inputs.inactive || '500' }}", text)
        self.assertNotIn("INACTIVE: ${{ inputs.inactive || '100' }}", text)

    def test_source_diagnostics_are_generated_before_aggregation(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        diagnostics = text.index("scripts/audit_c5g7_source_convergence.py")
        aggregator = text.index("scripts/analyze_c5g7_canonical_convergence.py")
        self.assertLess(diagnostics, aggregator)
        spatial = text.index("scripts/audit_c5g7_spatial_reference.py")
        self.assertLess(spatial, aggregator)

    def test_transport_and_analysis_artifacts_are_preserved_even_on_failure(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("if: always()", text)
        self.assertIn("name: seed_${{ matrix.seed_base }}", text)
        self.assertIn("path: ${{ runner.temp }}/c5g7-canonical-convergence/seed_", text)
        self.assertIn("name: c5g7-canonical-confirmation-aggregate", text)
        self.assertIn("pattern: seed_*", text)
        self.assertIn("Validate run settings against the predeclared profile", text)

    def test_recovery_workflow_installs_openmc_and_activates_environment(self):
        recovery = ROOT / ".github" / "workflows" / "c5g7-canonical-recover-analysis.yml"
        text = recovery.read_text(encoding="utf-8")
        self.assertIn("openmc=0.16.0", text)
        self.assertIn("python=3.12", text)
        self.assertIn("shell: bash -el {0}", text)
        self.assertIn("actions/download-artifact@v4", text)
        self.assertIn("scripts/audit_c5g7_source_convergence.py", text)
        self.assertIn("scripts/analyze_c5g7_canonical_convergence.py", text)


if __name__ == "__main__":
    unittest.main()
