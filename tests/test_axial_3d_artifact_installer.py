from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from tools import install_axial_3d_artifact as installer


ARCHIVE_SHA = "7a5e2a3daf87d0141ddc5e0922b88c4c0e2c3cb91af67ca6a2f50b6535e9862b"


def make_npz_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in (
            "mean.npy", "standard_error.npy", "relative_error_percent.npy",
            "score_names.npy", "x_centers_cm.npy", "y_centers_cm.npy", "z_centers_cm.npy",
        ):
            archive.writestr(name, b"test-array-payload")
    return buffer.getvalue()


def make_artifact_zip():
    npz = make_npz_bytes()
    summary = {
        "schema_version": 1,
        "status": "3d_openmc_statepoint_mesh_exported",
        "statepoint": {
            "sha256": "b" * 64, "n_batches": 7000, "n_inactive": 500,
            "n_particles": 10000, "n_realizations": 6500, "seed": 640000,
        },
        "mesh": {
            "dimension_xyz": [51, 51, 30], "array_shape": [30, 51, 51, 3],
            "bin_count": 78030,
        },
        "scores": ["flux", "fission", "nu-fission"],
        "npz": {"bytes": len(npz), "sha256": hashlib.sha256(npz).hexdigest()},
    }
    audit = {
        "status": "generated_3d_inputs_passed_structural_audit",
        "candidate_id": "c5g7-2x2-UMMU",
    }
    manifest = {
        "candidate_id": "c5g7-2x2-UMMU",
        "layout_signature": "UMMU",
        "source": {"archive_sha256": ARCHIVE_SHA},
    }
    members = {
        "model/3d/axial-3d-export/axial_tally_3d.npz": npz,
        "model/3d/axial-3d-export/AXIAL_3D_STATEPOINT_SUMMARY.json": json.dumps(summary).encode(),
        "AXIAL_3D_INPUT_AUDIT.json": json.dumps(audit).encode(),
        "AXIAL_3D_INPUT_MANIFEST.json": json.dumps(manifest).encode(),
    }
    outer = io.BytesIO()
    with zipfile.ZipFile(outer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)
    return outer.getvalue(), npz


class AxialProductionArtifactInstallerTests(unittest.TestCase):
    def test_installs_only_hash_verified_ummu_production_fields(self):
        archive_bytes, npz_bytes = make_artifact_zip()
        artifact = {
            "artifact_id": 991,
            "artifact_name": installer.ARTIFACT_PREFIX + "test-run",
            "artifact_url": f"{installer.API_ROOT}/actions/artifacts/991/zip",
            "run_id": 234,
            "run_url": "https://github.com/thenextw4ng/cb-pfr/actions/runs/234",
            "created_at": "2026-10-13T12:33:20Z",
            "expires_at": "2026-10-27T12:33:20Z",
        }

        def fake_json(url):,            if url.endswith("/actions/artifacts/991"):,                return {,                    "id": 991, "name": artifact["artifact_name"], "expired": False,,                    "created_at": artifact["created_at"], "expires_at": artifact["expires_at"],,                    "workflow_run": {"id": 234, "html_url": artifact["run_url"]},,                },            raise AssertionError("Unexpected GitHub API URL: " + url),,        with tempfile.TemporaryDirectory() as tmp:,            target = Path(tmp) / "evidence" / "axial_tally_3d.npz",            with patch.object(installer, "KNOWN_PRODUCTION_ARTIFACT_ID", 991), patch.object(,                installer, "_get_json", side_effect=fake_json,            ), patch.object(installer, "_get_bytes", return_value=archive_bytes):
                result = installer.install_latest_production_axial_tally(target)

            self.assertEqual(target.read_bytes(), npz_bytes)
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), result["axial_tally_npz_sha256"])
            self.assertEqual(result["mesh_dimension_xyz"], [51, 51, 30])
            self.assertEqual(result["n_realizations"], 6500)
            self.assertTrue((target.parent / "AXIAL_3D_STATEPOINT_SUMMARY.json").is_file())
            self.assertTrue((target.parent / "AXIAL_3D_INPUT_AUDIT.json").is_file())
            self.assertTrue((target.parent / "AXIAL_3D_INPUT_MANIFEST.json").is_file())
            provenance = json.loads((target.parent / "AXIAL_3D_PROVENANCE.json").read_text())
            self.assertEqual(provenance["artifact_id"], 991)
            self.assertEqual(provenance["workflow_run_id"], 234)
            self.assertEqual(provenance["axial_tally_npz_sha256"], result["axial_tally_npz_sha256"])

    def test_rejects_smoke_budget_and_hash_mismatch(self):
        archive_bytes, _ = make_artifact_zip()
        members = installer._validated_members(archive_bytes, "test")
        summary = json.loads(members["AXIAL_3D_STATEPOINT_SUMMARY.json"])
        summary["statepoint"]["n_batches"] = 25
        members["AXIAL_3D_STATEPOINT_SUMMARY.json"] = json.dumps(summary).encode()
        with self.assertRaisesRegex(installer.AxialArtifactError, "high-budget production"):
            installer.validate_evidence_files(members)

        members = installer._validated_members(archive_bytes, "test")
        members["axial_tally_3d.npz"] += b"altered"
        with self.assertRaisesRegex(installer.AxialArtifactError, "byte count"):
            installer.validate_evidence_files(members)

    def test_rejects_wrong_candidate_and_missing_npz_arrays(self):
        archive_bytes, _ = make_artifact_zip()
        members = installer._validated_members(archive_bytes, "test")
        manifest = json.loads(members["AXIAL_3D_INPUT_MANIFEST.json"])
        manifest["layout_signature"] = "MUMU"
        members["AXIAL_3D_INPUT_MANIFEST.json"] = json.dumps(manifest).encode()
        with self.assertRaisesRegex(installer.AxialArtifactError, "canonical UMMU"):
            installer.validate_evidence_files(members)

        npz = io.BytesIO()
        with zipfile.ZipFile(npz, "w") as nested:
            nested.writestr("means.npy", b"wrong-name")
        summary = json.loads(members["AXIAL_3D_STATEPOINT_SUMMARY.json"])
        nested_bytes = npz.getvalue()
        summary["npz"] = {"bytes": len(nested_bytes), "sha256": hashlib.sha256(nested_bytes).hexdigest()}
        members["axial_tally_3d.npz"] = nested_bytes
        members["AXIAL_3D_STATEPOINT_SUMMARY.json"] = json.dumps(summary).encode()
        manifest["layout_signature"] = "UMMU"
        members["AXIAL_3D_INPUT_MANIFEST.json"] = json.dumps(manifest).encode()
        with self.assertRaisesRegex(installer.AxialArtifactError, "missing required arrays"):
            installer.validate_evidence_files(members)


if __name__ == "__main__":
    unittest.main()
