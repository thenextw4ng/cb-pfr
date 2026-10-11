#!/usr/bin/env python3
"""Compute assembly-integrated fission-rate proxy from the 51x51 C5G7 mesh tally.

This reports a normalized fission-rate peaking factor, not absolute power. The
mapping assumes the pinned 3x3 lattice: a 2x2 fuel block in the upper-left
corner and a reflector row/column elsewhere. OpenMC's RectLattice universe
array is top-down in y; see the linked geometry documentation in the report.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

POSITIONS = ("p00", "p01", "p10", "p11")
MESH_N = 51
BLOCK_N = 17


class AssemblyTallyError(ValueError):
    pass


def summarize_assembly_rates(mesh_mean: Sequence[Sequence[float]], layout_signature: str) -> dict:
    """Aggregate a 51x51 fission mesh into four 17x17 fuel assembly blocks."""
    import numpy as np

    arr = np.asarray(mesh_mean, dtype=float)
    if arr.shape != (MESH_N, MESH_N):
        raise AssemblyTallyError(f"expected mesh shape {(MESH_N, MESH_N)}, got {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise AssemblyTallyError("mesh tally contains non-finite values")
    if not isinstance(layout_signature, str) or len(layout_signature) != 4 or any(c not in "UM" for c in layout_signature):
        raise AssemblyTallyError("layout signature must be four characters from U/M")
    if layout_signature.count("M") != 2:
        raise AssemblyTallyError("layout signature must contain exactly two MOX positions")
    if np.any(arr < 0):
        raise AssemblyTallyError("fission-rate mesh tally must be non-negative")

    # The first row in RectLattice.universes is the highest-y row. Mesh y index
    # increases from lower to higher y, so the top fuel row occupies [34:51].
    blocks = {
        "p00": (slice(0, 17), slice(34, 51)),
        "p01": (slice(17, 34), slice(34, 51)),
        "p10": (slice(0, 17), slice(17, 34)),
        "p11": (slice(17, 34), slice(17, 34)),
    }
    rates = {position: float(arr[x_slice, y_slice].sum())
             for position, (x_slice, y_slice) in blocks.items()}
    if any(value <= 0 for value in rates.values()):
        raise AssemblyTallyError("each fuel assembly must have a positive integrated fission-rate tally")
    mean_rate = sum(rates.values()) / len(rates)
    normalized = {position: value / mean_rate for position, value in rates.items()}
    peak = max(rates.values()) / mean_rate
    return {
        "layout_signature": layout_signature,
        "positions_order": list(POSITIONS),
        "material_by_position": {position: ("MOX" if layout_signature[i] == "M" else "UO2")
                                 for i, position in enumerate(POSITIONS)},
        "assembly_integrated_fission_rate": rates,
        "mean_assembly_fission_rate": mean_rate,
        "normalized_assembly_fission_rate": normalized,
        "fission_rate_peaking_factor": peak,
        "metric_definition": "max(assembly-integrated fission rate) / mean(assembly-integrated fission rate)",
        "metric_interpretation": "dimensionless fission-rate proxy; not absolute power or a reactor-safety metric",
        "uncertainty_status": "not_propagated_for_correlated_mesh_bins; estimate across independent statepoints instead",
    }


def analyze_statepoint(statepoint: Path, candidate_id: str, layout_signature: str) -> dict:
    try:
        import openmc
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("OpenMC 0.16.0 Python API and NumPy are required") from exc
    if not statepoint.is_file():
        raise FileNotFoundError(statepoint)
    with openmc.StatePoint(statepoint) as sp:
        tally = sp.get_tally(name="tally 1")
        mesh_filter = next((f for f in tally.filters if isinstance(f, openmc.MeshFilter)), None)
        if mesh_filter is None:
            raise AssemblyTallyError("tally 1 has no mesh filter")
        mesh = mesh_filter.mesh
        if list(mesh.dimension) != [51, 51, 1]:
            raise AssemblyTallyError(f"expected mesh dimension [51, 51, 1], got {list(mesh.dimension)}")
        if "fission" not in tally.scores:
            raise AssemblyTallyError(f"tally 1 lacks fission score: {tally.scores}")
        score_index = tally.scores.index("fission")
        values = np.asarray(tally.get_reshaped_data(value="mean", expand_dims=True), dtype=float)
        # One mesh filter contributes x,y,z axes, followed by nuclide and score.
        values = values.reshape((51, 51, 1, -1, len(tally.scores)))
        mesh_mean = values[:, :, 0, 0, score_index]
        result = summarize_assembly_rates(mesh_mean, layout_signature)
        result.update({
            "schema_version": "1.0",
            "candidate_id": candidate_id,
            "statepoint": str(statepoint),
            "keff_mean": float(sp.keff.nominal_value),
            "keff_std_dev": float(sp.keff.std_dev),
            "mesh_dimension": [int(v) for v in mesh.dimension],
            "mesh_lower_left": [float(v) for v in mesh.lower_left],
            "mesh_upper_right": [float(v) for v in mesh.upper_right],
            "score": "fission",
            "openmc_version": ".".join(str(v) for v in sp.version),
        })
        return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--statepoint", required=True, type=Path)
    p.add_argument("--candidate-id", required=True)
    p.add_argument("--layout-signature", required=True, help="4-char signature in p00,p01,p10,p11 order")
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    if a.out.exists():
        p.error(f"refusing to overwrite existing output: {a.out}")
    try:
        report = analyze_statepoint(a.statepoint, a.candidate_id, a.layout_signature)
    except (OSError, ValueError, RuntimeError) as exc:
        p.error(str(exc))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate_id": report["candidate_id"],
        "layout_signature": report["layout_signature"],
        "fission_rate_peaking_factor": report["fission_rate_peaking_factor"],
        "uncertainty_status": report["uncertainty_status"],
        "output": str(a.out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
