from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="CB-PFR Research Workstation", page_icon="⚛", layout="wide")
ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "results" / "c5g7_layout_smoke_2026-10-10" / "candidate_summary.csv"
def load_smoke():
    if not SMOKE.exists():
        st.error(f"Evidence file unavailable: {SMOKE}")
        st.stop()
    return pd.read_csv(SMOKE)
st.markdown("""<style>
.stApp{background:#06101e;color:#dceaff}.block-container{max-width:1600px;padding-top:1.2rem}
section[data-testid="stSidebar"]{background:#07182b;border-right:1px solid #153a5e}
.panel{border:1px solid #153a5e;border-radius:10px;background:#07192b;padding:16px}
.muted{color:#91b0cf;font-size:13px}.eyebrow{color:#48c7ff;font-size:11px;font-weight:700;letter-spacing:.16em}
</style>""", unsafe_allow_html=True)
def header(title, subtitle, status="EVIDENCE-LINKED"):
    st.markdown(f'<div class="panel"><div class="eyebrow">CB-PFR · RESEARCH WORKSTATION</div><h1 style="margin:5px 0;color:#eff7ff">{title}</h1><div class="muted">{subtitle}</div><p style="margin-bottom:0"><code>{status}</code></p></div>', unsafe_allow_html=True)

header("Physics Field Explorer","OpenMC statepoint and tally evidence · field inventory · uncertainty-aware inspection","TALLY DATA REQUIRED FOR SPATIAL MAPS")
st.write("This workspace is designed to display neutron flux, fission, and power-related tallies only when the corresponding arrays and mesh metadata are available. It does not synthesize a spatial heatmap from aggregate scores.")
st.info("The repository documents an OpenMC statepoint/tally audit and mesh-index plots. The committed six-layout summary CSV contains aggregate scores, not the cell-by-cell arrays required to draw a physical field map.")
df=load_smoke()
a,b,c=st.columns(3)
a.metric("Layout records",len(df))
b.metric("Available aggregate fields",3)
c.metric("Cell-wise field arrays","Not in summary CSV")
st.markdown("### Available evidence in the current summary")
st.dataframe(df[["candidate_id","layout_signature","aggregate_flux_score","aggregate_fission_score","aggregate_nu_fission_score"]],use_container_width=True,hide_index=True)
st.markdown("### Field readiness")
st.table(pd.DataFrame([
{"Field":"Neutron flux","Data available here":"Aggregate score only","Spatial map":"Blocked — mesh tally array required"},
{"Field":"Fission rate","Data available here":"Aggregate score only","Spatial map":"Blocked — cell/mesh tally array required"},
{"Field":"Power distribution","Data available here":"Not established in this CSV","Spatial map":"Blocked — units and normalization required"},
{"Field":"Uncertainty","Data available here":"k-effective standard deviation per run","Spatial map":"Tally-specific uncertainty required"},
]))
st.warning("Aggregate flux/fission scores are not substitutes for spatial distributions. Before displaying a field map, load a verified statepoint, retain tally filters/mesh dimensions, show units and uncertainty, and identify the exact statepoint hash.")
