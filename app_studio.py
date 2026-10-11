"""ReactorQ Studio — scientific UI prototype for CB-PFR / C5G7 evidence.

This is an additive prototype. It does not modify app.py or run OpenMC.
All physical-study values are loaded from committed CSV evidence; no synthetic
reactor values are generated here. Smoke-study results are clearly labelled
exploratory and cannot trigger a candidate recommendation.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
RUNS_CSV = ROOT / "results/c5g7_corrected_group_repeatability_smoke_2026-10-11/run_level_fission_objective.csv"
REPORT = ROOT / "reports/c5g7_corrected_group_repeatability_smoke_2026-10-11.md"

st.set_page_config(
    page_title="ReactorQ Studio | CB-PFR",
    page_icon="⚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
:root { --ink:#e8eef7; --muted:#92a3b9; --panel:#111d2c; --line:#27384d; --cyan:#56d7e5; --amber:#f2bb64; }
.stApp { background: radial-gradient(ellipse at 80% 0%, #142d43 0%, #0b1420 42%, #08111b 100%); color:var(--ink); }
.block-container { max-width: 1500px; padding-top: 1.6rem; padding-bottom: 3rem; }
[data-testid="stSidebar"] { background:#0b1623; border-right:1px solid #24354a; }
h1,h2,h3 { letter-spacing:-.025em; }
h1 { font-size:2.15rem !important; }
p,li,label { color:#c8d4e3; }
.hero { border:1px solid #2a465e; border-radius:18px; padding:24px 28px; background:linear-gradient(115deg,rgba(27,61,83,.92),rgba(13,28,43,.84)); margin-bottom:18px; }
.eyebrow { color:#65dce8; font-size:.73rem; font-weight:750; letter-spacing:.16em; text-transform:uppercase; }
.hero h1 { margin:.45rem 0 .35rem 0; color:#f3f7fc; }
.hero p { color:#b4c5d8; margin-bottom:0; max-width:900px; }
.pill { display:inline-block; border:1px solid #70582d; background:#332a1b; color:#ffd58a; border-radius:999px; padding:4px 10px; font-size:.72rem; font-weight:700; }
.section-kicker { color:#67d8e5; text-transform:uppercase; letter-spacing:.12em; font-size:.72rem; font-weight:750; margin-bottom:5px; }
.note { border-left:3px solid #e6b45e; background:#211f1a; padding:12px 15px; border-radius:0 9px 9px 0; color:#f0dfbd; font-size:.9rem; }
.good { border-left:3px solid #55c9b4; background:#102a2b; padding:12px 15px; border-radius:0 9px 9px 0; color:#c8f3e8; font-size:.9rem; }
.small-muted { color:#8fa3b9; font-size:.82rem; }
div[data-testid="stMetric"] { background:rgba(16,30,45,.88); border:1px solid #283b50; padding:14px 16px; border-radius:13px; }
div[data-testid="stMetricLabel"] { color:#9fb1c5; }
div[data-testid="stMetricValue"] { color:#eff6ff; }
.stTabs [data-baseweb="tab-list"] { gap:8px; }
.stTabs [data-baseweb="tab"] { background:#101e2d; border:1px solid #283b50; border-radius:9px 9px 0 0; padding:8px 14px; }
hr { border-color:#26394d; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_runs() -> pd.DataFrame:
    if not RUNS_CSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(RUNS_CSV)
    numeric = ["keff_mean", "keff_std_dev", "fission_rate_peaking_factor"]
    for col in numeric:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


df = load_runs()
with st.sidebar:
    st.markdown("## ⚛ ReactorQ")
    st.caption("CB-PFR · Scientific workbench")
    st.markdown("---")
    page = st.radio(
        "WORKSPACE",
        ["Research overview", "C5G7 layout study", "Run-level explorer", "Evidence & validation gates"],
        label_visibility="visible",
    )
    st.markdown("---")
    st.markdown("**Active evidence set**")
    st.caption("C5G7 · corrected 7-group structure")
    st.caption("18 runs · 6 layouts · 3 seed rounds")
    st.markdown('<span class="pill">EXPLORATORY ONLY</span>', unsafe_allow_html=True)
    st.markdown("---")
    st.caption("Prototype UI · reads repository evidence")
    st.caption("No transport run is launched by this dashboard.")

st.markdown("""
<div class="hero">
  <div class="eyebrow">Computational reactor research · evidence-first interface</div>
  <h1>ReactorQ Studio</h1>
  <p>Explore candidate layouts, Monte Carlo variability, QUBO formulation, and validation status in one auditable workspace.</p>
  <p style="margin-top:14px"><span class="pill">SMOKE STUDY — NOT A DESIGN RECOMMENDATION</span></p>
