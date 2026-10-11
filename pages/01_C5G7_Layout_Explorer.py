"""Evidence-aware C5G7 layout comparison with native Streamlit controls and Plotly figures."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "results" / "c5g7_layout_smoke_2026-10-10" / "candidate_summary.csv"

st.set_page_config(page_title="CB-PFR | C5G7 Layout", page_icon="⚛️", layout="wide")

st.markdown("""
<style>
.block-container {max-width: 1600px; padding-top: 1.1rem; padding-bottom: 2.4rem;}
[data-testid="stMetric"] {background: linear-gradient(145deg,rgba(18,36,54,.9),rgba(10,20,32,.9)); border:1px solid #294056; padding:15px 17px; border-radius:10px;}
[data-testid="stMetricLabel"] p {font-size:.75rem; letter-spacing:.07em; text-transform:uppercase;}
.report-kicker {font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:#59d8df;font-weight:700;margin-bottom:.25rem}
.report-title {font-size:2.15rem;font-weight:750;letter-spacing:-.04em;margin:.1rem 0 .25rem}
.report-sub {color:#9eb0c3;max-width:900px;font-size:.95rem}
.evidence-note {border:1px solid #65543a;background:rgba(107,77,32,.15);border-radius:8px;padding:13px 16px;margin:.8rem 0 1.2rem}
.small-muted {color:#91a4b7;font-size:.82rem}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ⚛️ CB·PFR")
    st.caption("COMPUTATIONAL REACTOR LAB")
    st.divider()
    st.page_link("pages/01_C5G7_Layout_Explorer.py", label="01 · C5G7 Layout", icon="🧩")
    st.page_link("pages/02_Physics_Field_Explorer.py", label="02 · Physics Field", icon="🌐")
    st.page_link("pages/03_Monte_Carlo_Reliability.py", label="03 · Monte Carlo", icon="🎲")
    st.page_link("pages/04_QUBO_Optimization.py", label="04 · QUBO Lab", icon="⚙️")
    st.page_link("pages/05_Provenance_Validation.py", label="05 · Provenance", icon="🔎")
    st.divider()
    st.caption("DATA MODE: REPOSITORY CSV")
    st.caption("MODEL STATUS: SCHEMATIC / PARTIAL EVIDENCE")

st.markdown('<div class="report-kicker">RESEARCH MODULE / 01 · CORE CONFIGURATION STUDY</div>', unsafe_allow_html=True)
st.markdown('<div class="report-title">C5G7 Core <span style="color:#7ba8ff">Layout Explorer</span></div>', unsafe_allow_html=True)
st.markdown('<div class="report-sub">Interactive inspection of recorded 2 × 2 material-assignment candidates and their transport-summary statistics.</div>', unsafe_allow_html=True)

st.markdown("""
<div class="evidence-note">
<b>Evidence boundary</b><br>
This page visualizes the repository's recorded candidate-summary CSV. The 2 × 2 map is a categorical schematic, not a pin-resolved C5G7 geometry or spatial flux solution. Reported aggregate scores are not spatially resolved physical fields.
</div>
""", unsafe_allow_html=True)

if not CSV.is_file():
    st.error(f"Required evidence CSV was not found at: {CSV.relative_to(ROOT)}")
    st.stop()

try:
    raw = pd.read_csv(CSV)
except Exception as exc:
    st.error(f"Could not read the candidate-summary CSV: {exc}")
    st.stop()

required = [
    "candidate_id", "layout_signature", "canonical_reference", "seed",
    "batches", "inactive", "particles_per_batch", "keff_mean",
    "keff_std_dev", "keff_relative_sd_percent", "aggregate_flux_score",
    "aggregate_fission_score", "mgxs_sha256_before_transport",
    "mgxs_sha256_after_transport",
]
missing = [column for column in required if column not in raw.columns]
if missing:
    st.error("Candidate CSV is missing required columns: " + ", ".join(missing))
    st.stop()

df = raw.copy()
df["layout_signature"] = df["layout_signature"].astype(str).str.strip().str.upper()
df = df[df["layout_signature"].map(lambda value: len(value) == 4 and set(value) <= {"U", "M"})].copy()
for col in ["seed", "batches", "inactive", "particles_per_batch", "keff_mean", "keff_std_dev", "keff_relative_sd_percent", "aggregate_flux_score", "aggregate_fission_score"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df = df.dropna(subset=["keff_mean", "keff_std_dev", "aggregate_flux_score", "aggregate_fission_score"])
if df.empty:
    st.error("No valid four-position candidate records remain after validation.")
    st.stop()

df["canonical_reference"] = df["canonical_reference"].astype(str).str.strip().str.lower().isin(["true", "1", "yes"])
df["candidate_label"] = df["candidate_id"].astype(str) + " · " + df["layout_signature"]
csv_hash = hashlib.sha256(CSV.read_bytes()).hexdigest()
candidate_labels = df["candidate_label"].tolist()
selected_label = st.selectbox("Inspect candidate", candidate_labels, index=next((i for i, x in enumerate(candidate_labels) if bool(df.iloc[i]["canonical_reference"])), 0))
selected = df.loc[df["candidate_label"] == selected_label].iloc[0]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Recorded candidates", f"{len(df):02d}", help="Valid four-position records in the CSV.")
m2.metric("Selected k-effective mean", f"{selected['keff_mean']:.6f}", help="Recorded value; interpretation depends on source run methodology.")
m3.metric("Reported standard deviation", f"{selected['keff_std_dev']:.6f}")
m4.metric("Relative SD", f"{selected['keff_relative_sd_percent']:.4f}%")

st.divider()
left, right = st.columns([1.12, 1], gap="large")
with left:
    st.markdown("### 01 / Material-assignment schematic")
    st.caption("Position order follows the stored four-character signature: P00, P10, P01, P11. U = UO₂; M = MOX.")
    sig = selected["layout_signature"]
    positions = [("P00", sig[0]), ("P10", sig[1]), ("P01", sig[2]), ("P11", sig[3])]
    z = [[1 if sig[0] == "U" else 0, 1 if sig[1] == "U" else 0],
         [1 if sig[2] == "U" else 0, 1 if sig[3] == "U" else 0]]
    labels = [[f"P00<br>{'UO₂' if sig[0] == 'U' else 'MOX'}", f"P10<br>{'UO₂' if sig[1] == 'U' else 'MOX'}"],
              [f"P01<br>{'UO₂' if sig[2] == 'U' else 'MOX'}", f"P11<br>{'UO₂' if sig[3] == 'U' else 'MOX'}"]]
    fig_geo = go.Figure(go.Heatmap(
        z=z, x=["Column 0", "Column 1"], y=["Row 0", "Row 1"],
        text=labels, texttemplate="%{text}", textfont={"size": 18},
        customdata=[[positions[0][1], positions[1][1]], [positions[2][1], positions[3][1]]],
        hovertemplate="%{y}, %{x}<br>Material: %{customdata}<extra></extra>",
        colorscale=[[0, "#6a4b26"], [0.49, "#6a4b26"], [0.5, "#234e82"], [1, "#234e82"]],
        showscale=False, xgap=8, ygap=8,
    ))
    fig_geo.update_layout(template="plotly_dark", height=380, margin=dict(l=20,r=20,t=25,b=20),
                         paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         xaxis=dict(side="top", tickfont=dict(size=11), fixedrange=True),
                         yaxis=dict(autorange="reversed", tickfont=dict(size=11), fixedrange=True),
                         annotations=[dict(x=0.5,y=-0.14,xref="paper",yref="paper",text="SCHEMATIC ONLY · NOT TO SCALE",showarrow=False,font=dict(size=10,color="#91a4b7"))])
    st.plotly_chart(fig_geo, use_container_width=True, key="c5g7_layout_schematic")
    st.caption("Blue = UO₂; amber = MOX. This visualization does not infer pin locations, dimensions, or neutron-flux distribution.")

with right:
    st.markdown("### 02 / Candidate record")
    st.markdown(f"**{selected['candidate_id']}**")
    st.code(f"layout_signature = {sig}", language="text")
    details = pd.DataFrame([
        ("Canonical reference", "Yes" if selected["canonical_reference"] else "No"),
        ("Random seed", f"{int(selected['seed'])}"),
        ("Batches / inactive", f"{int(selected['batches'])} / {int(selected['inactive'])}"),
        ("Particles per batch", f"{int(selected['particles_per_batch']):,}"),
        ("MOX positions", f"{sig.count('M')} / 4"),
        ("UO₂ positions", f"{sig.count('U')} / 4"),
        ("MGXS hash before", str(selected["mgxs_sha256_before_transport"])[:20] + "…"),
        ("MGXS hash after", str(selected["mgxs_sha256_after_transport"])[:20] + "…"),
    ], columns=["Field", "Recorded value"])
    st.dataframe(details, hide_index=True, use_container_width=True)
    same_hash = str(selected["mgxs_sha256_before_transport"]) == str(selected["mgxs_sha256_after_transport"])
    st.success("MGXS input hash unchanged for this run.") if same_hash else st.warning("MGXS input hash differs before and after transport.")
    st.caption("Hash equality supports input-file integrity only; it does not establish solver correctness or physical validation.")

st.divider()
st.markdown("### 03 / Recorded transport-summary comparison")
st.caption("Each point is a recorded candidate mean. Error bars show the CSV's reported standard deviation (σ), not a confidence interval.")
plot_df = df.sort_values("keff_mean").reset_index(drop=True)
fig_compare = go.Figure()
for is_reference, group in plot_df.groupby("canonical_reference", sort=False):
    fig_compare.add_trace(go.Scatter(
        x=group["candidate_id"], y=group["keff_mean"], mode="markers+lines",
        name="Canonical reference" if is_reference else "Other candidate",
        marker=dict(size=11, symbol="diamond" if is_reference else "circle"),
        line=dict(width=1, dash="dot"),
        error_y=dict(type="data", array=group["keff_std_dev"], visible=True, thickness=1.4, width=4),
        customdata=group[["layout_signature", "seed", "keff_relative_sd_percent"]].to_numpy(),
        hovertemplate="<b>%{x}</b><br>Layout: %{customdata[0]}<br>k-effective mean: %{y:.7f}<br>Seed: %{customdata[1]}<br>Relative SD: %{customdata[2]:.4f}%<extra></extra>",
    ))
fig_compare.update_layout(template="plotly_dark", height=430, hovermode="closest",
    margin=dict(l=60,r=25,t=20,b=100), paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)", xaxis_title="Candidate ID",
    yaxis_title="Recorded k-effective mean", legend=dict(orientation="h",y=1.12),
    xaxis=dict(tickangle=-25, gridcolor="#25374a"),
    yaxis=dict(gridcolor="#25374a", zeroline=False))
st.plotly_chart(fig_compare, use_container_width=True, key="c5g7_keff_comparison")

a, b = st.columns(2, gap="large")
with a:
    st.markdown("### 04 / Relative statistical spread")
    rel = plot_df.sort_values("keff_relative_sd_percent")
    fig_sd = go.Figure(go.Bar(
        x=rel["keff_relative_sd_percent"], y=rel["candidate_id"], orientation="h",
        marker_color=["#58d7df" if x else "#7ba8ff" for x in rel["canonical_reference"]],
        customdata=rel[["layout_signature", "keff_std_dev"]].to_numpy(),
        hovertemplate="%{y}<br>Layout %{customdata[0]}<br>Relative SD %{x:.4f}%<br>Reported σ %{customdata[1]:.6f}<extra></extra>",
    ))
    fig_sd.update_layout(template="plotly_dark", height=320, margin=dict(l=15,r=20,t=10,b=45),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Relative SD (%)", yaxis_title="", xaxis=dict(gridcolor="#25374a"))
    st.plotly_chart(fig_sd, use_container_width=True, key="c5g7_relative_sd")
with b:
    st.markdown("### 05 / Evidence table")
    show_cols = ["candidate_id", "layout_signature", "canonical_reference", "seed", "keff_mean", "keff_std_dev", "keff_relative_sd_percent", "aggregate_flux_score", "aggregate_fission_score"]
    view = df[show_cols].rename(columns={
        "candidate_id":"Candidate", "layout_signature":"Layout", "canonical_reference":"Reference",
        "seed":"Seed", "keff_mean":"k-eff mean", "keff_std_dev":"Reported σ",
        "keff_relative_sd_percent":"Relative SD (%)", "aggregate_flux_score":"Flux score",
        "aggregate_fission_score":"Fission score",
    })
    st.dataframe(view, hide_index=True, use_container_width=True, height=320)

with st.expander("Methodology, provenance and interpretation"):
    st.markdown(f"""
**Data source:** `{CSV.relative_to(ROOT)}`  
**CSV SHA-256:** `{csv_hash}`  
**Records displayed:** {len(df)} valid four-position candidates.

- Layout signatures are categorical labels; this page maps the four stored characters to four schematic cells.
- k-effective values, standard deviations, relative SD, and aggregate scores are read from the recorded CSV; the UI does not rerun OpenMC.
- Aggregate flux and fission scores are not spatial fields and are not interpreted as absolute physical units here.
- The reported standard deviation is plotted as supplied; it is not relabelled as a confidence interval.
- The shared MGXS hash can indicate that the input file did not change during the recorded runs, but cannot prove model validation.
- Candidate differences should not be treated as a validated physical ranking without documented model setup, convergence checks, uncertainty treatment, and independent validation.
""")
st.caption("CB-PFR · Scientific workstation · CSV-backed exploratory evidence · Not a validated reactor design or safety analysis.")
