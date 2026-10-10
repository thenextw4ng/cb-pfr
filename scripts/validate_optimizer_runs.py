"""Validate optimizer-run experiment JSON records."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from cbpfr.experiment_log import validate_experiment_payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="Will not overwrite an existing file")
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"output already exists: {args.output}")
    try:
        payload = validate_experiment_payload(json.loads(args.input.read_text(encoding="utf-8")))
        payload["source"] = str(args.input)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Validated optimizer-run records written to {args.output}")
    print("Structural validation does not prove records genuinely came from the stated optimizer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
