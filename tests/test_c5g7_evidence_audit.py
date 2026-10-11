import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from itertools import combinations

from scripts.audit_c5g7_evidence import audit_study, expected_lattice


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class C5G7EvidenceAuditTests(unittest.TestCase):
    def make_fixture(self, root: Path):
        positions = ("p00", "p01", "p10", "p11")
        candidates = []
        for mox in combinations(positions, 2):
            layout = {p: ("MOX" if p in mox else "UO2") for p in positions}
            signature = "".join("M" if layout[p] == "MOX" else "U" for p in positions)
            candidates.append({
                "candidate_id": f"c5g7-2x2-{signature}",
                "fuel_assembly_layout": layout,
                "is_canonical_reference_arrangement": layout == {
                    "p00": "UO2", "p01": "MOX", "p10": "MOX", "p11": "UO2"
                },
            })
        design = {
            "design_study_id": "C5G7-2x2-two-UO2-two-MOX-layout-enumeration",
            "fixed_reflector_positions": ["p02", "p12", "p20", "p21", "p22"],
            "constraints": {"reflector_positions_fixed": True},
            "candidate_layouts": candidates,
        }
        design_path = root / "design.json"
        design_path.write_text(json.dumps(design), encoding="utf-8")
        cases = []
        raw_candidates = []
        for index, candidate in enumerate(candidates):
            cid = candidate["candidate_id"]
            case_dir = root / cid
            model_dir = case_dir / "model" / "2d"
            model_dir.mkdir(parents=True)
            (case_dir / "build.log").write_text("builder success\n", encoding="utf-8")
            (case_dir / "openmc.log").write_text("transport success\n", encoding="utf-8")
            (model_dir / "settings.xml").write_text(
                f"<settings><run_mode>eigenvalue</run_mode><energy_mode>multi-group</energy_mode>"
                f"<batches>100</batches><inactive>10</inactive><particles>1000</particles>"
                f"<seed>{620000 + index}</seed></settings>", encoding="utf-8")
            (model_dir / "materials.xml").write_text("<materials/>\n", encoding="utf-8")
            (model_dir / "geometry.xml").write_text("<geometry/>\n", encoding="utf-8")
            (model_dir / "mgxs.h5").write_bytes(b"shared mgxs placeholder")
            (model_dir / "build-xml-2d.py").write_text(
                expected_lattice(candidate["fuel_assembly_layout"]) + "\n", encoding="utf-8")
            statepoint_rel = "model/2d/statepoint.100.h5"
            statepoint = case_dir / statepoint_rel
            statepoint.write_bytes(f"statepoint {index}\n".encode())
            all_files = [p for p in case_dir.rglob("*") if p.is_file()]
            hashes = {str(p.relative_to(case_dir)): digest(p) for p in all_files}
            physical = {
                "status": "completed", "statepoint": statepoint_rel,
                "keff_mean": 1.1 + index * 0.001, "keff_std_dev": 0.0001,
                "commands": [{"returncode": 0}, {"returncode": 0}],
            }
            case = {
                "candidate_id": cid, "seed": 620000 + index,
                "layout": candidate["fuel_assembly_layout"], "status": "completed",
                "physical_results": physical, "output_hashes_after_run": hashes,
            }
            (case_dir / "CASE_RESULT.json").write_text(json.dumps(case), encoding="utf-8")
            cases.append(case)
            raw_candidates.append({"candidate_id": cid, "status": "PASS",
                                   "statepoint_sha256": digest(statepoint)})
        study = {
            "mode": "run", "status": "all_runs_completed_needs_independent_validation",
            "design_space_sha256": digest(design_path),
            "settings": {"batches": 100, "inactive": 10, "particles": 1000},
            "cases": cases,
        }
        study_path = root / "STUDY_SUMMARY.json"
        study_path.write_text(json.dumps(study), encoding="utf-8")
        raw_path = root / "raw_audit.json"
        raw_path.write_text(json.dumps({"status": "PASS", "candidates": raw_candidates}), encoding="utf-8")
        return study_path, design_path, raw_path, cases

    def test_valid_completed_study_passes_integrity_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            study, design, raw, _ = self.make_fixture(Path(temp))
            report = audit_study(study, design, raw)
            self.assertEqual(report["status"], "PASS", report["failed_checks"])
            self.assertEqual(report["candidate_count"], 6)

    def test_tampered_statepoint_fails_manifest_hash_check(self):
        with tempfile.TemporaryDirectory() as temp:
            study, design, raw, cases = self.make_fixture(Path(temp))
            statepoint = Path(temp) / cases[0]["candidate_id"] / cases[0]["physical_results"]["statepoint"]
            statepoint.write_bytes(b"tampered")
            report = audit_study(study, design, raw)
            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(any("manifest_hash_matches:model/2d/statepoint.100.h5" in x
                                for x in report["failed_checks"]))

    def test_reflector_contract_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            study, design, raw, _ = self.make_fixture(Path(temp))
            data = json.loads(design.read_text())
            data["fixed_reflector_positions"][-1] = "p23"
            design.write_text(json.dumps(data))
            report = audit_study(study, design, raw)
            self.assertEqual(report["status"], "FAIL")
            self.assertIn("design_contract_valid", report["failed_checks"])


if __name__ == "__main__":
    unittest.main()
