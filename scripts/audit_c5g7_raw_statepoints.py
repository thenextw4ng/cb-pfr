#!/usr/bin/env python3
"""Audit raw C5G7 OpenMC statepoints; reconstruct fission proxy and summarize entropy.
Requires h5py/numpy. Does not launch OpenMC and cannot certify physical validity.
"""
import argparse,csv,hashlib,json,re,statistics
from pathlib import Path
import h5py,numpy as np
PAT=re.compile(r"c5g7-study-(\d+)/c5g7-2x2-([A-Z]+)/model/2d/statepoint\.7000\.h5$")
WINS=[(500,1499),(2500,3499),(6000,6999)]
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""): h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--artifact-root",type=Path,required=True)
 p.add_argument("--run-level-csv",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 rows=list(csv.DictReader(a.run_level_csv.open(encoding="utf-8-sig",newline="")))
 byseed={int(r["seed"]):r for r in rows}; runs=[]; errors=[]
 for f in sorted(a.artifact_root.glob("c5g7-study-*/c5g7-2x2-*/model/2d/statepoint.7000.h5")):
  m=PAT.search(f.as_posix())
  if not m: continue
  rnd,layout=int(m.group(1)),m.group(2)
  case=json.loads((f.parents[2]/"CASE_RESULT.json").read_text()); seed=int(case["seed"])
  with h5py.File(f,"r") as h:
   dims=h["tallies/meshes/mesh 1/dimension"][:].astype(int).tolist()
   entropy=h["entropy"][:]; kgen=h["k_generation"][:]
   vals=h["tallies/tally 1/results"][:]
   scores=[x.decode() for x in h["tallies/tally 1/score_bins"][:]]
   field=vals[:,scores.index("fission"),0].reshape((dims[0],dims[1]),order="F")
   # Four fuel blocks beside the symmetry corner; five reflector blocks excluded.
   blocks=[float(field[i*17:(i+1)*17,j*17:(j+1)*17].sum()) for i,j in [(0,1),(0,2),(1,1),(1,2)]]
   proxy=max(blocks)/(sum(blocks)/4)
   ew=[]
   for lo,hi in WINS:
    x=entropy[lo:hi+1]; ew.append({"batch_start":lo+1,"batch_end":hi+1,"mean":float(x.mean()),"sd":float(x.std(ddof=1))})
   kw=[]
   for lo,hi in WINS:
    x=kgen[lo:hi+1]; kw.append({"batch_start":lo+1,"batch_end":hi+1,"mean":float(x.mean()),"sd":float(x.std(ddof=1))})
   rec={"round":rnd,"layout":layout,"seed":seed,"statepoint_sha256":sha(f),
        "batches":int(h["n_batches"][()]),"inactive":int(h["n_inactive"][()]),"mesh_dimension":dims,
        "k_combined":float(h["k_combined"][0]),"k_combined_sd":float(h["k_combined"][1]),
        "fuel_block_fission_sums":blocks,"reconstructed_proxy":proxy,"entropy_windows":ew,"k_generation_windows":kw,
        "entropy_first_last_window_delta":ew[-1]["mean"]-ew[0]["mean"]}
  row=byseed.get(seed)
  if row is None: errors.append(f"missing CSV row for seed {seed}"); continue
  rec["csv_proxy"]=float(row["fission_rate_peaking_factor"])
  rec["proxy_abs_difference"]=abs(proxy-rec["csv_proxy"])
  runs.append(rec)
 expected={(int(r["round"]),r["layout_signature"]) for r in rows}
 observed={(r["round"],r["layout"]) for r in runs}
 maxdiff=max((r["proxy_abs_difference"] for r in runs),default=float("inf"))
 shifts=[abs(r["entropy_first_last_window_delta"]) for r in runs]
 report={"schema_version":"cbpfr.raw-statepoint-audit.v1","csv_sha256":sha(a.run_level_csv),
  "run_count_statepoints":len(runs),"run_count_csv":len(rows),"statepoint_pairs_match_csv":observed==expected,
  "all_meshes_51x51x1":all(r["mesh_dimension"]==[51,51,1] for r in runs),
  "all_batches_7000":all(r["batches"]==7000 for r in runs),"all_inactive_500":all(r["inactive"]==500 for r in runs),
  "proxy_reconstruction_max_abs_difference":maxdiff,"proxy_reconstruction_matches_to_1e-12":maxdiff<1e-12,
  "entropy_diagnostic":{"windows":"501-1500, 2501-3500, 6001-7000","mean_absolute_first_last_window_shift":statistics.mean(shifts) if shifts else None,
   "maximum_absolute_first_last_window_shift":max(shifts) if shifts else None,"threshold_predeclared":False,
   "interpretation":"Descriptive diagnostic only; not a convergence certificate."},
  "physical_validation_certified":False,"cbpfr_superiority_established":False,"winner_selected":False,
  "errors":errors,"runs":sorted(runs,key=lambda r:(r["round"],r["layout"]))}
 a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
 print(json.dumps({k:report[k] for k in ["run_count_statepoints","run_count_csv","statepoint_pairs_match_csv","all_meshes_51x51x1","proxy_reconstruction_max_abs_difference","proxy_reconstruction_matches_to_1e-12","physical_validation_certified","cbpfr_superiority_established","winner_selected","errors"]},indent=2))
 return 0 if len(runs)==18 and observed==expected and maxdiff<1e-12 and not errors else 2
if __name__=="__main__": raise SystemExit(main())
