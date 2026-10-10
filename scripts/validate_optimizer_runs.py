"""Validate and normalize auditable optimizer-run JSON records."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cbpfr.experiment_log import validate_experiment_payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="JSON file containing experiment metadata and run records")
    parser.add_argument("--output", required=True, type=Path, help="Path for normalized JSON; existing files are not overwritten")
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"output already exists: {args.output}")
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        normalized = validate_experiment_payload(payload)
        normalized["source"] = str(args.input)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(normalized, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Validated and wrote optimizer-run records to {args.output}")
    print("Validation checks record structure and numeric integrity; it does not verify that an optimizer actually produced these records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
