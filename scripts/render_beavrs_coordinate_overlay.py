#!/usr/bin/env python3
"""Overlay BEAVRS assembly labels and instrumented locations on the OpenMC geometry plot."""
from __future__ import annotations

import argparse
import csv
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def render_overlay(run_dir: Path) -> Path:
    run_dir = run_dir.resolve()
    plot_path = run_dir / "radial_mats_midplane.png"
    crosswalk_path = run_dir / "beavrs_coordinate_crosswalk.csv"
    plots_path = run_dir / "plots.xml"
    for path in (plot_path, crosswalk_path, plots_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    plots = ET.parse(plots_path).getroot()
    plot = next(
        (item for item in plots.findall("plot") if item.get("filename") == "radial_mats_midplane"),
        None,
    )
    if plot is None:
        raise ValueError("plots.xml has no radial_mats_midplane plot")
    origin = [float(value) for value in plot.findtext("origin", "0 0 0").split()]
    width = [float(value) for value in plot.findtext("width", "").split()]
    pixels = [int(value) for value in plot.findtext("pixels", "").split()]
    if len(origin) < 2 or len(width) != 2 or len(pixels) != 2 or min(width) <= 0:
        raise ValueError("invalid radial_mats_midplane plot dimensions")

    with crosswalk_path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    labels = [row.get("assembly", "") for row in rows]
    instrumented = {
        row.get("assembly", "")
        for row in rows
        if row.get("is_instrumented_detector", "").strip().lower() == "true"
    }
    if len(rows) != 193 or len(set(labels)) != 193 or any(not label for label in labels):
        raise ValueError(f"expected 193 unique assembly labels, got {len(rows)} rows")
    if len(instrumented) != 58:
        raise ValueError(f"expected 58 instrumented locations, got {len(instrumented)}")

    image = Image.open(plot_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    image_width, image_height = image.size
    x_min = origin[0] - width[0] / 2.0
    y_max = origin[1] + width[1] / 2.0

    for row in rows:
        x = float(row["mesh_center_x_cm"])
        y = float(row["mesh_center_y_cm"])
        px = (x - x_min) / width[0] * image_width
        py = (y_max - y) / width[1] * image_height
        label = row["assembly"]
        box = draw.textbbox((0, 0), label, font=font)
        text_width, text_height = box[2] - box[0], box[3] - box[1]
        draw.rectangle(
            (px - text_width / 2 - 1, py - text_height / 2 - 1,
             px + text_width / 2 + 1, py + text_height / 2 + 1),
            fill="white",
        )
        draw.text((px - text_width / 2, py - text_height / 2), label, fill="black", font=font)
        if label in instrumented:
            draw.rectangle((px - 11, py - 9, px + 11, py + 9), outline="red", width=1)

    output = run_dir / "beavrs_coordinate_overlay.png"
    image.save(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    output = render_overlay(args.run_dir)
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
