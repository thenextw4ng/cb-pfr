#!/usr/bin/env python3
"""Audit recorded CB-PFR trial-level results without rerunning the experiment."""
from __future__ import annotations
import csv,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/"results"/"per_seed_results.csv"
OUTPUT=ROOT/"results"/"recorded_results_audit.json"
def exact_sign_test(k:int,n:int)->float:
    if k==0 or k==n:return 2.0*(0.5**n)
    tail=sum(math.comb(n,i) for i in range(k,n+1))/(2.0**n)
    return min(1.0,2.0*tail)
def main()->None:
    with INPUT.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    methods=["qubo_only","point_estimate","cb_pfr","uniform_margin"]
    outcomes={}; rates={}
    for method in methods:
        selected=[r for r in rows if r["method"]==method]
        truth=[r["selected_true_feasible"].lower()=="true" for r in selected]
        outcomes[method]=truth; rates[method]=sum(truth)/len(truth)
    comparisons={}
    for baseline in [m for m in methods if m!="cb_pfr"]:
        cb,base=outcomes["cb_pfr"],outcomes[baseline]
        cb_only=sum(a and not b for a,b in zip(cb,base))
        base_only=sum((not a) and b for a,b in zip(cb,base))
        discordant=cb_only+base_only
        comparisons[baseline]={"cb_only":cb_only,"baseline_only":base_only,"ties":len(cb)-discordant,"discordant":discordant,"exact_two_sided_sign_test_p":exact_sign_test(min(cb_only,base_only),discordant) if discordant else 1.0}
    audit={"status":"VERIFIED FROM AVAILABLE ARTIFACTS","independent_full_rerun":False,"physical_validation":False,"rows":len(rows),"trials":len(outcomes["cb_pfr"]),"rates":rates,"paired_comparisons":comparisons,"interpretation":"This audits recorded trial-level outputs; it does not establish physical effectiveness or independent end-to-end reproduction."}
    OUTPUT.write_text(json.dumps(audit,indent=2,sort_keys=True)+"\\n",encoding="utf-8")
    print(json.dumps(audit,indent=2,sort_keys=True))
if __name__=="__main__": main()
