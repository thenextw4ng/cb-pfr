"""Evidence-aware physics-field explorer with verified OpenMC mesh tally maps."""
from pathlib import Path
import hashlib
import io
import json
import zipfile

import h5py
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st



ROOT = Path(__file__).resolve().parents[1]
STATEPOINT_ARCHIVE = ROOT / "OpenMC_HDF5_Evidence_2026-10-11.zip"
STATEPOINT_BASELINE = ROOT / "evidence" / "openmc_local_baseline_2026-10-11" / "statepoint_summary.json"
PRODUCTION_MEMBER = "c5g7-run/2d/statepoint.20000.h5"


def _decode_h5_text(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").rstrip("\x00")
    if hasattr(value, "item"):
        try:
            return _decode_h5_text(value.item())
        except (ValueError, TypeError):
            pass
    return str(value)


def _read_mesh_statepoint(data: bytes):
    """Read the audited OpenMC HDF5 mesh tally; never infer material identity."""
    with h5py.File(io.BytesIO(data), "r") as handle:
        if "tallies" not in handle:
            raise ValueError("The HDF5 file has no OpenMC tallies group.")
        tallies = handle["tallies"]
        meshes = []
        if "meshes" in tallies:
            for name, mesh in tallies["meshes"].items():
                if "dimension" in mesh:
                    dims = [int(v) for v in np.asarray(mesh["dimension"][()]).reshape(-1)]
                    if len(dims) == 3:
                        meshes.append((name, dims))
        records = []
        for name, tally in tallies.items():
            if not name.startswith("tally ") or not hasattr(tally, "keys"):
                continue
            if "results" not in tally or "score_bins" not in tally:
                continue
            scores = [_decode_h5_text(v) for v in np.asarray(tally["score_bins"][()]).reshape(-1)]
            raw = np.asarray(tally["results"][()])
            if raw.ndim == 4 and raw.shape[1] == 1:
                raw = raw[:, 0, :, :]
            if raw.ndim != 3 or raw.shape[-1] != 2 or raw.shape[-2] != len(scores):
                continue
            n_bins = raw.shape[0]
            matching_mesh = next((item for item in meshes if int(np.prod(item[1])) == n_bins), None)
            if matching_mesh is None:
                continue
            dims = matching_mesh[1]
            if dims[2] != 1 or dims[0] * dims[1] != n_bins:
                continue
            records.append({
                "tally_name": name,
                "mesh_name": matching_mesh[0],
                "dimensions": dims,
                "scores": scores,
                "mean": np.asarray(raw[:, :, 0], dtype=float),
                "std_dev": np.asarray(raw[:, :, 1], dtype=float),
            })
        if not records:
            raise ValueError("No 2-D mesh tally with a recognized OpenMC results layout was found.")
        keff = None
        if "k_combined" in handle:
            values = np.asarray(handle["k_combined"][()]).reshape(-1)
            if values.size >= 2:
                keff = {"mean": float(values[0]), "std_dev": float(values[1])}
        settings = {}
        for key in ("n_batches", "n_inactive", "n_particles", "n_realizations", "run_mode", "energy_mode"):
            if key in handle:
                value = handle[key][()]
                settings[key] = _decode_h5_text(value) if key in ("run_mode", "energy_mode") else int(np.asarray(value).item())
        return {"mesh_tallies": records, "keff": keff, "settings": settings}


def _load_bundled_statepoint():
    """Load the production statepoint from the committed evidence ZIP."""
    if not STATEPOINT_ARCHIVE.is_file():
        raise FileNotFoundError(f"Evidence archive not found: {STATEPOINT_ARCHIVE.name}")
    with zipfile.ZipFile(STATEPOINT_ARCHIVE) as archive:
        matches = [n for n in archive.namelist() if n == PRODUCTION_MEMBER]
        if len(matches) != 1:
            raise ValueError(f"Expected one {PRODUCTION_MEMBER} entry, found {len(matches)}.")
        data = archive.read(matches[0])
    expected_hash = None
    if STATEPOINT_BASELINE.is_file():
        baseline = json.loads(STATEPOINT_BASELINE.read_text(encoding="utf-8"))
        expected_hash = baseline.get("statepoint_file_sha256")
    actual_hash = hashlib.sha256(data).hexdigest()
    return data, actual_hash, expected_hash

from cbpfr.dashboard_ui import (
    CYAN, MUTED, apply_workstation_style, base_layout, candidate_label,
    layout_figure, load_smoke, render_header, render_page_intro, render_workspace_sidebar,
)

st.set_page_config(page_title="CB-PFR · Physics Field Explorer", page_icon="⚛", layout="wide")
apply_workstation_style()
render_header("Physics fields", "STATEPOINT-BASED MESH TALLIES")
df = load_smoke().sort_values("candidate_id").reset_index(drop=True)
render_workspace_sidebar("Physics Fields", df)

render_page_intro(
    "PHYSICS FIELD EXPLORER / C5G7 2×2 STUDY",
    "Physics Field Explorer",
    "Compare recorded aggregate evidence with the archived OpenMC mesh tally. Spatial maps use the actual 51 × 51 statepoint bins; mesh indices are not mapped to materials or assembly positions.",
)

a, b, c, d = st.columns(4)
a.metric("Layout records", len(df))
b.metric("Aggregate flux scores", int(df["aggregate_flux_score"].notna().sum()))
c.metric("Aggregate fission scores", int(df["aggregate_fission_score"].notna().sum()))
d.metric("Verified mesh bins", "2,601")

st.markdown(
    '<div class="evidence-note"><b>Scientific boundary</b> · The candidate CSV contains aggregate scores only, but the separately archived production statepoint contains a 51 × 51 mesh tally with flux, fission, nu-fission, and standard deviations. The maps below show those recorded tally bins—not absolute power, material identity, or a validated assembly map.</div>',
    unsafe_allow_html=True,
)
st.write("")

control, spacer = st.columns([1.1, 2.4])
with control:
    view = st.selectbox("Analysis metric", ["Assembly placement", "k-effective", "Aggregate flux score", "Aggregate fission score"])
with spacer:
    st.markdown('<div class="small-muted" style="padding-top:28px">Use the candidate selector to compare a specific layout against the recorded dataset.</div>', unsafe_allow_html=True)
selected_id = st.selectbox(
    "Selected candidate",
    df["candidate_id"].tolist(),
    format_func=lambda value: candidate_label(df.loc[df["candidate_id"] == value].iloc[0]),
)
selected = df.loc[df["candidate_id"] == selected_id].iloc[0]

left, right = st.columns([.92, 1.55], gap="large")
with left:
    st.markdown('<div class="panel-title">Assembly placement</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">2×2 categorical arrangement · U = UO₂ · M = MOX</div>', unsafe_allow_html=True)
    st.plotly_chart(layout_figure(str(selected["layout_signature"]), height=350), use_container_width=True, config={"displaylogo": False})
    st.caption(f'Reference: {selected["candidate_id"]} · seed {int(selected["seed"])}')
    st.markdown('<div class="small-muted">Squares are assembly positions, not pin cells, material volumes, or a transport mesh.</div>', unsafe_allow_html=True)

with right:
    metric_map = {
        "Assembly placement": ("keff_mean", "keff_std_dev", "Recorded k-effective mean", "k-effective (reported mean)", True),
        "k-effective": ("keff_mean", "keff_std_dev", "Recorded k-effective mean", "k-effective (reported mean)", True),
        "Aggregate flux score": ("aggregate_flux_score", None, "Aggregate flux score", "Repository score (units not specified)", False),
        "Aggregate fission score": ("aggregate_fission_score", None, "Aggregate fission score", "Repository score (units not specified)", False),
    }
    metric, error_col, chart_title, y_title, show_error = metric_map[view]
    ordered = df.sort_values(metric)
    colors = [CYAN if x == selected_id else "#36536e" for x in ordered["candidate_id"]]
    fig = go.Figure(go.Bar(
        x=[candidate_label(row) for _, row in ordered.iterrows()],
        y=ordered[metric],
        marker_color=colors,
        error_y=({"type": "data", "array": ordered[error_col], "visible": True, "color": MUTED, "thickness": 1.4, "width": 4} if show_error else None),
        customdata=ordered[["candidate_id", "layout_signature", "seed"]].to_numpy(),
        hovertemplate="Candidate %{customdata[0]}<br>Layout %{customdata[1]}<br>Seed %{customdata[2]}<br>" + y_title + ": %{y:.7f}<extra></extra>",
    ))
    base_layout(fig, height=445, title={"text": chart_title, "x": .02, "font": {"size": 14}})
    fig.update_layout(xaxis_title="Candidate / layout", yaxis_title=y_title, showlegend=False)
    fig.update_xaxes(tickangle=-22)
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

st.markdown("### Selected record")
record_cols = ["candidate_id", "layout_signature", "canonical_reference", "seed", "keff_mean", "keff_std_dev", "aggregate_flux_score", "aggregate_fission_score"]
st.dataframe(df.loc[df["candidate_id"] == selected_id, record_cols], use_container_width=True, hide_index=True)
st.caption("k-effective whiskers show the reported within-run standard deviation, not a confidence interval or a between-seed reproducibility estimate.")

st.markdown("### OpenMC spatial tally maps")
st.markdown(
    '<div class="panel-subtitle">Values are read from the archived production statepoint using the HDF5 tally datasets. Mesh axes are bin indices only; they are not assembly coordinates.</div>',
    unsafe_allow_html=True,
)
uploaded_statepoint = st.file_uploader(
    "Optional: inspect another OpenMC statepoint (.h5)",
    type=["h5"],
    help="Leave empty to use the production statepoint already archived with this repository.",
)
try:
    if uploaded_statepoint is not None:
        statepoint_bytes = uploaded_statepoint.getvalue()
        statepoint_hash = hashlib.sha256(statepoint_bytes).hexdigest()
        expected_hash = None
        statepoint_origin = f"Uploaded file · {uploaded_statepoint.name}"
    else:
        statepoint_bytes, statepoint_hash, expected_hash = _load_bundled_statepoint()
        statepoint_origin = "Repository evidence archive · statepoint.20000.h5"
    statepoint = _read_mesh_statepoint(statepoint_bytes)
    hash_matches = expected_hash is not None and statepoint_hash == expected_hash
    if uploaded_statepoint is None:
        if hash_matches:
            st.success("Production statepoint loaded; SHA-256 matches the recorded baseline.")
        else:
            st.warning("Statepoint loaded, but its SHA-256 does not match the recorded baseline. Check provenance before comparing results.")
    else:
        st.info("Uploaded statepoint loaded for inspection. Its identity has not been associated with a candidate layout.")
    st.caption(f"{statepoint_origin} · SHA-256: {statepoint_hash}")
    if not statepoint["mesh_tallies"]:
        st.warning("No compatible mesh tallies were found in this statepoint.")
        st.stop()
    mesh_tally = st.selectbox(
        "Mesh tally",
        statepoint["mesh_tallies"],
        format_func=lambda item: f'{item["tally_name"]} · {item["dimensions"][0]} × {item["dimensions"][1]} mesh',
        key="physics_mesh_tally",
    )
    if not mesh_tally["scores"]:
        st.warning("The selected mesh tally has no readable score bins.")
        st.stop()
    score_name = st.selectbox("Tally score", mesh_tally["scores"], key="physics_tally_score")
    view_col, scale_col, palette_col = st.columns([1, 1, 1.2])
    with view_col:
        field_view = st.selectbox("Field view", ["Mean tally", "Relative SD (%)"], key="physics_field_view")
    with scale_col:
        color_scale = st.selectbox("Mean scale", ["Log₁₀", "Linear"], key="physics_mean_scale")
    with palette_col:
        palette = st.selectbox("Mean color palette", ["Viridis", "Cividis", "Plasma", "Turbo"], key="physics_palette")
    score_index = mesh_tally["scores"].index(score_name)
    dims = mesh_tally["dimensions"]
    mean_values = mesh_tally["mean"][:, score_index]
    sd_values = mesh_tally["std_dev"][:, score_index]
    mean_grid = mean_values.reshape((dims[1], dims[0]))
    sd_grid = sd_values.reshape((dims[1], dims[0]))
    rel_grid = np.full(mean_grid.shape, np.nan, dtype=float)
    positive = np.isfinite(mean_grid) & (mean_grid > 0) & np.isfinite(sd_grid) & (sd_grid >= 0)
    rel_grid[positive] = 100.0 * sd_grid[positive] / mean_grid[positive]

    metric_left, metric_right = st.columns([1.55, 1], gap="large")
    with metric_left:
        positive_values = mean_values[np.isfinite(mean_values) & (mean_values > 0)]
        if field_view == "Relative SD (%)":
            field_grid = rel_grid
            hover_values = rel_grid
            field_title = f"{score_name} · relative Monte Carlo SD"
            colorbar_title = "Relative SD (%)"
            colorscale = "Magma"
        else:
            field_grid = mean_grid.copy()
            if color_scale == "Log₁₀":
                field_grid[~positive] = np.nan
                field_grid[positive] = np.log10(field_grid[positive])
                colorbar_title = "log₁₀(score mean)"
            else:
                field_grid[~np.isfinite(field_grid)] = np.nan
                colorbar_title = "Score mean"
            hover_values = mean_grid
            field_title = f"{score_name} · mesh tally mean ({color_scale.lower()} display)"
            colorscale = palette
        if np.isfinite(field_grid).any():
            fig_mesh = go.Figure(go.Heatmap(
                z=field_grid,
                customdata=hover_values,
                colorscale=colorscale,
                colorbar={"title": colorbar_title},
                hovertemplate="Mesh x-bin %{x}<br>Mesh y-bin %{y}<br>Recorded value %{customdata:.6g}<extra></extra>",
                connectgaps=False,
            ))
            fig_mesh.update_layout(
                title=field_title,
                xaxis_title="Mesh x-bin index",
                yaxis_title="Mesh y-bin index",
                yaxis={"autorange": "reversed"},
            )
            base_layout(fig_mesh, height=520)
            st.plotly_chart(fig_mesh, use_container_width=True, config={"displaylogo": False, "scrollZoom": True})
        else:
            st.warning("No finite values are available for this selected field.")
    with metric_right:
        fig_unc = go.Figure(go.Heatmap(
            z=rel_grid,
            colorscale="Magma",
            colorbar={"title": "Relative SD (%)"},
            hovertemplate="Mesh x-bin %{x}<br>Mesh y-bin %{y}<br>Relative SD %{z:.4g}%<extra></extra>",
            connectgaps=False,
        ))
        fig_unc.update_layout(
            title=f"{score_name} · relative Monte Carlo SD",
            xaxis_title="Mesh x-bin index",
            yaxis_title="Mesh y-bin index",
            yaxis={"autorange": "reversed"},
        )
        base_layout(fig_unc, height=520)
        st.plotly_chart(fig_unc, use_container_width=True, config={"displaylogo": False, "scrollZoom": True})

    positive_count = int(np.count_nonzero(positive))
    zero_count = int(np.count_nonzero(np.isfinite(mean_grid) & (mean_grid == 0)))
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Mesh dimensions", f"{dims[0]} × {dims[1]}")
    m2.metric("Positive-mean bins", f"{positive_count:,}")
    m3.metric("Zero-mean bins", f"{zero_count:,}")
    finite_rel = rel_grid[np.isfinite(rel_grid)]
    m4.metric("Median relative SD", f"{np.median(finite_rel):.4g}%" if finite_rel.size else "N/A")
    st.caption("Relative SD = tally standard deviation / tally mean for positive-mean bins. Zero bins are not assigned to a material or reflector without a verified geometry mapping.")
    with st.expander("Statepoint metadata and tally audit"):
        st.json({
            "statepoint_sha256": statepoint_hash,
            "sha256_matches_recorded_baseline": hash_matches,
            "keff": statepoint["keff"],
            "settings": statepoint["settings"],
            "tally_name": mesh_tally["tally_name"],
            "mesh_name": mesh_tally["mesh_name"],
            "mesh_dimensions": dims,
            "scores": mesh_tally["scores"],
            "mean_array_shape": list(mesh_tally["mean"].shape),
            "std_dev_array_shape": list(mesh_tally["std_dev"].shape),
        })
    st.download_button(
        "Export selected mesh tally CSV",
        pd.DataFrame({
            "mesh_x_bin": np.tile(np.arange(dims[0]), dims[1]),
            "mesh_y_bin": np.repeat(np.arange(dims[1]), dims[0]),
            "score": score_name,
            "mean": mean_values,
            "std_dev": sd_values,
            "relative_sd_percent": rel_grid.reshape(-1),
        }).to_csv(index=False).encode("utf-8"),
        file_name=f"cbpfr_mesh_{score_name.replace('-', '_')}.csv",
        mime="text/csv",
    )
except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
    st.error(f"Could not read the OpenMC mesh tally: {exc}")
    st.caption("The app does not synthesize missing spatial data. Verify that the file is a compatible OpenMC statepoint and includes a 2-D mesh tally.")


st.markdown("### Spatial-field readiness")
g1, g2, g3 = st.columns(3)
g1.markdown('<div class="scientific-panel"><div class="scientific-panel-title">Required source</div><p class="small-muted">Verified OpenMC statepoint and exact tally definition.</p></div>', unsafe_allow_html=True)
g2.markdown('<div class="scientific-panel"><div class="scientific-panel-title">Required metadata</div><p class="small-muted">Mesh/filter dimensions, score units, normalization basis, and uncertainty array.</p></div>', unsafe_allow_html=True)
g3.markdown('<div class="scientific-panel"><div class="scientific-panel-title">Required provenance</div><p class="small-muted">Source hash, settings, run identity, and validation record.</p></div>', unsafe_allow_html=True)
