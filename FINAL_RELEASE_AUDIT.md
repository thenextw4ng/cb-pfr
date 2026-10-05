# Final Release Audit

## Release status

This repository is a transparent research/software release of CB-PFR. The synthetic mathematical benchmark is now independently reproducible from the released source and configuration. Physical CB-PFR validation remains unestablished.

## Verified

- Core CB-PFR ranking implementation is present.
- Abstract QUBO construction and exact enumeration are present.
- Expanded automated tests are present.
- GitHub Actions has produced successful test runs on the repository.
- The frozen 1,000-trial synthetic generator is present.
- The exact seven-position benchmark configuration is present.
- Independent reproduction matches the preserved archival experiment on all 4,000 method/trial rows for substantive experiment columns.
- Recorded-result statistical audit logic is preserved.
- MC/DC C5G7 execution evidence is documented separately.

## Evidence taxonomy

- Independently reproduced: the 1,000-trial synthetic software/protocol experiment.
- Recorded-result artifact: the preserved archival per_seed_results.csv.
- Recorded execution evidence: MC/DC C5G7 simulator runs.
- Physically validated: not established.

## Not claimed

- Physical validation of CB-PFR.
- Reactor-safety validation.
- Universal superiority.
- A defensible QUBO-to-C5G7 mapping.
- Transfer of synthetic uncertainty calibration to a physical simulator.

## Reproducibility boundary

The synthetic benchmark uses a declared data-generating process with known standard errors. Its successful rerun verifies software and protocol reproducibility under that model. It does not prove that the uncertainty model is appropriate for MC/DC, OpenMC, reactor physics, or any real engineering system.

## Physical boundary

The seven-position QUBO uses abstract fresh, once_burned, and twice_burned labels. These are not silently converted into C5G7 UO2/MOX material states. The mapping audit status is:

NO_DEFENSIBLE_MAPPING_FOUND

The physical simulator report is therefore execution evidence, not CB-PFR physical validation.

## Current archival artifact gap

The original workspace still contains the full per_seed_results.csv and compiled paper PDF. They are tracked in Issue #9 for synchronization into the public GitHub release because the current GitHub connector cannot directly transfer local large/binary artifacts into the repository. Their SHA-256 identities are recorded separately; no placeholder has been substituted.

Known artifact hashes:
- per_seed_results.csv: f7fb629fa182778645c41dcbc20f063599b41e09d428ea8204d4af10855e2133
- CB-PFR_Methodological_Working_Paper.pdf: 89e786d529ca3131e0182fcaad315dd4332491aa51253f936072cfda37bd5d96
- paper/source/main.tex: c0369fd420cba0b9c205503bee03841cd6bcdf082ba35838ad7ef7b90290a56f

## Next research gates

1. Synchronize the archival CSV and compiled paper into the public release/archive.
2. Run the benchmark in a clean CI environment and retain the generated artifact/checksum.
3. Add broader uncertainty calibration and sensitivity studies.
4. Define a defensible physical benchmark and mapping.
5. Obtain independent external runs and downstream users.
