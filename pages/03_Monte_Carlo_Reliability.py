"""Monte Carlo run inspection for the available exploratory C5G7 smoke data."""
import plotly.graph_objects as go
import streamlit as st

from cbpfr.dashboard_ui import (
    CYAN, ORANGE, MUTED, apply_workstation_style, base_layout, candidate_label,
    load_smoke, render_header, render_page_intro, render_workspace_sidebar,
)

st.set_page_config(page_title="CB-PFR · Monte Carlo Reliability", page_icon="⚛", layout="wide")
apply_workstation_style()
render_header("Monte Carlo", "EXPLORATORY SMOKE DATA · NOT A RELIABILITY STUDY")
df = load_smoke().sort_values("candidate_id").reset_index(drop=True)
render_workspace_sidebar("Monte Carlo Results", df)

render_page_intro(
    "MONTE CARLO / TRANSPORT RUN EVIDENCE",
    "Monte Carlo Reliability",
    "Review reported k-effective estimates, within-run spread, and run settings. Reliability across independent runs is not established by the current one-seed-per-layout snapshot.",
)

a, b, c, d = st.columns(4)
a.metric("Layout records", len(df))
b.metric("Independent seeds / layout", "1 recorded")
c.metric("Batches / run", f'{int(df["batches"].iloc[0])}')
d.metric("Particles / batch", f'{int(df["particles_per_batch"].iloc[0]):,}')

st.markdown(
    '<div class="evidence-note"><b>Interpretation limit</b> · These are exploratory low-budget smoke runs. One recorded seed per layout cannot establish between-run repeatability or support a reliability ranking. Whiskers below are reported within-run standard deviations, not confidence intervals across independent runs.</div>',
    unsafe_allow_html=True,
)
st.write("")

left, right = st.columns([1.45, 1], gap="large")
with left:
    st.markdown('<div class="panel-title">k-effective by candidate</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">Reported run means with within-run standard-deviation whiskers.</div>', unsafe_allow_html=True)
    fig = go.Figure(go.Scatter(
        x=[candidate_label(row) for _, row in df.iterrows()],
        y=df["keff_mean"],
        mode="markers",
        marker={"size": 12, "color": [CYAN if bool(v) else ORANGE for v in df["canonical_reference"]], "line": {"color": "#dceaff", "width": .8}},
        error_y={"type": "data", "array": df["keff_std_dev"], "visible": True, "color": MUTED, "thickness": 1.5, "width": 4},
        customdata=df[["candidate_id", "layout_signature", "seed", "keff_relative_sd_percent"]].to_numpy(),
        hovertemplate="Candidate %{customdata[0]}<br>Layout %{customdata[1]}<br>Seed %{customdata[2]}<br>k-effective %{y:.7f}<br>Relative reported SD %{customdata[3]:.4f}%<extra></extra>",
    ))
    base_layout(fig, height=430)
    fig.update_layout(xaxis_title="Candidate / layout", yaxis_title="k-effective (reported mean)", showlegend=False)
    fig.update_xaxes(tickangle=-22)
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

with right:
    st.markdown('<div class="panel-title">Within-run relative spread</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">Descriptive statistic from the reported run, not a reliability score.</div>', unsafe_allow_html=True)
    rel = df.sort_values("keff_relative_sd_percent")
    fig2 = go.Figure(go.Bar(
        x=rel["keff_relative_sd_percent"],
        y=[candidate_label(row) for _, row in rel.iterrows()],
        orientation="h",
        marker_color=[CYAN if bool(v) else "#36536e" for v in rel["canonical_reference"]],
        customdata=rel[["candidate_id", "seed"]].to_numpy(),
        hovertemplate="Candidate %{customdata[0]}<br>Seed %{customdata[1]}<br>Relative SD %{x:.5f}%<extra></extra>",
    ))
    base_layout(fig2, height=430)
    fig2.update_layout(xaxis_title="Reported relative SD (%)", yaxis_title="", showlegend=False, margin={"l": 105, "r": 20, "t": 28, "b": 48})
    st.plotly_chart(fig2, use_container_width=True, config={"displaylogo": False})

