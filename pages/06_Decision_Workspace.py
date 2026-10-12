"""Evidence-aware decision workspace; intentionally does not auto-approve a physical design."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from cbpfr.dashboard_ui import (
    BG, PANEL, LINE, TEXT, MUTED, CYAN, ORANGE, GREEN, BLUE,
    apply_workstation_style, base_layout, candidate_label, load_smoke,
    render_header, render_page_intro, render_workspace_sidebar,
)

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "results" / "c5g7_layout_smoke_2026-10-10" / "candidate_summary.csv"

st.set_page_config(page_title="CB-PFR · Decision Workspace", page_icon="⚛", layout="wide")
apply_workstation_style()
render_header("Decision Workspace", "EVIDENCE REVIEW · NO AUTOMATIC WINNER")
df = load_smoke().sort_values("candidate_id").reset_index(drop=True)
render_workspace_sidebar("Decision Workspace", df)
render_page_intro(
    "DECISION WORKSPACE / CANDIDATE TRADE-OFFS",
    "Candidate Decision Workspace",
    "Compare recorded candidate-level indicators, capture review gates, and export a traceable decision record. This page does not certify physical acceptability or choose a reactor design automatically.",
)

st.markdown(
    '<div class="evidence-note"><b>Decision gate: BLOCKED</b> · Available records are low-budget exploratory smoke data. They are not benchmark-grade evidence; the interface deliberately leaves physical approval to an independently reviewed protocol.</div>',
    unsafe_allow_html=True,
)

labels = [candidate_label(row) for _, row in df.iterrows()]
selected_label = st.selectbox("Candidate under review", labels, index=next((i for i, row in df.iterrows() if bool(row["canonical_reference"])), 0))
selected = df.loc[[candidate_label(row) == selected_label for _, row in df.iterrows()]].iloc[0]

a, b, c, d = st.columns(4)
a.metric("Candidate", str(selected["candidate_id"]).replace("c5g7-2x2-", ""))
b.metric("k-effective mean", f'{float(selected["keff_mean"]):.6f}')
c.metric("Reported within-run σ", f'{float(selected["keff_std_dev"]):.6f}')
d.metric("Relative SD", f'{float(selected["keff_relative_sd_percent"]):.4f}%')

left, right = st.columns([1.25, 1], gap="large")
with left:
    st.markdown("### Recorded trade-off map")
    st.caption("Axes are repository-provided aggregate scores. Their physical units and decision thresholds must be verified before using them as acceptance criteria.")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["aggregate_flux_score"], y=df["aggregate_fission_score"],
        mode="markers+text",
        text=[candidate_label(row) for _, row in df.iterrows()],
        textposition="top center",
        marker=dict(
            size=[18 if candidate_label(row) == selected_label else 12 for _, row in df.iterrows()],
            color=[CYAN if bool(row["canonical_reference"]) else BLUE for _, row in df.iterrows()],
            line=dict(color=TEXT, width=[1.8 if candidate_label(row) == selected_label else 0.6 for _, row in df.iterrows()]),
        ),
        customdata=df[["layout_signature", "keff_mean", "keff_std_dev", "seed"]].to_numpy(),
        hovertemplate="<b>%{text}</b><br>Layout %{customdata[0]}<br>Aggregate flux score %{x:.5g}<br>Aggregate fission score %{y:.5g}<br>k-eff %{customdata[1]:.7f} ± %{customdata[2]:.5g}<br>Seed %{customdata[3]}<extra></extra>",
    ))
    base_layout(fig, height=430)
    fig.update_layout(xaxis_title="Recorded aggregate flux score", yaxis_title="Recorded aggregate fission score")
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
with right:
    st.markdown("### Evidence gates")
    gates = [
        ("QUBO ↔ material mapping documented", False),
        ("Independent repeated runs per candidate", False),
        ("Design-specific k-effective acceptance band approved", False),
        ("Spatial tally mapping independently reviewed", False),
        ("Convergence and uncertainty protocol passed", False),
        ("Independent benchmark comparison accepted", False),
    ]
    for label, default in gates:
        st.checkbox(label, value=default, key="gate_" + str(abs(hash(label))))
    st.markdown(
        '<div class="scientific-panel"><div class="workspace-kicker">Current disposition</div>'
        '<div style="font-size:1.1rem;font-weight:700;color:#f5bb62;margin:.35rem 0">HOLD · NOT PHYSICALLY APPROVED</div>'
        '<div class="small-muted">Checking boxes records reviewer input only. It does not verify the underlying evidence or change the scientific gate automatically.</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("### Review note")
review_note = st.text_area("Reviewer rationale / outstanding issues", value="Exploratory smoke evidence only. No winner declared; require approved physical acceptance criteria and reviewed spatial mapping.", height=100)
if st.button("Export decision review record", type="primary"):
    checklist = {label: bool(st.session_state.get("gate_" + str(abs(hash(label))), False)) for label, _ in gates}
    payload = {
        "schema_version": "1.0",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_id": str(selected["candidate_id"]),
        "layout_signature": str(selected["layout_signature"]),
        "source_csv": str(CSV.relative_to(ROOT)),
        "source_csv_sha256": hashlib.sha256(CSV.read_bytes()).hexdigest(),
        "recorded_metrics": {
            "keff_mean": float(selected["keff_mean"]),
            "keff_std_dev": float(selected["keff_std_dev"]),
            "keff_relative_sd_percent": float(selected["keff_relative_sd_percent"]),
            "aggregate_flux_score": float(selected["aggregate_flux_score"]),
            "aggregate_fission_score": float(selected["aggregate_fission_score"]),
            "seed": int(selected["seed"]),
        },
        "review_checklist": checklist,
        "review_note": review_note,
        "disposition": "HOLD_NOT_PHYSICALLY_APPROVED",
        "winner_selected": False,
        "claim_boundary": "Exploratory recorded smoke data; not benchmark-grade physical validation.",
    }
    st.download_button("Download review JSON", json.dumps(payload, indent=2, allow_nan=False), "cbpfr_decision_review.json", "application/json")
    st.success("Review record prepared. This export records review state; it does not validate the design.")
