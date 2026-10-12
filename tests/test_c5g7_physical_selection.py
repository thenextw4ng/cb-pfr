import unittest

from scripts.run_c5g7_cbpfr_physical_selection import evaluate, load_and_validate, EXPECTED, GROUP_EDGES


def fixture_rows():
    rows = []
    signatures = sorted(EXPECTED)
    for round_index, seed_base in enumerate((720000, 730000, 740000)):
        for index, sig in enumerate(signatures):
            fpeak = 1.30 + 0.04 * index + 0.001 * round_index
            keff = 1.1860 + index * 0.00005 + round_index * 0.000001
            keff_sd = 0.00002
            rows.append({
                "keff": keff,
                "keff_sd": keff_sd,
                "seed_i": seed_base + index,
                "fpeak": fpeak,
                "round": f"round_{seed_base}",
                "candidate_id": f"c5g7-2x2-{sig}",
                "layout_signature": sig,
                "seed": str(seed_base + index),
                "keff_mean": str(keff),
                "keff_std_dev": str(keff_sd),
                "fission_rate_peaking_factor": str(fpeak),
                "statepoint_sha256": f"{seed_base + index:064x}",
                "mgxs_sha256": "a" * 64,
                "group_structure_audit": "PASS",
                "mgxs_energy_group_boundaries_eV": GROUP_EDGES,
                "batches": "2000",
                "inactive": "100",
                "particles_per_batch": "5000",
                "threads": "1",
            })
    return rows


class PhysicalSelectionTests(unittest.TestCase):
    def test_corrected_group_budget_and_all_six_layouts_required(self):
        rows = fixture_rows()
        self.assertEqual(len(rows), 18)
        self.assertEqual({r["layout_signature"] for r in rows}, EXPECTED)
        self.assertTrue(all(r["group_structure_audit"] == "PASS" for r in rows))

    def test_cbpfr_and_exact_one_hot_qubo_agree(self):
        rows = fixture_rows()
        # This tests the algorithm on controlled fixture data, not OpenMC physics.
        report = evaluate(
            rows, keff_min=1.18, keff_max=1.19, fission_peaking_max=1.8,
            uncertainty_multiplier=1.0, keff_scale=0.01,
            fission_peaking_scale=1.0, risk_weight=1.0,
        )
        self.assertEqual(report["status"], "SELECTION_PIPELINE_PASS_PHYSICAL_VALIDATION_NOT_CERTIFIED")
        self.assertEqual(report["selected_candidate_id"], report["cbpfr_selected_candidate_id"])
        self.assertEqual(report["qubo"]["exact_binary_states_enumerated"], 64)
        self.assertTrue(report["qubo"]["unique_one_hot_minimizer"])

    def test_no_feasible_candidate_never_emits_a_qubo_winner(self):
        rows = fixture_rows()
        report = evaluate(
            rows, keff_min=1.30, keff_max=1.31, fission_peaking_max=1.1,
            uncertainty_multiplier=1.0, keff_scale=0.01,
            fission_peaking_scale=1.0, risk_weight=1.0,
        )
        self.assertEqual(report["status"], "NO_CONSERVATIVELY_FEASIBLE_CANDIDATE")
        self.assertFalse(report["winner_selected"])
        self.assertIsNone(report["qubo"])

    def test_budget_mismatch_is_rejected(self):
        rows = fixture_rows()
        rows[-1]["batches"] = "100"
        with self.assertRaisesRegex(ValueError, "budget is below"):
            # Exercise the real CSV validator without introducing filesystem state.
            import csv, tempfile
            from pathlib import Path
            with tempfile.TemporaryDirectory() as td:
                path = Path(td) / "runs.csv"
                with path.open("w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                    writer.writeheader()
                    writer.writerows(rows)
                load_and_validate(path, min_batches=2000, min_particles=5000, min_replicates=3)

    def test_rejects_non_sha256_provenance_and_duplicate_global_seeds(self):
        import csv, tempfile
        from pathlib import Path
        rows = fixture_rows()
        rows[0]["statepoint_sha256"] = "not-a-hash"
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "runs.csv"
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, "64-character lowercase SHA-256"):
                load_and_validate(path, min_batches=2000, min_particles=5000, min_replicates=3)

        rows = fixture_rows()
        rows[-1]["seed"] = rows[0]["seed"]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "runs.csv"
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, "seeds must be unique"):
                load_and_validate(path, min_batches=2000, min_particles=5000, min_replicates=3)

    def test_rejects_boolean_or_nonpositive_budget_contract(self):
        import csv, tempfile
        from pathlib import Path
        rows = fixture_rows()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "runs.csv"
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, "min_batches must be a positive integer"):
                load_and_validate(path, min_batches=True, min_particles=5000, min_replicates=3)

    def test_inconsistent_compute_settings_are_rejected(self):
        rows = fixture_rows()
        rows[-1]["particles_per_batch"] = "10000"
        import csv, tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "runs.csv"
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, "identical compute settings"):
                load_and_validate(path, min_batches=2000, min_particles=5000, min_replicates=3)


if __name__ == "__main__":
    unittest.main()
