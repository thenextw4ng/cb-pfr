#!/usr/bin/env python3
"""Trace-level operational review of archived C5G7/OpenMC runs (not certification)."""
from __future__ import annotations
import argparse, csv, json, math, statistics
from pathlib import Path
WARNING = "Fission source site(s) outside of entropy box"
DEFAULTS = {
    "max_abs_k_half_shift_pcm": 25.0,
    "max_abs_k_slope_pcm_per_1000_active_batches": 25.0,
    "max_abs_entropy_quartile_relative_drift_pct": 0.1,
    "max_abs_entropy_slope_relative_pct_per_1000_active_batches": 0.1,
    "minimum_active_batches": 100,
}
def mean(xs):
    return statistics.fmean(xs) if xs else math.nan
def slope_per_1000(xs):
    n=len(xs)
    if n<2: return math.nan
    xm,ym=(n-1)/2.0,mean(xs); den=sum((i-xm)**2 for i in range(n))
    return 1000.0*sum((i-xm)*(v-ym) for i,v in enumerate(xs))/den if den else math.nan
def active_trace(path):
    with path.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    k=[];h=[]
    for r in rows:
        if str(r.get("active","")).lower() not in ("true","1","yes"): continue
        if r.get("k_generation") not in ("",None): k.append(float(r["k_generation"]))
        if r.get("shannon_entropy") not in ("",None): h.append(float(r["shannon_entropy"]))
    if len(k)<4 or len(h)<4 or not all(math.isfinite(x) for x in k+h):
        raise ValueError("active k-generation/entropy trace is missing, short, or non-finite")
    return k,h
def inspect(study_path,thresholds):
    root=study_path.parent; out={"artifact_path":str(study_path),"status":"REVIEW_REQUIRED","screen_pass":False}
    try:
        study=json.loads(study_path.read_text());mp=root/"NIGHT_RUN_METADATA.json"
        if not mp.is_file(): raise ValueError("missing NIGHT_RUN_METADATA.json")
        meta=json.loads(mp.read_text()); cases=study.get("cases",[])
        if len(cases)!=1: raise ValueError("expected one transport case")
        case=cases[0];phys=case.get("physical_results",{})
        if case.get("status")!="completed" or phys.get("status")!="completed": raise ValueError("OpenMC case not complete")
        stage=str(meta.get("stage","UNKNOWN"))
        out.update({"run_id":meta.get("run_id",root.name),"stage":stage,"signature":meta.get("signature","UNKNOWN"),
          "seed":meta.get("seed",case.get("seed")),"batches":(study.get("settings") or {}).get("batches"),
          "inactive":(study.get("settings") or {}).get("inactive"),"particles":(study.get("settings") or {}).get("particles"),
          "source_profile":meta.get("source")})
        ana=root/"analysis"; rawp=ana/"raw_hdf5_audit.json"; srcp=ana/"source_convergence.json"; tracep=ana/"source_convergence.csv"
        logp=root/case.get("candidate_id","")/"openmc.log"
        for p in (rawp,srcp,tracep):
            if not p.is_file(): raise ValueError("missing audit or trace evidence: "+p.name)
        raw=json.loads(rawp.read_text());src=json.loads(srcp.read_text());k,h=active_trace(tracep)
        n=min(len(k),len(h));k,h=k[:n],h[:n];half=n//2;q=max(1,n//4)
        khalf=(mean(k[half:])-mean(k[:half]))*1e5; kslope=slope_per_1000(k)*1e5; hm=mean(h)
        hquart=abs(mean(h[-q:])-mean(h[:q]))/abs(hm)*100 if hm else math.inf
        hslope=abs(slope_per_1000(h))/abs(hm)*100 if hm else math.inf
        warnings=logp.read_text(errors="replace").count(WARNING) if logp.is_file() else None
        integrity=raw.get("status")=="PASS" and raw.get("candidate_count")==1 and warnings==0
        checks={"integrity_gate":integrity,"minimum_active_batches":n>=thresholds["minimum_active_batches"],
          "k_half_shift":abs(khalf)<=thresholds["max_abs_k_half_shift_pcm"],
          "k_slope":abs(kslope)<=thresholds["max_abs_k_slope_pcm_per_1000_active_batches"],
          "entropy_quartile_drift":hquart<=thresholds["max_abs_entropy_quartile_relative_drift_pct"],
          "entropy_slope":hslope<=thresholds["max_abs_entropy_slope_relative_pct_per_1000_active_batches"]}
        out.update({"active_batches":n,"k_generation_half_shift_pcm":khalf,"k_generation_slope_pcm_per_1000_active_batches":kslope,
          "entropy_quartile_relative_drift_pct":hquart,"entropy_slope_relative_pct_per_1000_active_batches":hslope,
          "raw_hdf5_audit_status":raw.get("status"),"source_diagnostic_status":src.get("status"),
          "mesh_warning_count":warnings,"integrity_gate_pass":integrity,"screen_checks":checks,
          "failed_screen_checks":[k for k,v in checks.items() if not v]})
        out["status"]="SCREEN_PASS" if all(checks.values()) else "SCREEN_FAIL_NEEDS_REVIEW_OR_MORE_HISTORIES"
        out["screen_pass"]=all(checks.values())
    except Exception as exc:
        out["error"]=type(exc).__name__+": "+str(exc);out["status"]="REVIEW_REQUIRED"
    return out
