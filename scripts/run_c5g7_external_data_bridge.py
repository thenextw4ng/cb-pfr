#!/usr/bin/env python3
"""Audit source-attributed C5G7 layout data and optionally build a layout QUBO."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbpfr.c5g7_data_bridge import (  # noqa: E402
    ExternalDataError, build_one_hot_selection_qubo, coverage_report, load_external_results,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="source-attributed CSV; one aggregate row per candidate")
    parser.add_argument("--output", required=True, help="new JSON output path (must not already exist)")
    parser.add_argument("--objective-column", choices=("keff_mean", "fission_rate_peaking_factor"))
    parser.add_argument("--direction", choices=("min", "max"), default="min")
    args = parser.parse_args()
    output = Path(args.output).expanduser().resolve()
    if output.exists():
        parser.error(f"output already exists; refusing to overwrite: {output}")
    if not output.parent.is_dir():
        parser.error(f"output parent directory does not exist: {output.parent}")
    try:
        results = load_external_results(args.input)
        coverage = coverage_report(results)
        report = {
            "schema_version": "1.0",
            "input_csv": str(Path(args.input).expanduser()),
            "coverage": coverage,
            "source_records": [
                {
                    "candidate_id": item.candidate_id,
                    "benchmark_case": item.benchmark_case,
                    "source_url": item.source_url,
                    "source_kind": item.source_kind,
                    "keff_mean": item.keff_mean,
                    "keff_uncertainty": item.keff_uncertainty,
                    "keff_uncertainty_kind": item.keff_uncertainty_kind,
                    "configuration_hash": item.configuration_hash,
                    "notes": item.notes,
                }
                for item in results.values()
            ],
            "qubo": None,
            "cbpfr_status": "limits_not_supplied; no CB-PFR feasibility claim made",
        }
        if args.objective_column:
            report["qubo"] = build_one_hot_selection_qubo(
                results, objective_column=args.objective_column, direction=args.direction
            )
        elif coverage["status"] == "complete":
            report["next_step"] = (
                "Six candidates are covered. Supply --objective-column explicitly to build the "
                "C5G7 layout-selector QUBO; do not assume keff should be minimized."
            )
        else:
            report["next_step"] = (
                "No full-candidate ranking/QUBO generated. Add source-attributed data for the missing "
                "layouts or restrict the research claim to baseline verification."
            )
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "output": str(output),
            "coverage_status": coverage["status"],
            "observed_candidates": coverage["observed_candidate_count"],
            "expected_candidates": coverage["expected_candidate_count"],
            "qubo_generated": report["qubo"] is not None,
        }, indent=2))
        return 0
    except (ExternalDataError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
