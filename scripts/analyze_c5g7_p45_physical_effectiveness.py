#!/usr/bin/env python3
"""Audit P-4/P-5 repeated OpenMC runs and compare frozen selection rules on held-out physics.

This is a descriptive pilot. It never declares a reactor-safe or benchmark-validated
layout and never treats the cardinality-only layout QUBO as a physical optimizer.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import statistics
from pathlib import Path
from typing import Any

EXPECTED_LAYOUTS = {"MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM"}
EXPECTED_PER_PHASE = {"P4": 18, "P5": 18}
BOOTSTRAP_REPLICATES = 10000
RISK_WEIGHT = 1.0
BOOTSTRAP_SEED = 20261018


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def file_sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def sample_sd(values: list[float]) -> float:
    return statistics.stdev(values) if len(values) >= 2 else 0.0


def mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else math.nan


def phase_from_artifact(name: str) -> str:
    for phase in ("P4", "P5"):
        if f"-{phase}-" in name:
            return phase
    return "UNKNOWN"


def collect_runs(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for study_path in sorted(root.rglob("STUDY_SUMMARY.json")):
        study = read_json(study_path)
        relative = study_path.relative_to(root)
        artifact = relative.parts[0] if relative.parts else "unknown"
        phase = phase_from_artifact(artifact)
        raw_audit = read_json(study_path.parent / "analysis" / "raw_hdf5_audit.json")
        for case in study.get("cases", []):
            cid = str(case.get("candidate_id", "UNKNOWN"))
            physical = case.get("physical_results") or {}
            case_dir = study_path.parent / cid
            statepoint_rel = physical.get("statepoint")
            statepoint = case_dir / statepoint_rel if isinstance(statepoint_rel, str) else None
            source = read_json(case_dir / "analysis" / "source_convergence.json")
            fission = read_json(case_dir / "analysis" / "assembly_fission.json")
            rows.append({
                "phase": phase,
                "artifact": artifact,
                "candidate_id": cid,
                "layout_signature": cid.removeprefix("c5g7-2x2-"),
                "case_status": case.get("status", "MISSING"),
                "batches": (study.get("settings") or {}).get("batches"),
                "inactive": (study.get("settings") or {}).get("inactive"),
                "particles_per_batch": (study.get("settings") or {}).get("particles"),
                "active_histories": max(0, int((study.get("settings") or {}).get("batches", 0))
                                          - int((study.get("settings") or {}).get("inactive", 0)))
                                     * int((study.get("settings") or {}).get("particles", 0)),
                "seed": case.get("seed"),
                "keff_mean": physical.get("keff_mean"),
                "keff_std_dev_within_run": physical.get("keff_std_dev"),
                "fission_rate_peaking_factor": fission.get("fission_rate_peaking_factor"),
                "raw_hdf5_audit": raw_audit.get("status", "MISSING"),
                "mgxs_group_structure_audit": physical.get("mgxs_group_structure_audit", "MISSING"),
                "mgxs_sha256": physical.get("mgxs_sha256_after_transport"),
                "source_convergence_status": source.get("status", "MISSING"),
                "statepoint_path": str(statepoint) if statepoint else "",
                "statepoint_sha256": file_sha256(statepoint) if statepoint else None,
                "study_status": study.get("status", "MISSING"),
            })
    return rows


def percentile(values: list[float], q: float) -> float:
    if not values:
        return math.nan
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def bootstrap_comparison(screening: dict[str, list[float]],
                         heldout: dict[str, list[float]],
                         replicates: int = BOOTSTRAP_REPLICATES) -> dict[str, Any]:
    """Nested seed bootstrap for selection stability and independent-test regret."""
    rng = random.Random(BOOTSTRAP_SEED)
    layouts = sorted(EXPECTED_LAYOUTS)
    methods = ("point_estimate", "cbpfr_risk_adjusted", "uniform_margin",
               "random_feasible", "qubo_feasibility_only")
    regret_samples: dict[str, list[float]] = {name: [] for name in methods}
    selected_counts: dict[str, dict[str, int]] = {name: {layout: 0 for layout in layouts} for name in methods}
    paired_differences: list[float] = []
    cb_win = point_win = tie_count = 0

    for _ in range(replicates):
        s_means: dict[str, float] = {}
        s_sds: dict[str, float] = {}
        for layout in layouts:
            sample = [rng.choice(screening[layout]) for _ in screening[layout]]
            s_means[layout] = mean(sample)
            s_sds[layout] = sample_sd(sample)
        # Common additive margins cannot change a ranking; this is an explicit sanity baseline.
        common_margin = mean(list(s_sds.values()))
        scores = {
            "point_estimate": {layout: s_means[layout] for layout in layouts},
            "cbpfr_risk_adjusted": {layout: s_means[layout] + RISK_WEIGHT * s_sds[layout] for layout in layouts},
            "uniform_margin": {layout: s_means[layout] + common_margin for layout in layouts},
        }
        choices = {
            "point_estimate": min(layouts, key=lambda x: (scores["point_estimate"][x], x)),
            "cbpfr_risk_adjusted": min(layouts, key=lambda x: (scores["cbpfr_risk_adjusted"][x], x)),
            "uniform_margin": min(layouts, key=lambda x: (scores["uniform_margin"][x], x)),
            "random_feasible": rng.choice(layouts),
            # The material-count QUBO gives every exactly-two-MOX layout equal energy.
            "qubo_feasibility_only": rng.choice(layouts),
        }
        test_means: dict[str, float] = {}
        for layout in layouts:
            sample = [rng.choice(heldout[layout]) for _ in heldout[layout]]
            test_means[layout] = mean(sample)
        oracle = min(test_means.values())
        regrets = {name: test_means[layout] - oracle for name, layout in choices.items()}
        for name, layout in choices.items():
            selected_counts[name][layout] += 1
            regret_samples[name].append(regrets[name])
        diff = regrets["cbpfr_risk_adjusted"] - regrets["point_estimate"]
        paired_differences.append(diff)
        if diff < -1e-12:
            cb_win += 1
        elif diff > 1e-12:
            point_win += 1
        else:
            tie_count += 1

    return {
        "bootstrap_replicates": replicates,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "risk_weight": RISK_WEIGHT,
        "method_mean_heldout_regret": {
            name: {
                "mean": mean(values),
                "median": percentile(values, 0.5),
                "percentile_95_interval": [percentile(values, 0.025), percentile(values, 0.975)],
            }
            for name, values in regret_samples.items()
        },
        "paired_cbpfr_minus_point_regret": {
            "mean": mean(paired_differences),
            "percentile_95_interval": [percentile(paired_differences, 0.025),
                                       percentile(paired_differences, 0.975)],
            "bootstrap_fraction_cbpfr_lower_regret": cb_win / replicates,
            "bootstrap_fraction_point_estimate_lower_regret": point_win / replicates,
            "bootstrap_fraction_tied_regret": tie_count / replicates,
            "interpretation": (
                "Negative difference favours CB-PFR on the held-out fission-rate proxy. "
                "The bootstrap is exploratory with only three seeds per layout and does not "
                "establish generalizable superiority."
            ),
        },
        "selection_frequency_by_layout": {
            method: {layout: count / replicates for layout, count in counts.items()}
            for method, counts in selected_counts.items()
        },
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    phase_counts = {phase: sum(row["phase"] == phase for row in rows) for phase in ("P4", "P5")}
    count_per_candidate = {
        phase: {
            layout: sum(row["phase"] == phase and row["layout_signature"] == layout for row in rows)
            for layout in sorted(EXPECTED_LAYOUTS)
        }
        for phase in ("P4", "P5")
    }
    hashes = [row["statepoint_sha256"] for row in rows if row["statepoint_sha256"]]
    mgxs_hashes = {row["mgxs_sha256"] for row in rows if row["mgxs_sha256"]}
    integrity_checks = {
        "expected_36_run_records": len(rows) == 36,
        "expected_phase_run_counts": phase_counts == EXPECTED_PER_PHASE,
        "three_runs_per_layout_each_phase": all(
            count_per_candidate[phase][layout] == 3
            for phase in ("P4", "P5") for layout in EXPECTED_LAYOUTS
        ),
        "all_transport_cases_completed": all(row["case_status"] == "completed" for row in rows),
        "all_raw_hdf5_audits_pass": all(row["raw_hdf5_audit"] == "PASS" for row in rows),
        "all_standard_mgxs_group_audits_pass": all(row["mgxs_group_structure_audit"] == "PASS" for row in rows),
        "all_statepoint_hashes_present": len(hashes) == len(rows),
        "unique_statepoint_hashes": len(set(hashes)) == len(rows),
        "single_shared_mgxs_hash": len(mgxs_hashes) == 1 and len(mgxs_hashes) > 0,
    }
    integrity_pass = all(integrity_checks.values())
    screening: dict[str, list[float]] = {}
    heldout: dict[str, list[float]] = {}
    method_report: dict[str, Any] = {}
    physical_comparison: dict[str, Any] = {
        "status": "BLOCKED_INCOMPLETE_EVIDENCE" if not integrity_pass else "EXPLORATORY_COMPARISON_ONLY",
        "objective": "minimize the held-out mean assembly-integrated fission-rate peaking proxy",
        "objective_interpretation": "Relative fission-rate shape proxy only; not absolute power or a safety metric.",
        "independent_high_budget_evaluation": "P5 uses seed bases 910000, 920000, 930000, distinct from P4's 810000, 820000, 830000.",
        "design_specific_keff_acceptance_band": "NOT_SUPPLIED; physical feasibility and selection remain blocked.",
        "within_tally_covariance_propagation": "NOT_IMPLEMENTED; cross-seed variability only is available in this pilot.",
    }
    if integrity_pass:
        for layout in sorted(EXPECTED_LAYOUTS):
            for phase, container in (("P4", screening), ("P5", heldout)):
                selected = [row for row in rows if row["phase"] == phase and row["layout_signature"] == layout]
                selected.sort(key=lambda row: int(row["seed"]))
                container[layout] = [float(row["fission_rate_peaking_factor"]) for row in selected]
                if not all(math.isfinite(x) and x > 0 for x in container[layout]):
                    integrity_checks["finite_positive_fission_proxy_values"] = False
        integrity_pass = all(integrity_checks.values())
    if integrity_pass:
        p4 = {}
        p5 = {}
        for layout in sorted(EXPECTED_LAYOUTS):
            p4rows = [r for r in rows if r["phase"] == "P4" and r["layout_signature"] == layout]
            p5rows = [r for r in rows if r["phase"] == "P5" and r["layout_signature"] == layout]
            f4 = screening[layout]
            f5 = heldout[layout]
            p4[layout] = {
                "n_independent_seeds": len(f4),
                "mean_keff": mean([float(r["keff_mean"]) for r in p4rows]),
                "mean_within_run_keff_sd": mean([float(r["keff_std_dev_within_run"]) for r in p4rows]),
                "mean_fission_rate_peaking_factor": mean(f4),
                "between_seed_sd_fission_peaking_factor": sample_sd(f4),
                "risk_adjusted_score": mean(f4) + RISK_WEIGHT * sample_sd(f4),
            }
            p5[layout] = {
                "n_independent_seeds": len(f5),
                "mean_keff": mean([float(r["keff_mean"]) for r in p5rows]),
                "mean_within_run_keff_sd": mean([float(r["keff_std_dev_within_run"]) for r in p5rows]),
                "mean_fission_rate_peaking_factor": mean(f5),
                "between_seed_sd_fission_peaking_factor": sample_sd(f5),
            }
        point = min(sorted(EXPECTED_LAYOUTS), key=lambda x: (p4[x]["mean_fission_rate_peaking_factor"], x))
        cbpfr = min(sorted(EXPECTED_LAYOUTS), key=lambda x: (p4[x]["risk_adjusted_score"], x))
        margin = mean([p4[x]["between_seed_sd_fission_peaking_factor"] for x in sorted(EXPECTED_LAYOUTS)])
        uniform = min(sorted(EXPECTED_LAYOUTS), key=lambda x: (p4[x]["mean_fission_rate_peaking_factor"] + margin, x))
        test_means = {layout: p5[layout]["mean_fission_rate_peaking_factor"] for layout in sorted(EXPECTED_LAYOUTS)}
        best_heldout = min(test_means, key=lambda x: (test_means[x], x))
        boot = bootstrap_comparison(screening, heldout)
        method_report = {
            "P4_screening_summaries": p4,
            "P5_independent_high_budget_summaries": p5,
            "selected_layouts_from_P4": {
                "point_estimate": point,
                "cbpfr_risk_adjusted": cbpfr,
                "uniform_margin": uniform,
                "random_feasible": "distribution over all six layouts",
                "qubo_feasibility_only": "distribution over all six equal-energy feasible layouts",
            },
            "P5_heldout_evaluation": {
                "lowest_observed_high_budget_mean_proxy": best_heldout,
                "mean_proxy_by_layout": test_means,
                "observed_regret_by_selected_layout": {
                    "point_estimate": test_means[point] - test_means[best_heldout],
                    "cbpfr_risk_adjusted": test_means[cbpfr] - test_means[best_heldout],
                    "uniform_margin": test_means[uniform] - test_means[best_heldout],
                },
            },
            "bootstrap_comparison": boot,
        }
        physical_comparison.update({
            "status": "EXPLORATORY_HELDOUT_EVIDENCE; PHYSICAL_FEASIBILITY_NOT_ESTABLISHED",
            "risk_score": "mean P4 fission-peaking proxy + 1.0 × between-seed SD; descriptive, not a calibrated confidence bound",
            "uniform_margin_note": "A common additive margin cannot change a single-objective ranking; it should match the point-estimate selection apart from ties.",
            "qubo_only_note": "The two-MOX cardinality QUBO has equal energy for all six feasible layouts; without a physical objective its output is not a physical ranking, so the baseline is uniform sampling over feasible layouts.",
            "P4_vs_P5": "P4 screening and P5 held-out evaluation use disjoint seed-base groups; the bootstrap is exploratory because only three seed observations per layout are available.",
            "method_comparison": method_report,
            "claims": {
                "cbpfr_physical_superiority": "NOT_ESTABLISHED_BY_DESIGN; only exploratory held-out proxy comparison is produced",
                "physical_feasibility": "BLOCKED until a defensible design-specific k_eff band and independent model/tally review exist",
                "absolute_power_or_safety": "NOT_CLAIMED",
                "legacy_burnup_qubo_mapping": "NO_DEFENSIBLE_MAPPING_FOUND",
            },
        })

    rows.sort(key=lambda r: (r["phase"], r["layout_signature"], int(r["seed"] or -1)))
    return {
        "schema_version": "1.0",
        "study_id": "CBPFR-C5G7-P4-P5-heldout-effectiveness-pilot-2026-10-18",
        "status": "EVIDENCE_INTEGRITY_PASS_INTERPRETATION_OPEN" if integrity_pass else "INCOMPLETE_OR_AUDIT_FAILURE",
        "planned_runs": 36,
        "observed_run_records": len(rows),
        "phase_counts": phase_counts,
        "per_candidate_run_counts": count_per_candidate,
        "integrity_checks": integrity_checks,
        "winner_selected_for_physical_use": False,
        "physical_comparison": physical_comparison,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-root", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    args = parser.parse_args()
    if not args.artifacts_root.is_dir():
        parser.error(f"artifact root does not exist: {args.artifacts_root}")
    if args.outdir.exists():
        parser.error(f"refusing to overwrite existing output: {args.outdir}")
    rows = collect_runs(args.artifacts_root.resolve())
    report = aggregate(rows)
    args.outdir.mkdir(parents=True)
    (args.outdir / "p45_campaign_audit.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    with (args.outdir / "p45_run_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = list(rows[0].keys()) if rows else ["phase", "candidate_id", "case_status"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in report["rows"]:
            writer.writerow(row)
    lines = [
        "# C5G7 P-4/P-5 physical-effectiveness pilot",
        "",
        f"**Campaign evidence status:** `{report['status']}`",
        "",
        "This report uses P-4 intermediate-budget screening data to choose candidates and P-5 high-budget data with independent seed bases as held-out evaluation. It does not declare a physically feasible or safe design.",
        "",
        "## Integrity gates",
        "",
        "| Check | Result |",
        "|---|---|",
    ]
    lines.extend(f"| {key} | {'PASS' if value else 'FAIL'} |" for key, value in report["integrity_checks"].items())
    lines.extend(["", "## Selection-effectiveness comparison", ""])
    comparison = report["physical_comparison"]
    if "method_comparison" not in comparison:
        lines.append("Incomplete artifacts: comparison was not computed.")
    else:
        method = comparison["method_comparison"]
        lines.extend([
            "| Method | Chosen from P-4 | P-5 observed mean proxy | Observed regret |",
            "|---|---|---:|---:|",
        ])
        p5 = method["P5_independent_high_budget_summaries"]
        heldout_regret = method["P5_heldout_evaluation"]["observed_regret_by_selected_layout"]
        for name, label in (("point_estimate", "Point estimate"),
                            ("cbpfr_risk_adjusted", "CB-PFR risk-adjusted"),
                            ("uniform_margin", "Uniform margin")):
            layout = method["selected_layouts_from_P4"][name]
            score = p5[layout]["mean_fission_rate_peaking_factor"]
            lines.append(f"| {label} | {layout} | {score:.6g} | {heldout_regret[name]:.6g} |")
        boot = method["bootstrap_comparison"]
        diff = boot["paired_cbpfr_minus_point_regret"]
        interval = diff["percentile_95_interval"]
        lines.extend([
            "",
            f"Bootstrap mean regret difference (CB-PFR − point estimate): {diff['mean']:.6g}.",
            f"Exploratory 95% percentile interval: [{interval[0]:.6g}, {interval[1]:.6g}].",
            "",
            "The resampling uses only three seed-level observations per layout and is a pilot uncertainty analysis, not a generalizable superiority test.",
        ])
    lines.extend([
        "",
        "## Interpretation limits",
        "",
        "- Lower fission-peaking proxy indicates a less peaked relative fission-rate shape under the declared exploratory objective. It is not absolute power or a safety metric.",
        "- No design-specific acceptable k_eff band was supplied. Physical-feasibility filtering therefore remains blocked.",
        "- Within-run k-effective uncertainty and between-seed variability are recorded separately; correlated mesh-tally uncertainty is not yet propagated to the peaking objective.",
        "- The point-estimate and uniform-additive-margin rules should select the same layout except for ties; the material-count QUBO is equal-energy across all six feasible layouts.",
        "- A passing artifact audit is not a convergence certificate or official OECD/NEA benchmark acceptance.",
        "- A negative CB-PFR-minus-point regret difference favours CB-PFR on this held-out proxy; generalizable physical superiority still requires multiple independent selection/evaluation cohorts and approved acceptance constraints.",
        "",
        "Machine-readable outputs: `p45_campaign_audit.json` and `p45_run_summary.csv`.",
        "",
    ])
    (args.outdir / "P45_PHYSICAL_EFFECTIVENESS_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "run_records": report["observed_run_records"],
        "phase_counts": report["phase_counts"],
        "outdir": str(args.outdir),
    }, indent=2))
    return 0 if report["status"] == "EVIDENCE_INTEGRITY_PASS_INTERPRETATION_OPEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
