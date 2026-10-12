from pathlib import Path

from scripts.audit_cbpfr_comparison_readiness import analyze


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "results/c5g7_six_layout_confirmation_2026-10-12/run_level_results.csv"
RULE = ROOT / "protocols/cbpfr_physical_decision_rule_TEMPLATE_NOT_APPROVED.json"


def test_saved_campaign_integrity_passes_but_comparison_fails_closed():
    report = analyze(RUNS)
    assert report["run_count"] == 18
    assert all(report["checks"].values())
    assert len(report["descriptive_proxy_holdout"]) == 3
    assert all(row["proxy_selected_layout"] == "MMUU" for row in report["descriptive_proxy_holdout"])
    assert report["comparison_status"] == "BLOCKED_NOT_IDENTIFIABLE"
    assert report["cbpfr_superiority_established"] is False
    assert report["physical_validation_certified"] is False
    assert report["winner_selected"] is False


def test_unapproved_decision_rule_template_cannot_unlock_comparison():
    report = analyze(RUNS, decision_rule_path=RULE)
    assert report["decision_rule_status"] == "INCOMPLETE"
    assert report["comparison_status"] == "BLOCKED_NOT_IDENTIFIABLE"
    assert any("decision-rule file" in blocker.lower() for blocker in report["blockers"])
