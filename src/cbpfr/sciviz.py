"""Reusable scientific field visualizations for CB-PFR.

The 2-D mesh tally remains the authoritative spatial source. The VTK view is a
rotatable rendering of that plane, not an inferred 3-D reactor volume.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
import plotly.graph_objects as go

from cbpfr.dashboard_ui import CYAN, LINE, MUTED, PANEL, TEXT, base_layout


def axis_centers(bounds: Sequence[float] | None, count: int) -> tuple[np.ndarray, str]:
    """Return mesh-cell centers and an honest axis label.

    bounds must be (lower, upper) in OpenMC model coordinates (cm). If absent,
    return bin indices rather than pretending physical coordinates are known.
    """
    if bounds is not None and len(bounds) == 2:
        lower, upper = float(bounds[0]), float(bounds[1])
        if np.isfinite(lower) and np.isfinite(upper) and upper > lower:
            width = (upper - lower) / count
            return lower + (np.arange(count, dtype=float) + 0.5) * width, "Position (cm)"
    return np.arange(count, dtype=float), "Mesh-bin index"


def _finite_range(values: np.ndarray) -> tuple[float, float]:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return 0.0, 1.0
    low, high = float(np.min(finite)), float(np.max(finite))
    if high <= low:
        high = low + max(abs(low) * 1e-6, 1e-12)
    return low, high


def field_figure(
    mean_grid: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    score_name: str,
    selected_row: int,
    log_color: bool = True,
    x_label: str = "x-coordinate / bin",
    y_label: str = "y-coordinate / bin",
) -> go.Figure:
    """Heatmap with contour lines and a row locator linked to the profile plot."""
    z = np.asarray(mean_grid, dtype=float)
    positive = np.isfinite(z) & (z > 0)
    if log_color and positive.any():
        color_values = np.full(z.shape, np.nan, dtype=float)
        color_values[positive] = np.log10(z[positive])
        color_label = "log₁₀(mean)"
    else:
        color_values = z
        color_label = "Mean score"
    zmin, zmax = _finite_range(color_values)
    custom = z.copy()

    fig = go.Figure(
        go.Heatmap(
            x=x,
            y=y,
            z=color_values,
            customdata=custom,
            colorscale="Viridis",
            zmin=zmin,
            zmax=zmax,
            colorbar={"title": {"text": color_label}, "thickness": 15, "len": 0.82},
            hovertemplate=(
                "x = %{x:.5g}<br>y = %{y:.5g}<br>"
                "Mean score = %{customdata:.6g}<extra></extra>"
            ),
            connectgaps=False,
            name="Mesh mean",
        )
    )

    finite = z[np.isfinite(z)]
    if finite.size > 1 and float(np.max(finite)) > float(np.min(finite)):
        low, high = _finite_range(finite)
        step = (high - low) / 7.0
        if step > 0:
            fig.add_trace(
                go.Contour(
                    x=x,
                    y=y,
                    z=z,
                    contours={
                        "start": low + step,
                        "end": high,
                        "size": step,
                        "coloring": "none",
                        "showlabels": True,
                        "labelfont": {"color": TEXT, "size": 9},
                    },
                    line={"color": "rgba(245,248,252,0.88)", "width": 1},
                    showscale=False,
                    hoverinfo="skip",
                    name="Contour levels",
                )
            )

    row_index = max(0, min(int(selected_row), len(y) - 1))
    fig.add_trace(
        go.Scatter(
            x=[float(np.min(x)), float(np.max(x))],
            y=[float(y[row_index]), float(y[row_index])],
            mode="lines",
            line={"color": "#f5bb62", "width": 2, "dash": "dash"},
            name=f"Profile row {row_index}",
            hovertemplate=f"Selected profile row {row_index}<extra></extra>",
        )
    )
    base_layout(fig, height=600)
    fig.update_layout(
        title={"text": f"{score_name} · spatial field with contour overlay", "x": 0.02},
        xaxis_title=x_label,
        yaxis_title=y_label,
        margin={"l": 60, "r": 25, "t": 55, "b": 55},
        hovermode="closest",
        yaxis={"gridcolor": LINE, "linecolor": LINE, "scaleanchor": "x", "scaleratio": 1},
        paper_bgcolor=PANEL,
    )
    return fig


def profile_figure(
    x: np.ndarray,
    mean_values: np.ndarray,
    sd_values: np.ndarray,
    score_name: str,
    row_index: int,
    x_label: str,
) -> go.Figure:
    """Selected row profile with the reported tally SD, not a CI."""
    mean = np.asarray(mean_values, dtype=float)
    sd = np.asarray(sd_values, dtype=float)
    fig = go.Figure(
        go.Scatter(
            x=x,
            y=mean,
            mode="lines+markers",
            line={"color": CYAN, "width": 2.2},
            marker={"size": 5, "color": CYAN, "line": {"color": PANEL, "width": 1}},
            error_y={
                "type": "data",
                "array": np.where(np.isfinite(sd), sd, 0.0),
                "visible": True,
                "color": MUTED,
                "thickness": 1,
                "width": 2,
            },
            customdata=sd,
            hovertemplate=(
                f"{x_label}: %{{x:.5g}}<br>Mean: %{{y:.6g}}"
                "<br>Reported tally SD: %{customdata:.4g}<extra></extra>"
            ),
            name="Selected-row mean",
        )
    )
    base_layout(fig, height=360)
    fig.update_layout(
        title={"text": f"Selected-row profile · row {row_index}", "x": 0.02},
        xaxis_title=x_label,
        yaxis_title=f"{score_name} mean (score units as stored)",
        margin={"l": 65, "r": 25, "t": 55, "b": 55},
    )
    return fig


def uncertainty_figure(
    relative_sd_grid: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    score_name: str,
    x_label: str = "x-coordinate / bin",
    y_label: str = "y-coordinate / bin",
) -> go.Figure:
    """Spatial map of relative tally SD for positive-mean bins."""
    values = np.asarray(relative_sd_grid, dtype=float)
    finite = values[np.isfinite(values)]
    max_value = float(np.max(finite)) if finite.size else 1.0
    if max_value <= 0:
        max_value = 1.0
    fig = go.Figure(
        go.Heatmap(
            x=x,
            y=y,
            z=values,
            colorscale="Magma",
            zmin=0,
            zmax=max_value,
            colorbar={"title": {"text": "Relative SD (%)"}, "thickness": 13},
            hovertemplate=(
                "x = %{x:.5g}<br>y = %{y:.5g}"
                "<br>Relative tally SD = %{z:.4g}%<extra></extra>"
            ),
            connectgaps=False,
        )
    )
    base_layout(fig, height=500)
    fig.update_layout(
        title={"text": f"{score_name} · relative Monte Carlo uncertainty", "x": 0.02},
        xaxis_title=x_label,
        yaxis_title=y_label,
        margin={"l": 60, "r": 25, "t": 55, "b": 55},
        yaxis={"gridcolor": LINE, "linecolor": LINE, "scaleanchor": "x", "scaleratio": 1},
    )
    return fig


def distribution_figure(values: np.ndarray, score_name: str) -> go.Figure:
    """Histogram of spatial bin values; explicitly descriptive, not inferential."""
    data = np.asarray(values, dtype=float)
    data = data[np.isfinite(data)]
    fig = go.Figure(
        go.Histogram(
            x=data,
            nbinsx=48,
            marker={"color": CYAN, "line": {"color": PANEL, "width": 0.6}},
            hovertemplate="Bin count = %{y}<br>Mean value range: %{x}<extra></extra>",
            name="Mesh-bin distribution",
        )
    )
    base_layout(fig, height=320)
    fig.update_layout(
        title={"text": "Spatial-bin value distribution", "x": 0.02},
        xaxis_title=f"{score_name} mean",
        yaxis_title="Number of mesh bins",
        bargap=0.04,
        margin={"l": 60, "r": 25, "t": 50, "b": 55},
    )
    return fig


def vtk_plane_html(
    mean_grid: np.ndarray,
    x_bounds: Sequence[float] | None,
    y_bounds: Sequence[float] | None,
    score_name: str,
) -> str:
    """Export the 2-D mesh plane as an interactive client-side VTK/Trame scene."""
    import pyvista as pv

    values = np.asarray(mean_grid, dtype=float)
    ny, nx = values.shape
    x0, x1 = (float(x_bounds[0]), float(x_bounds[1])) if x_bounds else (0.0, float(nx))
    y0, y1 = (float(y_bounds[0]), float(y_bounds[1])) if y_bounds else (0.0, float(ny))
    if x1 <= x0 or y1 <= y0:
        raise ValueError("Mesh bounds must be increasing.")

    grid = pv.ImageData(
        dimensions=(nx + 1, ny + 1, 1),
        origin=(x0, y0, 0.0),
        spacing=((x1 - x0) / nx, (y1 - y0) / ny, 1.0),
    )
    if grid.n_cells != values.size:
        raise ValueError(
            f"VTK plane cell count {grid.n_cells} does not match tally bins {values.size}."
        )
    if not np.isfinite(values).all():
        raise ValueError("The mesh contains non-finite values; missing bins are not silently replaced with zero.")
    grid.cell_data[score_name] = values.ravel(order="C")

    plotter = pv.Plotter(off_screen=True, window_size=(1050, 620))
    try:
        plotter.set_background("#07111b", top="#132a38")
        plotter.add_mesh(
            grid,
            scalars=score_name,
            cmap="viridis",
            show_edges=False,
            scalar_bar_args={
                "title": score_name,
                "color": "#e8f1f7",
                "title_font_size": 12,
                "label_font_size": 10,
            },
        )
        plotter.add_axes(line_width=2)
        plotter.show_grid(
            color="#8da4b7",
            xtitle="x (cm)" if x_bounds else "x-bin",
            ytitle="y (cm)" if y_bounds else "y-bin",
            ztitle="mesh plane",
        )
        plotter.view_isometric()
        exported = plotter.trame.export_html(None)
        if hasattr(exported, "getvalue"):
            html = exported.getvalue()
        else:
            html = str(exported)
        if not html or "<html" not in html.lower():
            raise RuntimeError("VTK/Trame did not return a complete HTML scene.")
        return html
    finally:
        plotter.close()
