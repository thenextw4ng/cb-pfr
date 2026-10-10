#!/usr/bin/env python3
"""Render index-space mesh tally maps from an OpenMC statepoint audit export."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-json", required=True, type=Path)
    parser.add_argument("--tally-csv", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    args = parser.parse_args()
    if args.outdir.exists() and any(args.outdir.iterdir()):
        parser.error(f"output directory is not empty: {args.outdir}")

    audit = json.loads(args.audit_json.read_text(encoding="utf-8"))
    mesh_tally = next(
        (tally for tally in audit.get("tallies", [])
         if any(filt.get("type") == "MeshFilter" for filt in tally.get("filters", []))),
        None,
    )
    if mesh_tally is None:
        parser.error("no mesh-filtered tally found in audit JSON")
    mesh_filter = next(filt for filt in mesh_tally["filters"] if filt.get("type") == "MeshFilter")
    dimensions = mesh_filter.get("mesh_dimension")
    if not dimensions or len(dimensions) != 3 or dimensions[2] != 1:
        parser.error(f"expected a 2-D mesh with singleton z dimension; got {dimensions}")

    with args.tally_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows = [row for row in rows if int(row["tally_index"]) == int(mesh_tally["index"])]
    scores = sorted({row["score_name_assuming_score_last"] for row in rows})
    expected_bins = int(dimensions[0]) * int(dimensions[1])
    args.outdir.mkdir(parents=True, exist_ok=True)
    plots = []

    for score in scores:
        selected = sorted(
            (row for row in rows if row["score_name_assuming_score_last"] == score),
            key=lambda row: int(row["flat_bin_index_assuming_score_last"]),
        )
        if len(selected) != expected_bins:
            parser.error(f"{score}: expected {expected_bins} mesh bins, got {len(selected)}")
        values = np.asarray([float(row["mean"]) for row in selected], dtype=float)
        sds = np.asarray([float(row["std_dev"]) for row in selected], dtype=float)
        # OpenMC's mesh filter bins in this statepoint enumerate x fastest, then y.
        # Axes remain mesh indices only; they are not labeled as assembly/material locations.
        image = values.reshape((int(dimensions[1]), int(dimensions[0])))
        fig, ax = plt.subplots(figsize=(8, 6), constrained_layout=True)
        if np.any(image > 0) and np.any(image == 0):
            shown = np.ma.masked_where(image <= 0, image)
            mesh = ax.imshow(shown, origin="lower", aspect="equal", norm=matplotlib.colors.LogNorm())
            ax.set_title(f"Mesh tally mean — {score} (positive bins, log scale)")
        elif np.all(image > 0):
            mesh = ax.imshow(image, origin="lower", aspect="equal", norm=matplotlib.colors.LogNorm())
            ax.set_title(f"Mesh tally mean — {score} (log scale)")
        else:
            mesh = ax.imshow(image, origin="lower", aspect="equal")
            ax.set_title(f"Mesh tally mean — {score}")
        ax.set_xlabel("Mesh x-bin index (not physical coordinates)")
        ax.set_ylabel("Mesh y-bin index (not physical coordinates)")
        fig.colorbar(mesh, ax=ax, label=f"{score} tally mean")
        filename = f"mesh_{score.replace('-', '_')}.png"
        fig.savefig(args.outdir / filename, dpi=180)
        plt.close(fig)
        plots.append({"file": filename, "score": score, "kind": "mesh_mean"})

        relative = np.full(values.shape, np.nan, dtype=float)
        positive = (values > 0) & np.isfinite(values) & np.isfinite(sds) & (sds >= 0)
        relative[positive] = sds[positive] / values[positive]
        rel_image = relative.reshape((int(dimensions[1]), int(dimensions[0])))
        if positive.any():
            fig, ax = plt.subplots(figsize=(8, 6), constrained_layout=True)
            shown = np.ma.masked_invalid(rel_image)
            mesh = ax.imshow(shown, origin="lower", aspect="equal", vmin=0)
            ax.set_xlabel("Mesh x-bin index (not physical coordinates)")
            ax.set_ylabel("Mesh y-bin index (not physical coordinates)")
            ax.set_title(f"Relative tally SD — {score} (positive-mean bins)")
            fig.colorbar(mesh, ax=ax, label="Standard deviation / mean")
            filename = f"mesh_{score.replace('-', '_')}_relative_sd.png"
            fig.savefig(args.outdir / filename, dpi=180)
            plt.close(fig)
            plots.append({"file": filename, "score": score, "kind": "relative_sd"})

    manifest = {
        "schema_version": "1.0",
        "statepoint_path": audit.get("statepoint_path"),
        "mesh_dimensions": dimensions,
        "axis_semantics": "mesh-bin indices only; no physical orientation/material identity asserted",
        "plots": plots,
        "limitations": [
            "Plots visualize tally scores and Monte Carlo relative standard deviations, not absolute power.",
            "Masked zero bins are not assigned to physical materials without a geometry mapping.",
        ],
    }
    (args.outdir / "plot_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"outdir": str(args.outdir), "plot_count": len(plots), "plots": plots}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
