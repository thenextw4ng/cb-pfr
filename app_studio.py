"""ReactorQ Studio — visual scientific workbench for CB-PFR / C5G7.

Evidence-first: run metrics and four-position layout contributions come from the
committed run-level CSV. A full spatial flux/power field is shown only when a
real mesh-tally CSV is supplied (x, y, value columns); the UI never fabricates
physics data and never launches OpenMC.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
RUNS_CSV = ROOT / "results/c5g7_corrected_group_repeatability_smoke_2026-10-11/run_level_fission_objective.csv"
REPORT = ROOT / "reports/c5g7_corrected_group_repeatability_smoke_2026-10-11.md"

st.set_page_config(page_title="ReactorQ Studio | CB-PFR", page_icon="⚛", layout="wide")

# A restrained scientific workstation aesthetic: bright canvas, ink typography,
# fine grid lines, clear chart hierarchy, and compact controls.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --ink:#172638; --muted:#68788a; --line:#dce4ec; --panel:#ffffff; --canvas:#f3f6fa; --blue:#245b88; --cyan:#13a6b4; }
.stApp { background:#f3f6fa; color:var(--ink); font-family:'Manrope',sans-serif; }
.block-container { max-width:1680px; padding-top:1.3rem; padding-bottom:2.5rem; }
[data-testid="stSidebar"] { background:#101f31; border-right:1px solid #23384e; }
[data-testid="stSidebar"] * { color:#e4edf5 !important; }
h1,h2,h3 { letter-spacing:-.035em; color:#172638; }
h1 { font-size:2.15rem !important; font-weight:800 !important; }
h2 { font-size:1.35rem !important; font-weight:800 !important; }
h3 { font-size:1.04rem !important; font-weight:750 !important; }
p,li { color:#425469; }
.hero { background:linear-gradient(115deg,#10243a 0%,#173c58 65%,#17616c 100%); color:white; border-radius:18px; padding:25px 30px; margin-bottom:18px; box-shadow:0 8px 28px rgba(21,49,73,.12); }
.hero .eyebrow { color:#7ce3e8; text-transform:uppercase; letter-spacing:.16em; font:500 .7rem 'DM Mono',monospace; }
.hero h1 { color:white; margin:.45rem 0 .35rem; font-size:2.2rem !important; }
.hero p { color:#d4e2ee; max-width:900px; margin:0; }
.status { display:inline-block; border:1px solid #b77924; color:#8a5207; background:#fff5df; border-radius:5px; padding:4px 8px; font:500 .69rem 'DM Mono',monospace; letter-spacing:.04em; }
.panel { background:white; border:1px solid #dce4ec; border-radius:13px; padding:16px 18px; }
.section-label { font:500 .68rem 'DM Mono',monospace; color:#148b9a; text-transform:uppercase; letter-spacing:.14em; margin-bottom:4px; }
.small-muted { color:#6b7b8e; font-size:.79rem; }
div[data-testid="stMetric"] { background:white; border:1px solid #dce4ec; border-radius:12px; padding:13px 16px; box-shadow:0 2px 8px rgba(21,49,73,.025); }
div[data-testid="stMetricLabel"] { color:#6b7b8e; }
div[data-testid="stMetricValue"] { color:#17334d; font-weight:800; }
.stTabs [data-baseweb="tab-list"] { gap:8px; }
.stTabs [data-baseweb="tab"] { background:#e8eef4; border-radius:8px 8px 0 0; padding:9px 14px; }
hr { border-color:#dce4ec; }
div[data-testid="stDataFrame"] { border:1px solid #dce4ec; border-radius:9px; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_runs() -> pd.DataFrame:
    if not RUNS_CSV.exists():
        return pd.DataFrame()
    out = pd.read_csv(RUNS_CSV)
    for col in ["keff_mean", "keff_std_dev", "fission_rate_peaking_factor", "R_p00", "R_p01", "R_p10", "R_p11"]:
        if col in out:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def layout_matrix(signature: str):
    # Signature order follows row-major assembly positions p00, p01, p10, p11.
    letters = list(str(signature).upper())
    if len(letters) != 4 or any(x not in "UM" for x in letters):
        return [["?", "?"], ["?", "?"]]
    return [[letters[0], letters[1]], [letters[2], letters[3]]]


def assembly_map(signature: str):
    matrix = layout_matrix(signature)
    colors = {"U": "#e5b65c", "M": "#3c91b8", "?": "#aeb9c4"}
    fig = go.Figure()
    for r in range(2):
        for c in range(2):
            mat = matrix[r][c]
            fig.add_shape(type="rect", x0=c, y0=1-r, x1=c+1, y1=2-r,
                          line=dict(color="#ffffff", width=5), fillcolor=colors[mat])
            fig.add_annotation(x=c+.5, y=1.5-r, text=f"<b>{mat}</b><br><sup>p{r}{c}</sup>",
                               showarrow=False, font=dict(size=19, color="#172638"))
    fig.update_xaxes(range=[0,2], showticklabels=False, showgrid=False, zeroline=False, title="Assembly position")
    fig.update_yaxes(range=[0,2], showticklabels=False, showgrid=False, zeroline=False, scaleanchor="x", scaleratio=1)
    fig.update_layout(height=370, margin=dict(l=8,r=8,t=8,b=36), paper_bgcolor="white", plot_bgcolor="white",
                      showlegend=False, title=dict(text="2 × 2 material placement", x=.02, font=dict(size=15)))
    return fig


def position_heatmap(row):
    # Actual tally-derived position contributions recorded in the evidence CSV,
    # not a reconstructed flux field.
    vals = [[row.get("R_p00", float("nan")), row.get("R_p01", float("nan"))],
            [row.get("R_p10", float("nan")), row.get("R_p11", float("nan"))]]
    fig = go.Figure(data=go.Heatmap(z=vals, x=["p00", "p01"], y=["p10", "p11"],
                                    colorscale="YlOrRd", text=[[f"{v:.4f}" for v in line] for line in vals],
                                    texttemplate="%{text}", textfont=dict(size=14), colorbar=dict(title="Recorded<br>proxy")))
    fig.update_layout(height=370, margin=dict(l=8,r=8,t=8,b=8), paper_bgcolor="white", plot_bgcolor="white",
                      title=dict(text="Four-position tally contribution", x=.02, font=dict(size=15)))
    fig.update_yaxes(autorange="reversed", title="")
    fig.update_xaxes(title="")
    return fig


def spatial_tally_plot(uploaded):
    if uploaded is None:
        return None, "Upload a CSV exported from a real OpenMC mesh tally. Required columns: x, y, value. No synthetic field is displayed."
    try:
        data = pd.read_csv(uploaded)
    except Exception as exc:
        return None, f"CSV could not be read: {exc}"
    data.columns = [str(c).strip().lower() for c in data.columns]
    required = {"x", "y", "value"}
    if not required.issubset(data.columns):
        return None, "CSV schema mismatch. Required columns: x, y, value."
    for col in ["x", "y", "value"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=["x", "y", "value"])
    if data.empty:
        return None, "No numeric spatial tally records found."
    pivot = data.pivot_table(index="y", columns="x", values="value", aggfunc="mean").sort_index(ascending=True)
    fig = go.Figure(go.Heatmap(z=pivot.values, x=pivot.columns, y=pivot.index, colorscale="Viridis",
                               colorbar=dict(title="Tally value"), hovertemplate="x=%{x}<br>y=%{y}<br>value=%{z:.5g}<extra></extra>"))
    fig.update_layout(height=570, margin=dict(l=12,r=12,t=18,b=12), paper_bgcolor="white", plot_bgcolor="white",
                      xaxis_title="x (CSV coordinate)", yaxis_title="y (CSV coordinate)")
    return fig, f"Showing {len(data):,} actual spatial records. Verify tally normalization and units before interpreting this map."


df = load_runs()
with st.sidebar:
    st.markdown("## ⚛ REACTORQ")
    st.caption("CB-PFR / C5G7 research workstation")
    st.markdown("---")
    page = st.radio("WORKSPACE", ["Reactor map", "Physics results", "Layout lab", "Run provenance", "Validation gates"], index=0)
    st.markdown("---")
    st.markdown("**DATA SOURCE**")
    st.caption("Committed C5G7 2×2 repeatability smoke study")
    st.caption("18 runs · 6 layouts · 3 seed rounds")
    st.markdown('<span class="status">EXPLORATORY DATA</span>', unsafe_allow_html=True)
    st.markdown("---")
    st.caption("This UI visualizes evidence; it does not run OpenMC.")

st.markdown("""
<div class="hero">
  <div class="eyebrow">CB-PFR · Computational reactor physics · Evidence-first</div>
  <h1>ReactorQ Studio</h1>
  <p>Inspect material placement, tally-derived spatial contributions, Monte Carlo variability, and evidence quality in one visual workspace.</p>
