"""Shared visual system and evidence helpers for the CB-PFR Streamlit workstation."""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
SMOKE_CSV = ROOT / "results" / "c5g7_layout_smoke_2026-10-10" / "candidate_summary.csv"

BG = "#07111b"
PANEL = "#0c1b29"
PANEL_ALT = "#102536"
LINE = "#263f52"
TEXT = "#e8f1f7"
MUTED = "#9aafbf"
CYAN = "#55d4df"
BLUE = "#247fa0"
ORANGE = "#f5bb62"
GREEN = "#4bd5a5"
RED = "#ff7f86"


def apply_workstation_style():
    st.markdown(
        f"""
        <style>
        :root {{ color-scheme: dark; }}
        .stApp {{ background: radial-gradient(ellipse at 52% -15%, #132a38 0%, {BG} 58%); color: {TEXT}; }}
        .block-container {{ max-width: 1640px; padding: 1.15rem 2rem 3rem; }}
        section[data-testid="stSidebar"] {{ background: #0a1925; border-right: 1px solid {LINE}; }}
        section[data-testid="stSidebar"] * {{ color: {TEXT}; }}
        h1, h2, h3 {{ color: {TEXT}; letter-spacing: -.025em; }}
        h1 {{ font-size: clamp(1.65rem, 2.4vw, 2.15rem); font-weight: 700; }}
        h2 {{ font-size: 1.18rem; font-weight: 650; }}
        h3 {{ font-size: 1rem; font-weight: 650; }}
        p, li, label {{ color: {TEXT}; }}
        [data-testid="stCaptionContainer"] p {{ color: {MUTED}; }}
        div[data-testid="stMetric"] {{ background: linear-gradient(145deg, {PANEL_ALT}, {PANEL}); border: 1px solid {LINE}; padding: 15px 17px; border-radius: 8px; min-height: 105px; }}
        div[data-testid="stMetricLabel"] {{ color: {MUTED}; font-size: .76rem; letter-spacing: .025em; }}
        div[data-testid="stMetricValue"] {{ color: {TEXT}; font-weight: 680; }}
        div[data-testid="stMetricDelta"] {{ font-size: .74rem; }}
        div[data-testid="stAlert"] {{ border-radius: 7px; border: 1px solid {LINE}; }}
        div[data-testid="stDataFrame"], div[data-testid="stTable"] {{ border: 1px solid {LINE}; border-radius: 7px; overflow: hidden; }}
        div[data-testid="stPageLink"] a {{ border: 1px solid {LINE}; background: {PANEL}; border-radius: 6px; padding: 9px 11px; transition: border-color .15s ease, background .15s ease; }}
        div[data-testid="stPageLink"] a:hover {{ border-color: {CYAN}; background: #123242; color: {CYAN}; }}
        button[kind="primary"] {{ background: {BLUE}; border: 1px solid {CYAN}; border-radius: 6px; }}
        button {{ border-radius: 6px !important; }}
        .cbpfr-brand {{ border-bottom: 1px solid {LINE}; padding: 0 0 15px; margin-bottom: 12px; }}
        .cbpfr-brand .brand {{ color: {TEXT}; font-size: 1.45rem; font-weight: 760; letter-spacing: .06em; }}
        .cbpfr-brand .descriptor {{ color: {MUTED}; font-size: .64rem; letter-spacing: .12em; margin-top: 4px; }}
        .cbpfr-brand .status {{ color: {ORANGE}; font-size: .66rem; letter-spacing: .09em; text-align: right; border: 1px solid #754b2e; background: #2a1b12; padding: 6px 9px; border-radius: 4px; }}
        .section-kicker {{ color: {CYAN}; font-size: .68rem; font-weight: 750; letter-spacing: .15em; text-transform: uppercase; margin: 4px 0 8px; }}
        .page-intro {{ padding: 6px 0 17px; }}
        .page-intro-subtitle {{ color: {MUTED}; font-size: .91rem; line-height: 1.55; max-width: 980px; }}
        .panel-title {{ color: {TEXT}; font-size: .96rem; font-weight: 680; margin: 0 0 4px; }}
        .panel-subtitle {{ color: {MUTED}; font-size: .75rem; line-height: 1.45; margin-bottom: 12px; }}
        .evidence-note {{ border: 1px solid #76532f; border-left: 3px solid {ORANGE}; background: linear-gradient(100deg, #201f1a, {PANEL}); padding: 12px 15px; color: #c4d2dc; font-size: .82rem; line-height: 1.55; border-radius: 5px; }}
        .small-muted {{ color: {MUTED}; font-size: .78rem; }}
        .workspace-kicker {{ color: {MUTED}; font-size: .65rem; letter-spacing: .13em; text-transform: uppercase; font-weight: 700; }}
        .workspace-value {{ color: {TEXT}; font-size: .82rem; font-weight: 600; }}
        .workspace-note {{ color: {MUTED}; font-size: .72rem; line-height: 1.5; }}
        .metric-caption {{ color: {MUTED}; font-size: .72rem; margin-top: -7px; }}
        .status-line {{ display: flex; gap: 8px; align-items: center; font-size: .76rem; color: {TEXT}; padding: 8px 0; border-bottom: 1px solid {LINE}; }}
        .status-dot {{ width: 7px; height: 7px; display: inline-block; border-radius: 50%; background: {ORANGE}; flex-shrink: 0; }}
        .scientific-panel {{ background: linear-gradient(145deg, {PANEL_ALT}, {PANEL}); border: 1px solid {LINE}; border-radius: 8px; padding: 15px 17px; }}
        .scientific-panel-title {{ font-size: .86rem; color: {TEXT}; font-weight: 680; }}
        div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {{ background: {PANEL}; border-color: {LINE}; }}
        div[role="radiogroup"] {{ gap: 8px; }}
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
    nav = st.columns([1.05, 1.1, 1.3, 1.2, .85, 1.0])
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
                st.markdown(
                    f'<div style="border:1px solid {CYAN};background:#123242;border-radius:6px;'
                    f'padding:9px 11px;color:{TEXT};font-size:.8rem;font-weight:700;text-align:center">'
                    f'{label}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.page_link(path, label=label)


def render_page_intro(kicker: str, title: str, subtitle: str):
    st.markdown(f'<div class="section-kicker">{kicker}</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-intro">', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="page-intro-subtitle">{subtitle}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


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
                    f'<div style="border:1px solid {CYAN};background:#123242;border-radius:6px;'
                    f'padding:9px 10px;margin:5px 0;color:{TEXT};font-size:.77rem;font-weight:700">'
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
        margin={"l": 56, "r": 22, "t": 28, "b": 55},
        xaxis={"gridcolor": LINE, "linecolor": LINE, "zerolinecolor": LINE, "ticks": "outside", "tickcolor": LINE},
        yaxis={"gridcolor": LINE, "linecolor": LINE, "zerolinecolor": LINE, "ticks": "outside", "tickcolor": LINE},
        legend={"bgcolor": "rgba(0,0,0,0)", "font": {"color": TEXT}},
        hoverlabel={"bgcolor": PANEL_ALT, "bordercolor": CYAN, "font": {"color": TEXT}},
        **kwargs,
    )
    return fig


def layout_figure(signature: str, height: int = 330) -> go.Figure:
    """Categorical 2x2 assembly-placement schematic; not pin-resolved geometry."""
    if len(signature) != 4 or any(ch not in "UM" for ch in signature):
        signature = "UMMU"
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
        xgap=8, ygap=8,
    ))
    fig.update_layout(
        height=height, paper_bgcolor=BG, plot_bgcolor=PANEL,
        font={"family": "Inter, ui-sans-serif, sans-serif", "color": TEXT, "size": 11},
        margin={"l": 52, "r": 18, "t": 24, "b": 45},
        xaxis={"side": "top", "fixedrange": True},
        yaxis={"autorange": "reversed", "fixedrange": True},
    )
    fig.update_traces(textfont={"size": 18, "color": "#ffffff"})
    return fig


def candidate_label(row) -> str:
    return str(row["candidate_id"]).replace("c5g7-2x2-", "")
