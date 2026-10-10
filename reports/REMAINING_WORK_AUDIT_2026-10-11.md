# Remaining-work audit and execution boundary — 2026-10-11

## Purpose

This report separates completed repository/software work from the scientific gates that still require a defensible candidate-to-physics formulation and independent candidate runs. It is not a claim that the research is complete.

## Work completed and verified

- Consolidated and indexed 86 historical project artifacts in `CBPFR_ReactorQ__Archive_2026-10-11.zip` and `archive/conversation-artifacts/CONVERSATION_ARTIFACT_MANIFEST.json`.
- Added `OpenMC_HDF5_Evidence_2026-10-11.zip` (1,398,773 bytes) to the repository.
- Fixed a doubled-backslash regular-expression bug in the OpenMC stdout (k_\mathrm{eff}) parser and added regression tests.
- Restored the experiment-log validator, repeated-ranking summary, and validation CLI needed by the repository test suite.
- Added OpenMC statepoint/tally audit, ZIP integrity audit, run-input hash/settings audit, tally-summary, plot, and all-run inventory scripts.
- Added a GitHub Actions workflow that installs OpenMC 0.16.0, extracts and reads every archived statepoint, checks the production (k_\mathrm{eff}) scalar against the recorded summary, inventories settings/log hashes, summarizes tally uncertainty, and generates six mesh-index plots.
- The full software CI passed on Python 3.10, 3.11 and 3.12: [CB-PFR CI](https://github.com/thenextw4ng/cb-pfr/actions/runs/38084209681).
- The OpenMC audit workflow passed: [OpenMC evidence audit](https://github.com/thenextw4ng/cb-pfr/actions/runs/38084209709).

## Current scientific status

| Item | Status | Meaning |
|---|---|---|
| CB-PFR ranking software and abstract QUBO | Implemented; CI passes | Software functionality, not reactor validity |
| Synthetic benchmark and archived trial data | Present; documented as synthetic | Supports conclusions only under its declared synthetic data-generating process |
| Conversation archive and raw HDF5 evidence ZIP | Committed to `main`; ZIP integrity checks pass | Historical preservation and reproducible input evidence |
| Production C5G7 statepoint scalar | Independently read through OpenMC 0.16.0; recorded mean/SD match | Verifies scalar extraction, not benchmark validity |
| Production mesh and aggregate tallies | Exported and summarized; six plots generated | Descriptive score distributions and Monte Carlo uncertainty only |
| Three recovered stage34 statepoints | Read successfully, but **not demonstrated independent repetitions** | Colocated settings files are identical and have no explicit seed; tallies/keff are almost identical |
| Separate settings files with seeds 481730–481732 | Present, but corresponding statepoints are absent from those directories in the archive | Cannot pair these seeded inputs with the recovered stage34 outputs |
| Six candidate layouts evaluated and ranked physically | Not established | Candidate IDs/configuration hashes are not matched to the statepoints |
| Abstract QUBO categories mapped to C5G7 materials/depletion states | Blocked | No defensible mapping is documented |
| CB-PFR physical validation | Not established | Cannot be inferred from successful C5G7 execution alone |
| Independent external replication | Not established | GitHub Actions audit is a reproducible software workflow, not third-party replication |

## Most important new finding

The three recovered stage34 statepoints each report 100 batches, 20 inactive batches, 1,000 particles per batch, and 80 active realizations. Their (k_\mathrm{eff}) means differ by only about (1.55\times10^{-15}); the largest absolute difference among their exported mesh-tally means is about (6.4\times10^{-14}). Their colocated `settings.xml` files share SHA-256:

`ec18cf927d20edc3593b01378b7b856e3b66bbf3b5d4d511f385707b4d921baa`

and contain no explicit seed. Meanwhile, separate `stage34_runs/run_01-03/settings.xml` files specify seeds 481730, 481731, and 481732 but have no matching statepoints in the archive. **Do not treat the recovered trio as independent seeded runs.** See [Stage 3–4 statepoint provenance audit](stage34_statepoint_provenance_audit_2026-10-11.md).

## Remaining research gates

1. Recover or regenerate the exact six candidate configuration manifests and assign stable candidate IDs.
2. Decide on a scientifically defensible formulation: the existing abstract `fresh / once_burned / twice_burned` QUBO must not be silently mapped to C5G7 UO₂/MOX categories. If using C5G7 assembly-placement variants, state clearly that this is a separate formulation and document why each layout is physically meaningful.
3. Run each candidate from a per-run directory containing its exact input XMLs, model/material/geometry hashes, seed, log, summary, and statepoint. Confirm that the five fixed reflector positions are unchanged if that is part of the design contract.
4. For repeatability, run genuinely independent seeds with matched settings and verify that each statepoint is produced by its paired settings file.
5. Predeclare benchmark reference values and acceptance tolerances before comparing (k_\mathrm{eff}), flux, or fission tallies. Keep Monte Carlo uncertainty separate from model bias and nuclear-data uncertainty.
6. Only after the mapping and candidate identity gates pass, compute candidate rankings, sensitivity analyses, and reliability statistics. Do not use the recovered stage34 trio as independent-run evidence.
7. Update the manuscript to match these evidence boundaries and avoid claims of physical validation or reactor safety.

## Release language

Safe: “CB-PFR is an open research prototype with a reproducible synthetic benchmark, a machine-audited C5G7/OpenMC baseline, and an explicit unresolved candidate-to-physics mapping.”

Unsafe without new evidence: “physically validated optimizer,” “validated reactor design,” “six candidates successfully compared,” “independent three-seed confirmation,” or any reactor-safety claim.
