#!/usr/bin/env python3
"""Equal-evaluation synthetic benchmark: feasible classical random search vs classical QUBO simulated annealing."""
from __future__ import annotations
import argparse,csv,json,math,platform,random,statistics,sys,time
from itertools import combinations
from pathlib import Path
def mean_ci(xs,seed,reps=4000):
    if not xs:return [None,None]
    rng=random.Random(seed);n=len(xs);m=[statistics.fmean(xs[rng.randrange(n)] for _ in range(n)) for _ in range(reps)];m.sort()
    return [m[int(.025*(reps-1))],m[int(.975*(reps-1))]]
class Instance:
    def __init__(self,n,seed):
        rng=random.Random(seed);self.n=n;self.k=n//2;self.h=[rng.uniform(-1,1) for _ in range(n)];self.j=[[0.0]*n for _ in range(n)]
        for i in range(n):
            for q in range(i+1,n):
                x=rng.uniform(-1,1);self.j[i][q]=self.j[q][i]=x
        self.penalty=2*(sum(abs(x) for x in self.h)+sum(abs(self.j[i][q]) for i in range(n) for q in range(i+1,n)))+1
    def obj(self,x):return sum(self.h[i]*x[i] for i in range(self.n))+sum(self.j[i][q]*x[i]*x[q] for i in range(self.n) for q in range(i+1,self.n))
    def energy(self,x):return self.obj(x)+self.penalty*(sum(x)-self.k)**2
    def flip_delta(self,x,i,count):
        d=1-2*x[i];do=d*(self.h[i]+sum(self.j[i][q]*x[q] for q in range(self.n) if q!=i))
        return do+self.penalty*((count+d-self.k)**2-(count-self.k)**2),do,d
def oracle(inst):
    best=math.inf;bestsel=()
    for sel in combinations(range(inst.n),inst.k):
        v=sum(inst.h[i] for i in sel)+sum(inst.j[a][b] for ii,a in enumerate(sel) for b in sel[ii+1:])
        if v<best:best=v;bestsel=sel
    return best,bestsel,math.comb(inst.n,inst.k)
def classical(inst,budget,seed):
    rng=random.Random(seed);best=math.inf;bx=None
    for _ in range(budget):
        sel=rng.sample(range(inst.n),inst.k);x=[int(i in set(sel)) for i in range(inst.n)];v=inst.obj(x)
        if v<best:best=v;bx=x
    return best,bx,1.0
