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
    positive_pin_values=[]
    seen_coordinates=set()
    n_positive=0
    n_block_bins=0
    with csv_path.open(newline="",encoding="utf-8") as f:
        reader=csv.DictReader(f)
        if not {"pc","pr","assembly","norm_power"}.issubset(set(reader.fieldnames or [])):
            issues.append("unexpected pin-power CSV schema")
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
                value=float(row["norm_power"])
                if not math.isfinite(value) or value < 0:
                    issues.append(f"invalid pin power at coordinate {key}: {value}")
                    continue
                aidx=str(int(row["assembly"]))
                if aidx not in assembly_sums:
                    if value > 0:
                        issues.append(f"positive power assigned to unknown assembly {aidx} at {key}")
                    continue
                if value>0:
                    n_positive+=1
                    positive_pin_values.append(value)
                    assembly_sums[aidx]+=value
    if n_block_bins != 1156:
        issues.append(f"expected 1156 unique bins in 34x34 block, found {n_block_bins}")
    total=sum(assembly_sums.values())
    if total<=0: issues.append("non-positive summed assembly power")
    if n_positive != 1060:
        issues.append(f"expected 1060 positive fuel-pin bins, found {n_positive}")
    if not positive_pin_values:
        issues.append("no positive fuel-pin powers found in CSV")
    pmax=max(positive_pin_values) if positive_pin_values else None
    pmin=min(positive_pin_values) if positive_pin_values else None
    # The upstream solver's console min is calculated across all bins and thus
    # reports 0 for included non-fuel/guide positions. Use the CSV's positive
    # fissionable-fuel mask for the positive fuel-pin minimum instead.
    if pmax is not None and pmax_log is not None and abs(pmax-pmax_log) > 5e-4:
        issues.append(f"pin-power CSV maximum {pmax} disagrees with rounded solver-log max {pmax_log}")
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
      "max_positive_normalized_pin_power_csv":pmax,
      "min_positive_normalized_pin_power_csv":pmin,
      "solver_log_max_over_all_reported_bins":pmax_log,
      "solver_log_min_over_all_reported_bins":pmin_log,
      "mesh_block_bins":n_block_bins,
      "positive_fuel_pin_bins":n_positive,
      "zero_nonfuel_bins_excluded_from_positive_min":n_block_bins-n_positive,
      "position_power_fractions_percent":{"p00":fractions["1"],"p01":fractions["2"],"p10":fractions["3"],"p11":fractions["4"]},
      "solver_log_sha256":sha(log_path),
      "pinpower_csv_sha256":sha(csv_path),
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
    ranking=sorted(ordered,key=lambda x:x["max_positive_normalized_pin_power_csv"] if x.get("max_positive_normalized_pin_power_csv") is not None else math.inf)
    report={
      "schema_version":"1.0",
      "study":"six-layout independent deterministic C5G7 S_N transport cross-check",
      "status":"COMPLETE_COMPUTATIONAL_SCREEN" if not issues else "INCOMPLETE_OR_REVIEW_REQUIRED",
      "upstream_solver_commit":COMMIT,
      "candidate_count":len(rows),
      "layout_coverage":sorted(set(seen)),
      "issues":issues,
      "results":rows,
      "descriptive_low_to_high_peak_pin_power_order":[{"layout":x["layout_signature"],"max_normalized_pin_power":x.get("max_positive_normalized_pin_power_csv")} for x in ranking],
      "interpretation_limits":[
        "This is an independent numerical comparison, not an official OECD/NEA acceptance test.",
        "The S_N solver uses Cartesian digital-disk pin geometry and has a documented spatial-discretization bias relative to the published Monte Carlo reference.",
        "The canonical published k_eff and pin-power summary apply to UMMU only; they must not be used as physical pass/fail thresholds for the other five layouts.",
        "The solver's maximum normalized pin power is a descriptive pin-power-shape metric, not an absolute power limit or a reactor-safety criterion.",
        "A completed transport run does not certify convergence, design-specific feasibility, licensability, or safety."
      ]
    }
    (a.outdir/"six_layout_independent_transport_summary.json").write_text(json.dumps(report,indent=2)+"\n")
    fields=["layout_signature","keff","difference_from_canonical_published_reference_pcm","max_positive_normalized_pin_power_csv","min_positive_normalized_pin_power_csv","solver_log_max_over_all_reported_bins","solver_log_min_over_all_reported_bins","positive_pin_bins","non_fuel_zero_bins_excluded_from_positive_min","status","solver_log_sha256","pinpower_csv_sha256"]
    with (a.outdir/"six_layout_independent_transport_summary.csv").open("w",newline="",encoding="utf-8") as f:
      w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
      for x in rows:w.writerow({k:x.get(k) for k in fields})
    print(json.dumps({"status":report["status"],"candidate_count":len(rows),"layout_coverage":report["layout_coverage"],"issues":issues,
      "broad_physical_feasibility":"NOT_ESTABLISHED","output":str(a.outdir/"six_layout_independent_transport_summary.json")},indent=2))
    if issues: raise SystemExit(1)
if __name__=="__main__":main()
