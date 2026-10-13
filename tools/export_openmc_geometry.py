#!/usr/bin/env python3
"""Generate geometry-only PNG plots from an existing OpenMC model input directory.

This runs OpenMC in plotting mode only; it does not run neutron transport.
Usage: python tools/export_openmc_geometry.py --model-dir path/to/model-inputs
Requires an OpenMC executable and geometry.xml + materials.xml (+ settings.xml).
Outputs are written into <model-dir>/cbpfr_geometry/ for the HTML workstation to discover
when that directory is within a scanned repository folder.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", required=True, type=Path, help="Directory containing the validated OpenMC XML model inputs")
    parser.add_argument("--openmc", default="openmc", help="OpenMC executable path (default: openmc)")
    parser.add_argument("--pixels", type=int, default=900, help="Square image resolution (default: 900)")
    parser.add_argument("--origin", nargs=3, type=float, metavar=("X", "Y", "Z"),
                        help="Explicit slice origin in cm; defaults to model bounding-box center")
    parser.add_argument("--width", nargs=2, type=float, metavar=("X", "Y"),
                        help="Explicit plot width in cm; defaults to finite model bounding-box width")
    args = parser.parse_args()

    model_dir = args.model_dir.expanduser().resolve()
    if not model_dir.is_dir():
        parser.error(f"Model directory does not exist: {model_dir}")
    required = ("geometry.xml", "materials.xml", "settings.xml")
    missing = [name for name in required if not (model_dir / name).is_file()]
    if missing:
        parser.error("Missing required model inputs: " + ", ".join(missing))
    executable = shutil.which(args.openmc) if not Path(args.openmc).is_file() else str(Path(args.openmc).resolve())
    if not executable:
        parser.error(f"OpenMC executable not found: {args.openmc}. Activate the environment where OpenMC is installed.")

    origin = args.origin
    width = args.width
    if origin is None or width is None:
        try:
            import openmc
            geometry = openmc.Geometry.from_xml(str(model_dir / "geometry.xml"))
            bounds = geometry.bounding_box
            lower = [float(v) for v in bounds.lower_left]
            upper = [float(v) for v in bounds.upper_right]
            if any(not (lo < hi and abs(lo) < 1.0e100 and abs(hi) < 1.0e100)
                   for lo, hi in zip(lower, upper)):
                raise ValueError("The model bounding box is not finite.")
            if origin is None:
                origin = [(lo + hi) / 2.0 for lo, hi in zip(lower, upper)]
            if width is None:
                width = [upper[0] - lower[0], upper[1] - lower[1]]
        except Exception as exc:
            parser.error(
                "Could not derive finite plot bounds from geometry.xml using the OpenMC Python API. "
                "Install/import openmc successfully or pass both --origin X Y Z and --width X Y. "
                f"Details: {exc}"
            )
    if args.pixels < 100 or args.pixels > 4000:
        parser.error("--pixels must be between 100 and 4000.")
    if any(v <= 0 for v in width):
        parser.error("--width values must be positive.")

    output = model_dir / "cbpfr_geometry"
    output.mkdir(exist_ok=True)
    plots_xml = ET.Element("plots")
    plot = ET.SubElement(plots_xml, "plot", id="1", filename="cbpfr_geometry_xy", type="slice", color_by="material")
    ET.SubElement(plot, "basis").text = "xy"
    ET.SubElement(plot, "origin").text = " ".join(f"{v:.8g}" for v in origin)
    ET.SubElement(plot, "width").text = " ".join(f"{v:.8g}" for v in width)
    ET.SubElement(plot, "pixels").text = f"{args.pixels} {args.pixels}"
    ET.SubElement(plot, "background").text = "245 248 250"
    ET.ElementTree(plots_xml).write(output / "plots.xml", encoding="utf-8", xml_declaration=True)

    # Keep all inputs and outputs separate from the source model directory.
    # OpenMC resolves model XML relative to cwd, so use a temporary output folder
    # and copy the three authoritative inputs without editing their contents.
    import tempfile
    import shutil as _shutil
    with tempfile.TemporaryDirectory(prefix="cbpfr-openmc-plot-") as tmp:
        work = Path(tmp)
        for name in required:
            _shutil.copy2(model_dir / name, work / name)
        _shutil.copy2(output / "plots.xml", work / "plots.xml")
        result = subprocess.run([executable, "--plot"], cwd=work, text=True, capture_output=True)
        if result.returncode != 0:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            print("OpenMC geometry plotting failed; no transport simulation was run.", file=sys.stderr)
            return result.returncode
        generated = work / "cbpfr_geometry_xy.png"
        if not generated.is_file():
            print("OpenMC exited successfully but did not produce cbpfr_geometry_xy.png. Check OpenMC plotting support and model inputs.", file=sys.stderr)
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            return 2
        shutil.copy2(generated, output / generated.name)
    print(f"Geometry plot created: {output / 'cbpfr_geometry_xy.png'}")
    print("Source: OpenMC plot mode using the supplied model XML files; no transport calculation performed.")
    print(f"Slice origin (cm): {origin}; plot width (cm): {width}. Bounds are derived from the model unless explicitly supplied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