def sa(inst,budget,seed):
    rng=random.Random(seed);x=[rng.randrange(2) for _ in range(inst.n)];count=sum(x);obj=inst.obj(x);e=obj+inst.penalty*(count-inst.k)**2
    best=math.inf;bx=None;feas=0
    if count==inst.k:best=obj;bx=x.copy();feas+=1
    for step in range(1,budget):
        i=rng.randrange(inst.n);de,do,dc=inst.flip_delta(x,i,count);f=step/max(1,budget-1);t0=max(.01,.75*inst.penalty);temp=t0*(.01/t0)**f
        if de<=0 or rng.random()<math.exp(-de/max(temp,1e-12)):x[i]=1-x[i];e+=de;obj+=do;count+=dc
        if count==inst.k:
            feas+=1
            if obj<best:best=obj;bx=x.copy()
    if not math.isclose(e,inst.energy(x),rel_tol=1e-8,abs_tol=1e-8):raise RuntimeError("incremental QUBO energy audit failed")
    return (best,bx,feas/budget) if bx is not None else (None,None,feas/budget)
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--outdir",type=Path,required=True);ap.add_argument("--sizes",type=int,nargs="*",default=[10,14,18])
    ap.add_argument("--instances-per-size",type=int,default=30);ap.add_argument("--budget",type=int,default=5000);ap.add_argument("--seed",type=int,default=20261016);a=ap.parse_args()
    if a.outdir.exists() and any(a.outdir.iterdir()):ap.error("refusing to overwrite non-empty output")
    if any(n not in (10,14,18) for n in a.sizes) or a.instances_per_size<1 or a.budget<10:ap.error("invalid frozen protocol settings")
    rows=[];pairs=[]
    for n in a.sizes:
        for idx in range(a.instances_per_size):
            seed=a.seed+n*100000+idx;ins=Instance(n,seed);best,_,space=oracle(ins)
            t=time.perf_counter();c,cv,cf=classical(ins,a.budget,seed+1);ct=time.perf_counter()-t
            t=time.perf_counter();q,qv,qf=sa(ins,a.budget,seed+2);qt=time.perf_counter()-t
            for alg,v,x,frac,elapsed in (("classical_direct_feasible_random_search",c,cv,cf,ct),("qubo_classical_simulated_annealing",q,qv,qf,qt)):
                rows.append({"study_id":"CBPFR-classical-vs-QUBO-SA-equal-energy-eval-2026-10-16","n_variables":n,"instance_index":idx+1,"instance_seed":seed,
                  "algorithm":alg,"evaluation_count":a.budget,"budget":a.budget,"objective_value":v,"oracle_objective":best,
                  "absolute_objective_gap":v-best if v is not None else None,"best_found_feasible":v is not None,
                  "fraction_evaluations_feasible":frac,"wallclock_seconds":elapsed,"solution_vector":"".join(map(str,x)) if x else "",
                  "oracle_feasible_state_count":space,"quantum_hardware_used":False})
            pairs.append({"n_variables":n,"instance_index":idx+1,"instance_seed":seed,"classical_gap":c-best,"qubo_sa_gap":q-best if q is not None else None,
              "qubo_sa_feasible_found":q is not None,"qubo_sa_better_than_classical":q is not None and q<c,"equal_budget":True})
    summary=[]
    for n in a.sizes:
        for alg in ("classical_direct_feasible_random_search","qubo_classical_simulated_annealing"):
            sub=[r for r in rows if r["n_variables"]==n and r["algorithm"]==alg];g=[r["absolute_objective_gap"] for r in sub if r["absolute_objective_gap"] is not None]
            summary.append({"n_variables":n,"algorithm":alg,"instances":len(sub),"budget_per_instance":a.budget,
              "mean_absolute_gap":statistics.fmean(g) if g else None,"mean_gap_bootstrap_95pct_ci":mean_ci(g,a.seed+n+len(alg)),
              "median_absolute_gap":statistics.median(g) if g else None,"exact_oracle_match_rate":statistics.fmean(int(abs(x)<1e-9) for x in g) if g else 0,
              "feasible_solution_found_rate":statistics.fmean(int(r["best_found_feasible"]) for r in sub),
              "mean_wallclock_seconds":statistics.fmean(r["wallclock_seconds"] for r in sub),"quantum_hardware_used":False})
    paired=[]
    for n in a.sizes:
        sub=[r for r in pairs if r["n_variables"]==n and r["qubo_sa_gap"] is not None];d=[r["qubo_sa_gap"]-r["classical_gap"] for r in sub]
        paired.append({"n_variables":n,"instances":len(sub),"mean_gap_difference_qubo_minus_classical":statistics.fmean(d),
            "paired_bootstrap_95pct_ci":mean_ci(d,a.seed+n+9000),"fraction_qubo_sa_better":statistics.fmean(int(r["qubo_sa_better_than_classical"]) for r in sub),
            "fraction_qubo_sa_exact":statistics.fmean(int(abs(r["qubo_sa_gap"])<1e-9) for r in sub)})
    a.outdir.mkdir(parents=True,exist_ok=True)
    def save(name,data):
        with (a.outdir/name).open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    save("solver_run_level.csv",rows);save("solver_instance_comparison.csv",pairs);save("solver_summary.csv",summary)
    report={"schema_version":"1.0","study_id":"CBPFR-classical-vs-QUBO-SA-equal-energy-eval-2026-10-16","status":"COMPLETED",
      "environment":{"python_version":sys.version.split()[0],"platform":platform.platform(),"processor":platform.processor() or "not reported"},
      "instances_total":len(pairs),"sizes":a.sizes,"instances_per_size":a.instances_per_size,"evaluation_budget_each_method_each_instance":a.budget,
      "constraint":"sum(x)=n/2","qubo_penalty":"A=2*(sum absolute linear coefficients + sum absolute pair coefficients)+1",
      "methods":["direct random search over feasible states","QUBO with classical simulated annealing"],
      "oracle":"exact feasible-state enumeration; used for gap measurement only, not counted against either heuristic",
      "fairness_boundary":"equal objective/energy evaluation count, not equal wallclock time or cost per evaluation",
      "paired_comparison_by_size":paired,"summary":summary,
      "nonclaims":["simulated annealing is classical, not quantum annealing","no quantum hardware or quantum advantage tested",
       "synthetic QUBO instances are not OpenMC physics","C5G7 two-MOX penalty alone gives all six feasible states equal energy and cannot rank them"]}
    (a.outdir/"solver_comparison_report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":report["status"],"total_instances":len(pairs),"budget":a.budget,"summary":summary,"paired":paired},indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
