"""Exact four-variable QUBO constraint explorer, separate from physical ranking."""
from itertools import product

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from cbpfr.dashboard_ui import (
    CYAN, ORANGE, apply_workstation_style, base_layout, layout_figure,
    load_smoke, render_header, render_page_intro, render_workspace_sidebar,
)

st.set_page_config(page_title="CB-PFR · QUBO Optimization", page_icon="⚛", layout="wide")
apply_workstation_style()
render_header("QUBO", "EXACT COMBINATORICS · NOT PHYSICAL VALIDATION")
df = load_smoke().sort_values("candidate_id").reset_index(drop=True)
render_workspace_sidebar("QUBO / Optimization", df)

render_page_intro(
    "QUBO / CONSTRAINT FORMULATION",
    "QUBO Optimization",
    "Explore the exact feasible design space for a four-position, two-material count constraint. Feasibility is reported separately from transport performance and physical validity.",
)

st.latex(r"E(y)=A\left(\sum_{i=1}^{4} y_i-2\right)^2,\qquad y_i\in\{0,1\}")
st.markdown('<div class="small-muted">Encoding: 1 = MOX · 0 = UO₂. The penalty is zero exactly when two of four positions are MOX. It enforces a count constraint only; it does not encode k-effective, flux, fission, safety, or physical performance.</div>', unsafe_allow_html=True)
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
a.metric("Binary assignments", len(rows))
b.metric("Feasible layouts", sum(row["feasible"] for row in rows))
c.metric("Infeasible assignments", sum(not row["feasible"] for row in rows))
d.metric("Feasible penalty", "0 exactly")

# The exact 16-state landscape is arranged by bit pairs, so neighboring cells
# differ in a compact, inspectable representation of the binary state space.
pair_labels = ["00", "01", "10", "11"]
lookup = {row["vector"]: row for row in rows}
energy_grid = [
    [lookup[first + last]["energy"] for first in pair_labels]
    for last in pair_labels
]
vector_grid = [
    [first + last for first in pair_labels]
    for last in pair_labels
]
hover_grid = [
    [
        [
            lookup[first + last]["vector"],
            lookup[first + last]["signature"],
            lookup[first + last]["mox_count"],
            "Yes" if lookup[first + last]["feasible"] else "No",
        ]
        for first in pair_labels
    ]
    for last in pair_labels
]

chosen = st.selectbox(
    "Inspect binary assignment",
    [row["vector"] for row in rows],
    index=5,
    format_func=lambda vector: next(
        f'{item["vector"]} · {item["signature"]} · E={item["energy"]:.2f}'
        for item in rows if item["vector"] == vector
    ),
)
row = lookup[chosen]

left, right = st.columns([1.35, 1], gap="large")
with left:
    st.markdown('<div class="panel-title">Exact QUBO penalty landscape</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="panel-subtitle">All 16 binary assignments in one energy map. '
        'Outlined markers denote the six exactly-feasible states; the amber marker is the inspected state.</div>',
        unsafe_allow_html=True,
    )
    fig = go.Figure(go.Heatmap(
        x=pair_labels,
        y=pair_labels,
        z=energy_grid,
        text=vector_grid,
        texttemplate="%{text}",
        textfont={"size": 12, "color": "#ffffff"},
        customdata=hover_grid,
        colorscale=[
            [0.0, "#16394b"],
            [0.001, "#55d4df"],
            [0.0011, "#254158"],
            [0.55, "#49617a"],
            [1.0, "#f5bb62"],
        ],
        zmin=0,
        zmax=max(row_item["energy"] for row_item in rows) or 1,
        colorbar={"title": {"text": "Penalty energy"}, "thickness": 13},
        xgap=5,
        ygap=5,
        hovertemplate=(
            "Vector: %{customdata[0]}<br>Layout: %{customdata[1]}"
            "<br>MOX count: %{customdata[2]}<br>Feasible: %{customdata[3]}"
            "<br>Penalty energy: %{z:.4g}<extra></extra>"
        ),
        name="QUBO penalty",
    ))
    feasible_rows = [item for item in rows if item["feasible"]]
    fig.add_trace(go.Scatter(
        x=[item["vector"][:2] for item in feasible_rows],
        y=[item["vector"][2:] for item in feasible_rows],
        mode="markers",
        marker={"symbol": "circle-open", "size": 21, "color": "#ffffff", "line": {"width": 2}},
        name="Feasible states",
        hovertemplate="Feasible state %{x}%{y}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[chosen[:2]],
        y=[chosen[2:]],
        mode="markers",
        marker={"symbol": "star", "size": 20, "color": ORANGE, "line": {"color": "#ffffff", "width": 1}},
        name="Selected state",
        hovertemplate=f"Selected vector {chosen}<extra></extra>",
    ))
    base_layout(fig, height=505)
    fig.update_layout(
        xaxis_title="First bit pair · y₁y₂",
        yaxis_title="Second bit pair · y₃y₄",
        yaxis={"autorange": "reversed", "gridcolor": "#263f52", "linecolor": "#263f52", "scaleanchor": "x", "scaleratio": 1},
        legend={"orientation": "h", "y": 1.08, "x": 0.02},
        margin={"l": 72, "r": 25, "t": 65, "b": 65},
    )
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False}, key="qubo_energy_landscape")

