#!/usr/bin/env python3
"""Independently audit C5G7 mesh-to-assembly spatial support from raw statepoints.

Requires h5py and NumPy. This is a structural mapping check, not benchmark or
physics validation. It verifies candidate labels against the generated lattice
assignment, checks mesh extents/pitch, and confirms that fission-score support
occupies the four fuel blocks while fixed reflector blocks remain zero.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path


EXPECTED_DIMENSION = (51, 51, 1)
EXPECTED_LOWER_LEFT_XY = (-32.13, -32.13)
EXPECTED_UPPER_RIGHT_XY = (32.13, 32.13)
EXPECTED_PITCH = 1.26
POSITIONS = ("p00", "p01", "p10", "p11")
BLOCKS = {
    "p00": (slice(0, 17), slice(34, 51)),
    "p01": (slice(17, 34), slice(34, 51)),
    "p10": (slice(0, 17), slice(17, 34)),
    "p11": (slice(17, 34), slice(17, 34)),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_lattice_rows(builder_text: str) -> list[list[str]]:
    match = re.search(
        r"lattices\[['\"]Core['\"]\]\.universes\s*=\s*(\[\[.*?\]\])",
        builder_text,
        flags=re.S,
    )
    if not match:
        raise ValueError("generated builder lacks an auditable Core lattice assignment")
    rows = re.findall(r"\[([umw,\s]+)\]", match.group(1))
    parsed = [[token.strip() for token in row.split(",") if token.strip()] for row in rows]
    if len(parsed) != 3 or any(len(row) != 3 for row in parsed):
        raise ValueError(f"expected a 3x3 Core lattice assignment, got {parsed}")
    if any(symbol not in {"u", "m", "w"} for row in parsed for symbol in row):
        raise ValueError(f"unexpected lattice symbol in assignment: {parsed}")
    return parsed


def expected_lattice(layout: dict) -> list[list[str]]:
    if set(layout) != set(POSITIONS):
        raise ValueError(f"layout positions must be exactly {POSITIONS}")
    if any(material not in {"UO2", "MOX"} for material in layout.values()):
        raise ValueError("layout contains unknown fuel material")
    if sorted(layout.values()) != ["MOX", "MOX", "UO2", "UO2"]:
        raise ValueError("layout must contain exactly two UO2 and two MOX assemblies")
    symbol = {p: ("u" if layout[p] == "UO2" else "m") for p in POSITIONS}
    return [
        [symbol["p00"], symbol["p01"], "w"],
        [symbol["p10"], symbol["p11"], "w"],
        ["w", "w", "w"],
    ]


def audit_case(case_dir: Path) -> dict:
    import h5py
    import numpy as np

    result_path = case_dir / "CASE_RESULT.json"
    builder_path = case_dir / "model" / "2d" / "build-xml-2d.py"
    if not result_path.is_file() or not builder_path.is_file():
        raise ValueError(f"{case_dir}: CASE_RESULT.json or generated builder missing")
    case = json.loads(result_path.read_text(encoding="utf-8"))
    candidate_id = case.get("candidate_id")
    layout = case.get("layout")
    signature = "".join("M" if layout.get(p) == "MOX" else "U" for p in POSITIONS)
    if candidate_id != f"c5g7-2x2-{signature}":
        raise ValueError(f"{case_dir}: candidate ID does not match material layout")
    actual_rows = parse_lattice_rows(builder_path.read_text(encoding="utf-8"))
    expected_rows = expected_lattice(layout)
    if actual_rows != expected_rows:
        raise ValueError(
            f"{case_dir}: generated lattice assignment does not match manifest; "
            f"expected {expected_rows}, got {actual_rows}"
        )

    physical = case.get("physical_results") or {}
    statepoint_rel = physical.get("statepoint")
    if not isinstance(statepoint_rel, str) or not statepoint_rel:
        raise ValueError(f"{case_dir}: statepoint path missing from physical_results")
    statepoint = case_dir / statepoint_rel
    if not statepoint.is_file():
        raise FileNotFoundError(statepoint)

    with h5py.File(statepoint, "r") as sp:
        mesh = sp["tallies/meshes/mesh 1"]
        dimension = tuple(int(v) for v in mesh["dimension"][:])
        lower_left = tuple(float(v) for v in mesh["lower_left"][:])
        upper_right = tuple(float(v) for v in mesh["upper_right"][:])
        width = tuple(float(v) for v in mesh["width"][:])
        if dimension != EXPECTED_DIMENSION:
            raise ValueError(f"{candidate_id}: mesh dimension mismatch: {dimension}")
        if not all(math.isclose(lower_left[i], EXPECTED_LOWER_LEFT_XY[i], abs_tol=1e-10) for i in range(2)):
            raise ValueError(f"{candidate_id}: mesh lower-left XY mismatch: {lower_left}")
        if not all(math.isclose(upper_right[i], EXPECTED_UPPER_RIGHT_XY[i], abs_tol=1e-10) for i in range(2)):
            raise ValueError(f"{candidate_id}: mesh upper-right XY mismatch: {upper_right}")
        if not all(math.isclose(width[i], EXPECTED_PITCH, abs_tol=1e-10) for i in range(2)):
            raise ValueError(f"{candidate_id}: mesh bin pitch mismatch: {width}")

        tally = sp["tallies/tally 1"]
        scores = [v.decode() if isinstance(v, bytes) else str(v) for v in tally["score_bins"][:]]
        if "fission" not in scores:
            raise ValueError(f"{candidate_id}: mesh tally has no fission score")
        results = tally["results"][:]
        if results.shape != (51 * 51, len(scores), 2):
            raise ValueError(f"{candidate_id}: unexpected raw tally result shape {results.shape}")
        # OpenMC's serialized mesh-bin sequence increments x fastest. Fortran
        # reshaping restores [x, y] axes, independently of the OpenMC Python API.
        mesh_fission = results[:, scores.index("fission"), 0].reshape((51, 51), order="F")
        if not np.isfinite(mesh_fission).all() or np.any(mesh_fission < 0):
            raise ValueError(f"{candidate_id}: invalid fission tally values")
        positive = mesh_fission > 0
        fuel_support = {
            p: int(np.count_nonzero(positive[x, y]))
            for p, (x, y) in BLOCKS.items()
        }
        right_reflector_nonzero = int(np.count_nonzero(positive[34:51, :]))
        bottom_reflector_nonzero = int(np.count_nonzero(positive[:, 0:17]))
        if any(count <= 0 for count in fuel_support.values()):
            raise ValueError(f"{candidate_id}: at least one expected fuel block has no fission support: {fuel_support}")
        if len(set(fuel_support.values())) != 1:
            raise ValueError(f"{candidate_id}: fission support differs by assembly block: {fuel_support}")
        if right_reflector_nonzero or bottom_reflector_nonzero:
            raise ValueError(
                f"{candidate_id}: fission tally leaks into fixed reflector region "
                f"(right={right_reflector_nonzero}, bottom={bottom_reflector_nonzero})"
            )

    return {
        "candidate_id": candidate_id,
        "layout_signature": signature,
        "layout_matches_generated_lattice": True,
        "statepoint": str(statepoint_rel),
        "statepoint_sha256": sha256(statepoint),
        "mesh_dimension": list(dimension),
        "mesh_lower_left": list(lower_left),
        "mesh_upper_right": list(upper_right),
        "mesh_xy_bin_pitch": list(width[:2]),
        "fission_positive_bins_by_fuel_assembly": fuel_support,
        "right_reflector_positive_bins": right_reflector_nonzero,
        "bottom_reflector_positive_bins": bottom_reflector_nonzero,
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-root", required=True, type=Path,
                        help="Unpacked root containing round_*/candidate directories")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite existing output: {args.out}")
    try:
        round_dirs = sorted(
            d for d in args.study_root.glob("round_*")
            if (d / "STUDY_SUMMARY.json").is_file()
        )
        if not round_dirs:
            raise ValueError(f"no round_*/STUDY_SUMMARY.json found under {args.study_root}")
        cases = []
        for round_dir in round_dirs:
            summary = json.loads((round_dir / "STUDY_SUMMARY.json").read_text(encoding="utf-8"))
            for case in summary.get("cases", []):
                candidate_dir = round_dir / case["candidate_id"]
                cases.append(audit_case(candidate_dir))
        candidate_ids = {r["candidate_id"] for r in cases}
        round_ids = len(round_dirs)
        if len(candidate_ids) != 6 or len(cases) != round_ids * 6:
            raise ValueError(f"expected six candidates in every round; rounds={round_ids}, cases={len(cases)}")
        if len({r["statepoint_sha256"] for r in cases}) != len(cases):
            raise ValueError("statepoint hashes are not unique across the audited study")
        report = {
            "schema_version": "1.0",
            "status": "PASS",
            "audit_type": "independent_raw_hdf5_mesh_spatial_support_and_generated_lattice_check",
            "round_count": round_ids,
            "candidate_count": len(candidate_ids),
            "case_count": len(cases),
            "unique_statepoint_hash_count": len({r["statepoint_sha256"] for r in cases}),
            "cases": cases,
            "interpretation_limits": [
                "This audit checks structural mesh-to-assembly support and candidate-to-lattice identity.",
                "It does not validate cross sections, geometry against the full primary benchmark specification, convergence, or physical suitability.",
                "Zero fission support in reflectors and equal positive-bin counts in fuel blocks are structural checks, not a power-validation result.",
            ],
        }
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "round_count": round_ids,
        "candidate_count": report["candidate_count"],
        "case_count": report["case_count"],
        "output": str(args.out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
