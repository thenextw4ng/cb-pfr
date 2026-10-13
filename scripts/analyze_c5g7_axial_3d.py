#!/usr/bin/env python3
"""Create an evidence-bounded scalar C5G7 3-D reference comparison report.

This compares one reported OpenMC eigenvalue with the OECD/NEA reference only.
It deliberately does not produce an overall benchmark pass/fail or compare pin power.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

REFERENCE = {
    "benchmark": "OECD/NEA C5G7 3-D MOX fuel assembly benchmark",
    "report": "NEA/NSC/DOC(2003)16",
    "table": "Table 10, 3-D multi-group reference solutions",
    "url": "https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/nsc-doc2003-16.pdf",
    "k_eff": 1.183810,
    "relative_confidence_half_width_percent": {"68": 0.003, "98": 0.008, "99.8": 0.010},
}

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read JSON evidence {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return value

def parse_openmc_log(path: Path) -> dict:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ValueError(f"Cannot read OpenMC log {path}: {exc}") from exc
    numeric = r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
    match = re.search(r"Combined\s+k-effective\s*=\s*" + numeric + r"\s*\+/-\s*" + numeric, raw, re.I)
    if not match:
        raise ValueError("OpenMC log lacks a parseable Combined k-effective = mean +/- SD line.")
    leak = re.search(r"Leakage\s+Fraction\s*=\s*" + numeric + r"\s*\+/-\s*" + numeric, raw, re.I)
    return {
        "k_eff_mean": float(match.group(1)),
        "k_eff_reported_sd": float(match.group(2)),
        "leakage_fraction_mean": float(leak.group(1)) if leak else None,
        "leakage_fraction_reported_sd": float(leak.group(2)) if leak else None,
        "log_sha256": sha256_file(path),
        "log_path": str(path),
    }

def analyze(candidate_root: Path, openmc_log: Path, output_dir: Path) -> tuple[dict, str]:
    candidate_root, openmc_log = candidate_root.resolve(), openmc_log.resolve()
    manifest_path = candidate_root / "AXIAL_3D_INPUT_MANIFEST.json"
    audit_path = candidate_root / "AXIAL_3D_INPUT_AUDIT.json"
    output_root = candidate_root / "model" / "3d" / "axial-3d-export"
    summary_path = output_root / "AXIAL_3D_STATEPOINT_SUMMARY.json"
    tally_path = output_root / "axial_tally_3d.npz"
    manifest, audit, state = read_json(manifest_path), read_json(audit_path), read_json(summary_path)
    log = parse_openmc_log(openmc_log)
    if audit.get("status") != "generated_3d_inputs_passed_structural_audit":
        raise ValueError("The generated 3-D input audit did not pass.")
    if state.get("status") != "3d_openmc_statepoint_mesh_exported":
        raise ValueError("A real 3-D statepoint summary is required.")
    if manifest.get("candidate_id") != audit.get("candidate_id"):
        raise ValueError("Candidate ID mismatch between input manifest and geometry audit.")
    if state.get("mesh", {}).get("dimension_xyz") != [51, 51, 30] or not tally_path.is_file():
        raise ValueError("Expected an actual 51 x 51 x 30 mesh and NPZ export.")
    settings, run = audit.get("settings", {}), state.get("statepoint", {})
    for key, field in (("batches", "n_batches"), ("inactive", "n_inactive"),
                       ("particles_per_batch", "n_particles"), ("seed", "seed")):
        if settings.get(key) != run.get(field):
            raise ValueError(f"Run provenance mismatch for {key}: {settings.get(key)!r} != {run.get(field)!r}")

    reference = float(REFERENCE["k_eff"])
    calculated, calc_sd = log["k_eff_mean"], log["k_eff_reported_sd"]
    # Table 10 gives confidence half-widths relative to k_eff. Use the 68% half-width
    # as an approximate 1-sigma reference uncertainty solely for an indicative comparison.
    ref_sd = reference * REFERENCE["relative_confidence_half_width_percent"]["68"] / 100.0
    combined_sd = math.sqrt(calc_sd ** 2 + ref_sd ** 2)
    delta = calculated - reference
    z_combined = delta / combined_sd if combined_sd else None
    half95 = 1.96 * combined_sd
    lo, hi = delta - half95, delta + half95
    active = int(settings["batches"]) - int(settings["inactive"])
    histories = active * int(settings["particles_per_batch"])
    scalar_close = z_combined is not None and abs(z_combined) <= 2.0
    enough_budget = active >= 1000
    status = (
        "preliminary_scalar_consistency_not_a_benchmark_pass" if enough_budget and scalar_close
        else "scalar_difference_requires_review" if enough_budget
        else "smoke_only_no_benchmark_conclusion"
    )
    scores = state.get("score_summary", {})
    report = {
        "schema_version": 1,
        "status": status,
        "scope": "scalar eigenvalue consistency only; not a full benchmark verification",
        "candidate": {"candidate_id": manifest.get("candidate_id"), "layout_signature": manifest.get("layout_signature")},
        "reference": {
            **REFERENCE,
            "absolute_68pct_half_width_approx": ref_sd,
            "uncertainty_interpretation": "Approximate the 68% reference confidence half-width as one sigma for a diagnostic combined-uncertainty check.",
        },
        "calculation": log,
        "run": {
            "batches": int(settings["batches"]), "inactive_batches": int(settings["inactive"]),
            "active_batches": active, "particles_per_batch": int(settings["particles_per_batch"]),
            "total_active_histories": histories, "seed": int(settings["seed"]),
            "statepoint_n_realizations": int(run["n_realizations"]), "statepoint_sha256": run["sha256"],
            "npz_sha256": sha256_file(tally_path),
            "geometry_xml_sha256": audit["model_files"]["geometry.xml"]["sha256"],
            "materials_xml_sha256": audit["model_files"]["materials.xml"]["sha256"],
            "settings_xml_sha256": audit["model_files"]["settings.xml"]["sha256"],
            "tallies_xml_sha256": audit["model_files"]["tallies.xml"]["sha256"],
            "mgxs_sha256": audit["model_files"]["mgxs.h5"]["sha256"],
            "source_archive_sha256": manifest.get("source", {}).get("archive_sha256"),
        },
        "comparison": {
            "calculated_k_eff": calculated, "calculated_reported_sd": calc_sd,
            "reference_k_eff": reference, "delta_k_eff": delta, "delta_pcm": delta * 100000.0,
            "relative_bias_percent": delta / reference * 100.0,
            "combined_statistical_sd_approx": combined_sd, "difference_in_combined_sd_approx": z_combined,
            "approx_difference_95pct_interval": [lo, hi],
            "approx_95pct_interval_includes_zero": lo <= 0.0 <= hi,
        },
        "spatial_tally_uncertainty": {
            name: {
                "nonzero_mean_bins": value.get("nonzero_mean_bin_count"),
                "relative_error_percent_median_positive_bins": value.get("relative_error_percent_median_positive_bins"),
                "relative_error_percent_p95_positive_bins": value.get("relative_error_percent_p95_positive_bins"),
            } for name, value in scores.items()
        },
        "evidence": {
            "input_audit_status": audit.get("status"), "statepoint_status": state.get("status"),
            "input_manifest_sha256": sha256_file(manifest_path), "input_audit_sha256": sha256_file(audit_path),
            "statepoint_summary_sha256": sha256_file(summary_path),
        },
        "limitations": [
            "Close scalar k-effective consistency is not a full OECD/NEA benchmark pass.",
            "Pin-wise and assembly-wise fission-power distributions have not been compared with reference data.",
            "The mesh tally is source-normalized, not absolute-power normalized.",
            "The combined-uncertainty calculation is approximate and assumes the 68% reference half-width is one sigma.",
            "One candidate and one random seed do not establish ranking reliability or repeatability.",
            "No safety, burnup/depletion, thermal-hydraulic, or design-suitability claim follows.",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "AXIAL_3D_BENCHMARK_CHECK.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    spatial = report["spatial_tally_uncertainty"]
    def stat(name: str, key: str) -> str:
        value = spatial.get(name, {}).get(key)
        return "not available" if value is None else f"{float(value):.2f}%"
    md = f"""# C5G7 3-D scalar benchmark consistency check