with right:
    st.markdown('<div class="panel-title">Selected state · material assignment</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="panel-subtitle">A categorical 2 × 2 layout view. The cell identities are positional labels, '
        'not pin-resolved geometry.</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(layout_figure(row["signature"], height=330), use_container_width=True, config={"displaylogo": False})
    x, y = st.columns(2)
    x.metric("MOX count", row["mox_count"])
    y.metric("Penalty energy", f'{row["energy"]:.2f}')
    if row["feasible"]:
        st.success("Feasible under the stated material-count constraint.")
    else:
        st.error("Infeasible: the vector does not contain exactly two MOX positions.")
    st.markdown("**Selected vector**")
    st.code(f'y = ({", ".join(chosen)})\nlayout = {row["signature"]}\nE(y) = {row["energy"]:.6g}', language="text")

st.markdown("### Energy by Hamming weight")
st.caption("The penalty depends only on the number of MOX positions; assignments with the same count share the same penalty. This is a cardinality constraint, not a physical-performance objective.")
count_groups = (
    pd.DataFrame(rows)
    .groupby("mox_count", as_index=False)
    .agg(
        assignments=("vector", "count"),
        penalty_energy=("energy", "first"),
        feasible_assignments=("feasible", "sum"),
    )
)
fig_weight = go.Figure(go.Bar(
    x=count_groups["mox_count"],
    y=count_groups["penalty_energy"],
    marker={"color": ["#55d4df" if int(value) == 2 else "#49617a" for value in count_groups["mox_count"]]},
    customdata=count_groups[["assignments", "feasible_assignments"]].to_numpy(),
    text=[f'{int(count)} states' for count in count_groups["assignments"]],
    textposition="outside",
    hovertemplate=(
        "MOX count: %{x}<br>Penalty energy: %{y:.4g}"
        "<br>Assignments: %{customdata[0]}<br>Feasible assignments: %{customdata[1]}<extra></extra>"
    ),
))
base_layout(fig_weight, height=310)
fig_weight.update_layout(
    xaxis_title="Hamming weight / number of MOX positions",
    yaxis_title="Constraint penalty energy",
    showlegend=False,
    margin={"l": 65, "r": 25, "t": 25, "b": 65},
)
st.plotly_chart(fig_weight, use_container_width=True, config={"displaylogo": False}, key="qubo_hamming_weight_summary")

st.markdown("### Complete enumeration")
table = [{
    "Binary vector": row["vector"], "Layout signature": row["signature"],
    "P00": row["p00"], "P10": row["p10"], "P01": row["p01"], "P11": row["p11"],
    "MOX count": row["mox_count"], "Penalty energy": row["energy"], "Feasible": row["feasible"],
} for row in rows]
st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)
st.caption("The six feasible assignments correspond to choosing two MOX positions among four. A zero QUBO penalty does not establish that a layout is physically preferable in OpenMC.")
st.download_button("Export exact enumeration CSV", pd.DataFrame(table).to_csv(index=False).encode("utf-8"), "cbpfr_qubo_exact_enumeration.csv", "text/csv")

st.markdown("### Scientific interpretation")
g1, g2, g3 = st.columns(3)
g1.markdown('<div class="scientific-panel"><div class="scientific-panel-title">What this proves</div><p class="small-muted">Exact feasibility under the chosen cardinality constraint.</p></div>', unsafe_allow_html=True)
g2.markdown('<div class="scientific-panel"><div class="scientific-panel-title">What this does not prove</div><p class="small-muted">A best-performing, safe, or physically validated reactor layout.</p></div>', unsafe_allow_html=True)
g3.markdown('<div class="scientific-panel"><div class="scientific-panel-title">Next required link</div><p class="small-muted">A source-backed objective mapped to verified transport results.</p></div>', unsafe_allow_html=True)
