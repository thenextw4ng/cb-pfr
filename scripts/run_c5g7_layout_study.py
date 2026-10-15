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
import re
import shutil
import subprocess
import time
import sys
from datetime import datetime, timezone
from pathlib import Path

SOURCE_REPO = "https://github.com/mit-crpg/benchmarks.git"
PINNED_UPSTREAM_COMMIT = "ba41bee54320ada0b4ac39a0dd2ca3c1d090a450"
MODEL_RELATIVE = Path("c5g7/openmc")
BUILDER_RELATIVE = Path("2d/build-xml-2d.py")
CANONICAL_ASSIGNMENT = "lattices['Core'].universes = [[u, m, w], [m, u, w], [w, w, w]]"
MGXS_GROUPS_ANCHOR = "groups = openmc.mgxs.EnergyGroups(np.logspace(-5, 7, 8))"
C5G7_GROUP_BOUNDARIES = (1.0e-5, 0.0635, 10.0, 100.0, 1000.0, 500000.0, 1000000.0, 20000000.0)
MGXS_GROUPS_REPLACEMENT = """energy_boundaries = np.array([1.0e-5, 0.0635, 10.0, 100.0, 1000.0, 500000.0, 1000000.0, 20000000.0], dtype=float)
# OECD/NEA C5G7 standard seven-group energy boundaries (eV).
groups = openmc.mgxs.EnergyGroups(energy_boundaries)"""
POSITION_ORDER = ("p00", "p01", "p10", "p11")
SOURCE_PROFILES = {
    # Initial-source boxes; only_fissionable=True rejects non-fissionable locations.
    "baseline_all_fuel": ([-32.13, -10.71, -1.0], [10.71, 32.13, 1.0]),
    "left_column_only": ([-32.13, -10.71, -1.0], [-10.71, 32.13, 1.0]),
    "right_column_only": ([-10.71, -10.71, -1.0], [10.71, 32.13, 1.0]),
    "upper_row_only": ([-32.13, 10.71, -1.0], [10.71, 32.13, 1.0]),
    # Deliberately pathological initial source confined to the top-left fuel assembly.
    "bad_initial_source": ([-32.13, 10.71, -1.0], [-10.71, 32.13, 1.0]),
}


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
    if revision != PINNED_UPSTREAM_COMMIT:
        raise ValueError(
            f"upstream source commit {revision} differs from pinned audited commit {PINNED_UPSTREAM_COMMIT}"
        )
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


def patch_mgxs_energy_boundaries(materials_file: Path) -> None:
    """Replace nonstandard upstream log-spaced edges with official C5G7 7-group boundaries."""
    source = materials_file.read_text(encoding="utf-8")
    if source.count(MGXS_GROUPS_ANCHOR) != 1:
        raise ValueError("upstream energy-group construction differs from audited template; refusing to patch")
    materials_file.write_text(
        source.replace(MGXS_GROUPS_ANCHOR, MGXS_GROUPS_REPLACEMENT),
        encoding="utf-8",
    )


def audit_mgxs_group_structure(mgxs_file: Path) -> tuple[float, ...]:
    """Fail closed unless generated MGXS has the standard C5G7 energy boundaries."""
    import h5py
    with h5py.File(mgxs_file, "r") as handle:
        if "group structure" not in handle.attrs:
            raise ValueError("MGXS file lacks root group structure attribute")
        actual = tuple(float(value) for value in handle.attrs["group structure"])
    if len(actual) != len(C5G7_GROUP_BOUNDARIES) or any(
        value != expected for value, expected in zip(actual, C5G7_GROUP_BOUNDARIES)
    ):
        raise ValueError(f"generated MGXS energy-group boundaries are not standard C5G7: expected {C5G7_GROUP_BOUNDARIES}, got {actual}")
    return actual


