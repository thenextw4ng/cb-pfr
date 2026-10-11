# KRITZ-2 low-compute validation gate

**Status: NOT VALIDATED — reproducible comparison utility added; a matching finite-core run remains outstanding.**

## Why this gate exists

The OECD/NEA KRITZ-2 benchmark report describes critical lattices of UO2 and MOX fuel rods in light water, at room and elevated temperatures. The repository's discovered public OpenMC example is a *single reflective pin cell*, i.e. an infinite-lattice calculation. It is useful for a lattice-physics check, but it is not a finite-core model and must not be presented as direct reproduction of the experiment's core-level k-effective.

Reference: OECD/NEA, *Benchmark on the KRITZ-2 LEU and MOX Critical Experiments*, NEA/NSC/DOC(2005)24 (2006), https://oecd-nea.org/jcms/pl_18320/benchmark-on-the-kritz-2-leu-and-mox-critical-experiments-final-report

## What was added

- `scripts/evaluate_kritz2_reference.py`: deterministic, low-compute evaluator for a supplied OpenMC k-eff estimate and standard deviation.
- `tests/test_kritz2_reference_evaluator.py`: checks arithmetic, missing-reference-spread handling, invalid inputs, and conservative status labels.
- The evaluator emits JSON with delta-k, pcm, a descriptive comparison against participant spread when available, and an explicit `validation_status: NOT_ESTABLISHED` field.

## Reference values

The following values are participant-solution means/spreads transcribed from the repository's KRITZ-2 benchmark reference configuration. These spreads are not automatically experimental measurement uncertainties.

| Configuration | Fuel | Temperature (C) | Participant mean k-eff | Participant spread |
|---|---:|---:|---:|---:|
| 2:1-cold | UO2 | 19.7 | 0.99463 | 0.00330 |
| 2:1-hot | UO2 | 248.5 | 0.99290 | 0.00346 |
| 2:13-cold | UO2 | 22.1 | 0.99736 | 0.00204 |
| 2:13-hot | UO2 | 243.0 | 0.99605 | 0.00280 |
| 2:19-cold | MOX | 21.1 | 0.99908 | Not reported in this summary |
| 2:19-hot | MOX | 235.9 | 0.99822 | Not reported in this summary |

## Run the evaluator

After running a model and extracting its combined k-eff mean and standard deviation:

```bash
python scripts/evaluate_kritz2_reference.py \
  --config 2:1-cold \
  --keff 0.99500 \
  --std 0.00050 \
  --model-scope reflective-pin-cell \
  --out results/kritz2_comparison.json
```

The numbers in this example are **illustrative placeholders**, not simulation results. Do not cite them as measured or computed evidence.

## Minimum criteria before claiming experimental validation

1. Freeze one configuration and the exact reference observable.
2. Reconstruct the benchmark's geometry, material/isotopic composition, temperature, moderator density/boron, water level/leakage treatment, and relevant boundary conditions from the official specification.
3. Record nuclear-data library, OpenMC version, input files, seeds, particle/batch/inactive counts, and statepoint checksum.
4. Demonstrate source convergence and statistical precision; repeat with independent seeds when practical.
5. Compare the same physical observable and model scope; report delta-k in pcm and uncertainty treatment.
6. Predefine acceptance criteria and report pass/fail/inconclusive without changing thresholds after seeing results.
7. Only then promote the status from `NOT VALIDATED`; even a KRITZ-2 pass validates that benchmark/model path, not the QUBO-to-C5G7 mapping or CB-PFR's claimed physical effectiveness.

## Project-level conclusion

This is an auditable validation *gate* and result-analysis helper, not a completed physical validation. The current evidence still supports software/algorithmic-method claims and exploratory computational results with caveats. It does not yet support a claim that CB-PFR has been physically validated against reactor experiments.
