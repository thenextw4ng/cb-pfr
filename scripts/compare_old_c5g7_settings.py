#!/usr/bin/env python3
"""Compare archived Protocol A/B settings.xml while treating inactive count as intentional."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET

SEEDS=(720000,730000,740000)
PROTOCOLS=("a","b")

def sha256(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()

def normalized(path):
 root=ET.parse(path).getroot()
 inactive=root.find("inactive")
 if inactive is not None:inactive.text="__INACTIVE_PROFILE__"
 return ET.canonicalize(ET.tostring(root,encoding="unicode"))

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--root",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();results=[];errors=[]
 for seed in SEEDS:
  pair={}
  for protocol in PROTOCOLS:
   dirname=f"protocol-{protocol}-seed-{seed}"
   candidates=list((a.root/dirname).rglob("settings.xml")) if (a.root/dirname).exists() else []
   if len(candidates)!=1:
    errors.append(f"{dirname}: expected one settings.xml, found {len(candidates)}")
   else:pair[protocol]=candidates[0]
  if set(pair)!={"a","b"}:continue
  sa=normalized(pair["a"]);sb=normalized(pair["b"])
  results.append({"seed":seed,"protocol_a_path":str(pair["a"]),"protocol_b_path":str(pair["b"]),
    "protocol_a_sha256":sha256(pair["a"]),"protocol_b_sha256":sha256(pair["b"]),
    "normalized_xml_identical_except_inactive":sa==sb,
    "protocol_a_inactive":ET.parse(pair["a"]).getroot().findtext("inactive"),
    "protocol_b_inactive":ET.parse(pair["b"]).getroot().findtext("inactive")})
 status="R0D_SETTINGS_MATCH_EXCEPT_INACTIVE" if len(results)==3 and all(x["normalized_xml_identical_except_inactive"] for x in results) else "R0D_SETTINGS_DIFFER_OR_ARTIFACTS_MISSING"
 report={"status":status,"pair_count":len(results),"comparisons":results,"errors":errors,
  "interpretation":"Only the inactive element is normalized. Any other settings.xml difference remains visible as a mismatch and must be reviewed; matching XML does not explain the Protocol B dispersion by itself."}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print(json.dumps(report,indent=2))
if __name__=="__main__":main()
