#!/usr/bin/env python3
"""Run the prespecified synthetic CB-PFR calibration and ranking experiment."""
from __future__ import annotations
import argparse,csv,json,random,sys
from math import sqrt
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from cbpfr.qubo import BURNUP_LABELS,CoreSpec,build_usmanov_style_qubo,enumerate_feasible_candidates
from cbpfr.ranking import MetricLimit,PhysicalEstimate,rank_all_methods
from cbpfr.experiments import held_out_lookup,paired_binary_difference,require_equal_evaluation_budget

def fresh_ring_pairs(model,candidate)->int:
    decoded=model.decode(candidate.vector)
    return sum(decoded[left]==BURNUP_LABELS[0] and decoded[right]==BURNUP_LABELS[0] for left,right in model.spec.edges if left in model.spec.boundary and right in model.spec.boundary)

def arrangement_indicator(model,candidate)->int:
    decoded=model.decode(candidate.vector)
    return sum(index+1 for index,position in enumerate(model.spec.positions) if decoded[position]==BURNUP_LABELS[0])%2

def metric_from_config(raw:dict[str,Any])->MetricLimit:
    return MetricLimit(name=raw["name"],lower=raw.get("lower"),upper=raw.get("upper"),z=float(raw["z"]),scale=float(raw["scale"]),weight=float(raw["weight"]),uncertainty_kind=raw["uncertainty_kind"],units=raw["units"],bound_kind=raw.get("bound_kind","operational_heuristic"))

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core",type=Path,default=ROOT/"config"/"toy_core_7.json")
    parser.add_argument("--config",type=Path,default=ROOT/"config"/"reduced_synthetic_calibration.json")
    parser.add_argument("--results-dir",type=Path,default=ROOT/"results"/"reduced_synthetic_benchmark")
    args=parser.parse_args()
    if args.results_dir.exists() and any(args.results_dir.iterdir()): raise FileExistsError(f"refusing to overwrite existing experiment directory: {args.results_dir}")
    config=json.loads(args.config.read_text(encoding="utf-8"))
    model=build_usmanov_style_qubo(CoreSpec.from_json(args.core))
    candidates=enumerate_feasible_candidates(model)
    metric=metric_from_config(config["metric"])
    all_rows=[]; coverage_count=0; observation_count=0
    methods=("qubo_only","point_estimate","cb_pfr","uniform_margin")
    for trial_index in range(int(config["trials"])):
        trial_seed=int(config["seed"])+trial_index
        rng=random.Random(trial_seed)
        pool=rng.sample(candidates,int(config["candidate_pool_size"]))
        estimates={}; truth={}
        for candidate in pool:
            standard_error=float(config["low_standard_error"]) if arrangement_indicator(model,candidate)==0 else float(config["high_standard_error"])
            latent=float(config["true_response_base"])+float(config["fresh_ring_pair_increment"])*fresh_ring_pairs(model,candidate)+float(config["arrangement_increment"])*arrangement_indicator(model,candidate)
            observed=latent+rng.gauss(0.0,standard_error)
            estimates[candidate.candidate_id]=PhysicalEstimate(candidate.candidate_id,{metric.name:(observed,standard_error)})
            truth[candidate.candidate_id]=latent
            coverage_count+=int(latent<=observed+metric.z*standard_error); observation_count+=1
        rankings=rank_all_methods(model,pool,estimates,[metric],{metric.name:float(config["uniform_margin"])})
        require_equal_evaluation_budget({method:len(pool) for method in methods},len(pool))
        selected_truth=held_out_lookup({method:rankings[method][0].candidate.candidate_id for method in methods},truth)
        for method in methods:
            selected=rankings[method][0]; latent_truth=selected_truth[method]
            all_rows.append({"kind":"synthetic_reduced_benchmark_post_evaluation_ranking","not_physical_validation":True,"study_id":config["study_id"],"trial_index":trial_index,"seed":trial_seed,"method":method,"candidate_id":selected.candidate.candidate_id,"selected_latent_true_response":latent_truth,"selected_true_feasible":latent_truth<=float(config["metric"]["upper"]),"ranking_observed_estimate":estimates[selected.candidate.candidate_id].values[metric.name][0],"ranking_reported_standard_error":estimates[selected.candidate.candidate_id].values[metric.name][1],"physical_evaluations_per_method":len(pool),"role":"post-evaluation ranking; all methods receive the identical synthetic observation pool"})
    args.results_dir.mkdir(parents=True,exist_ok=True)
    with (args.results_dir/"per_seed_results.csv").open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(all_rows[0])); writer.writeheader(); writer.writerows(all_rows)
    aggregate_rows=[]
    for method in methods:
        selected=[row for row in all_rows if row["method"]==method]
        feasibility=sum(bool(row["selected_true_feasible"]) for row in selected)/len(selected)
        aggregate_rows.append({"kind":"synthetic_reduced_benchmark_aggregate","not_physical_validation":True,"method":method,"trials":len(selected),"physical_evaluations_per_method":int(config["candidate_pool_size"]),"selected_true_feasibility_rate":feasibility,"mean_selected_latent_true_response":sum(float(row["selected_latent_true_response"]) for row in selected)/len(selected)})
    coverage=coverage_count/observation_count; nominal=float(config["nominal_one_sided_coverage"])
    coverage_report={"kind":"synthetic_known_normal_one_sided_bound_coverage","not_physical_validation":True,"observation_count":observation_count,"z":metric.z,"empirical_coverage":coverage,"nominal_one_sided_coverage":nominal,"nominal_binomial_standard_error":sqrt(nominal*(1.0-nominal)/observation_count),"interpretation":"This checks only the explicitly injected normal-error model with known standard errors. It does not calibrate MC/DC, OpenMC, surrogate, model-form, or parameter uncertainty."}
    cbpfr_outcomes=[bool(row["selected_true_feasible"]) for row in all_rows if row["method"]=="cb_pfr"]
    coverage_report["paired_cb_pfr_minus_baseline"]={method:paired_binary_difference(cbpfr_outcomes,[bool(row["selected_true_feasible"]) for row in all_rows if row["method"]==method]) for method in ("qubo_only","point_estimate","uniform_margin")}
    for filename,rows in (("main_results.csv",aggregate_rows),("ablation_results.csv",aggregate_rows)):
        with (args.results_dir/filename).open("w",newline="",encoding="utf-8") as handle:
            writer=csv.DictWriter(handle,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (args.results_dir/"coverage.json").write_text(json.dumps(coverage_report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (args.results_dir/"protocol_snapshot.json").write_text(json.dumps(config,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"coverage":coverage,"nominal":nominal,"results_dir":str(args.results_dir)},sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
