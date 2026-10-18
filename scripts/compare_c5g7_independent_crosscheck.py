#!/usr/bin/env python3
"""Audit P4/P5 artifacts and cross-check canonical UMMU P5 against C5G7 references."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, re, statistics
from pathlib import Path

LAYOUTS = {"MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM"}
K_REF, K_REF_SD = 1.18655, 0.000095
P_MAX_REF, P_MIN_REF = 2.498, 0.232
SN_COMMIT = "db421c969ee2de83e2d2ae2b14bda368567b558d"

def readj(p):
    try:
        x = json.loads(p.read_text(encoding="utf-8"))
        return x if isinstance(x, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}

def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def phase(name):
    for p in ("P4", "P5"):
        if f"-{p}-" in name:
            return p
    return "UNKNOWN"

def collect(root):
    rows = []
    for study_path in sorted(root.rglob("STUDY_SUMMARY.json")):
        artifact = study_path.relative_to(root).parts[0]
        ph = phase(artifact)
        if ph not in {"P4", "P5"}:
            continue
        study = readj(study_path)
        audit = readj(study_path.parent / "analysis" / "raw_hdf5_posthoc_reaudit.json")
        for case in study.get("cases", []):
            cid = str(case.get("candidate_id", "UNKNOWN"))
            phys = case.get("physical_results") or {}
            cdir = study_path.parent / cid
            rel = phys.get("statepoint")
            sp = cdir / rel if isinstance(rel, str) else None
            fission = readj(cdir / "analysis" / "assembly_fission.json")
            rows.append({
                "phase": ph, "artifact": artifact, "candidate_id": cid,
                "layout": cid.removeprefix("c5g7-2x2-"), "seed": case.get("seed"),
                "batches": (study.get("settings") or {}).get("batches"),
                "inactive": (study.get("settings") or {}).get("inactive"),
                "particles": (study.get("settings") or {}).get("particles"),
                "keff_mean": phys.get("keff_mean"), "keff_sd_within_run": phys.get("keff_std_dev"),
                "peaking_proxy": fission.get("fission_rate_peaking_factor"),
                "raw_hdf5_posthoc_reaudit": audit.get("status", "MISSING"),
                "statepoint": str(sp) if sp else None,
                "statepoint_exists": bool(sp and sp.is_file()),
                "statepoint_sha256": sha(sp) if sp and sp.is_file() else None,
            })
    return rows

def sn_map(path):
    a = [[math.nan for _ in range(34)] for _ in range(34)]
    count = 0
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        if not {"pc","pr","norm_power"}.issubset(set(r.fieldnames or [])):
            raise ValueError("S_N pin-power CSV has unexpected columns")
        for row in r:
            x, y = int(row["pc"]), int(row["pr"])
            # External solver uses global 1-based pin coordinates: x=1..34,
            # fuel y=18..51; row-major order corresponds to the OpenMC mesh.
            if 1 <= x <= 34 and 18 <= y <= 51:
                a[y-18][x-1] = float(row["norm_power"]); count += 1
    if count != 1156 or any(not math.isfinite(v) for rr in a for v in rr):
        raise ValueError(f"expected 1156 finite S_N fuel-pin values, got {count}")
    flat = [v for rr in a for v in rr]
    return a, {"pin_count": count, "min_normalized_pin_power": min(flat), "max_normalized_pin_power": max(flat)}

def openmc_map(path):
    import h5py, numpy as np
    with h5py.File(path, "r") as f:
        dims = tuple(int(v) for v in f["tallies/meshes/mesh 1/dimension"][:])
        if dims != (51,51,1): raise ValueError(f"OpenMC mesh dimensions {dims}, expected (51,51,1)")
        t = f["tallies/tally 1"]
        scores = [x.decode() if isinstance(x, bytes) else str(x) for x in t["score_bins"][:]]
        if "fission" not in scores: raise ValueError("OpenMC tally lacks fission score")
        raw = t["results"][:, scores.index("fission"), 0].reshape((51,51), order="F")
        # Extract 34 x 34 fuel pins; transpose from [x,y] to [row-y,col-x].
        pins = np.asarray(raw[0:34,17:51].T, dtype=float)
        if pins.shape != (34,34) or not np.isfinite(pins).all() or np.any(pins < 0):
            raise ValueError("OpenMC fuel pin map invalid")
        if pins.mean() <= 0: raise ValueError("OpenMC fuel pin mean is not positive")
        return (pins / pins.mean()).tolist()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifacts-root", type=Path, required=True)
    ap.add_argument("--sn-csv", type=Path, required=True)
    ap.add_argument("--sn-log", type=Path, required=True)
    ap.add_argument("--outdir", type=Path, required=True)
    a = ap.parse_args()
    a.outdir.mkdir(parents=True, exist_ok=True)
    rows = collect(a.artifacts_root)
    counts = {p: sum(x["phase"] == p for x in rows) for p in ("P4","P5")}
    by = {p: {l: sum(x["phase"] == p and x["layout"] == l for x in rows) for l in sorted(LAYOUTS)} for p in ("P4","P5")}
    issues = []
    if counts != {"P4":18,"P5":18}: issues.append(f"Expected 18 P4 and 18 P5 rows, found {counts}")
    for ph in ("P4","P5"):
        for layout in LAYOUTS:
            sub = [x for x in rows if x["phase"] == ph and x["layout"] == layout]
            if len(sub) != 3: issues.append(f"{ph}/{layout}: expected 3 records, got {len(sub)}")
            seeds = [x["seed"] for x in sub]
            if None in seeds or len(set(seeds)) != len(seeds): issues.append(f"{ph}/{layout}: missing/duplicate seeds {seeds}")
            for x in sub:
                if x["raw_hdf5_posthoc_reaudit"] != "PASS": issues.append(f"{ph}/{layout}/{x['seed']}: raw HDF5 re-audit={x['raw_hdf5_posthoc_reaudit']}")
                if not x["statepoint_exists"] or not x["statepoint_sha256"]: issues.append(f"{ph}/{layout}/{x['seed']}: statepoint/hash missing")
    canonical = [x for x in rows if x["phase"] == "P5" and x["layout"] == "UMMU" and x["statepoint_exists"]]
    kscreen = {"status":"NOT_EVALUATED"}
    spatial = {"status":"NOT_EVALUATED"}
    snk = snmax = snmin = None
    log = a.sn_log.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"C5G7\s+k_eff\s+\(this solver\)\s*=\s*([0-9.]+)", log)
    mx = re.search(r"Pin power:\s+fuel pins=\s*\d+\s+max=\s*([0-9.]+)", log)
    mn = re.search(r"Pin power:\s+fuel pins=\s*\d+\s+max=\s*[0-9.]+\s+min=\s*([0-9.]+)", log)
    if m: snk = float(m.group(1))
    if mx: snmax = float(mx.group(1))
    if mn: snmin = float(mn.group(1))
    if len(canonical) == 3:
        kv = [float(x["keff_mean"]) for x in canonical]
        km = statistics.fmean(kv); sdb = statistics.stdev(kv); sem = sdb / math.sqrt(3)
        comb = math.sqrt(sem*sem + K_REF_SD*K_REF_SD); diff = (km-K_REF)*1e5
        z = abs(km-K_REF)/comb if comb else math.inf
        kscreen = {
            "status": "PASS_PROJECT_SCREEN" if abs(diff) <= 100 and z <= 2 else "REVIEW_PROJECT_SCREEN_NOT_MET",
            "n_independent_p5_seeds":3, "keff_values":kv, "mean_keff":km,
            "between_seed_sd":sdb, "between_seed_sem":sem,
            "published_reference_keff":K_REF, "published_reference_standard_uncertainty":K_REF_SD,
            "combined_standard_uncertainty":comb, "difference_pcm":diff, "absolute_difference_pcm":abs(diff),
            "combined_uncertainty_z":z, "project_limits":{"absolute_difference_pcm_max":100,"combined_uncertainty_z_max":2},
            "official_nea_acceptance":False,
        }
        try:
            import numpy as np
            ref, ref_sum = sn_map(a.sn_csv)
            maps = [openmc_map(Path(x["statepoint"])) for x in canonical]
            got = np.mean(np.asarray(maps,dtype=float),axis=0)
            refa = np.asarray(ref,dtype=float)
            rel = (got-refa)/refa
            spatial = {
                "status":"COMPUTED_CROSS_CODE_SHAPE_CHECK_NOT_OFFICIAL_ACCEPTANCE",
                "n_openmc_seeds":3, "fuel_pin_count":1156,
                "openmc_quantity":"normalized mesh-bin fission-rate tally; relative-shape proxy, not absolute power",
                "independent_quantity":"normalized pin-power output from pinned S_N deterministic solver",
                "comparison_metrics":{
                    "rms_relative_error_percent":float(np.sqrt(np.mean(rel*rel))*100),
                    "mean_absolute_relative_error_percent":float(np.mean(np.abs(rel))*100),
                    "max_absolute_relative_error_percent":float(np.max(np.abs(rel))*100),
                    "openmc_max_normalized_pin_fission_rate":float(got.max()),
                    "openmc_min_normalized_pin_fission_rate":float(got.min()),
                    "sn_max_normalized_pin_power":float(refa.max()),
                    "sn_min_normalized_pin_power":float(refa.min()),
                },
                "sn_pin_map_summary":ref_sum,
                "published_mcnp_pin_power_summary":{"max":P_MAX_REF,"min":P_MIN_REF,"max_relative_sd":0.0016,"min_relative_sd":0.0058},
                "sn_max_vs_published_percent":(snmax/P_MAX_REF-1)*100 if snmax is not None else None,
                "sn_min_vs_published_percent":(snmin/P_MIN_REF-1)*100 if snmin is not None else None,
                "interpretation":"Fission-rate and normalized-power tallies are related but not identical. This spatial comparison is cross-code evidence only; it is not a safety limit or official acceptance test.",
            }
        except Exception as e:
            spatial = {"status":"CROSS_CODE_COMPARISON_FAILED_OR_INCOMPLETE","error":str(e)}
    else:
        issues.append(f"Need three P5 UMMU statepoints, found {len(canonical)}")
    p6files = list(a.artifacts_root.rglob("p45_campaign_audit.json"))
    p6 = readj(p6files[0]) if p6files else {}
    pc = p6.get("physical_comparison") or {}
    p6summary = {"report_found":bool(p6files),"integrity_status":p6.get("status"),
                 "physical_comparison_status":pc.get("status"),"claims":pc.get("claims"),
                 "baseline_results":pc.get("baseline_results"),"regret_summary":pc.get("regret_summary"),
                 "caveat":"Pilot comparison uses three independent held-out P5 seeds per candidate; 10,000 bootstrap resamples do not mean 10,000 independent simulations."}
    report = {
      "schema_version":"1.0",
      "protocol":"C5G7 independent cross-code and published-reference check",
      "source_campaign":{"run_id":39098770358,"url":"https://github.com/thenextw4ng/cb-pfr/actions/runs/39098770358"},
      "integrity":{"status":"PASS" if not issues else "INCOMPLETE_OR_FAIL","phase_counts":counts,"layout_phase_counts":by,"issue_count":len(issues),"issues":issues,"run_records":rows},
      "published_reference":{"benchmark":"OECD/NEA C5G7 2-D 2x2 UO2/MOX assembly benchmark","keff":K_REF,"keff_standard_uncertainty":K_REF_SD,
        "max_normalized_pin_power":P_MAX_REF,"min_normalized_pin_power":P_MIN_REF,
        "source":"https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2020.00124/full"},
      "canonical_openmc_keff_screen":kscreen,
      "independent_solver":{"repository":"https://github.com/EmreSakarya/c5g7-2d-transport-benchmark","pinned_commit":SN_COMMIT,
        "method":"2-D, seven-group S_N discrete ordinates with Cartesian digital-disk pin geometry",
        "keff":snk,"max_normalized_pin_power":snmax,"min_normalized_pin_power":snmin,
        "log_sha256":sha(a.sn_log),"pinpower_csv_sha256":sha(a.sn_csv),
        "limitation":"The solver reports known mesh-discretization bias relative to the MCNP benchmark; treat as an independent comparator, not ground truth."},
      "canonical_spatial_cross_code_check":spatial,
      "cbpfr_heldout_p6":p6summary,
      "decision":{"broad_physical_superiority":"NOT_ESTABLISHED",
        "limited_cbpfr_effectiveness":"ELIGIBLE_FOR_BOUNDED_INTERPRETATION" if not issues and kscreen.get("status")=="PASS_PROJECT_SCREEN" and spatial.get("status","").startswith("COMPUTED") and p6.get("status")=="EVIDENCE_INTEGRITY_PASS_INTERPRETATION_OPEN" else "NOT_ESTABLISHED_OR_REVIEW_REQUIRED",
        "reasons":["The canonical benchmark does not define a design-specific keff acceptance band for the five alternative layouts.",
          "The OpenMC tally here is fission rate, not absolute power or a licensed safety metric.",
          "P6 can support only a bounded claim about the declared six-layout model and held-out proxy.",
          "DIAGNOSTIC_REVIEW_REQUIRED is not a convergence certificate."]}}
    (a.outdir/"independent_physical_crosscheck.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    fields=["phase","candidate_id","layout","seed","batches","inactive","particles","keff_mean","keff_sd_within_run","peaking_proxy","raw_hdf5_posthoc_reaudit","statepoint_exists","statepoint_sha256"]
    with (a.outdir/"p4_p5_run_inventory.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for row in rows:
            w.writerow({"phase":row["phase"],"candidate_id":row["candidate_id"],"layout":row["layout"],"seed":row["seed"],
                "batches":row["batches"],"inactive":row["inactive"],"particles":row["particles"],"keff_mean":row["keff_mean"],
                "keff_sd_within_run":row["keff_sd_within_run"],"peaking_proxy":row["peaking_proxy"],
                "raw_hdf5_posthoc_reaudit":row["raw_hdf5_posthoc_reaudit"],"statepoint_exists":row["statepoint_exists"],"statepoint_sha256":row["statepoint_sha256"]})
    print(json.dumps({"integrity":report["integrity"]["status"],"phase_counts":counts,
      "canonical_keff_screen":kscreen.get("status"),"spatial_check":spatial.get("status"),
      "broad_physical_superiority":"NOT_ESTABLISHED","output":str(a.outdir/"independent_physical_crosscheck.json")},indent=2))
    return 0

if __name__ == "__main__":
    main()
