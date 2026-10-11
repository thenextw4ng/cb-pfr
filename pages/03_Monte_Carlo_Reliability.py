"""Monte Carlo run inspection for the available exploratory C5G7 smoke data."""
import plotly.graph_objects as go
import streamlit as st

from cbpfr.dashboard_ui import (
    CYAN, ORANGE, MUTED, apply_workstation_style, base_layout, candidate_label,
    load_smoke, render_header,
)

st.set_page_config(page_title="CB-PFR · Monte Carlo Results", page_icon="⚛", layout="wide")
apply_workstation_style()
render_header("Monte Carlo", "EXPLORATORY SMOKE DATA · NOT A RELIABILITY STUDY")
df = load_smoke().sort_values("candidate_id").reset_index(drop=True)

st.markdown('<div class="section-kicker">Transport run evidence</div>', unsafe_allow_html=True)
st.title("Monte Carlo & Reliability")
st.caption("Inspect recorded run means, within-run standard deviations, and computational settings.")

a, b, c, d = st.columns(4)
a.metric("Layout records", len(df))
a.caption("One recorded run per candidate")
b.metric("Batches / run", f'{int(df["batches"].iloc[0])}')
c.metric("Inactive batches", f'{int(df["inactive"].iloc[0])}')
d.metric("Particles / batch", f'{int(df["particles_per_batch"].iloc[0]):,}')

st.warning(
    "These are exploratory, low-budget smoke runs. There is only one recorded seed per layout, "
    "so this table cannot establish between-run repeatability or support a reliability ranking."
)

left, right = st.columns([1.45, 1], gap="large")
with left:
    st.markdown('<div class="panel-title">k-effective by candidate</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">Markers are reported run means; whiskers are reported within-run standard deviations.</div>', unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[candidate_label(row) for _, row in df.iterrows()],
        y=df["keff_mean"],
        mode="markers",
        marker={"size": 11, "color": [CYAN if bool(v) else ORANGE for v in df["canonical_reference"]], "line": {"color": "#dceaff", "width": 0.7}},
        error_y={"type": "data", "array": df["keff_std_dev"], "visible": True, "color": MUTED, "thickness": 1.4, "width": 4},
        customdata=df[["candidate_id", "layout_signature", "seed", "keff_relative_sd_percent"]].to_numpy(),
        hovertemplate="Candidate %{customdata[0]}<br>Layout %{customdata[1]}<br>Seed %{customdata[2]}<br>k-effective %{y:.7f}<br>Relative reported SD %{customdata[3]:.4f}%<extra></extra>",
    ))
    base_layout(fig, height=400)
    fig.update_layout(xaxis_title="Candidate / layout", yaxis_title="k-effective (reported mean)", showlegend=False)
    fig.update_xaxes(tickangle=-25)
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
    st.caption("Whiskers are not confidence intervals and should not be interpreted as uncertainty across independent runs.")
with right:
    st.markdown('<div class="panel-title">Reported relative standard deviation</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">A descriptive within-run statistic, not a repeatability score.</div>', unsafe_allow_html=True)
    rel = df.sort_values("keff_relative_sd_percent")
    fig2 = go.Figure(go.Bar(
        x=rel["keff_relative_sd_percent"],
        y=[candidate_label(row) for _, row in rel.iterrows()],
        orientation="h",
        marker_color=[CYAN if bool(v) else "#42617d" for v in rel["canonical_reference"]],
        customdata=rel[["candidate_id", "seed"]].to_numpy(),
        hovertemplate="Candidate %{customdata[0]}<br>Seed %{customdata[1]}<br>Relative SD %{x:.5f}%<extra></extra>",
    ))
    base_layout(fig2, height=400)
    fig2.update_layout(xaxis_title="Reported relative SD (%)", yaxis_title="", showlegend=False, margin={"l": 110, "r": 20, "t": 26, "b": 45})
    st.plotly_chart(fig2, use_container_width=True, config={"displaylogo": False})

st.markdown("### Run manifest")
st.dataframe(
    df[[
        "candidate_id", "layout_signature", "canonical_reference", "seed",
        "batches", "inactive", "particles_per_batch", "keff_mean",
        "keff_std_dev", "keff_relative_sd_percent",
    ]],
    use_container_width=True, hide_index=True,
)
st.markdown("### What a reliability comparison still needs")
st.write(
    "Run every candidate at a common budget over multiple independent seeds; archive the matching "
    "settings, logs, and statepoints; verify tally definitions and MGXS identity; then predeclare "
    "the acceptance band, objective, uncertainty treatment, and decision rule."
)
st.download_button(
    "Export run summary CSV",
    df.to_csv(index=False).encode("utf-8"),
    "cbpfr_monte_carlo_smoke_summary.csv",
    "text/csv",
)
