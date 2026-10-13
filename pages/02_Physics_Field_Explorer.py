"""Scientific field workbench for audited OpenMC mesh tally evidence."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import zipfile

import h5py
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from cbpfr.dashboard_ui import (
    CYAN, MUTED, ORANGE, PANEL, apply_workstation_style, base_layout,
    candidate_label, layout_figure, load_smoke, render_header,
    render_page_intro, render_workspace_sidebar,
)
from cbpfr.sciviz import (
    axis_centers, distribution_figure, field_figure, profile_figure,
    uncertainty_figure, vtk_plane_html,
)

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
    """Read mesh tallies only when their HDF5 mesh-filter association is explicit."""
    with h5py.File(io.BytesIO(data), "r") as handle:
        if "tallies" not in handle:
            raise ValueError("The HDF5 file has no OpenMC tallies group.")
        tallies = handle["tallies"]
        mesh_by_id = {}

        if "meshes" in tallies:
            for name, mesh in tallies["meshes"].items():
                if "dimension" not in mesh:
                    continue
                dims = [int(v) for v in np.asarray(mesh["dimension"][()]).reshape(-1)]
                if len(dims) != 3:
                    continue

                mesh_id = None
                if "id" in mesh.attrs:
                    try:
                        mesh_id = int(mesh.attrs["id"])
                    except (TypeError, ValueError):
                        pass
                if mesh_id is None and "id" in mesh:
                    try:
                        mesh_id = int(np.asarray(mesh["id"][()]).item())
                    except (TypeError, ValueError):
                        pass
                if mesh_id is None:
                    try:
                        mesh_id = int(name.rsplit(" ", 1)[-1])
                    except (ValueError, IndexError):
                        continue

                metadata = {"id": mesh_id, "name": name, "dimensions": dims}
                for attr in ("lower_left", "upper_right", "width"):
                    if attr in mesh:
                        try:
                            metadata[attr] = np.asarray(mesh[attr][()], dtype=float).reshape(-1).tolist()
                        except (TypeError, ValueError):
                            pass
                mesh_by_id[mesh_id] = metadata

        # A mesh-shaped array by itself is not enough to identify the physical
        # mesh. Resolve the tally's filter IDs to the mesh filter's declared ID.
        filter_groups = tallies.get("filters")
        filter_to_mesh_id = {}
        if filter_groups is not None:
            for filter_name, filter_group in filter_groups.items():
                if not filter_name.startswith("filter ") or not hasattr(filter_group, "keys"):
                    continue
                if "type" not in filter_group or "bins" not in filter_group:
                    continue
                filter_type = _decode_h5_text(filter_group["type"][()])
                if filter_type != "mesh":
                    continue
                bins = np.asarray(filter_group["bins"][()]).reshape(-1)
                if bins.size != 1:
                    continue
                try:
                    filter_to_mesh_id[int(filter_name.rsplit(" ", 1)[-1])] = int(bins[0])
                except (ValueError, IndexError, TypeError):
                    continue

        records = []
        for name, tally in tallies.items():
            if not name.startswith("tally ") or not hasattr(tally, "keys"):
                continue
            if "results" not in tally or "score_bins" not in tally or "filters" not in tally:
                continue

            tally_filter_ids = [
                int(value) for value in np.asarray(tally["filters"][()]).reshape(-1)
            ]
            associated_mesh_ids = {
                filter_to_mesh_id[filter_id]
                for filter_id in tally_filter_ids
                if filter_id in filter_to_mesh_id
            }
            # A unique mesh-filter link is mandatory; do not infer a mesh by
            # matching only the number of bins.
            if len(associated_mesh_ids) != 1:
                continue
            mesh_id = next(iter(associated_mesh_ids))
            matching_mesh = mesh_by_id.get(mesh_id)
            if matching_mesh is None:
                continue

            scores = [
                _decode_h5_text(value)
                for value in np.asarray(tally["score_bins"][()]).reshape(-1)
            ]
            raw = np.asarray(tally["results"][()])
            if raw.ndim == 4 and raw.shape[1] == 1:
                raw = raw[:, 0, :, :]
            if raw.ndim != 3 or raw.shape[-1] != 2 or raw.shape[-2] != len(scores):
                continue

            n_bins = raw.shape[0]
            dims = matching_mesh["dimensions"]
            if int(np.prod(dims)) != n_bins or dims[2] != 1 or dims[0] * dims[1] != n_bins:
                continue

            records.append({
                "tally_name": name,
                "mesh_name": matching_mesh["name"],
                "mesh_id": mesh_id,
                "mesh_metadata": matching_mesh,
                "dimensions": dims,
                "scores": scores,
                "mean": np.asarray(raw[:, :, 0], dtype=float),
                "std_dev": np.asarray(raw[:, :, 1], dtype=float),
            })

        if not records:
            raise ValueError(
                "No 2-D mesh tally could be linked to a declared OpenMC mesh filter. "
                "The reader will not guess a mesh from dimensions alone."
            )

        keff = None
        if "k_combined" in handle:
            values = np.asarray(handle["k_combined"][()]).reshape(-1)
            if values.size >= 2:
                keff = {"mean": float(values[0]), "std_dev": float(values[1])}
        settings = {}
        for key in (
            "n_batches", "n_inactive", "n_particles", "n_realizations",
            "run_mode", "energy_mode",
        ):
            if key in handle:
                value = handle[key][()]
                settings[key] = (
                    _decode_h5_text(value)
                    if key in ("run_mode", "energy_mode")
                    else int(np.asarray(value).item())
                )
        return {"mesh_tallies": records, "keff": keff, "settings": settings}


def _load_bundled_statepoint():
    """Load the production statepoint from the committed evidence ZIP."""
    if not STATEPOINT_ARCHIVE.is_file():
        raise FileNotFoundError(f"Evidence archive not found: {STATEPOINT_ARCHIVE.name}")
    with zipfile.ZipFile(STATEPOINT_ARCHIVE) as archive:
        matches = [name for name in archive.namelist() if name == PRODUCTION_MEMBER]
        if len(matches) != 1:
            raise ValueError(f"Expected one {PRODUCTION_MEMBER} entry, found {len(matches)}.")
        data = archive.read(matches[0])
    expected_hash = None
    if STATEPOINT_BASELINE.is_file():
        baseline = json.loads(STATEPOINT_BASELINE.read_text(encoding="utf-8"))
        expected_hash = baseline.get("statepoint_file_sha256")
    return data, hashlib.sha256(data).hexdigest(), expected_hash


@st.cache_data(show_spinner=False)
def _cached_vtk_plane(values, x_bounds, y_bounds, score_name):
    """Cache the exported browser scene so control changes do not rebuild VTK."""
    return vtk_plane_html(np.asarray(values, dtype=float), x_bounds, y_bounds, score_name)


st.set_page_config(page_title="CB-PFR · Scientific Field Explorer", page_icon="⚛", layout="wide")
apply_workstation_style()
df = load_smoke().sort_values("candidate_id").reset_index(drop=True)
render_header("Scientific visualization", "OPENMC MESH TALLY · EVIDENCE-AWARE")
render_workspace_sidebar("Physics Fields", df)
render_page_intro(
    "SCIENTIFIC VISUALIZATION / C5G7 TRANSPORT EVIDENCE",
    "Physics Field Explorer",
    "Linked spatial field, contour levels, row profile, uncertainty map, and an interactive VTK rendering of the archived two-dimensional mesh tally.",
)

st.markdown(
    '<div class="evidence-note"><b>Data boundary</b> · Spatial maps below come from the archived production OpenMC statepoint, not from a candidate-specific field solution. The existing candidate CSV contains aggregate scores; the 51 × 51 mesh is displayed with its recorded mesh coordinates when available. This is not yet a validated physical ranking or a three-dimensional core-volume solution.</div>',
    unsafe_allow_html=True,
)

candidate_tab, field_tab, provenance_tab = st.tabs(
    ["Candidate comparison", "Spatial field workbench", "Statepoint & provenance"]
)

with candidate_tab:
    st.markdown("### Recorded candidate comparison")
    left, right = st.columns([0.92, 1.55], gap="large")
    with left:
        selected_id = st.selectbox(
            "Inspect candidate layout",
            df["candidate_id"].tolist(),
            format_func=lambda value: candidate_label(df.loc[df["candidate_id"] == value].iloc[0]),
        )
        selected = df.loc[df["candidate_id"] == selected_id].iloc[0]
        st.plotly_chart(
            layout_figure(str(selected["layout_signature"]), height=360),
            use_container_width=True,
            config={"displaylogo": False},
        )
        st.caption("Categorical 2 × 2 layout schematic. It is not a pin-resolved geometry or a field-to-candidate mapping.")
        k1, k2 = st.columns(2)
        k1.metric("k-effective mean", f"{selected['keff_mean']:.6f}")
        k2.metric("Reported tally SD", f"{selected['keff_std_dev']:.6g}")
        st.caption(f"Seed {int(selected['seed'])} · layout {selected['layout_signature']}")
    with right:
        metric_options = {
            "k-effective mean": ("keff_mean", "keff_std_dev", "Reported k-effective mean"),
            "Aggregate flux score": ("aggregate_flux_score", None, "Aggregate flux score (units not specified)"),
            "Aggregate fission score": ("aggregate_fission_score", None, "Aggregate fission score (units not specified)"),
            "Relative k-effective SD": ("keff_relative_sd_percent", None, "Reported relative SD (%)"),
        }
        metric_label = st.selectbox("Comparison quantity", list(metric_options))
        metric, error_column, axis_label = metric_options[metric_label]
        chart_df = df.dropna(subset=[metric]).sort_values(metric).reset_index(drop=True)
        colors = [CYAN if value == selected_id else "#36536e" for value in chart_df["candidate_id"]]
        fig = go.Figure(go.Bar(
            x=[candidate_label(row) for _, row in chart_df.iterrows()],
            y=chart_df[metric],
            marker={"color": colors, "line": {"color": "#263f52", "width": 0.5}},
            error_y=(
                {"type": "data", "array": chart_df[error_column], "visible": True,
                 "color": MUTED, "thickness": 1.2, "width": 3}
                if error_column else None
            ),
            customdata=chart_df[["candidate_id", "layout_signature", "seed"]].to_numpy(),
            hovertemplate=(
                "Candidate %{customdata[0]}<br>Layout %{customdata[1]}"
                "<br>Seed %{customdata[2]}<br>Value %{y:.7g}<extra></extra>"
            ),
        ))
        base_layout(fig, height=460)
        fig.update_layout(
            title={"text": axis_label, "x": 0.02},
            xaxis_title="Candidate / material signature",
            yaxis_title=axis_label,
            showlegend=False,
            margin={"l": 65, "r": 25, "t": 55, "b": 90},
        )
        fig.update_xaxes(tickangle=-28)
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
        st.caption("Error bars appear only for k-effective and show the reported within-run standard deviation, not a confidence interval.")

    with st.expander("Candidate records"):
        show_columns = [
            "candidate_id", "layout_signature", "canonical_reference", "seed",
            "keff_mean", "keff_std_dev", "keff_relative_sd_percent",
            "aggregate_flux_score", "aggregate_fission_score",
        ]
        st.dataframe(df[show_columns], use_container_width=True, hide_index=True)
        st.download_button(
            "Export candidate summary CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name="cbpfr_candidate_summary.csv",
            mime="text/csv",
        )

with field_tab:
    uploaded_statepoint = st.file_uploader(
        "Optional: inspect another OpenMC statepoint",
        type=["h5"],
        help="Leave empty to inspect the production statepoint included in the repository evidence archive.",
        key="field_statepoint_upload",
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
                st.warning("Statepoint loaded, but SHA-256 does not match the recorded baseline. Check provenance.")
        else:
            st.info("Uploaded statepoint loaded for inspection. Its identity is not associated with a candidate layout.")
        st.caption(f"{statepoint_origin} · SHA-256: {statepoint_hash}")

        mesh_tally = st.selectbox(
            "Mesh tally",
            statepoint["mesh_tallies"],
            format_func=lambda item: (
                f'{item["tally_name"]} · {item["dimensions"][0]} × {item["dimensions"][1]}'
            ),
            key="field_mesh_tally",
        )
        score_name = st.selectbox("Tally score", mesh_tally["scores"], key="field_score")
        score_index = mesh_tally["scores"].index(score_name)
        dims = mesh_tally["dimensions"]
        nx, ny = dims[0], dims[1]
        mean_values = mesh_tally["mean"][:, score_index]
        sd_values = mesh_tally["std_dev"][:, score_index]
        mean_grid = mean_values.reshape((ny, nx))
        sd_grid = sd_values.reshape((ny, nx))

        mesh_metadata = mesh_tally.get("mesh_metadata", {})
        lower_left = mesh_metadata.get("lower_left")
        upper_right = mesh_metadata.get("upper_right")
        x_bounds = (
            (float(lower_left[0]), float(upper_right[0]))
            if lower_left and upper_right and len(lower_left) >= 2 and len(upper_right) >= 2
            else None
        )
        y_bounds = (
            (float(lower_left[1]), float(upper_right[1]))
            if lower_left and upper_right and len(lower_left) >= 2 and len(upper_right) >= 2
            else None
        )
        x, x_axis_base = axis_centers(x_bounds, nx)
        y, y_axis_base = axis_centers(y_bounds, ny)
        x_label = "x-position (cm)" if x_bounds else "x-bin index"
        y_label = "y-position (cm)" if y_bounds else "y-bin index"

        control_a, control_b, control_c = st.columns([1.2, 1, 1])
        with control_a:
            profile_row = st.slider(
                "Profile row (j index)",
                min_value=0,
                max_value=ny - 1,
                value=ny // 2,
                help="This shared selection highlights the same row on the field map and drives the profile chart.",
            )
        with control_b:
            scale_choice = st.radio(
                "Field color scale",
                ["Logarithmic", "Linear"],
                horizontal=True,
                help="Logarithmic coloring is defined only for positive tally means; hover values remain untransformed.",
            )
        with control_c:
            st.metric("Selected row y", f"{y[profile_row]:.4g}")
            st.caption("Coordinates are physical model positions only when the statepoint stores bounds.")

        positive = np.isfinite(mean_grid) & (mean_grid > 0)
        valid_sd = np.isfinite(sd_grid) & (sd_grid >= 0)
        relative_sd = np.full(mean_grid.shape, np.nan, dtype=float)
        use_relative = positive & valid_sd
        relative_sd[use_relative] = 100.0 * sd_grid[use_relative] / mean_grid[use_relative]
        finite_means = mean_grid[np.isfinite(mean_grid)]
        finite_relative = relative_sd[np.isfinite(relative_sd)]

        f1, f2, f3, f4 = st.columns(4)
        f1.metric("Mesh dimensions", f"{nx} × {ny}")
        f2.metric("Positive-mean bins", f"{int(positive.sum()):,}")
        f3.metric("Zero-mean bins", f"{int((np.isfinite(mean_grid) & (mean_grid == 0)).sum()):,}")
        f4.metric(
            "Median relative tally SD",
            f"{np.median(finite_relative):.4g}%" if finite_relative.size else "N/A",
        )

        if x_bounds is None or y_bounds is None:
            st.warning("Physical mesh bounds were not found in this file. Axes are shown as mesh-bin indices; no assembly labels are inferred.")

        field_col, uncertainty_col = st.columns([1.55, 1], gap="large")
        with field_col:
            field_fig = field_figure(
                mean_grid, x, y, score_name, profile_row,
                log_color=(scale_choice == "Logarithmic"),
                x_label=x_label, y_label=y_label,
            )
            st.plotly_chart(field_fig, use_container_width=True, config={"displaylogo": False}, key="scientific_field_contour")
        with uncertainty_col:
            uncertainty_fig = uncertainty_figure(
                relative_sd, x, y, score_name,
                x_label=x_label, y_label=y_label,
            )
            st.plotly_chart(uncertainty_fig, use_container_width=True, config={"displaylogo": False}, key="scientific_field_uncertainty")
            st.caption("Relative tally SD = standard deviation / mean for positive bins. It is not model-bias uncertainty.")

        profile_col, distribution_col = st.columns([1.35, 1], gap="large")
        with profile_col:
            st.plotly_chart(
                profile_figure(
                    x, mean_grid[profile_row, :], sd_grid[profile_row, :],
                    score_name, profile_row, x_label,
                ),
                use_container_width=True,
                config={"displaylogo": False},
                key="scientific_central_row_profile",
            )
            st.caption("The dashed row locator above and this profile use the same selected mesh row. Error bars are reported tally SD.")
        with distribution_col:
            st.plotly_chart(
                distribution_figure(mean_values, score_name),
                use_container_width=True,
                config={"displaylogo": False},
                key="scientific_field_distribution",
            )
            if finite_means.size:
                p95 = float(np.percentile(finite_means, 95))
                st.markdown(
                    f'<div class="small-muted">Mean {np.mean(finite_means):.5g} · median {np.median(finite_means):.5g} · '
                    f'95th percentile {p95:.5g} · maximum {np.max(finite_means):.5g}</div>',
                    unsafe_allow_html=True,
                )
            st.caption("This is a descriptive distribution across spatial bins, not a sample distribution for statistical inference.")

        with st.expander("Interactive 3D viewer · VTK / Trame", expanded=True):
            st.markdown(
                '<div class="panel-subtitle">Rotate and inspect the spatial mesh in a WebGL scene. Because this statepoint contains a 2-D mesh (51 × 51 × 1), this is a flat scalar-field plane—not a three-dimensional reactor core or volume rendering.</div>',
                unsafe_allow_html=True,
            )
            try:
                x_bound_key = tuple(x_bounds) if x_bounds else None
                y_bound_key = tuple(y_bounds) if y_bounds else None
                with st.spinner("Preparing interactive VTK field plane…"):
                    html_scene = _cached_vtk_plane(mean_grid, x_bound_key, y_bound_key, score_name)
                components.html(html_scene, height=625, scrolling=False)
            except (ImportError, RuntimeError, ValueError, OSError) as exc:
                st.error(f"The interactive VTK viewer could not be rendered: {exc}")
                st.caption("The 2-D Plotly field and contour views remain available. Check the PyVista/Trame dependencies and graphics runtime.")

        export_table = pd.DataFrame({
            "mesh_x": np.tile(x, ny),
            "mesh_y": np.repeat(y, nx),
            "score": score_name,
            "mean": mean_grid.reshape(-1, order="C"),
            "std_dev": sd_grid.reshape(-1, order="C"),
            "relative_sd_percent": relative_sd.reshape(-1, order="C"),
        })
        st.download_button(
            "Export current spatial field CSV",
            export_table.to_csv(index=False).encode("utf-8"),
            file_name=f"cbpfr_mesh_{score_name.replace('-', '_')}.csv",
            mime="text/csv",
        )

        with st.expander("Mesh definition and numerical provenance"):
            st.json({
                "statepoint_origin": statepoint_origin,
                "statepoint_sha256": statepoint_hash,
                "sha256_matches_recorded_baseline": hash_matches,
                "keff": statepoint["keff"],
                "settings": statepoint["settings"],
                "tally_name": mesh_tally["tally_name"],
                "mesh_name": mesh_tally["mesh_name"],
                "mesh_metadata": mesh_metadata,
                "mesh_dimensions": dims,
                "score_names": mesh_tally["scores"],
                "selected_score": score_name,
                "mean_array_shape": list(mesh_tally["mean"].shape),
                "std_dev_array_shape": list(mesh_tally["std_dev"].shape),
                "profile_row_index": profile_row,
                "profile_row_coordinate": float(y[profile_row]),
                "color_scale": scale_choice,
                "physical_validation": "not established by visualization alone",
            })
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        st.error(f"Could not read the OpenMC mesh tally: {exc}")
        st.caption("No missing spatial values are synthesized. Verify that the file is a compatible OpenMC statepoint containing a 2-D mesh tally.")

with provenance_tab:
    st.markdown("### Current evidence boundary")
    evidence = pd.DataFrame([
        ("Candidate summary CSV", "Available", "Recorded per-layout scalar/aggregate values"),
        ("Archived statepoint", "Available in repository", "Recorded scalar and mesh tally extraction"),
        ("Spatial mesh bounds", "Read when present", "Physical coordinates only when bounds exist"),
        ("Candidate-to-spatial-field association", "Not established", "The production mesh is not automatically assigned to each candidate"),
        ("3-D core volume", "Not provided by this 2-D tally", "Requires a spatially resolved 3-D dataset and verified geometry"),
        ("Independent-run reliability", "Not established by one-seed snapshot", "Requires matched, independent repeated runs"),
        ("Benchmark physical validation", "Not established", "Requires source-backed model correspondence and predeclared acceptance criteria"),
    ], columns=["Evidence item", "Current status", "Interpretation"])
    st.dataframe(evidence, use_container_width=True, hide_index=True)
    st.markdown("### Provenance record")
    hash_equal = (
        df["mgxs_sha256_before_transport"].astype(str)
        == df["mgxs_sha256_after_transport"].astype(str)
    )
    st.metric("Within-run MGXS hashes matched", f"{int(hash_equal.sum())}/{len(df)}")
    st.caption("Matching source hashes support input-integrity consistency. They do not establish nuclear benchmark validity, correct spatial mapping, or physical optimality.")
    st.download_button(
        "Export validation evidence table",
        evidence.to_csv(index=False).encode("utf-8"),
        file_name="cbpfr_visualization_evidence_boundary.csv",
        mime="text/csv",
    )

st.caption("CB-PFR · Scientific workstation · Statepoint-backed exploratory visualization · Not a validated reactor design or safety analysis.")
