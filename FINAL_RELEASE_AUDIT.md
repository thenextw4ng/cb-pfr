# Final Release Audit

## Release status

This repository is a transparent research/software release of CB-PFR. It is **not** a claim of a fully self-contained, end-to-end reproducible 1,000-trial computational release.

## Verified

- Core CB-PFR ranking implementation is present.
- Abstract QUBO construction and exact enumeration are present.
- Smoke tests pass locally: 3/3.
- Synthetic trial-level result artifacts are preserved.
- Recorded-result audit logic is preserved.
- MC/DC C5G7 execution evidence is documented separately.

## Not claimed

- Physical validation of CB-PFR.
- Physical CB-PFR validation.
- Reactor-safety validation.
- Universal superiority.
- A defensible QUBO-to-C5G7 mapping.

## Reproduction boundary

The historical runner expects experiment utilities and a toy-core configuration that are not part of the supplied workspace. The repository therefore distinguishes recorded artifact auditing from independent rerunning.

## Physical boundary

The seven-position QUBO uses abstract fresh/once-burned/twice-burned labels. These are not silently converted into C5G7 UO2/MOX material states. The mapping audit status is:

NO_DEFENSIBLE_MAPPING_FOUND

## Current archival artifact gap

The original workspace still contains the full `per_seed_results.csv` and compiled paper PDF. They are tracked in Issue #9 for synchronization into the public GitHub release because the current GitHub connector cannot directly transfer local binary/large artifacts into the repository. Their SHA-256 identities are recorded in the release notes rather than replaced with placeholders.

## Next research gates

1. Reconstruct the missing experiment utilities and toy-core configuration.
2. Make the benchmark turnkey in a clean environment.
3. Add broader sensitivity and calibration studies.
4. Define a defensible physical benchmark and mapping.
5. Obtain independent external runs and downstream users.
