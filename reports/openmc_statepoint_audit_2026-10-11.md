# OpenMC statepoint audit — 2026-10-11

## Verification result

**OpenMC Python API audit: passed.** The committed `OpenMC_HDF5_Evidence_2026-10-11.zip` was extracted in GitHub Actions, and `openmc.StatePoint` successfully read the production `statepoint.20000.h5` using OpenMC 0.16.0. The machine-derived mean and standard deviation of (k_\mathrm{eff}) matched the transcribed `result_summary.json` within the workflow's declared tolerance.

- Workflow: [OpenMC evidence audit](https://github.com/thenextw4ng/cb-pfr/actions/runs/38083671809)
- Machine-derived audit artifact: `openmc-statepoint-audit` attached to that workflow run.
- Statepoint read success: `true`
- OpenMC version: `0.16.0`
- Run mode: `eigenvalue`
- Batches: 20,000; inactive batches: 500; particles per batch: 10,000; active realizations: 19,500.

## Scalar eigenvalue result

| Quantity | Independently read from statepoint |
|---|---:|
| (k_\mathrm{eff}) mean | 1.186394144702191 |
| Reported standard deviation | 0.000056113408647969484 |
| Relative standard deviation | 0.0047297% |

The API-derived values match the previously transcribed scalar. This verifies the scalar extraction and consistency of the record; it does **not** by itself validate the benchmark model, nuclear data, geometry, or QUBO-to-physics mapping.

## Tally inventory

Two tallies were read through OpenMC's Python API. All reported tally means and standard deviations were finite.

| Tally | Filters | Score array shape | Scores |
|---|---|---|---|
| Tally 1 | 51 × 51 × 1 mesh filter | 2601 × 1 × 3 | flux, fission, nu-fission |
| Tally 2 | No filters; one aggregate bin | 1 × 1 × 3 | flux, fission, nu-fission |

Mesh bounds reported by the API were ([-32.13,-32.13,-10^{50}]) to ([32.13,32.13,10^{50}]), with mesh width ([1.26,1.26,2\times10^{50}]). The audit exports mesh-bin indices and does not assume that a bin index is a material identity or a fuel-assembly label.

### Mesh tally descriptive statistics

The following are descriptive summaries of the 2,601 mesh-bin means. They preserve the values and score names as read from the statepoint; they do not imply physical power in watts.

| Score | Positive bins | Zero bins | Mean across bins | Median | 95th percentile | Maximum |
|---|---:|---:|---:|---:|---:|---:|
| Flux | 2,601 | 0 | 0.01536992 | 0.00725697 | 0.06029649 | 0.07350854 |
| Fission | 1,060 | 1,541 | 0.00017394 | 0 | 0.00083385 | 0.00107202 |
| Nu-fission | 1,060 | 1,541 | 0.00045609 | 0 | 0.00204733 | 0.00262927 |

### Relative Monte Carlo uncertainty across positive mesh bins

Relative uncertainty here means tally standard deviation divided by its mean for bins with positive means. It is not a confidence interval for model bias.

| Score | Median relative SD | 95th percentile | Maximum |
|---|---:|---:|---:|
| Flux | 0.1803% | 1.7378% | 7.3943% |
| Fission | 0.2280% | 0.3211% | 0.4157% |
| Nu-fission | 0.2271% | 0.3208% | 0.4133% |

The larger maximum relative uncertainty for flux occurs in low-mean bins; relative ratios become large when the denominator is small. It should not be read as a 7.4% uncertainty across the whole mesh.

### Aggregate tally (Tally 2)

| Score | Mean | Standard deviation |
|---|---:|---:|
| Flux | 39.97716609233386 | 0.0017833759169101 |
| Fission | 0.4524277680376544 | 0.00004212618699552408 |
| Nu-fission | 1.186294998565931 | 0.0001085100433054 |

The aggregate `nu-fission` tally is a tally score, **not** the eigenvalue estimate. Do not substitute it for (k_\mathrm{eff}).

## What is established—and what is not

Established:
1. The production statepoint exists in the committed evidence ZIP and passes ZIP CRC validation.
2. OpenMC 0.16.0 successfully reads it.
3. The API-derived (k_\mathrm{eff}) mean and standard deviation match the transcribed summary.
4. Both tallies, their score names, array shapes, mesh dimensions, and finite-value checks have been exported.

Not established:
1. That the C5G7 model reproduces a benchmark reference within a predeclared acceptance criterion.
2. That zero mesh scores identify reflectors, non-fuel regions, or any particular physical material.
3. That these flux/fission/nu-fission scores are absolute power in watts.
4. That any of the six candidate layouts has been correctly matched to a statepoint.
5. That the abstract QUBO states `fresh / once_burned / twice_burned` map defensibly to C5G7 material/depletion states.
6. That CB-PFR has been physically validated or supports reactor-safety claims.

## Reproduction

The workflow extracts the archived statepoint, runs `scripts/audit_openmc_statepoint.py`, compares the machine-derived eigenvalue summary with `evidence/openmc_local_baseline_2026-10-11/result_summary.json`, and preserves `statepoint_audit.json` plus `tally_values_flat.csv` as a workflow artifact. `scripts/summarize_openmc_tallies.py` generates a score-level descriptive summary from those machine-derived files.
