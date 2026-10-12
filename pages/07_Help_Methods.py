"""Help, methods, reproducibility protocol, and scientific claim boundaries."""
import streamlit as st

from cbpfr.dashboard_ui import (
    apply_workstation_style, render_header, render_page_intro, render_workspace_sidebar, load_smoke,
)

st.set_page_config(page_title="CB-PFR · Help & Methods", page_icon="⚛", layout="wide")
apply_workstation_style()
render_header("Help & Methods", "METHODS · REPRODUCIBILITY · CLAIM BOUNDARIES")
df = load_smoke()
render_workspace_sidebar("Help & Methods", df)
render_page_intro(
    "DOCUMENTATION / OPERATOR GUIDE",
    "Help & Methods",
    "A concise guide to the CB-PFR workflow, evidence provenance, visualization semantics, and the checks required before making a physical claim.",
)

st.markdown("### Research workflow")
st.code(
    "Recorded candidate inputs\n"
    "        ↓\n"
    "QUBO formulation / feasible-state enumeration\n"
    "        ↓\n"
    "Candidate configurations (mapping must be documented)\n"
    "        ↓\n"
    "OpenMC transport + audited statepoint/tallies\n"
    "        ↓\n"
    "Uncertainty-aware CB-PFR screening and ranking\n"
    "        ↓\n"
    "Independent review gates → decision record",
    language="text",
)
st.caption("The arrows describe the intended research pipeline. The current software does not automatically perform every stage end-to-end.")

with st.expander("01 · What the modules show", expanded=True):
    st.markdown("""
- **Overview:** project status and recorded evidence summaries.
- **C5G7 Layout Explorer:** categorical 2×2 UO₂/MOX layout signatures and recorded smoke-run metrics; not a pin-resolved core model.
- **Physics Fields:** fields extracted from an archived OpenMC mesh tally when available. The mesh is not automatically registered to assembly coordinates.
- **Monte Carlo Results:** recorded k-effective means and within-run standard deviations. A single seed per layout cannot establish between-run repeatability.
- **QUBO / Optimization:** abstract QUBO or the separate four-position material-assignment formulation; these formulations must not be silently conflated.
- **Decision Workspace:** side-by-side indicators and reviewer checklist. It intentionally does not declare a physical winner.
- **Provenance & Validation:** input hashes, run metadata, and evidence audit state.
- **Help & Methods:** this protocol and the claim boundary.
""")

with st.expander("02 · Interpret the metrics"):
    st.markdown("""
- **k-effective mean:** estimate reported by the archived transport run; acceptance requires a predeclared, benchmark-appropriate band.
- **Reported standard deviation (σ):** the uncertainty statistic stored with the run. Do not relabel it as a confidence interval across independent runs.
- **Relative SD:** descriptive within-run spread, not a candidate reliability probability.
- **Aggregate flux / fission scores:** use only with their source definitions and units; they are not automatically spatially resolved flux or absolute power.
- **QUBO energy:** objective value of a specific encoded problem. It is not a physical score unless the mapping and objective relationship are documented.
- **CB-PFR score:** post-optimization uncertainty-aware ranking output. It is not a reactor-safety method or a substitute for independent validation.
""")

with st.expander("03 · Minimum reproducibility record"):
    st.markdown("""
Before comparing candidates, retain:
1. Exact geometry, material definitions, temperatures, and burnup/composition assumptions.
2. Nuclear-data library and hash, plus audited multigroup boundaries when using MGXS.
3. OpenMC version, settings, seeds, tally definitions, statepoint hashes, and logs.
4. Explicit candidate-to-geometry/material mapping and invariants.
5. Repeated independent runs and a predeclared uncertainty/convergence procedure.
6. Physical acceptance limits and an independent benchmark-comparison protocol.
7. The analysis code/configuration version and generated machine-readable audit reports.
""")

with st.expander("04 · Current evidence boundary", expanded=True):
    st.warning("Current C5G7 layout runs are exploratory smoke evidence. The repository records that legacy burnup-state QUBO labels have no defensible mapping to C5G7 materials. The corrected-group repeated-run study is internally audited, but physical winner selection remains blocked pending approved acceptance criteria and independent tally review.")
    st.markdown("""
**Supported:** software integration tests, exact enumeration for small encoded instances, archived-run parsing, provenance checks, and descriptive comparisons of recorded data.

**Not established:** benchmark-grade C5G7 physical validation, a physically acceptable winning layout, a validated legacy-QUBO-to-material mapping, reactor-safety conclusions, or quantum advantage from a QPU.

**Rule:** if evidence is missing or ambiguous, keep the gate blocked and report the limitation explicitly.
""")

st.markdown("### Source files and protocols")
st.markdown("""
- [Repository README and evidence index](https://github.com/thenextw4ng/cb-pfr/blob/main/README.md)
- [C5G7 validation and mapping plan](https://github.com/thenextw4ng/cb-pfr/blob/main/reports/C5G7_VALIDATION_AND_MAPPING_PLAN.md)
- [Validation claim decision](https://github.com/thenextw4ng/cb-pfr/blob/main/reports/VALIDATION_CLAIM_DECISION_2026-10-11.md)
- [Corrected-group repeatability smoke report](https://github.com/thenextw4ng/cb-pfr/blob/main/reports/c5g7_corrected_group_repeatability_smoke_2026-10-11.md)
- [BEAVRS experimental comparison protocol](https://github.com/thenextw4ng/cb-pfr/blob/main/reports/BEAVRS_CYCLE1_EXPERIMENTAL_COMPARISON_PROTOCOL.md)
""")
