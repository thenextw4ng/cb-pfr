#!/usr/bin/env python3
"""Low-cost OpenMC replication screen with corrected subcriticality bound.

This is an exploratory method test on a C5G7-derived toy lattice, not a
canonical C5G7 benchmark and not a reactor-safety validation. Five distinct
fuel/moderator arrangements are simulated at equal budgets. Each candidate is
replicated under multiple independent seeds. A leave-one-seed-out analysis
compares point-estimate, CB-PFR-style upper-bound, and uniform-margin policies
against held-out runs. No QUBO-only baseline is claimed because no defensible
QUBO-to-geometry/physics mapping exists in this repository.
"""
from __future__ import annotations
import csv, json, os
from pathlib import Path
import numpy as np
import openmc

OUT = Path("results/openmc_cbpfr_subcritical_replicated_screen_2026-10-11")
BATCHES = int(os.getenv("OPENMC_BATCHES", "20"))
INACTIVE = int(os.getenv("OPENMC_INACTIVE", "6"))
PARTICLES = int(os.getenv("OPENMC_PARTICLES", "500"))
THREADS = int(os.getenv("OPENMC_THREADS", "2"))
SEEDS = [int(x) for x in os.getenv("OPENMC_SEEDS", "20261021,20261022,20261023,20261024,20261025").split(",")]
Z = float(os.getenv("CBPFR_Z", "1.96"))
THRESHOLD = float(os.getenv("KEFF_THRESHOLD", "1.0"))
UNIFORM_MARGIN = float(os.getenv("UNIFORM_MARGIN", "0.02"))

# Candidate designs: number of fuel positions and placement. Arrangement order
# is documented in the report; all use the same bundled fuel/moderator universes.
CANDIDATES = [
    ("four_fuel", [[1,1],[1,1]], 4),
    ("three_fuel", [[1,1],[1,0]], 3),
    ("two_fuel_adjacent", [[1,1],[0,0]], 2),
    ("two_fuel_diagonal", [[1,0],[0,1]], 2),
    ("one_fuel", [[1,0],[0,0]], 1),
]

def build_model(pattern):
    model = openmc.examples.random_ray_lattice()
    candidates = [c for c in model.geometry.get_all_cells().values()
                  if isinstance(c.fill, openmc.RectLattice)
                  and np.asarray(c.fill.universes, dtype=object).shape == (2, 2)]
    if not candidates:
        raise RuntimeError("2x2 top-level lattice not found in bundled example")
    lat = candidates[0].fill
    arr = np.asarray(lat.universes, dtype=object)
    flat = list(arr.flat)
    counts = {id(u): sum(id(v) == id(u) for v in flat) for u in flat}
    fuel = max(flat, key=lambda u: counts[id(u)])
    moderator = min(flat, key=lambda u: counts[id(u)])
    # Assign to an ndarray so each candidate's 2x2 spatial pattern is preserved.
    new = np.empty((2,2), dtype=object)
    for i in range(2):
        for j in range(2):
            new[i,j] = fuel if pattern[i][j] else moderator
    lat.universes = new.tolist()
    model.settings.run_mode = "eigenvalue"
    model.settings.energy_mode = "multi-group"
    model.settings.batches = BATCHES
    model.settings.inactive = INACTIVE
    model.settings.particles = PARTICLES
    model.settings.output = {"summary": True, "tallies": True}
    return model

def run_one(name, pattern, n_fuel, seed):
    model = build_model(pattern)
    model.settings.seed = seed
    run_dir = OUT / name / f"seed_{seed}"
    run_dir.mkdir(parents=True, exist_ok=True)
    inputs = run_dir / "inputs"
    inputs.mkdir(exist_ok=True)
    model.export_to_xml(directory=str(inputs))
    sp_path = model.run(cwd=str(run_dir / "run"), threads=THREADS)
    with openmc.StatePoint(sp_path) as sp:
        return {"candidate": name, "fuel_positions": n_fuel, "seed": seed,
                "keff": float(sp.keff.n), "keff_sd": float(sp.keff.s),
                "batches": BATCHES, "inactive": INACTIVE,
                "particles_per_batch": PARTICLES}

