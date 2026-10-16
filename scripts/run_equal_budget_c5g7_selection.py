#!/usr/bin/env python3
"""Offline replay of equal-budget candidate-selection policies; requires complete C5G7 campaign CSVs."""
from __future__ import annotations
import argparse,csv,json,math,random,statistics
from pathlib import Path
SIGS=("MMUU","MUMU","MUUM","UMMU","UMUM","UUMM");BUDGET=18;EQUAL_PER=3;Z=1.96;T95_DF4=2.132
def read_csv(p):
    with p.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def val(r,k):
    x=float(r[k])
    if not math.isfinite(x):raise ValueError("non-finite "+k)
    return x
def sd(xs):return statistics.stdev(xs) if len(xs)>1 else math.nan
def bootstrap_ci(xs,seed=20261016,nboot=4000):
    if not xs:return [None,None]
    rng=random.Random(seed);n=len(xs);means=[statistics.fmean(xs[rng.randrange(n)] for _ in range(n)) for _ in range(nboot)]
    means.sort();return [means[int(.025*(nboot-1))],means[int(.975*(nboot-1))]]
def choose(est,sigma,threshold,rule):
    common=statistics.median(list(sigma.values()));info={}
    for s,(mu,n) in est.items():
        width=0 if rule=="point" else Z*(common if rule=="uniform" else sigma[s])/math.sqrt(n)
        info[s]={"mean":mu,"n":n,"lower":mu-width,"upper":mu+width}
    passed=[s for s in SIGS if info[s]["upper"]<=threshold]
    if passed:w=min(passed,key=lambda s:(info[s]["upper"],info[s]["mean"],SIGS.index(s)))
    else:w=min(SIGS,key=lambda s:(max(0,info[s]["upper"]-threshold),info[s]["upper"],info[s]["mean"],SIGS.index(s)))
    return w,info,bool(passed)
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--v2a-csv",type=Path,required=True)
    ap.add_argument("--high-budget-csv",type=Path,required=True);ap.add_argument("--outdir",type=Path,required=True)
    ap.add_argument("--calibration-pools",type=int,default=60);a=ap.parse_args()
    if a.outdir.exists() and any(a.outdir.iterdir()):ap.error("refusing to overwrite non-empty output directory")
    low,high=read_csv(a.v2a_csv),read_csv(a.high_budget_csv)
    if len(low)!=1200 or len(high)!=60:raise SystemExit(f"requires exactly 1200 V2a and 60 high-budget rows; got {len(low)} and {len(high)}")
    byrep={}
    for r in low:
        rep,s=int(r["replicate"]),r["signature"]
        if s not in SIGS or (int(r["batches"]),int(r["inactive"]),int(r["particles"]))!=(800,500,2000):raise SystemExit("unexpected V2a signature/settings")
        byrep.setdefault(rep,{})
        if s in byrep[rep]:raise SystemExit(f"duplicate V2a layout in pool {rep}")
        byrep[rep][s]=val(r,"F_fission")
    if len(byrep)!=200 or any(set(x)!=set(SIGS) for x in byrep.values()):raise SystemExit("need 200 complete seed pools for all six layouts")
    hby={s:[] for s in SIGS}
    for r in high:
        s,rep=r["signature"],int(r["replicate"])
        if s not in SIGS or r["stage"] not in ("P1","P2","P3","P4") or (int(r["batches"]),int(r["inactive"]),int(r["particles"]))!=(10000,1000,10000):
            raise SystemExit("unexpected high-budget reference row")
        hby[s].append((rep,val(r,"F_fission")))
    if any(len(v)!=10 or {r for r,_ in v}!=set(range(1,11)) for v in hby.values()):raise SystemExit("need ten unique high-budget replicates per layout")
    if not 30<=a.calibration_pools<=100 or a.calibration_pools%5:raise SystemExit("calibration-pools must be multiple of 5 between 30 and 100")
    cal=set(range(1,a.calibration_pools+1));held=sorted(set(byrep)-cal)
    if len(held)%5:raise SystemExit("held-out pools must split into blocks of five")
    sigma={s:sd([byrep[i][s] for i in sorted(cal)]) for s in SIGS}
    if any(not math.isfinite(v) or v<=0 for v in sigma.values()):raise SystemExit("cannot calibrate positive per-layout variability")
    btrain=sorted(v for rep,v in hby["UMMU"] if rep<=5)
    threshold=statistics.fmean(btrain)+T95_DF4*sd(btrain)/math.sqrt(5)
    refs={s:statistics.fmean(v for rep,v in hby[s] if rep>=6) for s in SIGS}
    refbest=min(SIGS,key=lambda s:(refs[s],SIGS.index(s)));blocks=[held[i:i+5] for i in range(0,len(held),5)];decisions=[]
    for bi,block in enumerate(blocks):
        order=list(block);random.Random(20261016+bi).shuffle(order);reservoir={s:[byrep[i][s] for i in order] for s in SIGS}
        equal={s:(statistics.fmean(reservoir[s][:3]),3) for s in SIGS}
        for policy,rule in (("equal_allocation_point_estimate","point"),("equal_allocation_uniform_margin","uniform"),("equal_allocation_cbpfr_relative_screen","candidate")):
            winner,info,passed=choose(equal,sigma,threshold,rule)
            decisions.append({"block":bi+1,"policy":policy,"selected":winner,"evaluations":18,
              "passing_candidates":sum(x["upper"]<=threshold for x in info.values()),"baseline_screen_pass":passed,
              "match_empirical_best":winner==refbest,"empirical_regret_F":refs[winner]-refs[refbest],"selected_reference_F":refs[winner],
              "reference_best_layout":refbest,"allocations":{s:3 for s in SIGS}})
        observed={s:[reservoir[s][0]] for s in SIGS};used={s:1 for s in SIGS}
        for _ in range(BUDGET-len(SIGS)):
            avail=[s for s in SIGS if used[s]<len(reservoir[s])]
            lcb={s:statistics.fmean(observed[s])-Z*sigma[s]/math.sqrt(len(observed[s])) for s in avail}
            who=min(avail,key=lambda s:(lcb[s],SIGS.index(s)));observed[who].append(reservoir[who][used[who]]);used[who]+=1
        est={s:(statistics.fmean(observed[s]),len(observed[s])) for s in SIGS};winner,info,passed=choose(est,sigma,threshold,"candidate")
        decisions.append({"block":bi+1,"policy":"adaptive_RandS_equal_budget","selected":winner,"evaluations":sum(used.values()),
          "passing_candidates":sum(x["upper"]<=threshold for x in info.values()),"baseline_screen_pass":passed,
          "match_empirical_best":winner==refbest,"empirical_regret_F":refs[winner]-refs[refbest],"selected_reference_F":refs[winner],
          "reference_best_layout":refbest,"allocations":used})
    lookup={(r["block"],r["policy"]):r for r in decisions};policies=sorted({r["policy"] for r in decisions});summaries=[]
    for p in policies:
        rows=[r for r in decisions if r["policy"]==p]
        diffs=[r["empirical_regret_F"]-lookup[(r["block"],"equal_allocation_point_estimate")]["empirical_regret_F"] for r in rows]
        summaries.append({"policy":p,"blocks":len(rows),"evaluations_per_decision":sorted({r["evaluations"] for r in rows}),
          "empirical_best_match_rate":statistics.fmean(int(r["match_empirical_best"]) for r in rows),
          "mean_empirical_regret_F":statistics.fmean(r["empirical_regret_F"] for r in rows),
          "median_empirical_regret_F":statistics.median(r["empirical_regret_F"] for r in rows),
          "paired_bootstrap_95pct_ci_regret_difference_vs_point":bootstrap_ci(diffs,seed=20261016+len(p)),
          "baseline_screen_pass_rate":statistics.fmean(int(r["baseline_screen_pass"]) for r in rows),
          "mean_evaluations":statistics.fmean(r["evaluations"] for r in rows)})
    a.outdir.mkdir(parents=True,exist_ok=True)
    for name,data in (("equal_budget_policy_decisions.csv",decisions),("equal_budget_policy_summary.csv",summaries)):
        with (a.outdir/name).open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader()
            for r in data:w.writerow({k:json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in r.items()})
    report={"schema_version":"1.0","study_id":"CBPFR-C5G7-equal-budget-policy-replay-2026-10-16","status":"COMPLETED_OFFLINE_REPLAY",
      "new_openmc_runs":0,"v2a_rows":len(low),"high_budget_rows":len(high),"calibration_pools":len(cal),"held_out_pools":len(held),
      "decision_blocks":len(blocks),"budget_run_equivalents":18,"objective":"minimize F_fission=max assembly-integrated fission rate / mean assembly-integrated fission rate",
      "baseline_screen":{"reference":"UMMU","threshold":"mean high-budget replicates 1-5 + 2.132*SD/sqrt(5)","interpretation":"operational relative screen; not safety or benchmark acceptance"},
      "empirical_reference":"mean of high-budget replicates 6-10 per layout; noisy, not exact physical truth",
      "metrics":["empirical-best match rate","mean/median regret F","paired bootstrap 95% CI vs point policy","screen pass rate","evaluation count and allocation"],
      "limitations":["offline replay; no new transport","within-statepoint tally uncertainty not propagated","run-to-run SD calibrated on disjoint low-budget pools","does not prove universal physical superiority"],"summary":summaries}
    (a.outdir/"equal_budget_policy_report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
