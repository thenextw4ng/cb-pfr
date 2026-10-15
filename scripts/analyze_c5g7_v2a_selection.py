#!/usr/bin/env python3
"""Audit 1,200 V2a physical run artifacts and compare low-budget selection observations with P1-P4 reference runs.

This reports an empirical candidate-observation benchmark. It never calls a noisy
single V2a observation the physical truth and never upgrades the result to
official C5G7 acceptance or experimental validation.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,statistics
from pathlib import Path
import numpy as np

SIGS=("MMUU","MUMU","MUUM","UMMU","UMUM","UUMM")
EXPECTED=1200
FUEL_OBJECTIVE="minimize max assembly-integrated fission rate / mean assembly-integrated fission rate"

def sha256(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()

def gather(root, expected_stage, expected_profile=None):
 rows=[];errors=[]
 for p in sorted(root.rglob("STUDY_SUMMARY.json")):
  try:
   meta_p=p.parent/"NIGHT_RUN_METADATA.json"
   if not meta_p.is_file():raise ValueError("missing NIGHT_RUN_METADATA.json")
   meta=json.loads(meta_p.read_text());study=json.loads(p.read_text())
   if meta.get("stage")!=expected_stage:raise ValueError(f"wrong stage {meta.get('stage')}")
   cases=study.get("cases",[])
   if len(cases)!=1 or cases[0].get("status")!="completed":raise ValueError("case not completed")
   case=cases[0];sig="".join("M" if case["layout"][k]=="MOX" else "U" for k in ("p00","p01","p10","p11"))
   if sig not in SIGS or case["candidate_id"]!="c5g7-2x2-"+sig:raise ValueError("candidate identity mismatch")
   seed=int(case["seed"]);phys=case["physical_results"];cd=p.parent/case["candidate_id"]
   files={
    "statepoint":cd/phys["statepoint"],
    "manifest":cd/"RUN_MANIFEST.json",
    "trace":cd/"trace.npz",
    "mesh_audit":cd/"model/2d/entropy_mesh_audit.json",
    "raw_audit":p.parent/"analysis/raw_hdf5_audit.json",
    "source_trace":p.parent/"analysis/source_convergence.json",
    "assembly":p.parent/"analysis/assembly_fission.json",
    "settings":cd/"model/2d/settings.xml",
    "log":cd/"openmc.log",
   }
   for name,path in files.items():
    if not path.is_file():raise ValueError(f"missing {name}: {path}")
   manifest=json.loads(files["manifest"].read_text());mesh=json.loads(files["mesh_audit"].read_text())
   raw=json.loads(files["raw_audit"].read_text());tr=json.loads(files["source_trace"].read_text());f=json.loads(files["assembly"].read_text())
   if raw.get("status")!="PASS" or raw.get("candidate_count")!=1:raise ValueError("raw HDF5 audit failure")
   if tr.get("status")!="DIAGNOSTIC_REVIEW_REQUIRED" or not tr.get("entropy"):raise ValueError("source trace absent")
   if mesh.get("derived_from_geometry_bounding_box") is not True or mesh.get("entropy_dimension")!=[24,24,1]:raise ValueError("geometry-derived entropy mesh audit failed")
   if files["log"].read_text(errors="replace").count("Fission source site(s) outside of entropy box"):raise ValueError("entropy mesh warning")
   if manifest.get("openmc_version")!="0.16.0" or manifest.get("seed")!=seed:raise ValueError("manifest version or seed mismatch")
   if manifest.get("mgxs_sha256")!=phys.get("mgxs_sha256_after_transport"):raise ValueError("MGXS hash mismatch")
   if manifest.get("statepoint_sha256")!=sha256(files["statepoint"]):raise ValueError("statepoint hash mismatch")
   if int(study["settings"]["batches"])!=int(meta["batches"]) or int(study["settings"]["inactive"])!=int(meta["inactive"]) or int(study["settings"]["particles"])!=int(meta["particles"]) or int(study["settings"]["threads"])!=int(meta["threads"]):
    raise ValueError("run settings disagree with metadata")
   if expected_profile and (int(study["settings"]["batches"]),int(study["settings"]["inactive"]),int(study["settings"]["particles"]))!=expected_profile:
    raise ValueError(f"wrong profile; expected {expected_profile}")
   if f.get("candidate_id")!=case["candidate_id"] or f.get("layout_signature")!=sig:raise ValueError("assembly tally identity mismatch")
   if meta.get("candidate_id")!=case["candidate_id"] or int(meta.get("seed",-1))!=seed:raise ValueError("matrix/run identity mismatch")
   rows.append({
    "run_id":meta["run_id"],"stage":meta["stage"],"candidate_id":case["candidate_id"],"signature":sig,
    "seed":seed,"replicate":int(meta["replicate"]),"batches":int(study["settings"]["batches"]),
    "inactive":int(study["settings"]["inactive"]),"particles":int(study["settings"]["particles"]),
    "threads":int(study["settings"]["threads"]),"source":meta["source"],
    "keff_mean":float(phys["keff_mean"]),"keff_sd":float(phys["keff_std_dev"]),
    "F_fission":float(f["fission_rate_peaking_factor"]),
    "statepoint_sha256":sha256(files["statepoint"]),"settings_sha256":sha256(files["settings"]),
    "mgxs_sha256":manifest["mgxs_sha256"],"trace_sha256":sha256(files["trace"]),
    "run_wallclock_seconds":float(manifest.get("run_wallclock_seconds",math.nan)),
    "status":"PASS_INTEGRITY","study_path":str(p),"statepoint_path":str(files["statepoint"])
   })
  except Exception as e:
   errors.append(f"{p}: {type(e).__name__}: {e}")
 return rows,errors

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--v2a-root",type=Path,required=True)
 p.add_argument("--production-root",type=Path,required=True)
 p.add_argument("--outdir",type=Path,required=True)
 a=p.parse_args()
 if a.outdir.exists() and any(a.outdir.iterdir()):p.error("refusing to overwrite non-empty output directory")
 low,low_errors=gather(a.v2a_root,"V2a",(800,500,2000))
 high,high_errors=[],[]
 for stage in ("P1","P2","P3","P4"):
  r,e=gather(a.production_root,stage)
  high.extend(r);high_errors.extend(e)
 errors=low_errors+high_errors
 expected_pairs={(seed,sig) for seed in {r["seed"] for r in low} for sig in SIGS}
 observed={(r["seed"],r["signature"]) for r in low}
 per_seed={s:sorted([r["signature"] for r in low if r["seed"]==s]) for s in {r["seed"] for r in low}}
 complete_pools=[s for s,v in per_seed.items() if len(v)==6 and tuple(v)==tuple(SIGS)]
 hashes=[r["statepoint_sha256"] for r in low+high]
 mgxs={r["mgxs_sha256"] for r in low+high}
 high_by={sig:[r["F_fission"] for r in high if r["signature"]==sig] for sig in SIGS}
 truth={}
 for sig,vals in high_by.items():
  truth[sig]={"n_high_budget_runs":len(vals),"mean_F_fission":statistics.mean(vals) if vals else None,
   "between_seed_sd_F_fission":statistics.stdev(vals) if len(vals)>1 else None,
   "status":"HIGH_BUDGET_EMPIRICAL_REFERENCE" if len(vals)==10 else "HIGH_BUDGET_REFERENCE_INCOMPLETE"}
 truth_best=min(( (v["mean_F_fission"],sig) for sig,v in truth.items() if v["mean_F_fission"] is not None),default=(None,None))[1]
 decisions=[]
 for seed in sorted(complete_pools):
  bundle={r["signature"]:r for r in low if r["seed"]==seed}
  chosen=min(SIGS,key=lambda s:(bundle[s]["F_fission"],s))
  true_value=truth.get(truth_best,{}).get("mean_F_fission") if truth_best else None
  selected_value=truth.get(chosen,{}).get("mean_F_fission")
  decisions.append({"pool_seed":seed,"point_estimate_selected":chosen,
   "observed_F_selected":bundle[chosen]["F_fission"],"high_budget_empirical_best":truth_best,
   "selection_matches_empirical_high_budget_best":chosen==truth_best if truth_best else None,
   "empirical_regret_F":(selected_value-true_value) if selected_value is not None and true_value is not None else None,
   "note":"This is one point-estimate rule. CB-PFR, uniform-margin and adaptive/equal-allocation R&S policy comparison needs its own equal-budget policy simulation and is not implied by these run outputs."})
 integrity=(not errors and len(low)==EXPECTED and len({r["run_id"] for r in low})==EXPECTED and len(observed)==EXPECTED and
  len(complete_pools)==200 and len(set(hashes))==len(hashes) and len(mgxs)==1 and None not in mgxs and
  all(len(v)==10 for v in high_by.values()) and truth_best is not None)
 result={"schema_version":"1.0","protocol_id":"CBPFR-C5G7-NIGHT-CAMPAIGN-2026-10-15",
  "status":"V2A_DATA_INTEGRITY_PASS_POLICY_ANALYSIS_PENDING" if integrity else "V2A_INCOMPLETE_OR_INTEGRITY_FAIL",
  "integrity_pass":integrity,"observed_v2a_runs":len(low),"expected_v2a_runs":EXPECTED,
  "complete_six-layout_pools":len(complete_pools),"distinct_seed_count":len(per_seed),
  "settings":{"batches":800,"inactive":500,"particles":2000,"threads":1},
  "objective":FUEL_OBJECTIVE,"high_budget_empirical_reference_by_layout":truth,
  "high_budget_empirical_best_layout":truth_best,"point_estimate_selection_summary":{
   "n_pools":len(decisions),"matches_empirical_high_budget_best":sum(d["selection_matches_empirical_high_budget_best"] is True for d in decisions),
   "match_fraction":sum(d["selection_matches_empirical_high_budget_best"] is True for d in decisions)/len(decisions) if decisions else None,
   "mean_empirical_regret_F":statistics.mean([d["empirical_regret_F"] for d in decisions if d["empirical_regret_F"] is not None]) if any(d["empirical_regret_F"] is not None for d in decisions) else None},
  "point_estimate_decisions":decisions,"v2a_run_level_results":low,"high_budget_run_level_results":high,
  "errors":errors,"global_unique_statepoint_hashes":len(set(hashes))==len(hashes),"one_common_mgxs_hash":len(mgxs)==1 and None not in mgxs,
  "nonclaims":["The ten high-budget runs/layout are an empirical reference sample, not mathematically exact truth.",
   "The point-estimate selection analysis is not a comparison of CB-PFR against other methods.",
   "No experimental validation or official benchmark acceptance is implied."]}
 a.outdir.mkdir(parents=True,exist_ok=True)
 (a.outdir/"v2a_selection_summary.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
 for fn,rows in (("v2a_run_level.csv",low),("v2a_high_budget_reference.csv",high),("v2a_point_estimate_decisions.csv",decisions)):
  if rows:
   with (a.outdir/fn).open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print(json.dumps({"status":result["status"],"integrity_pass":integrity,"v2a_runs":len(low),"high_budget_runs":len(high),
  "complete_pools":len(complete_pools),"empirical_best":truth_best,"point_estimate_match_fraction":result["point_estimate_selection_summary"]["match_fraction"],"errors":errors[:10]},indent=2))
 return 2 if not integrity else 0
if __name__=="__main__":raise SystemExit(main())
