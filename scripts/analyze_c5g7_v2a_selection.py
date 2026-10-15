#!/usr/bin/env python3
"""Audit 1,200 V2a physical run artifacts and compare low-budget selection observations with P1-P4 reference runs.

This reports an empirical candidate-observation benchmark. It never calls a noisy
single V2a observation the physical truth and never upgrades the result to
official C5G7 acceptance or experimental validation.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,statistics
from pathlib import Path
import xml.etree.ElementTree as ET

SIGS=("MMUU","MUMU","MUUM","UMMU","UMUM","UUMM")
EXPECTED=1200
FUEL_OBJECTIVE="minimize max assembly-integrated fission rate / mean assembly-integrated fission rate"

def sha256(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()

def audit_entropy_mesh(mesh, settings_path):
 if mesh.get("derived_from_geometry_bounding_box") is not True:raise ValueError("entropy mesh is not certified as geometry-derived")
 if mesh.get("entropy_dimension")!=[24,24]:raise ValueError(f"entropy mesh dimension mismatch: {mesh.get('entropy_dimension')!r}")
 if mesh.get("z_axis_unbounded") is not True:raise ValueError("entropy mesh is not recorded as a 2-D x-y mesh with unbounded z")
 names=("geometry_lower_xy","geometry_upper_xy","entropy_lower_left","entropy_upper_right")
 pairs={}
 for name in names:
  value=mesh.get(name)
  if not isinstance(value,list) or len(value)!=2:raise ValueError(f"entropy mesh audit field {name} must be a 2-vector")
  pairs[name]=[float(v) for v in value]
  if not all(math.isfinite(v) for v in pairs[name]):raise ValueError(f"entropy mesh audit field {name} contains non-finite bounds")
 padding=float(mesh.get("padding_cm",math.nan))
 if not math.isfinite(padding) or padding<0:raise ValueError("entropy mesh padding must be finite and non-negative")
 for axis in range(2):
  gl,gu=pairs["geometry_lower_xy"][axis],pairs["geometry_upper_xy"][axis]
  el,eu=pairs["entropy_lower_left"][axis],pairs["entropy_upper_right"][axis]
  if not gu>gl:raise ValueError(f"invalid geometry bounding-box bounds on axis {axis}")
  if not math.isclose(el,gl-padding,rel_tol=0.0,abs_tol=1e-8):raise ValueError(f"entropy lower bound axis {axis} does not equal geometry lower bound minus padding")
  if not math.isclose(eu,gu+padding,rel_tol=0.0,abs_tol=1e-8):raise ValueError(f"entropy upper bound axis {axis} does not equal geometry upper bound plus padding")
 settings=ET.parse(settings_path).getroot()
 mesh_id=settings.findtext("entropy_mesh")
 actual_mesh=settings.find(f"mesh[@id='{mesh_id}']") if mesh_id else None
 if actual_mesh is None:raise ValueError("settings.xml entropy_mesh reference does not resolve to a mesh element")
 dims=[int(v) for v in (actual_mesh.findtext("dimension") or "").split()]
 lower=[float(v) for v in (actual_mesh.findtext("lower_left") or "").split()]
 upper=[float(v) for v in (actual_mesh.findtext("upper_right") or "").split()]
 if dims!=[24,24]:raise ValueError(f"settings.xml entropy mesh dimension mismatch: {dims!r}")
 if len(lower)!=2 or len(upper)!=2:raise ValueError("settings.xml entropy mesh bounds must be two-dimensional")
 for axis in range(2):
  if not math.isclose(lower[axis],pairs["entropy_lower_left"][axis],rel_tol=0.0,abs_tol=1e-8):raise ValueError("settings.xml lower-left does not match entropy mesh audit JSON")
  if not math.isclose(upper[axis],pairs["entropy_upper_right"][axis],rel_tol=0.0,abs_tol=1e-8):raise ValueError("settings.xml upper-right does not match entropy mesh audit JSON")
 return True

def gather(root, expected_stage, expected_profile=None):
 rows=[];errors=[]
 for p in sorted(root.rglob("STUDY_SUMMARY.json")):
  try:
   meta_p=p.parent/"NIGHT_RUN_METADATA.json"
   if not meta_p.is_file():raise ValueError("missing NIGHT_RUN_METADATA.json")
   meta=json.loads(meta_p.read_text());study=json.loads(p.read_text())
   if meta.get("stage")!=expected_stage:continue
   cases=study.get("cases",[])
   if len(cases)!=1 or cases[0].get("status")!="completed":raise ValueError("case not completed")
   case=cases[0];sig="".join("M" if case["layout"][k]=="MOX" else "U" for k in ("p00","p01","p10","p11"))
   if sig not in SIGS or case["candidate_id"]!="c5g7-2x2-"+sig:raise ValueError("candidate identity mismatch")
   seed=int(case["seed"]);phys=case["physical_results"];cd=p.parent/case["candidate_id"]
   settings=study.get("settings") or {}
   if meta.get("signature")!=sig:raise ValueError("metadata layout signature mismatch")
   if meta.get("source")!="good":raise ValueError("unexpected source profile; V2a/P1-P4 require source=good")
   if int(meta.get("replicate",-1))<1:raise ValueError("invalid replicate metadata")
   for key in ("batches","inactive","particles","threads"):
    if int(meta.get(key,-1))!=int(settings[key]):raise ValueError(f"metadata {key} does not match STUDY_SUMMARY settings")
   expected_run_id=f"{expected_stage}-{sig}-s{seed}-b{int(settings['batches'])}-i{int(settings['inactive'])}-p{int(settings['particles'])}-t{int(settings['threads'])}-good"
   if meta.get("run_id")!=expected_run_id:raise ValueError(f"run_id does not match stage/layout/seed/settings: {meta.get('run_id')!r} != {expected_run_id!r}")
   files={
    "statepoint":cd/phys["statepoint"],
    "manifest":cd/"RUN_MANIFEST.json",
    "trace":cd/"trace.npz",
    "mesh_audit":cd/"model/2d/entropy_mesh_audit.json",
    "raw_audit":p.parent/"analysis/raw_hdf5_audit.json",
    "source_trace":p.parent/"analysis/source_convergence.json",
    "source_trace_csv":p.parent/"analysis/source_convergence.csv",
    "assembly":p.parent/"analysis/assembly_fission.json",
    "settings":cd/"model/2d/settings.xml",
    "tally_output":cd/"model/2d/tallies.out",
    "tally_xml":cd/"model/2d/tallies.xml",
    "log":cd/"openmc.log",
   }
   for name,path in files.items():
    if not path.is_file():raise ValueError(f"missing {name}: {path}")
   manifest=json.loads(files["manifest"].read_text());mesh=json.loads(files["mesh_audit"].read_text())
   raw=json.loads(files["raw_audit"].read_text());tr=json.loads(files["source_trace"].read_text());f=json.loads(files["assembly"].read_text())
   if raw.get("status")!="PASS" or raw.get("candidate_count")!=1:raise ValueError("raw HDF5 audit failure")
   if not manifest.get("required_balance_scores_present") or not manifest.get("tallies"):raise ValueError("manifest tally/balance-score evidence missing")
   if tr.get("status")!="DIAGNOSTIC_REVIEW_REQUIRED" or tr.get("automatic_convergence_claim") is not False or not tr.get("entropy") or not tr.get("k_generation"):raise ValueError("source diagnostics absent or status is not explicitly non-certifying")
   audit_entropy_mesh(mesh,files['settings'])
   if files["log"].read_text(errors="replace").count("Fission source site(s) outside of entropy box"):raise ValueError("entropy mesh warning")
   if manifest.get("openmc_version")!="0.16.0" or manifest.get("seed")!=seed:raise ValueError("manifest version or seed mismatch")
   for key in ("threads","batches","inactive","particles"):
    if int(manifest.get(key,-1))!=int(settings[key]):raise ValueError(f"manifest {key} mismatch")
   if manifest.get("mgxs_sha256")!=phys.get("mgxs_sha256_after_transport"):raise ValueError("MGXS hash mismatch")
   statepoint_hash=sha256(files["statepoint"]);trace_hash=sha256(files["trace"]);settings_hash=sha256(files["settings"])
   if manifest.get("statepoint_sha256")!=statepoint_hash:raise ValueError("statepoint hash mismatch")
   if manifest.get("trace_file")!="trace.npz" or manifest.get("trace_sha256")!=trace_hash:raise ValueError("trace hash mismatch")
   expected_hashes=case.get("output_hashes_after_run") or {}
   if expected_hashes.get(str(Path(phys["statepoint"])))!=statepoint_hash:raise ValueError("statepoint hash disagrees with study output manifest")
   if expected_hashes.get("trace.npz")!=trace_hash:raise ValueError("trace hash disagrees with study output manifest")
   if expected_hashes.get("model/2d/settings.xml")!=settings_hash:raise ValueError("settings.xml hash disagrees with study output manifest")
   if expected_hashes.get("model/2d/tallies.out")!=sha256(files["tally_output"]):raise ValueError("tallies.out hash disagrees with study output manifest")
   if expected_hashes.get("model/2d/tallies.xml")!=sha256(files["tally_xml"]):raise ValueError("tallies.xml hash disagrees with study output manifest")
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
    "convergence_status":tr["status"],"convergence_certified":False,
    "k_generation_half_delta_pcm":float(tr["k_generation_second_minus_first_half_pcm"]),
    "k_generation_first_quarter_mean":float(tr["k_generation"]["first_quarter_mean"]),
    "k_generation_last_quarter_mean":float(tr["k_generation"]["last_quarter_mean"]),
    "k_generation_last_minus_first_quarter_mean":float(tr["k_generation"]["last_minus_first_quarter_mean"]),
    "k_generation_ols_slope_per_1000_active_batches":float(tr["k_generation"]["ols_slope_per_1000_active_batches"]),
    "entropy_first_quarter_mean":float(tr["entropy"]["first_quarter_mean"]),
    "entropy_last_quarter_mean":float(tr["entropy"]["last_quarter_mean"]),
    "entropy_last_minus_first_quarter_mean":float(tr["entropy"]["last_minus_first_quarter_mean"]),
    "statepoint_sha256":statepoint_hash,"settings_sha256":settings_hash,
    "mgxs_sha256":manifest["mgxs_sha256"],"trace_sha256":trace_hash,
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
 p.add_argument("--seed-ledger",type=Path,required=True,help="Deterministic campaign_plan.json archived before transport")
 a=p.parse_args()
 if a.outdir.exists() and any(a.outdir.iterdir()):p.error("refusing to overwrite non-empty output directory")
 low,low_errors=gather(a.v2a_root,"V2a",(800,500,2000))
 high,high_errors=[],[]
 for stage in ("P1","P2","P3","P4"):
  r,e=gather(a.production_root,stage)
  high.extend(r);high_errors.extend(e)
 errors=low_errors+high_errors
 try:
  ledger=json.loads(a.seed_ledger.read_text())
  low_plan=[item for shard in ledger.get("V2a_shards",[]) for item in shard]
  high_plan=[item for item in ledger.get("production_matrix",[]) if item.get("stage") in ("P1","P2","P3","P4")]
  plan_rows=low_plan+high_plan
  if len(low_plan)!=EXPECTED:raise ValueError(f"seed ledger has {len(low_plan)} V2a entries, expected {EXPECTED}")
  if len(high_plan)!=60:raise ValueError(f"seed ledger has {len(high_plan)} P1-P4 high-budget entries, expected 60")
  plan_by_id={x["run_id"]:x for x in plan_rows}
  if len(plan_by_id)!=len(plan_rows):raise ValueError("duplicate run_id in seed ledger")
  observed_rows=low+high
  observed_ids=[r["run_id"] for r in observed_rows]
  if len(set(observed_ids))!=len(observed_ids):raise ValueError("duplicate run_id among observed V2a/high-budget artifacts")
  missing=sorted(set(plan_by_id)-set(observed_ids));unexpected=sorted(set(observed_ids)-set(plan_by_id))
  if missing:errors.append(f"seed ledger missing observed run IDs: {missing[:20]}")
  if unexpected:errors.append(f"observed run IDs not present in seed ledger: {unexpected[:20]}")
  for row in observed_rows:
   planned=plan_by_id.get(row["run_id"])
   if planned is None:continue
   for key in ("stage","candidate_id","signature","seed","replicate","batches","inactive","particles","threads","source"):
    if row.get(key)!=planned.get(key):errors.append(f"seed ledger mismatch {row['run_id']} field {key}: observed={row.get(key)!r}, planned={planned.get(key)!r}")
  field_mismatch_count=sum(1 for message in errors if message.startswith("seed ledger mismatch "))
  seed_ledger_audit={"status":"PASS" if not missing and not unexpected and field_mismatch_count==0 else "FAIL","expected_total_count":len(plan_rows),"expected_v2a_count":len(low_plan),"expected_high_budget_count":len(high_plan),"observed_total_count":len(observed_rows),"missing_run_ids":missing,"unexpected_run_ids":unexpected,"field_mismatch_count":field_mismatch_count,"sha256":sha256(a.seed_ledger)}
 except Exception as e:
  errors.append(f"seed ledger audit: {type(e).__name__}: {e}")
  seed_ledger_audit={"status":"FAIL","error":f"{type(e).__name__}: {e}","sha256":sha256(a.seed_ledger) if a.seed_ledger.is_file() else None}
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
 integrity=(not errors and seed_ledger_audit["status"]=="PASS" and len(low)==EXPECTED and len({r["run_id"] for r in low})==EXPECTED and len(observed)==EXPECTED and
  len(complete_pools)==200 and len(set(hashes))==len(hashes) and len(mgxs)==1 and None not in mgxs and
  all(len(v)==10 for v in high_by.values()) and len(high)==60 and len({r["run_id"] for r in high})==len(high) and truth_best is not None)
 result={"schema_version":"1.0","protocol_id":"CBPFR-C5G7-NIGHT-CAMPAIGN-2026-10-15",
  "status":"V2A_DATA_INTEGRITY_PASS_POLICY_ANALYSIS_PENDING" if integrity else "V2A_INCOMPLETE_OR_INTEGRITY_FAIL",
  "integrity_pass":integrity,"observed_v2a_runs":len(low),"expected_v2a_runs":EXPECTED,
  "complete_six-layout_pools":len(complete_pools),"distinct_seed_count":len(per_seed),
  "settings":{"batches":800,"inactive":500,"particles":2000,"threads":1},
  "seed_ledger_audit":seed_ledger_audit,"convergence_certified":False,
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
