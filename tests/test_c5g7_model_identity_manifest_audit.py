"""Tests for fail-closed C5G7 input provenance auditing."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_c5g7_model_identity_manifest.py"
SPEC = importlib.util.spec_from_file_location("audit_c5g7_model_identity_manifest", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ModelIdentityManifestAuditTests(unittest.TestCase):
    def _fixture(self, root: Path, signed=False):
        paths = {}
        hashes = {}
        for key, filename in (
            ("geometry_xml", "geometry.xml"),
            ("materials_xml", "materials.xml"),
            ("settings_xml", "settings.xml"),
            ("mgxs_hdf5", "mgxs.h5"),
            ("source_builder", "build.py"),
        ):
            path = root / filename
            path.write_text(f"fixture content: {key}\n", encoding="utf-8")
            paths[key] = path
            hash_key = {
                "geometry_xml": "geometry_xml_sha256",
                "materials_xml": "materials_xml_sha256",
                "settings_xml": "settings_xml_sha256",
                "mgxs_hdf5": "mgxs_hdf5_sha256",
                "source_builder": "source_builder_sha256",
            }[key]
            hashes[hash_key] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest = {
            "schema_version": "1.0",
            "manifest_id": "test-manifest",
            "model": {
                "upstream_commit_expected": "ba41bee54320ada0b4ac39a0dd2ca3c1d090a450",
                "energy_group_boundaries_eV_expected": MODULE.EXPECTED_GROUPS,
            },
            "generated_inputs": hashes,
            "review": {
                "reviewer": "Independent reviewer" if signed else None,
                "review_date": "2026-10-12" if signed else None,
                "primary_specification_reference": "benchmark section X" if signed else None,
                "independent_signoff": signed,
            },
        }
        manifest_path = root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest_path, paths

    def test_matching_hashes_remain_review_pending_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest, paths = self._fixture(Path(tmp))
            result = MODULE.audit_manifest(manifest, paths)
        self.assertEqual(result["status"], "INPUT_PROVENANCE_PASS_REVIEW_PENDING")
        self.assertFalse(result["physical_fidelity_certified"])
        self.assertFalse(result["independent_signoff_recorded"])

    def test_hash_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest, paths = self._fixture(root)
            paths["geometry_xml"].write_text("changed after manifest", encoding="utf-8")
            result = MODULE.audit_manifest(manifest, paths)
        self.assertEqual(result["status"], "FAIL_INPUT_PROVENANCE")
        self.assertTrue(any("geometry_xml SHA-256" in error for error in result["errors"]))

    def test_missing_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest, paths = self._fixture(Path(tmp))
            paths["settings_xml"] = Path(tmp) / "missing-settings.xml"
            result = MODULE.audit_manifest(manifest, paths)
        self.assertEqual(result["status"], "FAIL_INPUT_PROVENANCE")

    def test_signoff_never_certifies_physical_fidelity(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest, paths = self._fixture(Path(tmp), signed=True)
            result = MODULE.audit_manifest(manifest, paths)
        self.assertEqual(
            result["status"],
            "INPUT_PROVENANCE_PASS_REVIEW_RECORDED_PHYSICS_FIDELITY_NOT_CERTIFIED",
        )
        self.assertTrue(result["independent_signoff_recorded"])
        self.assertFalse(result["physical_fidelity_certified"])


if __name__ == "__main__":
    unittest.main()
