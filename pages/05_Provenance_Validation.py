"""Provenance and validation boundary for recorded C5G7 smoke runs."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from cbpfr.dashboard_ui import (
    CYAN, GREEN, ORANGE, RED, apply_workstation_style, base_layout,
    load_smoke, render_header,
)

st.set_page_config(page_title="CB-PFR · Provenance & Validation", page_icon="⚛", layout="wide")
apply_workstation_style()
render_header("Provenance", "FAIL-CLOSED SCIENTIFIC AUDIT")

df = load_smoke().sort_values("candidate_id").reset_index(drop=True)
hash_equal = (
    df["mgxs_sha256_before_transport"].astype(str)
    == df["mgxs_sha256_after_transport"].astype(str)
)
one_seed_each = bool((df.groupby("layout_signature")["seed"].nunique() == 1).all())
single_record_each = bool((df.groupby("layout_signature").size() == 1).all())
mutations = int(df["mutated_preexisting_file_count"].fillna(0).sum()) if "mutated_preexisting_file_count" in df else None

st.markdown('<div class="section-kicker">Evidence chain / current repository snapshot</div>', unsafe_allow_html=True)
st.title("Provenance & Validation")
st.caption("Separate file-integrity checks, software readiness, exploratory results, and physical-validation claims.")

a, b, c, d = st.columns(4)
a.metric("Candidate records", len(df))
b.metric("Before/after hash matches", f"{int(hash_equal.sum())}/{len(df)}")
c.metric("Distinct candidate seeds", df["seed"].nunique())
d.metric("Physical validation", "Not established")

if bool(hash_equal.all()):
    st.success("Recorded MGXS SHA-256 values match before and after transport for every listed row. This is an input-integrity check only.")
else:
    st.error("At least one recorded before/after MGXS hash differs. Inspect the candidate records before interpreting the run results.")

st.markdown("### Evidence gates")
gates = [
    {
        "Gate": "Candidate summary CSV",
        "Observed status": "AVAILABLE" if len(df) else "MISSING",
        "What it supports": "Inspection of recorded run metadata and aggregate metrics.",
        "What it does not prove": "Benchmark-grade performance or physical validity.",
    },
    {
        "Gate": "MGXS before/after hash",
        "Observed status": "MATCHED" if bool(hash_equal.all()) else "MISMATCH",
        "What it supports": "The recorded hash values are consistent within each row.",
        "What it does not prove": "That the underlying physics model is correct.",
    },
    {
        "Gate": "Repeated independent seeds per layout",
        "Observed status": "NOT ESTABLISHED" if single_record_each else "REVIEW REQUIRED",
        "What it supports": "Current table shows the number of recorded candidate rows.",
        "What it does not prove": "Between-run repeatability from one record per layout.",
    },
    {
        "Gate": "Spatial flux / fission / power fields",
        "Observed status": "BLOCKED — TALLY ARRAYS ABSENT",
        "What it supports": "Only the aggregate scores present in the summary CSV.",
        "What it does not prove": "Any cell-wise or pin-wise spatial distribution.",
    },
    {
        "Gate": "CB-PFR physical validation",
        "Observed status": "NOT ESTABLISHED",
        "What it supports": "Software and evidence-inspection workflow only.",
        "What it does not prove": "A validated reactor design, safety, or optimal physical layout.",
    },
]
st.dataframe(pd.DataFrame(gates), use_container_width=True, hide_index=True)

left, right = st.columns([1.25, 1], gap="large")
with left:
    st.markdown('<div class="panel-title">Recorded run identity</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">Candidate ID, layout signature, seed, and source hashes from the committed summary.</div>', unsafe_allow_html=True)
    cols = [
        "candidate_id", "layout_signature", "canonical_reference", "seed",
        "batches", "inactive", "particles_per_batch",
        "mgxs_sha256_before_transport", "mgxs_sha256_after_transport",
    ]
    st.dataframe(df[cols], use_container_width=True, hide_index=True)
with right:
    st.markdown('<div class="panel-title">Recorded k-effective values</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">Descriptive view of the current smoke-run snapshot only.</div>', unsafe_allow_html=True)
    fig = go.Figure(go.Scatter(
        x=df["keff_mean"], y=df["candidate_id"].str.replace("c5g7-2x2-", "", regex=False),
        mode="markers",
        marker={"size": 10, "color": [CYAN if bool(v) else ORANGE for v in df["canonical_reference"]]},
        error_x={"type": "data", "array": df["keff_std_dev"], "visible": True, "color": "#87abc9"},
        customdata=df[["seed", "layout_signature"]].to_numpy(),
        hovertemplate="Candidate %{y}<br>Layout %{customdata[1]}<br>Seed %{customdata[0]}<br>k-effective %{x:.7f}<extra></extra>",
    ))
    base_layout(fig, height=420)
    fig.update_layout(xaxis_title="k-effective (reported mean)", yaxis_title="Candidate", showlegend=False, margin={"l": 105, "r": 20, "t": 26, "b": 48})
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

st.markdown("### Required before making a physical-ranking claim")
st.write(
    "1. Confirm the primary C5G7 specification and the geometry/material correspondence.\n"
    "2. Archive the exact model inputs, transport settings, logs, and statepoints for every seed.\n"
    "3. Run independent repeats per candidate at a common computational budget.\n"
    "4. Extract spatial tallies with mesh/filter metadata, units, normalization, and uncertainty.\n"
    "5. Predeclare the objective, k-effective acceptance band, uncertainty treatment, and decision rule.\n"
    "6. Keep the legacy burnup-state QUBO separate unless a source-backed mapping is established."
)
st.download_button(
    "Export candidate provenance CSV",
    df.to_csv(index=False).encode("utf-8"),
    "cbpfr_candidate_provenance.csv",
    "text/csv",
)
