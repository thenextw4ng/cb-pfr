#!/usr/bin/env python3
"""Unit tests for the archive preparation and 3-D tally evidence contract."""
from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.prepare_c5g7_axial_3d import prepare_candidate
from scripts.audit_c5g7_axial_3d import audit_inputs, export_statepoint
import web_server


BUILDER = """import openmc
import sys
sys.path.append('../')
from lattices import lattices, universes, cells
from surfaces import surfaces
from tally import tallies, mesh
from materials import materials
batches = 20000
inactive = 500
particles = 10000
settings_file = openmc.Settings()
settings_file.particles = particles
"""
GEOMETRY_XML = """<?xml version="1.0"?>
<geometry>
  <surface id="18" type="z-plane" boundary="reflective" coeffs="-107.1" name="Big Core z-min"/>
  <surface id="19" type="z-plane" boundary="vacuum" coeffs="107.1" name="Big Core z-max"/>
  <cell id="20" name="Core" fill="201"/>
  <lattice id="101" name="UO2 Unrodded Assembly"><dimension>17 17</dimension><pitch>1.26 1.26</pitch><lower_left>-10.71 -10.71</lower_left><universes>1</universes></lattice>
  <lattice id="103" name="MOX Unrodded Assembly"><dimension>17 17</dimension><pitch>1.26 1.26</pitch><lower_left>-10.71 -10.71</lower_left><universes>2</universes></lattice>
  <lattice id="105" name="Reflector Unrodded Assembly"><dimension>1 1</dimension><pitch>21.42 21.42</pitch><lower_left>-10.71 -10.71</lower_left><universes>8</universes></lattice>
  <lattice id="201" name="3x3 core lattice">
    <dimension>3 3 10</dimension><lower_left>-32.13 -32.13 -107.1</lower_left><pitch>21.42 21.42 21.42</pitch>
    <universes>UNIVERSE_GRID</universes>
  </lattice>
</geometry>
"""
MATERIALS_XML = """<?xml version="1.0"?>
<materials>
<material id="1" name="UO2"/><material id="2" name="MOX 4.3%"/>
<material id="3" name="MOX 7.0%"/><material id="4" name="MOX 8.7%"/>
<material id="5" name="Fission Chamber"/><material id="6" name="Guide Tube"/>
<material id="7" name="Water"/><material id="8" name="Control Rod"/>
</materials>
"""
TALLIES_XML = """<?xml version="1.0"?>
<tallies>
  <mesh id="1" type="regular"><dimension>51 51 30</dimension><lower_left>-32.13 -32.13 -107.1</lower_left><upper_right>32.13 32.13 107.1</upper_right></mesh>
  <filter id="1" type="mesh" bins="1"/>
  <tally id="1" name="axial mesh tally"><filter>1</filter><scores>flux fission nu-fission</scores></tally>
</tallies>
"""
SETTINGS_XML = """<?xml version="1.0"?>
<settings><run_mode>eigenvalue</run_mode><batches>30</batches><inactive>5</inactive><particles>500</particles><seed>640000</seed><energy_mode>multi-group</energy_mode></settings>
"""


