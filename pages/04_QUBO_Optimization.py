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

header("QUBO / Optimization","Inspect the separate four-variable material-count constraint and its exact feasible design space","EXACT COMBINATORICS · NOT PHYSICAL VALIDATION")
st.markdown("### Formulation")
st.latex(r"E(y)=A(\sum_{i=1}^{4}y_i-2)^2, \quad y_i\in\{0,1\}")
st.write("Here 1 = MOX and 0 = UO₂. The penalty enforces exactly two MOX and two UO₂ assemblies across four positions. This is a separate C5G7 design formulation; it is not a mapping of the legacy fresh / once-burned / twice-burned QUBO.")
A=st.slider("Constraint penalty A",min_value=0.5,max_value=10.0,value=1.0,step=0.5)
rows=[]
from itertools import product
for bits in product((0,1),repeat=4):
    energy=A*(sum(bits)-2)**2
    rows.append({"p00":"MOX" if bits[0] else "UO₂","p01":"MOX" if bits[1] else "UO₂","p10":"MOX" if bits[2] else "UO₂","p11":"MOX" if bits[3] else "UO₂","Binary vector":"".join(map(str,bits)),"MOX count":sum(bits),"Penalty energy":energy,"Feasible":sum(bits)==2})
all_df=pd.DataFrame(rows)
feasible=all_df[all_df["Feasible"]].copy()
a,b,c=st.columns(3)
a.metric("Binary vectors",len(all_df))
b.metric("Feasible layouts",len(feasible))
c.metric("Penalty energy · feasible",f'{feasible["Penalty energy"].max():.2f}')
st.markdown("### Exact enumeration")
st.dataframe(all_df,use_container_width=True,hide_index=True)
st.caption("The six feasible layouts are the combinations of choosing two MOX positions among four. QUBO feasibility does not determine which layout performs best in OpenMC.")
st.download_button("Export enumeration CSV",all_df.to_csv(index=False).encode(),"cbpfr_qubo_exact_enumeration.csv","text/csv")
