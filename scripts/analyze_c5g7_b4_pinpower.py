#!/usr/bin/env python3
"""Audit B2 statepoints and evaluate the canonical C5G7 pin-power comparison.

B4 does not pass on k-effective alone. A reviewed Appendix-D reference table,
explicit pin indexing/normalization, uncertainty metadata, and preregistered
acceptance limits are required. Without them, results are retained as blocked.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,statistics
from pathlib import Path
import numpy as np
import openmc

EXPECTED_SEEDS=set(range(8200001,8200011))
GROUPS=(1e-5,0.0635,10.0,100.0,1000.0,500000.0,1000000.0,20000000.0)
NON_FUEL={
 (r,c)
 for r,cols in {
  2:(5,8,11),3:(3,13),5:(2,5,8,11,14),
  8:(2,5,8,11,14),11:(2,5,8,11,14),13:(3,13),14:(5,8,11)
 }.items() for c in cols
}
EXPECTED_PROFILE_KEYS=("batches","inactive","particles","threads")


def file_hash(path:Path)->str:
 h=hashlib.sha256()
 with path.open("rb") as f:
  for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
 return h.hexdigest()


def fuel_mask():
 mask=np.ones((34,34),dtype=bool)
 for row in range(34):
  for col in range(34):
   _,ir=divmod(row,17);_,ic=divmod(col,17)
   if (ir,ic) in NON_FUEL:mask[row,col]=False
 if int(mask.sum())!=1056:raise ValueError(f"expected 1056 fissionable fuel pins, got {mask.sum()}")
 return mask


def extract_pin_map(statepoint:Path):
 with openmc.StatePoint(statepoint) as sp:
  tally=sp.get_tally(name="tally 1")
  mesh_filter=next((f for f in tally.filters if isinstance(f,openmc.MeshFilter)),None)
  if mesh_filter is None:raise ValueError("fission tally missing MeshFilter")
  mesh=mesh_filter.mesh
  if list(mesh.dimension)!=[51,51,1]:raise ValueError(f"expected mesh [51,51,1], got {list(mesh.dimension)}")
  if "fission" not in tally.scores:raise ValueError(f"tally lacks fission score {tally.scores}")
  edges=tuple(float(x) for x in mesh.lower_left[:2])+tuple(float(x) for x in mesh.upper_right[:2])
  if any(abs(a-b)>1e-9 for a,b in zip(edges,(-32.14,-32.14,32.14,32.14))):
   raise ValueError(f"mesh bounds differ from registered B0 bounds: {edges}")
  vals=np.asarray(tally.get_reshaped_data(value="mean",expand_dims=True),dtype=float).reshape((51,51,1,-1,len(tally.scores)))
  sd=np.asarray(tally.get_reshaped_data(value="std_dev",expand_dims=True),dtype=float).reshape((51,51,1,-1,len(tally.scores)))
  idx=tally.scores.index("fission")
  grid=vals[:,:,0,0,idx]
  grid_sd=sd[:,:,0,0,idx]
  # Pin row 0 is highest-y; pin column 0 is lowest-x, per official Figure 3.
  pin=np.asarray([[grid[col,50-row] for col in range(34)] for row in range(34)],dtype=float)
  pin_sd=np.asarray([[grid_sd[col,50-row] for col in range(34)] for row in range(34)],dtype=float)
  if not np.all(np.isfinite(pin)) or np.any(pin<0):raise ValueError("invalid fission-mesh values")
  mask=fuel_mask()
  if np.any(pin[mask]<=0):raise ValueError("one or more fuel pin tallies are non-positive")
  mean=float(pin[mask].mean())
  norm=pin/mean
  # Per-run normalized map; seed-to-seed variation is retained at aggregate time.
  return {
   "pin_power_normalized":norm,
   "pin_power_raw":pin,
   "pin_power_sd_raw":pin_sd,
   "normalization_mean_fission_rate":mean,
   "fuel_mask":mask,
   "keff_mean":float(sp.keff.nominal_value),
   "keff_sd":float(sp.keff.std_dev),
   "n_batches":int(sp.n_batches),
   "n_inactive":int(sp.n_inactive),
   "n_particles":int(sp.n_particles),
   "seed":int(sp.seed),
   "mesh_bounds":edges,
  }


def load_b2(artifacts_root:Path):
 rows=[];maps=[];errors=[]
 for p in sorted(artifacts_root.rglob("STUDY_SUMMARY.json")):
  try:
   study=json.loads(p.read_text())
   if study.get("status")!="all_runs_completed_needs_independent_validation":raise ValueError("study incomplete")
   if study.get("upstream_commit")!="ba41bee54320ada0b4ac39a0dd2ca3c1d090a450":raise ValueError("wrong upstream revision")
   cases=study.get("cases",[])
   if len(cases)!=1 or cases[0].get("candidate_id")!="c5g7-2x2-UMMU" or cases[0].get("status")!="completed":
    raise ValueError("not one completed canonical UMMU case")
   case=cases[0];physical=case["physical_results"];seed=int(case["seed"])
   if seed not in EXPECTED_SEEDS:raise ValueError(f"unexpected B2 seed {seed}")
   case_dir=p.parent/case["candidate_id"]
   sp=case_dir/physical["statepoint"]
   raw_p=p.parent/"analysis/raw_hdf5_audit.json"
   trace_p=p.parent/"analysis/source_convergence.json"
   log_p=case_dir/"model/2d/openmc.log"
   for x in (sp,raw_p,trace_p,log_p):
    if not x.is_file():raise ValueError(f"missing {x}")
   raw=json.loads(raw_p.read_text());trace=json.loads(trace_p.read_text())
   if raw.get("status")!="PASS":raise ValueError("raw HDF5 audit not PASS")
   if trace.get("status")!="DIAGNOSTIC_REVIEW_REQUIRED" or not trace.get("entropy"):raise ValueError("source traces absent")
   log=log_p.read_text(errors="replace")
   if log.count("Fission source site(s) outside of entropy box"):raise ValueError("entropy mesh warning")
   group_edges=tuple(float(x) for x in physical.get("mgxs_energy_group_boundaries",[]))
   if physical.get("mgxs_group_structure_audit")!="PASS" or group_edges!=GROUPS:raise ValueError("nonstandard energy group structure")
   run=extract_pin_map(sp)
   if run["seed"]!=seed:raise ValueError("statepoint seed mismatch")
   row={"seed":seed,"keff_mean":run["keff_mean"],"keff_sd":run["keff_sd"],
        "statepoint_sha256":file_hash(sp),"settings_sha256":raw["candidates"][0]["settings_sha256"],
        "mgxs_sha256":raw["candidates"][0]["mgxs_sha256"],"source_trace_status":trace["status"],
        "warning_count":0,"batches":run["n_batches"],"inactive":run["n_inactive"],"particles":run["n_particles"]}
   rows.append(row);maps.append(run["pin_power_normalized"])
  except Exception as e:errors.append(f"{p}: {type(e).__name__}: {e}")
 return rows,maps,errors


def evaluate_reference(reference_csv:Path,manifest_path:Path,mean_map:np.ndarray,between_seed_sd:np.ndarray,mask:np.ndarray,output:Path):
 if not reference_csv.is_file() or not manifest_path.is_file():
  return {"status":"B4_BLOCKED_REFERENCE_DATA_NOT_PRESENT","b4_gate_pass":False,"reason":"The official NEA Appendix-D pin-power table and reviewed manifest are not both present."}
 manifest=json.loads(manifest_path.read_text())
 if manifest.get("review_status")!="independently_reviewed":
  return {"status":"B4_BLOCKED_REFERENCE_MANIFEST_NOT_SIGNED_OFF","b4_gate_pass":False,"reason":"Reference manifest needs independent review."}
 if manifest.get("primary_source_url")!="https://www.oecd-nea.org/jcms/pl_73373/appendices-d-i-benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation-a-2-d/3-d-mox-fuel-assembly-benchmark?details=true":
  return {"status":"B4_BLOCKED_REFERENCE_PROVENANCE_MISMATCH","b4_gate_pass":False,"reason":"Reference source URL is not the registered official NEA Appendix D-I resource."}
 expected_hash=manifest.get("csv_sha256")
 if not expected_hash or file_hash(reference_csv)!=expected_hash:
  return {"status":"B4_BLOCKED_REFERENCE_HASH_MISMATCH","b4_gate_pass":False,"reason":"Reference CSV hash differs from reviewed manifest."}
 rows=[]
 with reference_csv.open(newline="",encoding="utf-8-sig") as f:
  rows=list(csv.DictReader(f))
 if len(rows)!=1056: return {"status":"B4_BLOCKED_REFERENCE_ROW_COUNT","b4_gate_pass":False,"reason":f"Expected 1056 active fuel pins, got {len(rows)}."}
 coords=set();ref=[];calc=[];calc_se=[];pins=[]
 for r in rows:
  row=int(r["pin_row"]);col=int(r["pin_col"])
  if not (1<=row<=34 and 1<=col<=34):raise ValueError(f"invalid pin coordinate {(row,col)}")
  if not mask[row-1,col-1]:raise ValueError(f"reference includes non-fuel cell {(row,col)}")
  if (row,col) in coords:raise ValueError(f"duplicate reference pin {(row,col)}")
  coords.add((row,col))
  rv=float(r["reference_normalized_power"])
  if not math.isfinite(rv) or rv<=0:raise ValueError(f"invalid reference power {(row,col)}")
  sd_text=r.get("reference_standard_uncertainty","").strip()
  if not sd_text:return {"status":"B4_BLOCKED_REFERENCE_UNCERTAINTY_MISSING","b4_gate_pass":False,"reason":"The reviewed pin-power data do not include reference uncertainty."}
  r_sd=float(sd_text)
  if not math.isfinite(r_sd) or r_sd<0:raise ValueError(f"invalid reference uncertainty {(row,col)}")
  ref.append(rv);calc.append(float(mean_map[row-1,col-1]))
  calc_se.append(float(between_seed_sd[row-1,col-1]/math.sqrt(10)))
  pins.append((row,col,rv,r_sd,float(mean_map[row-1,col-1]),float(between_seed_sd[row-1,col-1])))
  if (r_sd/rv*100)>float(manifest.get("reference_relative_uncertainty_pct_max_allowed",math.inf)):
   return {"status":"B4_BLOCKED_REFERENCE_UNCERTAINTY_SCREEN","b4_gate_pass":False,"reason":"Reference uncertainty exceeds the reviewed manifest's allowable uncertainty screen."}
 if len(coords)!=1056:return {"status":"B4_BLOCKED_REFERENCE_PIN_COVERAGE","b4_gate_pass":False,"reason":"Pin coordinates are incomplete."}
 if not math.isclose(statistics.mean(ref),1.0,rel_tol=0,abs_tol=0.005):
  return {"status":"B4_BLOCKED_REFERENCE_NORMALIZATION","b4_gate_pass":False,"reason":f"Mean reference power over fuel pins is {statistics.mean(ref):.6f}, expected 1 within 0.5%."}
 # AVG/RMS/MAX refer to absolute percentage error, consistent with benchmark reporting.
 errors_pct=[(a-r)/r*100.0 for a,r in zip(calc,ref)]
 avg=float(np.mean(np.abs(errors_pct)));rms=float(np.sqrt(np.mean(np.square(errors_pct))))
 maxerr=float(np.max(np.abs(errors_pct)))
 limits=manifest.get("predeclared_project_screen_limits_pct")
 if not isinstance(limits,dict) or not all(k in limits for k in ("avg","rms","max_abs")):
  status="B4_BLOCKED_NO_PREDECLARED_PINPOWER_LIMITS";passed=False
 else:
  passed=avg<=float(limits["avg"]) and rms<=float(limits["rms"]) and maxerr<=float(limits["max_abs"])
  status="B4_PASS" if passed else "B4_FAIL_PINPOWER_SCREEN"
 with output.open("w",newline="",encoding="utf-8") as f:
  w=csv.writer(f);w.writerow(["pin_row","pin_col","reference_normalized_power","reference_standard_uncertainty","openmc_mean_normalized_power","openmc_between_seed_sd","relative_error_percent"])
  for ((row,col,rv,rs,cv,cs),err) in zip(pins,errors_pct):w.writerow([row,col,rv,rs,cv,cs,err])
 return {"status":status,"b4_gate_pass":passed,"n_fuel_pins":1056,"avg_abs_relative_error_pct":avg,
         "rms_relative_error_pct":rms,"max_abs_relative_error_pct":maxerr,
         "reference_normalized_mean":statistics.mean(ref),"normalization":"each run normalized to mean of 1056 fissionable fuel pins",
         "limits":limits if isinstance(manifest.get("predeclared_project_screen_limits_pct"),dict) else None,
         "note":"A passing numerical screen is not official benchmark acceptance without independent model-identity sign-off."}


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--artifacts-root",type=Path,required=True);p.add_argument("--b2-summary",type=Path,required=True)
 p.add_argument("--reference-csv",type=Path,default=Path("data/reference/c5g7_2d_reference_pin_power.csv"))
 p.add_argument("--reference-manifest",type=Path,default=Path("data/reference/c5g7_2d_reference_pin_power_manifest.json"))
 p.add_argument("--outdir",type=Path,required=True);a=p.parse_args()
 if a.outdir.exists() and any(a.outdir.iterdir()):p.error("refusing to overwrite non-empty output directory")
 summary=json.loads(a.b2_summary.read_text())
 if not summary.get("b2_gate_pass"):
  report={"protocol_id":"CBPFR-C5G7-PREREG-B0-2026-10-15","status":"B4_BLOCKED_B2_GATE_NOT_PASSED","b4_gate_pass":False,"b2_status":summary.get("status")}
  a.outdir.mkdir(parents=True,exist_ok=True);(a.outdir/"b4_summary.json").write_text(json.dumps(report,indent=2)+"\n")
  print(json.dumps(report,indent=2));return 0
 rows,maps,errors=load_b2(a.artifacts_root)
 if errors or len(rows)!=10 or {x["seed"] for x in rows}!=EXPECTED_SEEDS:
  report={"protocol_id":"CBPFR-C5G7-PREREG-B0-2026-10-15","status":"B4_BLOCKED_B2_ARTIFACT_INTEGRITY","b4_gate_pass":False,"run_count":len(rows),"errors":errors}
 else:
  arr=np.stack(maps)
  mean_map=arr.mean(axis=0);sd_map=arr.std(axis=0,ddof=1)
  mask=fuel_mask();a.outdir.mkdir(parents=True,exist_ok=True)
  with (a.outdir/"b2_pin_power_maps.csv").open("w",newline="",encoding="utf-8") as f:
   w=csv.writer(f);w.writerow(["pin_row","pin_col","is_fissionable_fuel","mean_normalized_power","between_seed_sd","between_seed_se"])
   for row in range(34):
    for col in range(34):w.writerow([row+1,col+1,bool(mask[row,col]),float(mean_map[row,col]),float(sd_map[row,col]),float(sd_map[row,col]/math.sqrt(10))])
  b4=evaluate_reference(a.reference_csv,a.reference_manifest,mean_map,sd_map,mask,a.outdir/"b4_pinpower_comparison.csv")
  keff=[r["keff_mean"] for r in rows]
  report={"protocol_id":"CBPFR-C5G7-PREREG-B0-2026-10-15","status":b4["status"],"b2_gate_pass":True,
          "b4_gate_pass":bool(b4["b4_gate_pass"]),"b2_runs":len(rows),
          "b2_keff_mean":statistics.mean(keff),"b2_between_seed_sd":statistics.stdev(keff),
          "b2_run_level_results":rows,"pin_map_file":"b2_pin_power_maps.csv",
          "reference_comparison":b4,
          "official_benchmark_acceptance":False,
          "explicit_blockers":["independent model-identity sign-off against the primary specification remains required",
          "C5G7 is a computational benchmark and does not validate unmeasured noncanonical-layout rankings experimentally"]}
 a.outdir.mkdir(parents=True,exist_ok=True)
 (a.outdir/"b4_summary.json").write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n")
 (a.outdir/"b4_report.md").write_text("# B4 canonical pin-power comparison\n\n"+f"Status: **{report['status']}**\n\nB2 runs used: {report['b2_runs'] if 'b2_runs' in report else 0}\n\n"+json.dumps(report,indent=2)+"\n")
 if rows:
  with (a.outdir/"b2_run_level_results.csv").open("w",newline="",encoding="utf-8") as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print(json.dumps({"status":report["status"],"b4_gate_pass":report.get("b4_gate_pass",False),"reference_comparison":report.get("reference_comparison")},indent=2))
 # Blocked/missing reference data are valid and reportable, not infrastructure errors.
 return 2 if errors else 0

if __name__=="__main__":raise SystemExit(main())
