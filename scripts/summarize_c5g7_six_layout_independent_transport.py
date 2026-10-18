#!/usr/bin/env python3
"""Summarize six independent C5G7 S_N transport runs without overstating acceptance."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, re, statistics
from pathlib import Path

EXPECTED = {"MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM"}
COMMIT = "db421c969ee2de83e2d2ae2b14bda368567b558d"

def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def parse_sig_dir(d: Path) -> dict:
    meta_path=d/"layout_metadata.json"
    log_path=d/"sn_solver.log"
    csv_path=d/"c5g7_pinpower.csv"
    issues=[]
    if not meta_path.is_file() or not log_path.is_file() or not csv_path.is_file():
        return {"layout":d.name,"status":"INCOMPLETE","issues":["metadata/log/pinpower file missing"]}
    meta=json.loads(meta_path.read_text())
    log=log_path.read_text(errors="replace")
    def match(pattern):
        m=re.search(pattern,log)
        return float(m.group(1)) if m else None
    k=match(r"C5G7\s+k_eff\s+\(this solver\)\s*=\s*([0-9.]+)")
    pmax_log=match(r"Pin power:\s+fuel pins=\s*\d+\s+max=\s*([0-9.]+)")
    pmin_log=match(r"Pin power:\s+fuel pins=\s*\d+\s+max=\s*[0-9.]+\s+min=\s*([0-9.]+)")
    if meta.get("upstream_commit") != COMMIT: issues.append("unexpected upstream commit")
    if meta.get("layout_signature") not in EXPECTED: issues.append("unexpected layout signature")
    if k is None or pmax_log is None or pmin_log is None: issues.append("key metric absent from solver log")
    assembly_sums={str(i):0.0 for i in range(1,5)}
    fuel_values_raw=[]
    seen_coordinates=set()
    n_block_bins=0
    n_instrument=0
    n_zero_guide=0
    with csv_path.open(newline="",encoding="utf-8") as f:
        reader=csv.DictReader(f)
        required={"pc","pr","assembly","local_row","local_col","norm_power"}
        if not required.issubset(set(reader.fieldnames or [])):
            issues.append(f"unexpected pin-power CSV schema; expected {sorted(required)}")
        else:
            for row in reader:
                x, y = int(row["pc"]), int(row["pr"])
                if not (1 <= x <= 34 and 18 <= y <= 51):
                    continue
                key=(x,y)
                if key in seen_coordinates:
                    issues.append(f"duplicate pin-power coordinate {key}")
                    continue
                seen_coordinates.add(key)
                n_block_bins += 1
                lr, lc = int(row["local_row"]), int(row["local_col"])
                if (lr,lc) != ((y-1)%17+1, (x-1)%17+1):
                    issues.append(f"local pin coordinate mismatch at {key}: CSV={(lr,lc)}")
                value=float(row["norm_power"])
                if not math.isfinite(value) or value < 0:
                    issues.append(f"invalid pin power at coordinate {key}: {value}")
                    continue
                aidx=str(int(row["assembly"]))
                is_instrument=(lr==9 and lc==9)
                if is_instrument:
                    n_instrument += 1
                    if value <= 0:
                        issues.append(f"central instrument tube expected trace positive fission at {key}")
                    continue
                if aidx not in assembly_sums:
                    if value > 0:
                        issues.append(f"positive power assigned to unknown assembly {aidx} at {key}")
                    continue
                if value > 0:
                    fuel_values_raw.append(value)
                    assembly_sums[aidx]+=value
                else:
                    n_zero_guide += 1
    if n_block_bins != 1156:
        issues.append(f"expected 1156 unique bins in 34x34 block, found {n_block_bins}")
    if len(fuel_values_raw) != 1056:
        issues.append(f"expected 1056 true fuel-pin bins, found {len(fuel_values_raw)}")
    if n_instrument != 4:
        issues.append(f"expected four central instrument-tube bins, found {n_instrument}")
    if n_zero_guide != 96:
        issues.append(f"expected 96 zero-power guide-tube bins, found {n_zero_guide}")
    if not fuel_values_raw:
        issues.append("no positive true fuel-pin powers found in CSV")
    fuel_mean=statistics.fmean(fuel_values_raw) if fuel_values_raw else math.nan
    if not math.isfinite(fuel_mean) or fuel_mean <= 0:
        issues.append("true fuel-pin normalization mean is not positive and finite")
    fuel_values_norm=[v/fuel_mean for v in fuel_values_raw] if math.isfinite(fuel_mean) and fuel_mean>0 else []
    pmax_raw=max(fuel_values_raw) if fuel_values_raw else None
    pmin_raw=min(fuel_values_raw) if fuel_values_raw else None
    pmax_norm=max(fuel_values_norm) if fuel_values_norm else None
    pmin_norm=min(fuel_values_norm) if fuel_values_norm else None
    # Compare the CSV raw maximum with the solver's rounded console maximum.
    # The console minimum is over all bins and prints zero because guide tubes
    # contain no fission; true fuel minimum is computed from CSV after masking.
    if pmax_raw is not None and pmax_log is not None and abs(pmax_raw-pmax_log)>5e-4:
        issues.append(f"true-fuel CSV raw maximum {pmax_raw} disagrees with rounded solver-log max {pmax_log}")
    total=sum(assembly_sums.values())
    if total<=0: issues.append("non-positive summed true-fuel power")
    fractions={key:(100*val/total if total>0 else None) for key,val in assembly_sums.items()}
    return {
      "layout_signature":meta.get("layout_signature",d.name),
      "candidate_id":"c5g7-2x2-"+str(meta.get("layout_signature",d.name)),
      "status":"PASS_RUN_ARTIFACTS" if not issues else "INCOMPLETE_OR_REVIEW",
      "issues":issues,
      "settings":meta.get("settings"),
      "solver":{"repository":"https://github.com/EmreSakarya/c5g7-2d-transport-benchmark","upstream_commit":meta.get("upstream_commit"),
        "patched_source_sha256":meta.get("patched_source_sha256"),"compile_flags":meta.get("compile_flags")},
      "keff":k,
      "difference_from_canonical_published_reference_pcm":((k-1.18655)*100000 if k is not None else None),
      "difference_note":"Reference comparison is meaningful as a benchmark check only for canonical UMMU; not an acceptance test for other permutations.",
      "mesh_block_bins":n_block_bins,
      "true_fuel_pin_bins":len(fuel_values_raw),
      "instrument_tube_bins":n_instrument,
      "zero_power_guide_tube_bins":n_zero_guide,
      "excluded_non_fuel_mesh_bins":n_instrument+n_zero_guide,
      "solver_csv_true_fuel_mean_before_renormalization":fuel_mean if math.isfinite(fuel_mean) else None,
      "raw_solver_csv_min_true_fuel_pin_power":pmin_raw,
      "raw_solver_csv_max_true_fuel_pin_power":pmax_raw,
      "min_normalized_fuel_pin_power":pmin_norm,
      "max_normalized_fuel_pin_power":pmax_norm,
      "solver_log_max_over_all_reported_bins":pmax_log,
      "solver_log_min_over_all_reported_bins":pmin_log,
      "position_power_fractions_percent_true_fuel_only":{"p00":fractions["1"],"p01":fractions["2"],"p10":fractions["3"],"p11":fractions["4"]},
      "solver_log_sha256":sha(log_path),
      "pinpower_csv_sha256":sha(csv_path),
      "interpretation":"Four central instrument-tube cells have tiny positive fission and are excluded from true fuel-pin metrics; 96 guide-tube bins are zero. Values are renormalized over 1,056 true fuel pins."
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--outdir",type=Path,required=True)
    a=p.parse_args()
    a.outdir.mkdir(parents=True,exist_ok=True)
    # Each artifact can nest its signature folder one level below its artifact root.
    dirs=[]
    for meta in a.root.rglob("layout_metadata.json"):
        dirs.append(meta.parent)
    rows=[parse_sig_dir(d) for d in sorted(dirs)]
    seen=[x["layout_signature"] for x in rows]
    issues=[]
    if len(rows)!=6: issues.append(f"expected six layout records, found {len(rows)}")
    if set(seen)!=EXPECTED: issues.append(f"layout coverage mismatch; seen={sorted(seen)}")
    if len(seen)!=len(set(seen)): issues.append("duplicate layout signatures")
    if any(x["status"]!="PASS_RUN_ARTIFACTS" for x in rows): issues.append("one or more solver artifacts are incomplete or need review")
    # Do not declare a layout physically feasible/safe based on this code-to-code screen.
    ordered=[x for x in rows if x.get("keff") is not None]
    ranking=sorted(ordered,key=lambda x:x["max_normalized_fuel_pin_power"] if x.get("max_normalized_fuel_pin_power") is not None else math.inf)
    report={
      "schema_version":"1.0",
      "study":"six-layout independent deterministic C5G7 S_N transport cross-check",
      "status":"COMPLETE_COMPUTATIONAL_SCREEN" if not issues else "INCOMPLETE_OR_REVIEW_REQUIRED",
      "upstream_solver_commit":COMMIT,
      "candidate_count":len(rows),
      "layout_coverage":sorted(set(seen)),
      "issues":issues,
      "results":rows,
      "descriptive_low_to_high_peak_pin_power_order":[{"layout":x["layout_signature"],"max_normalized_pin_power":x.get("max_normalized_fuel_pin_power")} for x in ranking],
      "interpretation_limits":[
        "This is an independent numerical comparison, not an official OECD/NEA acceptance test.",
        "The S_N solver uses Cartesian digital-disk pin geometry and has a documented spatial-discretization bias relative to the published Monte Carlo reference.",
        "The canonical published k_eff and pin-power summary apply to UMMU only; they must not be used as physical pass/fail thresholds for the other five layouts.",
        "The solver's maximum normalized pin power is a descriptive pin-power-shape metric, not an absolute power limit or a reactor-safety criterion.",
        "A completed transport run does not certify convergence, design-specific feasibility, licensability, or safety."
      ]
    }
    (a.outdir/"six_layout_independent_transport_summary.json").write_text(json.dumps(report,indent=2)+"\n")
    fields=["layout_signature","keff","difference_from_canonical_published_reference_pcm","raw_solver_csv_min_true_fuel_pin_power","raw_solver_csv_max_true_fuel_pin_power","min_normalized_fuel_pin_power","max_normalized_fuel_pin_power","solver_csv_true_fuel_mean_before_renormalization","solver_log_max_over_all_reported_bins","solver_log_min_over_all_reported_bins","mesh_block_bins","true_fuel_pin_bins","instrument_tube_bins","zero_power_guide_tube_bins","excluded_non_fuel_mesh_bins","status","solver_log_sha256","pinpower_csv_sha256"]
    with (a.outdir/"six_layout_independent_transport_summary.csv").open("w",newline="",encoding="utf-8") as f:
      w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
      for x in rows:w.writerow({k:x.get(k) for k in fields})
    print(json.dumps({"status":report["status"],"candidate_count":len(rows),"layout_coverage":report["layout_coverage"],"issues":issues,
      "broad_physical_feasibility":"NOT_ESTABLISHED","output":str(a.outdir/"six_layout_independent_transport_summary.json")},indent=2))
    if issues: raise SystemExit(1)
if __name__=="__main__":main()
