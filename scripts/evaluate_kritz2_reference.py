#!/usr/bin/env python3
"""Compare an OpenMC k-eff estimate with a published KRITZ-2 participant mean.

This utility evaluates a supplied calculation; it does not run OpenMC and does
not turn a pin-cell/infinite-lattice result into a finite-core experimental
validation. Reference spreads are participant-to-participant spreads, not
necessarily experimental measurement uncertainties. The combined-z score is
therefore a diagnostic, not a formal validation statistic.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

REFERENCE = {
    # OECD/NEA NEA/NSC/DOC(2005)24 values transcribed in the repository's
    # KRITZ-2 reference manifest. Spread is across participant solutions.
    "2:1-cold": {"keff": 0.99463, "participant_spread": 0.00330, "temperature_C": 19.7, "fuel": "UO2"},
    "2:1-hot": {"keff": 0.99290, "participant_spread": 0.00346, "temperature_C": 248.5, "fuel": "UO2"},
    "2:13-cold": {"keff": 0.99736, "participant_spread": 0.00204, "temperature_C": 22.1, "fuel": "UO2"},
    "2:13-hot": {"keff": 0.99605, "participant_spread": 0.00280, "temperature_C": 243.0, "fuel": "UO2"},
    "2:19-cold": {"keff": 0.99908, "participant_spread": None, "temperature_C": 21.1, "fuel": "MOX"},
    "2:19-hot": {"keff": 0.99822, "participant_spread": None, "temperature_C": 235.9, "fuel": "MOX"},
}

def evaluate(config: str, calculated_keff: float, calculation_std: float,
             model_scope: str = "unspecified") -> dict:
    if config not in REFERENCE:
        raise ValueError(f"unknown configuration {config!r}; choose from {', '.join(REFERENCE)}")
    if not math.isfinite(calculated_keff):
        raise ValueError("calculated_keff must be finite")
    if not math.isfinite(calculation_std) or calculation_std < 0:
        raise ValueError("calculation_std must be finite and non-negative")
    ref = REFERENCE[config]
    delta = calculated_keff - ref["keff"]
    spread = ref["participant_spread"]
    if spread is None:
        combined = None
        normalized = None
        diagnostic = "REFERENCE_SPREAD_UNAVAILABLE"
    else:
        # This is only a descriptive combination: participant spread is not
        # assumed to be an experimental standard uncertainty.
        combined = math.hypot(calculation_std, spread)
        normalized = abs(delta) / combined if combined > 0 else (0.0 if delta == 0 else math.inf)
        diagnostic = "WITHIN_2_COMBINED_SPREADS" if normalized <= 2 else "OUTSIDE_2_COMBINED_SPREADS"
    return {
        "schema_version": "1.0",
        "benchmark": "KRITZ-2",
        "reference_source": "OECD/NEA NEA/NSC/DOC(2005)24 (2006)",
        "configuration": config,
        "fuel": ref["fuel"],
        "temperature_C": ref["temperature_C"],
        "reference_participant_mean_keff": ref["keff"],
        "reference_participant_spread": spread,
        "calculated_keff": calculated_keff,
        "calculation_standard_deviation": calculation_std,
        "delta_keff_calculated_minus_reference": delta,
        "delta_pcm": delta * 100000.0,
        "descriptive_combined_spread": combined,
        "absolute_delta_over_combined_spread": normalized,
        "diagnostic": diagnostic,
        "model_scope": model_scope,
        "validation_status": "NOT_ESTABLISHED",
        "limitations": [
            "A numerical comparison is not itself proof of experimental validation.",
            "Participant-to-participant spread is not automatically an experimental measurement uncertainty.",
            "A reflective pin-cell/infinite-lattice model is not comparable to finite-core k-effective as though they were the same model scope.",
            "Model geometry, material composition, temperature, boron, boundary/leakage treatment, nuclear-data provenance, convergence, and reference observable must be independently checked."
        ],
    }

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", choices=sorted(REFERENCE), required=True)
    parser.add_argument("--keff", type=float, required=True, help="OpenMC combined k-eff estimate")
    parser.add_argument("--std", type=float, required=True, help="OpenMC standard deviation of k-eff")
    parser.add_argument("--model-scope", default="unspecified", help="e.g. reflective-pin-cell or finite-core")
    parser.add_argument("--out", type=Path, default=Path("kritz2_comparison.json"))
    args = parser.parse_args()
    result = evaluate(args.config, args.keff, args.std, args.model_scope)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
