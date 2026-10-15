#!/usr/bin/env python3
"""Stable compatibility entry point for the audited C5G7 layout runner."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_c5g7_layout_study import main

if __name__ == "__main__":
    raise SystemExit(main())