</div>
""", unsafe_allow_html=True)

if df.empty:
    st.error(f"Evidence CSV not found: {RUNS_CSV.relative_to(ROOT)}")
    st.info("Run this app from the repository checkout after syncing the corrected-group study artifacts.")
    st.stop()

df["layout_signature"] = df["layout_signature"].astype(str)
summary = df.groupby("layout_signature", as_index=False).agg(
    runs=("seed", "count"),
    keff_mean=("keff_mean", "mean"),
    keff_between_seed_sd=("keff_mean", "std"),
    fission_peaking_mean=("fission_rate_peaking_factor", "mean"),
    fission_peaking_between_seed_sd=("fission_rate_peaking_factor", "std"),
    group_audits=("group_structure_audit", lambda s: (s == "PASS").sum()),
)
summary["fission_cv_pct"] = 100 * summary["fission_peaking_between_seed_sd"] / summary["fission_peaking_mean"]
summary = summary.sort_values("fission_peaking_mean", ascending=True).reset_index(drop=True)

if page == "Research overview":
    st.markdown('<div class="section-kicker">01 / Research status</div>', unsafe_allow_html=True)
    a, b, c, d = st.columns(4)
    a.metric("Run records", f"{len(df)}", "3 independent seed rounds")
    b.metric("Candidate layouts", f"{df['layout_signature'].nunique()}", "2×2 UO₂/MOX study")
    c.metric("Group audits passed", f"{(df['group_structure_audit'] == 'PASS').sum()}/{len(df)}", "standard C5G7 boundaries")
    d.metric("Design selection", "BLOCKED", "acceptance band not approved")
    st.markdown("")
    left, right = st.columns([1.25, 1])
    with left:
        st.subheader("Study pipeline")
        st.markdown("""
        <div class="good"><b>Evidence integrity checks passed</b><br>Unique statepoint hashes, corrected MGXS identity, and group-structure audits are recorded for this smoke study.</div>
        <br>
        <div class="note"><b>Scientific decision remains gated</b><br>The run budget is exploratory; no design-specific acceptable k<sub>eff</sub> band has been approved, and the fission metric is a relative shape proxy—not absolute power.</div>
        """, unsafe_allow_html=True)
        st.markdown("#### Workflow")
        st.code("Layout definition  →  OpenMC transport  →  statepoint audit  →  tally-derived metrics  →  repeatability analysis  →  validation gate", language="text")
    with right:
        st.subheader("Evidence boundary")
        st.markdown("""
        - **Measured from committed outputs:** run-level k-effective, fission-peaking proxy, seed, statepoint hash, MGXS hash, group audit.
        - **Not established:** benchmark-grade convergence, accepted design window, final physical winner.
        - **Separate formulation:** the four-position UO₂/MOX layout QUBO is not the legacy fresh/once-burned/twice-burned QUBO.
        - **No silent inference:** the dashboard never converts a proxy ranking into a safety or power claim.
        """)
    st.markdown("---")
    st.subheader("At-a-glance layout comparison")
    chart_data = summary.set_index("layout_signature")[["keff_mean", "fission_peaking_mean"]]
    st.bar_chart(chart_data, height=280)
    st.caption("Different physical meanings and scales: use the detailed view to inspect each metric separately. This chart is descriptive, not a multi-objective decision rule.")

elif page == "C5G7 layout study":
    st.markdown('<div class="section-kicker">02 / Candidate analysis</div>', unsafe_allow_html=True)
    st.subheader("Six 2×2 UO₂/MOX placement candidates")
    st.markdown('<div class="note">Ranks below are descriptive ordering by mean fission-rate peaking proxy only. They are not recommendations; the k-effective acceptance gate is unresolved.</div>', unsafe_allow_html=True)
    metric = st.selectbox("View metric", ["fission_peaking_mean", "keff_mean", "fission_cv_pct"], format_func=lambda x: {
        "fission_peaking_mean": "Mean fission-rate peaking proxy ↓",
        "keff_mean": "Mean k-effective",
        "fission_cv_pct": "Between-seed coefficient of variation (%)",
    }[x])
    ordered = summary.sort_values(metric, ascending=(metric != "keff_mean"))
    chart = ordered.set_index("layout_signature")[[metric]].rename(columns={metric: metric.replace("_", " ").title()})
    st.bar_chart(chart, height=330)
    display = ordered[["layout_signature", "runs", "keff_mean", "keff_between_seed_sd", "fission_peaking_mean", "fission_peaking_between_seed_sd", "fission_cv_pct", "group_audits"]].copy()
    display.columns = ["Layout", "Runs", "Mean k-effective", "Between-seed SD(k)", "Mean fission proxy", "Between-seed SD(F)", "CV(F), %", "Group audits passed"]
    st.dataframe(display.style.format({
        "Mean k-effective": "{:.6f}", "Between-seed SD(k)": "{:.6f}",
        "Mean fission proxy": "{:.6f}", "Between-seed SD(F)": "{:.6f}", "CV(F), %": "{:.3f}",
    }), use_container_width=True, hide_index=True)
    st.caption("Between-seed SD is descriptive across three independent runs per layout; it is not a calibrated confidence interval.")

elif page == "Run-level explorer":
    st.markdown('<div class="section-kicker">03 / Provenance and variability</div>', unsafe_allow_html=True)
    st.subheader("Inspect individual transport runs")
    layouts = ["All layouts"] + sorted(df["layout_signature"].unique().tolist())
    selected_layout = st.selectbox("Layout filter", layouts)
    filtered = df if selected_layout == "All layouts" else df[df["layout_signature"] == selected_layout]
    rounds = ["All rounds"] + sorted(filtered["round"].unique().tolist())
    selected_round = st.selectbox("Seed round", rounds)
    if selected_round != "All rounds":
        filtered = filtered[filtered["round"] == selected_round]
    x, y = st.columns(2)
    with x:
        st.markdown("**k-effective by run**")
        st.bar_chart(filtered.set_index("candidate_id")[["keff_mean"]], height=270)
    with y:
        st.markdown("**Fission-rate peaking proxy by run**")
        st.bar_chart(filtered.set_index("candidate_id")[["fission_rate_peaking_factor"]], height=270)
    cols = ["round", "layout_signature", "candidate_id", "seed", "keff_mean", "keff_std_dev", "fission_rate_peaking_factor", "group_structure_audit", "statepoint_sha256", "mgxs_sha256"]
    st.dataframe(filtered[cols], use_container_width=True, hide_index=True)
    st.download_button("Download filtered run records (CSV)", filtered.to_csv(index=False).encode("utf-8"), "cbpfr_c5g7_filtered_runs.csv", "text/csv")
    st.caption("Hashes are shown for traceability. A matching hash is an identity/provenance check, not proof of model validity.")

else:
    st.markdown('<div class="section-kicker">04 / Scientific acceptance gates</div>', unsafe_allow_html=True)
    st.subheader("What the current evidence does—and does not—support")
    gates = [
        ("Run-record completeness", "PASS", "18 run records present; three runs per layout."),
        ("Statepoint uniqueness", "RECORDED", "The accompanying audit checks unique statepoint hashes."),
        ("C5G7 energy-group structure", "PASS", "Corrected standard seven-group boundaries audited in all 18 runs."),
        ("Common MGXS identity", "PASS", "All corrected-group runs use the same recorded MGXS hash."),
        ("Benchmark-grade convergence", "OPEN", "Smoke budget: 100 batches, 10 inactive, 1,000 particles/batch."),
        ("Design-specific k-effective acceptance band", "OPEN", "No approved band is available; no winner can be declared."),
        ("Legacy burnup-QUBO to UO₂/MOX mapping", "BLOCKED", "No defensible mapping is established; keep formulations separate."),
        ("Final candidate recommendation", "BLOCKED", "Requires validated model, approved limits, and predeclared ranking protocol."),
    ]
    for title, status, detail in gates:
        color = {"PASS":"#55c9b4", "RECORDED":"#69c9e8", "OPEN":"#f2bb64", "BLOCKED":"#ff8f83"}[status]
        st.markdown(f"""
        <div style="display:flex;gap:14px;align-items:flex-start;padding:13px 15px;border:1px solid #283b50;border-radius:11px;background:rgba(16,30,45,.78);margin:8px 0">
          <div style="min-width:110px;color:{color};font-size:.75rem;font-weight:800;letter-spacing:.08em;padding-top:2px">{status}</div>
          <div><div style="font-weight:700;color:#eaf1fa">{title}</div><div class="small-muted">{detail}</div></div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("Next research actions")
    st.markdown("""
    1. Run the canonical UMMU configuration at a higher common transport budget with independent seeds.
    2. Review primary C5G7 benchmark specifications and the tally-to-assembly integration.
    3. Predeclare a design-specific acceptable k-effective band and ranking protocol with domain justification.
    4. Keep the legacy burnup-state QUBO separate until traceable material/depletion mapping exists.
    """)
    if REPORT.exists():
        with st.expander("Open the study interpretation"):
            st.markdown(REPORT.read_text(encoding="utf-8"))

st.markdown("---")
st.markdown('<div class="small-muted">ReactorQ Studio · CB-PFR research prototype · Interface does not certify reactor safety or automatically validate physical models.</div>', unsafe_allow_html=True)
