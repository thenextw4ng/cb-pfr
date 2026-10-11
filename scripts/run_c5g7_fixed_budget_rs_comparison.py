#!/usr/bin/env python3
"""Compare CB-PFR with a fixed-budget equal-allocation R&S baseline on archived C5G7 runs.

This is a retrospective analysis of the existing 18-run smoke dataset. It does not
rerun OpenMC, certify C5G7 physics, or establish quantum-hardware execution.
"""
from __future__ import annotations
import argparse, csv, json, math, statistics
from collections import defaultdict
from pathlib import Path

EXPECTED = {"MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM"}

def load_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {"round", "candidate_id", "layout_signature", "seed", "keff_mean",
                    "keff_std_dev", "fission_rate_peaking_factor", "statepoint_sha256",
                    "mgxs_sha256", "group_structure_audit"}
        missing = required - set(reader.fieldnames or ())
        if missing: raise ValueError(f"Missing columns: {sorted(missing)}")
        rows = list(reader)
    if len(rows) < 18: raise ValueError(f"Expected at least 18 rows for six layouts and three replicates; found {len(rows)}")
    if {r["layout_signature"] for r in rows} != EXPECTED: raise ValueError("Expected exactly six declared layouts")
    if any(r["group_structure_audit"] != "PASS" for r in rows): raise ValueError("Group-structure audit failed")
    mgxs_hashes = {r["mgxs_sha256"] for r in rows}
    if len(mgxs_hashes) != 1: raise ValueError("All candidate runs must share one MGXS hash")
    if len({r["statepoint_sha256"] for r in rows}) != len(rows): raise ValueError("Statepoint hashes are not unique")
    
    for r in rows:
        r["keff"] = float(r["keff_mean"]); r["keff_sd"] = float(r["keff_std_dev"])
        r["fpeak"] = float(r["fission_rate_peaking_factor"])
        if not all(math.isfinite(r[k]) for k in ("keff","keff_sd","fpeak")): raise ValueError("Non-finite estimate")
    groups = defaultdict(list)
    for r in rows: groups[r["layout_signature"]].append(r)
    if any(len(groups[s]) < 3 for s in EXPECTED): raise ValueError("Need at least three replicates per layout")
    counts = {len(groups[s]) for s in EXPECTED}
    if len(counts) != 1: raise ValueError("Equal-allocation comparison requires the same replicate count per layout")
    for sig in EXPECTED:
        if len({r["seed"] for r in groups[sig]}) != len(groups[sig]):
            raise ValueError(f"Seed identifiers are not unique within layout {sig}")
    return rows

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True); p.add_argument("--out",type=Path,required=True)
    p.add_argument("--sqa-reads",type=int,default=200); p.add_argument("--sqa-sweeps",type=int,default=200); p.add_argument("--sqa-seed",type=int,default=20261011)
    a=p.parse_args()
    if a.sqa_reads<1 or a.sqa_sweeps<1: raise ValueError("SQA reads/sweeps must be positive")
    rows=load_rows(a.input); groups=defaultdict(list)
    for r in rows: groups[r["layout_signature"]].append(r)
    mgxs_hashes = {r["mgxs_sha256"] for r in rows}
    summaries=[]
    for sig in sorted(EXPECTED):
        g=groups[sig]
        summaries.append({"layout_signature":sig,"replicates":len(g),
          "mean_keff":statistics.mean(r["keff"] for r in g),
          "between_seed_sd_keff":statistics.stdev(r["keff"] for r in g),
          "mean_fission_peaking_proxy":statistics.mean(r["fpeak"] for r in g),
          "between_seed_sd_fission_peaking_proxy":statistics.stdev(r["fpeak"] for r in g),
          "mean_reported_within_run_keff_sd":statistics.mean(r["keff_sd"] for r in g),
          "seed_ids":sorted(int(r["seed"]) for r in g)})
    # Fixed-budget equal allocation: same 18 physical runs, three per design.
    # Objective is lower mean dimensionless fission-peaking proxy; no invented keff acceptance band.
    rs=min(summaries,key=lambda s:(s["mean_fission_peaking_proxy"],s["layout_signature"]))
    # Reproduce existing CB-PFR smoke limits; these are illustrative only.
    kmin,kmax,fmax,z,kscale,fscale,risk=1.13,1.22,2.0,2.0,0.01,0.1,1.0
    scored=[]
    for s in summaries:
        ku=max(s["between_seed_sd_keff"],s["mean_reported_within_run_keff_sd"])
        klo,khi=s["mean_keff"]-z*ku,s["mean_keff"]+z*ku
        fhi=s["mean_fission_peaking_proxy"]+z*s["between_seed_sd_fission_peaking_proxy"]
        v=(max(0.0,kmin-klo)+max(0.0,khi-kmax))/kscale+max(0.0,fhi-fmax)/fscale
        feasible=klo>=kmin and khi<=kmax and fhi<=fmax
        scored.append({**s,"operational_keff_interval":[klo,khi],"operational_fission_proxy_upper":fhi,
          "illustrative_screen_feasible":feasible,"illustrative_normalized_violation":v,
          "cbpfr_score_raw":s["mean_fission_peaking_proxy"]+risk*s["between_seed_sd_fission_peaking_proxy"]})
    feasible=[s for s in scored if s["illustrative_screen_feasible"]]
    cb=min(feasible,key=lambda s:(s["illustrative_normalized_violation"],s["cbpfr_score_raw"],s["layout_signature"])) if feasible else None
    # One-hot selector QUBO, using same normalized CB-PFR score and penalties as smoke implementation.
    try:
        from dwave.samplers import PathIntegralAnnealingSampler
    except ImportError as e: raise RuntimeError("Install dwave-samplers to run classical SQA") from e
    order=[s["layout_signature"] for s in summaries]
    raw={s["layout_signature"]:s["cbpfr_score_raw"] for s in scored}
    lo,hi=min(raw.values()),max(raw.values())
    norm={k:((v-lo)/(hi-lo) if hi>lo else 0.0) for k,v in raw.items()}
    penalty,infeasible_penalty=2.0,2.0; q={}
    for i,sig in enumerate(order):
        item=next(s for s in scored if s["layout_signature"]==sig)
        q[(i,i)]=norm[sig]+(0.0 if item["illustrative_screen_feasible"] else infeasible_penalty)-penalty
        for j in range(i+1,len(order)): q[(i,j)]=2.0*penalty
    energies=[]
    for mask in range(1<<len(order)):
        bits=[(mask>>i)&1 for i in range(len(order))]
        energy=sum(q[(i,i)]*bits[i] for i in range(len(order)))
        energy+=sum(q[(i,j)]*bits[i]*bits[j] for i in range(len(order)) for j in range(i+1,len(order)))
        energies.append((energy,bits))
    exact_energy=min(e for e,_ in energies)
    exact_bits=[b for e,b in energies if math.isclose(e,exact_energy,abs_tol=1e-10)]
    if len(exact_bits)!=1 or sum(exact_bits[0])!=1: raise RuntimeError("No unique exact one-hot minimizer")
    exact_winner=order[exact_bits[0].index(1)]
    sampler=PathIntegralAnnealingSampler()
    sampleset=sampler.sample_qubo(q,num_reads=a.sqa_reads,num_sweeps=a.sqa_sweeps,seed=a.sqa_seed)
    rec=sampleset.record; total=int(sum(int(n) for n in rec.num_occurrences))
    best_energy=float(sampleset.first.energy); best_bits=[int(sampleset.first.sample[i]) for i in range(len(order))]
    sqa_winner=order[best_bits.index(1)] if sum(best_bits)==1 else None
    hits=sum(int(n) for e,n in zip(rec.energy,rec.num_occurrences) if math.isclose(float(e),exact_energy,abs_tol=1e-8))
    onehot=sum(int(n) for sample,n in zip(rec.sample,rec.num_occurrences) if sum(int(v) for v in sample)==1)
    payload={
      "schema_version":"1.0","status":"RETROSPECTIVE_SMOKE_DATA_COMPARISON_NOT_PHYSICAL_VALIDATION",
      "data_validation":{"rows":len(rows),"layouts":6,"replicates_per_layout":len(groups[next(iter(EXPECTED))]),"unique_statepoint_hashes":True,
        "unique_seed_ids_within_each_layout":True,"common_mgxs_hash":next(iter(mgxs_hashes)),"all_group_audits_pass":True,
        "recorded_run_budget":{"batches":100,"inactive":10,"particles_per_batch":1000}},
      "objective":"minimize mean dimensionless assembly fission-rate-peaking proxy; lower is better",
      "rs_method":"fixed-budget equal allocation; 18 archived runs total, 3 per layout; retrospective, not adaptive",
      "rs_selected_layout":rs["layout_signature"],"cbpfr_method":"existing CB-PFR heuristic with illustrative, non-authoritative limits",
      "cbpfr_selected_layout":cb["layout_signature"] if cb else None,
      "selection_agreement":bool(cb and cb["layout_signature"]==rs["layout_signature"]),
      "cbpfr_incremental_selection_gain_demonstrated":False,
      "cbpfr_gain_reason":"R&S selects the same layout on this dataset; incremental selection gain is not demonstrated.",
      "qubo_exact":{"variables":len(order),"binary_states_enumerated":len(energies),"exact_minimum_energy":exact_energy,
        "exact_minimizer_layout":exact_winner,"unique_one_hot_minimizer":True},
      "classical_sqa":{"sampler":"dwave.samplers.PathIntegralAnnealingSampler","not_quantum_hardware":True,
        "reads_requested":a.sqa_reads,"sweeps_per_read":a.sqa_sweeps,"seed":a.sqa_seed,"reads_returned":total,"best_energy":best_energy,
        "best_sample_one_hot":sum(best_bits)==1,"best_sample_layout":sqa_winner,"exact_ground_state_hits":hits,
        "empirical_ground_state_hit_rate":hits/total if total else None,"one_hot_sample_count":onehot,
        "one_hot_sample_rate":onehot/total if total else None,"exact_energy_match":math.isclose(best_energy,exact_energy,abs_tol=1e-8)},
      "candidate_summaries":scored,
      "interpretation_limits":[
        "Exploratory smoke-budget OpenMC data; not benchmark-grade convergence.",
        "Fission-peaking is a dimensionless proxy, not absolute power or a safety metric.",
        "CB-PFR limits are illustrative, not authoritative C5G7 acceptance criteria.",
        "R&S comparison is retrospective equal allocation, not adaptive sequential R&S.",
        "Legacy fresh/once_burned/twice_burned QUBO has no defensible mapping to these UO2/MOX layouts.",
        "Classical simulated quantum annealing is not QPU execution and does not establish quantum advantage.",
        "This analysis cannot certify physical validation or close all scientific claims."]}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(payload,indent=2)); return 0

if __name__=="__main__": raise SystemExit(main())
