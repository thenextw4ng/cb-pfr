import csv
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_c5g7_selection_input import GROUP_EDGES, prepare


class PrepareC5G7SelectionInputTests(unittest.TestCase):
    def _source(self, path: Path) -> None:
        fields = [
            "round", "candidate_id", "layout_signature", "seed", "keff_mean",
            "keff_std_dev", "fission_rate_peaking_factor", "statepoint_sha256",
            "mgxs_sha256", "group_structure_audit", "uncertainty_note",
        ]
        signatures = ["MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM"]
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for round_i, round_name in enumerate(("round_1", "round_2", "round_3")):
                for sig_i, sig in enumerate(signatures):
                    seed = 1000 * (round_i + 1) + sig_i
                    writer.writerow({
                        "round": round_name,
                        "candidate_id": f"c5g7-2x2-{sig}",
                        "layout_signature": sig,
                        "seed": seed,
                        "keff_mean": 1.18,
                        "keff_std_dev": 0.001,
                        "fission_rate_peaking_factor": 1.5,
                        "statepoint_sha256": f"{seed:064x}",
                        "mgxs_sha256": "a" * 64,
                        "group_structure_audit": "PASS",
                        "uncertainty_note": "smoke",
                    })

    def test_enriches_exactly_18_corrected_group_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, output = root / "source.csv", root / "enriched.csv"
            self._source(source)
            report = prepare(source, output)
            self.assertEqual(report["status"], "INPUT_INTEGRITY_PASS_SMOKE_EVIDENCE_ONLY")
            with output.open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 18)
            self.assertEqual(rows[0]["mgxs_energy_group_boundaries_eV"], GROUP_EDGES)
            self.assertEqual(rows[0]["batches"], "100")
            self.assertEqual(rows[0]["particles_per_batch"], "1000")
            self.assertEqual(report["physical_validation_claim"], "NOT_ESTABLISHED")

    def test_rejects_missing_layout_replicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, output = root / "source.csv", root / "enriched.csv"
            self._source(source)
            lines = source.read_text().splitlines()
            source.write_text("\n".join(lines[:-1]) + "\n")
            with self.assertRaisesRegex(ValueError, "exactly 18"):
                prepare(source, output)


if __name__ == "__main__":
    unittest.main()
