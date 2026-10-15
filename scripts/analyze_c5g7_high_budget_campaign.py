#!/usr/bin/env python3
"""Aggregate and fail-closed audit the high-budget six-layout C5G7 campaign.

This is a project-level numerical screen, not official benchmark acceptance.
A scalar k-effective match does not replace model-identity review and a
benchmark-compatible spatial pin-power comparison.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, statistics, xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

GROUPS = (1e-5, 0.0635, 10.0, 100.0, 1000.0, 500000.0, 1000000.0, 20000000.0)
REFERENCE_KEFF, REFERENCE_SD = 1.18655, 0.000095
PROFILE = (20000, 500, 10000, 1)
EXPECTED = {
    "c5g7-2x2-MMUU": "MMUU", "c5g7-2x2-MUMU": "MUMU",
    "c5g7-2x2-MUUM": "MUUM", "c5g7-2x2-UMMU": "UMMU",
    "c5g7-2x2-UMUM": "UMUM", "c5g7-2x2-UUMM": "UUMM",
}
POSITIONS = ("p00", "p01", "p10", "p11")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sig(layout: dict[str, str]) -> str:
    return "".join("M" if layout.get(p) == "MOX" else "U" if layout.get(p) == "UO2" else "?" for p in POSITIONS)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def load_records(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows, errors = [], []
    summaries = sorted(root.rglob("STUDY_SUMMARY.json"))
    if not summaries:
        raise ValueError(f"No STUDY_SUMMARY.json found under {root}")
    for summary_path in summaries:
        rd = summary_path.parent
        try:
            study = json.loads(summary_path.read_text())
            if study.get("status") != "all_runs_completed_needs_independent_validation":
                raise ValueError(f"study status is {study.get('status')!r}")
            cases = study.get("cases", [])
            if len(cases) != 1:
                raise ValueError(f"expected one candidate, got {len(cases)}")
            case = cases[0]
            cid = case.get("candidate_id")
            if cid not in EXPECTED or sig(case.get("layout") or {}) != EXPECTED[cid]:
                raise ValueError(f"candidate/layout mismatch: {cid}")
            if case.get("status") != "completed":
                raise ValueError(f"case status is {case.get('status')!r}")
            physical = case.get("physical_results") or {}
            case_dir = rd / cid
            sp_rel = physical.get("statepoint")
            if not isinstance(sp_rel, str) or not sp_rel:
                raise ValueError("missing statepoint path")
            sp = case_dir / sp_rel
            if not sp.is_file() or not sp.stat().st_size:
                raise ValueError(f"missing/empty statepoint {sp}")
            required = {
                "raw": rd / "analysis/raw_hdf5_audit.json",
                "source": rd / "analysis/source_convergence.json",
                "source_csv": rd / "analysis/source_convergence.csv",
                "fission": rd / "analysis/assembly_fission.json",
                "mesh": rd / "analysis/high_budget_run_audit.json",
            }
            missing = [str(p.relative_to(rd)) for p in required.values() if not p.is_file()]
            if missing:
                raise ValueError(f"missing audit outputs {missing}")
            raw = json.loads(required["raw"].read_text())
            source = json.loads(required["source"].read_text())
            fission = json.loads(required["fission"].read_text())
            mesh = json.loads(required["mesh"].read_text())
            if raw.get("status") != "PASS" or raw.get("candidate_count") != 1:
                raise ValueError(f"raw HDF5 audit status={raw.get('status')!r}")
            if source.get("status") != "DIAGNOSTIC_REVIEW_REQUIRED" or not source.get("entropy"):
                raise ValueError("source entropy/k-generation traces absent")
            if mesh.get("warning_count") != 0 or mesh.get("settings_profile_pass") is not True:
                raise ValueError("mesh warning or common settings check failed")
            if fission.get("candidate_id") != cid or fission.get("layout_signature") != EXPECTED[cid]:
                raise ValueError("assembly fission analysis does not match candidate")
            boundaries = tuple(float(v) for v in (physical.get("mgxs_energy_group_boundaries") or []))
            if physical.get("mgxs_group_structure_audit") != "PASS" or boundaries != GROUPS:
                raise ValueError("official C5G7 energy group structure audit failed")
            state_hash = sha256(sp)
            raw_case = raw["candidates"][0]
            if raw_case.get("statepoint_sha256") != state_hash:
                raise ValueError("statepoint hash disagrees with raw audit")
            settings_path = case_dir / "model/2d/settings.xml"
            settings = ET.parse(settings_path).getroot()
            seed = int(case["seed"])
            observed_seed = int(settings.findtext("seed"))
            profile = (int(settings.findtext("batches")), int(settings.findtext("inactive")),
                       int(settings.findtext("particles")), int(study["settings"]["threads"]))
            if observed_seed != seed:
                raise ValueError(f"settings seed {observed_seed} != study seed {seed}")
            if profile != PROFILE:
                raise ValueError(f"settings profile {profile} != {PROFILE}")
            rate = fission["assembly_integrated_fission_rate"]
            normalized = fission["normalized_assembly_fission_rate"]
            rows.append({
                "run_dir": str(rd), "candidate_id": cid, "layout_signature": EXPECTED[cid],
                "seed": seed, "seed_base": int(study["settings"]["seed_base"]),
                "batches": profile[0], "inactive": profile[1], "particles_per_batch": profile[2],
                "threads": profile[3], "keff_mean": float(physical["keff_mean"]),
                "keff_std_dev": float(physical["keff_std_dev"]),
                "fission_rate_peaking_factor": float(fission["fission_rate_peaking_factor"]),
                "assembly_rate_p00": float(rate["p00"]), "assembly_rate_p01": float(rate["p01"]),
                "assembly_rate_p10": float(rate["p10"]), "assembly_rate_p11": float(rate["p11"]),
                "normalized_rate_p00": float(normalized["p00"]), "normalized_rate_p01": float(normalized["p01"]),
                "normalized_rate_p10": float(normalized["p10"]), "normalized_rate_p11": float(normalized["p11"]),
                "statepoint_sha256": state_hash, "settings_sha256": raw_case.get("settings_sha256"),
                "mgxs_sha256": raw_case.get("mgxs_sha256"),
                "mgxs_group_structure_audit": physical.get("mgxs_group_structure_audit"),
                "mgxs_energy_group_boundaries": ";".join(str(x) for x in boundaries),
                "raw_hdf5_audit": raw.get("status"), "entropy_mesh_warning_count": int(mesh["warning_count"]),
                "source_convergence_status": source.get("status"),
                "source_entropy_trace_present": bool(source.get("entropy")),
                "entropy_lag1_acf": (source.get("entropy") or {}).get("lag1_autocorrelation"),
                "k_generation_half_delta_pcm": source.get("k_generation_second_minus_first_half_pcm"),
                "upstream_commit": study.get("upstream_commit"),
                "openmc_version": physical.get("openmc_version"),
            })
        except Exception as exc:
            errors.append(f"{summary_path}: {type(exc).__name__}: {exc}")
    return rows, errors


def aggregate(rows: list[dict[str, Any]], errors: list[str], protocol: dict[str, Any]) -> dict[str, Any]:
    by_cid = {cid: [r for r in rows if r["candidate_id"] == cid] for cid in EXPECTED}
    checks = {
        "all_18_runs_present_and_auditable": len(rows) == 18 and not errors,
        "exact_six_declared_layouts": {r["candidate_id"] for r in rows} == set(EXPECTED),
        "three_replicates_per_layout": all(len(v) == 3 for v in by_cid.values()),
        "unique_actual_seeds": len({r["seed"] for r in rows}) == len(rows),
        "unique_statepoint_hashes": len({r["statepoint_sha256"] for r in rows}) == len(rows),
        "one_common_mgxs_hash": len({r["mgxs_sha256"] for r in rows}) == 1 and bool(rows) and all(r["mgxs_sha256"] for r in rows),
        "one_pinned_upstream_revision": len({r["upstream_commit"] for r in rows}) == 1 and bool(rows),
        "official_group_structure_all_runs": all(r["mgxs_group_structure_audit"] == "PASS" and tuple(float(v) for v in r["mgxs_energy_group_boundaries"].split(";")) == GROUPS for r in rows),
        "all_raw_hdf5_audits_pass": len(rows) == 18 and all(r["raw_hdf5_audit"] == "PASS" for r in rows),
        "zero_entropy_mesh_warnings": len(rows) == 18 and all(r["entropy_mesh_warning_count"] == 0 for r in rows),
        "common_high_budget_settings": len({(r["batches"], r["inactive"], r["particles_per_batch"], r["threads"]) for r in rows}) == 1 and all((r["batches"], r["inactive"], r["particles_per_batch"], r["threads"]) == PROFILE for r in rows),
        "source_diagnostics_preserved": len(rows) == 18 and all(r["source_convergence_status"] == "DIAGNOSTIC_REVIEW_REQUIRED" and r["source_entropy_trace_present"] for r in rows),
    }
    layouts = []
    for cid, signature in EXPECTED.items():
        group = sorted(by_cid[cid], key=lambda r: r["seed"])
        if not group:
            continue
        ks = [r["keff_mean"] for r in group]
        ksd = [r["keff_std_dev"] for r in group]
        peaks = [r["fission_rate_peaking_factor"] for r in group]
        asm = {}
        for pos in POSITIONS:
            vals = [r[f"normalized_rate_{pos}"] for r in group]
            asm[pos] = {"mean": statistics.mean(vals), "between_seed_sample_sd": statistics.stdev(vals) if len(vals) > 1 else None}
        layouts.append({
            "candidate_id": cid, "layout_signature": signature, "n_runs": len(group),
            "seeds": [r["seed"] for r in group], "mean_keff": statistics.mean(ks),
            "between_seed_sample_sd_keff": statistics.stdev(ks) if len(ks) > 1 else None,
            "pooled_within_run_reported_sd_keff": math.sqrt(statistics.mean(v*v for v in ksd)),
            "mean_fission_rate_peaking_factor": statistics.mean(peaks),
            "between_seed_sample_sd_fission_rate_peaking_factor": statistics.stdev(peaks) if len(peaks) > 1 else None,
            "mean_normalized_assembly_fission_rates": asm,
            "metric_note": "descriptive fission-rate proxy, not absolute power or an approved final design objective",
        })
    complete_layouts = [x for x in layouts if x["n_runs"] == 3]
    for rank, item in enumerate(sorted(complete_layouts, key=lambda x: (x["mean_fission_rate_peaking_factor"], x["layout_signature"])), start=1):
        item["descriptive_fission_peaking_order"] = rank

    canonical = by_cid["c5g7-2x2-UMMU"]
    scalar = {"status": "NOT_EVALUATED", "numerical_screen_pass": False}
    if len(canonical) == 3:
        means = [r["keff_mean"] for r in canonical]
        sds = [r["keff_std_dev"] for r in canonical]
        mean_k = statistics.mean(means)
        between = statistics.stdev(means)
        pooled_within = math.sqrt(statistics.mean(x*x for x in sds))
        combined_se = math.sqrt(REFERENCE_SD**2 + (between / math.sqrt(3))**2)
        delta_pcm = (mean_k - REFERENCE_KEFF) * 1e5
        z = (mean_k - REFERENCE_KEFF) / combined_se
        max_run_sd = max(sds) * 1e5
        numeric_pass = (abs(delta_pcm) <= 100 and abs(z) <= 2 and max_run_sd <= 10
                        and checks["all_raw_hdf5_audits_pass"]
                        and checks["official_group_structure_all_runs"]
                        and checks["zero_entropy_mesh_warnings"]
                        and checks["unique_statepoint_hashes"] and checks["one_common_mgxs_hash"])
        scalar = {
            "status": "NUMERICAL_SCREEN_PASS_FULL_BENCHMARK_STILL_BLOCKED" if numeric_pass else "FAIL_OR_INCOMPLETE_NUMERICAL_SCREEN",
            "mean_keff": mean_k, "between_run_sample_sd": between,
            "pooled_within_run_reported_sd": pooled_within, "mean_combined_standard_uncertainty": combined_se,
            "reference_delta_pcm": delta_pcm, "combined_uncertainty_z": z,
            "max_single_run_reported_sd_pcm": max_run_sd, "numerical_screen_pass": numeric_pass,
        }
    integrity_pass = all(checks.values())
    if errors or not integrity_pass:
        status = "FAIL_OR_INCOMPLETE_DATA_INTEGRITY"
    elif scalar.get("numerical_screen_pass"):
        status = "NUMERICAL_SCREEN_PASS_FULL_BENCHMARK_STILL_BLOCKED"
    else:
        status = "FAIL_OR_INCOMPLETE_NUMERICAL_SCREEN"
    return {
        "schema_version": "1.0", "protocol_id": protocol["protocol_id"], "overall_status": status,
        "official_benchmark_acceptance": False, "physical_validation_claim_authorized": False,
        "model_identity_independently_reviewed_against_primary_specification": False,
        "official_spatial_pin_power_reference_transcribed_and_reviewed": False,
        "benchmark_compatible_spatial_tally_comparison_passed": False,
        "legacy_qubo_to_uo2_mox_mapping_validated": False,
        "run_count": len(rows), "candidate_count": len({r["candidate_id"] for r in rows}),
        "run_errors": errors, "global_checks": checks, "canonical_ummu_reference_screen": scalar,
        "layout_summaries": layouts,
        "run_summaries": rows,
        "expected_profile": {"batches": PROFILE[0], "inactive": PROFILE[1], "particles_per_batch": PROFILE[2], "threads": PROFILE[3]},
        "resource_accounting": {"histories_per_run": PROFILE[0]*PROFILE[2], "total_histories_if_all_18_complete": 18*PROFILE[0]*PROFILE[2]},
        "interpretation": (
            "Even if canonical UMMU passes the provisional scalar screen, official benchmark acceptance is blocked until "
            "an independent model-identity review and benchmark-compatible spatial pin-power comparison are completed. "
            "The other five layouts are design variants, not official C5G7 reference cases. The fission-peaking proxy is "
            "descriptive and does not validate the legacy QUBO mapping or prove CB-PFR superiority."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    if args.outdir.exists() and any(args.outdir.iterdir()):
        parser.error(f"refusing to overwrite non-empty output directory: {args.outdir}")
    protocol = json.loads(args.protocol.read_text())
    if protocol.get("protocol_id") != "CBPFR-C5G7-HIGH-BUDGET-SIX-LAYOUT-2026-10-15":
        parser.error("unexpected protocol ID")
    rows, errors = load_records(args.artifacts_root)
    report = aggregate(rows, errors, protocol)
    args.outdir.mkdir(parents=True, exist_ok=True)
    write_csv(args.outdir / "run_level_results.csv", rows)
    write_csv(args.outdir / "layout_summary.csv", report["layout_summaries"])
    (args.outdir / "high_budget_campaign_summary.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    metric = report["canonical_ummu_reference_screen"]
    lines = [
        "# High-budget C5G7 six-layout transport campaign", "",
        f"**Overall status:** {report['overall_status']}",
        f"**Runs audited:** {report['run_count']} / 18",
        "**Configured budget:** 20,000 batches × 10,000 particles; 500 inactive; one thread.",
        f"**Planned total particle histories:** {report['resource_accounting']['total_histories_if_all_18_complete']:,}.",
        "", "## Canonical UMMU: provisional scalar reference screen", "",
        f"- Status: {metric.get('status', 'NOT_EVALUATED')}",
        f"- Mean k-effective: {metric.get('mean_keff', 'NA')}",
        f"- Between-run sample SD: {metric.get('between_run_sample_sd', 'NA')}",
        f"- Pooled within-run reported SD: {metric.get('pooled_within_run_reported_sd', 'NA')}",
        f"- Difference from reference: {metric.get('reference_delta_pcm', 'NA')} pcm",
        f"- Combined-uncertainty z: {metric.get('combined_uncertainty_z', 'NA')}",
        f"- Maximum individual-run SD: {metric.get('max_single_run_reported_sd_pcm', 'NA')} pcm",
        "", "These are provisional project screens, not official OECD/NEA acceptance tolerances. Matching a scalar k-effective is not sufficient validation.",
        "", "## Six-layout high-budget results", "",
        "| Layout | Runs | Mean k-effective | Between-seed SD (k) | Mean fission-peaking proxy | SD (proxy) | Descriptive order |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in report["layout_summaries"]:
        lines.append(
            f"| {item['layout_signature']} | {item['n_runs']} | {item['mean_keff']:.8f} | "
            f"{item['between_seed_sample_sd_keff'] if item['between_seed_sample_sd_keff'] is not None else 'NA'} | "
            f"{item['mean_fission_rate_peaking_factor']:.6f} | "
            f"{item['between_seed_sample_sd_fission_rate_peaking_factor'] if item['between_seed_sample_sd_fission_rate_peaking_factor'] is not None else 'NA'} | "
            f"{item.get('descriptive_fission_peaking_order', 'NA')} |"
        )
    lines.extend(["", "## Integrity gates", "", "| Gate | Status |", "|---|---|"])
    lines.extend(f"| {key} | {'PASS' if value else 'FAIL'} |" for key, value in report["global_checks"].items())
    if errors:
        lines.extend(["", "## Run errors", ""] + [f"- {error}" for error in errors])
    lines.extend([
        "", "## What still blocks benchmark-level validation", "",
        "- Independent review of geometry, boundaries, materials, compositions, nuclear-data provenance, and generated inputs against the primary C5G7 specification.",
        "- A reviewed official spatial pin-power reference table with matched normalization, followed by RMS and maximum relative error with uncertainty treatment. Assembly-integrated tallies alone do not satisfy this gate.",
        "- Source-convergence diagnostics must be reviewed against explicit justified criteria; this campaign does not auto-certify convergence from scalar summaries.",
        "- UMMU is the canonical reference check. Other layouts are not official independent C5G7 reference cases.",
        "- No legacy QUBO-to-UO2/MOX mapping, CB-PFR physical superiority, or reactor-safety claim follows from these runs.",
        "", "## Sources", "",
        "- OECD/NEA C5G7 benchmark description: https://www.oecd-nea.org/jcms/pl_13548/benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation",
        "- Original 2D/3D benchmark paper: https://doi.org/10.1016/j.pnueene.2004.09.003",
        "- Pinned OpenMC model source: https://github.com/mit-crpg/benchmarks",
        "", "Raw statepoints, logs, XML inputs, tallies, source traces, and per-run audits are preserved in GitHub Actions artifacts named c5g7-high-budget-*. This report does not authorize a benchmark-validation claim."
    ])
    (args.outdir / "high_budget_campaign_report.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"overall_status": report["overall_status"], "run_count": report["run_count"],
                      "global_checks": report["global_checks"], "canonical_ummu_reference_screen": metric,
                      "outdir": str(args.outdir)}, indent=2, sort_keys=True))
    # Integrity failures must fail the aggregate job; a failed provisional numerical
    # screen is a reportable result and must not be silently retried or hidden.
    return 2 if errors or not all(report["global_checks"].values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
