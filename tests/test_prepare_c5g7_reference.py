"""Offline safety tests for the C5G7 source-staging CLI."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare_c5g7_reference.py"


class PrepareC5G7ReferenceTests(unittest.TestCase):
    def test_refuses_existing_destination_without_modifying_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "existing"
            destination.mkdir()
            sentinel = destination / "keep.txt"
            sentinel.write_text("preserve me", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--destination", str(destination)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("refusing to overwrite", result.stderr)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve me")

    def test_refuses_missing_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "missing-parent" / "checkout"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--destination", str(destination)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("parent directory does not exist", result.stderr)
            self.assertFalse(destination.parent.exists())


if __name__ == "__main__":
    unittest.main()
