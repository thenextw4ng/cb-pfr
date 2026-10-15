#!/usr/bin/env python3
"""Analyze R0 paired determinism, wall-clock, and archived settings diff."""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np

def load_runs(root):
    out={}
    for summary_path in root.rglob("STUDY_SUMMARY.json"):
        study=json.loads(summary_path.read_text())
        cases=study.get("cases",[])
        if len(cases)!=1 or cases[0].get("status")!="completed":
            continue
        case=cases[0]
        meta_path=summary_path.parent/"R0_METADATA.json"
        if not meta_path.is_file():
            continue
        run_id=json.loads(meta_path.read_text())["run_id"]
        case_dir=summary_path.parent/case["candidate_id"]
        trace_path=case_dir/"trace.npz"
        manifest_path=case_dir/"RUN_MANIFEST.json"
        if not trace_path.is_file() or not manifest_path.is_file():
            continue
        with np.load(trace_path,allow_pickle=False) as z:
            trace={k:np.array(z[k]) for k in z.files}
        manifest=json.loads(manifest_path.read_text())
        out[run_id]={"study":study,"case":case,"trace":trace,"manifest":manifest,
                     "trace_path":str(trace_path),"manifest_path":str(manifest_path)}
    return out

def eq(a,b):
    aa=np.asarray(a);bb=np.asarray(b)
    return aa.shape==bb.shape and np.array_equal(aa,bb,equal_nan=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--artifacts-root",type=Path,required=True)
    p.add_argument("--old-settings-diff",type=Path)
    p.add_argument("--outdir",type=Path,required=True)
    a=p.parse_args()
    if a.outdir.exists() and any(a.outdir.iterdir()):p.error("refusing to overwrite a non-empty output directory")
    runs=load_runs(a.artifacts_root)
    errors=[]
    def one(run_id):
        if run_id not in runs:
            errors.append(f"missing R0 run {run_id}")
            return None
        return runs[run_id]
    a50=one("R0a_i50");a150=one("R0a_i150");t1=one("R0b_t1");t2=one("R0b_t2");r0c=one("R0c")
    result={"protocol_id":"CBPFR-C5G7-NIGHT-CAMPAIGN-2026-10-15","status":"R0_COMPLETE_WITH_REVIEW",
      "run_count":len(runs),"errors":errors,"R0a":{},"R0b":{},"R0c":{},"R0d":{}}
    if a50 and a150:
        x=a50["trace"];y=a150["trace"]
        result["R0a"]={"seed_50":int(x["seed"][0]),"seed_150":int(y["seed"][0]),
          "same_seed":int(x["seed"][0])==int(y["seed"][0]),
          "k_generation_identical":eq(x["k_generation"],y["k_generation"]),
          "k_generation_length_50":len(x["k_generation"]),"k_generation_length_150":len(y["k_generation"]),
          "keff_mean_50":float(x["keff_mean"][0]),"keff_mean_150":float(y["keff_mean"][0]),
          "difference_keff_pcm":(float(x["keff_mean"][0])-float(y["keff_mean"][0]))*1e5,
          "entropy_identical":eq(x["entropy"],y["entropy"]),
          "protocol_A_B_replay_needed":not eq(x["k_generation"],y["k_generation"]),
          "interpretation":"Same-seed raw batch traces are compared directly; changing only n_inactive should not alter the underlying transport random stream."}
    if t1 and t2:
        x=t1["trace"];y=t2["trace"]
        result["R0b"]={"seed_1_thread":int(x["seed"][0]),"seed_2_threads":int(y["seed"][0]),
          "same_seed":int(x["seed"][0])==int(y["seed"][0]),
          "k_generation_identical":eq(x["k_generation"],y["k_generation"]),
          "entropy_identical":eq(x["entropy"],y["entropy"]),
          "tally_mesh_mean_identical":eq(x["tally_1_mean"],y["tally_1_mean"]) if "tally_1_mean" in x and "tally_1_mean" in y else False,
          "keff_mean_1_thread":float(x["keff_mean"][0]),"keff_mean_2_threads":float(y["keff_mean"][0]),
          "keff_difference_pcm":(float(x["keff_mean"][0])-float(y["keff_mean"][0]))*1e5,
          "interpretation":"Bitwise equality is reported as an empirical result, not assumed for every OpenMC build."}
    if r0c:
        secs=float(r0c["manifest"].get("run_wallclock_seconds",math.nan))
        result["R0c"]={"run_wallclock_seconds":secs,"settings":r0c["study"]["settings"],
          "estimated_7000x10000_seconds_linear_history_scaling":secs*7000/500 if math.isfinite(secs) else None,
          "estimate_caveat":"Scaling from a 500-batch pilot is rough and must be adjusted for per-batch startup/output overhead and different particle counts."}
    if a.old_settings_diff and a.old_settings_diff.is_file():
        result["R0d"]=json.loads(a.old_settings_diff.read_text())
    else:
        result["R0d"]={"status":"BLOCKED_NO_ARCHIVED_SETTINGS_DIFF","reason":"Old Protocol A/B artifact comparison was not supplied by the artifact-download step."}
    result["status"]="R0_COMPLETE" if not errors else "R0_INCOMPLETE"
    result["main_protocol_dispatch_recommended"]=not errors
    result["protocol_A_B_replay_needed"]=bool(result.get("R0a",{}).get("protocol_A_B_replay_needed",False))
    a.outdir.mkdir(parents=True,exist_ok=True)
    (a.outdir/"r0_summary.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    lines=["# R0 quick characterization","","Status: "+result["status"],
      "Protocol A/B replay needed: "+str(result["protocol_A_B_replay_needed"]),
      "","## R0a: 300 batches, inactive 50 vs 150","",
      json.dumps(result["R0a"],indent=2),"","## R0b: 1 vs 2 threads","",
      json.dumps(result["R0b"],indent=2),"","## R0c: wall-clock","",
      json.dumps(result["R0c"],indent=2),"","## R0d: prior settings.xml diff","",
      json.dumps(result["R0d"],indent=2)]
    (a.outdir/"r0_report.md").write_text("\n".join(lines)+"\n")
    print(json.dumps({"status":result["status"],"protocol_A_B_replay_needed":result["protocol_A_B_replay_needed"],
      "R0a":result["R0a"],"R0b":result["R0b"],"R0c":result["R0c"],"R0d":result["R0d"]},indent=2))
    return 2 if errors else 0
if __name__=="__main__":raise SystemExit(main())
