#!/usr/bin/env python3
"""Aggregate the complete C5G7 night campaign without upgrading screening evidence into validation."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,statistics
from pathlib import Path
import numpy as np
import openmc

REFERENCE_KEFF=1.18655
REFERENCE_KEFF_SD=0.000095
EXPECTED_MAIN={"P1":10,"V1a":5,"P2":10,"P3":20,"P4":20,"P5":5,"P6":5}
NON_FUEL={
 (r,c)
 for r,cols in {
  2:(5,8,11),3:(3,13),5:(2,5,8,11,14),
  8:(2,5,8,11,14),11:(2,5,8,11,14),13:(3,13),14:(5,8,11)
 }.items() for c in cols
}
SIGS={"MMUU","MUMU","MUUM","UMMU","UMUM","UUMM"}

def sha256(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()

def audit_entropy_mesh(mesh):
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
 return True

def pin_max_min(statepoint):
 with openmc.StatePoint(statepoint) as sp:
  tally=sp.get_tally(name="tally 1")
  mf=next((f for f in tally.filters if isinstance(f,openmc.MeshFilter)),None)
  if mf is None or list(mf.mesh.dimension)!=[51,51,1]:raise ValueError("V1a mesh is not the required 51x51x1 mesh")
  if "fission" not in tally.scores:raise ValueError("mesh tally missing fission")
  score=tally.scores.index("fission")
  values=np.asarray(tally.get_reshaped_data(value="mean",expand_dims=True),dtype=float).reshape((51,51,1,-1,len(tally.scores)))
  grid=values[:,:,0,0,score]
  # Four 17x17 fuel assemblies occupy x bins 0:34 and y bins 17:51.
  fuel=[]
  for bx in range(2):
   for by in range(2):
    for r in range(17):
     for col in range(17):
      if (r,col) in NON_FUEL:continue
      fuel.append(float(grid[bx*17+r,17+by*17+col]))
  if len(fuel)!=1056 or any(not math.isfinite(x) or x<=0 for x in fuel):
   raise ValueError("fuel-pin tally coverage/data integrity failed")
  mean=float(np.mean(fuel))
  norm=np.asarray(fuel)/mean
  return {"fuel_pin_count":len(fuel),"fuel_pin_mean_raw_tally":mean,
   "maximum_normalized_fuel_pin_fission_rate":float(norm.max()),
   "minimum_normalized_fuel_pin_fission_rate":float(norm.min()),
   "reference_maximum_NE A":2.498,"reference_minimum_NEA_rounded":0.23,
   "max_relative_difference_pct":(float(norm.max())/2.498-1)*100,
   "min_relative_difference_pct":(float(norm.min())/0.23-1)*100,
   "pin_power_table_comparison":"BLOCKED_NO_REVIEWED_FULL_OFFICIAL_PIN_TABLE",
   "note":"This compares only max/min against the rounded scalar references accessible in the recorded source; it is not AVG/RMS/MAX full pin-wise benchmark acceptance."}

def gather(root):
 rows=[];errors=[]
 for p in sorted(root.rglob("STUDY_SUMMARY.json")):
  try:
   study=json.loads(p.read_text())
   meta_path=p.parent/"NIGHT_RUN_METADATA.json"
   if not meta_path.is_file():raise ValueError("missing NIGHT_RUN_METADATA.json")
   meta=json.loads(meta_path.read_text())
   cases=study.get("cases",[])
   if len(cases)!=1:raise ValueError("expected exactly one candidate")
   case=cases[0]
   if case.get("status")!="completed" or case.get("physical_results",{}).get("status")!="completed":raise ValueError("run not complete")
   cid=case["candidate_id"];sig="".join("M" if case["layout"][pos]=="MOX" else "U" for pos in ("p00","p01","p10","p11"))
   if cid!="c5g7-2x2-"+sig:raise ValueError("candidate signature mismatch")
   if sig not in SIGS:raise ValueError("unregistered layout signature")
   stage=meta.get("stage")
   if stage not in EXPECTED_MAIN:raise ValueError(f"unexpected stage in production-only aggregator: {stage!r}")
   settings=study.get("settings") or {}
   seed=int(case["seed"])
   expected_source="bad" if stage=="P6" else "good"
   if meta.get("source")!=expected_source:raise ValueError(f"source profile mismatch for {stage}: {meta.get('source')!r}")
   expected_run_id=f"{stage}-{sig}-s{seed}-b{int(settings['batches'])}-i{int(settings['inactive'])}-p{int(settings['particles'])}-t{int(settings['threads'])}-{expected_source}"
   if meta.get("run_id")!=expected_run_id:raise ValueError(f"run_id does not match stage/layout/seed/settings: {meta.get('run_id')!r} != {expected_run_id!r}")
   if meta.get("signature")!=sig:raise ValueError("metadata layout signature mismatch")
   if int(meta.get("replicate",-1))<1:raise ValueError("invalid replicate metadata")
   for key in ("batches","inactive","particles","threads"):
    if int(meta.get(key,-1))!=int(settings[key]):raise ValueError(f"metadata {key} does not match STUDY_SUMMARY settings")
   phys=case["physical_results"];case_dir=p.parent/cid
   manifest_path=case_dir/"RUN_MANIFEST.json";trace_path=case_dir/"trace.npz"
   settings_path=case_dir/"model/2d/settings.xml"
   raw_path=p.parent/"analysis/raw_hdf5_audit.json";source_path=p.parent/"analysis/source_convergence.json"
   source_csv=p.parent/"analysis/source_convergence.csv"
   fission_path=p.parent/"analysis/assembly_fission.json";mesh_audit=case_dir/"model/2d/entropy_mesh_audit.json"
   statepoint=case_dir/phys["statepoint"]
   for f in (manifest_path,trace_path,settings_path,raw_path,source_path,source_csv,fission_path,mesh_audit,statepoint):
    if not f.is_file():raise ValueError("missing evidence: "+str(f))
   manifest=json.loads(manifest_path.read_text());raw=json.loads(raw_path.read_text())
   source=json.loads(source_path.read_text());fission=json.loads(fission_path.read_text());entropy=json.loads(mesh_audit.read_text())
   if raw.get("status")!="PASS":raise ValueError("raw HDF5 audit failed")
   if source.get("status")!="DIAGNOSTIC_REVIEW_REQUIRED" or source.get("automatic_convergence_claim") is not False or not source.get("entropy") or not source.get("k_generation"):raise ValueError("source diagnostics absent or status is not explicitly non-certifying")
   if manifest.get("openmc_version")!="0.16.0":raise ValueError("OpenMC version mismatch")
   for key in ("seed","threads","batches","inactive","particles"):
    expected=int(case["seed"]) if key=="seed" else int(settings[key])
    if int(manifest.get(key,-1))!=expected:raise ValueError(f"manifest {key} mismatch")
   if manifest.get("mgxs_sha256")!=phys.get("mgxs_sha256_after_transport"):raise ValueError("MGXS hash mismatch")
   if manifest.get("statepoint_sha256")!=sha256(statepoint):raise ValueError("statepoint hash mismatch")
   if manifest.get("trace_file")!="trace.npz" or manifest.get("trace_sha256")!=sha256(trace_path):raise ValueError("trace hash mismatch")
   expected_hashes=case.get("output_hashes_after_run") or {}
   if expected_hashes.get(str(Path(phys["statepoint"])))!=sha256(statepoint):raise ValueError("statepoint hash disagrees with study output manifest")
   if expected_hashes.get("trace.npz")!=sha256(trace_path):raise ValueError("trace hash disagrees with study output manifest")
   if expected_hashes.get("model/2d/settings.xml")!=sha256(settings_path):raise ValueError("settings.xml hash disagrees with study output manifest")
   audit_entropy_mesh(entropy)
   log=(case_dir/"openmc.log")
   if not log.is_file():raise ValueError("captured OpenMC log absent")
   warnings=log.read_text(errors="replace").count("Fission source site(s) outside of entropy box")
   if warnings:raise ValueError(f"entropy-mesh warnings={warnings}")
   if fission.get("candidate_id")!=cid or fission.get("layout_signature")!=sig:raise ValueError("assembly tally signature mismatch")
   if meta.get("candidate_id")!=cid or int(meta.get("seed",-1))!=seed:raise ValueError("matrix metadata mismatch")
   row={"run_id":meta["run_id"],"stage":stage,"candidate_id":cid,"signature":sig,
    "seed":int(case["seed"]),"replicate":int(meta["replicate"]),"batches":int(study["settings"]["batches"]),
    "inactive":int(study["settings"]["inactive"]),"particles":int(study["settings"]["particles"]),
    "threads":int(study["settings"]["threads"]),"source":meta["source"],
    "keff_mean":float(phys["keff_mean"]),"keff_std_dev":float(phys["keff_std_dev"]),
    "fission_rate_peaking_factor":float(fission["fission_rate_peaking_factor"]),
    "convergence_status":source["status"],"convergence_certified":False,
    "k_generation_half_delta_pcm":float(source["k_generation_second_minus_first_half_pcm"]),
    "k_generation_first_quarter_mean":float(source["k_generation"]["first_quarter_mean"]),
    "k_generation_last_quarter_mean":float(source["k_generation"]["last_quarter_mean"]),
    "k_generation_last_minus_first_quarter_mean":float(source["k_generation"]["last_minus_first_quarter_mean"]),
    "k_generation_ols_slope_per_1000_active_batches":float(source["k_generation"]["ols_slope_per_1000_active_batches"]),
    "entropy_first_quarter_mean":float(source["entropy"]["first_quarter_mean"]),
    "entropy_last_quarter_mean":float(source["entropy"]["last_quarter_mean"]),
    "entropy_last_minus_first_quarter":float(source["entropy"]["last_minus_first_quarter_mean"]),
    "run_wallclock_seconds":float(manifest.get("run_wallclock_seconds",math.nan)),
    "statepoint_sha256":sha256(statepoint),"mgxs_sha256":manifest.get("mgxs_sha256"),
    "settings_sha256":sha256(case_dir/"model/2d/settings.xml"),"warning_count":warnings,"status":"PASS_INTEGRITY",
    "study_path":str(p),"statepoint_path":str(statepoint)}
   if meta["stage"]=="V1a":
    row["v1a_pin_power_summary"]=pin_max_min(statepoint)
   rows.append(row)
  except Exception as e:errors.append(f"{p}: {type(e).__name__}: {e}")
 return rows,errors

def stage_summary(rows,stage):
 g=[r for r in rows if r["stage"]==stage]
 if not g:return {"stage":stage,"run_count":0,"status":"MISSING"}
 ks=[r["keff_mean"] for r in g];within=[r["keff_std_dev"] for r in g];fps=[r["fission_rate_peaking_factor"] for r in g]
 out={"stage":stage,"run_count":len(g),"layouts":sorted(set(r["signature"] for r in g)),
  "seeds":sorted(set(r["seed"] for r in g)),"mean_keff_all_runs":statistics.mean(ks),
  "between_run_sd_keff":statistics.stdev(ks) if len(ks)>1 else None,
  "pooled_reported_within_run_sd_keff":math.sqrt(statistics.mean(x*x for x in within)),
  "mean_fission_rate_peaking_factor":statistics.mean(fps),
  "between_run_sd_fission_rate_peaking_factor":statistics.stdev(fps) if len(fps)>1 else None,
  "mean_run_wallclock_seconds":statistics.mean(r["run_wallclock_seconds"] for r in g if math.isfinite(r["run_wallclock_seconds"])) if any(math.isfinite(r["run_wallclock_seconds"]) for r in g) else None,
  "status":"PASS_INTEGRITY"}
 if stage in ("P1","V1a") and all(r["signature"]=="UMMU" for r in g):
  delta=(out["mean_keff_all_runs"]-REFERENCE_KEFF)*1e5
  sem=(out["between_run_sd_keff"]/math.sqrt(len(g))) if len(g)>1 else None
  combined=math.sqrt(REFERENCE_KEFF_SD**2+sem**2) if sem is not None else None
  out["reference_keff"]=REFERENCE_KEFF;out["reference_uncertainty"]=REFERENCE_KEFF_SD
  out["delta_reference_pcm"]=delta;out["combined_z"]=((out["mean_keff_all_runs"]-REFERENCE_KEFF)/combined) if combined else None
  out["note"]="Numerical screening only; model identity and pin-power gate still require independent review."
 if stage=="V1a":
  out["per_seed_pin_power"]=[{"seed":r["seed"],**r.get("v1a_pin_power_summary",{})} for r in g]
 return out

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--artifacts-root",type=Path,required=True);p.add_argument("--outdir",type=Path,required=True)
 p.add_argument("--seed-ledger",type=Path,required=True,help="Deterministic campaign_plan.json archived before transport")
 p.add_argument("--expected-main-runs",type=int,default=75);a=p.parse_args()
 if a.outdir.exists() and any(a.outdir.iterdir()):p.error("refusing to overwrite non-empty output directory")
 if a.expected_main_runs!=sum(EXPECTED_MAIN.values()):p.error(f"expected-main-runs must be {sum(EXPECTED_MAIN.values())} for this production-only aggregator")
 rows,errors=gather(a.artifacts_root);by_stage={s:stage_summary(rows,s) for s in ("P1","V1a","P2","P3","P4","P5","P6")}
 actual={s:by_stage[s]["run_count"] for s in by_stage}
 try:
  ledger=json.loads(a.seed_ledger.read_text())
  plan_rows=ledger.get("production_matrix",[])
  if len(plan_rows)!=a.expected_main_runs:raise ValueError(f"seed ledger production_matrix has {len(plan_rows)} entries, expected {a.expected_main_runs}")
  plan_by_id={x["run_id"]:x for x in plan_rows}
  if len(plan_by_id)!=len(plan_rows):raise ValueError("duplicate run_id in seed ledger")
  observed_ids=[r["run_id"] for r in rows]
  if len(set(observed_ids))!=len(observed_ids):raise ValueError("duplicate run_id among observed production artifacts")
  missing=sorted(set(plan_by_id)-set(observed_ids));unexpected=sorted(set(observed_ids)-set(plan_by_id))
  if missing:errors.append(f"seed ledger missing observed production runs: {missing[:20]}")
  if unexpected:errors.append(f"observed run IDs not present in seed ledger: {unexpected[:20]}")
  for row in rows:
   planned=plan_by_id.get(row["run_id"])
   if planned is None:continue
   for key in ("stage","candidate_id","signature","seed","replicate","batches","inactive","particles","threads","source"):
    if row.get(key)!=planned.get(key):errors.append(f"seed ledger mismatch {row['run_id']} field {key}: observed={row.get(key)!r}, planned={planned.get(key)!r}")
  seed_ledger_audit={"status":"PASS" if not errors else "FAIL","expected_count":len(plan_rows),"observed_count":len(rows),"missing_run_ids":missing,"unexpected_run_ids":unexpected,"sha256":sha256(a.seed_ledger)}
 except Exception as e:
  errors.append(f"seed ledger audit: {type(e).__name__}: {e}")
  seed_ledger_audit={"status":"FAIL","error":f"{type(e).__name__}: {e}","sha256":sha256(a.seed_ledger) if a.seed_ledger.is_file() else None}
 hashes=[r["statepoint_sha256"] for r in rows];mgxs={r["mgxs_sha256"] for r in rows}
 integrity=not errors and seed_ledger_audit["status"]=="PASS" and sum(actual.values())==a.expected_main_runs and all(actual[s]==EXPECTED_MAIN[s] for s in EXPECTED_MAIN)
 integrity=integrity and len(set(hashes))==len(hashes) and len(mgxs)==1 and None not in mgxs and all(r["status"]=="PASS_INTEGRITY" for r in rows)
 result={"schema_version":"1.0","protocol_id":"CBPFR-C5G7-NIGHT-CAMPAIGN-2026-10-15",
  "status":"MAIN_CAMPAIGN_INTEGRITY_PASS_PENDING_SCIENTIFIC_REVIEW" if integrity else "MAIN_CAMPAIGN_INCOMPLETE_OR_INTEGRITY_FAIL",
  "integrity_pass":integrity,"convergence_certified":False,"expected_run_count":a.expected_main_runs,"observed_run_count":len(rows),
  "seed_ledger_audit":seed_ledger_audit,"run_counts_by_stage":actual,"errors":errors,"global_unique_statepoint_hashes":len(set(hashes))==len(hashes),
  "single_common_mgxs_sha256":len(mgxs)==1 and None not in mgxs,"stage_summaries":by_stage,
  "run_level_results":rows,"official_benchmark_acceptance":False,
  "selection_claim_status":"NOT_EVALUATED_BY_THIS_AGGREGATOR",
  "nonclaims":["C5G7 is a computational benchmark, not an experiment.",
  "A k-effective scalar match is not model-identity sign-off or official benchmark acceptance.",
  "Pin-wise AVG/RMS/MAX reference comparison remains blocked until a reviewed full official reference table and uncertainty are available.",
  "The 1,200 V2a smoke-budget outputs are observations for subsequent equal-budget policy analysis, not validated physical truth."]}
 a.outdir.mkdir(parents=True,exist_ok=True)
 (a.outdir/"night_campaign_summary.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
 if rows:
  with (a.outdir/"night_campaign_run_level.csv").open("w",newline="",encoding="utf-8") as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 with (a.outdir/"night_campaign_stage_summary.csv").open("w",newline="",encoding="utf-8") as f:
  flat=[]
  for s,d in by_stage.items():
   flat.append({k:v for k,v in d.items() if isinstance(v,(str,int,float,bool,type(None)))})
  w=csv.DictWriter(f,fieldnames=list(flat[0]) if flat else ["stage"]);w.writeheader();w.writerows(flat)
 print(json.dumps({"status":result["status"],"integrity_pass":integrity,"observed_run_count":len(rows),
  "run_counts_by_stage":actual,"errors":errors[:20]},indent=2))
 return 2 if errors or not integrity else 0
if __name__=="__main__":raise SystemExit(main())
