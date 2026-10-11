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

header("Provenance & Validation","Trace input identity, simulation records, uncertainty provenance, and claim boundaries","FAIL-CLOSED SCIENTIFIC AUDIT")
st.markdown("### Evidence status")
st.table(pd.DataFrame([
{"Gate":"CB-PFR ranking implementation + CI","Status":"Implemented / automated tests","Interpretation":"Software verification only"},
{"Gate":"Synthetic benchmark","Status":"Reproducible; explicitly synthetic","Interpretation":"Supports conclusions only under declared synthetic process"},
{"Gate":"Archived OpenMC statepoints","Status":"Read and audited","Interpretation":"Extraction/consistency checks, not benchmark acceptance"},
{"Gate":"Corrected-group 18-run smoke study","Status":"Exploratory runs recorded","Interpretation":"Not benchmark-grade ranking"},
{"Gate":"Legacy burnup QUBO → UO₂/MOX mapping","Status":"NO_DEFENSIBLE_MAPPING_FOUND","Interpretation":"Must remain separate formulations"},
{"Gate":"CB-PFR physical validation","Status":"Not established","Interpretation":"Do not claim validated reactor design or safety"}
]))
st.markdown("### Candidate-level run records")
df=load_smoke()
st.dataframe(df[["candidate_id","layout_signature","canonical_reference","seed","batches","inactive","particles_per_batch","mgxs_sha256_before_transport","mgxs_sha256_after_transport"]],use_container_width=True,hide_index=True)
st.markdown("### Required before physical ranking")
st.write("1. Review the primary C5G7 specification and material/geometry correspondence.")
st.write("2. Use the standard seven-group boundaries and audit the generated MGXS identity.")
st.write("3. Run each candidate at a common higher-fidelity budget with independent seeds.")
st.write("4. Pair each seed with its exact settings, log, statepoint, and input hashes.")
st.write("5. Predeclare the k-effective acceptance band, objective, uncertainty treatment, and decision rule.")
st.write("6. Keep the legacy burnup-state QUBO separate unless a source-backed physical mapping is established.")
st.markdown("### Repository reports")
st.markdown("- [Remaining-work audit](https://github.com/thenextw4ng/cb-pfr/blob/main/reports/REMAINING_WORK_AUDIT_2026-10-11.md)")
st.markdown("- [C5G7 validation and mapping plan](https://github.com/thenextw4ng/cb-pfr/blob/main/reports/C5G7_VALIDATION_AND_MAPPING_PLAN.md)")
st.markdown("- [Corrected-group repeatability smoke report](https://github.com/thenextw4ng/cb-pfr/blob/main/reports/c5g7_corrected_group_repeatability_smoke_2026-10-11.md)")
st.download_button("Export candidate provenance CSV",df.to_csv(index=False).encode(),"cbpfr_candidate_provenance.csv","text/csv")
