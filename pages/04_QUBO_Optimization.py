"""Exact four-variable QUBO constraint explorer (not a physical performance optimizer)."""
from itertools import product

import plotly.graph_objects as go
import streamlit as st

from cbpfr.dashboard_ui import (
    CYAN, ORANGE, apply_workstation_style, base_layout, layout_figure,
    load_smoke, render_header, render_workspace_sidebar,
)

st.set_page_config(page_title="CB-PFR · QUBO Optimization", page_icon="⚛", layout="wide")
apply_workstation_style()
render_header("QUBO", "EXACT COMBINATORICS · NOT PHYSICAL VALIDATION")

st.markdown('<div class="section-kicker">Constraint formulation</div>', unsafe_allow_html=True)
st.title("QUBO / Optimization")
st.caption("Explore the exact feasible design space for a four-position, two-material count constraint.")
render_workspace_sidebar("QUBO / Optimization", load_smoke())

st.latex(r"E(y)=A\left(\sum_{i=1}^{4} y_i-2\right)^2,\qquad y_i\in\{0,1\}")
st.write("Here 1 = MOX and 0 = UO₂. The penalty is zero exactly when two of the four positions are MOX and two are UO₂. It enforces feasibility only; it does not encode physical performance.")

penalty = st.slider("Constraint penalty A", min_value=0.5, max_value=10.0, value=1.0, step=0.5)
rows = []
for bits in product((0, 1), repeat=4):
    count = sum(bits)
    rows.append({
        "vector": "".join(map(str, bits)),
        "signature": "".join("M" if bit else "U" for bit in bits),
        "p00": "MOX" if bits[0] else "UO₂",
        "p10": "MOX" if bits[1] else "UO₂",
        "p01": "MOX" if bits[2] else "UO₂",
        "p11": "MOX" if bits[3] else "UO₂",
        "mox_count": count,
        "energy": penalty * (count - 2) ** 2,
        "feasible": count == 2,
    })

a, b, c, d = st.columns(4)
a.metric("Binary vectors", len(rows))
b.metric("Feasible layouts", sum(row["feasible"] for row in rows))
c.metric("Infeasible vectors", sum(not row["feasible"] for row in rows))
d.metric("Feasible penalty energy", "0 exactly")

left, right = st.columns([1.4, 1], gap="large")
with left:
    st.markdown('<div class="panel-title">Exact penalty landscape</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">All 16 binary vectors; feasible vectors have exactly two 1s.</div>', unsafe_allow_html=True)
    fig = go.Figure(go.Bar(
        x=[row["vector"] for row in rows],
        y=[row["energy"] for row in rows],
        marker_color=[CYAN if row["feasible"] else "#36516b" for row in rows],
        customdata=[[row["signature"], row["mox_count"], row["feasible"]] for row in rows],
        hovertemplate="Binary vector %{x}<br>Layout %{customdata[0]}<br>MOX count %{customdata[1]}<br>Feasible %{customdata[2]}<br>Penalty energy %{y:.3f}<extra></extra>",
    ))
    base_layout(fig, height=380)
    fig.update_layout(xaxis_title="Binary vector y₁y₂y₃y₄", yaxis_title="Penalty energy E(y)", showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
with right:
    st.markdown('<div class="panel-title">Inspect one design vector</div>', unsafe_allow_html=True)
    chosen = st.selectbox(
        "Binary vector",
        [row["vector"] for row in rows],
        index=5,
        format_func=lambda vector: next(f'{r["vector"]}  ·  {r["signature"]}' for r in rows if r["vector"] == vector),
    )
    row = next(r for r in rows if r["vector"] == chosen)
    st.plotly_chart(layout_figure(row["signature"]), use_container_width=True, config={"displaylogo": False})
    x, y = st.columns(2)
    x.metric("MOX count", row["mox_count"])
    y.metric("Penalty energy", f'{row["energy"]:.2f}')
    if row["feasible"]:
        st.success("Feasible under the stated material-count constraint.")
    else:
        st.error("Infeasible: the vector does not contain exactly two MOX positions.")

st.markdown("### Complete enumeration")
table = [{
    "Binary vector": row["vector"],
    "Layout signature": row["signature"],
    "P00": row["p00"], "P10": row["p10"], "P01": row["p01"], "P11": row["p11"],
    "MOX count": row["mox_count"], "Penalty energy": row["energy"],
    "Feasible": row["feasible"],
} for row in rows]
st.dataframe(table, use_container_width=True, hide_index=True)
st.caption("The six feasible layouts are the combinations of choosing two MOX positions among four. A zero QUBO penalty is not evidence that a layout is physically preferable in OpenMC.")
st.download_button(
    "Export exact enumeration CSV",
    __import__("pandas").DataFrame(table).to_csv(index=False).encode("utf-8"),
    "cbpfr_qubo_exact_enumeration.csv",
    "text/csv",
)
