#!/usr/bin/env python3
"""Verify recoverable C5G7 mesh-tally evidence in an archived study ZIP."""
from __future__ import annotations
import argparse, hashlib, io, json, math, zipfile
from pathlib import Path

EXPECTED_ARCHIVE_SHA256 = "7a5e2a3daf87d0141ddc5e0922b88c4c0e2c3cb91af67ca6a2f50b6535e9862b"
LAYOUTS = ("MUMU", "MMUU", "MUUM", "UMMU", "UUMM", "UMUM")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".ppm", ".tif", ".tiff"}
PLOT_DATA_SUFFIXES = {".vtk", ".vti", ".vtp", ".vtu", ".vtm", ".xdmf"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_value(value) -> str:
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").rstrip("\x00")
    return str(value)


def audit(archive_path: Path, expected_hash: str | None = None) -> dict:
    try:
        import h5py
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("h5py and numpy are required for HDF5 inspection") from exc
    raw = archive_path.read_bytes()
    outer_hash = sha256(raw)
    if expected_hash and outer_hash.lower() != expected_hash.lower():
        raise ValueError(f"Archive SHA-256 mismatch: expected {expected_hash}, got {outer_hash}")
    candidates = []
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        for layout in LAYOUTS:
            suffix = f"c5g7-2x2-{layout}/model/2d/statepoint.5000.h5"
            matches = [n for n in names if n.endswith(suffix)]
            if len(matches) != 1:
                raise ValueError(f"Expected one statepoint for {layout}, found {matches}")
            member = matches[0]
            case_path = member.removesuffix("model/2d/statepoint.5000.h5") + "CASE_RESULT.json"
            case = json.loads(z.read(case_path))
            state_bytes = z.read(member)
            state_hash = sha256(state_bytes)
            declared_hash = (case.get("output_hashes_after_run") or {}).get("model/2d/statepoint.5000.h5")
            if case.get("status") != "completed" or state_hash != declared_hash:
                raise ValueError(f"Run status/hash verification failed for {layout}")
            with h5py.File(io.BytesIO(state_bytes), "r") as h5:
                h5version = ".".join(str(int(x)) for x in np.asarray(h5.attrs["openmc_version"]).reshape(-1))
                n_batches, n_particles, n_inactive = int(h5["n_batches"][()]), int(h5["n_particles"][()]), int(h5["n_inactive"][()])
                seed = int(h5["seed"][()])
                tally = h5["tallies/tally 1"]
                values = np.asarray(tally["results"][()], dtype=float)
                scores = [text_value(v) for v in np.asarray(tally["score_bins"][()]).reshape(-1)]
                realizations = int(tally["n_realizations"][()])
                filter_ids = [int(v) for v in np.asarray(tally["filters"][()]).reshape(-1)]
                linked, filter_records = [], []
                for fid in filter_ids:
                    f = h5[f"tallies/filters/filter {fid}"]
                    ftype = text_value(f["type"][()]).lower()
                    bins = np.asarray(f["bins"][()]).reshape(-1).astype(int).tolist() if "bins" in f else []
                    filter_records.append({"id": fid, "type": ftype, "bins": bins})
                    if ftype == "mesh":
                        for mesh_id in bins:
                            mesh = h5.get(f"tallies/meshes/mesh {mesh_id}")
                            if mesh is None:
                                raise ValueError(f"Filter {fid} references missing mesh {mesh_id}")
                            dims = [int(v) for v in np.asarray(mesh["dimension"][()]).reshape(-1)]
                            if math.prod(dims) == values.shape[0] and len(dims) == 3 and dims[2] == 1:
                                linked.append({"id": mesh_id, "dimensions": dims})
                if n_batches != 5000 or n_particles != 5000 or n_inactive != 500 or int(case.get("seed", -1)) != seed:
                    raise ValueError(f"Unexpected run settings or seed for {layout}")
                if values.shape != (2601, 3, 2) or realizations != 4500 or scores != ["flux", "fission", "nu-fission"] or not linked:
                    raise ValueError(f"Invalid/incompatible mesh tally for {layout}: shape={values.shape}, scores={scores}, linked={linked}")
                sums, sums_sq = values[:, :, 0], values[:, :, 1]
                means = sums / realizations
                variance = np.maximum((sums_sq - sums * sums / realizations) / (realizations - 1), 0.0)
                se = np.sqrt(variance / realizations)
                if not np.isfinite(means).all() or not np.isfinite(se).all():
                    raise ValueError(f"Non-finite mean or standard error in {layout}")
                candidates.append({
                    "candidate_id": case.get("candidate_id"), "layout_signature": layout, "status": case["status"],
                    "seed": seed, "n_batches": n_batches, "n_particles_per_batch": n_particles,
                    "n_inactive": n_inactive, "n_realizations": realizations, "openmc_version": h5version,
                    "statepoint_member": member, "statepoint_bytes": len(state_bytes),
                    "statepoint_sha256": state_hash, "case_result_sha256": declared_hash,
                    "tally_shape": list(values.shape), "scores": scores, "filter_ids": filter_ids,
                    "filters": filter_records, "compatible_meshes": linked,
                    "score_range": {scores[i]: {"min_mean": float(means[:, i].min()), "max_mean": float(means[:, i].max()), "max_standard_error": float(se[:, i].max())} for i in range(len(scores))},
                })
        image_files = [n for n in names if Path(n).suffix.lower() in IMAGE_SUFFIXES]
        plot_data_files = [n for n in names if Path(n).suffix.lower() in PLOT_DATA_SUFFIXES]
        plots_xml_files = [n for n in names if Path(n).name.lower() == "plots.xml"]
    return {
        "audit_date": "2026-10-13", "source_archive": {"filename": archive_path.name, "bytes": len(raw), "sha256": outer_hash, "matches_known_c5g7_study_640000": outer_hash == EXPECTED_ARCHIVE_SHA256},
        "summary": {"statepoints": len(candidates), "all_runs_completed": all(c["status"] == "completed" for c in candidates), "all_statepoint_hashes_match_case_result": all(c["statepoint_sha256"] == c["case_result_sha256"] for c in candidates), "unique_statepoint_hashes": len({c["statepoint_sha256"] for c in candidates}), "all_have_linked_51x51_mesh": all(c["compatible_meshes"][0]["dimensions"] == [51, 51, 1] for c in candidates)},
        "plot_inventory": {"plots_xml_count": len(plots_xml_files), "rendered_image_count": len(image_files), "rendered_vtk_family_count": len(plot_data_files), "image_members": image_files, "vtk_family_members": plot_data_files},
        "root_cause": "OpenMC 0.16 mesh filter stores mesh ID in dataset 'bins' (for this artifact: [1]). The current CB-PFR parser looks only for datasets named 'mesh' or 'mesh_id', leaves mesh_id unset, and rejects the compatible tally.",
        "source_boundary": "This is the GitHub Actions smoke-study artifact, not the user's separate local 20,000-batch OpenMC_HDF5_Evidence_2026-10-11.zip archive.",
        "scientific_boundary": "5,000 batches, 5,000 particles per batch, 500 inactive, 4,500 active tally realizations. Source artifact says independent validation is still needed; not benchmark-grade or convergence-certified.",
        "candidates": candidates,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", required=True, type=Path)
    p.add_argument("--expected-sha256", default=None)
    p.add_argument("--json-output", type=Path, default=None)
    args = p.parse_args()
    data = audit(args.archive, args.expected_sha256)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"source_archive": data["source_archive"], "summary": data["summary"], "plot_inventory": data["plot_inventory"], "root_cause": data["root_cause"]}, indent=2))


if __name__ == "__main__":
    main()
