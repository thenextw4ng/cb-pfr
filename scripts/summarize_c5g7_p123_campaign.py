#!/usr/bin/env python3
"""Aggregate P-1/P-2/P-3 C5G7 OpenMC pilot artifacts without selecting a winner."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
    except OSError:
        return None


def phase_from_artifact_name(name: str) -> str:
    for phase in ("P1", "P2", "P3"):
        if f"-{phase}-" in name:
            return phase
    return "UNKNOWN"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-root", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()

    artifacts_root = args.artifacts_root.resolve()
    outdir = args.outdir.resolve()
    if not artifacts_root.is_dir():
        parser.error(f"artifact root does not exist: {artifacts_root}")
    if outdir.exists():
        parser.error(f"output directory already exists: {outdir}")
    outdir.mkdir(parents=True)

    rows: list[dict[str, Any]] = []
    summaries = sorted(artifacts_root.rglob("STUDY_SUMMARY.json"))
    for summary_path in summaries:
        study = load_json(summary_path)
        rel = summary_path.relative_to(artifacts_root)
        artifact_name = rel.parts[0] if rel.parts else "unknown-artifact"
        phase = phase_from_artifact_name(artifact_name)
        settings = study.get("settings") or {}
        batches = settings.get("batches")
        inactive = settings.get("inactive")
        particles = settings.get("particles")
        try:
            active_histories = max(0, int(batches) - int(inactive)) * int(particles)
        except (TypeError, ValueError):
            active_histories = None

        raw_audit = load_json(summary_path.parent / "analysis" / "raw_hdf5_audit.json")
        raw_status = raw_audit.get("status", "MISSING")
        for case in study.get("cases", []):
            candidate_id = case.get("candidate_id", "UNKNOWN")
            physical = case.get("physical_results") or {}
            case_dir = summary_path.parent / candidate_id
            statepoint_rel = physical.get("statepoint")
            statepoint_path = case_dir / statepoint_rel if statepoint_rel else None
            statepoint_hash = sha256(statepoint_path) if statepoint_path else None
            diagnostics_dir = case_dir / "analysis"
            source_diag = load_json(diagnostics_dir / "source_convergence.json")
            fission = load_json(diagnostics_dir / "assembly_fission.json")
            settings_case = dict(settings)
            rows.append({
                "phase": phase,
                "artifact": artifact_name,
                "candidate_id": candidate_id,
                "layout_signature": candidate_id.removeprefix("c5g7-2x2-"),
                "case_status": case.get("status", "MISSING"),
                "batches": batches,
                "inactive": inactive,
                "particles_per_batch": particles,
                "active_histories": active_histories,
                "seed": case.get("seed"),
                "openmc_version": physical.get("openmc_version"),
                "keff_mean": physical.get("keff_mean"),
                "keff_std_dev": physical.get("keff_std_dev"),
                "fission_rate_peaking_factor": fission.get("fission_rate_peaking_factor"),
                "mgxs_group_structure_audit": physical.get("mgxs_group_structure_audit", "MISSING"),
                "raw_hdf5_audit": raw_status,
                "source_convergence_status": source_diag.get("status", "MISSING"),
                "statepoint_path": str(statepoint_path) if statepoint_path else "",
                "statepoint_sha256": statepoint_hash or "",
                "study_status": study.get("status", "MISSING"),
            })

    order = {"P1": 1, "P2": 2, "P3": 3}
    rows.sort(key=lambda r: (order.get(str(r["phase"]), 9), str(r["candidate_id"])))
    csv_path = outdir / "p123_run_summary.csv"
    fieldnames = [
        "phase", "artifact", "candidate_id", "layout_signature", "case_status",
        "batches", "inactive", "particles_per_batch", "active_histories", "seed",
        "openmc_version", "keff_mean", "keff_std_dev", "fission_rate_peaking_factor",
        "mgxs_group_structure_audit", "raw_hdf5_audit", "source_convergence_status",
        "statepoint_path", "statepoint_sha256", "study_status",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    phases = {p: sum(1 for row in rows if row["phase"] == p) for p in ("P1", "P2", "P3")}
    unique_hashes = {row["statepoint_sha256"] for row in rows if row["statepoint_sha256"]}
    integrity_pass = (
        len(rows) == 10
        and phases == {"P1": 6, "P2": 2, "P3": 2}
        and all(row["case_status"] == "completed" for row in rows)
        and all(row["mgxs_group_structure_audit"] == "PASS" for row in rows)
        and all(row["raw_hdf5_audit"] == "PASS" for row in rows)
        and all(bool(row["statepoint_sha256"]) for row in rows)
        and len(unique_hashes) == len(rows)
    )
    result = {
        "schema_version": "1.0",
        "study_id": "CBPFR-C5G7-P123-discriminative-physics-pilot-2026-10-18",
        "status": "EVIDENCE_INTEGRITY_PASS_INTERPRETATION_OPEN" if integrity_pass else "INCOMPLETE_OR_AUDIT_FAILURE",
        "planned_run_count": 10,
        "observed_run_count": len(rows),
        "phase_counts": phases,
        "integrity_checks": {
            "expected_10_runs": len(rows) == 10,
            "expected_phase_counts": phases == {"P1": 6, "P2": 2, "P3": 2},
            "all_transport_cases_completed": all(row["case_status"] == "completed" for row in rows),
            "all_standard_mgxs_group_audits_pass": all(row["mgxs_group_structure_audit"] == "PASS" for row in rows),
            "all_raw_hdf5_audits_pass": all(row["raw_hdf5_audit"] == "PASS" for row in rows),
            "all_statepoint_hashes_present": all(bool(row["statepoint_sha256"]) for row in rows),
            "unique_statepoint_hashes": len(unique_hashes) == len(rows),
        },
        "winner_selected": False,
        "official_benchmark_acceptance": False,
        "convergence_certified": False,
        "cbpfr_physical_selection_effectiveness_established": False,
        "nonclaims": [
            "This is exploratory screening, not official C5G7 benchmark acceptance.",
            "The assembly fission-rate peaking factor is a relative-shape proxy, not absolute power.",
            "Source-convergence diagnostic review is not replaced by a successful job or raw-data audit.",
            "Matched seeds across different budget profiles are not independent replicates.",
            "The 10 runs do not establish a physically preferred layout or a CB-PFR treatment effect.",
            "The legacy burnup-state QUBO is not mapped to UO2/MOX by this experiment.",
        ],
        "rows": rows,
    }
    json_path = outdir / "p123_campaign_audit.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")

    lines = [
        "# C5G7 P-1/P-2/P-3 discriminative-physics pilot — run summary",
        "",
        f"**Evidence-integrity status:** `{result['status']}`",
        "",
        f"Observed {len(rows)} run records (expected 10: P-1 = 6, P-2 = 2, P-3 = 2).",
        "",
        "| Phase | Layout | Batches / inactive / particles | Active histories | Seed | k-effective ± within-run SD | Fission-peaking proxy | Raw HDF5 | MGXS groups | Source diagnostic |",
        "|---|---|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for row in rows:
        keff = row["keff_mean"]
        sd = row["keff_std_dev"]
        keff_text = f"{keff:.6g} ± {sd:.2g}" if isinstance(keff, (int, float)) and isinstance(sd, (int, float)) else "n/a"
        peaking = row["fission_rate_peaking_factor"]
        peak_text = f"{peaking:.6g}" if isinstance(peaking, (int, float)) else "n/a"
        budget = f"{row['batches']}/{row['inactive']}/{row['particles_per_batch']}"
        lines.append(
            f"| {row['phase']} | {row['layout_signature']} | {budget} | "
            f"{row['active_histories'] if row['active_histories'] is not None else 'n/a'} | "
            f"{row['seed'] if row['seed'] is not None else 'n/a'} | {keff_text} | {peak_text} | "
            f"{row['raw_hdf5_audit']} | {row['mgxs_group_structure_audit']} | "
            f"{row['source_convergence_status']} |"
        )
    lines.extend([
        "",
        "## Interpretation boundary",
        "",
        "- No winner is selected. Do not rank designs by highest or lowest k-effective without a predeclared, physically justified objective and acceptance limits.",
        "- Fission-peaking is a relative-shape proxy, not absolute power or a safety metric.",
        "- A passing raw-HDF5/MGXS audit establishes record integrity, not convergence or official benchmark acceptance.",
        "- `DIAGNOSTIC_REVIEW_REQUIRED` must remain visible and be reviewed; it must not be renamed as a pass.",
        "- Differences across phases are budget-profile sensitivity. Batch count, inactive count, and particles per batch change together, so the pilot does not isolate history count as the sole cause.",
        "- CB-PFR physical selection effectiveness, a legacy QUBO-to-material mapping, and reactor safety are not established.",
        "",
        "## Machine-readable audit",
        "",
        f"See `p123_campaign_audit.json` and `p123_run_summary.csv`. Integrity checks: `{json.dumps(result['integrity_checks'], sort_keys=True)}`.",
        "",
    ])
    report_path = outdir / "P123_DISCRIMINATIVE_PHYSICS_REPORT.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "observed_run_count": len(rows),
        "phase_counts": phases,
        "report": str(report_path),
        "csv": str(csv_path),
        "audit": str(json_path),
    }, indent=2))
    return 0 if integrity_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
