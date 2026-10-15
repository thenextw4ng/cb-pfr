#!/usr/bin/env python3
"""Fail-closed analyzer for the preregistered C5G7 B1 convergence pilot."""
from __future__ import annotations
import argparse,csv,json,math,statistics,xml.etree.ElementTree as ET
from pathlib import Path

GROUPS=(1e-5,0.0635,10.0,100.0,1000.0,500000.0,1000000.0,20000000.0)
BOUNDS={
 "baseline_all_fuel":(-32.13,-10.71,-1.0,10.71,32.13,1.0),
 "left_column_only":(-32.13,-10.71,-1.0,-10.71,32.13,1.0),
 "right_column_only":(-10.71,-10.71,-1.0,10.71,32.13,1.0),
 "upper_row_only":(-32.13,10.71,-1.0,10.71,32.13,1.0),
}
PROFILES=tuple(BOUNDS)
SOURCE_SEEDS=(810001,810002,810003)
INACTIVE_SEEDS=(820001,820002,820003)
INACTIVE_OPTIONS=(100,300,500,1000)
T90_DF2=2.919985580355516
K_DRIFT_MAX=25.0
ENTROPY_DRIFT_MAX=0.01
SOURCE_EQ_MARGIN=25.0

def paired_ci(vals):
 if len(vals)!=3: raise ValueError("source comparison must have three paired seeds")
 m=statistics.mean(vals); h=T90_DF2*statistics.stdev(vals)/math.sqrt(3)
 return m,m-h,m+h

def hash_file(path):
 import hashlib
 h=hashlib.sha256()
 with path.open("rb") as f:
  for block in iter(lambda:f.read(1048576),b""): h.update(block)
 return h.hexdigest()

def audit_one(summary_path,batches):
 rd=summary_path.parent
 meta=json.loads((rd/"B1_CASE_METADATA.json").read_text())
 study=json.loads(summary_path.read_text())
 if study.get("status")!="all_runs_completed_needs_independent_validation": raise ValueError("study did not complete")
 cases=study.get("cases",[])
 if len(cases)!=1 or cases[0].get("status")!="completed": raise ValueError("expected one completed UMMU case")
 case=cases[0]
 if case.get("candidate_id")!="c5g7-2x2-UMMU": raise ValueError("wrong candidate")
 prof=meta["source_profile"]; inactive=int(meta["inactive"]); seed=int(meta["seed_base"])
 if prof not in PROFILES: raise ValueError("unknown source profile")
 if study.get("initial_source_profile")!=prof or case.get("initial_source_profile")!=prof: raise ValueError("source profile metadata mismatch")
 settings=study["settings"]
 if (int(settings["batches"]),int(settings["inactive"]),int(settings["particles"]),int(settings["threads"]))!=(batches,inactive,10000,1): raise ValueError("wrong compute settings")
 if int(case["seed"])!=seed: raise ValueError("actual seed differs from requested seed")
 case_dir=rd/case["candidate_id"]; physical=case["physical_results"]
 rel=physical["statepoint"]; sp=case_dir/rel
 if not sp.is_file() or sp.stat().st_size==0: raise ValueError("statepoint missing")
 raw=json.loads((rd/"analysis/raw_hdf5_audit.json").read_text())
 trace=json.loads((rd/"analysis/source_convergence.json").read_text())
 if raw.get("status")!="PASS" or raw.get("candidate_count")!=1: raise ValueError("raw HDF5 audit failed")
 if trace.get("status")!="DIAGNOSTIC_REVIEW_REQUIRED" or not trace.get("entropy"): raise ValueError("missing entropy / k-generation diagnostics")
 edges=tuple(float(x) for x in physical.get("mgxs_energy_group_boundaries",[]))
 if physical.get("mgxs_group_structure_audit")!="PASS" or edges!=GROUPS: raise ValueError("standard C5G7 group structure fails")
 root=ET.parse(case_dir/"model/2d/settings.xml").getroot()
 space=next((x for x in root.iter() if x.tag.endswith("space") and x.get("type")=="box"),None)
 if space is None or not space.get("parameters"): raise ValueError("serialized initial source box absent")
 box=tuple(float(x) for x in space.get("parameters").split())
 if len(box)!=6 or any(abs(x-y)>1e-8 for x,y in zip(box,BOUNDS[prof])): raise ValueError("serialized source box differs from registered profile")
 if space.get("only_fissionable","true").lower() not in ("true","1"): raise ValueError("initial source not restricted to fissionable cells")
 log=case_dir/"model/2d/openmc.log"
 if not log.is_file(): raise ValueError("OpenMC log missing")
 warnings=log.read_text(errors="replace").count("Fission source site(s) outside of entropy box")
 if warnings: raise ValueError(f"entropy mesh warnings={warnings}")
 raw_case=raw["candidates"][0]
 if raw_case.get("statepoint_sha256")!=hash_file(sp): raise ValueError("statepoint hash disagreement")
 return {
  "group":meta["group"],"condition_id":meta["condition_id"],"source_profile":prof,
  "inactive":inactive,"seed":seed,"batches":batches,"particles":10000,"threads":1,
  "keff_mean":float(physical["keff_mean"]),"keff_std_dev":float(physical["keff_std_dev"]),
  "k_generation_half_delta_pcm":float(trace["k_generation_second_minus_first_half_pcm"]),
  "entropy_quarter_delta":float(trace["entropy"]["last_minus_first_quarter_mean"]),
  "entropy_slope_per_1000":float(trace["entropy"]["ols_slope_per_1000_active_batches"]),
  "warning_count":warnings,"raw_hdf5_audit":raw["status"],"statepoint_sha256":hash_file(sp),
  "mgxs_sha256":raw_case.get("mgxs_sha256"),"upstream_commit":study.get("upstream_commit"),
  "source_box_parameters":";".join(str(x) for x in box),"status":"PASS_INTEGRITY"
 }

