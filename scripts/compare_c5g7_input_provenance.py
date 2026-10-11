#!/usr/bin/env python3
"""Compare production C5G7 XML inputs with regenerated canonical smoke inputs."""
from __future__ import annotations
import argparse, difflib, hashlib, json
from pathlib import Path
import xml.etree.ElementTree as ET


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_xml(path: Path, *, normalize_cross_sections_path: bool = False) -> str:
    root = ET.parse(path).getroot()
    if normalize_cross_sections_path:
        for node in root.findall("cross_sections"):
            node.text = "<cross-sections-path>"
    for element in root.iter():
        element.attrib = dict(sorted(element.attrib.items()))
        if element.text is not None and not element.text.strip():
            element.text = None
        if element.tail is not None and not element.tail.strip():
            element.tail = None
    return ET.tostring(root, encoding="unicode", short_empty_elements=True)


def compare_file(name: str, production_root: Path, candidate_root: Path) -> dict:
    left, right = production_root / name, candidate_root / name
    if not left.is_file() or not right.is_file():
        return {"file": name, "status": "MISSING", "production_exists": left.is_file(),
                "candidate_exists": right.is_file()}
    a, b = canonical_xml(left), canonical_xml(right)
    diff = list(difflib.unified_diff(a.splitlines(), b.splitlines(),
                                     fromfile=f"production/{name}", tofile=f"candidate/{name}",
                                     lineterm=""))
    result = {
        "file": name,
        "status": "IDENTICAL_AFTER_ATTRIBUTE_ORDER_NORMALIZATION" if a == b else "DIFFERENT",
        "production_byte_sha256": sha(left),
        "candidate_byte_sha256": sha(right),
        "production_canonical_sha256": hashlib.sha256(a.encode()).hexdigest(),
        "candidate_canonical_sha256": hashlib.sha256(b.encode()).hexdigest(),
        "canonical_xml_equal": a == b,
        "diff_lines": diff[:300],
        "diff_truncated": len(diff) > 300,
    }
    if name == "materials.xml":
        left_def = canonical_xml(left, normalize_cross_sections_path=True)
        right_def = canonical_xml(right, normalize_cross_sections_path=True)
        result["material_definitions_equal_ignoring_cross_sections_path"] = left_def == right_def
        result["production_cross_sections_path"] = ET.parse(left).getroot().findtext("cross_sections")
        result["candidate_cross_sections_path"] = ET.parse(right).getroot().findtext("cross_sections")
        result["material_definition_sha256_production"] = hashlib.sha256(left_def.encode()).hexdigest()
        result["material_definition_sha256_candidate"] = hashlib.sha256(right_def.encode()).hexdigest()
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--production-root", required=True, type=Path,
                   help="directory containing the recorded production statepoint and XML files")
    p.add_argument("--candidate-root", required=True, type=Path,
                   help="directory containing regenerated canonical candidate XML files")
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    if a.out.exists():
        p.error(f"refusing to overwrite existing output: {a.out}")
    if not (a.production_root / "statepoint.20000.h5").is_file():
        p.error("production root must be the directory containing statepoint.20000.h5")
    names = ("geometry.xml", "materials.xml", "settings.xml", "tallies.xml", "plots.xml")
    results = [compare_file(name, a.production_root, a.candidate_root) for name in names]
    model_files = [r for r in results if r["file"] in ("geometry.xml", "materials.xml", "tallies.xml")]
    by_name = {r["file"]: r for r in results}
    model_definitions_match = (
        by_name["geometry.xml"].get("canonical_xml_equal") is True
        and by_name["materials.xml"].get("material_definitions_equal_ignoring_cross_sections_path") is True
        and by_name["tallies.xml"].get("canonical_xml_equal") is True
    )
    production_mgxs_exists = (a.production_root / "mgxs.h5").is_file()
    candidate_mgxs_exists = (a.candidate_root / "mgxs.h5").is_file()
    report = {
        "schema_version": "1.0",
        "status": "INPUTS_DIFFER" if any(r["status"] in ("DIFFERENT", "MISSING") for r in model_files) else "MODEL_XML_MATCH",
        "model_definitions_match_ignoring_cross_sections_path": model_definitions_match,
        "production_mgxs_file_available_for_direct_hash": production_mgxs_exists,
        "candidate_mgxs_file_available_for_direct_hash": candidate_mgxs_exists,
        "full_nuclear_data_identity_verified": False,
        "production_root": str(a.production_root),
        "candidate_root": str(a.candidate_root),
        "comparison_method": "XML attribute-order normalization; child order and all element values are preserved",
        "files": results,
        "interpretation": (
            "This is a structural input comparison, not proof that nuclear data or the selected benchmark case is correct. "
            "Settings differences may be intentional because compute budgets and seeds differ. Any materials.xml or geometry.xml "
            "difference must be reviewed before numerical benchmark acceptance."
        ),
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"],
                      "files": {r["file"]: r["status"] for r in results},
                      "output": str(a.out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
