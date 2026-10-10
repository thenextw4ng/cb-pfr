"""Audit a benchmark manifest and write a machine-readable gate report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cbpfr.benchmark import audit_benchmark_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="Will not overwrite an existing file")
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"output already exists: {args.output}")
    try:
        manifest = json.loads(args.input.read_text(encoding="utf-8"))
        audit = audit_benchmark_manifest(manifest)
        result = {"source_manifest": str(args.input), "audit": audit}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Benchmark gate: {audit['status']}")
    print(f"Blockers: {len(audit['blockers'])}")
    for blocker in audit["blockers"]:
        print(f"- {blocker}")
    print("This structural audit does not validate physics or independently verify cited sources.")
    return 0 if audit["status"] == "ready_for_baseline_run" else 2


if __name__ == "__main__":
    raise SystemExit(main())
