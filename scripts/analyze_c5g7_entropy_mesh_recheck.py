#!/usr/bin/env python3
"""Reproduce the corrected C5G7 entropy-mesh audit from extracted Actions artifacts."""
import argparse,csv,hashlib,json,math,re,statistics
from pathlib import Path
import xml.etree.ElementTree as ET
import h5py
import numpy as np
WARNING="Fission source site(s) outside of entropy box"
REF=1.18655

def sha(path):
 h=hashlib.sha256()
 with open(path,"rb") as f:
  for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
 return h.hexdigest()

def acf(x,maxlag=50):
 x=np.asarray(x,dtype=float); x=x-x.mean(); den=float(np.dot(x,x))
 return [] if not den else [float(np.dot(x[:-i],x[i:])/den) for i in range(1,min(maxlag,len(x)-1)+1)]

def iat(rhos):
 total=0.0
 for r in rhos:
  if r<=0: break
  total+=r
 return 1+2*total

def row(case):
 seeddir=case.parent; protocol=seeddir.parent.name; seed=int(seeddir.name.split("_")[-1])
 result=json.loads((case/"CASE_RESULT.json").read_text())
 summary=json.loads((seeddir/"STUDY_SUMMARY.json").read_text())
 audit=json.loads((case/"entropy_mesh_audit.json").read_text())
 settings=ET.parse(case/"model/2d/settings.xml").getroot()
 mesh=settings.find("mesh")
 dim=[int(v) for v in mesh.findtext("dimension").split()]
 lower=[float(v) for v in mesh.findtext("lower_left").split()]
 upper=[float(v) for v in mesh.findtext("upper_right").split()]
 seed_xml=int(settings.findtext("seed")); batches=int(settings.findtext("batches"))
 inactive=int(settings.findtext("inactive")); particles=int(settings.findtext("particles"))
 log=(case/"openmc.log").read_text(errors="replace"); warnings=log.count(WARNING)
 sp=case/"model/2d/statepoint.7000.h5"
 with h5py.File(sp,"r") as f:
  n=int(f["n_batches"][()]); ni=int(f["n_inactive"][()]); ss=int(f["seed"][()])
  stride=int(f["stride"][()]); keff,sd=[float(x) for x in f["k_combined"][:]]
  kg=np.asarray(f["k_generation"][:],dtype=float); ent=np.asarray(f["entropy"][:],dtype=float)
  bank=hashlib.sha256(f["source_bank"][:].tobytes()).hexdigest()
 if not (batches==n==len(kg)==len(ent) and inactive==ni and seed==seed_xml==ss): raise ValueError(f"settings/statepoint mismatch: {case}")
 ak=kg[inactive:]; ae=ent[inactive:]; q=len(ak)//4
 rk=acf(ak); re_=acf(ae)
 return {"protocol":protocol,"seed":seed,"status":result["status"],"study_status":summary["status"],"batches":batches,"inactive_batches":inactive,"particles_per_batch":particles,"seed_in_settings":seed_xml,"rng_stride":stride,"mesh_dimension":"x".join(map(str,dim)),"mesh_lower_left":";".join(map(str,lower)),"mesh_upper_right":";".join(map(str,upper)),"entropy_mesh_warning_count":warnings,"warning_free":warnings==0,"keff_mean":keff,"keff_std_dev":sd,"delta_reference_pcm":(keff-REF)*1e5,"within_run_sd_pcm":sd*1e5,"active_batches":len(ak),"quartile_batches":q,"k_generation_q4_minus_q1_pcm":(ak[-q:].mean()-ak[:q].mean())*1e5,"entropy_q4_minus_q1":ae[-q:].mean()-ae[:q].mean(),"k_generation_lag1_acf":rk[0] if rk else None,"entropy_lag1_acf":re_[0] if re_ else None,"k_generation_iat_positive_sequence_exploratory":iat(rk),"entropy_iat_positive_sequence_exploratory":iat(re_),"statepoint_sha256":sha(sp),"source_bank_sha256":bank,"geometry_sha256":sha(case/"model/2d/geometry.xml"),"mgxs_sha256":sha(case/"model/2d/mgxs.h5"),"materials_xml_sha256_path_sensitive":sha(case/"model/2d/materials.xml"),"statepoint_bytes":sp.stat().st_size,"convergence_certified":False}

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True,type=Path); p.add_argument("--out-csv",required=True,type=Path)
 a=p.parse_args(); cases=sorted(a.root.glob("*/seed_*/c5g7-2x2-UMMU"))
 if not cases: raise SystemExit(f"No cases found under {a.root}")
 rows=[row(c) for c in cases]; a.out_csv.parent.mkdir(parents=True,exist_ok=True)
 with a.out_csv.open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
 print(json.dumps({"n_runs":len(rows),"warnings":sum(r["entropy_mesh_warning_count"] for r in rows),"all_completed":all(r["status"]=="completed" for r in rows),"convergence_certified":False},indent=2))
if __name__=="__main__": main()