def source_gate(rows,group,inactive,seeds):
 g=[r for r in rows if r["group"]==group and r["inactive"]==inactive]
 lookup={(r["source_profile"],r["seed"]):r for r in g}
 complete=all((p,s) in lookup for p in PROFILES for s in seeds)
 comparisons=[]
 for p in PROFILES:
  if p=="baseline_all_fuel": continue
  diffs=[(lookup[(p,s)]["keff_mean"]-lookup[("baseline_all_fuel",s)]["keff_mean"])*1e5 for s in seeds] if complete else []
  if complete:
   m,lo,hi=paired_ci(diffs); passed=lo>-SOURCE_EQ_MARGIN and hi<SOURCE_EQ_MARGIN
  else: m=lo=hi=None;passed=False
  comparisons.append({"profile":p,"paired_delta_pcm":diffs,"mean_delta_pcm":m,"ci90_low_pcm":lo,"ci90_high_pcm":hi,"equivalence_margin_pcm":SOURCE_EQ_MARGIN,"pass":passed})
 return {"group":group,"inactive":inactive,"complete":complete,"comparisons":comparisons,"pass":complete and all(x["pass"] for x in comparisons)}

def analyze(rows,errors,batches,mode):
 hashes=[r["statepoint_sha256"] for r in rows]; mgxs={r["mgxs_sha256"] for r in rows}
 integrity=bool(rows) and not errors and len(set(hashes))==len(hashes) and len(mgxs)==1 and None not in mgxs and all(r["raw_hdf5_audit"]=="PASS" and r["warning_count"]==0 and r["batches"]==batches for r in rows)
 if mode=="full_pilot":
  nsource=[r for r in rows if r["group"]=="initial"]
  ninact=[r for r in rows if r["group"]=="inactive"]
  sgate=source_gate(rows,"initial",500,SOURCE_SEEDS)
  checks=[]
  for n in INACTIVE_OPTIONS:
   g=[r for r in ninact if r["inactive"]==n]
   ok=len(g)==3 and {r["seed"] for r in g}==set(INACTIVE_SEEDS)
   kpass=ok and all(abs(r["k_generation_half_delta_pcm"])<=K_DRIFT_MAX for r in g)
   hpass=ok and all(abs(r["entropy_quarter_delta"])<=ENTROPY_DRIFT_MAX for r in g)
   checks.append({"inactive":n,"n":len(g),"seeds":sorted(r["seed"] for r in g),"k_drift_pass":kpass,"entropy_drift_pass":hpass,"eligible":kpass and hpass})
  eligible=[x["inactive"] for x in checks if x["eligible"]]
  recommended=min(eligible) if eligible else None
  complete=len(rows)==24 and len(nsource)==12 and len(ninact)==12
  prelim=integrity and complete and sgate["pass"] and recommended is not None
  confirm_needed=prelim and recommended!=500
  final=prelim and recommended==500
  status="B1_PASS" if final else "B1_PASS_PENDING_SELECTED_INACTIVE_SOURCE_CONFIRMATION" if confirm_needed else "B1_INCONCLUSIVE_NO_INACTIVE_PROFILE_PASSED" if recommended is None else "B1_INCONCLUSIVE_SOURCE_START_EQUIVALENCE_FAILED" if not sgate["pass"] else "B1_INCONCLUSIVE_INTEGRITY_FAILURE"
  selected_source=sgate if recommended==500 else None
 else:
  n=rows[0]["inactive"] if rows else -1
  sgate=source_gate(rows,"source_confirmation",n,(830001,830002,830003))
  checks=[];recommended=n if rows else None;complete=len(rows)==12
  final=integrity and complete and sgate["pass"];prelim=final;confirm_needed=False;selected_source=sgate
  status="B1_SELECTED_INACTIVE_SOURCE_CONFIRMATION_PASS" if final else "B1_SELECTED_INACTIVE_SOURCE_CONFIRMATION_INCONCLUSIVE"
 return {
  "schema_version":"1.0","protocol_id":"CBPFR-C5G7-PREREG-B0-2026-10-15","mode":mode,"status":status,
  "integrity_pass":integrity,"preliminary_gate_pass":prelim,"b1_gate_pass":final,
  "selected_source_confirmation_needed":confirm_needed,"recommended_inactive_batches":recommended,
  "recommended_total_batches":batches if final else None,"run_count":len(rows),"errors":errors,
  "source_equivalence":sgate,"selected_source_equivalence":selected_source,
  "inactive_sweep":checks,"criteria":{"k_generation_half_drift_pcm_max":K_DRIFT_MAX,"entropy_quarter_drift_nat_max":ENTROPY_DRIFT_MAX,"source_equivalence_ci":"90% paired Student-t, df=2, margin ±25 pcm"},
  "runs":rows,"nonclaims":["pilot only; not benchmark acceptance","B2 blocked unless b1_gate_pass is true","a passing pilot does not certify source convergence"]
 }

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--artifacts-root",type=Path,required=True);p.add_argument("--outdir",type=Path,required=True)
 p.add_argument("--batches",type=int,required=True);p.add_argument("--mode",choices=("full_pilot","source_confirmation"),default="full_pilot")
 a=p.parse_args()
 if a.outdir.exists() and any(a.outdir.iterdir()): p.error("refusing to overwrite non-empty output directory")
 paths=sorted(a.artifacts_root.rglob("STUDY_SUMMARY.json"));rows=[];errors=[]
 for path in paths:
  try: rows.append(audit_one(path,a.batches))
  except Exception as e: errors.append(f"{path}: {type(e).__name__}: {e}")
 report=analyze(rows,errors,a.batches,a.mode);a.outdir.mkdir(parents=True,exist_ok=True)
 if rows:
  with (a.outdir/"b1_run_level_results.csv").open("w",newline="",encoding="utf-8") as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 (a.outdir/"b1_pilot_summary.json").write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n")
 lines=["# C5G7 B1 convergence pilot","","Status: "+report["status"],"Runs audited: "+str(report["run_count"]),"Configured total batches: "+str(a.batches),"Recommended inactive batches: "+str(report["recommended_inactive_batches"]),"","Inactive sweep","","| Inactive | Runs | K-drift pass | Entropy-drift pass | Eligible |","|---:|---:|---|---|---|"]
 for x in report["inactive_sweep"]: lines.append(f"| {x['inactive']} | {x['n']} | {x['k_drift_pass']} | {x['entropy_drift_pass']} | {x['eligible']} |")
 lines.extend(["","Source-start equivalence","","| Profile | Mean delta pcm | 90% CI pcm | Pass |","|---|---:|---:|---|"])
 for x in report["source_equivalence"]["comparisons"]:
  m="NA" if x["mean_delta_pcm"] is None else f"{x['mean_delta_pcm']:.2f}"
  ci="NA" if x["ci90_low_pcm"] is None else f"[{x['ci90_low_pcm']:.2f}, {x['ci90_high_pcm']:.2f}]"
  lines.append(f"| {x['profile']} | {m} | {ci} | {x['pass']} |")
 lines.extend(["","This is a pilot only. Inconclusive criteria block B2 until a versioned extension passes."])
 (a.outdir/"b1_pilot_report.md").write_text("\n".join(lines)+"\n")
 print(json.dumps({"status":report["status"],"run_count":report["run_count"],"recommended_inactive_batches":report["recommended_inactive_batches"],"b1_gate_pass":report["b1_gate_pass"],"integrity_pass":report["integrity_pass"]},indent=2))
 return 2 if errors or not report["integrity_pass"] else 0

if __name__=="__main__": raise SystemExit(main())
