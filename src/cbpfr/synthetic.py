"""Clearly segregated synthetic CB-PFR method-verification experiments."""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
import random
from typing import Any, Mapping
from .qubo import BURNUP_LABELS, Candidate, QuboModel, enumerate_feasible_candidates
from .ranking import MetricLimit, PhysicalEstimate, RankedCandidate, rank_all_methods, selected_is_conservatively_feasible

def _fresh_ring_pairs(model: QuboModel, candidate: Candidate) -> int:
    decoded=model.decode(candidate.vector)
    return sum(decoded[left]==BURNUP_LABELS[0] and decoded[right]==BURNUP_LABELS[0] for left,right in model.spec.edges if left in model.spec.boundary and right in model.spec.boundary)

def _arrangement_code(model: QuboModel, candidate: Candidate) -> int:
    decoded=model.decode(candidate.vector)
    return sum(position_index+1 for position_index,position in enumerate(model.spec.positions) if decoded[position]==BURNUP_LABELS[0])

def _serialize_selection(selection: RankedCandidate)->dict[str,Any]:
    physical=selection.physical
    return {"candidate_id":selection.candidate.candidate_id,"input_index":selection.input_index,"qubo_energy":selection.qubo_energy,"qubo_feasible":selection.qubo_indicator==0,"ranking_key":list(selection.ranking_key),"conservatively_feasible":selected_is_conservatively_feasible(selection),"physical_indicator":None if physical is None else physical.indicator,"aggregate_conservative_violation":None if physical is None else physical.aggregate_violation}

def run_synthetic_pilot(model:QuboModel,config:Mapping[str,Any])->tuple[list[dict[str,Any]],dict[str,Any]]:
    metric_raw=config["metric"]
    metric=MetricLimit(name=metric_raw["name"],lower=metric_raw.get("lower"),upper=metric_raw.get("upper"),z=float(metric_raw["z"]),scale=float(metric_raw["scale"]),weight=float(metric_raw["weight"]),uncertainty_kind=metric_raw["uncertainty_kind"],units=metric_raw["units"],bound_kind=metric_raw.get("bound_kind","operational_heuristic"))
    uniform_margins={metric.name:float(config["uniform_margin"])}
    all_candidates=enumerate_feasible_candidates(model)
    sample_size=int(config["candidate_pool_size"])
    if sample_size>len(all_candidates): raise ValueError("candidate_pool_size exceeds number of feasible toy-core candidates")
    trial_records=[]
    for trial_index in range(int(config["trials"])):
        trial_seed=int(config["seed"])+trial_index
        rng=random.Random(trial_seed)
        candidates=rng.sample(all_candidates,sample_size)
        estimates={}; reference={}; candidates_payload=[]
        for candidate in candidates:
            pair_count=_fresh_ring_pairs(model,candidate)
            true_response=float(config["true_response_base"])+float(config["fresh_ring_pair_increment"])*pair_count
            standard_error=float(config["low_standard_error"]) if _arrangement_code(model,candidate)%2==0 else float(config["high_standard_error"])
            observed=true_response+rng.gauss(0.0,standard_error)
            independent_reference=true_response+rng.gauss(0.0,float(config["reference_standard_error"]))
            reference_feasible=independent_reference<=float(config["reference_upper"])
            estimates[candidate.candidate_id]=PhysicalEstimate(candidate.candidate_id,{metric.name:(observed,standard_error)})
            reference[candidate.candidate_id]=(independent_reference,reference_feasible,pair_count,true_response)
            candidates_payload.append({"candidate_id":candidate.candidate_id,"vector":list(candidate.vector),"synthetic_true_response":true_response,"observed_estimate":observed,"injected_standard_error":standard_error,"fresh_ring_pair_count":pair_count,"independent_synthetic_reference":independent_reference,"reference_feasible":reference_feasible})
        rankings=rank_all_methods(model,candidates,estimates,[metric],uniform_margins)
        selections={}
        for method,ranking in rankings.items():
            selected=ranking[0]
            reference_value,reference_feasible,_,_=reference[selected.candidate.candidate_id]
            selections[method]={**_serialize_selection(selected),"independent_synthetic_reference":reference_value,"reference_feasible":reference_feasible}
        trial_records.append({"kind":"synthetic_method_verification_trial","not_physical_validation":True,"trial_index":trial_index,"seed":trial_seed,"candidate_pool":candidates_payload,"selections":selections})
    method_counts={}
    for method in ("qubo_only","point_estimate","cb_pfr","uniform_margin"):
        counts=Counter("reference_feasible" if record["selections"][method]["reference_feasible"] else "reference_infeasible" for record in trial_records)
        method_counts[method]=counts
    total=len(trial_records)
    summary={"kind":"synthetic_method_verification_summary","not_physical_validation":True,"trials":total,"candidate_pool_size":sample_size,"seed_policy":"trial_seed = configured_seed + trial_index","methods":{method:{"selected_reference_feasible":counts["reference_feasible"],"selected_reference_infeasible":counts["reference_infeasible"],"selected_reference_feasibility_rate":counts["reference_feasible"]/total} for method,counts in method_counts.items()}}
    return trial_records,summary

def write_synthetic_results(records:list[dict[str,Any]],summary:Mapping[str,Any],results_directory:str|Path)->tuple[Path,Path]:
    results_directory=Path(results_directory); results_directory.mkdir(parents=True,exist_ok=True)
    raw_path=results_directory/"synthetic_pilot_trials.jsonl"; summary_path=results_directory/"synthetic_pilot_summary.json"
    raw_path.write_text("".join(json.dumps(record,sort_keys=True,allow_nan=False)+"\n" for record in records),encoding="utf-8")
    summary_path.write_text(json.dumps(summary,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    return raw_path,summary_path
