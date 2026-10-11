import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.export_c5g7_run_level_evidence import (
    EXPECTED,
    GROUP_EDGES,
    export_run_level_evidence,
)


class ExportC5G7RunLevelEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.studies = []
        signatures = sorted(EXPECTED)
        for round_index, seed_base in enumerate((620000, 630000, 640000)):
            study_root = self.root / f"round-{round_index}"
            study_root.mkdir()
            cases = []
            for candidate_index, signature in enumerate(signatures):
                candidate_id = f"c5g7-2x2-{signature}"
                case_dir = study_root / candidate_id
                (case_dir / "model" / "2d").mkdir(parents=True)
                statepoint = case_dir / "model" / "2d" / "statepoint.100.h5"
                statepoint.write_bytes(f"statepoint-{round_index}-{signature}".encode())
                mgxs = case_dir / "model" / "2d" / "mgxs.h5"
                mgxs.write_bytes(b"shared-standard-c5g7-mgxs")
                statepoint_rel = "model/2d/statepoint.100.h5"
                mgxs_rel = "model/2d/mgxs.h5"
                statepoint_hash = hashlib.sha256(statepoint.read_bytes()).hexdigest()
                mgxs_hash = hashlib.sha256(mgxs.read_bytes()).hexdigest()
                keff = 1.18 + candidate_index * 0.001
                keff_sd = 0.002
                cases.append({
                    "candidate_id": candidate_id,
                    "seed": seed_base + candidate_index,
                    "layout": {
                        f"p{row}{col}": ("MOX" if signature[row * 2 + col] == "M" else "UO2")
                        for row in range(2) for col in range(2)
                    },
                    "status": "completed",
                    "output_hashes_after_run": {
                        statepoint_rel: statepoint_hash,
                        mgxs_rel: mgxs_hash,
                    },
                    "physical_results": {
                        "status": "completed",
                        "statepoint": statepoint_rel,
                        "keff_mean": keff,
                        "keff_std_dev": keff_sd,
                        "mgxs_group_structure_audit": "PASS",
                        "mgxs_energy_group_boundaries": list(GROUP_EDGES),
                        "mgxs_sha256_before_transport": mgxs_hash,
                        "mgxs_sha256_after_transport": mgxs_hash,
                    },
                })
            summary = {
                "study_id": "C5G7-2x2-two-UO2-two-MOX-layout-enumeration",
                "status": "all_runs_completed_needs_independent_validation",
                "mode": "run",
                "upstream_commit": "ba41bee54320ada0b4ac39a0dd2ca3c1d090a450",
                "settings": {
                    "batches": 100, "inactive": 10, "particles": 1000, "threads": 1,
                    "seed_base": seed_base, "seed_policy": "test fixture",
                },
                "cases": cases,
            }
            summary_path = study_root / "STUDY_SUMMARY.json"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            self.studies.append(summary_path)

    def fake_analyzer(self, statepoint, candidate_id, signature):
        index = sorted(EXPECTED).index(signature)
        return {
            "keff_mean": 1.18 + index * 0.001,
            "keff_std_dev": 0.002,
            "fission_rate_peaking_factor": 1.2 + index * 0.01,
        }

    def test_exports_only_complete_audited_runs_and_hashes_outputs(self):
        out_csv = self.root / "export" / "run_level_results.csv"
        audit_json = self.root / "export" / "audit.json"
        audit = export_run_level_evidence(
            self.studies,
            output_csv=out_csv,
            audit_json=audit_json,
            analyzer=self.fake_analyzer,
        )
        self.assertEqual(audit["status"], "RUN_EVIDENCE_EXPORTED_INTEGRITY_PASS_PHYSICAL_VALIDATION_NOT_CERTIFIED")
        self.assertEqual(audit["run_count"], 18)
        self.assertEqual(audit["replicates_per_layout"], {signature: 3 for signature in EXPECTED})
        self.assertEqual(len(audit["output_csv_sha256"]), 64)
        self.assertIn("mgxs_energy_group_boundaries_eV", out_csv.read_text(encoding="utf-8").splitlines()[0])
        self.assertFalse(audit["physical_validation_certified"])

    def test_rejects_fewer_than_three_studies(self):
        with self.assertRaisesRegex(ValueError, "at least three"):
            export_run_level_evidence(
                self.studies[:2],
                output_csv=self.root / "out.csv",
                audit_json=self.root / "audit.json",
                analyzer=self.fake_analyzer,
            )

    def test_rejects_nonstandard_group_boundaries(self):
        summary = json.loads(self.studies[0].read_text(encoding="utf-8"))
        summary["cases"][0]["physical_results"]["mgxs_energy_group_boundaries"] = [1.0, 2.0]
        self.studies[0].write_text(json.dumps(summary), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "nonstandard C5G7 group boundaries"):
            export_run_level_evidence(
                self.studies,
                output_csv=self.root / "out.csv",
                audit_json=self.root / "audit.json",
                analyzer=self.fake_analyzer,
            )


if __name__ == "__main__":
    unittest.main()
