#!/usr/bin/env python3
"""Fail-closed readiness audit for fair CB-PFR vs QUBO-only comparison.

Audits saved run-level evidence; never launches OpenMC or certifies physics.
"""
from __future__ import annotations
import argparse, csv, hashlib, json
from collections import defaultdict
from pathlib import Path

REQUIRED = {
    "round", "candidate_id", "layout_signature", "seed", "keff_mean", "keff_std_dev",
    "fission_rate_peaking_factor", "statepoint_sha256", "mgxs_sha256",
    "group_structure_audit", "batches", "inactive", "particles_per_batch", "threads"
}
LAYOUTS = {"MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def analyze(csv_path: Path, qubo_scores_path: Path | None = None,
            decision_rule_path: Path | None = None) -> dict:
    rows = list(csv.DictReader(csv_path.read_text(encoding="utf-8-sig").splitlines()))
    columns = set(rows[0]) if rows else set()
    missing = sorted(REQUIRED - columns)
    checks = {
        "nonempty_csv": bool(rows),
        "required_columns_present": not missing,
        "exactly_18_runs": len(rows) == 18,
        "six_expected_layouts": {r.get("layout_signature") for r in rows} == LAYOUTS,
        "three_seed_rounds": len({r.get("round") for r in rows}) == 3,
        "unique_seed_ids": len({r.get("seed") for r in rows}) == len(rows),
        "unique_statepoint_hashes": len({r.get("statepoint_sha256") for r in rows}) == len(rows),
        "single_mgxs_hash": len({r.get("mgxs_sha256") for r in rows}) == 1,
        "group_structure_pass": bool(rows) and all(r.get("group_structure_audit") == "PASS" for r in rows),
        "common_run_settings": len({(r.get("batches"), r.get("inactive"), r.get("particles_per_batch"), r.get("threads")) for r in rows}) == 1,
    }
    blockers = [f"Evidence-integrity gate failed: {k}" for k, ok in checks.items() if not ok]
    if missing:
        blockers.append("Missing columns: " + ", ".join(missing))

    # Descriptive holdout uses the fission-rate proxy only; it is not a validated physical objective.
    grouped = defaultdict(dict)
    folds = []
    if not missing and rows:
        try:
            for row in rows:
                grouped[row["round"]][row["layout_signature"]] = float(row["fission_rate_peaking_factor"])
        except (ValueError, KeyError):
            blockers.append("Non-numeric or missing fission-rate proxy")
        rounds = sorted(grouped)
        if len(rounds) == 3 and all(set(grouped[r]) == LAYOUTS for r in rounds):
            for heldout in rounds:
                train = [r for r in rounds if r != heldout]
                means = {layout: sum(grouped[r][layout] for r in train) / len(train) for layout in sorted(LAYOUTS)}
                selected = min(means, key=lambda x: (means[x], x))
                best = min(grouped[heldout], key=lambda x: (grouped[heldout][x], x))
                folds.append({
                    "held_out_round": heldout, "training_rounds": train,
                    "proxy_selected_layout": selected,
                    "held_out_proxy_of_selected": grouped[heldout][selected],
                    "held_out_proxy_minimum_layout": best,
                    "held_out_proxy_minimum": grouped[heldout][best],
                    "descriptive_proxy_regret": grouped[heldout][selected] - grouped[heldout][best],
                    "same_layout_as_held_out_proxy_minimum": selected == best,
                })
        else:
            blockers.append("Cannot form complete three-fold holdout; every round must contain all six layouts")

    qubo_status = "MISSING"
    if qubo_scores_path and qubo_scores_path.exists():
        try:
            qrows = list(csv.DictReader(qubo_scores_path.open(encoding="utf-8-sig", newline="")))
            required_q = {"layout_signature", "qubo_score", "score_stage"}
            valid = bool(qrows) and required_q <= set(qrows[0]) and {r["layout_signature"] for r in qrows} == LAYOUTS
            valid = valid and all(r["score_stage"].strip().lower() in {"pre_physics", "pre-physics"} for r in qrows)
            if not valid:
                qubo_status = "INVALID_OR_INCOMPLETE"
                blockers.append("QUBO score file lacks all six layouts, required columns, or pre-physics provenance")
            else:
                scores = [float(r["qubo_score"]) for r in qrows]
                qubo_status = "PRESENT_REQUIRES_OBJECTIVE_PROVENANCE_REVIEW"
                if max(scores) - min(scores) <= 1e-12:
                    blockers.append("Pre-physics QUBO scores tie across all feasible layouts; QUBO-only cannot rank them")
        except (OSError, ValueError, KeyError):
            qubo_status = "INVALID_OR_INCOMPLETE"
            blockers.append("QUBO score file is unreadable or has non-numeric scores")
    else:
        blockers.append("No comparable pre-physics QUBO score table for all six layouts")

    rule_status = "MISSING"
    if decision_rule_path and decision_rule_path.exists():
        try:
            rule = json.loads(decision_rule_path.read_text(encoding="utf-8"))
            keys = {"version", "approved_by", "approved_at", "physical_metrics", "acceptance_criteria",
                    "uncertainty_method", "selection_objective", "heldout_protocol"}
            if keys <= set(rule) and all(rule.get(k) for k in keys):
                rule_status = "PRESENT_REQUIRES_HUMAN_REVIEW"
            else:
                rule_status = "INCOMPLETE"
                blockers.append("Decision-rule file is not fully specified and approved")
        except (OSError, json.JSONDecodeError):
            rule_status = "INVALID"
            blockers.append("Decision-rule file is invalid")
    else:
        blockers.append("No approved, predeclared physical acceptance-rule file")

    blockers += [
        "Independent primary C5G7 model/tally sign-off is not recorded in this input package",
        "Three seed rounds are exploratory only; prospective held-out evaluation is needed for a confirmatory superiority claim",
        "Fission-rate peaking factor is a relative proxy, not absolute power or an approved safety criterion",
    ]
    blockers = list(dict.fromkeys(blockers))
    return {
        "schema_version": "cbpfr.comparison-readiness.v1",
        "input_csv": str(csv_path), "input_csv_sha256": sha256(csv_path),
        "run_count": len(rows), "checks": checks, "missing_columns": missing,
        "descriptive_proxy_holdout": folds, "qubo_score_table_status": qubo_status,
        "decision_rule_status": rule_status,
        "comparison_status": "BLOCKED_NOT_IDENTIFIABLE" if blockers else "READY_FOR_REVIEW_NOT_AUTOMATICALLY_VALIDATED",
        "cbpfr_superiority_established": False, "physical_validation_certified": False,
        "winner_selected": False, "blockers": blockers,
        "interpretation": (
            "This audit confirms data shape/integrity and reports exploratory proxy ranking only. "
            "It cannot certify physical validity or superiority. The feasible material-placement QUBO "
            "uses A*(sum(y_i)-2)^2, so every exactly-two-MOX layout ties; it has no physical ranking objective. "
            "Do not compare post-physics selector energy as if it were pre-physics QUBO performance."
        ),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-level-csv", required=True, type=Path)
    p.add_argument("--qubo-scores-csv", type=Path)
    p.add_argument("--decision-rule-json", type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    result = analyze(a.run_level_csv, a.qubo_scores_csv, a.decision_rule_json)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"comparison_status": result["comparison_status"], "run_count": result["run_count"],
                      "folds": len(result["descriptive_proxy_holdout"]), "blocker_count": len(result["blockers"]),
                      "out": str(a.out)}, indent=2))
    return 0 if result["comparison_status"] == "READY_FOR_REVIEW_NOT_AUTOMATICALLY_VALIDATED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