class Axial3DPreparationTests(unittest.TestCase):
    def _fixture(self, root: Path) -> Path:
        candidate = root / "c5g7-2x2-UMMU"
        model = candidate / "model"
        (model / "3d").mkdir(parents=True)
        (model / "2d").mkdir(parents=True)
        (model / "3d" / "build-xml-3d.py").write_text(BUILDER, encoding="utf-8")
        active_layer = [9, 11, 13, 11, 9, 13, 13, 13, 13]
        universe_grid = " ".join(str(value) for _ in range(9) for value in active_layer)
        universe_grid += " " + " ".join(["13"] * 9)
        (model / "3d" / "geometry.xml").write_text(
            GEOMETRY_XML.replace("UNIVERSE_GRID", universe_grid), encoding="utf-8"
        )
        for name in ("materials.py", "lattices.py", "surfaces.py"):
            (model / name).write_text("# archived source fixture\n", encoding="utf-8")
        return candidate

    def test_builder_patch_switches_to_3d_tally_and_reproducible_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            candidate = self._fixture(Path(tmp))
            manifest = prepare_candidate(candidate, "a" * 64)
            patched = (candidate / "model/3d/build-xml-3d.py").read_text(encoding="utf-8")
            self.assertIn("from tally_3d import tallies, mesh", patched)
            self.assertNotIn("from tally import tallies, mesh", patched)
            for setting in ("BATCHES", "INACTIVE", "PARTICLES", "SEED"):
                self.assertIn("CBPFR_3D_" + setting, patched)
            tally_text = (candidate / "model/tally_3d.py").read_text(encoding="utf-8")
            self.assertIn("mesh.dimension = [51, 51, 30]", tally_text)
            self.assertNotIn("mesh.dimension = [51, 51, 1]", tally_text)
            self.assertEqual(manifest["geometry_contract"]["z_bins_per_lattice_layer"], 3)
            self.assertEqual(manifest["status"], "prepared_input_not_yet_transport_validated")
            self.assertTrue((candidate / "AXIAL_3D_INPUT_MANIFEST.json").is_file())

    def test_prep_fails_closed_when_upstream_builder_has_drifted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            candidate = self._fixture(Path(tmp))
            path = candidate / "model/3d/build-xml-3d.py"
            path.write_text("import openmc\nprint('changed')\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                prepare_candidate(candidate, "b" * 64)

    def test_input_audit_rejects_2d_mesh_and_accepts_3d_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            candidate = self._fixture(Path(tmp))
            model3d = candidate / "model/3d"
            (model3d / "geometry.xml").write_text((model3d / "geometry.xml").read_text(encoding="utf-8"), encoding="utf-8")
            (model3d / "materials.xml").write_text(MATERIALS_XML, encoding="utf-8")
            (model3d / "settings.xml").write_text(SETTINGS_XML, encoding="utf-8")
            (model3d / "tallies.xml").write_text(TALLIES_XML, encoding="utf-8")
            (model3d / "mgxs.h5").write_bytes(b"test fixture only")
            result = audit_inputs(candidate)
            self.assertEqual(result["mesh_tally"]["bin_count"], 51 * 51 * 30)
            self.assertAlmostEqual(result["mesh_tally"]["bin_width_cm_xyz"][2], 7.14)
            bad = TALLIES_XML.replace("51 51 30", "51 51 1")
            (model3d / "tallies.xml").write_text(bad, encoding="utf-8")
            with self.assertRaises(ValueError):
                audit_inputs(candidate)

    def test_statepoint_export_computes_3d_shape_and_standard_error(self) -> None:
        try:
            import h5py
            import numpy as np
        except ImportError:
            self.skipTest("h5py/numpy unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            statepoint = root / "statepoint.30.h5"
            with h5py.File(statepoint, "w") as h5:
                h5["n_batches"] = 30
                h5["n_inactive"] = 5
                h5["n_particles"] = 500
                h5["n_realizations"] = 25
                h5["seed"] = 640000
                mesh = h5.create_group("tallies/meshes/mesh 1")
                mesh["dimension"] = [2, 2, 3]
                mesh["lower_left"] = [-1.0, -1.0, -3.0]
                mesh["upper_right"] = [1.0, 1.0, 3.0]
                tally = h5.create_group("tallies/tally 1")
                tally["score_bins"] = np.asarray([b"flux", b"fission", b"nu-fission"])
                tally["n_realizations"] = 25
                raw = np.zeros((12, 3, 2), dtype=np.float64)
                raw[:, :, 0] = 25.0
                raw[:, :, 1] = 26.0
                tally["results"] = raw
            out = root / "exports"
            summary = export_statepoint(statepoint, out)
            self.assertEqual(summary["mesh"]["array_shape"], [3, 2, 2, 3])
            self.assertEqual(summary["statepoint"]["n_realizations"], 25)
            self.assertTrue((out / "axial_tally_3d.npz").is_file())
            self.assertTrue((out / "AXIAL_3D_STATEPOINT_SUMMARY.json").is_file())
            with np.load(out / "axial_tally_3d.npz") as payload:
                self.assertEqual(payload["mean"].shape, (3, 2, 2, 3))


    def test_workstation_api_serves_only_a_true_3d_export(self) -> None:
        try:
            import numpy as np
        except ImportError:
            self.skipTest("numpy unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            npz = root / "axial_tally_3d.npz"
            means = np.ones((3, 2, 2, 3), dtype=np.float32)
            errors = np.full_like(means, 0.1)
            relatives = np.full_like(means, 10.0)
            relatives[0, 0, 0, 0] = np.nan
            np.savez_compressed(
                npz, mean=means, standard_error=errors,
                relative_error_percent=relatives,
                score_names=np.asarray(["flux", "fission", "nu-fission"]),
                x_centers_cm=np.asarray([-0.5, 0.5]),
                y_centers_cm=np.asarray([-0.5, 0.5]),
                z_centers_cm=np.asarray([-2.0, 0.0, 2.0]),
            )
            summary = {
                "status": "3d_openmc_statepoint_mesh_exported",
                "statepoint": {"sha256": "c" * 64, "n_realizations": 25},
                "mesh": {
                    "dimension_xyz": [2, 2, 3],
                    "lower_left_cm_xyz": [-1.0, -1.0, -3.0],
                    "upper_right_cm_xyz": [1.0, 1.0, 3.0],
                },
            }
            (root / "AXIAL_3D_STATEPOINT_SUMMARY.json").write_text(
                json.dumps(summary), encoding="utf-8"
            )
            old_path = web_server.AXIAL_TALLY_NPZ
            web_server.AXIAL_TALLY_NPZ = npz
            try:
                payload = web_server.read_axial_3d_evidence("fission")
                flux_payload = web_server.read_axial_3d_evidence("flux")
                with self.assertRaises(ValueError):
                    web_server.read_axial_3d_evidence("not-a-score")
            finally:
                web_server.AXIAL_TALLY_NPZ = old_path
            self.assertTrue(payload["available"])
            self.assertEqual(payload["mesh"]["dimension_xyz"], [2, 2, 3])
            self.assertEqual(payload["mean"], [[[1.0, 1.0], [1.0, 1.0]]] * 3)
            self.assertEqual(payload["provenance"]["statepoint"]["n_realizations"], 25)
            self.assertEqual(payload["score"], "fission")
            self.assertIsNone(flux_payload["relative_error_percent"][0][0][0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
