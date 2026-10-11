"""CB-PFR research workstation overview; demo and smoke data are clearly bounded."""
import plotly.graph_objects as go
import streamlit as st

from cbpfr.dashboard_ui import (
    CYAN, ORANGE, apply_workstation_style, base_layout, candidate_label,
    layout_figure, load_smoke, render_header,
)

st.set_page_config(page_title="CB-PFR · Research Workstation", page_icon="⚛", layout="wide")
apply_workstation_style()
render_header("Overview", "C5G7 SMOKE DATA · NOT PHYSICALLY VALIDATED")

df = load_smoke().sort_values("candidate_id").reset_index(drop=True)
st.markdown('<div class="section-kicker">Research workspace / evidence snapshot</div>', unsafe_allow_html=True)
st.title("Confidence-Bounded Physical Feasibility Ranking")
st.caption("A research workstation for candidate layouts, uncertainty-aware inspection, QUBO feasibility, and evidence provenance.")

a, b, c, d = st.columns(4)
a.metric("Recorded layout candidates", len(df))
b.metric("Canonical reference rows", int(df["canonical_reference"].sum()))
c.metric("Distinct recorded seeds", df["seed"].nunique())
d.metric("Physical validation", "Not established")

st.warning(
    "Current evidence is an exploratory C5G7 smoke snapshot: one recorded run per layout. "
    "The dashboard reports observed values but does not claim benchmark-grade ranking, spatial "
    "field reconstruction, reactor safety, or physical validation."
)

left, right = st.columns([1, 1.45], gap="large")
with left:
    st.markdown('<div class="panel-title">Canonical reference layout</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">2 × 2 categorical assembly placement · UO₂ / MOX only</div>', unsafe_allow_html=True)
    canonical = df[df["canonical_reference"]]
    selected = canonical.iloc[0] if not canonical.empty else df.iloc[0]
    st.plotly_chart(layout_figure(str(selected["layout_signature"])), use_container_width=True, config={"displaylogo": False})
    st.caption(f'Reference record: {selected["candidate_id"]} · seed {int(selected["seed"])}')
with right:
    st.markdown('<div class="panel-title">Recorded k-effective by layout</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">Reported means with within-run standard-deviation whiskers.</div>', unsafe_allow_html=True)
    fig = go.Figure(go.Scatter(
        x=[candidate_label(row) for _, row in df.iterrows()],
        y=df["keff_mean"],
        mode="markers",
        marker={"size": 11, "color": [CYAN if bool(v) else ORANGE for v in df["canonical_reference"]]},
        error_y={"type": "data", "array": df["keff_std_dev"], "visible": True, "color": "#87abc9", "thickness": 1.4, "width": 4},
        customdata=df[["candidate_id", "layout_signature", "seed"]].to_numpy(),
        hovertemplate="Candidate %{customdata[0]}<br>Layout %{customdata[1]}<br>Seed %{customdata[2]}<br>k-effective %{y:.7f}<extra></extra>",
    ))
    base_layout(fig, height=360)
    fig.update_layout(xaxis_title="Candidate / layout", yaxis_title="k-effective (reported mean)", showlegend=False)
    fig.update_xaxes(tickangle=-20)
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

st.markdown("### Evidence inventory")
inventory = [
    {"Evidence item": "Candidate summary CSV", "Available": "Yes", "Can support": "Aggregate candidate/run comparison"},
    {"Evidence item": "2 × 2 material layout signature", "Available": "Yes", "Can support": "Categorical assembly-placement schematic"},
    {"Evidence item": "Within-run k-effective standard deviation", "Available": "Yes", "Can support": "Reported within-run spread only"},
    {"Evidence item": "Cell-wise neutron flux / fission / power arrays", "Available": "No", "Can support": "No spatial field map until tally arrays are supplied"},
    {"Evidence item": "Independent repeated seeds per layout", "Available": "Not in current summary", "Can support": "No between-run reliability conclusion yet"},
]
st.dataframe(inventory, use_container_width=True, hide_index=True)

st.markdown("### Workstation modules")
cols = st.columns(5)
pages = [
    ("Geometry Explorer", "pages/01_C5G7_Layout_Explorer.py"),
    ("Physics Fields", "pages/02_Physics_Field_Explorer.py"),
    ("Monte Carlo", "pages/03_Monte_Carlo_Reliability.py"),
    ("QUBO / Optimization", "pages/04_QUBO_Optimization.py"),
    ("Provenance", "pages/05_Provenance_Validation.py"),
]
for col, (label, path) in zip(cols, pages):
    with col:
        st.page_link(path, label=label, icon="↗")

st.caption("Scientific rule: if a source array, unit, mesh/filter definition, or provenance record is absent, the interface marks that view unavailable instead of inventing a plausible-looking visualization.")
