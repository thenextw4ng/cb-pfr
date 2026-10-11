#!/usr/bin/env python3
"""Low-cost OpenMC comparison on distinct toy physical configurations.

This is an exploratory screening exercise, NOT benchmark-grade validation.
It compares three physically distinct fuel/moderator arrangements from the
OpenMC bundled C5G7-derived 2x2 multigroup example. Each configuration receives
the same low computational budget and independent seeds. R&S policy selection
is deliberately reported as exploratory because the replication count and
particle budget are too small for confirmatory claims.
"""
from __future__ import annotations
import json, os
from pathlib import Path
import numpy as np
import openmc

OUT = Path("results/openmc_distinct_candidates_rs_2026-10-11")
BATCHES = int(os.getenv("OPENMC_BATCHES", "12"))
INACTIVE = int(os.getenv("OPENMC_INACTIVE", "4"))
PARTICLES = int(os.getenv("OPENMC_PARTICLES", "300"))
THREADS = int(os.getenv("OPENMC_THREADS", "2"))
SEEDS = [int(x) for x in os.getenv("OPENMC_SEEDS", "20261011,20261012,20261013").split(",")]
Z = float(os.getenv("CBPFR_Z", "1.96"))
THRESHOLD = float(os.getenv("KEFF_THRESHOLD", "1.0"))

def build_candidate(name: str, fuel_count: int):
    model = openmc.examples.random_ray_lattice()
    # Locate the top-level 2x2 RectLattice, excluding the nested 10x10 moderator lattice.
    lattices = [cell.fill for cell in model.geometry.get_all_cells().values()
                if isinstance(cell.fill, openmc.RectLattice)
                and np.asarray(cell.fill.universes, dtype=object).shape == (2, 2)]
    if not lattices:
        raise RuntimeError("Could not locate the 2x2 lattice in the bundled example")
    lat = lattices[0]
    arr = np.asarray(lat.universes, dtype=object).copy()
    flat = list(arr.flat)
    # Fuel universe occurs three times; moderator-only universe occurs once.
    counts = {id(u): sum(id(v) == id(u) for v in flat) for u in flat}
    fuel = max(flat, key=lambda u: counts[id(u)])
    moderator = min(flat, key=lambda u: counts[id(u)])
    # Deterministic arrangements with exactly fuel_count fuel positions.
    patterns = {
        3: [[fuel, fuel], [fuel, moderator]],
        2: [[fuel, moderator], [fuel, moderator]],
        1: [[fuel, moderator], [moderator, moderator]],
    }
    lat.universes = patterns[fuel_count]
    model.settings.run_mode = "eigenvalue"
    model.settings.energy_mode = "multi-group"
    model.settings.batches = BATCHES
    model.settings.inactive = INACTIVE
    model.settings.particles = PARTICLES
    model.settings.seed = SEEDS[0]
    try:
        model.settings.random_ray = {}
    except Exception:
        pass
    model.settings.output = {"summary": True, "tallies": True}
    return model

def run_one(name, fuel_count, seed):
    model = build_candidate(name, fuel_count)
    model.settings.seed = seed
    run_dir = OUT / name / f"seed_{seed}"
    run_dir.mkdir(parents=True, exist_ok=True)
    model.export_to_xml(directory=str(run_dir / "inputs"))
    sp_path = model.run(cwd=str(run_dir / "run"), threads=THREADS)
    with openmc.StatePoint(sp_path) as sp:
        k = float(sp.keff.n)
        sd = float(sp.keff.s)
    return {"candidate":name,"fuel_pins":fuel_count,"seed":seed,
            "keff":k,"keff_sd":sd,"batches":BATCHES,
            "inactive":INACTIVE,"particles_per_batch":PARTICLES}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    configs = [("three_fuel_one_moderator",3),("two_fuel_two_moderator",2),
               ("one_fuel_three_moderator",1)]
    rows = []
    for name, n_fuel in configs:
        for seed in SEEDS:
            print(f"Running {name}, seed={seed}", flush=True)
            rows.append(run_one(name,n_fuel,seed))
    grouped = {}
    for name, n_fuel in configs:
        rs = [r for r in rows if r["candidate"] == name]
        mean = float(np.mean([r["keff"] for r in rs]))
        between_sd = float(np.std([r["keff"] for r in rs], ddof=1)) if len(rs)>1 else None
        within_sd = float(np.mean([r["keff_sd"] for r in rs]))
        lower = mean - Z * (between_sd if between_sd is not None else within_sd)
        grouped[name] = {"fuel_pins":n_fuel,"replicates":len(rs),"mean_keff":mean,
                         "between_seed_sd":between_sd,"mean_openmc_reported_sd":within_sd,
                         "lower_bound":lower,"conservative_feasible":lower >= THRESHOLD,
                         "violation":max(0.0,THRESHOLD-lower)}
    # Illustrative selection policies on physical candidates. Since this is an
    # eigenvalue screen, lower keff is NOT asserted to mean a better/safe design.
    # We report raw k-eff ordering and feasibility-screen output separately.
    ordered = sorted(grouped.items(), key=lambda kv: kv[1]["mean_keff"])
    ranked_feas = sorted(grouped.items(), key=lambda kv:(0 if kv[1]["conservative_feasible"] else 1,
                                                          kv[1]["violation"],kv[1]["mean_keff"]))
    result = {
      "study_id":"cbpfr_openmc_distinct_candidate_exploratory_rs_v1",
      "status":"completed",
      "openmc_version":openmc.__version__,
      "model":"OpenMC bundled C5G7-derived 2x2 multigroup lattice; distinct fuel/moderator arrangements",
      "run_settings":{"batches":BATCHES,"inactive":INACTIVE,"particles_per_batch":PARTICLES,
                      "threads":THREADS,"seeds":SEEDS,"runs_total":len(rows)},
      "feasibility_threshold_keff":THRESHOLD,"z":Z,
      "raw_runs":rows,"candidate_summary":grouped,
      "ascending_mean_keff_order":[name for name,_ in ordered],
      "cbpfr_style_conservative_screen_order":[name for name,_ in ranked_feas],
      "interpretation":"Exploratory low-budget comparison on distinct geometry arrangements. k-eff is an observable, not a complete design objective or safety criterion. Threshold 1.0 is a screening value, not a validated acceptance rule.",
      "physical_validation":"EXPLORATORY_OPENMC_SCREEN_ONLY_NOT_ESTABLISHED",
      "claims_not_supported":["reactor safety or design feasibility","canonical C5G7 benchmark agreement",
        "CB-PFR general superiority","physical validity of QUBO mapping","a validated R&S treatment effect"]
    }
    (OUT/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    (OUT/"per_run_results.csv").write_text("candidate,fuel_pins,seed,keff,keff_sd,batches,inactive,particles_per_batch\n"+
       "".join(f'{r["candidate"]},{r["fuel_pins"]},{r["seed"]},{r["keff"]:.12g},{r["keff_sd"]:.12g},{r["batches"]},{r["inactive"]},{r["particles_per_batch"]}\n' for r in rows))
    print(json.dumps(result,indent=2))

if __name__ == "__main__":
    main()
