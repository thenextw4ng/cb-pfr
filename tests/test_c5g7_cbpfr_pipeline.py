import csv
import tempfile
import unittest
from pathlib import Path

from scripts.run_c5g7_cbpfr_pipeline import run_integrated_pipeline


LAYOUTS = ("MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM")
GROUP_EDGES = "1e-05;0.0635;10.0;100.0;1000.0;500000.0;1000000.0;20000000.0"
FIELDS = [
    "round", "candidate_id", "layout_signature", "seed", "keff_mean",
    "keff_std_dev", "fission_rate_peaking_factor", "statepoint_sha256",
    "mgxs_sha256", "group_structure_audit", "mgxs_energy_group_boundaries_eV",
    "batches", "inactive", "particles_per_batch", "threads",
]


class IntegratedC5G7PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.csv_path = Path(self.temp.name) / "runs.csv"
        with self.csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            row_index = 0
            for layout_index, signature in enumerate(LAYOUTS):
                for replicate in range(3):
                    row_index += 1
                    writer.writerow({
                        "round": replicate + 1,
                        "candidate_id": f"c5g7-2x2-{signature}",
                        "layout_signature": signature,
                        "seed": 620000 + row_index,
                        "keff_mean": 1.18 + layout_index * 0.0002 + replicate * 0.00001,
                        "keff_std_dev": 0.001,
                        "fission_rate_peaking_factor": 1.20 + layout_index * 0.01 + replicate * 0.001,
                        "statepoint_sha256": f"{row_index:064x}",
                        "mgxs_sha256": "a" * 64,
                        "group_structure_audit": "PASS",
                        "mgxs_energy_group_boundaries_eV": GROUP_EDGES,
                        "batches": 2000,
                        "inactive": 100,
                        "particles_per_batch": 5000,
                        "threads": 1,
                    })

    def _run(self, **overrides):
        params = dict(
            backend="exact",
            num_reads=100,
            keff_min=1.0,
            keff_max=1.3,
            fission_peaking_max=2.0,
            uncertainty_multiplier=1.0,
            keff_scale=0.1,
            fission_peaking_scale=1.0,
            risk_weight=1.0,
            min_batches=2000,
            min_particles=5000,
            min_replicates=3,
        )
        params.update(overrides)
        return run_integrated_pipeline(self.csv_path, **params)

    def test_completed_evidence_runs_through_cbpfr_and_selector_qubo(self):
        result = self._run()
        self.assertEqual(result["schema_version"], "cbpfr.c5g7-integrated-pipeline.v1")
        self.assertEqual(result["status"], "PIPELINE_COMPLETE_SELECTION_REPRODUCED")
        self.assertEqual(result["input"]["run_count"], 18)
        self.assertEqual(len(result["candidates"]), 6)
        self.assertTrue(result["decision"]["accepted"])
        self.assertEqual(
            result["decision"]["candidate_id"],
            result["decision"]["cbpfr_reference_candidate_id"],
        )
        self.assertEqual(result["solver_run"]["solver_class"], "classical_exact")
        self.assertFalse(result["workflow"]["openmc_transport_launched_by_this_command"])
        self.assertFalse(result["decision"]["physical_validation_certified"])
        self.assertEqual(len(result["bundle_sha256"]), 64)

    def test_no_conservatively_feasible_candidate_fails_closed(self):
        result = self._run(keff_min=1.25, keff_max=1.30)
        self.assertEqual(result["status"], "BLOCKED_NO_CONSERVATIVELY_FEASIBLE_CANDIDATE")
        self.assertIsNone(result["solver_run"])
        self.assertFalse(result["decision"]["accepted"])
        self.assertIsNone(result["decision"]["candidate_id"])

    def test_incorrect_group_structure_is_rejected_before_selection(self):
        text = self.csv_path.read_text(encoding="utf-8")
        self.csv_path.write_text(text.replace(GROUP_EDGES, "0.00001;1;2;3;4;5;6;7", 1), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "group structure audit failed"):
            self._run()


if __name__ == "__main__":
    unittest.main()
