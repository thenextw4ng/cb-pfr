#!/usr/bin/env python3
"""Verify a ZIP archive's integrity and write a SHA-256 member inventory."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit_archive(path: Path, *, require_statepoint: bool = False) -> dict:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"archive not found: {path}")
    archive_hash = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            archive_hash.update(chunk)

    members = []
    with zipfile.ZipFile(path) as archive:
        corrupt = archive.testzip()
        if corrupt is not None:
            raise ValueError(f"ZIP CRC failure in member: {corrupt}")
        for info in sorted(archive.infolist(), key=lambda item: item.filename):
            name = info.filename
            member_path = PurePosixPath(name)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValueError(f"unsafe archive member path: {name}")
            if info.is_dir():
                continue
            digest = hashlib.sha256()
            with archive.open(info, "r") as member:
                for chunk in iter(lambda: member.read(1024 * 1024), b""):
                    digest.update(chunk)
            members.append({
                "path": name,
                "size_bytes": info.file_size,
                "sha256": digest.hexdigest(),
                "suffix": member_path.suffix.lower(),
            })

    statepoints = [item["path"] for item in members
                   if PurePosixPath(item["path"]).name.startswith("statepoint")
                   and PurePosixPath(item["path"]).suffix.lower() == ".h5"]
    hdf5 = [item["path"] for item in members if item["suffix"] in {".h5", ".hdf5"}]
    if require_statepoint and not statepoints:
        raise ValueError("archive contains no statepoint*.h5 file")

    return {
        "schema_version": "1.0",
        "archive_path": str(path),
        "archive_name": path.name,
        "archive_size_bytes": path.stat().st_size,
        "archive_sha256": archive_hash.hexdigest(),
        "zip_integrity": "passed",
        "member_count": len(members),
        "hdf5_member_count": len(hdf5),
        "statepoint_member_count": len(statepoints),
        "statepoint_members": statepoints,
        "members": members,
        "interpretation": (
            "Archive integrity and byte hashes only; this does not parse HDF5 semantics, "
            "verify simulation success, match candidate IDs, or validate reactor physics."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--require-statepoint", action="store_true")
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"output already exists: {args.out}")
    try:
        result = audit_archive(args.archive, require_statepoint=args.require_statepoint)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "archive": result["archive_name"],
        "integrity": result["zip_integrity"],
        "members": result["member_count"],
        "hdf5_members": result["hdf5_member_count"],
        "statepoints": result["statepoint_member_count"],
        "sha256": result["archive_sha256"],
        "audit_json": str(args.out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