st.markdown("### Run configuration")
config_cols = st.columns(4)
config_cols[0].markdown(f'<div class="scientific-panel"><div class="workspace-kicker">Batches</div><div class="scientific-panel-title">{int(df["batches"].iloc[0]):,}</div><div class="small-muted">Recorded per run</div></div>', unsafe_allow_html=True)
config_cols[1].markdown(f'<div class="scientific-panel"><div class="workspace-kicker">Inactive batches</div><div class="scientific-panel-title">{int(df["inactive"].iloc[0]):,}</div><div class="small-muted">Recorded per run</div></div>', unsafe_allow_html=True)
config_cols[2].markdown(f'<div class="scientific-panel"><div class="workspace-kicker">Particles / batch</div><div class="scientific-panel-title">{int(df["particles_per_batch"].iloc[0]):,}</div><div class="small-muted">Recorded per run</div></div>', unsafe_allow_html=True)
config_cols[3].markdown(f'<div class="workspace-kicker">Seed coverage</div><div class="scientific-panel-title">Single seed per layout</div><div class="small-muted">Independent repeats still required</div>', unsafe_allow_html=True)

st.markdown("### Recorded run manifest")
st.dataframe(df[[
    "candidate_id", "layout_signature", "canonical_reference", "seed", "batches", "inactive",
    "particles_per_batch", "keff_mean", "keff_std_dev", "keff_relative_sd_percent",
]], use_container_width=True, hide_index=True)

st.markdown("### Candidate trade-off space")
st.markdown(
    '<div class="panel-subtitle">Explore relationships between the recorded scalar metrics. '
    'This is descriptive candidate-level context; with one seed per layout it is not a repeatability estimate or a causal relationship.</div>',
    unsafe_allow_html=True,
)
metric_options = {
    "k-effective mean": ("keff_mean", "Reported k-effective mean"),
    "Aggregate flux score": ("aggregate_flux_score", "Aggregate flux score (units not specified)"),
    "Aggregate fission score": ("aggregate_fission_score", "Aggregate fission score (units not specified)"),
    "Reported relative SD (%)": ("keff_relative_sd_percent", "Reported relative SD (%)"),
}
axis_a, axis_b = st.columns(2)
with axis_a:
    x_label = st.selectbox("Horizontal metric", list(metric_options), index=0, key="mc_tradeoff_x")
with axis_b:
    y_label = st.selectbox("Vertical metric", list(metric_options), index=1, key="mc_tradeoff_y")
x_key, x_title = metric_options[x_label]
y_key, y_title = metric_options[y_label]
trade_df = df.dropna(subset=[x_key, y_key]).copy()
fig_trade = go.Figure()
for is_reference, group in trade_df.groupby("canonical_reference", sort=False):
    fig_trade.add_trace(go.Scatter(
        x=group[x_key],
        y=group[y_key],
        mode="markers+text",
        text=group["candidate_id"].str.replace("c5g7-2x2-", "", regex=False),
        textposition="top center",
        textfont={"size": 10},
        marker={
            "size": 13,
            "color": CYAN if bool(is_reference) else ORANGE,
            "symbol": "diamond" if bool(is_reference) else "circle",
            "line": {"color": "#e8f1f7", "width": 0.8},
        },
        customdata=group[["candidate_id", "layout_signature", "seed"]].to_numpy(),
        name="Canonical reference" if bool(is_reference) else "Other layout",
        hovertemplate=(
            "Candidate: %{customdata[0]}<br>Layout: %{customdata[1]}"
            "<br>Seed: %{customdata[2]}<br>"
            + x_title + ": %{x:.7g}<br>" + y_title + ": %{y:.7g}<extra></extra>"
        ),
    ))
base_layout(fig_trade, height=465)
fig_trade.update_layout(
    xaxis_title=x_title,
    yaxis_title=y_title,
    hovermode="closest",
    legend={"orientation": "h", "y": 1.12, "x": 0.02},
    margin={"l": 75, "r": 30, "t": 55, "b": 70},
)
st.plotly_chart(fig_trade, use_container_width=True, config={"displaylogo": False}, key="mc_candidate_tradeoff")
st.caption("Only reported means/aggregate scores are plotted. No extra physical units, confidence intervals, or candidate-specific spatial fields are inferred.")

st.markdown("### What a reliability comparison still needs")
st.write("Run every candidate at a common computational budget over multiple independent seeds; archive matching settings, logs, and statepoints; verify tally definitions and MGXS identity; then predeclare the acceptance band, objective, uncertainty treatment, and decision rule.")
st.download_button("Export run summary CSV", df.to_csv(index=False).encode("utf-8"), "cbpfr_monte_carlo_smoke_summary.csv", "text/csv")