def policy_pick(train_rows, policy):
    stats = {}
    for name, _, n_fuel in CANDIDATES:
        xs = [r["keff"] for r in train_rows if r["candidate"] == name]
        if not xs:
            continue
        mean = float(np.mean(xs))
        sd = float(np.std(xs, ddof=1)) if len(xs) > 1 else float("inf")
        if policy == "point_estimate":
            upper = mean
        elif policy == "cbpfr_upper_bound":
            upper = mean + Z * sd
        elif policy == "uniform_margin":
            upper = mean + UNIFORM_MARGIN
        else:
            raise ValueError(policy)
        feasible = upper <= THRESHOLD
        violation = max(0.0, upper - THRESHOLD)
        # All policies use the same declared objective: satisfy subcriticality
        # conservatively, then prefer the lowest predicted k-eff.
        stats[name] = {"mean": mean, "sd": sd, "upper": upper,
                       "feasible": feasible, "violation": violation}
    return min(stats, key=lambda n: (not stats[n]["feasible"],
                                    stats[n]["violation"], stats[n]["mean"])), stats

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw = []
    for name, pattern, n in CANDIDATES:
        for seed in SEEDS:
            print(f"Running {name}, seed={seed}", flush=True)
            raw.append(run_one(name, pattern, n, seed))
    summary = {}
    for name, pattern, n in CANDIDATES:
        rs = [r for r in raw if r["candidate"] == name]
        vals = [r["keff"] for r in rs]
        summary[name] = {
            "fuel_positions": n, "replicates": len(rs),
            "mean_keff": float(np.mean(vals)),
            "between_seed_sd": float(np.std(vals, ddof=1)),
            "mean_openmc_reported_sd": float(np.mean([r["keff_sd"] for r in rs])),
            "empirical_min": float(np.min(vals)), "empirical_max": float(np.max(vals)),
            "fraction_heldout_runs_subcritical": float(np.mean(np.array(vals) < THRESHOLD)),
        }
    folds = []
    for heldout_seed in SEEDS:
        train = [r for r in raw if r["seed"] != heldout_seed]
        test = [r for r in raw if r["seed"] == heldout_seed]
        test_by_name = {r["candidate"]: r for r in test}
        for policy in ("point_estimate", "cbpfr_upper_bound", "uniform_margin"):
            chosen, stats = policy_pick(train, policy)
            heldout = test_by_name[chosen]
            folds.append({
                "heldout_seed": heldout_seed, "policy": policy,
                "selected_candidate": chosen,
                "training_predicted_mean_keff": stats[chosen]["mean"],
                "training_upper_screen": stats[chosen]["upper"],
                "training_screen_feasible": stats[chosen]["feasible"],
                "heldout_keff": heldout["keff"],
                "heldout_subcritical": heldout["keff"] < THRESHOLD,
                "training_candidate_stats": stats,
            })
    policy_summary = {}
    for policy in ("point_estimate", "cbpfr_upper_bound", "uniform_margin"):
        fs = [f for f in folds if f["policy"] == policy]
        policy_summary[policy] = {
            "heldout_subcritical_rate": float(np.mean([f["heldout_subcritical"] for f in fs])),
            "mean_heldout_keff": float(np.mean([f["heldout_keff"] for f in fs])),
            "selected_candidates": [f["selected_candidate"] for f in fs],
            "n_folds": len(fs),
        }
    result = {
      "study_id":"cbpfr_openmc_subcritical_replicated_screen_v1",
      "status":"completed",
      "openmc_version":openmc.__version__,
      "model":"OpenMC bundled C5G7-derived 2x2 multigroup lattice; five distinct fuel/moderator arrangements",
      "run_settings":{"batches":BATCHES,"inactive":INACTIVE,"particles_per_batch":PARTICLES,
                      "threads":THREADS,"seeds":SEEDS,"runs_total":len(raw)},
      "criterion":{"observable":"k-effective","subcritical_threshold":THRESHOLD,
                   "cbpfr_rule":"mean + z * between-seed SD <= threshold",
                   "z":Z,"uniform_margin":UNIFORM_MARGIN,
                   "caveat":"Between-seed SD from a small number of seeds is not a calibrated confidence interval."},
      "candidate_summary":summary,"leave_one_seed_out_folds":folds,
      "policy_summary":policy_summary,
      "interpretation":"Exploratory held-out screen on a C5G7-derived toy model. All policies use same candidate pool and same training/held-out split. Results are sensitive to low replication and simple criterion.",
      "physical_validation":"EXPLORATORY_SUBCRITICALITY_SCREEN_ONLY_NOT_ESTABLISHED",
      "claims_not_supported":["canonical C5G7 benchmark agreement","reactor safety or design certification",
        "valid QUBO-to-physics mapping","QUBO-only baseline comparison","general CB-PFR superiority"]
    }
    (OUT/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    with (OUT/"per_run_results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(raw[0].keys())); w.writeheader(); w.writerows(raw)
    with (OUT/"heldout_policy_comparison.csv").open("w",newline="") as f:
        fields=["heldout_seed","policy","selected_candidate","training_predicted_mean_keff",
                "training_upper_screen","training_screen_feasible","heldout_keff","heldout_subcritical"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for fold in folds: w.writerow({k:fold[k] for k in fields})
    print(json.dumps(result,indent=2))

if __name__ == "__main__":
    main()