def write_csv(path,rows):
    cols=[]
    for row in rows:
        for k in row:
            if k not in cols: cols.append(k)
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore");w.writeheader()
        for r in rows: w.writerow({k:json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in r.items()})
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--production-root",type=Path,required=True);ap.add_argument("--v2a-root",type=Path,required=True)
    ap.add_argument("--outdir",type=Path,required=True);ap.add_argument("--expected-production-runs",type=int,default=75)
    ap.add_argument("--expected-v2a-runs",type=int,default=1200);ap.add_argument("--thresholds-json",type=Path)
    a=ap.parse_args()
    if a.outdir.exists() and any(a.outdir.iterdir()): ap.error("refusing to overwrite non-empty output directory")
    limits=dict(DEFAULTS)
    if a.thresholds_json:
        loaded=json.loads(a.thresholds_json.read_text());limits.update(loaded.get("thresholds",loaded))
    pp=sorted(a.production_root.rglob("STUDY_SUMMARY.json"));vp=sorted(a.v2a_root.rglob("STUDY_SUMMARY.json"))
    rows=[inspect(p,limits) for p in pp+vp];seen=set();dups=[]
    for r in rows:
        rid=r.get("run_id")
        if rid and rid in seen: dups.append(rid)
        elif rid: seen.add(rid)
    stage_rows=[]
    for stage in sorted({str(r.get("stage","UNKNOWN")) for r in rows}):
        g=[r for r in rows if str(r.get("stage","UNKNOWN"))==stage]
        stage_rows.append({"stage":stage,"count":len(g),"screen_pass":sum(bool(r.get("screen_pass")) for r in g),
          "screen_fail":sum(r["status"]=="SCREEN_FAIL_NEEDS_REVIEW_OR_MORE_HISTORIES" for r in g),
          "review_required":sum(r["status"]=="REVIEW_REQUIRED" for r in g)})
    complete=len(pp)==a.expected_production_runs and len(vp)==a.expected_v2a_runs and not dups
    summary={"schema_version":"1.0","study_id":"CBPFR-C5G7-convergence-screen-2026-10-16",
      "status":"COMPLETE_SCREENED_PENDING_SCIENTIFIC_REVIEW" if complete else "INCOMPLETE_OR_DUPLICATE_ARTIFACTS",
      "production_artifact_count":len(pp),"production_expected_count":a.expected_production_runs,
      "v2a_artifact_count":len(vp),"v2a_expected_count":a.expected_v2a_runs,"unique_run_ids":len(seen),"duplicate_run_ids":dups,
      "run_level_count":len(rows),"screen_pass":sum(bool(r.get("screen_pass")) for r in rows),
      "screen_fail":sum(r["status"]=="SCREEN_FAIL_NEEDS_REVIEW_OR_MORE_HISTORIES" for r in rows),
      "review_required":sum(r["status"]=="REVIEW_REQUIRED" for r in rows),"by_stage":stage_rows,"thresholds":limits,
      "thresholds_are_operational_screens_not_official_acceptance":True,"threshold_origin":"Operational cutoffs fixed after preliminary artifact spot-checks; not a blinded preregistered acceptance test.","convergence_certified":False,"official_benchmark_acceptance":False,
      "interpretation":"SCREEN_PASS means only no declared operational alarm was triggered. It does not certify source/eigenvalue convergence, model validity, or benchmark acceptance. Review failing traces and choose follow-up from the diagnostic evidence."}
    a.outdir.mkdir(parents=True,exist_ok=True);write_csv(a.outdir/"convergence_run_level.csv",rows)
    (a.outdir/"convergence_study_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2,sort_keys=True));return 0
if __name__=="__main__": raise SystemExit(main())
