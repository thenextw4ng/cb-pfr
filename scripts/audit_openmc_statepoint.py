#!/usr/bin/env python3
"""Read-only audit/export of an OpenMC statepoint using OpenMC's Python API.

This script does not run or modify a simulation. It exports scalar metadata,
tally means/std-devs and a JSON audit report. Mesh bins are numbered only;
no physical orientation is assumed.
"""
from __future__ import annotations

import argparse
import json
import math
import platform
from pathlib import Path

import numpy as np


def _scalar(value):
    """Convert OpenMC uncertainty/scalar values into JSON-safe fields."""
    if value is None:
        return None
    nominal = getattr(value, "n", getattr(value, "nominal_value", value))
    std_dev = getattr(value, "s", getattr(value, "std_dev", None))
    try:
        nominal = float(nominal)
    except (TypeError, ValueError):
        return str(value)
    out = {"mean": nominal}
    if std_dev is not None:
        try:
            out["std_dev"] = float(std_dev)
        except (TypeError, ValueError):
            pass
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--statepoint", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    args = parser.parse_args()

    statepoint_path = args.statepoint.expanduser().resolve()
    if not statepoint_path.is_file():
        raise SystemExit(f"Statepoint not found: {statepoint_path}")
    args.outdir.mkdir(parents=True, exist_ok=True)

    try:
        import openmc
    except ImportError as exc:
        raise SystemExit(
            "OpenMC Python module is unavailable. Activate the environment "
            "that contains OpenMC (e.g. conda activate openmc-env)."
        ) from exc

    rows = []
    report = {
        "statepoint_path": str(statepoint_path),
        "python_version": platform.python_version(),
        "openmc_version": getattr(openmc, "__version__", "unknown"),
        "statepoint_file_size_bytes": statepoint_path.stat().st_size,
        "statepoint_read_success": False,
        "tallies": [],
        "warnings": [
            "Mesh bin indices are exported without asserting physical x-y orientation.",
            "Tally means/std-devs are read through OpenMC's Python API, not inferred from raw HDF5 array shape.",
            "Tally scores flux/fission/nu-fission are not automatically absolute power in watts."
        ],
    }

    with openmc.StatePoint(str(statepoint_path)) as sp:
        report["statepoint_read_success"] = True
        for attr in ("current_batch", "n_batches", "n_inactive", "n_particles",
                     "n_realizations", "run_mode", "energy_mode"):
            value = getattr(sp, attr, None)
            if value is not None:
                try:
                    report[attr] = value.item() if hasattr(value, "item") else value
                except Exception:
                    report[attr] = str(value)

        for attr in ("keff", "k_combined"):
            if hasattr(sp, attr):
                try:
                    result = _scalar(getattr(sp, attr))
                    if result is not None:
                        report["keff_source_attribute"] = attr
                        report["keff"] = result
                        break
                except Exception as exc:
                    report.setdefault("keff_read_warnings", []).append(
                        f"{attr}: {type(exc).__name__}: {exc}"
                    )

        try:
            tally_values = list(sp.tallies.values())
        except Exception:
            tally_values = []

        for tally_index, tally in enumerate(tally_values, start=1):
            tally_info = {
                "index": tally_index,
                "id": getattr(tally, "id", None),
                "name": getattr(tally, "name", "") or f"tally_{tally_index}",
                "scores": list(getattr(tally, "scores", []) or []),
                "filters": [],
            }
            for filt in getattr(tally, "filters", []) or []:
                fdesc = {"type": type(filt).__name__}
                for attr in ("type", "bins", "dimension", "lower_left", "upper_right"):
                    if hasattr(filt, attr):
                        try:
                            value = getattr(filt, attr)
                            if isinstance(value, np.ndarray):
                                value = value.tolist()
                            elif isinstance(value, tuple):
                                value = list(value)
                            fdesc[attr] = value
                        except Exception:
                            pass
                mesh = getattr(filt, "mesh", None)
                if mesh is not None:
                    for attr in ("dimension", "lower_left", "upper_right", "width"):
                        if hasattr(mesh, attr):
                            try:
                                value = getattr(mesh, attr)
                                fdesc["mesh_" + attr] = np.asarray(value).tolist()
                            except Exception:
                                pass
                tally_info["filters"].append(fdesc)

            mean = np.asarray(tally.mean)
            std_dev = np.asarray(tally.std_dev)
            tally_info["mean_shape"] = list(mean.shape)
            tally_info["std_dev_shape"] = list(std_dev.shape)
            tally_info["mean_finite"] = bool(np.isfinite(mean).all())
            tally_info["std_dev_finite"] = bool(np.isfinite(std_dev).all())
            tally_info["mean_nonzero_count"] = int(np.count_nonzero(mean))
            tally_info["std_dev_nonzero_count"] = int(np.count_nonzero(std_dev))
            report["tallies"].append(tally_info)

            # Keep the original multidimensional index in a transparent column.
            mean_flat = mean.reshape(-1)
            sd_flat = std_dev.reshape(-1)
            score_names = tally_info["scores"]
            for flat_index, mean_value in enumerate(mean_flat):
                sd_value = float(sd_flat[flat_index]) if flat_index < len(sd_flat) else math.nan
                score_index = flat_index % max(len(score_names), 1)
                bin_index = flat_index // max(len(score_names), 1)
                rows.append({
                    "tally_index": tally_index,
                    "tally_id": tally_info["id"],
                    "tally_name": tally_info["name"],
                    "flat_value_index": flat_index,
                    "flat_bin_index_assuming_score_last": bin_index,
                    "score_index_assuming_score_last": score_index,
                    "score_name_assuming_score_last": (
                        score_names[score_index] if score_names and score_index < len(score_names)
                        else "unknown"
                    ),
                    "mean": float(mean_value),
                    "std_dev": sd_value,
                })

    if rows:
        import csv
        csv_path = args.outdir / "tally_values_flat.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        report["tally_csv"] = str(csv_path)
        report["tally_csv_rows"] = len(rows)

    report_path = args.outdir / "statepoint_audit.json"
    report_path.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "statepoint": str(statepoint_path),
        "audit_json": str(report_path),
        "tally_csv_rows": len(rows),
        "keff": report.get("keff"),
        "tally_count": len(report["tallies"]),
    }, indent=2))


if __name__ == "__main__":
    main()
