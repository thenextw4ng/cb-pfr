#!/usr/bin/env python3
"""Inspect the committed OpenMC HDF5 archive and compare its production statepoint.

Requires h5py. This is a raw-file semantic consistency check, not a benchmark or
QUBO-to-physics validation.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile
from typing import Any


def _decode(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").rstrip("\x00")
    if hasattr(value, "item"):
        try:
            return _decode(value.item())
        except (ValueError, TypeError):
            pass
    if hasattr(value, "tolist"):
        try:
            return _decode(value.tolist())
        except (ValueError, TypeError):
            pass
    if isinstance(value, list):
        return [_decode(item) for item in value]
    return value


def _as_int(handle: Any, key: str) -> int | None:
    if key not in handle:
        return None
    value = _decode(handle[key][()])
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_text(handle: Any, key: str) -> str | None:
    if key not in handle:
        return None
    value = _decode(handle[key][()])
    return value if isinstance(value, str) else None


def _close(actual: Any, expected: Any, *, rel_tol: float = 1e-8,
           abs_tol: float = 1e-12) -> bool:
    try:
        a, e = float(actual), float(expected)
    except (TypeError, ValueError):
        return False
    return math.isfinite(a) and math.isfinite(e) and math.isclose(
        a, e, rel_tol=rel_tol, abs_tol=abs_tol
    )


def inspect_statepoint_bytes(data: bytes, member_path: str, baseline: dict[str, Any]) -> dict[str, Any]:
    try:
        import h5py
    except ImportError as exc:
        raise RuntimeError("h5py is required; install it with 'python -m pip install h5py'") from exc

    with h5py.File(io.BytesIO(data), "r") as handle:
        if "k_combined" not in handle:
            raise ValueError("statepoint lacks root dataset k_combined")
        keff = _decode(handle["k_combined"][()])
        if not isinstance(keff, list) or len(keff) < 2:
            try:
                keff = [float(keff[0]), float(keff[1])]
            except (TypeError, IndexError, ValueError):
                raise ValueError("k_combined does not contain mean and standard deviation")
        keff_mean, keff_sd = float(keff[0]), float(keff[1])

        metadata = {
            "n_batches": _as_int(handle, "n_batches"),
            "n_inactive": _as_int(handle, "n_inactive"),
            "n_particles": _as_int(handle, "n_particles"),
            "n_realizations": _as_int(handle, "n_realizations"),
            "run_mode": _as_text(handle, "run_mode"),
            "energy_mode": _as_text(handle, "energy_mode"),
        }

        tally_records = []
        mesh_dimensions = []
        if "tallies/meshes" in handle:
            for mesh_name, mesh in handle["tallies/meshes"].items():
                if "dimension" in mesh:
                    dims = [int(v) for v in mesh["dimension"][()]]
                    mesh_dimensions.append({"name": mesh_name, "dimension": dims})

        if "tallies" in handle:
            tallies_group = handle["tallies"]
            for tally_name, tally in tallies_group.items():
                if not tally_name.startswith("tally ") or not hasattr(tally, "keys"):
                    continue
                scores = []
                if "score_bins" in tally:
                    scores = [str(_decode(v)) for v in tally["score_bins"][()]]
                tally_records.append({"name": tally_name, "scores": scores})

    checks = []

    def add(name: str, passed: bool, actual: Any, expected: Any) -> None:
        checks.append({
            "name": name,
            "status": "PASS" if passed else "FAIL",
            "actual": actual,
            "expected": expected,
        })

    for key in ("n_batches", "n_inactive", "n_particles", "n_realizations", "run_mode", "energy_mode"):
        expected = baseline.get(key)
        actual = metadata.get(key)
        if expected is None:
            add(f"metadata:{key}", False, actual, None)
        elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
            add(f"metadata:{key}", _close(actual, expected), actual, expected)
        else:
            add(f"metadata:{key}", actual == expected, actual, expected)

    add("keff_mean", _close(keff_mean, baseline.get("keff_mean"), rel_tol=1e-10, abs_tol=1e-12),
        keff_mean, baseline.get("keff_mean"))
    add("keff_std_dev", _close(keff_sd, baseline.get("keff_std_dev"), rel_tol=1e-8, abs_tol=1e-12),
        keff_sd, baseline.get("keff_std_dev"))

    expected_mesh = baseline.get("tally_mesh_dimension")
    found_mesh = any(item["dimension"] == expected_mesh for item in mesh_dimensions)
    add("expected_mesh_dimension_present", found_mesh, mesh_dimensions, expected_mesh)

    expected_scores = set(baseline.get("tally_scores") or [])
    matching_score_tally = next(
        (item for item in tally_records if set(item["scores"]) == expected_scores),
        None,
    )
    add("expected_tally_scores_present", matching_score_tally is not None,
        matching_score_tally, sorted(expected_scores))

    failed = [item["name"] for item in checks if item["status"] != "PASS"]
    return {
        "schema_version": "1.0",
        "status": "PASS" if not failed else "FAIL",
        "statepoint_member": member_path,
        "statepoint_sha256": hashlib.sha256(data).hexdigest(),
        "statepoint_size_bytes": len(data),
        "keff_mean": keff_mean,
        "keff_std_dev": keff_sd,
        **metadata,
        "mesh_dimensions": mesh_dimensions,
        "tallies": tally_records,
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "failed_checks": failed,
        "checks": checks,
        "interpretation": (
            "PASS means the raw HDF5 statepoint agrees with the transcribed baseline for "
            "the checked fields. It does not validate model geometry, nuclear data, candidate "
            "identity, the QUBO-to-material mapping, or reactor safety."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--statepoint-name", default="statepoint.20000.h5")
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"output already exists: {args.out}")

    try:
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        with zipfile.ZipFile(args.archive) as archive:
            matches = [
                item for item in archive.infolist()
                if not item.is_dir() and Path(item.filename).name == args.statepoint_name
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"expected exactly one {args.statepoint_name} member, found {len(matches)}"
                )
            member = matches[0]
            data = archive.read(member)
        result = inspect_statepoint_bytes(data, member.filename, baseline)
    except (OSError, zipfile.BadZipFile, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "statepoint_member": result["statepoint_member"],
        "keff_mean": result["keff_mean"],
        "keff_std_dev": result["keff_std_dev"],
        "passed": result["passed_count"],
        "failed": result["failed_count"],
        "failed_checks": result["failed_checks"],
        "report": str(args.out),
    }, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
