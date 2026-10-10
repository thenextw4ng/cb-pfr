#!/usr/bin/env python3
"""Clone the public C5G7 reference source and record its exact Git revision.

This stages source code only. It does not run OpenMC or validate physical results.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

UPSTREAM_URL = "https://github.com/mit-crpg/benchmarks.git"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destination",
        required=True,
        help="new directory to clone into; existing paths are never overwritten",
    )
    args = parser.parse_args()

    if shutil.which("git") is None:
        print("ERROR: git executable not found; install Git and retry.", file=sys.stderr)
        return 2

    destination = Path(args.destination).expanduser().resolve()
    if destination.exists():
        print(
            f"ERROR: destination already exists; refusing to overwrite: {destination}",
            file=sys.stderr,
        )
        return 2
    if not destination.parent.exists():
        print(
            f"ERROR: parent directory does not exist: {destination.parent}",
            file=sys.stderr,
        )
        return 2

    try:
        subprocess.run(
            ["git", "clone", "--", UPSTREAM_URL, str(destination)],
            check=True,
            text=True,
        )
        revision = subprocess.run(
            ["git", "-C", str(destination), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if len(revision) != 40 or any(ch not in "0123456789abcdef" for ch in revision):
            raise RuntimeError(f"unexpected full Git commit SHA: {revision!r}")

        provenance = {
            "schema_version": "1.0",
            "source_repository": UPSTREAM_URL,
            "source_commit": revision,
            "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
            "prepared_by_script": "scripts/prepare_c5g7_reference.py",
            "scope": "source acquisition only; no OpenMC run or physical validation performed",
            "expected_model_path": "c5g7/openmc",
            "primary_benchmark_specification": (
                "https://www.oecd-nea.org/jcms/pl_13548/"
                "benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation"
            ),
        }
        (destination / "UPSTREAM_PROVENANCE.json").write_text(
            json.dumps(provenance, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, subprocess.CalledProcessError, RuntimeError) as exc:
        print(f"ERROR: unable to prepare source checkout: {exc}", file=sys.stderr)
        print(
            "Inspect and remove the incomplete destination manually before retrying.",
            file=sys.stderr,
        )
        return 2

    print(f"Staged C5G7 source at: {destination}")
    print(f"Upstream commit: {revision}")
    print("No OpenMC calculation was run; no physical validation is implied.")
    print(f"Review model files under: {destination / 'c5g7' / 'openmc'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
