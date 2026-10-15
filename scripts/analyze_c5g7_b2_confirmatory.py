#!/usr/bin/env python3
"""Confirmatory B2 analysis of ten new, audited canonical C5G7 UMMU seeds."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,statistics,xml.etree.ElementTree as ET
from pathlib import Path

GROUPS=(1e-5,0.0635,10.0,100.0,1000.0,500000.0,1000000.0,20000000.0)
REFERENCE=1.18655
REFERENCE_SD=0.000095
EXPECTED_SEEDS=tuple(range(8200001,8200011))
K_DRIFT_MAX_PCM=25.0
ENTROPY_DRIFT_MAX=0.01

def hash_file(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for block in iter(lambda:f.read(1048576),b""):h.update(block)
 return h.hexdigest()

def extract(summary_path,batches,inactive):
 rd=summary_path.parent
 study=json.loads(summary_path.read_text())
 if study.get("status")!="all_runs_completed_needs_independent_validation":raise ValueError("study status incomplete")
 if study.get("upstream_commit")!="ba41bee54320ada0b4ac39a0dd2ca3c1d090a450":raise ValueError("unregistered upstream revision")
 settings=study["settings"]
 if (int(settings["batches"]),int(settings["inactive"]),int(settings["particles"]),int(settings["threads"]))!=(batches,inactive,10000,1):raise ValueError("settings differ from the B1-locked profile")
 cases=study.get("cases",[])
 if len(cases)!=1:raise ValueError("expected one canonical case")
 case=cases[0]
 if case.get("candidate_id")!="c5g7-2x2-UMMU" or case.get("status")!="completed":raise ValueError("not a completed canonical UMMU case")
 if case.get("initial_source_profile")!="baseline_all_fuel":raise ValueError("B2 source profile changed")
 seed=int(case["seed"])
 if seed not in EXPECTED_SEEDS:raise ValueError(f"seed {seed} is not in the frozen B2 list")
 cd=rd/case["candidate_id"];physical=case["physical_results"];sp=cd/physical["statepoint"]
 if not sp.is_file() or sp.stat().st_size==0:raise ValueError("statepoint missing")
 raw_path=rd/"analysis/raw_hdf5_audit.json";trace_path=rd/"analysis/source_convergence.json"
 tally_path=rd/"analysis/assembly_fission.json"
 for p in (raw_path,trace_path,rd/"analysis/source_convergence.csv",tally_path):
  if not p.is_file():raise ValueError(f"missing audit output {p}")
 raw=json.loads(raw_path.read_text());trace=json.loads(trace_path.read_text());tally=json.loads(tally_path.read_text())
 if raw.get("status")!="PASS" or raw.get("candidate_count")!=1:raise ValueError("raw HDF5 audit failed")
 if trace.get("status")!="DIAGNOSTIC_REVIEW_REQUIRED" or not trace.get("entropy"):raise ValueError("missing source diagnostics")
 if tally.get("candidate_id")!="c5g7-2x2-UMMU" or tally.get("layout_signature")!="UMMU":raise ValueError("assembly tally mismatch")
 edges=tuple(float(x) for x in physical.get("mgxs_energy_group_boundaries",[]))
 if physical.get("mgxs_group_structure_audit")!="PASS" or edges!=GROUPS:raise ValueError("standard C5G7 group structure failed")
 settings_xml=ET.parse(cd/"model/2d/settings.xml").getroot()
 if int(settings_xml.findtext("seed"))!=seed:raise ValueError("settings seed mismatch")
 if tuple(int(settings_xml.findtext(k)) for k in ("batches","inactive","particles"))!=(batches,inactive,10000):raise ValueError("settings XML profile mismatch")
 log=(cd/"model/2d/openmc.log")
 if not log.is_file():raise ValueError("OpenMC log absent")
 warnings=log.read_text(errors="replace").count("Fission source site(s) outside of entropy box")
 if warnings:raise ValueError(f"entropy mesh warnings={warnings}")
 rawcase=raw["candidates"][0]
 if rawcase.get("statepoint_sha256")!=hash_file(sp):raise ValueError("statepoint hash mismatch")
 return {
  "seed":seed,"batches":batches,"inactive":inactive,"particles":10000,"threads":1,
  "keff_mean":float(physical["keff_mean"]),"keff_std_dev":float(physical["keff_std_dev"]),
  "k_generation_half_delta_pcm":float(trace["k_generation_second_minus_first_half_pcm"]),
  "entropy_quarter_delta":float(trace["entropy"]["last_minus_first_quarter_mean"]),
  "entropy_slope_per_1000":float(trace["entropy"]["ols_slope_per_1000_active_batches"]),
  "statepoint_sha256":hash_file(sp),"settings_sha256":rawcase.get("settings_sha256"),
  "mgxs_sha256":rawcase.get("mgxs_sha256"),"warning_count":warnings,
  "raw_hdf5_audit":raw["status"],"source_trace_status":trace["status"],
  "assembly_fission_peaking_factor":float(tally["fission_rate_peaking_factor"]),
  "upstream_commit":study["upstream_commit"],"openmc_version":physical["openmc_version"],
  "status":"PASS_INTEGRITY"
 }

def analyze(rows,errors,batches,inactive,protocol):
 seeds=[r["seed"] for r in rows];means=[r["keff_mean"] for r in rows];sds=[r["keff_std_dev"] for r in rows]
 hashes=[r["statepoint_sha256"] for r in rows];mgxs={r["mgxs_sha256"] for r in rows}
 complete=len(rows)==10 and set(seeds)==set(EXPECTED_SEEDS) and len(set(seeds))==10
 integrity=(complete and not errors and len(set(hashes))==10 and len(mgxs)==1 and None not in mgxs
   and all(r["raw_hdf5_audit"]=="PASS" and r["warning_count"]==0 and r["source_trace_status"]=="DIAGNOSTIC_REVIEW_REQUIRED" for r in rows)
   and all((r["batches"],r["inactive"],r["particles"],r["threads"])==(batches,inactive,10000,1) for r in rows))
 if len(rows)==10 and all(math.isfinite(v) for v in means+sds) and all(v>0 for v in sds):
  mean_k=statistics.mean(means)
  between=statistics.stdev(means)
  within=math.sqrt(statistics.mean(v*v for v in sds))
  ratio=between/within if within>0 else math.inf
  delta_pcm=(mean_k-REFERENCE)*1e5
  mean_se=between/math.sqrt(10)
  combined_se=math.sqrt(REFERENCE_SD**2+mean_se**2)
  z=(mean_k-REFERENCE)/combined_se if combined_se>0 else math.inf
  drift_pass=all(abs(r["k_generation_half_delta_pcm"])<=K_DRIFT_MAX_PCM and abs(r["entropy_quarter_delta"])<=ENTROPY_DRIFT_MAX for r in rows)
 else:
  mean_k=between=within=ratio=delta_pcm=combined_se=z=None;drift_pass=False
 scalar_pass=(mean_k is not None and abs(delta_pcm)<=100 and abs(z)<=2 and 0.55<=ratio<=1.45)
 passed=integrity and scalar_pass and drift_pass
 if errors or not complete or not integrity:status="B2_FAIL_DATA_INTEGRITY_OR_INCOMPLETE"
 elif not drift_pass:status="B2_FAIL_SOURCE_CONVERGENCE_SCREEN"
 elif not scalar_pass:status="B2_FAIL_NUMERICAL_CONFIRMATION"
 else:status="B2_PASS"
 metrics={"mean_keff":mean_k,"between_seed_sample_sd":between,"pooled_within_run_reported_sd":within,
  "between_to_within_sd_ratio":ratio,"reference_keff":REFERENCE,"reference_standard_uncertainty":REFERENCE_SD,
  "reference_delta_pcm":delta_pcm,"combined_standard_uncertainty_of_difference":combined_se,
  "combined_uncertainty_z":z,"abs_delta_pcm_max":100,"abs_z_max":2,
  "sd_ratio_bounds":[0.55,1.45],"k_generation_half_drift_pcm_max":K_DRIFT_MAX_PCM,
  "entropy_quarter_drift_nat_max":ENTROPY_DRIFT_MAX,"source_trace_screen_pass":drift_pass,
  "scalar_screen_pass":scalar_pass}
 return {"schema_version":"1.0","protocol_id":"CBPFR-C5G7-PREREG-B0-2026-10-15",
  "status":status,"b2_gate_pass":passed,"run_count":len(rows),"expected_seed_set":list(EXPECTED_SEEDS),
  "observed_seeds":sorted(seeds),"expected_settings":{"batches":batches,"inactive":inactive,"particles":10000,"threads":1},
  "integrity_pass":integrity,"integrity_errors":errors,"global_statepoint_hashes_unique":len(set(hashes))==len(hashes),
  "one_common_mgxs_hash":len(mgxs)==1 and None not in mgxs,"metrics":metrics,"runs":rows,
  "nonclaims":["This is numerical verification against the canonical C5G7 reference only.",
  "B2 pass alone is not full benchmark acceptance; B4 pin-power comparison and independent model identity sign-off remain mandatory.",
  "Do not pool B1 pilot seeds or any run with a different entropy mesh or nonstandard group structure."]}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--artifacts-root",type=Path,required=True);p.add_argument("--protocol",type=Path,required=True)
 p.add_argument("--expected-batches",type=int,required=True);p.add_argument("--expected-inactive",type=int,required=True)
 p.add_argument("--outdir",type=Path,required=True);a=p.parse_args()
 if a.outdir.exists() and any(a.outdir.iterdir()):p.error("refusing to overwrite non-empty output directory")
 protocol=json.loads(a.protocol.read_text())
 if protocol.get("protocol_id")!="CBPFR-C5G7-PREREG-B0-2026-10-15":p.error("unexpected B0 protocol")
 rows=[];errors=[]
 for path in sorted(a.artifacts_root.rglob("STUDY_SUMMARY.json")):
  try:rows.append(extract(path,a.expected_batches,a.expected_inactive))
  except Exception as e:errors.append(f"{path}: {type(e).__name__}: {e}")
 report=analyze(rows,errors,a.expected_batches,a.expected_inactive,protocol)
 a.outdir.mkdir(parents=True,exist_ok=True)
 if rows:
  with (a.outdir/"b2_run_level_results.csv").open("w",newline="",encoding="utf-8") as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 (a.outdir/"b2_confirmatory_summary.json").write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n")
 m=report["metrics"]
 lines=["# B2 canonical C5G7 confirmatory screen","","Status: "+report["status"],"Gate pass: "+str(report["b2_gate_pass"]),f"Runs audited: {report['run_count']}/10","","| Metric | Result |","|---|---:|"]
 for k,v in m.items():lines.append(f"| {k} | {v} |")
 lines.extend(["","B2 uses only the ten newly registered seed values. If a gate fails, report the failure and do not start B3. B4 still requires reviewed official pin-power reference data, and a scalar k-effective match is not benchmark acceptance."])
 (a.outdir/"b2_confirmatory_report.md").write_text("\n".join(lines)+"\n")
 print(json.dumps({"status":report["status"],"b2_gate_pass":report["b2_gate_pass"],"run_count":report["run_count"],"metrics":m},indent=2))
 return 2 if errors or not report["integrity_pass"] else 0

if __name__=="__main__":raise SystemExit(main())
