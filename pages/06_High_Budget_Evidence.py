"""High-budget C5G7 repeated-run evidence viewer for ReactorQ Studio."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from cbpfr.dashboard_ui import (
    CYAN, MUTED, ORANGE, apply_workstation_style, base_layout,
    render_header, render_page_intro,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = ROOT / "results" / "c5g7_high_budget_2026-10-12" / "run_level_evidence.json"
EXPECTED_LAYOUTS = {"MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM"}
GROUP_EDGES_CSV = "1e-05;0.0635;10.0;100.0;1000.0;500000.0;1000000.0;20000000.0"
T_CRITICAL_DF2_95 = 4.3026527299


def load_and_audit(path: Path) -> tuple[dict, pd.DataFrame, list[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    runs = pd.DataFrame(payload.get("runs", []))
    issues: list[str] = []
    required = {
        "round", "layout_signature", "seed", "keff_mean", "keff_std_dev",
        "fission_rate_peaking_factor", "statepoint_sha256", "mgxs_sha256",
        "group_structure_audit", "batches", "inactive", "particles_per_batch", "threads",
    }
    missing = sorted(required - set(runs.columns))
    if missing:
        return payload, runs, [f"Missing required fields: {', '.join(missing)}"]
    if len(runs) != 18:
        issues.append(f"Expected 18 run rows; found {len(runs)}.")
    if set(runs["layout_signature"].astype(str)) != EXPECTED_LAYOUTS:
        issues.append("The layout set does not match the six expected 2×2 assignments.")
    counts = runs.groupby("layout_signature").size().to_dict()
    if counts != {layout: 3 for layout in EXPECTED_LAYOUTS}:
        issues.append(f"Expected three runs per layout; observed {counts}.")
    if runs["seed"].nunique() != len(runs):
        issues.append("Run seeds are not unique.")
    if runs["statepoint_sha256"].nunique() != len(runs):
        issues.append("Statepoint hashes are not unique.")
    if runs["mgxs_sha256"].nunique() != 1:
        issues.append("The runs do not share a single MGXS hash.")
    if not runs["group_structure_audit"].astype(str).eq("PASS").all():
        issues.append("At least one corrected-group audit is not PASS.")
    for column, expected in {
        "batches": 5000, "inactive": 500, "particles_per_batch": 5000, "threads": 2,
    }.items():
        values = pd.to_numeric(runs[column], errors="coerce").dropna().unique()
        if len(values) != 1 or values[0] != expected:
            issues.append(f"Unexpected or inconsistent compute setting: {column}.")
    expected_boundaries = [0.00001, 0.0635, 10, 100, 1000, 500000, 1000000, 20000000]
    if payload.get("expected_group_boundaries_eV") != expected_boundaries:
        issues.append("The declared corrected seven-group boundary contract is missing or changed.")
    if payload.get("physical_validation_certified") is not False:
        issues.append("Evidence metadata must explicitly keep physical validation uncertified.")
    if payload.get("winner_selected") is not False:
        issues.append("Evidence metadata must not preselect a winner.")
    for col in ("keff_mean", "keff_std_dev", "fission_rate_peaking_factor"):
        runs[col] = pd.to_numeric(runs[col], errors="coerce")
        if runs[col].isna().any() or not np.isfinite(runs[col]).all():
            issues.append(f"Metric {col} contains missing or non-finite values.")
    if runs["keff_std_dev"].le(0).any():
        issues.append("Reported within-run keff standard deviations must be positive.")
    # These two fields are deterministic schema adapters required by the audited CLI.
    # They are derived from the declared six-layout encoding and group contract, not guessed measurements.
    runs["candidate_id"] = "c5g7-2x2-" + runs["layout_signature"].astype(str)
    runs["mgxs_energy_group_boundaries_eV"] = GROUP_EDGES_CSV
    return payload, runs, issues


def summarize_runs(runs: pd.DataFrame) -> pd.DataFrame:
    records = []
    for layout, group in runs.groupby("layout_signature"):
        record = {"layout_signature": layout, "n_runs": len(group)}
        for metric in ("keff_mean", "fission_rate_peaking_factor"):
            values = group[metric].astype(float)
            mean = float(values.mean())
            sd = float(values.std(ddof=1)) if len(values) > 1 else 0.0
            half_width = T_CRITICAL_DF2_95 * sd / math.sqrt(len(values)) if len(values) > 1 else float("nan")
            record[f"{metric}_mean"] = mean
            record[f"{metric}_sd_between_runs"] = sd
            record[f"{metric}_ci95_low"] = mean - half_width
            record[f"{metric}_ci95_high"] = mean + half_width
        record["mean_reported_within_run_keff_sd"] = float(group["keff_std_dev"].mean())
        record["seeds"] = ", ".join(str(int(x)) for x in sorted(group["seed"]))
        records.append(record)
    return pd.DataFrame(records).sort_values("fission_rate_peaking_factor_mean").reset_index(drop=True)


st.set_page_config(page_title="CB-PFR · High-Budget Evidence", page_icon="⚛", layout="wide")
apply_workstation_style()
render_header("High-Budget Evidence", "18 RUNS · THREE INDEPENDENT SEED ROUNDS")
render_page_intro(
    "C5G7 / RUN-LEVEL EVIDENCE",
    "High-Budget Study Inspector",
    "Inspect the archived 18-run C5G7 study, compare repeated-run variation, and export the evidence used by downstream CB-PFR analysis.",
)

if not EVIDENCE_PATH.is_file():
    st.error(f"Committed run evidence was not found: {EVIDENCE_PATH.relative_to(ROOT)}")
    st.stop()

try:
    payload, runs, issues = load_and_audit(EVIDENCE_PATH)
except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
    st.error(f"Evidence could not be loaded: {exc}")
    st.stop()

evidence_hash = hashlib.sha256(EVIDENCE_PATH.read_bytes()).hexdigest()
summary = summarize_runs(runs) if not runs.empty else pd.DataFrame()

if issues:
    st.error("Evidence contract blocked — do not use these data for candidate selection.")
    for issue in issues:
        st.write(f"- {issue}")
else:
    st.success("Local evidence contract passed: 18 unique run records, six layouts, three seeds per layout, common settings and matching group-audit labels.")

st.markdown(
    '<div class="evidence-note"><b>Interpretation boundary</b> · Integrity and repeated-run summaries are not a benchmark-validation certificate. '
    'The confidence intervals below are descriptive Student-t intervals across only three independent seed runs per layout. '
    'They do not establish convergence, physical superiority, or reactor safety. No winner is approved.</div>',
    unsafe_allow_html=True,
)

a, b, c, d = st.columns(4)
a.metric("Run records", f"{len(runs)} / 18")
b.metric("Candidate layouts", str(runs["layout_signature"].nunique()) if not runs.empty else "—")
c.metric("Runs per layout", "3" if not issues else "Check audit")
d.metric("Histories / run (nominal)", "25.0M")

tab_summary, tab_runs, tab_provenance = st.tabs(["Candidate comparison", "Run-level inspection", "Provenance & limits"])

with tab_summary:
    st.markdown("### Between-run estimates")
    st.caption("The ranking shown is descriptive and sorted by mean fission-rate peaking proxy (ascending). It is not an approved design ranking.")
    if not summary.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=summary["fission_rate_peaking_factor_mean"],
            y=summary["layout_signature"],
            mode="markers",
            name="Mean",
            marker={"size": 11, "color": CYAN, "line": {"color": "#dceaff", "width": 0.8}},
            error_x={
                "type": "data",
                "array": summary["fission_rate_peaking_factor_ci95_high"] - summary["fission_rate_peaking_factor_mean"],
                "arrayminus": summary["fission_rate_peaking_factor_mean"] - summary["fission_rate_peaking_factor_ci95_low"],
                "visible": True, "color": MUTED, "thickness": 1.5, "width": 5,
            },
            customdata=summary[["fission_rate_peaking_factor_sd_between_runs", "n_runs"]].to_numpy(),
            hovertemplate="Layout %{y}<br>Mean proxy %{x:.6f}<br>Between-run SD %{customdata[0]:.6f}<br>Independent runs %{customdata[1]}<extra></extra>",
        ))
        base_layout(fig, height=390)
        fig.update_layout(xaxis_title="Fission-rate peaking proxy (mean ± descriptive 95% t interval)", yaxis_title="", showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

        left, right = st.columns(2, gap="large")
        with left:
            st.markdown("#### k-effective by layout")
            fig_k = go.Figure()
            fig_k.add_trace(go.Scatter(
                x=summary["keff_mean_mean"], y=summary["layout_signature"], mode="markers",
                marker={"size": 10, "color": ORANGE},
                error_x={
                    "type": "data",
                    "array": summary["keff_mean_ci95_high"] - summary["keff_mean_mean"],
                    "arrayminus": summary["keff_mean_mean"] - summary["keff_mean_ci95_low"],
                    "visible": True, "color": MUTED, "width": 4,
                },
                hovertemplate="Layout %{y}<br>Mean k-effective %{x:.7f}<extra></extra>",
            ))
            base_layout(fig_k, height=330)
            fig_k.update_layout(xaxis_title="Reported k-effective mean ± descriptive 95% t interval", yaxis_title="")
            st.plotly_chart(fig_k, use_container_width=True, config={"displaylogo": False})
        with right:
            st.markdown("#### Between-run spread")
            spread = summary.sort_values("fission_rate_peaking_factor_sd_between_runs")
            fig_sd = go.Figure(go.Bar(
                x=spread["fission_rate_peaking_factor_sd_between_runs"],
                y=spread["layout_signature"], orientation="h",
                marker_color=CYAN,
                hovertemplate="Layout %{y}<br>Sample SD across runs %{x:.6f}<extra></extra>",
            ))
            base_layout(fig_sd, height=330)
            fig_sd.update_layout(xaxis_title="Sample SD of fission-rate peaking proxy", yaxis_title="")
            st.plotly_chart(fig_sd, use_container_width=True, config={"displaylogo": False})

        display = summary[[
            "layout_signature", "n_runs", "fission_rate_peaking_factor_mean",
            "fission_rate_peaking_factor_sd_between_runs", "fission_rate_peaking_factor_ci95_low",
            "fission_rate_peaking_factor_ci95_high", "keff_mean_mean",
            "keff_mean_ci95_low", "keff_mean_ci95_high", "mean_reported_within_run_keff_sd", "seeds",
        ]].rename(columns={
            "layout_signature": "Layout", "n_runs": "Runs",
            "fission_rate_peaking_factor_mean": "Fission proxy mean",
            "fission_rate_peaking_factor_sd_between_runs": "Fission proxy between-run SD",
            "fission_rate_peaking_factor_ci95_low": "Fission CI 95% low",
            "fission_rate_peaking_factor_ci95_high": "Fission CI 95% high",
            "keff_mean_mean": "k-effective mean", "keff_mean_ci95_low": "k-effective CI 95% low",
            "keff_mean_ci95_high": "k-effective CI 95% high",
            "mean_reported_within_run_keff_sd": "Mean reported within-run keff SD",
        })
        st.dataframe(display, use_container_width=True, hide_index=True)
        st.download_button(
            "Export candidate summary CSV",
            summary.to_csv(index=False).encode("utf-8"),
            "cbpfr_high_budget_candidate_summary.csv", "text/csv",
        )

with tab_runs:
    st.markdown("### Individual transport runs")
    layouts = sorted(runs["layout_signature"].unique())
    selected_layouts = st.multiselect("Filter layouts", layouts, default=layouts)
    filtered = runs[runs["layout_signature"].isin(selected_layouts)].sort_values(["layout_signature", "round"])
    metric = st.selectbox("Metric", ["fission_rate_peaking_factor", "keff_mean", "keff_std_dev"])
    fig_run = go.Figure()
    for layout in selected_layouts:
        group = filtered[filtered["layout_signature"] == layout]
        fig_run.add_trace(go.Scatter(
            x=group["round"].astype(str), y=group[metric], mode="lines+markers",
            name=layout, marker={"size": 8},
            customdata=group[["seed", "statepoint_sha256"]].to_numpy(),
            hovertemplate="Layout " + layout + "<br>Seed %{customdata[0]}<br>Value %{y:.7g}<br>Statepoint SHA-256 %{customdata[1]}<extra></extra>",
        ))
    base_layout(fig_run, height=400)
    fig_run.update_layout(xaxis_title="Seed round base", yaxis_title=metric.replace("_", " ").title())
    st.plotly_chart(fig_run, use_container_width=True, config={"displaylogo": False})
    st.dataframe(
        filtered[["round", "candidate_id", "layout_signature", "seed", "keff_mean", "keff_std_dev", "fission_rate_peaking_factor", "statepoint_sha256", "mgxs_sha256", "group_structure_audit", "mgxs_energy_group_boundaries_eV", "batches", "inactive", "particles_per_batch", "threads"]],
        use_container_width=True, hide_index=True,
    )
    st.download_button(
        "Export filtered run records CSV",
        filtered.to_csv(index=False).encode("utf-8"),
        "cbpfr_high_budget_run_records.csv", "text/csv",
    )

with tab_provenance:
    st.markdown("### Reproducibility record")
    st.code(f"Evidence file SHA-256\n{evidence_hash}", language="text")
    st.json({
        "schema_version": payload.get("schema_version"),
        "source_workflow_run": payload.get("source_workflow_run"),
        "source_artifact": payload.get("source_artifact"),
        "source_artifact_id": payload.get("source_artifact_id"),
        "upstream_commit": payload.get("upstream_commit"),
        "declared_status": payload.get("status"),
        "physical_validation_certified": payload.get("physical_validation_certified"),
        "convergence_certified": payload.get("convergence_certified"),
        "winner_selected": payload.get("winner_selected"),
        "expected_group_boundaries_eV": payload.get("expected_group_boundaries_eV"),
        "common_settings": {"batches": 5000, "inactive": 500, "particles_per_batch": 5000, "threads": 2},
        "unique_statepoint_hashes": bool(runs["statepoint_sha256"].nunique() == len(runs)),
        "single_mgxs_hash": runs["mgxs_sha256"].nunique() == 1,
        "integrity_issues": issues,
    })
    st.markdown("#### Download source records")
    st.download_button(
        "Download compact run evidence JSON",
        EVIDENCE_PATH.read_bytes(),
        "cbpfr_c5g7_high_budget_run_level_evidence.json",
        "application/json",
    )
    st.download_button(
        "Download integrated-pipeline CSV",
        runs.to_csv(index=False).encode("utf-8"),
        "cbpfr_c5g7_high_budget_pipeline_input.csv",
        "text/csv",
    )
    st.caption("The CSV adapter adds the deterministic candidate ID and declared corrected-group boundary string required by the CLI. It preserves the recorded run values and hashes unchanged.")
    st.link_button("Open source GitHub Actions run", payload["source_workflow_run"])

st.markdown("---")
st.caption("C5G7 high-budget study · 6 layouts × 3 independent seed rounds · 5,000 batches × 5,000 particles/run. The raw HDF5 statepoints remain in the linked workflow artifact.")
