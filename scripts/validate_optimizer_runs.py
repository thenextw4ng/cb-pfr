#!/usr/bin/env python3
"""Validate and normalize an optimizer experiment JSON file."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cbpfr.experiment_log import validate_experiment_payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"output already exists: {args.output}")
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        normalized = validate_experiment_payload(payload)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(normalized, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Wrote validated optimizer run log to {args.output}")
    print("Structural validation does not verify optimizer provenance or physical validity.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
