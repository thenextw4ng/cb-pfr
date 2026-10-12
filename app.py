"""CB-PFR scientific workstation entry point.

The legacy ReactorQ demo interface has been removed from the landing page.
Scientific modules remain separate and retain their evidence/validation boundaries.
"""
from __future__ import annotations

import streamlit as st

from cbpfr.dashboard_ui import (
    apply_workstation_style,
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
render_header("Workstation", "RESEARCH WORKSTATION · EVIDENCE-AWARE MODE")

evidence = load_smoke()
render_workspace_sidebar("Overview", evidence)

st.markdown("## CB-PFR Scientific Workstation")
st.caption(
    "Confidence-Bounded Physical Feasibility Ranking · "
    "C5G7 layout evidence, optimization, repeatability, and validation review."
)

st.warning(
    "Evidence status: exploratory. Recorded summaries and schematic layouts are not "
    "a substitute for spatially resolved physical validation. No candidate is "
    "automatically declared a winner."
)

st.markdown("### Workspaces")
left, right = st.columns(2, gap="large")
with left:
    st.markdown("#### 01 · Core configuration")
    st.write(
        "Inspect recorded C5G7 candidate layouts, reported k-effective statistics, "
        "and source-data provenance."
    )
    st.page_link(
        "pages/01_C5G7_Layout_Explorer.py",
        label="Open Geometry Explorer",
        icon="🧩",
        use_container_width=True,
    )
    st.markdown("#### 02 · Physics and transport evidence")
    st.write(
        "Review available physics-field views and Monte Carlo uncertainty summaries. "
        "Unavailable spatial evidence must remain explicitly marked as unavailable."
    )
    st.page_link(
        "pages/02_Physics_Field_Explorer.py",
        label="Open Physics Fields",
        icon="🌐",
        use_container_width=True,
    )
    st.page_link(
        "pages/03_Monte_Carlo_Reliability.py",
        label="Open Monte Carlo Results",
        icon="📊",
        use_container_width=True,
    )

with right:
    st.markdown("#### 03 · Optimization and decision review")
    st.write(
        "Inspect QUBO candidate-generation tools and review recorded candidate evidence "
        "without automatically approving a physical configuration."
    )
    st.page_link(
        "pages/04_QUBO_Optimization.py",
        label="Open QUBO Optimization",
        icon="⚙️",
        use_container_width=True,
    )
    st.page_link(
        "pages/06_Decision_Workspace.py",
        label="Open Decision Workspace",
        icon="🔎",
        use_container_width=True,
    )
    st.markdown("#### 04 · Provenance and methods")
    st.write(
        "Audit source records, validation limitations, reproducibility information, "
        "and method descriptions."
    )
    st.page_link(
        "pages/05_Provenance_Validation.py",
        label="Open Provenance & Validation",
        icon="🧾",
        use_container_width=True,
    )
    st.page_link(
        "pages/07_Help_Methods.py",
        label="Open Help & Methods",
        icon="📘",
        use_container_width=True,
    )

st.divider()
st.markdown("### Current evidence boundary")
m1, m2, m3 = st.columns(3)
m1.metric("Recorded candidate rows", len(evidence))
m2.metric("Distinct layout signatures", evidence["layout_signature"].nunique())
m3.metric(
    "MGXS hash consistency",
    "MATCHED"
    if {"mgxs_sha256_before_transport", "mgxs_sha256_after_transport"}.issubset(evidence.columns)
    and (evidence["mgxs_sha256_before_transport"].astype(str)
         == evidence["mgxs_sha256_after_transport"].astype(str)).all()
    else "REVIEW",
)
st.caption(
    "This landing page uses repository evidence already on disk. It does not start an "
    "OpenMC transport run. Hash consistency is an integrity check, not a physics-validation certificate."
)
