#!/usr/bin/env python3
"""Fail-closed analysis of corrected-group C5G7 layout evidence.

Computes descriptive t intervals for six-layout smoke data and explicitly
refuses to select a winner without a predeclared design-specific k_eff band,
approved spatial-tally mapping, and adequate convergence evidence.
"""
from __future__ import annotations
import argparse, csv, json, math, statistics
from collections import defaultdict
from pathlib import Path

EXPECTED_LAYOUTS = {"MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM"}
# Two-sided 95% Student-t critical values; n=3 is the current smoke study.
T95 = {2: 12.7062047364, 3: 4.30265272975, 4: 3.18244630528,
       5: 2.7764451052, 6: 2.57058183661, 7: 2.44691184879,
       8: 2.36462425101, 9: 2.3060041352, 10: 2.26215716285}

def analyze(path: Path) -> dict:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    required = {"round","candidate_id","layout_signature","seed","keff_mean",
                "keff_std_dev","fission_rate_peaking_factor","statepoint_sha256",
                "mgxs_sha256","group_structure_audit"}
    if not rows:
        raise ValueError("run-level CSV is empty")
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"run-level CSV missing columns: {sorted(missing)}")
    parsed=[]
    for n,row in enumerate(rows, start=2):
        try:
            item={**row,"seed":int(row["seed"]),"keff":float(row["keff_mean"]),
                  "keff_sd":float(row["keff_std_dev"]),
                  "fpeak":float(row["fission_rate_peaking_factor"])}
        except (ValueError, TypeError) as e:
            raise ValueError(f"invalid numeric data at CSV line {n}") from e
        if not all(math.isfinite(item[k]) for k in ("keff","keff_sd","fpeak")):
            raise ValueError(f"non-finite data at CSV line {n}")
        if item["keff_sd"] <= 0 or item["fpeak"] <= 0:
            raise ValueError(f"non-positive uncertainty or objective at CSV line {n}")
        parsed.append(item)
    layouts={r["layout_signature"] for r in parsed}
    seeds=[r["seed"] for r in parsed]
    hashes=[r["statepoint_sha256"] for r in parsed]
    mgxs={r["mgxs_sha256"] for r in parsed}
    all_standard=all(r["group_structure_audit"]=="PASS" for r in parsed)
    groups=defaultdict(list)
    for row in parsed: groups[row["layout_signature"]].append(row)
    summaries=[]
    for signature, group in sorted(groups.items()):
        if len(group)<2: raise ValueError(f"{signature}: at least two independent runs required")
        ks=[r["keff"] for r in group]; fs=[r["fpeak"] for r in group]
        def interval(values):
            mean=statistics.mean(values); sd=statistics.stdev(values)
            crit=T95.get(len(values)-1)
            half=crit*sd/math.sqrt(len(values)) if crit else None
            return {"mean":mean,"sample_sd":sd,"n":len(values),
                    "ci95_low":mean-half if half is not None else None,
                    "ci95_high":mean+half if half is not None else None,
                    "interval_method":"two-sided Student-t, descriptive; assumes independent runs"}
        summaries.append({"layout_signature":signature,"candidate_id":group[0]["candidate_id"],
                          "n_runs":len(group),"seeds":sorted(r["seed"] for r in group),
                          "keff":interval(ks),"fission_peaking":interval(fs),
                          "descriptive_fission_peaking_rank":None})
    ranked=sorted(summaries,key=lambda x:x["fission_peaking"]["mean"])
    for rank,row in enumerate(ranked,1): row["descriptive_fission_peaking_rank"]=rank
    complete=(layouts==EXPECTED_LAYOUTS and len(parsed)==18 and
              all(len(g)==3 for g in groups.values()) and len(seeds)==len(set(seeds)) and
              len(hashes)==len(set(hashes)) and len(mgxs)==1 and all_standard)
    return {
      "schema_version":"1.0",
      "status":"EVIDENCE_INTEGRITY_PASS_DESIGN_SELECTION_BLOCKED" if complete else "EVIDENCE_INCOMPLETE",
      "input":str(path),
      "checks":{"expected_six_layouts":layouts==EXPECTED_LAYOUTS,"exactly_18_runs":len(parsed)==18,
                "three_runs_per_layout":all(len(g)==3 for g in groups.values()),
                "unique_seeds":len(seeds)==len(set(seeds)),
                "unique_statepoint_hashes":len(hashes)==len(set(hashes)),
                "single_mgxs_hash":len(mgxs)==1,"all_standard_group_audits_pass":all_standard},
      "run_count":len(parsed),"layout_count":len(layouts),
      "mgxs_sha256":next(iter(mgxs)) if len(mgxs)==1 else None,
      "candidate_summaries":summaries,
      "decision":{"winner_selected":False,
                  "status":"BLOCKED_NO_APPROVED_DESIGN_KEFF_BAND_OR_INDEPENDENT_TALLY_REVIEW",
                  "reason":"Smoke-budget evidence and a relative fission-peaking proxy cannot establish a physically acceptable design. A design-specific k_eff acceptance band, reviewed mesh-to-assembly mapping, and higher-budget convergence study are still required."},
      "nonclaims":["not benchmark-grade convergence","not an official benchmark acceptance","not absolute power","not a reactor-safety conclusion","not a mapping of legacy burnup-state QUBO to UO2/MOX"]
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runs-csv",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.out.exists(): p.error(f"refusing to overwrite existing output: {a.out}")
    try: result=analyze(a.runs_csv)
    except (OSError,ValueError) as e: p.error(str(e))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"run_count":result["run_count"],
                      "layout_count":result["layout_count"],"winner_selected":False,"out":str(a.out)},indent=2))
    return 0 if result["status"]=="EVIDENCE_INTEGRITY_PASS_DESIGN_SELECTION_BLOCKED" else 2
if __name__=="__main__": raise SystemExit(main())
