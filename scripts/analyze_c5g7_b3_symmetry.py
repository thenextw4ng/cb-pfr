#!/usr/bin/env python3
"""Aggregate B3 six-layout repeats and paired TOST mirror-equivalence tests."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,statistics,xml.etree.ElementTree as ET
from pathlib import Path

EXPECTED={
 "c5g7-2x2-MMUU":"MMUU","c5g7-2x2-MUMU":"MUMU","c5g7-2x2-MUUM":"MUUM",
 "c5g7-2x2-UMMU":"UMMU","c5g7-2x2-UMUM":"UMUM","c5g7-2x2-UUMM":"UUMM"}
POSITIONS=("p00","p01","p10","p11")
SEEDS=set(range(9200001,9200011))
GROUPS=(1e-5,0.0635,10.,100.,1000.,500000.,1000000.,20000000.)
MARGIN_PCM=12.
T90_DF9=1.8331129326536335

def sha256(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1048576),b""):h.update(block)
 return h.hexdigest()

def signature(layout):
 return "".join("M" if layout.get(p)=="MOX" else "U" if layout.get(p)=="UO2" else "?" for p in POSITIONS)

def load(root,batches,inactive):
 rows=[];errors=[]
 for p in sorted(root.rglob("STUDY_SUMMARY.json")):
  try:
   study=json.loads(p.read_text())
   if study.get("status")!="all_runs_completed_needs_independent_validation":raise ValueError("study not completed")
   if study.get("upstream_commit")!="ba41bee54320ada0b4ac39a0dd2ca3c1d090a450":raise ValueError("wrong upstream revision")
   cases=study.get("cases",[])
   if len(cases)!=1:raise ValueError("expected one candidate")
   case=cases[0];cid=case.get("candidate_id");sig=signature(case.get("layout") or {})
   if cid not in EXPECTED or sig!=EXPECTED[cid]:raise ValueError("layout signature mismatch")
   if case.get("status")!="completed":raise ValueError("case not completed")
   seed=int(case["seed"])
   if seed not in SEEDS:raise ValueError(f"unregistered B3 seed {seed}")
   s=study["settings"]
   if (int(s["batches"]),int(s["inactive"]),int(s["particles"]),int(s["threads"]))!=(batches,inactive,10000,1):raise ValueError("budget mismatch")
   cd=p.parent/cid;phys=case["physical_results"];sp=cd/phys["statepoint"]
   rawp=p.parent/"analysis/raw_hdf5_audit.json";tracep=p.parent/"analysis/source_convergence.json";fissp=p.parent/"analysis/assembly_fission.json"
   settingsp=cd/"model/2d/settings.xml";logp=cd/"model/2d/openmc.log"
   for f in (sp,rawp,tracep,fissp,settingsp,logp):
    if not f.is_file():raise ValueError(f"missing evidence {f}")
   raw=json.loads(rawp.read_text());trace=json.loads(tracep.read_text());fiss=json.loads(fissp.read_text())
   if raw.get("status")!="PASS" or raw.get("candidate_count")!=1:raise ValueError("raw HDF5 audit failed")
   if trace.get("status")!="DIAGNOSTIC_REVIEW_REQUIRED" or not trace.get("entropy"):raise ValueError("source traces absent")
   if fiss.get("candidate_id")!=cid or fiss.get("layout_signature")!=sig:raise ValueError("fission tally identity mismatch")
   edges=tuple(float(x) for x in phys.get("mgxs_energy_group_boundaries",[]))
   if phys.get("mgxs_group_structure_audit")!="PASS" or edges!=GROUPS:raise ValueError("standard seven-group audit failed")
   if int(ET.parse(settingsp).getroot().findtext("seed"))!=seed:raise ValueError("statepoint/settings seed mismatch")
   if logp.read_text(errors="replace").count("Fission source site(s) outside of entropy box"):raise ValueError("entropy mesh warning")
   if raw["candidates"][0].get("statepoint_sha256")!=sha256(sp):raise ValueError("statepoint hash mismatch")
   rows.append({"candidate_id":cid,"layout_signature":sig,"seed":seed,"keff_mean":float(phys["keff_mean"]),
    "keff_sd":float(phys["keff_std_dev"]),"fission_rate_peaking_factor":float(fiss["fission_rate_peaking_factor"]),
    "statepoint_sha256":sha256(sp),"settings_sha256":raw["candidates"][0].get("settings_sha256"),
    "mgxs_sha256":raw["candidates"][0].get("mgxs_sha256"),"batches":batches,"inactive":inactive,
    "particles_per_batch":10000,"threads":1,"source_trace_status":trace["status"],"warning_count":0,
    "upstream_commit":study["upstream_commit"]})
  except Exception as e:errors.append(f"{p}: {type(e).__name__}: {e}")
 return rows,errors

def analyze(rows,errors,batches,inactive):
 by={cid:[r for r in rows if r["candidate_id"]==cid] for cid in EXPECTED}
 checks={
  "exactly_60_runs":len(rows)==60,
  "all_six_layouts":{r["candidate_id"] for r in rows}==set(EXPECTED),
  "ten_replicates_per_layout":all(len(v)==10 and {r["seed"] for r in v}==SEEDS for v in by.values()),
  "unique_candidate_seed_pairs":len({(r["candidate_id"],r["seed"]) for r in rows})==len(rows),
  "unique_statepoint_hashes":len({r["statepoint_sha256"] for r in rows})==len(rows),
  "shared_mgxs_hash":len({r["mgxs_sha256"] for r in rows})==1 and bool(rows) and all(r["mgxs_sha256"] for r in rows),
  "pinned_upstream_revision":all(r["upstream_commit"]=="ba41bee54320ada0b4ac39a0dd2ca3c1d090a450" for r in rows),
  "raw_hdf5_and_source_traces":len(rows)==60 and all(r["source_trace_status"]=="DIAGNOSTIC_REVIEW_REQUIRED" for r in rows),
  "zero_mesh_warnings":len(rows)==60 and all(r["warning_count"]==0 for r in rows),
  "common_budget":len({(r["batches"],r["inactive"],r["particles_per_batch"],r["threads"]) for r in rows})==1 and all((r["batches"],r["inactive"],r["particles_per_batch"],r["threads"])==(batches,inactive,10000,1) for r in rows)}
 pairs=[]
 for a,b in (("MMUU","MUMU"),("UMUM","UUMM")):
  la={r["seed"]:r for r in by["c5g7-2x2-"+a]};lb={r["seed"]:r for r in by["c5g7-2x2-"+b]}
  complete=set(la)==SEEDS and set(lb)==SEEDS
  diffs=[(la[s]["keff_mean"]-lb[s]["keff_mean"])*1e5 for s in sorted(SEEDS)] if complete else []
  if complete:
   m=statistics.mean(diffs);sd=statistics.stdev(diffs);half=T90_DF9*sd/math.sqrt(10);lo,hi=m-half,m+half
   equivalent=lo>-MARGIN_PCM and hi<MARGIN_PCM
  else:m=sd=lo=hi=None;equivalent=False
  pairs.append({"pair":f"{a}_minus_{b}","paired_differences_pcm":diffs,"n_pairs":len(diffs),
   "mean_difference_pcm":m,"paired_sd_pcm":sd,"ci90_low_pcm":lo,"ci90_high_pcm":hi,
   "equivalence_margin_pcm":MARGIN_PCM,"tost_equivalent":equivalent})
 layouts=[]
 for cid,sig in EXPECTED.items():
  g=by[cid]
  if not g:continue
  ks=[r["keff_mean"] for r in g];sds=[r["keff_sd"] for r in g];fps=[r["fission_rate_peaking_factor"] for r in g]
  layouts.append({"candidate_id":cid,"layout_signature":sig,"n_runs":len(g),"seeds":sorted(r["seed"] for r in g),
   "mean_keff":statistics.mean(ks),"between_seed_sd_keff":statistics.stdev(ks) if len(g)>1 else None,
   "pooled_within_run_sd_keff":math.sqrt(statistics.mean(v*v for v in sds)),
   "mean_fission_rate_peaking_factor":statistics.mean(fps),
   "between_seed_sd_fission_rate_peaking_factor":statistics.stdev(fps) if len(g)>1 else None,
   "rank_fission_peaking_descriptive_only":None})
 if len(layouts)==6 and all(x["n_runs"]==10 for x in layouts):
  ordered=sorted(layouts,key=lambda x:(x["mean_fission_rate_peaking_factor"],x["layout_signature"]))
  for rank,x in enumerate(ordered,1):x["rank_fission_peaking_descriptive_only"]=rank
 integrity=all(checks.values()) and not errors
 passed=integrity and all(x["tost_equivalent"] for x in pairs)
 status="B3_PASS" if passed else "B3_FAIL_OR_INCONCLUSIVE_SYMMETRY" if integrity else "B3_FAIL_DATA_INTEGRITY_OR_INCOMPLETE"
 return {"schema_version":"1.0","protocol_id":"CBPFR-C5G7-PREREG-B3-2026-10-15","status":status,
  "b3_gate_pass":passed,"run_count":len(rows),"integrity_pass":integrity,"global_checks":checks,"errors":errors,
  "tost_equivalence_tests":pairs,"layout_summaries":layouts,"runs":rows,"equivalence_margin_pcm":MARGIN_PCM,
  "t_critical_df9_90ci":T90_DF9,"official_benchmark_acceptance":False,
  "nonclaims":["TOST failure or inconclusiveness is not evidence of symmetry.",
   "Noncanonical layouts are design variants, not official C5G7 reference cases.",
   "Fission-peaking order is descriptive, not an approved safety or design-optimality claim."]}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--artifacts-root",type=Path,required=True)
 p.add_argument("--expected-batches",type=int,required=True);p.add_argument("--expected-inactive",type=int,required=True)
 p.add_argument("--outdir",type=Path,required=True);a=p.parse_args()
 if a.outdir.exists() and any(a.outdir.iterdir()):p.error("refusing to overwrite non-empty outdir")
 rows,errors=load(a.artifacts_root,a.expected_batches,a.expected_inactive);report=analyze(rows,errors,a.expected_batches,a.expected_inactive)
 a.outdir.mkdir(parents=True,exist_ok=True)
 if rows:
  for name,items in (("b3_run_level_results.csv",rows),("b3_layout_summary.csv",report["layout_summaries"])):
   if items:
    with (a.outdir/name).open("w",newline="",encoding="utf-8") as f:
     w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)
 (a.outdir/"b3_symmetry_summary.json").write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n")
 lines=["# B3 six-layout symmetry and repeatability","","Status: "+report["status"],"Runs: "+str(report["run_count"])+"/60","","| Pair | Mean delta pcm | 90% CI pcm | Margin pcm | Equivalent |","|---|---:|---:|---:|---|"]
 for x in report["tost_equivalence_tests"]:
  ci="NA" if x["ci90_low_pcm"] is None else f"[{x['ci90_low_pcm']:.2f}, {x['ci90_high_pcm']:.2f}]"
  m="NA" if x["mean_difference_pcm"] is None else f"{x['mean_difference_pcm']:.2f}"
  lines.append(f"| {x['pair']} | {m} | {ci} | ±{x['equivalence_margin_pcm']:.1f} | {x['tost_equivalent']} |")
 lines.extend(["","| Integrity check | Pass |","|---|---|"]+[f"| {k} | {v} |" for k,v in report["global_checks"].items()])
 (a.outdir/"b3_report.md").write_text("\n".join(lines)+"\n")
 print(json.dumps({"status":report["status"],"b3_gate_pass":report["b3_gate_pass"],"run_count":report["run_count"],"tost":report["tost_equivalence_tests"]},indent=2))
 return 2 if errors or not report["integrity_pass"] else 0
if __name__=="__main__":raise SystemExit(main())
