"""CB-PFR scientific workstation entry point.

The overview visualizes recorded repository evidence only. It never synthesizes
transport outputs or promotes a candidate to a physically validated winner.
"""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from cbpfr.dashboard_ui import (
    CYAN,
    MUTED,
    apply_workstation_style,
    base_layout,
    candidate_label,
    layout_figure,
    load_smoke,
    render_header,
    render_workspace_sidebar,
)

st.set_page_config(
    page_title="CB-PFR | Scientific Workstation",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_workstation_style()
render_header("Workstation", "C5G7 TRANSPORT · EVIDENCE-AWARE MODE")

evidence = load_smoke().sort_values("candidate_id").reset_index(drop=True)
render_workspace_sidebar("Overview", evidence)

st.markdown("## CB-PFR Scientific Workstation")
st.caption(
    "Confidence-Bounded Physical Feasibility Ranking · "
    "Candidate geometry, transport indicators, uncertainty, and provenance."
)

st.warning(
    "EVIDENCE GATE · Current candidate summaries are exploratory. The plots below show "
    "recorded values, not a new OpenMC calculation. No candidate is automatically "
    "declared physically valid or selected as a winner."
)

# Compact evidence strip: values are computed from the checked-in summary table.
k1, k2, k3, k4 = st.columns(4)
k1.metric("Candidate records", f"{len(evidence):,}")
k2.metric("Unique layouts", f'{evidence["layout_signature"].nunique():,}')
k3.metric("k-effective range", f'{evidence["keff_mean"].min():.6f}–{evidence["keff_mean"].max():.6f}')
k4.metric("Seed coverage", f'{evidence["seed"].nunique()} unique seed(s)')
st.caption("Dataset: repository candidate summary · see Provenance & Validation for integrity details.")

st.markdown("### Candidate observatory")
left, right = st.columns([0.92, 1.55], gap="large")
with left:
    candidate_id = st.selectbox(
        "Inspect candidate",
        evidence["candidate_id"].tolist(),
        format_func=lambda value: candidate_label(
            evidence.loc[evidence["candidate_id"] == value].iloc[0]
        ),
    )
    selected = evidence.loc[evidence["candidate_id"] == candidate_id].iloc[0]
    st.markdown('<div class="panel-title">Recorded 2 × 2 assembly arrangement</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="panel-subtitle">Schematic categorical layout · not a pin-cell or transport-mesh reconstruction.</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        layout_figure(str(selected["layout_signature"]), height=330),
        use_container_width=True,
        config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]},
    )
    m1, m2 = st.columns(2)
    m1.metric("Reported k-effective", f'{float(selected["keff_mean"]):.7f}')
    m2.metric("Within-run SD", f'{float(selected["keff_std_dev"]):.2e}')
    st.caption(
        f'Record {selected["candidate_id"]} · seed {int(selected["seed"])} · '
        f'layout {selected["layout_signature"]}'
    )

with right:
    st.markdown('<div class="panel-title">Transport indicator comparison</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="panel-subtitle">Recorded k-effective means with reported within-run standard-deviation whiskers. '
        'Whiskers are not between-seed confidence intervals.</div>',
        unsafe_allow_html=True,
    )
    ordered = evidence.sort_values("keff_mean").reset_index(drop=True)
    labels = [candidate_label(row) for _, row in ordered.iterrows()]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ordered["keff_mean"],
        y=labels,
        mode="markers",
        marker={
            "size": 11,
            "color": [CYAN if value == candidate_id else "#54748b" for value in ordered["candidate_id"]],
            "line": {"color": "#dceaf2", "width": 0.7},
        },
        error_x={
            "type": "data",
            "array": ordered["keff_std_dev"],
            "visible": True,
            "color": MUTED,
            "thickness": 1.2,
            "width": 4,
        },
        customdata=ordered[["candidate_id", "layout_signature", "seed", "canonical_reference"]].to_numpy(),
        hovertemplate=(
            "Candidate %{customdata[0]}<br>Layout %{customdata[1]}<br>"
            "Seed %{customdata[2]}<br>Canonical reference %{customdata[3]}<br>"
            "k-effective %{x:.7f}<extra></extra>"
        ),
    ))
    base_layout(fig, height=430)
    fig.update_layout(
        xaxis_title="Reported k-effective mean",
        yaxis_title="",
        showlegend=False,
        margin={"l": 115, "r": 24, "t": 25, "b": 55},
    )
    fig.update_xaxes(showgrid=True, gridcolor="#203747", zeroline=False)
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]},
    )

st.markdown("### Workspaces")
st.caption("Open a module to inspect the corresponding source data and scientific limitations.")
cards = [
    ("01 · Geometry", "Candidate arrangement and layout records.", "pages/01_C5G7_Layout_Explorer.py", "Open Geometry Explorer", "🧩"),
    ("02 · Physics fields", "Archived OpenMC mesh tallies and spatial uncertainty.", "pages/02_Physics_Field_Explorer.py", "Open Physics Fields", "🌐"),
    ("03 · Monte Carlo", "Run settings, reported spread, and seed coverage.", "pages/03_Monte_Carlo_Reliability.py", "Open Monte Carlo Results", "📊"),
    ("04 · QUBO", "Exact cardinality constraint and discrete energy landscape.", "pages/04_QUBO_Optimization.py", "Open QUBO Optimization", "⚙️"),
    ("05 · Provenance", "Input integrity, validation state, and evidence lineage.", "pages/05_Provenance_Validation.py", "Open Provenance Audit", "🧾"),
    ("06 · Decision", "Compare recorded candidates without automatic approval.", "pages/06_Decision_Workspace.py", "Open Decision Workspace", "🔎"),
    ("07 · Methods", "Workflow, metric definitions, and known limitations.", "pages/07_Help_Methods.py", "Open Help & Methods", "📘"),
]
for start in range(0, len(cards), 2):
    col_a, col_b = st.columns(2, gap="large")
    for col, item in zip((col_a, col_b), cards[start:start + 2]):
        title, description, page, label, icon = item
        with col:
            with st.container(border=True):
                st.markdown(f"#### {title}")
                st.write(description)
                st.page_link(page, label=label, icon=icon, use_container_width=True)

st.divider()
st.markdown("### Evidence integrity")
i1, i2, i3 = st.columns(3)
i1.metric("Recorded candidate rows", len(evidence))
i2.metric("Distinct layout signatures", evidence["layout_signature"].nunique())
hash_columns = {"mgxs_sha256_before_transport", "mgxs_sha256_after_transport"}
hash_consistent = (
    hash_columns.issubset(evidence.columns)
    and (
        evidence["mgxs_sha256_before_transport"].astype(str)
        == evidence["mgxs_sha256_after_transport"].astype(str)
    ).all()
)
i3.metric("MGXS hash consistency", "MATCHED" if hash_consistent else "REVIEW")
st.caption(
    "This page reads repository evidence already on disk; it does not start OpenMC. "
    "Matching hashes support input-integrity review but do not certify physical validity."
)