**Status:** {status}

This is a bounded comparison of one OpenMC 3-D eigenvalue against the OECD/NEA reference. It is not a full benchmark pass.

## Calculation

- Candidate: {manifest.get("candidate_id")} ({manifest.get("layout_signature")})
- Run: {settings["batches"]} batches, {settings["inactive"]} inactive, {settings["particles_per_batch"]:,} particles/batch, {histories:,} active histories, seed {settings["seed"]}.
- Calculated k-effective: **{calculated:.8f} ± {calc_sd:.8f}** (reported OpenMC statistical SD).
- OECD/NEA reference k-effective: **{reference:.6f}** (NEA/NSC/DOC(2003)16, Table 10).
- Difference: **{delta:+.8f}** ({delta * 100000:+.1f} pcm; relative bias {delta / reference * 100:+.5f}%).
- Difference / approximate combined statistical SD: **{z_combined:+.2f}**.
- Approximate 95% interval for the difference: **[{lo:+.8f}, {hi:+.8f}]**; includes zero: **{str(lo <= 0 <= hi).lower()}**.
- Reference: [OECD/NEA NEA/NSC/DOC(2003)16, Table 10]({REFERENCE["url"]}).

## Voxelwise mesh uncertainty

| Score | Positive-mean bins | Median relative MC SE | 95th percentile relative MC SE |
|---|---:|---:|---:|
| Flux | {spatial.get("flux", {}).get("nonzero_mean_bins", 0):,} | {stat("flux", "relative_error_percent_median_positive_bins")} | {stat("flux", "relative_error_percent_p95_positive_bins")} |
| Fission | {spatial.get("fission", {}).get("nonzero_mean_bins", 0):,} | {stat("fission", "relative_error_percent_median_positive_bins")} | {stat("fission", "relative_error_percent_p95_positive_bins")} |
| Nu-fission | {spatial.get("nu-fission", {}).get("nonzero_mean_bins", 0):,} | {stat("nu-fission", "relative_error_percent_median_positive_bins")} | {stat("nu-fission", "relative_error_percent_p95_positive_bins")} |

