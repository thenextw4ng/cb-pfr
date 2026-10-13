"""CB-PFR scientific workstation overview: recorded evidence only."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from cbpfr.dashboard_ui import (
    BG, BLUE, CYAN, LINE, MUTED, ORANGE, PANEL, TEXT,
    apply_workstation_style, base_layout, candidate_label, layout_figure,
    load_smoke, render_header, render_workspace_sidebar,
)

st.set_page_config(
    page_title="CB-PFR | Scientific Workstation",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_workstation_style()
evidence = load_smoke().sort_values("candidate_id").reset_index(drop=True)
render_workspace_sidebar("Overview", evidence)
render_header("Overview", "C5G7 TRANSPORT · EVIDENCE-AWARE MODE")

st.markdown(
    f"""
    <section class="cbpfr-hero">
      <div class="hero-eyebrow">RESEARCH CONTROL ROOM / 01</div>
      <div class="hero-title">Physical Feasibility<br><span>Ranking Workbench</span></div>
      <div class="hero-copy">A traceable workspace for inspecting C5G7 candidate configurations,
      recorded transport indicators, uncertainty, and evidence integrity.</div>
      <div class="hero-meta"><span>MODEL · C5G7 2×2 STUDY</span><span>DATA · RECORDED REPOSITORY EVIDENCE</span><span>MODE · EXPLORATORY</span></div>
    </section>
    """,
    unsafe_allow_html=True,
)
st.warning(
    "EVIDENCE GATE · Values below are read from the checked-in candidate summary. "
    "This dashboard does not launch OpenMC, infer missing spatial fields, or approve a physical design."
)

k1, k2, k3, k4 = st.columns(4, gap="medium")
k1.metric("Candidate records", f"{len(evidence):,}", help="Rows in the current candidate-summary dataset.")
k2.metric("Unique layouts", f'{evidence["layout_signature"].nunique():,}')
k3.metric("k-effective span", f'{evidence["keff_mean"].min():.5f} – {evidence["keff_mean"].max():.5f}')
k4.metric("Distinct recorded seeds", f'{evidence["seed"].nunique():,}')
st.markdown('<div class="section-kicker">01 / CANDIDATE OBSERVATORY</div>', unsafe_allow_html=True)

left, right = st.columns([0.82, 1.55], gap="large")
with left:
    with st.container(border=True):
        st.markdown("#### Configuration inspector")
        candidate_id = st.selectbox(
            "Select recorded candidate",
            evidence["candidate_id"].tolist(),
            format_func=lambda value: candidate_label(evidence.loc[evidence["candidate_id"] == value].iloc[0]),
            key="overview_candidate",
        )
        selected = evidence.loc[evidence["candidate_id"] == candidate_id].iloc[0]
        st.plotly_chart(
            layout_figure(str(selected["layout_signature"]), height=310),
            use_container_width=True,
            config={"displaylogo": False, "scrollZoom": False},
            key="overview_layout_plot",
        )
        a, b = st.columns(2)
        a.metric("k-effective mean", f'{float(selected["keff_mean"]):.7f}')
        b.metric("Reported within-run σ", f'{float(selected["keff_std_dev"]):.2e}')
        st.markdown(
            f'<div class="candidate-metadata"><span>ID</span><b>{selected["candidate_id"]}</b>'
            f'<span>LAYOUT</span><b>{selected["layout_signature"]}</b>'
            f'<span>SEED</span><b>{int(selected["seed"])}</b></div>',
            unsafe_allow_html=True,
        )
        st.caption("Categorical 2×2 schematic only; not a pin-resolved geometry reconstruction.")

with right:
    with st.container(border=True):
        st.markdown("#### Transport response · candidate comparison")
        st.caption("Points show recorded means. Whiskers show reported within-run standard deviation, not between-seed confidence intervals.")
        ordered = evidence.sort_values("keff_mean").reset_index(drop=True)
        labels = [candidate_label(row) for _, row in ordered.iterrows()]
        colors = [CYAN if value == candidate_id else "#638197" for value in ordered["candidate_id"]]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ordered["keff_mean"], y=labels, mode="markers",
            marker={"size": 12, "color": colors, "line": {"color": "#dceaf2", "width": 0.8}},
            error_x={"type": "data", "array": ordered["keff_std_dev"], "visible": True,
                     "color": MUTED, "thickness": 1.3, "width": 5},
            customdata=ordered[["candidate_id", "layout_signature", "seed", "canonical_reference"]].to_numpy(),
            hovertemplate=("<b>%{customdata[0]}</b><br>Layout %{customdata[1]}<br>"
                           "Seed %{customdata[2]}<br>Reference %{customdata[3]}<br>"
                           "k-effective %{x:.7f}<extra></extra>"),
        ))
        base_layout(fig, height=410)
        fig.update_layout(
            xaxis_title="Reported k-effective mean", yaxis_title="Candidate",
            showlegend=False, margin={"l": 85, "r": 22, "t": 12, "b": 52},
        )
        fig.update_xaxes(showgrid=True, gridcolor=LINE, zeroline=False, tickformat=".5f")
        fig.update_yaxes(showgrid=False, automargin=True)
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False}, key="overview_keff_chart")

        # The aggregate scores are shown as supplied; this is explicitly not a physical ranking.
        score = evidence[["candidate_id", "aggregate_flux_score", "aggregate_fission_score"]].copy()
        score["candidate"] = score["candidate_id"].map(lambda x: candidate_label({"candidate_id": x}))
        score = score.sort_values("aggregate_flux_score")
        score_fig = go.Figure()
        score_fig.add_trace(go.Bar(
            x=score["aggregate_flux_score"], y=score["candidate"], orientation="h",
            marker={"color": "#287f9b", "line": {"color": "#70d8df", "width": 0.5}},
            customdata=score[["aggregate_fission_score"]].to_numpy(),
            hovertemplate="Candidate %{y}<br>Recorded aggregate flux score %{x:.5g}<br>"
                          "Recorded aggregate fission score %{customdata[0]:.5g}<extra></extra>",
        ))
        base_layout(score_fig, height=255)
        score_fig.update_layout(
            title={"text": "Recorded aggregate flux score", "x": 0.02, "xanchor": "left", "font": {"size": 13}},
            xaxis_title="Source-reported score · units require verification",
            yaxis_title="", margin={"l": 80, "r": 18, "t": 40, "b": 48},
        )
        score_fig.update_yaxes(showgrid=False)
        st.plotly_chart(score_fig, use_container_width=True, config={"displaylogo": False}, key="overview_flux_score")

st.markdown('<div class="section-kicker">02 / WORKSPACE MODULES</div>', unsafe_allow_html=True)
st.caption("Each module opens a focused inspection workflow. Spatial results appear only when source tally arrays are available.")
cards = [
    ("01", "Geometry Explorer", "Material assignment and candidate layouts.", "pages/01_C5G7_Layout_Explorer.py", "Open geometry"),
    ("02", "Physics Fields", "Archived mesh tallies and relative statistical uncertainty.", "pages/02_Physics_Field_Explorer.py", "Inspect fields"),
    ("03", "Monte Carlo", "Reported run settings, uncertainty, and seed coverage.", "pages/03_Monte_Carlo_Reliability.py", "Inspect runs"),
    ("04", "QUBO / Optimization", "Discrete energy landscape and feasibility enumeration.", "pages/04_QUBO_Optimization.py", "Explore QUBO"),
    ("05", "Provenance & Validation", "Input hashes, evidence lineage, and blocked validation gates.", "pages/05_Provenance_Validation.py", "Open audit"),
    ("06", "Decision Workspace", "Candidate trade-offs and traceable review export.", "pages/06_Decision_Workspace.py", "Review evidence"),
]
for start in range(0, len(cards), 3):
    cols = st.columns(3, gap="medium")
    for col, item in zip(cols, cards[start:start + 3]):
        num, title, desc, page, action = item
        with col:
            with st.container(border=True):
                st.markdown(f'<div class="module-number">{num} / MODULE</div>', unsafe_allow_html=True)
                st.markdown(f"#### {title}")
                st.markdown(f'<div class="module-copy">{desc}</div>', unsafe_allow_html=True)
                st.page_link(page, label=action, use_container_width=True)

hash_columns = {"mgxs_sha256_before_transport", "mgxs_sha256_after_transport"}
hash_consistent = hash_columns.issubset(evidence.columns) and (
    evidence["mgxs_sha256_before_transport"].astype(str)
    == evidence["mgxs_sha256_after_transport"].astype(str)
).all()
st.markdown('<div class="section-kicker">03 / DATA INTEGRITY</div>', unsafe_allow_html=True)
a, b, c = st.columns(3, gap="medium")
a.metric("Candidate rows", len(evidence))
b.metric("Distinct layouts", evidence["layout_signature"].nunique())
c.metric("Recorded MGXS hash consistency", "MATCHED" if hash_consistent else "REVIEW")
st.caption("Matching recorded hashes support input-integrity review only. They do not certify the model, transport solution, or physical feasibility.")
