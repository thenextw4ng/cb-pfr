#!/usr/bin/env python3
"""Install the latest hash-verified production C5G7 axial tally artifact.

Only four small evidence files are installed. The OpenMC statepoint itself is not
committed or downloaded by the workstation installer.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import tempfile
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPOSITORY = "thenextw4ng/cb-pfr"
WORKFLOW_FILE = "c5g7-axial-3d.yml"
API_ROOT = f"https://api.github.com/repos/{REPOSITORY}"
ARTIFACT_PREFIX = "cbpfr-axial-3d-c5g7-2x2-UMMU-production-"
REQUIRED_MEMBERS = {
    "model/3d/axial-3d-export/axial_tally_3d.npz": "axial_tally_3d.npz",
    "model/3d/axial-3d-export/AXIAL_3D_STATEPOINT_SUMMARY.json": "AXIAL_3D_STATEPOINT_SUMMARY.json",
    "AXIAL_3D_INPUT_AUDIT.json": "AXIAL_3D_INPUT_AUDIT.json",
    "AXIAL_3D_INPUT_MANIFEST.json": "AXIAL_3D_INPUT_MANIFEST.json",
}
USER_AGENT = "CB-PFR-Scientific-Workstation/1.0"


class AxialArtifactError(RuntimeError):
    """The latest production artifact could not be safely installed."""


def _get_bytes(url: str, timeout: float = 12.0) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _get_json(url: str) -> dict:
    try:
        payload = json.loads(_get_bytes(url).decode("utf-8"))
    except (OSError, urllib.error.URLError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AxialArtifactError(f"GitHub API request failed for {url}: {exc}") from exc
    if not isinstance(payload, dict):
        raise AxialArtifactError(f"GitHub API returned a non-object response for {url}.")
    return payload


def find_latest_production_artifact() -> dict:
    """Find a successful, non-expired UMMU production artifact from this workflow."""
    workflow_url = f"{API_ROOT}/actions/workflows/{WORKFLOW_FILE}/runs?per_page=25"
    runs = _get_json(workflow_url).get("workflow_runs", [])
    if not isinstance(runs, list):
        raise AxialArtifactError("GitHub workflow response has no valid workflow_runs list.")

    for run in runs:
        if not isinstance(run, dict) or run.get("conclusion") != "success":
            continue
        run_id = run.get("id")
        if not isinstance(run_id, int):
            continue
        artifacts_payload = _get_json(f"{API_ROOT}/actions/runs/{run_id}/artifacts")
        artifacts = artifacts_payload.get("artifacts", [])
        if not isinstance(artifacts, list):
            continue
        matches = [
            item for item in artifacts
            if isinstance(item, dict)
            and str(item.get("name", "")).startswith(ARTIFACT_PREFIX)
            and item.get("expired") is False
            and isinstance(item.get("id"), int)
        ]
        if matches:
            artifact = matches[0]
            return {
                "artifact_id": artifact["id"],
                "artifact_name": str(artifact["name"]),
                "artifact_url": f"{API_ROOT}/actions/artifacts/{artifact['id']}/zip",
                "run_id": run_id,
                "run_url": str(run.get("html_url", "")),
                "created_at": str(artifact.get("created_at", run.get("created_at", ""))),
                "expires_at": str(artifact.get("expires_at", "")),
            }
    raise AxialArtifactError(
        "No successful, non-expired UMMU production artifact was found in the latest "
        f"25 runs of {WORKFLOW_FILE}. A smoke-only artifact is deliberately not accepted."
    )


def _validated_members(archive_bytes: bytes, artifact_name: str) -> dict[str, bytes]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
    except (zipfile.BadZipFile, OSError) as exc:
        raise AxialArtifactError(f"Downloaded artifact is not a valid ZIP: {exc}") from exc
    with archive:
        names = set(archive.namelist())
        missing = set(REQUIRED_MEMBERS) - names
        if missing:
            raise AxialArtifactError(
                f"Production artifact {artifact_name} is missing required evidence members: "
                + ", ".join(sorted(missing))
            )
        return {
            output_name: archive.read(member)
            for member, output_name in REQUIRED_MEMBERS.items()
        }


def validate_evidence_files(files: dict[str, bytes]) -> dict:
    """Fail closed on an unexpected run, mesh, schema, or altered tally export."""
    try:
        summary = json.loads(files["AXIAL_3D_STATEPOINT_SUMMARY.json"].decode("utf-8"))
        audit = json.loads(files["AXIAL_3D_INPUT_AUDIT.json"].decode("utf-8"))
        manifest = json.loads(files["AXIAL_3D_INPUT_MANIFEST.json"].decode("utf-8"))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AxialArtifactError(f"Production evidence JSON is missing or invalid: {exc}") from exc

    if summary.get("schema_version") != 1 or summary.get("status") != "3d_openmc_statepoint_mesh_exported":
        raise AxialArtifactError("Artifact summary does not identify a successfully exported OpenMC 3-D statepoint.")
    if audit.get("candidate_id") != "c5g7-2x2-UMMU":
        raise AxialArtifactError("Only the audited canonical UMMU geometry is accepted for the workstation volume.")
    if audit.get("status") != "generated_3d_inputs_passed_structural_audit":
        raise AxialArtifactError("Axial input audit status is missing or not accepted.")
    if manifest.get("candidate_id") != "c5g7-2x2-UMMU" or manifest.get("layout_signature") != "UMMU":
        raise AxialArtifactError("Axial input manifest does not match canonical UMMU.")
    if manifest.get("source", {}).get("archive_sha256") != "7a5e2a3daf87d0141ddc5e0922b88c4c0e2c3cb91af67ca6a2f50b6535e9862b":
        raise AxialArtifactError("Axial manifest refers to an unexpected source archive checksum.")

    statepoint = summary.get("statepoint", {})
    mesh = summary.get("mesh", {})
    if int(statepoint.get("n_batches", 0)) < 7000 or int(statepoint.get("n_inactive", 0)) < 500:
        raise AxialArtifactError("Artifact is not from the expected high-budget production profile.")
    if int(statepoint.get("n_realizations", 0)) < 6500 or int(statepoint.get("n_particles", 0)) < 10000:
        raise AxialArtifactError("Artifact statepoint budget does not match the expected production run.")
    if mesh.get("dimension_xyz") != [51, 51, 30] or mesh.get("array_shape") != [30, 51, 51, 3]:
        raise AxialArtifactError("Artifact mesh is not the expected real 51 × 51 × 30, three-score tally.")
    if mesh.get("bin_count") != 78030:
        raise AxialArtifactError("Artifact mesh bin count does not match 51 × 51 × 30.")
    if not {"flux", "fission", "nu-fission"}.issubset(set(summary.get("scores", []))):
        raise AxialArtifactError("Artifact summary is missing required tally scores.")

    npz_bytes = files["axial_tally_3d.npz"]
    npz_meta = summary.get("npz", {})
    actual_sha = hashlib.sha256(npz_bytes).hexdigest()
    if len(npz_bytes) != int(npz_meta.get("bytes", -1)):
        raise AxialArtifactError("Axial NPZ byte count does not match the source summary.")
    if actual_sha != npz_meta.get("sha256"):
        raise AxialArtifactError("Axial NPZ SHA-256 does not match the source summary.")
    try:
        with zipfile.ZipFile(io.BytesIO(npz_bytes)) as npz_archive:
            npz_members = set(npz_archive.namelist())
    except (zipfile.BadZipFile, OSError) as exc:
        raise AxialArtifactError(f"Axial tally export is not a valid NumPy NPZ archive: {exc}") from exc
    required_arrays = {
        "mean.npy", "standard_error.npy", "relative_error_percent.npy", "score_names.npy",
        "x_centers_cm.npy", "y_centers_cm.npy", "z_centers_cm.npy",
    }
    if not required_arrays.issubset(npz_members):
        raise AxialArtifactError(
            "Axial NPZ is missing required arrays: " + ", ".join(sorted(required_arrays - npz_members))
        )
    return {
        "summary": summary,
        "audit": audit,
        "manifest": manifest,
        "npz_sha256": actual_sha,
        "npz_bytes": len(npz_bytes),
    }


def install_latest_production_axial_tally(target_npz: str | Path) -> dict:
    """Download, validate, and atomically install the latest production volume evidence."""
    target_npz = Path(target_npz).expanduser().resolve()
    artifact = find_latest_production_artifact()
    try:
        archive_bytes = _get_bytes(artifact["artifact_url"], timeout=40.0)
    except (OSError, urllib.error.URLError) as exc:
        raise AxialArtifactError(f"Could not download production evidence artifact: {exc}") from exc

    files = _validated_members(archive_bytes, artifact["artifact_name"])
    validation = validate_evidence_files(files)
    target_dir = target_npz.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    provenance = {
        "schema_version": 1,
        "installed_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository": REPOSITORY,
        "workflow_file": WORKFLOW_FILE,
        "workflow_run_id": artifact["run_id"],
        "workflow_run_url": artifact["run_url"],
        "artifact_id": artifact["artifact_id"],
        "artifact_name": artifact["artifact_name"],
        "artifact_url": artifact["artifact_url"],
        "artifact_zip_sha256": hashlib.sha256(archive_bytes).hexdigest(),
        "axial_tally_npz_sha256": validation["npz_sha256"],
        "axial_tally_npz_bytes": validation["npz_bytes"],
        "mesh_dimension_xyz": validation["summary"]["mesh"]["dimension_xyz"],
        "n_realizations": validation["summary"]["statepoint"]["n_realizations"],
        "note": "Source-normalized OpenMC Monte Carlo tally, not absolute reactor power or a safety result.",
    }
    files["AXIAL_3D_PROVENANCE.json"] = json.dumps(provenance, indent=2).encode("utf-8") + b"\n"
    files["AXIAL_3D_STATEPOINT_SUMMARY.json"] = json.dumps(validation["summary"], indent=2).encode("utf-8") + b"\n"
    files["AXIAL_3D_INPUT_AUDIT.json"] = json.dumps(validation["audit"], indent=2).encode("utf-8") + b"\n"
    files["AXIAL_3D_INPUT_MANIFEST.json"] = json.dumps(validation["manifest"], indent=2).encode("utf-8") + b"\n"

    target_names = dict(files)
    target_names["axial_tally_3d.npz"] = files.pop("axial_tally_3d.npz")
    installed = []
    temporary = []
    try:
        for filename, content in target_names.items():
            fd, temp_name = tempfile.mkstemp(prefix=".cbpfr-axial-", dir=target_dir)
            temporary.append(temp_name)
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
        # All files have been written successfully; replace each target only after validation.
        for filename, temp_name in zip(target_names, temporary):
            os.replace(temp_name, target_dir / filename)
            installed.append(str(target_dir / filename))
        temporary.clear()
    finally:
        for temp_name in temporary:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass
    return {**provenance, "installed_paths": installed}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="evidence/cbpfr_axial_3d/axial_tally_3d.npz")
    args = parser.parse_args()
    result = install_latest_production_axial_tally(args.target)
    print(json.dumps(result, indent=2))
