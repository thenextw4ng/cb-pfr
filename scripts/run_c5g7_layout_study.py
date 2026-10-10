#!/usr/bin/env python3
"""Prepare and optionally execute the six reformulated C5G7 2-D layout cases.

This script only supports the explicitly reformulated assembly-placement study.
It never maps the legacy burnup-state QUBO to UO2/MOX. Preparation does not
require OpenMC; execution requires an installed OpenMC Python package and CLI.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SOURCE_REPO = "https://github.com/mit-crpg/benchmarks.git"
MODEL_RELATIVE = Path("c5g7/openmc")
BUILDER_RELATIVE = Path("2d/build-xml-2d.py")
CANONICAL_ASSIGNMENT = "lattices['Core'].universes = [[u, m, w], [m, u, w], [w, w, w]]"
POSITION_ORDER = ("p00", "p01", "p10", "p11")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_source(source_root: Path) -> tuple[Path, str]:
    provenance_path = source_root / "UPSTREAM_PROVENANCE.json"
    if not provenance_path.is_file():
        raise ValueError("source root must contain UPSTREAM_PROVENANCE.json from prepare_c5g7_reference.py")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    revision = provenance.get("source_commit")
    if provenance.get("source_repository") != SOURCE_REPO:
        raise ValueError("unexpected upstream repository in provenance")
    if not isinstance(revision, str) or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("provenance lacks a full lowercase Git commit SHA")
    model = source_root / MODEL_RELATIVE
    builder = model / BUILDER_RELATIVE
    if not builder.is_file():
        raise ValueError(f"expected upstream model builder not found: {builder}")
    return model, revision


def validate_design_space(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("design_study_id") != "C5G7-2x2-two-UO2-two-MOX-layout-enumeration":
        raise ValueError("unexpected design_study_id")
    candidates = data.get("candidate_layouts")
    if not isinstance(candidates, list) or len(candidates) != 6:
        raise ValueError("expected exactly six enumerated layouts")
    seen = set()
    baseline_count = 0
    for item in candidates:
        layout = item.get("fuel_assembly_layout", {})
        if set(layout) != set(POSITION_ORDER):
            raise ValueError(f"invalid position set in {item.get('candidate_id')}")
        if sorted(layout.values()) != ["MOX", "MOX", "UO2", "UO2"]:
            raise ValueError(f"invalid material counts in {item.get('candidate_id')}")
        signature = "".join("M" if layout[p] == "MOX" else "U" for p in POSITION_ORDER)
        if signature in seen:
            raise ValueError(f"duplicate layout signature: {signature}")
        seen.add(signature)
        baseline_count += bool(item.get("is_canonical_reference_arrangement"))
    if len(seen) != 6 or baseline_count != 1:
        raise ValueError("design space must have six unique layouts and exactly one canonical baseline")
    return data


def patch_builder(builder: Path, layout: dict, batches: int, inactive: int, particles: int) -> None:
    source = builder.read_text(encoding="utf-8")
    if source.count(CANONICAL_ASSIGNMENT) != 1:
        raise ValueError("upstream lattice assignment differs from audited template; refusing to patch")
    rows = []
    for row in range(2):
        cells = []
        for col in range(2):
            material = layout[f"p{row}{col}"]
            cells.append("u" if material == "UO2" else "m")
        cells.append("w")
        rows.append("[" + ", ".join(cells) + "]")
    rows.append("[w, w, w]")
    replacement = "lattices['Core'].universes = [" + ", ".join(rows) + "]"
    source = source.replace(CANONICAL_ASSIGNMENT, replacement)
    replacements = {
        "batches = 20000": f"batches = {batches}",
        "inactive = 500": f"inactive = {inactive}",
        "particles = 10000": f"particles = {particles}",
    }
    for old, new in replacements.items():
        if source.count(old) != 1:
            raise ValueError(f"upstream runtime setting differs from audited template: {old!r}")
        source = source.replace(old, new)
    if inactive >= batches:
        raise ValueError("inactive batches must be fewer than total batches")
    builder.write_text(source, encoding="utf-8")


def file_manifest(case_dir: Path) -> dict:
    result = {}
    for path in sorted(case_dir.rglob("*")):
        if path.is_file() and path.name != "CASE_MANIFEST.json":
            result[str(path.relative_to(case_dir))] = sha256(path)
    return result


def run_case(case_dir: Path, threads: int) -> dict:
    workdir = case_dir / "model" / "2d"
    env = os.environ.copy()
    commands = [
        [sys.executable, "build-xml-2d.py"],
        ["openmc", "-s", str(threads)],
    ]
    records = []
    for command in commands:
        started = datetime.now(timezone.utc).isoformat()
        try:
            proc = subprocess.run(command, cwd=workdir, env=env, text=True, capture_output=True)
        except OSError as exc:
            raise RuntimeError(f"unable to execute {command[0]} in {workdir}: {exc}") from exc
        record = {
            "command": command,
            "started_at_utc": started,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "returncode": proc.returncode,
            "stdout": proc.stdout[-12000:],
            "stderr": proc.stderr[-12000:],
        }
        records.append(record)
        (case_dir / ("build.log" if command[1] == "build-xml-2d.py" else "openmc.log")).write_text(
            "STDOUT\n" + proc.stdout + "\nSTDERR\n" + proc.stderr, encoding="utf-8"
        )
        if proc.returncode != 0:
            return {"status": "failed", "commands": records, "failure": f"command exited {proc.returncode}"}
    statepoints = sorted(workdir.glob("statepoint.*.h5"), key=lambda p: p.stat().st_mtime)
    if not statepoints:
        return {"status": "failed", "commands": records, "failure": "OpenMC exited successfully but no statepoint file was found"}
    try:
        import openmc  # type: ignore
        with openmc.StatePoint(statepoints[-1]) as sp:
            keff = sp.keff
            result = {
                "status": "completed",
                "commands": records,
                "statepoint": str(statepoints[-1].relative_to(case_dir)),
                "keff_mean": float(keff.nominal_value),
                "keff_std_dev": float(keff.std_dev),
                "tallies": {},
            }
            for name in ("tally 2", "tally 1"):
                try:
                    tally = sp.get_tally(name=name)
                    result["tallies"][name] = {
                        "scores": list(tally.scores),
                        "mean_shape": list(tally.mean.shape),
                        "mean": tally.mean.tolist(),
                        "std_dev": tally.std_dev.tolist(),
                    }
                except (LookupError, ValueError):
                    result["tallies"][name] = {"status": "not_found"}
            return result
    except Exception as exc:
        return {
            "status": "completed_unparsed",
            "commands": records,
            "statepoint": str(statepoints[-1].relative_to(case_dir)),
            "parser_error": f"{type(exc).__name__}: {exc}",
            "note": "Raw statepoint retained; do not use candidate for ranking until parsed and reviewed.",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, help="checkout prepared by scripts/prepare_c5g7_reference.py")
    parser.add_argument("--design-space", required=True, help="JSON produced by scripts/enumerate_c5g7_layouts.py")
    parser.add_argument("--output", required=True, help="new directory; never overwritten")
    parser.add_argument("--mode", choices=("prepare", "run"), default="prepare")
    parser.add_argument("--batches", type=int, default=100, help="total batches; default is a smoke-test profile, not benchmark-grade")
    parser.add_argument("--inactive", type=int, default=10, help="inactive batches; default is a smoke-test profile")
    parser.add_argument("--particles", type=int, default=1000, help="particles per batch; default is a smoke-test profile")
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args()
    if args.batches < 2 or args.inactive < 0 or args.inactive >= args.batches or args.particles < 1 or args.threads < 1:
        parser.error("require batches >= 2, 0 <= inactive < batches, particles >= 1, and threads >= 1")

    source_root = Path(args.source_root).expanduser().resolve()
    design_path = Path(args.design_space).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    if output.exists():
        parser.error(f"output already exists; refusing to overwrite: {output}")
    if not output.parent.is_dir():
        parser.error(f"output parent directory does not exist: {output.parent}")
    try:
        upstream_model, revision = validate_source(source_root)
        design = validate_design_space(design_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    if args.mode == "run" and (shutil.which("openmc") is None):
        parser.error("--mode run requires the OpenMC executable on PATH")

    output.mkdir()
    summary = {
        "schema_version": "1.0",
        "study_id": design["design_study_id"],
        "status": "preparing",
        "upstream_repository": SOURCE_REPO,
        "upstream_commit": revision,
        "upstream_model_builder_sha256": sha256(upstream_model / BUILDER_RELATIVE),
        "design_space_sha256": sha256(design_path),
        "mode": args.mode,
        "settings": {"batches": args.batches, "inactive": args.inactive, "particles": args.particles, "threads": args.threads},
        "profile_warning": "Default settings are smoke-test settings only; do not compare to benchmark reference or claim converged physics without a separate convergence study.",
        "cases": [],
        "nonclaims": [
            "This is a new C5G7 assembly-placement design study, not a mapping of the legacy burnup-state QUBO.",
            "A successful run does not by itself verify the model against the OECD/NEA reference.",
            "Smoke-test results are not benchmark-grade and must not be presented as converged physical evidence.",
        ],
    }
    for candidate in sorted(design["candidate_layouts"], key=lambda c: (not c["is_canonical_reference_arrangement"], c["candidate_id"])):
        case_dir = output / candidate["candidate_id"]
        case_dir.mkdir()
        model_copy = case_dir / "model"
        shutil.copytree(upstream_model, model_copy)
        builder = model_copy / BUILDER_RELATIVE
        patch_builder(builder, candidate["fuel_assembly_layout"], args.batches, args.inactive, args.particles)
        case = {
            "candidate_id": candidate["candidate_id"],
            "layout": candidate["fuel_assembly_layout"],
            "is_canonical_reference_arrangement": candidate["is_canonical_reference_arrangement"],
            "status": "prepared",
            "input_hashes": file_manifest(case_dir),
            "physical_results": None,
        }
        if args.mode == "run":
            result = run_case(case_dir, args.threads)
            case["status"] = result["status"]
            case["physical_results"] = result
            case["output_hashes_after_run"] = file_manifest(case_dir)
            (case_dir / "CASE_RESULT.json").write_text(json.dumps(case, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            if result["status"] != "completed":
                summary["cases"].append(case)
                summary["status"] = "incomplete"
                summary["cases"].extend({
                    "candidate_id": other["candidate_id"],
                    "status": "not_run_after_prior_failure",
                    "physical_results": None,
                } for other in sorted(design["candidate_layouts"], key=lambda c: (not c["is_canonical_reference_arrangement"], c["candidate_id"])) if other["candidate_id"] != candidate["candidate_id"] and other["candidate_id"] not in {c["candidate_id"] for c in summary["cases"]})
                break
        summary["cases"].append(case)
    else:
        summary["status"] = "prepared_only" if args.mode == "prepare" else "all_runs_completed_needs_independent_validation"
    (output / "STUDY_SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Study output: {output}")
    print(f"Status: {summary['status']}")
    if args.mode == "prepare":
        print("Inputs prepared only. No OpenMC transport calculation was run.")
    elif summary["status"] != "all_runs_completed_needs_independent_validation":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