These are descriptive voxel-level sampling statistics; the high tail can reflect low-importance bins and is not a global convergence gate.

## Interpretation boundary

For this one candidate and seed, the eigenvalue is close to the reference at the level of the approximate combined statistical uncertainty. This supports a **preliminary scalar consistency check** only. Full benchmark validation still requires a comparison of normalized pin-wise and assembly-wise fission-power distributions and independent-seed/repeatability evidence.

The tally is source-normalized, not absolute reactor power. This result does not establish the physically best candidate, quantum advantage, reactor safety, burnup/depletion, or thermal-hydraulic suitability.

## Provenance

- Statepoint SHA-256: {run["sha256"]}
- NPZ SHA-256: {sha256_file(tally_path)}
- Geometry XML SHA-256: {audit["model_files"]["geometry.xml"]["sha256"]}
- Materials XML SHA-256: {audit["model_files"]["materials.xml"]["sha256"]}
- Settings XML SHA-256: {audit["model_files"]["settings.xml"]["sha256"]}
- Tallies XML SHA-256: {audit["model_files"]["tallies.xml"]["sha256"]}
- MGXS SHA-256: {audit["model_files"]["mgxs.h5"]["sha256"]}
- Source archive SHA-256: {manifest.get("source", {}).get("archive_sha256")}

Machine-readable details: AXIAL_3D_BENCHMARK_CHECK.json.
"""
    (output_dir / "AXIAL_3D_BENCHMARK_CHECK.md").write_text(md, encoding="utf-8")
    return report, md

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--openmc-log", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    report, _ = analyze(args.candidate_root, args.openmc_log, args.output_dir)
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
