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

header("Monte Carlo & Reliability","Compare exploratory C5G7 layouts with recorded run settings and variability","EXPLORATORY SMOKE DATA")
df=load_smoke()
st.warning("These are low-budget smoke runs, not benchmark-grade layout rankings. The historical single-run-per-layout table is not a reliability study.")
st.markdown("### Run configuration")
a,b,c,d=st.columns(4)
a.metric("Layouts",len(df))
b.metric("Batches / run",int(df["batches"].iloc[0]))
c.metric("Inactive batches",int(df["inactive"].iloc[0]))
d.metric("Particles / batch",f'{int(df["particles_per_batch"].iloc[0]):,}')
st.markdown("### k-effective across layout smoke runs")
chart=df[["layout_signature","keff_mean","keff_std_dev"]].copy().sort_values("layout_signature").set_index("layout_signature")
st.bar_chart(chart[["keff_mean"]])
st.caption("Bars show reported run means. The separate standard-deviation column is reported below; these are not confidence intervals across independent repeats.")
st.dataframe(df[["candidate_id","layout_signature","seed","keff_mean","keff_std_dev","keff_relative_sd_percent","aggregate_fission_score"]],use_container_width=True,hide_index=True)
st.markdown("### Repeatability requirements")
st.write("A reliability comparison needs repeated independent seeds for each candidate at a common computational budget, paired statepoints/logs/settings, audited group structure and MGXS identity, and a predeclared objective/acceptance rule.")
st.markdown("### Export")
st.download_button("Download run summary CSV",df.to_csv(index=False).encode(), "cbpfr_monte_carlo_smoke_summary.csv","text/csv")
