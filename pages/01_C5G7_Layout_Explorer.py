"""C5G7 layout explorer for the CB-PFR research workstation.

All numeric rows come from the committed exploratory smoke-run CSV. The 2x2
layout is the explicitly defined design study, not a full-core geometry model.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="CB-PFR · C5G7 Layout Explorer", page_icon="⚛", layout="wide")

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "c5g7_layout_smoke_2026-10-10" / "candidate_summary.csv"

st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp { background: #06101e; color: #dceaff; }
[data-testid="stHeader"] { background: rgba(4, 14, 28, .92); }
.block-container { max-width: 1680px; padding-top: 1.25rem; padding-bottom: 2rem; }
section[data-testid="stSidebar"] { background: #07182b; border-right: 1px solid #153a5e; }
.hero { border: 1px solid #174b7b; border-radius: 12px; padding: 20px 24px;
        background: linear-gradient(115deg,#0b2745 0%,#07192c 62%,#08243b 100%); }
.eyebrow { color: #48c7ff; font-size: 11px; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; }
.hero h1 { margin: 4px 0 4px 0; font-size: 30px; color: #f0f7ff; }
.subtle { color: #93b0ce; font-size: 13px; }
.panel { border: 1px solid #153a5e; border-radius: 10px; background: #07192b; padding: 16px; }
.panel-title { font-size: 14px; font-weight: 650; color: #dceaff; margin-bottom: 12px; }
.status { display:inline-block; border:1px solid #805b26; border-radius:20px; padding:3px 9px;
          color:#ffd58a; font-size:11px; font-weight:650; letter-spacing:.03em; }
.metric-label { color:#8fb0d2; font-size:12px; }
.metric-value { color:#edf6ff; font-size:24px; font-weight:650; margin-top:3px; }
small { color:#8fb0d2; }
div[data-testid="stMetric"] { background:#081c30; border:1px solid #153a5e; padding:12px 14px; border-radius:9px; }
div[data-testid="stMetricLabel"] { color:#91b3d4; }
div[data-testid="stMetricValue"] { color:#edf6ff; }
.stButton button, .stDownloadButton button { border-radius:7px; border:1px solid #1d6da8; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="eyebrow">CB-PFR · Computational Burnup &amp; Physics for Reactor</div>
  <h1>C5G7 Layout Explorer</h1>
  <div class="subtle">Assembly-placement study · evidence-linked geometry · exploratory OpenMC results</div>
  <div style="margin-top:14px"><span class="status">SMOKE STUDY · NOT BENCHMARK-GRADE</span></div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### WORKSPACE")
    st.caption("C5G7 · 2×2 material-placement formulation")
    st.markdown("---")
    st.markdown("**Study inputs**")
    st.code("4 assembly positions\n2 × UO₂ + 2 × MOX\n6 feasible layouts", language="text")
    st.markdown("**Material key**")
    st.markdown("🟠 **UO₂** — uranium oxide")
    st.markdown("🟣 **MOX** — mixed oxide")
    st.markdown("---")
    st.caption("Data source")
    st.code("results/c5g7_layout_smoke_2026-10-10/candidate_summary.csv", language="text")

st.markdown("#### Study status")
st.write(
    "This page visualizes the repository's explicit four-position C5G7 layout study. "
    "It does **not** reconstruct the full benchmark core or map the legacy burnup-state QUBO to materials."
)

if not RESULTS.exists():
    st.error(f"Evidence CSV not found at {RESULTS}. Run this page from the repository root or restore the committed results file.")
    st.stop()

df = pd.read_csv(RESULTS)
required = {"candidate_id", "layout_signature", "canonical_reference", "seed", "batches",
            "inactive", "particles_per_batch", "keff_mean", "keff_std_dev",
            "aggregate_flux_score", "aggregate_fission_score"}
missing = required.difference(df.columns)
if missing:
    st.error("The evidence file is missing required columns: " + ", ".join(sorted(missing)))
    st.stop()

candidate_labels = {
    row["candidate_id"]: f'{row["candidate_id"]}  ·  {row["layout_signature"]}'
    for _, row in df.iterrows()
}
chosen_id = st.selectbox("Selected layout", df["candidate_id"].tolist(),
                         format_func=lambda value: candidate_labels[value])
row = df.loc[df["candidate_id"] == chosen_id].iloc[0]
signature = str(row["layout_signature"])
if len(signature) != 4 or any(char not in "UM" for char in signature):
    st.error(f"Unexpected layout signature: {signature!r}. Expected four U/M positions.")
    st.stop()

left, right = st.columns([1.35, 1], gap="large")
with left:
    st.markdown('<div class="panel"><div class="panel-title">Assembly placement map</div>', unsafe_allow_html=True)
    st.caption("Position order: p00 · p01 · p10 · p11. U = UO₂, M = MOX.")
    positions = [
        ("p00", signature[0]), ("p01", signature[1]),
        ("p10", signature[2]), ("p11", signature[3]),
    ]
    grid = st.columns(2, gap="medium")
    for idx, (position, material) in enumerate(positions):
        color = "#ff5a36" if material == "U" else "#a66bff"
        label = "UO₂" if material == "U" else "MOX"
        with grid[idx % 2]:
            st.markdown(
                f'<div style="border:1px solid {color};border-radius:10px;'
                f'background:linear-gradient(145deg,{color}24,#07192b);'
                f'min-height:120px;padding:16px;margin:5px 0;text-align:center">'
                f'<div style="font-size:11px;color:#8fb0d2">{position}</div>'
                f'<div style="font-size:30px;font-weight:750;color:{color};margin:8px 0">{label}</div>'
                f'<div style="font-size:11px;color:#a9c3de">Assembly material</div></div>',
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)
    st.caption("Schematic only: this is the explicit 2×2 design-space representation, not a spatially resolved transport mesh.")

with right:
    st.markdown('<div class="panel"><div class="panel-title">Selected candidate</div>', unsafe_allow_html=True)
    st.markdown(f"**{row['candidate_id']}**")
    st.code(f"layout_signature = {signature}\nrandom_seed = {int(row['seed'])}", language="text")
    st.metric("k-effective · mean", f"{row['keff_mean']:.6f}", delta=f"± {row['keff_std_dev']:.6f} reported std. dev.")
    st.metric("Aggregate flux score", f"{row['aggregate_flux_score']:.5f}")
    st.metric("Aggregate fission score", f"{row['aggregate_fission_score']:.5f}")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("#### Run provenance")
p1, p2, p3, p4 = st.columns(4)
p1.metric("Batches", f"{int(row['batches']):,}")
p2.metric("Inactive batches", f"{int(row['inactive']):,}")
p3.metric("Particles / batch", f"{int(row['particles_per_batch']):,}")
p4.metric("Canonical reference", "Yes" if bool(row["canonical_reference"]) else "No")

st.markdown("#### Candidate comparison")
view = df[["candidate_id", "layout_signature", "canonical_reference", "seed", "keff_mean",
           "keff_std_dev", "aggregate_flux_score", "aggregate_fission_score"]].copy()
view["canonical_reference"] = view["canonical_reference"].map({True: "Yes", False: "No"})
st.dataframe(
    view.sort_values("candidate_id"),
    use_container_width=True,
    hide_index=True,
    column_config={
        "candidate_id": st.column_config.TextColumn("Candidate"),
        "layout_signature": st.column_config.TextColumn("Layout"),
        "canonical_reference": st.column_config.TextColumn("Canonical reference"),
        "seed": st.column_config.NumberColumn("Seed", format="%d"),
        "keff_mean": st.column_config.NumberColumn("k-effective mean", format="%.6f"),
        "keff_std_dev": st.column_config.NumberColumn("Reported std. dev.", format="%.6f"),
        "aggregate_flux_score": st.column_config.NumberColumn("Flux score", format="%.5f"),
        "aggregate_fission_score": st.column_config.NumberColumn("Fission score", format="%.5f"),
    },
)
st.download_button(
    "Export visible study data (CSV)",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="cbpfr_c5g7_layout_smoke_data.csv",
    mime="text/csv",
)

st.warning(
    "Scientific interpretation: these are low-budget exploratory smoke runs. "
    "Do not interpret the values as benchmark-grade physical validation or declare a winning layout. "
    "The legacy fresh / once-burned / twice-burned QUBO is a separate formulation and is not mapped to UO₂/MOX."
)
st.caption("Source: committed candidate_summary.csv · C5G7 layout smoke study · see repository reports for provenance and limitations.")
