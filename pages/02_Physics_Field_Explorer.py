"""Evidence-aware physics-field explorer.

The current committed summary contains aggregate scores only; spatial fields stay blocked
until verified statepoint/mesh tally arrays and units are supplied.
"""
import plotly.graph_objects as go
import streamlit as st

from cbpfr.dashboard_ui import (
    CYAN, ORANGE, TEXT, MUTED, apply_workstation_style, base_layout,
    candidate_label, layout_figure, load_smoke, render_header,
)

st.set_page_config(page_title="CB-PFR · Physics Fields", page_icon="⚛", layout="wide")
apply_workstation_style()
render_header("Physics fields", "SPATIAL TALLY ARRAYS REQUIRED")
df = load_smoke().sort_values("candidate_id").reset_index(drop=True)

st.markdown('<div class="section-kicker">Field inventory / C5G7 2×2 study</div>', unsafe_allow_html=True)
st.title("Physics Field Explorer")
st.caption("Inspect the recorded aggregate evidence without implying cell-wise or pin-wise physical fields.")

a, b, c, d = st.columns(4)
a.metric("Layout records", len(df))
b.metric("Aggregate flux scores", int(df["aggregate_flux_score"].notna().sum()))
c.metric("Aggregate fission scores", int(df["aggregate_fission_score"].notna().sum()))
d.metric("Spatial field arrays", "Unavailable")

st.markdown(
    '<div class="evidence-note"><b>Scientific boundary:</b> the current CSV has one aggregate flux score and one aggregate fission score per layout. It does not contain mesh dimensions, cell-wise tally arrays, field units, or spatial uncertainty. A neutron-flux/power heatmap is therefore unavailable and is not synthesized.</div>',
    unsafe_allow_html=True,
)
st.write("")

view = st.radio(
    "Analysis view",
    ["Assembly layout", "k-effective", "Aggregate flux score", "Aggregate fission score"],
    horizontal=True,
)
selected_id = st.selectbox(
    "Selected candidate",
    df["candidate_id"].tolist(),
    format_func=lambda value: candidate_label(df.loc[df["candidate_id"] == value].iloc[0]),
)
selected = df.loc[df["candidate_id"] == selected_id].iloc[0]

left, right = st.columns([1.0, 1.45], gap="large")
with left:
    st.markdown('<div class="panel-title">2 × 2 assembly placement</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">Categorical layout only · U = UO₂ · M = MOX</div>', unsafe_allow_html=True)
    st.plotly_chart(layout_figure(str(selected["layout_signature"])), use_container_width=True, config={"displaylogo": False})
    st.caption("The four squares represent assembly positions. They are not pin cells, material volumes, or a transport mesh.")
with right:
    st.markdown('<div class="panel-title">Recorded candidate comparison</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">One selected metric at a time; values retain their source definitions.</div>', unsafe_allow_html=True)
    if view == "Assembly layout":
        metric = "keff_mean"
        errors = "keff_std_dev"
        title = "Recorded k-effective mean"
        ytitle = "k-effective (reported mean)"
        show_error = True
    elif view == "k-effective":
        metric = "keff_mean"
        errors = "keff_std_dev"
        title = "Recorded k-effective mean"
        ytitle = "k-effective (reported mean)"
        show_error = True
    elif view == "Aggregate flux score":
        metric = "aggregate_flux_score"
        errors = None
        title = "Aggregate flux score"
        ytitle = "Repository score (units not specified)"
        show_error = False
    else:
        metric = "aggregate_fission_score"
        errors = None
        title = "Aggregate fission score"
        ytitle = "Repository score (units not specified)"
        show_error = False

    ordered = df.sort_values(metric)
    colors = [CYAN if x == selected_id else "#42617d" for x in ordered["candidate_id"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[candidate_label(row) for _, row in ordered.iterrows()],
        y=ordered[metric],
        marker_color=colors,
        error_y=({"type": "data", "array": ordered[errors], "visible": True, "color": MUTED, "thickness": 1.3, "width": 3} if show_error else None),
        customdata=ordered[["candidate_id", "layout_signature"]].to_numpy(),
        hovertemplate="Candidate %{customdata[0]}<br>Layout %{customdata[1]}<br>" + ytitle + ": %{y:.6f}<extra></extra>",
    ))
    base_layout(fig, height=390, title={"text": title, "x": 0.02, "font": {"size": 13}})
    fig.update_layout(xaxis_title="Candidate (layout signature)", yaxis_title=ytitle, showlegend=False)
    fig.update_xaxes(tickangle=-25)
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

st.markdown("### Selected record")
st.dataframe(
    df.loc[df["candidate_id"] == selected_id, [
        "candidate_id", "layout_signature", "canonical_reference", "seed", "keff_mean",
        "keff_std_dev", "aggregate_flux_score", "aggregate_fission_score",
    ]],
    use_container_width=True, hide_index=True,
)
st.caption("The k-effective error bars show the reported within-run standard deviation, not a confidence interval or between-seed reproducibility estimate.")
st.markdown("### To unlock spatial field maps")
st.write("Load a verified OpenMC statepoint with the exact tally definition, mesh/filter metadata, physical units, normalization basis, uncertainty array, and source hash. The UI should only render the spatial map after those fields pass validation.")