def patch_builder(builder: Path, layout: dict, batches: int, inactive: int, particles: int, seed: int = 620000, source_profile: str = "baseline_all_fuel") -> None:
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
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    seed_anchor = "settings_file.particles = particles"
    if source.count(seed_anchor) != 1:
        raise ValueError(f"upstream runtime setting differs from audited template: {seed_anchor!r}")
    source = source.replace(seed_anchor, seed_anchor + f"\nsettings_file.seed = {seed}")
    if source_profile not in SOURCE_PROFILES:
        raise ValueError(f"unknown initial source profile: {source_profile!r}")
    source_anchor_pattern = re.compile(
        r"settings_file\.source\s*=\s*openmc\.Source\(space=openmc\.stats\.Box\(\s*\[-32\.13,\s*-10\.71,\s*-1\.0\],\s*\[10\.71,\s*32\.13,\s*1\.0\],\s*only_fissionable=True\)\)"
    )
    if len(source_anchor_pattern.findall(source)) != 1:
        raise ValueError("upstream initial source differs from the audited template; refusing to patch")
    source_lower, source_upper = SOURCE_PROFILES[source_profile]
    source_replacement = (
        "settings_file.source = openmc.Source(space=openmc.stats.Box("
        + repr(source_lower) + ", " + repr(source_upper)
        + ", only_fissionable=True))"
    )
    source = source_anchor_pattern.sub(source_replacement, source, count=1)
    entropy_anchor = (
        "settings_file.entropy_lower_left = [-32.13, -32.13, -1.E50]\n"
        "settings_file.entropy_upper_right = [32.13, 32.13, 1.E50]\n"
        "settings_file.entropy_dimension = [51, 51, 1]"
    )
    if source.count(entropy_anchor) != 1:
        raise ValueError("upstream entropy-mesh construction differs from audited template; refusing to patch")
    entropy_replacement = (
        "import math\n"
        "# Derive entropy coverage from the complete model geometry, not a hard-coded source box.\n"
        "entropy_bbox = geometry.bounding_box\n"
        "entropy_lower = [float(v) for v in entropy_bbox.lower_left]\n"
        "entropy_upper = [float(v) for v in entropy_bbox.upper_right]\n"
        "if not all(math.isfinite(v) for v in entropy_lower[:2] + entropy_upper[:2]):\n"
        "    raise ValueError('geometry.bounding_box has non-finite x/y bounds; refusing an incomplete entropy mesh')\n"
        "# The benchmark is two-dimensional; replace unbounded z geometry with a unit-thick diagnostic slab.\n"
        "if not math.isfinite(entropy_lower[2]): entropy_lower[2] = -0.5\n"
        "if not math.isfinite(entropy_upper[2]): entropy_upper[2] = 0.5\n"
        "if entropy_upper[2] <= entropy_lower[2]:\n"
        "    entropy_lower[2], entropy_upper[2] = -0.5, 0.5\n"
        "entropy_mesh = openmc.RegularMesh()\n"
        "entropy_mesh.dimension = [24, 24, 1]\n"
        "entropy_mesh.lower_left = entropy_lower\n"
        "entropy_mesh.upper_right = entropy_upper\n"
        "settings_file.entropy_mesh = entropy_mesh"
    )
    source = source.replace(entropy_anchor, entropy_replacement)
    builder.write_text(source, encoding="utf-8")


def patch_tally_scores(tally_file: Path) -> None:
    """Ensure the archived statepoint includes spatial and global balance responses."""
    source = tally_file.read_text(encoding="utf-8")
    old_mesh = "tallies['Mesh Rates'].scores = ['flux', 'fission', 'nu-fission']"
    new_mesh = "tallies['Mesh Rates'].scores = ['flux', 'fission', 'nu-fission', 'absorption']"
    old_global = "tallies['Global Rates'].scores = ['flux', 'fission', 'nu-fission']"
    new_global = "tallies['Global Rates'].scores = ['flux', 'fission', 'nu-fission', 'absorption']"
    for old, new, label in ((old_mesh, new_mesh, "mesh tally scores"), (old_global, new_global, "global tally scores")):
        if source.count(old) != 1:
            raise ValueError(f"upstream {label} differ from the audited template; refusing to patch")
        source = source.replace(old, new)
    tally_file.write_text(source, encoding="utf-8")


