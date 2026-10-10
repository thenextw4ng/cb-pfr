# Remaining-work audit and execution boundary — 2026-10-11

## Purpose

This is a candid handoff of what has been completed in the repository, what can be advanced using the committed artifacts, and what remains blocked by the need to execute or inspect the real local OpenMC environment. It is not a claim that the research is complete.

## Verified repository actions on this branch

- Indexed the recovered conversation archive: `archive/conversation-artifacts/CONVERSATION_ARTIFACT_MANIFEST.json` inventories 86 artifacts.
- Added the 21.7 MB consolidated conversation archive as `CBPFR_ReactorQ__Archive_2026-10-11.zip`.
- Added the separate local HDF5 evidence archive as `OpenMC_HDF5_Evidence_2026-10-11.zip` (1,398,773 bytes).
- Preserved the baseline metadata under `evidence/openmc_local_baseline_2026-10-11/`.
- Added read-only OpenMC statepoint audit and run-inventory scripts.
- Fixed an escaping defect in the OpenMC stdout keff parser. The old raw-string regex used doubled backslashes and would not match ordinary whitespace/digits.
- Added regression tests for decimal values, scientific notation, and malformed OpenMC stdout records.
- Updated handoff text to distinguish “ZIP committed” from “HDF5 values independently audited.”

## Current scientific status

| Item | Status | Meaning |
|---|---|---|
| CB-PFR ranking software and abstract QUBO | Implemented in repository | Software functionality, not reactor validity |
| Synthetic benchmark and archived trial data | Present; documented as synthetic | Supports only conclusions under the declared synthetic data-generating process |
| Conversation archive | Committed to this branch | Historical artifact preservation; older artifacts may be superseded |
| Raw OpenMC evidence ZIP | Committed to this branch | Presence is verified from the repository tree; contents have not been extracted/audited by this integration |
| Reported 20,000-batch C5G7 baseline scalar | Transcribed from terminal output | Must be regenerated from the statepoint audit before being treated as independently verified |
| Six candidate layouts evaluated by OpenMC | Not established | Existing stage34 runs are not yet matched to candidate IDs/configuration hashes |
| Abstract QUBO category to C5G7 material/depletion mapping | Blocked | No defensible mapping is documented |
| CB-PFR physical validation | Not established | Cannot be inferred from C5G7 execution alone |
| Independent external replication | Not established | Local rerun is not third-party replication |

## Next technical sequence

1. Extract `OpenMC_HDF5_Evidence_2026-10-11.zip` in the OpenMC environment and run:
   ```bash
   conda activate openmc-env
   python scripts/audit_openmc_statepoint.py \
     --statepoint "$HOME/C5G7_openmc_production/c5g7_2d_20261011_001910/c5g7-run/2d/statepoint.20000.h5" \
     --outdir results/openmc_local_baseline_2026-10-11
   ```
2. Generate checksums and an inventory for the extracted tree with `scripts/inventory_openmc_runs.py`.
3. Compare machine-derived keff, run settings, tally names, tally dimensions and uncertainty against `result_summary.json`; retain discrepancies rather than overwriting them silently.
4. Recover or regenerate the exact six candidate configuration manifests. A run is candidate evidence only if its configuration, input hashes, log and statepoint are joined by a stable candidate/run ID.
5. Review the C5G7 model/material/geometry changes and benchmark reference before interpreting any candidate-to-candidate difference.
6. Only after the mapping is scientifically defensible, run candidates with a predeclared common computational budget, repeat seeds where applicable, and quantify Monte Carlo uncertainty separately from between-run/configuration variability.
7. The full CI suite passed on Python 3.10, 3.11 and 3.12 after the parser fix and restoration of the experiment-log/repeatability modules and validation CLI: [GitHub Actions run](https://github.com/thenextw4ng/cb-pfr/actions/runs/38083497013). This is software verification, not physical simulation validation.

## Release language

Safe: “CB-PFR is an open research prototype with reproducible synthetic benchmark evidence and a separately recorded C5G7/OpenMC execution baseline; physical CB-PFR validation and the abstract-QUBO-to-C5G7 mapping remain unresolved.”

Unsafe without new evidence: “physically validated optimizer,” “validated reactor design,” “six candidates successfully compared,” or any reactor-safety claim.
