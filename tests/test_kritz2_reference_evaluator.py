import math
import pytest

from scripts.evaluate_kritz2_reference import evaluate

def test_comparison_records_delta_in_pcm_and_does_not_claim_validation():
    result = evaluate("2:1-cold", 0.99500, 0.00050, "reflective-pin-cell")
    assert result["delta_pcm"] == pytest.approx(37.0)
    assert result["validation_status"] == "NOT_ESTABLISHED"
    assert "finite-core" in result["limitations"][2]

def test_missing_mox_reference_spread_is_not_invented():
    result = evaluate("2:19-cold", 0.9990, 0.0005)
    assert result["reference_participant_spread"] is None
    assert result["diagnostic"] == "REFERENCE_SPREAD_UNAVAILABLE"
    assert result["absolute_delta_over_combined_spread"] is None

@pytest.mark.parametrize("keff,std", [(float("nan"), 0.001), (1.0, -0.1), (1.0, float("inf"))])
def test_invalid_inputs_rejected(keff, std):
    with pytest.raises(ValueError):
        evaluate("2:1-cold", keff, std)
