#!/usr/bin/env python3
"""Low-cost OpenMC smoke test plus CB-PFR-style ranking mechanics check.

Not a reactor benchmark. Three candidate estimates below are perturbations of
one model's k-eff, not three independent physical designs.
"""
import json, os
from pathlib import Path
import openmc

OUT = Path("results/openmc_cbpfr_smoke_2026-10-11")
OUT.mkdir(parents=True, exist_ok=True)

def main():
    model = openmc.examples.random_ray_lattice()
    s = model.settings
    s.run_mode = "eigenvalue"
    s.energy_mode = "multi-group"
    s.batches = int(os.getenv("OPENMC_BATCHES", "20"))
    s.inactive = int(os.getenv("OPENMC_INACTIVE", "5"))
    s.particles = int(os.getenv("OPENMC_PARTICLES", "500"))
    try:
        s.random_ray = {}
    except Exception:
        pass
    s.output = {"summary": True, "tallies": True}
    model.settings = s
    (OUT / "inputs").mkdir(exist_ok=True)
    model.export_to_xml(directory=str(OUT / "inputs"))
    sp_path = model.run(cwd=str(OUT / "run"), threads=int(os.getenv("OPENMC_THREADS", "2")))
    with openmc.StatePoint(sp_path) as sp:
        k = float(sp.keff.n)
        sd = max(float(sp.keff.s), 1e-8)
    z = float(os.getenv("CBPFR_Z", "1.96"))
    threshold = float(os.getenv("FEASIBILITY_THRESHOLD", "1.0"))
    candidates = []
    for name, delta, energy in [("replicate_A",-0.0004,0.0),("replicate_B",0.0,1.0),("replicate_C",0.0004,2.0)]:
        est = k + delta
        lower = est - z*sd
        violation = max(0.0, threshold-lower)
        candidates.append({"candidate":name,"estimate":est,"se":sd,"lower_bound":lower,
                           "conservative_feasible":lower >= threshold,"violation":violation,
                           "energy":energy,"rank_key":[0 if lower >= threshold else 1,violation,energy,name]})
    selected = sorted(candidates,key=lambda x:tuple(x["rank_key"]))[0]
    result = {
        "study_id":"cbpfr_openmc_low_cost_smoke_v1","status":"completed",
        "openmc_version":openmc.__version__,
        "model":"OpenMC bundled C5G7-derived 2x2 multigroup lattice example",
        "run_settings":{"batches":s.batches,"inactive":s.inactive,"particles_per_batch":s.particles},
        "keff_mean":k,"keff_sd_reported_by_openmc":sd,"threshold":threshold,"z":z,
        "candidate_rows":candidates,"selected_by_cbpfr_style_rule":selected["candidate"],
        "physical_validation":"SMOKE_TEST_ONLY_NOT_ESTABLISHED",
        "warning":"The three candidate estimates are artificial perturbations of one model result, not distinct physical designs. This checks execution and ranking mechanics only.",
        "claims_not_supported":["CB-PFR improves reactor performance","reactor design feasibility or safety","benchmark agreement","general R&S superiority"]
    }
    (OUT/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__ == "__main__":
    main()
