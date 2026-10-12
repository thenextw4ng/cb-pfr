"""PyVista/VTK 3-D viewer for recorded OpenMC mesh tallies only."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import h5py
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

from cbpfr.dashboard_ui import (
    CYAN, MUTED, apply_workstation_style, render_header,
    render_page_intro, render_workspace_sidebar, load_smoke,
)

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "OpenMC_HDF5_Evidence_2026-10-11.zip"
MEMBER = "c5g7-run/2d/statepoint.20000.h5"


def _text(v):
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="replace").rstrip("\\x00")
    if hasattr(v, "item"):
        try:
            return _text(v.item())
        except (ValueError, TypeError):
            pass
    return str(v)


def _read_3d_mesh_tallies(payload: bytes):
    """Return 3-D mesh tallies only when dimensions and result bins agree."""
    found = []
    with h5py.File(io.BytesIO(payload), "r") as h5:
        tallies = h5.get("tallies")
        if tallies is None or "meshes" not in tallies:
            return found
        meshes = []
        for mesh_name, mesh in tallies["meshes"].items():
            if "dimension" not in mesh:
                continue
            dims = [int(v) for v in np.asarray(mesh["dimension"][()]).reshape(-1)]
            if len(dims) == 3 and all(v > 1 for v in dims):
                meshes.append((mesh_name, dims))
        for tally_name, tally in tallies.items():
            if not tally_name.startswith("tally ") or "results" not in tally or "score_bins" not in tally:
                continue
            scores = [_text(v) for v in np.asarray(tally["score_bins"][()]).reshape(-1)]
            raw = np.asarray(tally["results"][()])
            if raw.ndim == 4 and raw.shape[1] == 1:
                raw = raw[:, 0, :, :]
            if raw.ndim != 3 or raw.shape[-1] != 2 or raw.shape[-2] != len(scores):
                continue
            n_bins = raw.shape[0]
            match = next((m for m in meshes if int(np.prod(m[1])) == n_bins), None)
            if match is None:
                continue
            found.append({
                "name": tally_name, "mesh": match[0], "dims": match[1],
                "scores": scores, "mean": raw[:, :, 0], "sd": raw[:, :, 1],
            })
    return found


st.set_page_config(page_title="CB-PFR · 3D Mesh Viewer", page_icon="⚛", layout="wide")
apply_workstation_style()
df = load_smoke()
render_workspace_sidebar("3D Mesh Viewer", df)
render_header("3D Mesh Viewer", "PYVISTA / VTK · SOURCE-DRIVEN SPATIAL VIEW")
render_page_intro(
    "SPATIAL VISUALIZATION / 3D",
    "3D Mesh Viewer",
    "Interactive volumetric inspection of OpenMC mesh tally values using PyVista/VTK. Only real 3-D mesh tally data are eligible; the viewer will not extrude a 2-D map or invent reactor geometry.",
)

st.markdown(
    '<div class="evidence-note"><b>Geometry gate</b> · Mesh dimensions, tally-bin count, score bins, and the source statepoint must agree. Mesh coordinates are shown in bin-index space unless verified physical bounds are present in the source.</div>',
    unsafe_allow_html=True,
)
uploaded = st.file_uploader("OpenMC statepoint (.h5)", type=["h5"], key="3d_statepoint")
if uploaded is not None:
    payload = uploaded.getvalue()
    source = f"Uploaded statepoint: {uploaded.name}"
elif ARCHIVE.is_file():
    try:
        with zipfile.ZipFile(ARCHIVE) as zf:
            if MEMBER not in zf.namelist():
                raise ValueError(f"Missing expected archive member: {MEMBER}")
            payload = zf.read(MEMBER)
        source = f"Repository archive · {MEMBER}"
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        st.error(f"Could not open statepoint archive: {exc}")
        st.stop()
else:
    st.warning("No archived statepoint found. Upload a real OpenMC .h5 statepoint to inspect 3-D tallies.")
    st.stop()

try:
    meshes = _read_3d_mesh_tallies(payload)
except (OSError, ValueError, KeyError) as exc:
    st.error(f"Statepoint tally parsing failed: {exc}")
    st.stop()

if not meshes:
    st.warning("No compatible 3-D mesh tally was detected in this statepoint.")
    st.info("The currently archived production statepoint is documented as a 51 × 51 2-D mesh. It remains viewable in Physics Fields; it is not converted into fake 3-D geometry. Upload a statepoint containing a genuine 3-D regular-mesh tally to enable this viewer.")
    st.page_link("pages/02_Physics_Field_Explorer.py", label="Open 2D Physics Field Explorer", use_container_width=True)
    st.stop()

mesh = st.selectbox("Mesh tally", meshes, format_func=lambda x: f'{x["name"]} · {x["dims"][0]}×{x["dims"][1]}×{x["dims"][2]}')
score = st.selectbox("Tally score", mesh["scores"])
mode = st.radio("Field", ["Mean", "Relative SD (%)"], horizontal=True)
import pyvista as pv

dims = mesh["dims"]
idx = mesh["scores"].index(score)
mean = np.asarray(mesh["mean"][:, idx], dtype=float)
sd = np.asarray(mesh["sd"][:, idx], dtype=float)
if mode == "Relative SD (%)":
    values = np.divide(100 * sd, mean, out=np.full_like(mean, np.nan), where=np.isfinite(mean) & (mean > 0))
    scalar_name = "relative_sd_percent"
else:
    values = mean
    scalar_name = "tally_mean"
if values.size != int(np.prod(dims)):
    st.error("Tally result length does not match the selected mesh dimensions; visualization blocked.")
    st.stop()

# Coordinates deliberately use mesh-bin indices, not unverified physical coordinates.
grid = pv.ImageData(dimensions=(dims[0] + 1, dims[1] + 1, dims[2] + 1), spacing=(1, 1, 1), origin=(0, 0, 0))
cell_values = values.reshape((dims[2], dims[1], dims[0])).ravel(order="C")
grid.cell_data[scalar_name] = cell_values
finite = values[np.isfinite(values)]
if finite.size == 0:
    st.error("The selected field contains no finite values.")
    st.stop()

low, high = float(np.nanmin(finite)), float(np.nanmax(finite))
if low == high:
    st.caption(f"Constant field: {low:.6g}")
threshold = st.slider("Display lower percentile", 0, 90, 0, 5, help="Filters low-valued cells for visibility; does not modify source data.")
cutoff = float(np.nanpercentile(finite, threshold))
display = grid.threshold(value=cutoff, scalars=scalar_name) if threshold > 0 else grid
plotter = pv.Plotter(off_screen=True, window_size=(1200, 760))
plotter.set_background("#07111b")
plotter.add_mesh(display, scalars=scalar_name, cmap="viridis", show_edges=False, scalar_bar_args={"title": scalar_name.replace("_", " ")})
plotter.add_axes(line_width=2, color="white")
plotter.view_isometric()
html = plotter.export_html(None, backend="static")
plotter.close()
components.html(html, height=700, scrolling=False)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Mesh dimensions", " × ".join(map(str, dims)))
m2.metric("Cell bins", f"{int(np.prod(dims)):,}")
m3.metric("Finite cells", f"{int(finite.size):,}")
m4.metric("Field range", f"{low:.4g} – {high:.4g}")
st.caption(f"Source: {source}. The view uses mesh-index coordinates unless physical mesh bounds are verified. This visualization is not a material/assembly reconstruction.")
st.download_button("Export displayed field as CSV", data=__import__("pandas").DataFrame({
    "mesh_x_bin": np.tile(np.arange(dims[0]), dims[1] * dims[2]),
    "mesh_y_bin": np.tile(np.repeat(np.arange(dims[1]), dims[0]), dims[2]),
    "mesh_z_bin": np.repeat(np.arange(dims[2]), dims[0] * dims[1]),
    "score": score, scalar_name: values,
}).to_csv(index=False).encode("utf-8"), file_name="cbpfr_3d_mesh_field.csv", mime="text/csv")
with st.expander("Source and field audit"):
    st.json({"source": source, "mesh_name": mesh["mesh"], "tally_name": mesh["name"], "dimensions": dims, "score": score, "field": mode, "coordinate_basis": "mesh-bin indices; physical bounds not inferred"})
