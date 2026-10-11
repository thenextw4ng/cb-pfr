"""Quantum optimization workstation for the separate C5G7 material-placement QUBO.

The current C5G7 QUBO encodes the exactly-two-MOX constraint only. It does not
contain OpenMC response as an objective; all six feasible layouts tie in QUBO
energy and must be evaluated by the downstream physics pipeline.
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
st.caption("Solver-aware workstation · QUBO feasibility is not a physical-performance objective")

st.markdown(
    """
    This page demonstrates the **C5G7 material-placement encoding** as a small,
    inspectable QUBO. It is a separate formulation from the legacy Usmanov-style
    fresh/once-burned/twice-burned model.

    The current objective penalizes violation of **exactly two MOX and two UO₂
    assemblies**. It does not encode neutron flux, k-effective, fission-rate
    peaking, or OpenMC results. Therefore, all six feasible layouts have equal
    QUBO energy: the QUBO generates feasible candidates; the physics evaluator
    must assess their reactor responses.
    """
)

q = upper_triangular_qubo()
coeff_rows = []
for i in range(len(POSITIONS)):
    for j in range(i, len(POSITIONS)):
        coeff_rows.append({"variable_i": POSITIONS[i], "variable_j": POSITIONS[j], "Q_ij": q[i][j]})
with st.expander("Inspect the mathematical encoding", expanded=True):
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
        "qubo_energy_without_offset": qubo_energy(vector),
        "feasible": sum(vector) == 2,
        "assignment": json.dumps(assignment_from_vector(vector)) if sum(vector) == 2 else "infeasible",
    })
df = pd.DataFrame(states).sort_values(["feasible", "qubo_energy_without_offset", "vector"], ascending=[False, True, True])
feasible_df = df[df["feasible"]].copy()

m1, m2, m3 = st.columns(3)
m1.metric("Binary variables", len(POSITIONS))
m2.metric("Total bitstrings", len(states))
m3.metric("Feasible layouts", len(feasible_df))
st.subheader("Feasible candidate pool")
st.dataframe(feasible_df[["vector", "MOX_count", "qubo_energy_without_offset", "assignment"]], use_container_width=True, hide_index=True)
st.info("All six feasible candidates tie in this QUBO. Selecting one as physically superior from QUBO energy alone would be incorrect.")

st.subheader("Solver backends")
st.markdown(
    "- **Exact enumeration** — classical reference; checks all 16 bitstrings and identifies all six feasible layouts.\n"
    "- **Ocean simulated annealing** — optional classical stochastic sampler, if dimod is installed. This is not quantum hardware.\n"
    "- **Quantum annealer / QPU** — requires a configured hardware/cloud sampler, credentials, solver metadata, and retained run records."
)
dimod_available = importlib.util.find_spec("dimod") is not None
dwave_available = importlib.util.find_spec("dwave") is not None
b1, b2 = st.columns(2)
b1.metric("dimod installed", "Yes" if dimod_available else "No")
b2.metric("dwave package installed", "Yes" if dwave_available else "No")
if dimod_available:
    if st.button("Run classical simulated annealing", type="primary"):
        try:
            import dimod
            sampler = dimod.SimulatedAnnealingSampler()
            samples = sampler.sample_qubo(
                {(i, j): q[i][j] for i in range(len(POSITIONS)) for j in range(i, len(POSITIONS)) if q[i][j] != 0},
                num_reads=100,
            )
            sample_rows = []
            for row in samples.data(fields=["sample", "energy", "num_occurrences"]):
                vector = tuple(int(row.sample[i]) for i in range(len(POSITIONS)))
                sample_rows.append({
                    "vector": "".join(map(str, vector)),
                    "MOX_count": sum(vector),
                    "sampler_energy_without_offset": float(row.energy),
                    "recomputed_feasibility_energy": qubo_energy(vector),
                    "occurrences": int(row.num_occurrences),
                })
            st.dataframe(pd.DataFrame(sample_rows), use_container_width=True, hide_index=True)
            st.caption("This was a classical simulated-annealing run. The constant offset is omitted by the sampler and does not affect the minimizer.")
        except Exception as exc:
            st.error(f"Sampler run failed: {exc}")
else:
    st.caption("Install the optional dwave-ocean-sdk package in the dashboard environment to enable the classical Ocean sampler demonstration.")

st.subheader("Handoff to physics and CB-PFR")
st.code(
    "QUBO formulation + solver metadata\n"
    "  -> candidate vectors and feasibility audit\n"
    "  -> per-candidate OpenMC / measurement evaluation with provenance\n"
    "  -> CB-PFR ranking against declared metric limits\n"
    "  -> reproducible decision bundle",
    language="text",
)
st.warning(
    "No OpenMC simulation is launched from this page. No QPU execution, quantum advantage, "
    "physical validation, or reactor-safety conclusion is claimed."
)
