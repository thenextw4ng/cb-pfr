#!/usr/bin/env python3
"""Summarize repeatability across three independent low-budget C5G7 smoke rounds."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, statistics
from pathlib import Path
import xml.etree.ElementTree as ET


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def spearman(a, b):
    keys = sorted(set(a) & set(b))
    n = len(keys)
    return 1.0 - 6.0 * sum((a[k] - b[k]) ** 2 for k in keys) / (n * (n*n - 1))


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--study-root", required=True, type=Path)
    p.add_argument("--outdir", required=True, type=Path)
    a = p.parse_args()
    if a.outdir.exists() and any(a.outdir.iterdir()):
        p.error(f"refusing to overwrite nonempty output directory: {a.outdir}")
    rounds = sorted(d for d in a.study_root.glob("round_*") if (d/"STUDY_SUMMARY.json").is_file())
    if len(rounds) != 3:
        p.error(f"expected three round directories, found {len(rounds)}")
    rows, seed_list, statepoint_hashes, mgxs_hashes, commits, profiles = [], [], [], [], set(), set()
    layouts = {}
    round_values, round_ranks = {}, {}
    for rd in rounds:
        s = json.loads((rd/"STUDY_SUMMARY.json").read_text())
        if s.get("status") != "all_runs_completed_needs_independent_validation" or len(s.get("cases", [])) != 6:
            p.error(f"{rd.name}: six completed candidates required")
        commits.add(s.get("upstream_commit"))
        cfg=s["settings"]; profiles.add((cfg["batches"],cfg["inactive"],cfg["particles"],cfg["threads"]))
        audit_path=rd/"analysis/raw_hdf5_audit.json"
        if not audit_path.is_file():
            p.error(f"{rd.name}: raw HDF5 audit missing")
        audit=json.loads(audit_path.read_text())
        if audit.get("status")!="PASS" or audit.get("candidate_count")!=6:
            p.error(f"{rd.name}: raw HDF5 audit did not pass")
        round_values[rd.name]={}
        for c in s["cases"]:
            cid=c["candidate_id"]; phys=c.get("physical_results") or {}
            if c.get("status")!="completed" or phys.get("status")!="completed":
                p.error(f"{rd.name}/{cid}: run incomplete")
            if cid in layouts and layouts[cid]!=c["layout"]:
                p.error(f"{cid}: layout changed across rounds")
            layouts[cid]=c["layout"]
            case_dir=rd/cid
            statepoint_rel = phys.get("statepoint")
            if not isinstance(statepoint_rel, str) or not statepoint_rel:
                p.error(f"{rd.name}/{cid}: physical result lacks a statepoint path")
            sp = case_dir / statepoint_rel
            settings=case_dir/"model/2d/settings.xml"; mgxs=case_dir/"model/2d/mgxs.h5"
            if not sp.is_file() or not settings.is_file() or not mgxs.is_file():
                p.error(f"{rd.name}/{cid}: required file missing")
            sp_hash,settings_hash,mgxs_hash=sha(sp),sha(settings),sha(mgxs)
            expected=c.get("output_hashes_after_run") or {}
            if expected.get(statepoint_rel)!=sp_hash or expected.get("model/2d/settings.xml")!=settings_hash:
                p.error(f"{rd.name}/{cid}: output hash mismatch")
            if mgxs_hash!=phys.get("mgxs_sha256_before_transport") or mgxs_hash!=phys.get("mgxs_sha256_after_transport"):
                p.error(f"{rd.name}/{cid}: MGXS hash mismatch")
            seed=int(c["seed"])
            if int(ET.parse(settings).getroot().findtext("seed"))!=seed:
                p.error(f"{rd.name}/{cid}: seed mismatch")
            ar=next((x for x in audit["candidates"] if x.get("candidate_id")==cid),None)
            if not ar or ar.get("status")!="PASS" or ar.get("statepoint_sha256")!=sp_hash:
                p.error(f"{rd.name}/{cid}: raw HDF5 audit mismatch")
            k=float(phys["keff_mean"]); sd=float(phys["keff_std_dev"])
            if not math.isfinite(k) or not math.isfinite(sd) or sd<=0:
                p.error(f"{rd.name}/{cid}: invalid k_eff")
            seed_list.append(seed); statepoint_hashes.append(sp_hash); mgxs_hashes.append(mgxs_hash)
            round_values[rd.name][cid]=k
            rows.append({"round_id":rd.name,"seed_base":cfg["seed_base"],"candidate_id":cid,
                "layout_signature":cid.split("-")[-1],"seed":seed,"batches":cfg["batches"],
                "inactive":cfg["inactive"],"particles_per_batch":cfg["particles"],
                "keff_mean":k,"keff_std_dev":sd,"relative_sd_percent":sd/abs(k)*100,
                "statepoint_sha256":sp_hash,"settings_sha256":settings_hash,"mgxs_sha256":mgxs_hash,
                "raw_hdf5_audit":"PASS"})
    if len(layouts)!=6 or len(commits)!=1 or len(profiles)!=1 or len(set(seed_list))!=18 or len(set(statepoint_hashes))!=18 or len(set(mgxs_hashes))!=1:
        p.error("cross-round identity/settings/seed/statepoint/MGXS checks failed")
    if len({r["candidate_id"] for r in rows})!=6:
        p.error("candidate IDs are not stable")
    for rd in rounds:
        order=sorted(round_values[rd.name],key=round_values[rd.name].get)
        round_ranks[rd.name]={cid:i+1 for i,cid in enumerate(order)}
    summary=[]
    for cid in sorted(layouts):
        cr=[r for r in rows if r["candidate_id"]==cid]
        ks=[r["keff_mean"] for r in cr]; sds=[r["keff_std_dev"] for r in cr]
        between=statistics.stdev(ks); pooled=math.sqrt(sum(x*x for x in sds)/len(sds))
        ranks=[round_ranks[rd.name][cid] for rd in rounds]
        summary.append({"candidate_id":cid,"layout_signature":cid.split("-")[-1],
          "n_runs":len(cr),"seeds":";".join(str(r["seed"]) for r in cr),
          "mean_keff":statistics.mean(ks),"between_run_sample_sd":between,
          "pooled_within_run_reported_sd":pooled,
          "between_to_within_sd_ratio":between/pooled if pooled else None,
          "relative_between_run_sd_percent":between/abs(statistics.mean(ks))*100,
          "mean_descriptive_rank":statistics.mean(ranks),"min_rank":min(ranks),
          "max_rank":max(ranks),"rank_range":max(ranks)-min(ranks)})
    correlations=[]
    for i,left in enumerate(rounds):
        for right in rounds[i+1:]:
            correlations.append({"round_i":left.name,"round_j":right.name,
                "spearman_rho":spearman(round_ranks[left.name],round_ranks[right.name])})
    a.outdir.mkdir(parents=True,exist_ok=True)
    write_csv(a.outdir/"run_level_results.csv",rows)
    write_csv(a.outdir/"repeatability_summary.csv",summary)
    report={"schema_version":"1.0","status":"PASS","upstream_commit":next(iter(commits)),
      "round_count":3,"candidate_count":6,"run_count":18,"unique_seed_count":len(set(seed_list)),
      "unique_statepoint_count":len(set(statepoint_hashes)),"shared_mgxs_sha256":next(iter(set(mgxs_hashes))),
      "settings_profile":list(next(iter(profiles))),"raw_hdf5_audits_all_passed":True,
      "candidate_summary":summary,"round_rank_correlations":correlations,
      "limits":["Three repetitions are too few for strong calibration.","All runs use smoke settings, not benchmark-grade convergence settings.",
        "Rank is by k_eff only; it is descriptive and not an optimization objective.",
        "Monte Carlo uncertainty does not capture model bias or nuclear-data uncertainty.",
        "No QUBO-to-material mapping or reactor-safety claim follows."]}
    (a.outdir/"repeatability_analysis.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    lines=["# C5G7 repeated-seed smoke analysis","",
      f"Rounds: 3; candidate layouts: 6; total runs: 18; unique seeds/statepoints: {len(set(seed_list))}/{len(set(statepoint_hashes))}.",
      f"Upstream commit: {report['upstream_commit']}.",
      f"Common MGXS SHA-256: {report['shared_mgxs_sha256']}.",
      "All 18 raw HDF5 statepoints matched their run manifests and OpenMC API-derived values.","",
      "| Candidate | Runs | Mean k_eff | Between-run SD | Pooled within-run SD | Between/within | Rank range |",
      "|---|---:|---:|---:|---:|---:|---:|"]
    for r in summary:
        lines.append(f"| {r['candidate_id']} | {r['n_runs']} | {r['mean_keff']:.8f} | {r['between_run_sample_sd']:.8f} | {r['pooled_within_run_reported_sd']:.8f} | {r['between_to_within_sd_ratio']:.3f} | {r['rank_range']} |")
    lines += ["","| Round pair | Spearman rho |","|---|---:|"]
    for c in correlations: lines.append(f"| {c['round_i']} vs {c['round_j']} | {c['spearman_rho']:.3f} |")
    lines += ["","These are exploratory smoke-budget repeatability estimates, not benchmark-grade results. With only three runs per layout, between-run SDs and rank correlations are noisy. The k_eff ranking is not a recommendation; predeclare the physical objective and acceptance rules before higher-budget runs."]
    (a.outdir/"REPEATABILITY_ANALYSIS.md").write_text("\n".join(lines)+"\n")
    print(json.dumps({"status":"PASS","rounds":3,"candidates":6,"runs":18,
      "unique_seeds":len(set(seed_list)),"unique_statepoints":len(set(statepoint_hashes)),
      "shared_mgxs_sha256":report["shared_mgxs_sha256"]},indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
