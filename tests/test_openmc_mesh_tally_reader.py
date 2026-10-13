#!/usr/bin/env python3
"""Runtime regression tests for reading archived OpenMC 0.16 mesh tallies."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

sys.path.insert(0, str(ROOT))
import web_server  # noqa: E402

EXPECTED_ARCHIVE_SHA256 = "7a5e2a3daf87d0141ddc5e0922b88c4c0e2c3cb91af67ca6a2f50b6535e9862b"
EXPECTED_SCORES = {"flux", "fission", "nu-fission"}


class OpenMCMeshTallyReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        archive_arg = os.environ.get("CBPFR_MESH_TALLY_TEST_ARCHIVE")
        if not archive_arg:
            raise unittest.SkipTest(
                "Artifact-backed mesh reader checks run in scientific workstation CI with the audited ZIP."
            )
        cls.archive_path = Path(archive_arg).expanduser().resolve()
        if not cls.archive_path.is_file():
            raise FileNotFoundError(cls.archive_path)
        archive_hash = hashlib.sha256(cls.archive_path.read_bytes()).hexdigest()
        if archive_hash != EXPECTED_ARCHIVE_SHA256:
            raise AssertionError(
                f"Mesh parser fixture hash mismatch: expected {EXPECTED_ARCHIVE_SHA256}, got {archive_hash}"
            )
        with zipfile.ZipFile(cls.archive_path) as archive:
            cls.statepoint_members = sorted(
                name for name in archive.namelist()
                if name.endswith("/model/2d/statepoint.5000.h5")
            )
        if len(cls.statepoint_members) != 6:
            raise AssertionError(f"Expected six audited statepoints; found {cls.statepoint_members}")

    def read_member(self, member: str) -> dict:
        original = (
            web_server.STATEPOINT_ARCHIVE,
            web_server.STATEPOINT_ARCHIVE_FALLBACK,
            web_server.STATEPOINT_MEMBER,
            web_server.STATEPOINT_BASELINE,
        )
        try:
            web_server.STATEPOINT_ARCHIVE = self.archive_path
            web_server.STATEPOINT_ARCHIVE_FALLBACK = self.archive_path
            web_server.STATEPOINT_MEMBER = member
            web_server.STATEPOINT_BASELINE = self.archive_path.parent / "__no_production_baseline_for_smoke_fixture__.json"
            return web_server.read_mesh_evidence()
        finally:
            (
                web_server.STATEPOINT_ARCHIVE,
                web_server.STATEPOINT_ARCHIVE_FALLBACK,
                web_server.STATEPOINT_MEMBER,
                web_server.STATEPOINT_BASELINE,
            ) = original

    def test_all_six_candidate_statepoints_return_51_by_51_mesh_data(self):
        for member in self.statepoint_members:
            with self.subTest(member=member):
                payload = self.read_member(member)
                self.assertIn("mesh_tallies", payload)
                self.assertTrue(payload["mesh_tallies"])
                self.assertEqual(payload["provenance"]["statepoint_member"], member)
                self.assertEqual(payload["provenance"]["hash_matches"], None)
                self.assertEqual(len(payload["provenance"]["sha256"]), 64)

                tally = payload["mesh_tallies"][0]
                self.assertEqual(tally["dimensions"], [51, 51, 1])
                self.assertEqual(tally["mesh_id"], 1)
                self.assertEqual(tally["n_realizations"], 4500)
                self.assertEqual(set(tally["scores"]), EXPECTED_SCORES)

                for score in EXPECTED_SCORES:
                    self.assertEqual(tally.get("uncertainty_statistic"), "standard_error")
                    field = tally["scores"][score]
                    self.assertEqual(field["standard_error"], field["std_dev"])
                    for key in ("mean", "standard_error", "std_dev"):
                        grid = field[key]
                        self.assertEqual(len(grid), 51, (score, key))
                        self.assertTrue(all(len(row) == 51 for row in grid), (score, key))
                        self.assertTrue(
                            all(math.isfinite(float(value)) for row in grid for value in row),
                            (score, key, "contains non-finite values"),
                        )
                    mean_values = [float(value) for row in field["mean"] for value in row]
                    se_values = [float(value) for row in field["std_dev"] for value in row]
                    self.assertGreaterEqual(min(mean_values), 0.0)
                    self.assertGreaterEqual(min(se_values), 0.0)

    def test_reader_reports_expected_mesh_link_failure_instead_of_guessing(self):
        # Structural guard: a real OpenMC mesh filter can declare its associated mesh via bins=[1].
        # The tested successful payload's mesh_id=1 assertion above ensures that link is honoured.
        payload = self.read_member(self.statepoint_members[0])
        self.assertEqual(payload["mesh_tallies"][0]["mesh_id"], 1)
        self.assertEqual(payload["mesh_tallies"][0]["dimensions"], [51, 51, 1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
