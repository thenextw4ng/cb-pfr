# OpenMC execution and evidence protocol

## Quick-check

The reproducible five-minute workflow is [c5g7-five-minute-quickcheck.yml](../.github/workflows/c5g7-five-minute-quickcheck.yml). The recorded successful run is [Actions run 38112118549](https://github.com/thenextw4ng/cb-pfr/actions/runs/38112118549).

Its execution profile is deliberately small: OpenMC 0.16.0, 20 batches, 5 inactive, 100 particles per batch, one thread, seed base 811011, one candidate. It downloads a pinned public MIT-CRPG benchmark source revision, prepares the corrected seven-group energy boundaries, runs OpenMC, audits the raw statepoint, extracts the assembly fission proxy, and uploads the output folder.

This profile checks that the pipeline executes. It is not a converged benchmark calculation.

## Artifacts and provenance

The Actions artifact contains the statepoint and summary HDF5, input XML and Python builders, logs, study summary, raw-HDF5 audit, and `assembly_fission.json`. Preserve the artifact with the run URL, commit SHA, source commit SHA, artifact digest, and seed. Do not commit large statepoints to Git.

For each independent replicate, retain a distinct seed, statepoint hash, candidate ID, layout signature, input hashes, OpenMC version, batch settings, and result JSON. The updated analysis output records statepoint metadata where available; the replicate aggregator rejects missing or duplicate seed/hash provenance.

## Recommended run modes

- **quick-check:** one small run; checks execution and output integrity only.
- **benchmark:** use a declared high-budget profile and at least three unique seeds for an initial repeatability screen; verify convergence and model identity before acceptance.
- **validation:** compare only like-for-like observables with cited reference data. Return BLOCKED if the reference quantity or model identity is not established.
- **full-run:** execute all six assembly placements with a common compute budget and independent seeds; report every layout rather than selecting a winner without a declared physical objective.

## Runtime and tally interpretation

OpenMC reports batch-statistics estimates for tallies. Mesh bins from the same statepoint must not be treated as independent replicates. For the nonlinear assembly peaking ratio, calculate the ratio within each independent statepoint and estimate between-seed variability across replicate ratios. Report that variability separately from each run's within-run uncertainty and from model/nuclear-data uncertainty.

See [OpenMC's statepoint format](https://docs.openmc.org/en/stable/io_formats/statepoint.html) and [tally statistics documentation](https://docs.openmc.org/en/stable/methods/tallies.html).