</div>
""", unsafe_allow_html=True)

if df.empty:
    st.error(f"Evidence CSV not found: {RUNS_CSV.relative_to(ROOT)}")
    st.info("Run this app from the repository checkout that contains the corrected-group study artifacts.")
    st.stop()

df["layout_signature"] = df["layout_signature"].astype(str)
summary = df.groupby("layout_signature", as_index=False).agg(
    runs=("seed", "count"), keff_mean=("keff_mean", "mean"), keff_sd_between=("keff_mean", "std"),
    keff_run_sd=("keff_std_dev", "mean"), fission_mean=("fission_rate_peaking_factor", "mean"),
    fission_sd_between=("fission_rate_peaking_factor", "std"),
    audit_pass=("group_structure_audit", lambda x: int((x == "PASS").sum())))
summary["fission_cv_pct"] = 100 * summary["fission_sd_between"] / summary["fission_mean"]
layouts = sorted(df["layout_signature"].unique().tolist())

if page == "Reactor map":
    st.markdown('<div class="section-label">01 / Geometry explorer</div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Recorded transport runs", f"{len(df)}")
    m2.metric("Candidate placements", f"{len(layouts)}")
    m3.metric("Group audits passed", f"{int((df['group_structure_audit'] == 'PASS').sum())}/{len(df)}")
    m4.metric("Physical design verdict", "NOT SET", "Acceptance criteria unresolved")
    st.markdown("")
    left, right = st.columns([1.05, 1])
    with left:
        selected = st.selectbox("Select material placement", layouts, index=layouts.index("UMMU") if "UMMU" in layouts else 0)
        st.plotly_chart(assembly_map(selected), use_container_width=True, config={"displayModeBar": False})
        st.markdown('<div class="small-muted">U = UO₂ assembly · M = MOX assembly. This is the study’s 2×2 assembly-placement abstraction, not a full pin-by-pin C5G7 geometry rendering.</div>', unsafe_allow_html=True)
    with right:
        chosen = df[df["layout_signature"] == selected].sort_values("round").iloc[-1]
        st.plotly_chart(position_heatmap(chosen), use_container_width=True, config={"displayModeBar": False})
        st.markdown('<div class="small-muted">Values are the recorded four-position tally contributions for the selected run. They are not a full-core neutron-flux or absolute-power map.</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("Spatial tally viewer")
    st.write("For a true 2D flux / fission-rate map, load the exported mesh-tally data from the OpenMC statepoint.")
    uploaded = st.file_uploader("OpenMC mesh tally CSV (columns: x, y, value)", type=["csv"], key="mesh_upload")
    fig, note = spatial_tally_plot(uploaded)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
        st.caption(note)
    else:
        st.info(note)
    st.warning("Current committed study is a smoke test. Do not interpret its layout colors or tally proxy as a validated reactor design or safety result.")

elif page == "Physics results":
    st.markdown('<div class="section-label">02 / Physics response</div>', unsafe_allow_html=True)
    st.subheader("k-effective by candidate and seed round")
    by_run = df.sort_values(["round", "layout_signature"])
    fig = px.line(by_run, x="round", y="keff_mean", color="layout_signature", markers=True,
                  hover_data=["candidate_id", "seed", "keff_std_dev"], labels={"round":"Seed round", "keff_mean":"k-effective", "layout_signature":"Layout"})
    fig.update_layout(height=420, paper_bgcolor="white", plot_bgcolor="white", margin=dict(l=10,r=10,t=20,b=10), legend_title_text="Placement")
    fig.update_yaxes(gridcolor="#e5ebf1")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Each point is an individual low-budget run. This is a descriptive repeatability plot, not a convergence certificate.")
    a, b = st.columns(2)
    with a:
        st.subheader("Fission-rate peaking proxy")
        fig2 = px.box(df, x="layout_signature", y="fission_rate_peaking_factor", points="all",
                      labels={"layout_signature":"Placement", "fission_rate_peaking_factor":"Relative peaking proxy"})
        fig2.update_layout(height=360, paper_bgcolor="white", plot_bgcolor="white", showlegend=False)
        fig2.update_yaxes(gridcolor="#e5ebf1")
        st.plotly_chart(fig2, use_container_width=True)
    with b:
        st.subheader("Mean k-effective by layout")
        s = summary.sort_values("keff_mean")
        fig3 = px.bar(s, x="layout_signature", y="keff_mean", error_y="keff_sd_between",
                      labels={"layout_signature":"Placement", "keff_mean":"Mean k-effective"})
        fig3.update_layout(height=360, paper_bgcolor="white", plot_bgcolor="white")
        fig3.update_yaxes(gridcolor="#e5ebf1")
        st.plotly_chart(fig3, use_container_width=True)
    st.markdown('<div class="small-muted">Between-seed error bars are descriptive standard deviations across only three runs, not calibrated confidence intervals. The fission quantity is a relative shape proxy, not absolute power.</div>', unsafe_allow_html=True)

elif page == "Layout lab":
    st.markdown('<div class="section-label">03 / Candidate comparison</div>', unsafe_allow_html=True)
    chosen_metric = st.selectbox("Compare layouts using", ["fission_mean", "keff_mean", "fission_cv_pct"],
        format_func=lambda x: {"fission_mean":"Mean fission peaking proxy", "keff_mean":"Mean k-effective", "fission_cv_pct":"Between-seed variability (%)"}[x])
    labels = {"fission_mean":"Mean fission peaking proxy", "keff_mean":"Mean k-effective", "fission_cv_pct":"Fission proxy CV (%)"}
    ordered = summary.sort_values(chosen_metric, ascending=(chosen_metric != "keff_mean"))
    fig = px.bar(ordered, x="layout_signature", y=chosen_metric, color="layout_signature",
                 labels={"layout_signature":"2×2 placement", chosen_metric:labels[chosen_metric]})
    fig.update_layout(height=410, paper_bgcolor="white", plot_bgcolor="white", showlegend=False)
    fig.update_yaxes(gridcolor="#e5ebf1")
    st.plotly_chart(fig, use_container_width=True)
    left, right = st.columns([.9, 1.1])
    with left:
        chosen = st.selectbox("Inspect layout", layouts, key="layout_inspect")
        st.plotly_chart(assembly_map(chosen), use_container_width=True, config={"displayModeBar": False})
    with right:
        row = summary[summary["layout_signature"] == chosen].iloc[0]
        st.markdown("#### Replicate summary")
        st.metric("Mean k-effective", f"{row.keff_mean:.6f}", f"between-seed SD {row.keff_sd_between:.6f}")
        st.metric("Mean fission proxy", f"{row.fission_mean:.4f}", f"between-seed SD {row.fission_sd_between:.4f}")
        st.metric("Runs / group audits", f"{int(row.runs)} / {int(row.audit_pass)}")
        st.caption("Descriptive comparison only. No winner is declared because acceptance criteria and benchmark-grade convergence are unresolved.")
    st.dataframe(summary.rename(columns={"layout_signature":"Layout","runs":"Runs","keff_mean":"Mean k-effective","keff_sd_between":"Between-seed SD(k)","fission_mean":"Mean fission proxy","fission_sd_between":"Between-seed SD(proxy)","fission_cv_pct":"Proxy CV (%)","audit_pass":"Group audits passed"}).round(6), use_container_width=True, hide_index=True)

elif page == "Run provenance":
    st.markdown('<div class="section-label">04 / Reproducibility</div>', unsafe_allow_html=True)
    layout_filter = st.selectbox("Filter layout", ["All"] + layouts)
    filtered = df if layout_filter == "All" else df[df["layout_signature"] == layout_filter]
    run_filter = st.multiselect("Seed rounds", sorted(filtered["round"].unique()), default=sorted(filtered["round"].unique()))
    filtered = filtered[filtered["round"].isin(run_filter)]
    a, b = st.columns(2)
    with a:
        fig = px.scatter(filtered, x="keff_mean", y="fission_rate_peaking_factor", color="layout_signature",
                         symbol="round", hover_data=["candidate_id", "seed", "keff_std_dev"],
                         labels={"keff_mean":"k-effective", "fission_rate_peaking_factor":"Fission peaking proxy"})
        fig.update_layout(height=390, paper_bgcolor="white", plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
    with b:
        st.markdown("#### Integrity snapshot")
        st.metric("Unique statepoint hashes", f"{filtered['statepoint_sha256'].nunique()} / {len(filtered)}")
        st.metric("Unique MGXS hashes", f"{filtered['mgxs_sha256'].nunique()}")
        st.metric("Group-structure audit pass", f"{int((filtered['group_structure_audit'] == 'PASS').sum())} / {len(filtered)}")
        st.caption("Hashes support provenance and identity checks; they do not establish physical validity.")
    cols = ["round","layout_signature","candidate_id","seed","keff_mean","keff_std_dev","fission_rate_peaking_factor","group_structure_audit","statepoint_sha256","mgxs_sha256"]
    st.dataframe(filtered[cols], use_container_width=True, hide_index=True)
    st.download_button("Export filtered run records", filtered.to_csv(index=False).encode("utf-8"), "cbpfr_filtered_run_records.csv", "text/csv")

else:
    st.markdown('<div class="section-label">05 / Evidence and acceptance gates</div>', unsafe_allow_html=True)
    st.subheader("Scientific validity is separate from visual polish")
    gates = [
        ("Run records", "PASS", "18 recorded smoke-study runs; three per layout."),
        ("Corrected C5G7 group structure", "PASS", "All recorded runs passed the group-structure audit."),
        ("Statepoint uniqueness", "RECORDED", "Unique statepoint hashes are present in the study data."),
        ("Common MGXS identity", "PASS", "The runs record one common MGXS hash."),
        ("Benchmark-grade convergence", "OPEN", "Smoke budget is insufficient to claim benchmark-grade convergence."),
        ("Spatial flux / absolute power field", "NOT LOADED", "Upload a real mesh-tally CSV in Reactor map; this app will not synthesize a field."),
        ("Approved k-effective acceptance band", "OPEN", "No approved design-specific band is encoded."),
        ("Legacy burnup QUBO → C5G7 mapping", "BLOCKED", "A defensible mapping has not been established."),
        ("Final design recommendation", "BLOCKED", "Requires validated physics, explicit acceptance limits, and a predeclared ranking protocol."),
    ]
    for title, status, detail in gates:
        color = {"PASS":"#087f68","RECORDED":"#236a9c","OPEN":"#99620c","BLOCKED":"#b43d36","NOT LOADED":"#6b7280"}[status]
        st.markdown(f'<div class="panel" style="display:flex;gap:18px;align-items:flex-start;margin:8px 0;padding:13px 16px"><div style="min-width:112px;color:{color};font:500 .72rem DM Mono,monospace;padding-top:3px">{status}</div><div><b>{title}</b><div class="small-muted">{detail}</div></div></div>', unsafe_allow_html=True)
    if REPORT.exists():
        with st.expander("Read interpretation of the current study"):
            st.markdown(REPORT.read_text(encoding="utf-8"))

st.markdown("---")
st.markdown('<div class="small-muted">ReactorQ Studio · CB-PFR prototype · Visual exploration is not a reactor safety assessment. Physical fields must be derived from audited OpenMC tallies.</div>', unsafe_allow_html=True)
