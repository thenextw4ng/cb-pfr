"""Analyze repeated optimizer ranking runs from a JSON file.

Input format:
{
  "runs": [
    {"run_id": "run-001", "candidate_ids_ranked": ["candidate-A", "candidate-B"]},
    {"run_id": "run-002", "candidate_ids_ranked": ["candidate-B", "candidate-A"]}
  ],
  "top_k": 2
}

This script summarizes observed ranking stability only; it does not run an optimizer.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cbpfr.repeatability import summarize_repeated_rankings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="JSON file containing ordered candidate IDs for each run")
    parser.add_argument("--output", required=True, type=Path, help="Path for summary JSON; existing files are not overwritten")
    args = parser.parse_args()

    if args.output.exists():
        parser.error(f"output already exists: {args.output}")
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("runs"), list):
            raise ValueError("input must be an object with a 'runs' array")
        run_records = payload["runs"]
        run_ids = []
        rankings = []
        for index, record in enumerate(run_records):
            if not isinstance(record, dict):
                raise ValueError(f"runs[{index}] must be an object")
            run_id = record.get("run_id")
            candidate_ids = record.get("candidate_ids_ranked")
            if not isinstance(run_id, str) or not run_id.strip():
                raise ValueError(f"runs[{index}].run_id must be a non-empty string")
            if run_id in run_ids:
                raise ValueError(f"duplicate run_id: {run_id}")
            if not isinstance(candidate_ids, list):
                raise ValueError(f"runs[{index}].candidate_ids_ranked must be an array")
            run_ids.append(run_id)
            rankings.append(candidate_ids)
        top_k = payload.get("top_k", 1)
        summary = summarize_repeated_rankings(rankings, top_k=top_k)
        output_payload = {
            "run_ids": run_ids,
            "summary": summary,
            "source": str(args.input),
            "evidence_kind": payload.get("evidence_kind", "unspecified"),
            "physical_simulation_performed": False,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(output_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        parser.error(str(exc))

    print(f"Wrote descriptive repeatability summary to {args.output}")
    print("This output is not a global-optimum certificate or physical-validation claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
