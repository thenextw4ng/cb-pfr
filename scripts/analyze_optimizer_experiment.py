"""Analyze validated optimizer-run records for stability and run quality."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cbpfr.experiment_analysis import summarize_optimizer_experiment


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Validated or raw optimizer experiment JSON")
    parser.add_argument("--output", required=True, type=Path, help="Summary JSON path; existing files are not overwritten")
    parser.add_argument("--top-k", type=int, default=1, help="Top-k candidate set size for cross-run stability")
    parser.add_argument("--objective-sense", choices=("min", "max"), default="min", help="Whether lower or higher objective values are better")
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"output already exists: {args.output}")
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        summary = summarize_optimizer_experiment(payload, top_k=args.top_k, objective_sense=args.objective_sense)
        result = {
            "experiment_id": payload.get("experiment_id", "unspecified"),
            "source": str(args.input),
            "evidence_kind": payload.get("evidence_kind", "as_recorded"),
            "physical_simulation_performed": all(
                run.get("physical_simulation_performed", False) for run in payload.get("runs", [])
            ),
            "summary": summary,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Wrote optimizer experiment summary to {args.output}")
    print("Summary is descriptive and does not certify global optimality or physical validity.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
