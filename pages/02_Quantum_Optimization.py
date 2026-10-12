"""Quantum optimization workstation for CB-PFR's separate QUBO layers.

The material-placement QUBO encodes exactly two MOX only. The physics-informed
CB-PFR selector QUBO is a second-stage model built only after physical evaluation
and conservative screening. These are different formulations and must not be conflated.
"""
from __future__ import annotations

import importlib.util
import itertools
import json

import pandas as pd
import streamlit as st

from cbpfr.c5g7_design_qubo import POSITIONS, assignment_from_vector, qubo_energy, upper_triangular_qubo

st.set_page_config(page_title="QUBO & Quantum Optimization", page_icon="⚛️", layout="wide")
st.title("QUBO & Quantum Optimization")
st.caption("Solver-aware workstation · optimization, physics evaluation, and selection are separate stages")

st.markdown(
    """
    This page separates two QUBO roles:
    1. **Material-placement feasibility:** encode exactly two MOX and two UO₂ assemblies.
    2. **CB-PFR candidate selection:** after physical evaluations and conservative screening,
       encode a one-hot selector over the six layouts using the declared risk-adjusted scores
       and feasibility penalties.

    The legacy Usmanov-style fresh/once-burned/twice-burned QUBO is a third, separate
    formulation. Candidate encodings must not be silently mapped between these models.
    """
)

q = upper_triangular_qubo()
coeff_rows = []
for i in range(len(POSITIONS)):
    for j in range(i, len(POSITIONS)):
        coeff_rows.append({"variable_i": POSITIONS[i], "variable_j": POSITIONS[j], "Q_ij": q[i][j]})
with st.expander("Layer 1 — inspect material-placement encoding", expanded=True):
    st.latex(r"E(y)=A\left(\sum_{i=1}^{4} y_i-2\right)^2")
    st.markdown(
        r"Here $y_i=1$ denotes MOX and $y_i=0$ denotes UO$_2$. "
        r"After expansion, $E(y)=4A-3A\sum_i y_i+2A\sum_{i<j}y_i y_j$. "
        r"The constant offset is omitted from the stored upper-triangular Q matrix."
    )
    st.dataframe(pd.DataFrame(coeff_rows), use_container_width=True, hide_index=True)

states = []
for vector in itertools.product((0, 1), repeat=len(POSITIONS)):
    states.append({
        "vector": "".join(map(str, vector)),
        "MOX_count": sum(vector),
        "qubo_energy": qubo_energy(vector),
        "feasible": sum(vector) == 2,
        "assignment": json.dumps(assignment_from_vector(vector)) if sum(vector) == 2 else "infeasible",
    })
df = pd.DataFrame(states).sort_values(["feasible", "qubo_energy", "vector"], ascending=[False, True, True])
feasible_df = df[df["feasible"]].copy()

m1, m2, m3 = st.columns(3)
m1.metric("Binary variables", len(POSITIONS))
m2.metric("Total bitstrings", len(states))
m3.metric("Feasible layouts", len(feasible_df))
st.subheader("Material-placement candidate pool")
st.dataframe(feasible_df[["vector", "MOX_count", "qubo_energy", "assignment"]], use_container_width=True, hide_index=True)
st.info("All six feasible layouts tie in this first-stage QUBO. It generates feasible candidates; it cannot identify the physically superior layout.")

st.subheader("Layer 2 — physics-informed CB-PFR selector QUBO")
st.markdown(
    """
    The selector QUBO is generated **after** repeated OpenMC evaluations and CB-PFR
    conservative screening. Its six binary variables indicate which candidate is selected.
    The diagonal terms combine normalized risk-adjusted scores and a penalty for candidates
    that fail the screen; pairwise terms enforce one-hot selection. The constant offset is
    retained in the emitted report.

    This is the meaningful solver handoff for the current CB-PFR workflow: a candidate's
    physical metrics determine its declared score, then a solver minimizes the selector QUBO.
    The existing pipeline uses exact enumeration as the reference. An optional Ocean sampler
    can be compared against that exact result.
    """
)
st.code(
    "python scripts/run_c5g7_cbpfr_physical_selection.py [declared limits and run-level CSV]\n"
    "python scripts/solve_c5g7_cbpfr_qubo.py \\\n"
    "  --selection-report path/to/accepted_selection.json \\\n"
    "  --out artifacts/selector_solver_run.json \\\n"
    "  --backend ocean-sa",
    language="bash",
)
st.caption("Use --backend dwave-qpu only with configured D-Wave credentials and actual QPU access. The solver adapter refuses reports without an accepted conservative candidate.")
st.warning("The archived low-budget smoke evidence has not established a validated physical winner. Do not feed it to the selector solver as if it were accepted benchmark evidence.")

st.subheader("Solver backends")
st.markdown(
    "- **Exact enumeration** — classical reference; exhaustive for these small binary spaces.\n"
    "- **Ocean simulated annealing** — optional classical stochastic sampler; not quantum hardware.\n"
    "- **Quantum annealer / QPU** — requires configured hardware/cloud credentials and retained provider run metadata."
)
dimod_available = importlib.util.find_spec("dimod") is not None
dwave_available = importlib.util.find_spec("dwave") is not None
b1, b2 = st.columns(2)
b1.metric("dimod installed", "Yes" if dimod_available else "No")
b2.metric("dwave package installed", "Yes" if dwave_available else "No")
if dimod_available:
    st.success("Ocean's Python package is available in this environment. The selector solver script can run the classical simulated-annealing backend.")
else:
    st.caption("Install the optional dwave-ocean-sdk package in the dashboard environment to enable the classical Ocean sampler.")
st.subheader("Handoff to physics and CB-PFR")
st.code(
    "QUBO formulation + solver metadata\n"
    "  -> candidate vectors and feasibility audit\n"
    "  -> per-candidate OpenMC / measurement evaluation with provenance\n"
    "  -> CB-PFR conservative screen and risk-adjusted score\n"
    "  -> one-hot selector QUBO\n"
    "  -> exact reference vs optional Ocean/QPU solver\n"
    "  -> reproducible decision bundle",
    language="text",
)
st.warning(
    "No OpenMC simulation is launched from this page. No QPU execution, quantum advantage, "
    "physical validation, or reactor-safety conclusion is claimed."
)
