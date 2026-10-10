"""ReactorQ Studio: transparent dashboard for QUBO/CB-PFR research experiments.

The bundled demo estimates are synthetic. This application does not claim to run
OpenMC unless a separately configured, validated OpenMC model is supplied.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from cbpfr.integration import rank_candidate_batch, ranking_to_records
from cbpfr.openmc import preflight_openmc
from cbpfr.qubo import CoreSpec, build_usmanov_style_qubo, enumerate_feasible_candidates
from cbpfr.ranking import MetricLimit, PhysicalEstimate

st.set_page_config(page_title="ReactorQ Studio", page_icon="⚛️", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1440px;}
.hero {padding: 1.5rem 1.8rem; border: 1px solid rgba(128,128,128,.25);
       border-radius: 18px; background: linear-gradient(120deg, rgba(40,90,150,.13), rgba(35,160,130,.08));}
.muted {color: #8b949e;}
</style>
<div class="hero">
  <h1>⚛️ ReactorQ Studio</h1>
  <p>QUBO optimization · uncertainty-aware ranking · OpenMC readiness</p>
  <p class="muted">Research prototype — demo data is synthetic, not reactor simulation evidence.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Experiment setup")
    run_mode = st.radio("Data source", ["Synthetic demo", "OpenMC preflight"], index=0)
    st.caption("Synthetic demo illustrates the pipeline only. It does not invoke OpenMC.")
    candidate_count = st.slider("Candidates to rank", min_value=4, max_value=20, value=12, step=4)
    uncertainty = st.slider("Demo uncertainty", min_value=0.0, max_value=0.15, value=0.02, step=0.005)
    margin = st.slider("Uniform comparison margin", min_value=0.0, max_value=0.2, value=0.04, step=0.01)
    model_dir = st.text_input("OpenMC model directory", value="openmc_model")
    run = st.button("Run experiment", type="primary", use_container_width=True)

@st.cache_data
def build_demo():
    spec = CoreSpec(
        name="abstract-seven-position-demo",
        positions=tuple(f"p{i}" for i in range(7)),
        boundary=frozenset(f"p{i}" for i in range(6)),
        inner=frozenset({"p6"}),
        edges=tuple((f"p{i}", f"p{(i + 1) % 6}") for i in range(6)),
        inventory=(3, 3, 1),
        description="Abstract topology for software demonstration; not a reactor geometry.",
    )
    model = build_usmanov_style_qubo(spec)
    candidates = enumerate_feasible_candidates(model)
    return spec, model, candidates

spec, model, candidates = build_demo()
tab_overview, tab_rank, tab_openmc, tab_export = st.tabs(
    ["Overview", "Candidate ranking", "OpenMC status", "Export & provenance"]
)

with tab_overview:
    st.subheader("Experiment overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Core positions", len(spec.positions))
    c2.metric("QUBO variables", model.variable_count)
    c3.metric("Feasible candidates", len(candidates))
    c4.metric("Execution mode", "Demo" if run_mode == "Synthetic demo" else "Preflight")
    st.warning("The built-in seven-position model is an abstract software fixture. It is not a validated reactor model and its labels are not mapped to OpenMC materials.")
    st.markdown("**Pipeline**")
    st.code("QUBO model → feasible candidates → evaluation records → four ranking baselines → CSV/JSON export", language="text")
    st.markdown("**Evidence boundary**")
    st.write("- Demo estimates are generated in-app and labelled synthetic.")
    st.write("- A green OpenMC preflight means required runtime/files are present; it does not validate model physics.")
    st.write("- keff, flux, and power distribution are not invented or populated from demo values.")

with tab_rank:
    st.subheader("Compare candidate selection methods")
    if run or "records" not in st.session_state:
        if run_mode == "OpenMC preflight":
            st.info("Preflight only: this action checks readiness. It does not run a transport simulation.")
            st.session_state["records"] = []
            st.session_state["run_metadata"] = {"mode": "openmc_preflight", "timestamp_utc": datetime.now(timezone.utc).isoformat()}
        else:
            selected = candidates[:candidate_count]
            # Deterministic fixture values for repeatable UI demonstrations, not physical estimates.
            estimates = {
                c.candidate_id: PhysicalEstimate(
                    c.candidate_id,
                    {"demo_response": (0.88 + ((i * 7) % 13) / 100, uncertainty * (1 + (i % 3) / 2))},
                )
                for i, c in enumerate(selected)
            }
            metric = MetricLimit(
                name="demo_response", upper=1.0, z=1.0, scale=1.0,
                uncertainty_kind="synthetic_fixture", units="arbitrary demo units",
                bound_kind="operational_heuristic",
            )
            rankings = rank_candidate_batch(model, selected, estimates, [metric], {"demo_response": margin})
            records = ranking_to_records(rankings, data_kind="synthetic")
            st.session_state["records"] = records
            st.session_state["run_metadata"] = {
                "mode": "synthetic_demo",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "candidate_count": len(selected),
                "metric": "demo_response",
                "uncertainty": uncertainty,
                "uniform_margin": margin,
                "physical_simulation_performed": False,
            }
    records = st.session_state.get("records", [])
    if records:
        df = pd.DataFrame(records)
        st.caption("All rows below are synthetic software-demo rankings, not OpenMC results.")
        methods = list(df["method"].drop_duplicates())
        selected_method = st.selectbox("Method", methods, index=methods.index("cb_pfr") if "cb_pfr" in methods else 0)
        view = df[df["method"] == selected_method].copy()
        view["candidate_vector"] = view["candidate_vector"].apply(lambda v: str(v))
        st.dataframe(view[["rank", "candidate_id", "qubo_feasible", "qubo_energy", "candidate_vector", "data_kind"]], use_container_width=True, hide_index=True)
        summary = df.groupby("method", as_index=False).agg(candidates=("candidate_id", "count"), best_energy=("qubo_energy", "min"))
        st.markdown("**Method coverage**")
        st.dataframe(summary, use_container_width=True, hide_index=True)
    else:
        st.info("Click Run experiment in the sidebar to generate demo rankings or check OpenMC readiness.")

with tab_openmc:
    st.subheader("OpenMC runtime and model preflight")
    preflight = preflight_openmc(Path(model_dir))
    if preflight.runnable:
        st.success("Runtime preflight ready — model still requires scientific validation.")
    else:
        st.error("OpenMC preflight blocked")
    st.json(preflight.to_dict())
    st.markdown("Required XML inputs: materials.xml, geometry.xml, settings.xml, plus an installed OpenMC executable and valid OPENMC_CROSS_SECTIONS path.")
    st.warning("This prototype intentionally does not convert abstract burnup labels into materials. No transport simulation is started from this dashboard.")

with tab_export:
    st.subheader("Reproducibility and exports")
    metadata = st.session_state.get("run_metadata", {"mode": "not_run", "physical_simulation_performed": False})
    st.json(metadata)
    records = st.session_state.get("records", [])
    if records:
        df = pd.DataFrame(records)
        st.download_button("Download rankings CSV", df.to_csv(index=False).encode("utf-8"), "reactorq_rankings.csv", "text/csv")
        st.download_button("Download rankings JSON", json.dumps({"metadata": metadata, "records": records}, indent=2).encode("utf-8"), "reactorq_experiment.json", "application/json")
    else:
        st.caption("Run the synthetic demo to enable ranking exports.")
    st.caption("Reproducibility note: the UI demo uses deterministic fixture estimates. It is not a stochastic solver study or physical validation.")
