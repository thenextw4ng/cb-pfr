import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cbpfr.openmc import preflight_openmc


class OpenMCPreflightTests(unittest.TestCase):
    def _write_model(self, directory: Path):
        (directory / "materials.xml").write_text("<materials />", encoding="utf-8")
        (directory / "geometry.xml").write_text("<geometry />", encoding="utf-8")
        (directory / "settings.xml").write_text("<settings />", encoding="utf-8")

    def test_ready_means_executable_and_well_formed_xml_files_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model"
            model.mkdir()
            self._write_model(model)
            cross_sections = root / "cross_sections.xml"
            cross_sections.write_text("<cross_sections />", encoding="utf-8")
            with patch("cbpfr.openmc.shutil.which", return_value="/usr/bin/openmc"), patch.dict(
                os.environ, {"OPENMC_CROSS_SECTIONS": str(cross_sections)}
            ):
                result = preflight_openmc(model)
            self.assertTrue(result.runnable)
            self.assertEqual(result.missing_files, ())
            self.assertEqual(result.reasons, ())

    def test_malformed_xml_blocks_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model"
            model.mkdir()
            self._write_model(model)
            (model / "geometry.xml").write_text("<geometry>", encoding="utf-8")
            cross_sections = root / "cross_sections.xml"
            cross_sections.write_text("<cross_sections />", encoding="utf-8")
            with patch("cbpfr.openmc.shutil.which", return_value="/usr/bin/openmc"), patch.dict(
                os.environ, {"OPENMC_CROSS_SECTIONS": str(cross_sections)}
            ):
                result = preflight_openmc(model)
            self.assertFalse(result.runnable)
            self.assertTrue(any("geometry.xml is not valid readable XML" in reason for reason in result.reasons))

    def test_missing_inputs_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("cbpfr.openmc.shutil.which", return_value=None), patch.dict(
                os.environ, {}, clear=True
            ):
                result = preflight_openmc(Path(tmp))
            self.assertFalse(result.runnable)
            self.assertEqual(set(result.missing_files), {"materials.xml", "geometry.xml", "settings.xml"})
            self.assertTrue(any("OPENMC_CROSS_SECTIONS is unset" in reason for reason in result.reasons))


if __name__ == "__main__":
    unittest.main()
