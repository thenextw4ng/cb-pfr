#!/usr/bin/env python3
"""Compare HDF5 file bytes, dataset payloads, and metadata separately."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import h5py
import numpy as np


def normalize(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").rstrip("\x00")
    if isinstance(value, np.ndarray):
        return normalize(value.tolist())
    if isinstance(value, np.generic):
        return normalize(value.item())
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, tuple):
        return [normalize(item) for item in value]
    if isinstance(value, float):
        return value
    if isinstance(value, (int, bool, str)) or value is None:
        return value
    return repr(value)


def digest_json(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def inspect(path: Path):
    objects, datasets, attrs = [], [], []
    dataset_count = group_count = 0
    with h5py.File(path, "r") as handle:
        def add(name, obj):
            nonlocal dataset_count, group_count
            path_name = name or "."
            attr_map = {key: normalize(value) for key, value in sorted(obj.attrs.items())}
            for key, value in attr_map.items():
                attrs.append({"path": path_name, "attribute": key, "value": value})
            if isinstance(obj, h5py.Dataset):
                dataset_count += 1
                value = obj[()]
                arr = np.asarray(value)
                if arr.dtype.kind in "biufc":
                    dtype = arr.dtype.newbyteorder("<")
                    canonical = np.ascontiguousarray(arr.astype(dtype, copy=False))
                    data = {"shape": list(arr.shape), "dtype": dtype.str,
                            "payload_sha256": hashlib.sha256(canonical.tobytes(order="C")).hexdigest()}
                else:
                    data = {"shape": list(arr.shape), "dtype": str(arr.dtype),
                            "normalized": normalize(value)}
                datasets.append({"path": path_name, **data})
                objects.append({"path": path_name, "kind": "dataset", "attrs": attr_map, "data": data})
            else:
                group_count += 1
                objects.append({"path": path_name, "kind": "group", "attrs": attr_map})
        add(".", handle)
        handle.visititems(add)
    objects.sort(key=lambda item: item["path"])
    datasets.sort(key=lambda item: item["path"])
    attrs.sort(key=lambda item: (item["path"], item["attribute"]))
    return {
        "path": str(path),
        "byte_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "full_semantic_sha256": digest_json(objects),
        "dataset_content_sha256": digest_json(datasets),
        "hdf5_object_count": len(objects),
        "dataset_count": dataset_count,
        "group_count": group_count,
        "attribute_count": len(attrs),
        "datasets": datasets,
        "attributes": attrs,
        "file_size_bytes": path.stat().st_size,
    }


def compare(left, right):
    left_attrs = {(x["path"], x["attribute"]): x["value"] for x in left["attributes"]}
    right_attrs = {(x["path"], x["attribute"]): x["value"] for x in right["attributes"]}
    attr_diffs = []
    for key in sorted(set(left_attrs) | set(right_attrs)):
        if left_attrs.get(key) != right_attrs.get(key):
            attr_diffs.append({"path": key[0], "attribute": key[1],
                               "left": left_attrs.get(key), "right": right_attrs.get(key)})
    left_data = {x["path"]: x for x in left["datasets"]}
    right_data = {x["path"]: x for x in right["datasets"]}
    data_diffs = []
    for key in sorted(set(left_data) | set(right_data)):
        if left_data.get(key) != right_data.get(key):
            data_diffs.append({"path": key, "left": left_data.get(key), "right": right_data.get(key)})
    return {
        "dataset_content_equal": left["dataset_content_sha256"] == right["dataset_content_sha256"] and not data_diffs,
        "full_semantic_equal": left["full_semantic_sha256"] == right["full_semantic_sha256"] and not attr_diffs,
        "dataset_differences": data_diffs,
        "attribute_differences": attr_diffs,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--files", nargs="+", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--require-datasets-identical", action="store_true")
    parser.add_argument("--require-fully-identical", action="store_true")
    args = parser.parse_args()
    results = [inspect(path) for path in args.files]
    comparisons = []
    for i, left in enumerate(results):
        for right in results[i + 1:]:
            item = compare(left, right)
            item["left"] = left["path"]
            item["right"] = right["path"]
            comparisons.append(item)
    dataset_equal = all(item["dataset_content_equal"] for item in comparisons)
    fully_equal = all(item["full_semantic_equal"] for item in comparisons)
    status = "PASS"
    if args.require_datasets_identical and not dataset_equal:
        status = "FAIL"
    if args.require_fully_identical and not fully_equal:
        status = "FAIL"
    report = {
        "schema_version": "1.0", "status": status,
        "dataset_content_equal": dataset_equal, "full_semantic_equal": fully_equal,
        "files": [{key: value for key, value in item.items() if key not in ("datasets", "attributes")}
                  for item in results],
        "comparisons": comparisons,
    }
    output = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.out:
        if args.out.exists():
            parser.error(f"output already exists: {args.out}")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
