"""Shared visual system and evidence helpers for the CB-PFR Streamlit workstation."""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
SMOKE_CSV = ROOT / "results" / "c5g7_layout_smoke_2026-10-10" / "candidate_summary.csv"

BG = "#030911"
PANEL = "#061321"
PANEL_ALT = "#091b2e"
LINE = "#143b59"
TEXT = "#e0edfa"
MUTED = "#87abc9"
CYAN = "#26bafa"
BLUE = "#1261b8"
ORANGE = "#ff8f38"
GREEN = "#38d49e"
RED = "#ff7777"


def apply_workstation_style():
    st.markdown(
        f"""
        <style>
        :root {{ color-scheme: dark; }}
        .stApp {{ background: {BG}; color: {TEXT}; }}
        .block-container {{ max-width: 1600px; padding-top: 1.1rem; padding-bottom: 2rem; }}
        section[data-testid="stSidebar"] {{ background: {PANEL}; border-right: 1px solid {LINE}; }}
        section[data-testid="stSidebar"] * {{ color: {TEXT}; }}
        h1, h2, h3 {{ color: {TEXT}; letter-spacing: -.02em; }}
        h1 {{ font-size: 1.8rem; }}
        h2 {{ font-size: 1.18rem; }}
        h3 {{ font-size: 1rem; }}
        p, li, label {{ color: {TEXT}; }}
        div[data-testid="stMetric"] {{ background: {PANEL}; border: 1px solid {LINE}; padding: 13px 15px; border-radius: 4px; }}
        div[data-testid="stMetricLabel"] {{ color: {MUTED}; font-size: .78rem; }}
        div[data-testid="stMetricValue"] {{ color: {TEXT}; }}
        div[data-testid="stAlert"] {{ border-radius: 4px; }}
        div[data-testid="stDataFrame"], div[data-testid="stTable"] {{ border: 1px solid {LINE}; border-radius: 4px; }}
        div[data-testid="stPageLink"] a {{ border: 1px solid {LINE}; background: {PANEL}; border-radius: 3px; padding: 8px 10px; }}
        div[data-testid="stPageLink"] a:hover {{ border-color: {CYAN}; color: {CYAN}; }}
        button[kind="primary"] {{ background: {BLUE}; border: 1px solid {CYAN}; }}
        .cbpfr-brand {{ border-bottom: 1px solid {LINE}; padding: 0 0 13px 0; margin-bottom: 10px; }}
        .cbpfr-brand .brand {{ color: {TEXT}; font-size: 1.35rem; font-weight: 700; letter-spacing: .04em; }}
        .cbpfr-brand .descriptor {{ color: {MUTED}; font-size: .68rem; letter-spacing: .13em; margin-top: 3px; }}
        .cbpfr-brand .status {{ color: {ORANGE}; font-size: .68rem; letter-spacing: .08em; text-align: right; }}
        .section-kicker {{ color: {CYAN}; font-size: .7rem; font-weight: 700; letter-spacing: .13em; text-transform: uppercase; }}
        .panel-title {{ color: {TEXT}; font-size: 1rem; font-weight: 650; margin: 0 0 3px 0; }}
        .panel-subtitle {{ color: {MUTED}; font-size: .76rem; margin-bottom: 10px; }}
        .evidence-note {{ border-left: 3px solid {ORANGE}; background: {PANEL}; padding: 10px 13px; color: {MUTED}; font-size: .83rem; }}
        .small-muted {{ color: {MUTED}; font-size: .78rem; }}
        .workspace-kicker {{ color: {MUTED}; font-size: .67rem; letter-spacing: .12em; text-transform: uppercase; }}
        .workspace-value {{ color: {TEXT}; font-size: .82rem; font-weight: 600; }}
        .workspace-note {{ color: {MUTED}; font-size: .72rem; line-height: 1.45; }}
        .metric-caption {{ color: {MUTED}; font-size: .72rem; margin-top: -7px; }}
        .status-line {{ display: flex; gap: 8px; align-items: center; font-size: .78rem; color: {TEXT}; padding: 7px 0; border-bottom: 1px solid {LINE}; }}
        .status-dot {{ width: 7px; height: 7px; display: inline-block; border-radius: 50%; background: {ORANGE}; flex-shrink: 0; }}
        .scientific-panel {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 4px; padding: 13px 15px; }}
        .scientific-panel-title {{ font-size: .87rem; color: {TEXT}; font-weight: 650; }}
        hr {{ border-color: {LINE}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(active: str, status: str = "RESEARCH PROTOTYPE"):
    st.markdown(
        f"""
        <div class="cbpfr-brand">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:18px;flex-wrap:wrap">
            <div><div class="brand">CB-PFR</div>
              <div class="descriptor">CONFIDENCE-BOUNDED PHYSICAL FEASIBILITY RANKING</div></div>
            <div class="status">{status}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    nav = st.columns([1.15, 1.15, 1.35, 1.3, 1.1, 1.0])
    items = [
        ("Overview", "app.py"),
        ("Geometry", "pages/01_C5G7_Layout_Explorer.py"),
        ("Physics fields", "pages/02_Physics_Field_Explorer.py"),
        ("Monte Carlo", "pages/03_Monte_Carlo_Reliability.py"),
        ("QUBO", "pages/04_QUBO_Optimization.py"),
        ("Provenance", "pages/05_Provenance_Validation.py"),
    ]
    for col, (label, path) in zip(nav, items):
        with col:
            if label == active:
                st.markdown(f'<div style="border:1px solid {CYAN};background:#0b2b46;border-radius:3px;padding:8px 10px;color:{TEXT};font-size:.82rem;font-weight:650">{label}</div>', unsafe_allow_html=True)
            else:
                st.page_link(path, label=label)



def render_workspace_sidebar(active: str, df: pd.DataFrame):
    """Shared project/evidence sidebar matching the Geometry Explorer workstation."""
    with st.sidebar:
        st.markdown(
            '<div class="cbpfr-brand"><div class="brand">CB-PFR</div>'
            '<div class="descriptor">RESEARCH WORKSPACE</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="workspace-kicker">Workspace & evidence</div>', unsafe_allow_html=True)
        st.caption("C5G7 · 2×2 assembly study")
        st.markdown("---")
        st.markdown('<div class="workspace-kicker">Project modules</div>', unsafe_allow_html=True)
        modules = [
            ("Overview", "app.py"),
            ("C5G7 Layout Explorer", "pages/01_C5G7_Layout_Explorer.py"),
            ("Physics Fields", "pages/02_Physics_Field_Explorer.py"),
            ("Monte Carlo Results", "pages/03_Monte_Carlo_Reliability.py"),
            ("QUBO / Optimization", "pages/04_QUBO_Optimization.py"),
            ("Provenance & Validation", "pages/05_Provenance_Validation.py"),
        ]
        for label, path in modules:
            if label == active:
                st.markdown(
                    f'<div style="border:1px solid {CYAN};background:#0b2b46;border-radius:3px;'
                    f'padding:8px 10px;margin:5px 0;color:{TEXT};font-size:.79rem;font-weight:650">'
                    f'● &nbsp;{label}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.page_link(path, label=label)
        st.markdown("---")
        st.markdown('<div class="workspace-kicker">System status</div>', unsafe_allow_html=True)
        st.markdown('<div class="status-line"><span class="status-dot"></span> OpenMC results <b style="margin-left:auto">SMOKE</b></div>', unsafe_allow_html=True)
        st.markdown('<div class="status-line"><span class="status-dot"></span> Spatial tallies <b style="margin-left:auto">PENDING</b></div>', unsafe_allow_html=True)
        hash_ok = bool((df["mgxs_sha256_before_transport"].astype(str) == df["mgxs_sha256_after_transport"].astype(str)).all())
        dot = GREEN if hash_ok else RED
        label = "MATCHED" if hash_ok else "REVIEW"
        st.markdown(f'<div class="status-line"><span class="status-dot" style="background:{dot}"></span> MGXS hash <b style="margin-left:auto">{label}</b></div>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown('<div class="workspace-kicker">Evidence boundary</div>', unsafe_allow_html=True)
        st.markdown('<div class="workspace-note">Current data supports aggregate comparisons only. Spatial fields and physical validation remain unavailable until source evidence is supplied.</div>', unsafe_allow_html=True)

def load_smoke() -> pd.DataFrame:
    if not SMOKE_CSV.exists():
        st.error(f"Evidence CSV is missing: {SMOKE_CSV}")
        st.stop()
    df = pd.read_csv(SMOKE_CSV)
    required = {
        "candidate_id", "layout_signature", "canonical_reference", "seed", "batches",
        "inactive", "particles_per_batch", "keff_mean", "keff_std_dev",
        "aggregate_flux_score", "aggregate_fission_score", "mgxs_sha256_before_transport",
        "mgxs_sha256_after_transport",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        st.error("Evidence CSV is missing required columns: " + ", ".join(missing))
        st.stop()
    df = df.copy()
    df["canonical_reference"] = df["canonical_reference"].astype(str).str.lower().isin(["true", "1", "yes"])
    return df


def base_layout(fig: go.Figure, height: int = 340, **kwargs) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor=BG,
        plot_bgcolor=PANEL,
        font={"family": "Inter, ui-sans-serif, sans-serif", "color": TEXT, "size": 11},
        margin={"l": 56, "r": 22, "t": 26, "b": 55},
        xaxis={"gridcolor": "#183752", "linecolor": LINE, "zerolinecolor": LINE},
        yaxis={"gridcolor": "#183752", "linecolor": LINE, "zerolinecolor": LINE},
        legend={"bgcolor": "rgba(0,0,0,0)", "font": {"color": TEXT}},
        hoverlabel={"bgcolor": PANEL_ALT, "bordercolor": CYAN, "font": {"color": TEXT}},
        **kwargs,
    )
    return fig


def layout_figure(signature: str, height: int = 330) -> go.Figure:
    """Categorical 2x2 assembly-placement schematic; not pin-resolved geometry."""
    if len(signature) != 4 or any(ch not in "UM" for ch in signature):
        signature = "UMMU"
    # CSV signature order is P00, P10, P01, P11.
    chars = [signature[0], signature[1], signature[2], signature[3]]
    z = [[0 if chars[0] == "U" else 1, 0 if chars[1] == "U" else 1],
         [0 if chars[2] == "U" else 1, 0 if chars[3] == "U" else 1]]
    labels = [["UO₂" if c == "U" else "MOX" for c in row] for row in [chars[:2], chars[2:]]]
    positions = [["P00", "P10"], ["P01", "P11"]]
    custom = [[positions[r][c] for c in range(2)] for r in range(2)]
    fig = go.Figure(go.Heatmap(
        z=z, x=["Column 0", "Column 1"], y=["Row 0", "Row 1"],
        zmin=0, zmax=1,
        colorscale=[[0, BLUE], [0.499, BLUE], [0.5, ORANGE], [1, ORANGE]],
        showscale=False, text=labels, texttemplate="%{text}",
        customdata=custom,
        hovertemplate="Position %{customdata}<br>Material: %{text}<extra></extra>",
        xgap=7, ygap=7,
    ))
    fig.update_layout(
        height=height, paper_bgcolor=BG, plot_bgcolor=PANEL,
        font={"family": "Inter, ui-sans-serif, sans-serif", "color": TEXT, "size": 11},
        margin={"l": 52, "r": 18, "t": 20, "b": 45},
        xaxis={"side": "top", "fixedrange": True},
        yaxis={"autorange": "reversed", "fixedrange": True},
    )
    fig.update_traces(textfont={"size": 18, "color": "#ffffff"})
    return fig


def candidate_label(row) -> str:
    return str(row["candidate_id"]).replace("c5g7-2x2-", "")
