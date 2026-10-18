#!/usr/bin/env python3
"""Compare six-layout OpenMC P5 results with matched independent S_N pin maps.

This is a code-to-code diagnostic. It does not equate fission-rate tallies with
absolute power and never declares physical feasibility or reactor safety.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, re, statistics
from pathlib import Path
from compare_c5g7_independent_crosscheck import (
    LAYOUTS, collect, sn_map, openmc_map, compare_spatial_maps, sha
)

def read_json(path: Path) -> dict:
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value,dict) else {}
    except (OSError,json.JSONDecodeError):
        return {}

def log_keff(path: Path) -> float | None:
    text=path.read_text(encoding="utf-8",errors="replace")
    m=re.search(r"C5G7\s+k_eff\s+\(this solver\)\s*=\s*([0-9.]+)",text)
    return float(m.group(1)) if m else None

def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--artifacts-root",type=Path,required=True)
    ap.add_argument("--sn-root",type=Path,required=True)
    ap.add_argument("--outdir",type=Path,required=True)
    a=ap.parse_args()
    a.outdir.mkdir(parents=True,exist_ok=True)
    rows=[r for r in collect(a.artifacts_root) if r.get("phase")=="P5"]
    sn_dirs={}
    duplicate_sn=[]
    for mpath in sorted(a.sn_root.rglob("layout_metadata.json")):
        meta=read_json(mpath)
        sig=meta.get("layout_signature")
        if sig not in LAYOUTS:
            continue
        if sig in sn_dirs:
            duplicate_sn.append(sig)
        sn_dirs[sig]=mpath.parent
    issues=[]
    if len(rows)!=18:
        issues.append(f"expected 18 held-out P5 OpenMC records (3/layout), found {len(rows)}")
    if len(sn_dirs)!=6 or set(sn_dirs)!=LAYOUTS:
        issues.append(f"expected one independent S_N artifact per layout; found {sorted(sn_dirs)}")
    if duplicate_sn:
        issues.append(f"duplicate S_N layout artifact metadata: {sorted(set(duplicate_sn))}")
    summaries=[]
    for layout in sorted(LAYOUTS):
        p5=[r for r in rows if r.get("layout")==layout]
        sd=sn_dirs.get(layout)
        item={"layout":layout,"status":"INCOMPLETE","openmc_p5_run_count":len(p5)}
        if len(p5)!=3 or sd is None:
            item["issues"]=[f"need 3 P5 statepoints and one S_N artifact; got P5={len(p5)}, S_N={sd is not None}"]
            summaries.append(item)
            issues.extend([f"{layout}: {q}" for q in item["issues"]])
            continue
        if any(not r.get("statepoint_exists") or not r.get("statepoint_sha256") for r in p5):
            item["issues"]=["one or more OpenMC statepoints or hashes missing"]
            summaries.append(item); issues.extend([f"{layout}: {q}" for q in item["issues"]]); continue
        if any(r.get("raw_hdf5_posthoc_reaudit")!="PASS" for r in p5):
            item["issues"]=["one or more OpenMC raw HDF5 posthoc audits did not pass"]
            summaries.append(item); issues.extend([f"{layout}: {q}" for q in item["issues"]]); continue
        csv_path=sd/"c5g7_pinpower.csv"
        log_path=sd/"sn_solver.log"
        meta_path=sd/"layout_metadata.json"
        if not all(p.is_file() for p in (csv_path,log_path,meta_path)):
            item["issues"]=["independent S_N CSV/log/metadata missing"]
            summaries.append(item); issues.extend([f"{layout}: {q}" for q in item["issues"]]); continue
        try:
            sn_values,fuel_mask,sn_summary=sn_map(csv_path)
            omaps=[openmc_map(Path(r["statepoint"]),fuel_mask) for r in p5]
            metrics=compare_spatial_maps(omaps,sn_values,fuel_mask)
            snk=log_keff(log_path)
            omkeff=[float(r["keff_mean"]) for r in p5]
            if snk is None: raise ValueError("independent S_N k_eff missing from log")
            if not all(math.isfinite(v) for v in omkeff): raise ValueError("non-finite OpenMC k_eff")
            mean_k=statistics.fmean(omkeff)
            item.update({
                "status":"COMPARED_CODE_TO_CODE_NOT_PHYSICAL_VALIDATION",
                "independent_solver":{"keff":snk,"log_sha256":sha(log_path),"pinpower_csv_sha256":sha(csv_path),
                    "solver_source_sha256":read_json(meta_path).get("patched_source_sha256")},
                "openmc_p5":{"keff_values":omkeff,"keff_mean":mean_k,
                    "between_seed_sample_sd":statistics.stdev(omkeff),"seeds":[r.get("seed") for r in p5],
                    "statepoint_sha256":[r.get("statepoint_sha256") for r in p5]},
                "keff_difference_s_n_minus_openmc_pcm":(snk-mean_k)*1e5,
                "sn_fuel_map_summary":sn_summary,
                "spatial_shape_metrics":metrics,
                "interpretation":"Comparable fuel-only bins and a common mask were used. Mesh-integrated fission rate and deterministic normalized pin power are related but not identical; deltas are diagnostic, not safety limits."
            })
        except Exception as e:
            item["issues"]=[f"{type(e).__name__}: {e}"]
            issues.extend([f"{layout}: {q}" for q in item["issues"]])
        summaries.append(item)
    status=("COMPLETE_CROSS_CODE_COMPARISON_NOT_VALIDATION"
            if not issues and len(summaries)==6 and all(x.get("status")=="COMPARED_CODE_TO_CODE_NOT_PHYSICAL_VALIDATION" for x in summaries)
            else "INCOMPLETE_OR_REVIEW_REQUIRED")
    report={
        "schema_version":"1.0",
        "protocol":"six-layout OpenMC P5 versus independent S_N fuel-only spatial cross-check",
        "status":status,
        "source_campaign_run_id":39098770358,
        "independent_solver_run_id":39104899024,
        "layout_count":len(summaries),
        "integrity":{"status":"PASS" if not issues else "INCOMPLETE_OR_FAIL","issue_count":len(issues),"issues":issues},
        "layouts":summaries,
        "nonclaims":[
            "This is independent code-to-code comparison, not experimental validation.",
            "The published canonical C5G7 k_eff reference is not an acceptance threshold for noncanonical layouts.",
            "No result establishes reactor safety, absolute power, or universal physical superiority.",
            "The S_N solver uses a Cartesian digital-disk approximation; geometry/discretization differences need interpretation."
        ]
    }
    (a.outdir/"six_layout_openmc_sn_crosscheck.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    with (a.outdir/"six_layout_openmc_sn_crosscheck.csv").open("w",newline="",encoding="utf-8") as f:
        fields=["layout","status","openmc_p5_run_count","openmc_keff_mean","s_n_keff","keff_difference_s_n_minus_openmc_pcm",
                "rms_relative_error_percent","mean_absolute_relative_error_percent","max_absolute_relative_error_percent",
                "comparable_fuel_pin_count","excluded_non_fuel_mesh_bins"]
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for x in summaries:
            m=x.get("spatial_shape_metrics",{})
            ok=x.get("openmc_p5",{})
            sn=x.get("independent_solver",{})
            w.writerow({"layout":x.get("layout"),"status":x.get("status"),"openmc_p5_run_count":x.get("openmc_p5_run_count"),
                "openmc_keff_mean":ok.get("keff_mean"),"s_n_keff":sn.get("keff"),
                "keff_difference_s_n_minus_openmc_pcm":x.get("keff_difference_s_n_minus_openmc_pcm"),
                "rms_relative_error_percent":m.get("rms_relative_error_percent"),
                "mean_absolute_relative_error_percent":m.get("mean_absolute_relative_error_percent"),
                "max_absolute_relative_error_percent":m.get("max_absolute_relative_error_percent"),
                "comparable_fuel_pin_count":m.get("comparable_fuel_pin_count"),
                "excluded_non_fuel_mesh_bins":m.get("excluded_non_fuel_mesh_bins")})
    print(json.dumps({"status":status,"layout_count":len(summaries),"issue_count":len(issues),"outdir":str(a.outdir)},indent=2))
    return 0 if status=="COMPLETE_CROSS_CODE_COMPARISON_NOT_VALIDATION" else 2

if __name__=="__main__":
    raise SystemExit(main())