def git_commit_sha() -> str | None:
    env_sha = os.environ.get("GITHUB_SHA")
    if env_sha and len(env_sha) == 40:
        return env_sha
    repo_root = Path(__file__).resolve().parents[1]
    try:
        proc = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"],
                              text=True, capture_output=True, check=True)
        return proc.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def preserve_statepoint_diagnostics(statepoint: Path, case_dir: Path, threads: int,
                                    mgxs_sha256: str | None) -> dict:
    """Persist raw source, global-balance and every tally array next to each statepoint."""
    import numpy as np
    import openmc  # type: ignore

    with openmc.StatePoint(statepoint) as sp:
        global_table = sp.global_tallies
        global_names = [x.decode("utf-8").rstrip("\x00") if isinstance(x, bytes) else str(x)
                        for x in global_table["name"]]
        tally_manifest = {}
        payload = {
            "k_generation": np.asarray(sp.k_generation, dtype=float),
            "entropy": np.asarray(sp.entropy if sp.entropy is not None else [], dtype=float),
            "seed": np.asarray([int(sp.seed)], dtype=np.int64),
            "n_inactive": np.asarray([int(sp.n_inactive)], dtype=np.int64),
            "n_batches": np.asarray([int(sp.n_batches)], dtype=np.int64),
            "n_particles": np.asarray([int(sp.n_particles)], dtype=np.int64),
            "keff_mean": np.asarray([float(sp.keff.nominal_value)], dtype=float),
            "keff_std_dev": np.asarray([float(sp.keff.std_dev)], dtype=float),
            "global_tallies_name": np.asarray(global_names, dtype="U32"),
            "global_tallies_mean": np.asarray(global_table["mean"], dtype=float),
            "global_tallies_std_dev": np.asarray(global_table["std_dev"], dtype=float),
        }
        for name in ("tally 1", "tally 2"):
            try:
                tally = sp.get_tally(name=name)
                safe = name.replace(" ", "_")
                payload[f"{safe}_scores"] = np.asarray(tally.scores, dtype="U32")
                payload[f"{safe}_mean"] = np.asarray(tally.mean, dtype=float)
                payload[f"{safe}_std_dev"] = np.asarray(tally.std_dev, dtype=float)
                tally_manifest[name] = {
                    "scores": list(tally.scores),
                    "filter_types": [type(f).__name__ for f in tally.filters],
                    "mean_shape": list(tally.mean.shape),
                    "std_dev_shape": list(tally.std_dev.shape),
                }
            except (LookupError, ValueError):
                tally_manifest[name] = {"status": "not_found"}
        trace_path = case_dir / "trace.npz"
        np.savez_compressed(trace_path, **payload)
        gt_summary = {
            name: {"mean": float(global_table[i]["mean"]),
                   "std_dev": float(global_table[i]["std_dev"])}
            for i, name in enumerate(global_names)
        }
        version = getattr(openmc, "__version__", "unknown")
        manifest = {
            "schema_version": "1.0",
            "openmc_version": str(version),
            "mgxs_sha256": mgxs_sha256,
            "seed": int(sp.seed),
            "threads": int(threads),
            "git_commit": git_commit_sha(),
            "statepoint": str(statepoint.relative_to(case_dir)),
            "statepoint_sha256": sha256(statepoint),
            "trace_file": "trace.npz",
            "trace_sha256": sha256(trace_path),
            "batches": int(sp.n_batches),
            "inactive": int(sp.n_inactive),
            "particles": int(sp.n_particles),
            "keff": {"mean": float(sp.keff.nominal_value), "std_dev": float(sp.keff.std_dev)},
            "global_tallies": gt_summary,
            "tallies": tally_manifest,
            "leakage_global_tally_present": "leakage" in gt_summary,
            "required_balance_scores_present": (
                "nu-fission" in tally_manifest.get("tally 2", {}).get("scores", [])
                and "absorption" in tally_manifest.get("tally 2", {}).get("scores", [])
                and "leakage" in gt_summary
            ),
        }
        (case_dir / "RUN_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return manifest


def file_manifest(case_dir: Path) -> dict:
    result = {}
    for path in sorted(case_dir.rglob("*")):
        if path.is_file() and path.name != "CASE_MANIFEST.json":
            result[str(path.relative_to(case_dir))] = sha256(path)
    return result


def run_case(case_dir: Path, threads: int) -> dict:
    overall_started = time.monotonic()
    workdir = case_dir / "model" / "2d"
    env = os.environ.copy()
    commands = [
        [sys.executable, "build-xml-2d.py"],
        ["openmc", "-s", str(threads)],
    ]
    records = []
    pre_transport_hashes = None
    mgxs_group_structure = None
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
        if command[1] == "build-xml-2d.py":
            try:
                mgxs_group_structure = audit_mgxs_group_structure(workdir / "mgxs.h5")
            except (OSError, ValueError, KeyError) as exc:
                return {"status": "failed", "commands": records,
                        "failure": f"MGXS group-structure audit failed: {exc}",
                        "mgxs_group_structure_audit": "FAIL"}
            # Freeze hashes after XML generation but before transport execution.
            pre_transport_hashes = file_manifest(case_dir)

    post_transport_hashes = file_manifest(case_dir)
    pre_transport_hashes = pre_transport_hashes or {}
    mutated = {
        path: {"before_sha256": digest, "after_sha256": post_transport_hashes[path]}
        for path, digest in pre_transport_hashes.items()
        if path in post_transport_hashes and post_transport_hashes[path] != digest
    }
    mgxs_path = "model/2d/mgxs.h5"
    provenance = {
        "mgxs_energy_group_boundaries": list(mgxs_group_structure or ()),
        "mgxs_group_structure_audit": "PASS" if mgxs_group_structure else "FAIL",
        "pre_transport_hashes": pre_transport_hashes,
        "post_transport_hashes": post_transport_hashes,
        "mutated_preexisting_files": mutated,
        "mgxs_sha256_before_transport": pre_transport_hashes.get(mgxs_path),
        "mgxs_sha256_after_transport": post_transport_hashes.get(mgxs_path),
    }

    statepoints = sorted(workdir.glob("statepoint.*.h5"), key=lambda p: p.stat().st_mtime)
    if not statepoints:
        return {
            "status": "failed",
            "commands": records,
            "failure": "OpenMC exited successfully but no statepoint file was found",
            **provenance,
        }
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
                **provenance,
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
        # Reopen once to archive all batch traces, global balance tallies and full tally arrays.
        result["diagnostics_manifest"] = preserve_statepoint_diagnostics(
            statepoints[-1], case_dir, threads, provenance.get("mgxs_sha256_after_transport")
        )
        result["openmc_version"] = result["diagnostics_manifest"]["openmc_version"]
        result["run_wallclock_seconds"] = round(time.monotonic() - overall_started, 3)
        result["run_manifest"] = "RUN_MANIFEST.json"
        result["trace_file"] = "trace.npz"
        manifest_path = case_dir / "RUN_MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["run_wallclock_seconds"] = result["run_wallclock_seconds"]
        manifest["command_records"] = records
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return result
    except Exception as exc:
        return {
            "status": "completed_unparsed",
            "commands": records,
            "statepoint": str(statepoints[-1].relative_to(case_dir)),
            "parser_error": f"{type(exc).__name__}: {exc}",
            "note": "Raw statepoint retained; do not use candidate for ranking until parsed and reviewed.",
            **provenance,
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
    parser.add_argument("--seed-base", type=int, default=620000, help="legacy deterministic seed base; prefer --seed from the preregistered SeedSequence list")
    parser.add_argument("--seed", type=int, help="explicit pseudorandom seed generated from the preregistered NumPy SeedSequence list")
    parser.add_argument("--candidate-ids", nargs="+", help="optional subset of candidate IDs; default runs all six layouts")
    parser.add_argument("--source-profile", choices=tuple(SOURCE_PROFILES), help="legacy explicit initial source box profile")
    parser.add_argument("--source", choices=("good", "bad"), help="good=uniform over the complete fuel region; bad=initial source restricted to one assembly")
    args = parser.parse_args()
    if args.source is not None:
        args.source_profile = "bad_initial_source" if args.source == "bad" else "baseline_all_fuel"
    elif args.source_profile is None:
        args.source_profile = "baseline_all_fuel"
    if args.batches < 2 or args.inactive < 0 or args.inactive >= args.batches or args.particles < 1 or args.threads < 1 or args.seed_base < 0 or (args.seed is not None and args.seed < 1):
        parser.error("require batches >= 2, 0 <= inactive < batches, particles >= 1, threads >= 1, and a positive seed")

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
        "initial_source_profile": args.source_profile,
        "source_mode": args.source or ("bad" if args.source_profile == "bad_initial_source" else "good" if args.source_profile == "baseline_all_fuel" else "custom_profile"),
        "git_commit": git_commit_sha(),
        "settings": {"batches": args.batches, "inactive": args.inactive, "particles": args.particles, "threads": args.threads, "seed_base": args.seed_base, "seed": args.seed, "seed_policy": "explicit NumPy SeedSequence seed when --seed is set; otherwise legacy base plus stable candidate offset"},
        "profile_warning": "Default settings are smoke-test settings only; do not compare to benchmark reference or claim converged physics without a separate convergence study.",
        "mgxs_generation_policy": "The copied upstream materials.py is patched to replace nonstandard log-spaced boundaries with the OECD/NEA C5G7 standard seven-group boundaries [1e-5, 0.0635, 10, 100, 1000, 500000, 1000000, 20000000] eV; the generated MGXS group-structure attribute is audited before transport.",
        "cases": [],
        "nonclaims": [
            "This is a new C5G7 assembly-placement design study, not a mapping of the legacy burnup-state QUBO.",
            "A successful run does not by itself verify the model against the OECD/NEA reference.",
            "Smoke-test results are not benchmark-grade and must not be presented as converged physical evidence.",
        ],
    }
    all_ordered_candidates = sorted(design["candidate_layouts"], key=lambda c: (not c["is_canonical_reference_arrangement"], c["candidate_id"]))
    seed_offsets = {candidate["candidate_id"]: i for i, candidate in enumerate(all_ordered_candidates)}
    if args.candidate_ids:
        requested = set(args.candidate_ids)
        known = {candidate["candidate_id"] for candidate in all_ordered_candidates}
        unknown = sorted(requested - known)
        if unknown:
            parser.error(f"unknown candidate IDs: {unknown}")
        ordered_candidates = [candidate for candidate in all_ordered_candidates if candidate["candidate_id"] in requested]
        if not ordered_candidates:
            parser.error("--candidate-ids must select at least one candidate")
    else:
        ordered_candidates = all_ordered_candidates
    summary["selected_candidate_ids"] = [candidate["candidate_id"] for candidate in ordered_candidates]
    for candidate in ordered_candidates:
        seed = int(args.seed) if args.seed is not None else args.seed_base + seed_offsets[candidate["candidate_id"]]
        case_dir = output / candidate["candidate_id"]
        case_dir.mkdir()
        model_copy = case_dir / "model"
        shutil.copytree(upstream_model, model_copy)
        patch_mgxs_energy_boundaries(model_copy / "materials.py")
        patch_tally_scores(model_copy / "tally.py")
        builder = model_copy / BUILDER_RELATIVE
        patch_builder(builder, candidate["fuel_assembly_layout"], args.batches, args.inactive, args.particles, seed=seed, source_profile=args.source_profile)
        case = {
            "candidate_id": candidate["candidate_id"],
            "seed": seed,
            "initial_source_profile": args.source_profile,
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
                } for other in ordered_candidates if other["candidate_id"] != candidate["candidate_id"] and other["candidate_id"] not in {c["candidate_id"] for c in summary["cases"]})
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
