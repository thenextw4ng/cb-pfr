import csv
import json
from pathlib import Path

from scripts.audit_cbpfr_comparison_readiness import analyze


LAYOUTS = ["MMUU", "MUMU", "MUUM", "UMMU", "UMUM", "UUMM"]
FIELDS = [
    "round", "candidate_id", "layout_signature", "seed", "keff_mean", "keff_std_dev",
    "fission_rate_peaking_factor", "statepoint_sha256", "mgxs_sha256",
    "group_structure_audit", "batches", "inactive", "particles_per_batch", "threads",
]


def make_fixture(path: Path) -> Path:
    rows = []
    for round_index, round_id in enumerate((820000, 830000, 840000)):
        for layout_index, layout in enumerate(LAYOUTS):
            rows.append({
                "round": str(round_id), "candidate_id": f"c5g7-2x2-{layout}",
                "layout_signature": layout, "seed": str(round_id + layout_index + 1),
                "keff_mean": "1.14", "keff_std_dev": "0.0001",
                "fission_rate_peaking_factor": str(1.29 + 0.01 * layout_index + 0.0001 * round_index),
                "statepoint_sha256": f"{round_id:06d}{layout_index:02d}".ljust(64, "a"),
                "mgxs_sha256": "b" * 64, "group_structure_audit": "PASS",
                "batches": "7000", "inactive": "500", "particles_per_batch": "10000", "threads": "2",
            })
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_integrity_passes_but_comparison_fails_closed(tmp_path):
    runs = make_fixture(tmp_path / "runs.csv")
    report = analyze(runs)
    assert report["run_count"] == 18
    assert all(report["checks"].values())
    assert len(report["descriptive_proxy_holdout"]) == 3
    assert report["comparison_status"] == "BLOCKED_NOT_IDENTIFIABLE"
    assert report["cbpfr_superiority_established"] is False
    assert report["physical_validation_certified"] is False
    assert report["winner_selected"] is False


def test_unapproved_decision_rule_template_cannot_unlock_comparison(tmp_path):
    runs = make_fixture(tmp_path / "runs.csv")
    rule = tmp_path / "decision_rule.json"
    rule.write_text(json.dumps({"status": "TEMPLATE_NOT_APPROVED", "approved_by": None}), encoding="utf-8")
    report = analyze(runs, decision_rule_path=rule)
    assert report["decision_rule_status"] == "INCOMPLETE"
    assert report["comparison_status"] == "BLOCKED_NOT_IDENTIFIABLE"
    assert any("decision-rule file" in blocker.lower() for blocker in report["blockers"])
