#!/usr/bin/env python3
"""Export completed repeated C5G7 study manifests into a validated CB-PFR run CSV.

The study runner must already have completed OpenMC transport for all six layouts
in every supplied study summary. This exporter re-hashes the raw statepoints and
MGXS files, re-parses the fission mesh tally, checks that parsed k-effective values
match the run manifest, and refuses partial, mixed-budget, or nonstandard-group
evidence. It does not launch OpenMC.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable

try:
    from scripts.analyze_c5g7_assembly_fission import analyze_statepoint
except ModuleNotFoundError:
    from analyze_c5g7_assembly_fission import analyze_statepoint


EXPECTED = {"MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM"}
POSITIONS = ("p00", "p01", "p10", "p11")
GROUP_EDGES = (1.0e-5, 0.0635, 10.0, 100.0, 1000.0, 500000.0, 1000000.0, 20000000.0)
GROUP_EDGES_CSV = "1e-05;0.0635;10.0;100.0;1000.0;500000.0;1000000.0;20000000.0"
PINNED_UPSTREAM_COMMIT = "ba41bee54320ada0b4ac39a0dd2ca3c1d090a450"
CSV_FIELDS = (
    "round", "candidate_id", "layout_signature", "seed", "keff_mean",
    "keff_std_dev", "fission_rate_peaking_factor", "statepoint_sha256",
    "mgxs_sha256", "group_structure_audit", "mgxs_energy_group_boundaries_eV",
    "batches", "inactive", "particles_per_batch", "threads",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def export_run_level_evidence(
    study_summaries: list[Path],
    *,
    output_csv: Path,
    audit_json: Path,
    analyzer: Callable[[Path, str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Validate and export one or more complete repeated study summaries."""
    if len(study_summaries) < 3:
        raise ValueError("at least three independent study summaries/seeds are required")
    if output_csv.exists() or audit_json.exists():
        raise ValueError("refusing to overwrite an existing output CSV or audit JSON")
    if output_csv.resolve() == audit_json.resolve():
        raise ValueError("CSV and audit JSON destinations must be different")
    analyze = analyzer or analyze_statepoint
    rows: list[dict[str, Any]] = []
    study_audits = []
    shared_settings = None
    shared_mgxs = None
    shared_builder_hash = None
    shared_design_hash = None
    used_seeds: set[int] = set()
    used_statepoint_hashes: set[str] = set()
    layout_counts: dict[str, int] = {signature: 0 for signature in EXPECTED}

    for summary_path in study_summaries:
        summary_path = summary_path.expanduser().resolve()
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        _require(summary.get("mode") == "run", f"{summary_path}: study mode must be run, not prepare")
        _require(
            summary.get("status") == "all_runs_completed_needs_independent_validation",
            f"{summary_path}: study is not marked as all runs completed",
        )
        _require(
            summary.get("study_id") == "C5G7-2x2-two-UO2-two-MOX-layout-enumeration",
            f"{summary_path}: unexpected C5G7 design study ID",
        )
        _require(summary.get("upstream_commit") == PINNED_UPSTREAM_COMMIT,
                 f"{summary_path}: upstream source commit is not the audited pinned revision")
        builder_hash = summary.get("upstream_model_builder_sha256")
        design_hash = summary.get("design_space_sha256")
        _require(isinstance(builder_hash, str) and len(builder_hash) == 64,
                 f"{summary_path}: missing upstream model builder SHA-256")
        _require(isinstance(design_hash, str) and len(design_hash) == 64,
                 f"{summary_path}: missing design-space SHA-256")
        if shared_builder_hash is None:
            shared_builder_hash = builder_hash
        _require(builder_hash == shared_builder_hash, f"{summary_path}: upstream model builder hash differs across rounds")
        if shared_design_hash is None:
            shared_design_hash = design_hash
        _require(design_hash == shared_design_hash, f"{summary_path}: design-space hash differs across rounds")
        settings = summary.get("settings") or {}
        required_settings = ("batches", "inactive", "particles", "threads")
        _require(all(key in settings for key in required_settings), f"{summary_path}: missing run settings")
        normalized_settings = {key: int(settings[key]) for key in required_settings}
        _require(normalized_settings["batches"] >= 2, f"{summary_path}: invalid batches")
        _require(0 <= normalized_settings["inactive"] < normalized_settings["batches"], f"{summary_path}: invalid inactive batches")
        _require(normalized_settings["particles"] >= 1 and normalized_settings["threads"] >= 1,
                 f"{summary_path}: invalid particle/thread count")
        if shared_settings is None:
            shared_settings = normalized_settings
        _require(normalized_settings == shared_settings, f"{summary_path}: compute settings differ across seed rounds")

        cases = summary.get("cases")
        _require(isinstance(cases, list) and len(cases) == 6, f"{summary_path}: expected six completed layout cases")
        seen_signatures: set[str] = set()
        this_study_hashes = []
        for case in cases:
            candidate_id = case.get("candidate_id")
            signature = case.get("layout")
            _require(case.get("status") == "completed", f"{summary_path}: {candidate_id} case is not completed")
            _require(isinstance(signature, dict) and set(signature) == set(POSITIONS),
                     f"{summary_path}: {candidate_id} must define exactly four fuel positions")
            _require(all(value in ("UO2", "MOX") for value in signature.values()),
                     f"{summary_path}: {candidate_id} contains an unknown fuel material")
            _require(sorted(signature.values()) == ["MOX", "MOX", "UO2", "UO2"],
                     f"{summary_path}: {candidate_id} must contain exactly two MOX and two UO2")
            layout_signature = "".join("M" if signature[p] == "MOX" else "U" for p in POSITIONS)
            _require(candidate_id == f"c5g7-2x2-{layout_signature}",
                     f"{summary_path}: candidate ID does not match material layout for {candidate_id}")
            _require(layout_signature in EXPECTED, f"{summary_path}: unknown layout signature {layout_signature}")
            _require(layout_signature not in seen_signatures, f"{summary_path}: duplicate layout {layout_signature}")
            seen_signatures.add(layout_signature)

            seed = int(case["seed"])
            _require(seed not in used_seeds, f"seed {seed} is reused across supplied studies")
            used_seeds.add(seed)
            physical = case.get("physical_results") or {}
            _require(physical.get("status") == "completed", f"{candidate_id}: parsed OpenMC result is not completed")
            _require(physical.get("mgxs_group_structure_audit") == "PASS",
                     f"{candidate_id}: corrected C5G7 group-structure audit did not pass")
            edges = tuple(float(v) for v in physical.get("mgxs_energy_group_boundaries", ()))
            _require(edges == GROUP_EDGES, f"{candidate_id}: nonstandard C5G7 group boundaries {edges}")

            case_dir = summary_path.parent / candidate_id
            statepoint_rel = physical.get("statepoint")
            _require(isinstance(statepoint_rel, str) and statepoint_rel, f"{candidate_id}: missing statepoint path")
            statepoint_path = case_dir / statepoint_rel
            _require(statepoint_path.is_file(), f"{candidate_id}: statepoint file is missing: {statepoint_path}")
            statepoint_hash = sha256(statepoint_path)
            _require(statepoint_hash not in used_statepoint_hashes, f"{candidate_id}: duplicate statepoint hash")
            used_statepoint_hashes.add(statepoint_hash)
            manifest_hashes = case.get("output_hashes_after_run") or {}
            _require(manifest_hashes.get(statepoint_rel) == statepoint_hash,
                     f"{candidate_id}: statepoint SHA-256 does not match run manifest")

            mgxs_rel = "model/2d/mgxs.h5"
            mgxs_path = case_dir / mgxs_rel
            _require(mgxs_path.is_file(), f"{candidate_id}: MGXS file is missing")
            mgxs_hash = sha256(mgxs_path)
            _require(mgxs_hash == physical.get("mgxs_sha256_before_transport") == physical.get("mgxs_sha256_after_transport"),
                     f"{candidate_id}: MGXS hash changed or does not match transport provenance")
            _require(manifest_hashes.get(mgxs_rel) == mgxs_hash,
                     f"{candidate_id}: MGXS SHA-256 does not match run manifest")
            if shared_mgxs is None:
                shared_mgxs = mgxs_hash
            _require(mgxs_hash == shared_mgxs, f"{candidate_id}: MGXS hash differs across candidate runs")

            tally = analyze(statepoint_path, candidate_id, layout_signature)
            for key in ("keff_mean", "keff_std_dev", "fission_rate_peaking_factor"):
                value = float(tally[key])
                _require(math.isfinite(value), f"{candidate_id}: non-finite {key}")
            _require(math.isclose(float(tally["keff_mean"]), float(physical["keff_mean"]), rel_tol=0.0, abs_tol=1e-12),
                     f"{candidate_id}: re-parsed k-effective mean differs from study summary")
            _require(math.isclose(float(tally["keff_std_dev"]), float(physical["keff_std_dev"]), rel_tol=0.0, abs_tol=1e-12),
                     f"{candidate_id}: re-parsed k-effective SD differs from study summary")
            rows.append({
                "round": str(settings.get("seed_base", summary.get("upstream_commit", summary_path.stem))),
                "candidate_id": candidate_id,
                "layout_signature": layout_signature,
                "seed": seed,
                "keff_mean": float(tally["keff_mean"]),
                "keff_std_dev": float(tally["keff_std_dev"]),
                "fission_rate_peaking_factor": float(tally["fission_rate_peaking_factor"]),
                "statepoint_sha256": statepoint_hash,
                "mgxs_sha256": mgxs_hash,
                "group_structure_audit": "PASS",
                "mgxs_energy_group_boundaries_eV": GROUP_EDGES_CSV,
                "batches": normalized_settings["batches"],
                "inactive": normalized_settings["inactive"],
                "particles_per_batch": normalized_settings["particles"],
                "threads": normalized_settings["threads"],
            })
            layout_counts[layout_signature] += 1
            this_study_hashes.append(statepoint_hash)

        _require(seen_signatures == EXPECTED, f"{summary_path}: all six expected layouts are not present")
        study_audits.append({
            "summary_path": str(summary_path),
            "summary_sha256": sha256(summary_path),
            "seed_base": settings.get("seed_base"),
            "case_count": len(cases),
            "all_six_layouts_present": True,
            "statepoint_hashes": this_study_hashes,
        })

    _require(len(set(layout_counts.values())) == 1, "replicate counts differ across layouts")
    _require(min(layout_counts.values()) >= 3, "each layout must have at least three independent runs")
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    audit_json.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    audit = {
        "schema_version": "cbpfr.c5g7-run-export-audit.v1",
        "status": "RUN_EVIDENCE_EXPORTED_INTEGRITY_PASS_PHYSICAL_VALIDATION_NOT_CERTIFIED",
        "study_count": len(study_audits),
        "run_count": len(rows),
        "layout_count": len(EXPECTED),
        "replicates_per_layout": layout_counts,
        "unique_seeds": len(used_seeds) == len(rows),
        "unique_statepoint_hashes": len(used_statepoint_hashes) == len(rows),
        "single_mgxs_sha256": shared_mgxs,
        "upstream_commit": PINNED_UPSTREAM_COMMIT,
        "upstream_model_builder_sha256": shared_builder_hash,
        "design_space_sha256": shared_design_hash,
        "common_compute_settings": shared_settings,
        "group_boundaries_eV": list(GROUP_EDGES),
        "study_summaries": study_audits,
        "output_csv": str(output_csv),
        "output_csv_sha256": sha256(output_csv),
        "physical_validation_certified": False,
        "note": (
            "Integrity checks establish that supplied run summaries and raw files agree and share the "
            "declared corrected-group/settings contract. They do not certify benchmark validity, convergence, "
            "physical superiority, or reactor safety."
        ),
    }
    audit_json.write_text(json.dumps(audit, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-summary", type=Path, nargs="+", required=True,
                        help="at least three completed STUDY_SUMMARY.json files, one per independent seed round")
    parser.add_argument("--out-csv", type=Path, required=True)
    parser.add_argument("--audit-out", type=Path, required=True)
    args = parser.parse_args()
    try:
        audit = export_run_level_evidence(args.study_summary, output_csv=args.out_csv, audit_json=args.audit_out)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "status": audit["status"],
        "study_count": audit["study_count"],
        "run_count": audit["run_count"],
        "replicates_per_layout": audit["replicates_per_layout"],
        "output_csv": audit["output_csv"],
        "audit_out": str(args.audit_out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
