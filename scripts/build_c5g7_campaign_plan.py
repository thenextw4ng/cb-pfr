#!/usr/bin/env python3
"""Reproducibly generate the preregistered R0 + 1,275-run OpenMC campaign."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np

ROOT_ENTROPY = 20261015
LAYOUTS = {
    "MMUU": "c5g7-2x2-MMUU",
    "MUMU": "c5g7-2x2-MUMU",
    "MUUM": "c5g7-2x2-MUUM",
    "UMMU": "c5g7-2x2-UMMU",
    "UMUM": "c5g7-2x2-UMUM",
    "UUMM": "c5g7-2x2-UUMM",
}
EXCLUDED = {
    *range(820000, 840001),
    620000, 810001,810002,810003,820001,820002,820003,
    *range(8200001,8200011),
    1720000,2720000,3720000,4720000,5720000,6720000,7720000,
    20261015,20262015,20263015,
}
USED = set(EXCLUDED)

def seeds(stage: int, count: int) -> list[int]:
    out = []
    root = np.random.SeedSequence([ROOT_ENTROPY, stage])
    children = root.spawn(count * 4 + 32)
    for child in children:
        seed = int(child.generate_state(1, dtype=np.uint32)[0])
        if seed < 1_000_000 or seed in USED:
            continue
        USED.add(seed)
        out.append(seed)
        if len(out) == count:
            break
    if len(out) != count:
        raise RuntimeError(f"SeedSequence failed to produce {count} unique seeds for stage {stage}")
    return out

def entry(stage, candidate_id, sig, seed, batches, inactive, particles, threads=1, source="good", rep=1):
    return {
        "stage":stage, "candidate_id":candidate_id, "signature":sig, "seed":int(seed),
        "batches":int(batches), "inactive":int(inactive), "particles":int(particles),
        "threads":int(threads), "source":source, "replicate":int(rep),
        "run_id":f"{stage}-{sig}-s{seed}-b{batches}-i{inactive}-p{particles}-t{threads}-{source}",
    }

def make_plan():
    # Pairing is explicit: same SeedSequence-generated seed within comparisons only.
    r0a_seed = seeds(1,1)[0]
    r0b_seed = seeds(2,1)[0]
    r0c_seed = seeds(3,1)[0]
    r0 = [
        entry("R0a_i50",LAYOUTS["UMMU"],"UMMU",r0a_seed,300,50,10000,1),
        entry("R0a_i150",LAYOUTS["UMMU"],"UMMU",r0a_seed,300,150,10000,1),
        entry("R0b_t1",LAYOUTS["UMMU"],"UMMU",r0b_seed,300,50,10000,1),
        entry("R0b_t2",LAYOUTS["UMMU"],"UMMU",r0b_seed,300,50,10000,2),
        entry("R0c",LAYOUTS["UMMU"],"UMMU",r0c_seed,500,50,10000,1),
    ]
    p1s = seeds(10,10)
    p1=[entry("P1",LAYOUTS["UMMU"],"UMMU",s,10000,1000,10000,rep=i+1) for i,s in enumerate(p1s)]
    v1s=seeds(11,5)
    v1a=[entry("V1a",LAYOUTS["UMMU"],"UMMU",s,6000,1000,50000,rep=i+1) for i,s in enumerate(v1s)]
    p2s=seeds(12,10)
    p2=[entry("P2",LAYOUTS["MUUM"],"MUUM",s,10000,1000,10000,rep=i+1) for i,s in enumerate(p2s)]
    p3s=seeds(13,10)
    p3=[entry("P3",LAYOUTS[sig],sig,seed,10000,1000,10000,rep=i+1)
        for sig in ("MMUU","UMUM") for i,seed in enumerate(p3s)]
    p4s=seeds(14,10)
    p4=[entry("P4",LAYOUTS[sig],sig,seed,10000,1000,10000,rep=i+1)
        for sig in ("MUMU","UUMM") for i,seed in enumerate(p4s)]
    v2s=seeds(20,200)
    v2=[]
    for i,seed in enumerate(v2s):
        for sig in ("MMUU","MUMU","MUUM","UMMU","UMUM","UUMM"):
            v2.append(entry("V2a",LAYOUTS[sig],sig,seed,800,500,2000,rep=i+1))
    # Contiguous replicate blocks keep all six labels of each replicate within the same shard.
    v2_shards=[v2[i*240:(i+1)*240] for i in range(5)]
    p5s=seeds(15,5)
    p5=[entry("P5",LAYOUTS["UMMU"],"UMMU",s,4000,1000,40000,rep=i+1) for i,s in enumerate(p5s)]
    p6s=seeds(16,5)
    p6=[entry("P6",LAYOUTS["UMMU"],"UMMU",s,10000,1000,10000,source="bad",rep=i+1) for i,s in enumerate(p6s)]
    # Conditional replay only if R0a reports different raw generation traces.
    replay_seeds=seeds(17,3)
    protocol_replay=[
        entry("AB_replay_A",LAYOUTS["UMMU"],"UMMU",s,7000,500,10000,rep=i+1)
        for i,s in enumerate(replay_seeds)
    ] + [
        entry("AB_replay_B",LAYOUTS["UMMU"],"UMMU",s,7000,100,10000,rep=i+1)
        for i,s in enumerate(replay_seeds)
    ]
    production=p1+v1a+p2+p3+p4+p5+p6
    plan={
        "schema_version":"1.0", "protocol_id":"CBPFR-C5G7-NIGHT-CAMPAIGN-2026-10-15",
        "root_seed_sequence_entropy":ROOT_ENTROPY,
        "seed_policy":"NumPy SeedSequence-derived 32-bit OpenMC seeds; no seed lies in the old 820000-840000 seed interval; seeds are non-sequential and unique across independent groups, with deliberate matched-seed reuse only inside explicitly paired comparisons and the six-label V2a replicate.",
        "run_count_main":sum(len(v) for v in (p1,v1a,p2,p3,p4,v2,p5,p6)),
        "run_count_by_stage":{"R0a":2,"R0b":2,"R0c":1,"R0d":0,"P1":len(p1),"V1a":len(v1a),"P2":len(p2),"P3":len(p3),"P4":len(p4),"V2a":len(v2),"P5":len(p5),"P6":len(p6)},
        "layout_mapping":LAYOUTS,
        "stages":{"R0":r0,"P1":p1,"V1a":v1a,"P2":p2,"P3":p3,"P4":p4,"P5":p5,"P6":p6,
                  "AB_replay_conditional":protocol_replay},
        "production_matrix":production,
        "V2a_shards":v2_shards,
        "important":{"P3_seed_pairing":"MMUU and UMUM share the ten seed values for paired symmetry analysis.",
                     "P4_seed_pairing":"MUMU and UUMM share the ten seed values for paired mirror analysis.",
                     "V2a_seed_pairing":"All six layouts share each replicate seed to enable paired selection analysis.",
                     "P6_source":"Initial fission source restricted to one fuel assembly; transport is otherwise unconstrained.",
                     "official_benchmark_acceptance":False}
    }
    assert plan["run_count_main"]==1275,plan["run_count_by_stage"]
    assert len(set(r["seed"] for k in ("P1","V1a","P2","P3","P4","P5","P6") for r in plan["stages"][k])) == 55
    return plan

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path)
    p.add_argument("--github-output",type=Path)
    p.add_argument("--print-json",action="store_true")
    a=p.parse_args()
    plan=make_plan()
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(plan,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    if a.github_output:
        pairs={
            "r0_matrix":plan["stages"]["R0"],
            "production_matrix":plan["production_matrix"],
            "protocol_replay_matrix":plan["stages"]["AB_replay_conditional"],
            "p1_matrix":plan["stages"]["P1"],
            "v1a_matrix":plan["stages"]["V1a"],
            "p2_matrix":plan["stages"]["P2"],
            "p3_matrix":plan["stages"]["P3"],
            "p4_matrix":plan["stages"]["P4"],
            "p5_matrix":plan["stages"]["P5"],
            "p6_matrix":plan["stages"]["P6"],
        }
        pairs.update({f"v2a_{i}_matrix":m for i,m in enumerate(plan["V2a_shards"])})
        with a.github_output.open("a",encoding="utf-8") as f:
            for key,value in pairs.items(): f.write(f"{key}={json.dumps(value,separators=(',',':'))}\n")
    print(json.dumps({"protocol_id":plan["protocol_id"],"run_count_main":plan["run_count_main"],"run_count_by_stage":plan["run_count_by_stage"],
        "v2a_shard_sizes":[len(x) for x in plan["V2a_shards"]],"unique_seed_count":len({r["seed"] for stage in plan["stages"].values() for r in stage}),"output":str(a.out) if a.out else None},indent=2))
    if a.print_json: print(json.dumps(plan,separators=(",",":")))
if __name__=="__main__": main()
