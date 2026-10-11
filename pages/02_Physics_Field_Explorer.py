"""Evidence-aware physics-field explorer for the recorded C5G7 smoke snapshot."""
import plotly.graph_objects as go
import streamlit as st

from cbpfr.dashboard_ui import (
    CYAN, MUTED, apply_workstation_style, base_layout, candidate_label,
    layout_figure, load_smoke, render_header, render_page_intro, render_workspace_sidebar,
)

st.set_page_config(page_title="CB-PFR · Physics Field Explorer", page_icon="⚛", layout="wide")
apply_workstation_style()
render_header("Physics fields", "SPATIAL TALLY ARRAYS REQUIRED")
df = load_smoke().sort_values("candidate_id").reset_index(drop=True)
render_workspace_sidebar("Physics Fields", df)

render_page_intro(
    "PHYSICS FIELD EXPLORER / C5G7 2×2 STUDY",
    "Physics Field Explorer",
    "Inspect the recorded aggregate evidence and identify which physical fields are actually available. Spatial maps remain gated until source tally arrays, units, and mesh metadata are present.",
)

a, b, c, d = st.columns(4)
a.metric("Layout records", len(df))
b.metric("Aggregate flux scores", int(df["aggregate_flux_score"].notna().sum()))
c.metric("Aggregate fission scores", int(df["aggregate_fission_score"].notna().sum()))
d.metric("Spatial field arrays", "Unavailable")

st.markdown(
    '<div class="evidence-note"><b>Scientific boundary</b> · The current CSV contains aggregate flux and fission scores only. It does not provide mesh dimensions, cell-wise tally arrays, field units, normalization, or spatial uncertainty. A neutron-flux or power heatmap would be fabricated, so this view deliberately does not synthesize one.</div>',
    unsafe_allow_html=True,
)
st.write("")

control, spacer = st.columns([1.1, 2.4])
with control:
    view = st.selectbox("Analysis metric", ["Assembly placement", "k-effective", "Aggregate flux score", "Aggregate fission score"])
with spacer:
    st.markdown('<div class="small-muted" style="padding-top:28px">Use the candidate selector to compare a specific layout against the recorded dataset.</div>', unsafe_allow_html=True)
selected_id = st.selectbox(
    "Selected candidate",
    df["candidate_id"].tolist(),
    format_func=lambda value: candidate_label(df.loc[df["candidate_id"] == value].iloc[0]),
)
selected = df.loc[df["candidate_id"] == selected_id].iloc[0]

left, right = st.columns([.92, 1.55], gap="large")
with left:
    st.markdown('<div class="panel-title">Assembly placement</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">2×2 categorical arrangement · U = UO₂ · M = MOX</div>', unsafe_allow_html=True)
    st.plotly_chart(layout_figure(str(selected["layout_signature"]), height=350), use_container_width=True, config={"displaylogo": False})
    st.caption(f'Reference: {selected["candidate_id"]} · seed {int(selected["seed"])}')
    st.markdown('<div class="small-muted">Squares are assembly positions, not pin cells, material volumes, or a transport mesh.</div>', unsafe_allow_html=True)

with right:
    metric_map = {
        "Assembly placement": ("keff_mean", "keff_std_dev", "Recorded k-effective mean", "k-effective (reported mean)", True),
        "k-effective": ("keff_mean", "keff_std_dev", "Recorded k-effective mean", "k-effective (reported mean)", True),
        "Aggregate flux score": ("aggregate_flux_score", None, "Aggregate flux score", "Repository score (units not specified)", False),
        "Aggregate fission score": ("aggregate_fission_score", None, "Aggregate fission score", "Repository score (units not specified)", False),
    }
    metric, error_col, chart_title, y_title, show_error = metric_map[view]
    ordered = df.sort_values(metric)
    colors = [CYAN if x == selected_id else "#36536e" for x in ordered["candidate_id"]]
    fig = go.Figure(go.Bar(
        x=[candidate_label(row) for _, row in ordered.iterrows()],
        y=ordered[metric],
        marker_color=colors,
        error_y=({"type": "data", "array": ordered[error_col], "visible": True, "color": MUTED, "thickness": 1.4, "width": 4} if show_error else None),
        customdata=ordered[["candidate_id", "layout_signature", "seed"]].to_numpy(),
        hovertemplate="Candidate %{customdata[0]}<br>Layout %{customdata[1]}<br>Seed %{customdata[2]}<br>" + y_title + ": %{y:.7f}<extra></extra>",
    ))
    base_layout(fig, height=445, title={"text": chart_title, "x": .02, "font": {"size": 14}})
    fig.update_layout(xaxis_title="Candidate / layout", yaxis_title=y_title, showlegend=False)
    fig.update_xaxes(tickangle=-22)
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

st.markdown("### Selected record")
record_cols = ["candidate_id", "layout_signature", "canonical_reference", "seed", "keff_mean", "keff_std_dev", "aggregate_flux_score", "aggregate_fission_score"]
st.dataframe(df.loc[df["candidate_id"] == selected_id, record_cols], use_container_width=True, hide_index=True)
st.caption("k-effective whiskers show the reported within-run standard deviation, not a confidence interval or a between-seed reproducibility estimate.")

st.markdown("### Spatial-field readiness")
g1, g2, g3 = st.columns(3)
g1.markdown('<div class="scientific-panel"><div class="scientific-panel-title">Required source</div><p class="small-muted">Verified OpenMC statepoint and exact tally definition.</p></div>', unsafe_allow_html=True)
g2.markdown('<div class="scientific-panel"><div class="scientific-panel-title">Required metadata</div><p class="small-muted">Mesh/filter dimensions, score units, normalization basis, and uncertainty array.</p></div>', unsafe_allow_html=True)
g3.markdown('<div class="scientific-panel"><div class="scientific-panel-title">Required provenance</div><p class="small-muted">Source hash, settings, run identity, and validation record.</p></div>', unsafe_allow_html=True)
