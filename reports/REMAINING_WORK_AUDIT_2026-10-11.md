# Remaining-work audit and execution boundary — 2026-10-11

## Purpose

This is the current handoff after consolidating the conversation archives, auditing the actual OpenMC statepoints, repairing CI, and integrating ReactorQ Studio plus the C5G7 layout-study tooling. It separates completed software/evidence work from the scientific work that still cannot be claimed.

## Work completed and verified

- Consolidated and indexed 86 historical project artifacts in `CBPFR_ReactorQ__Archive_2026-10-11.zip` and `archive/conversation-artifacts/CONVERSATION_ARTIFACT_MANIFEST.json`.
- Added `OpenMC_HDF5_Evidence_2026-10-11.zip` to `main`.
- Fixed the OpenMC stdout (k_\mathrm{eff}) parser's doubled-backslash regex and added regression tests.
- Restored strict optimizer experiment-log validation, repeated-ranking statistics, and the CLI.
- Integrated the ReactorQ Studio Streamlit dashboard. Its demo values are explicitly synthetic, and the OpenMC tab is preflight-only.
- Integrated the fail-closed C5G7 benchmark manifest, six-layout UO2/MOX assembly-placement enumerator, upstream source-provenance utility, and isolated case preparation/optional run pipeline.
- Hardened OpenMC preflight to reject malformed XML.
- Added reproducible OpenMC statepoint/tally audit, archive-integrity, settings/log provenance, run inventory, tally summary, and plot utilities.
- OpenMC 0.16.0 read all four archived statepoints successfully. The production (k_\mathrm{eff}) mean and standard deviation matched the transcribed summary. The tally arrays and six mesh-index plots are available from the audit workflow artifact.
- Full software CI passed on Python 3.10, 3.11 and 3.12 on the integration branch: [CI run](https://github.com/thenextw4ng/cb-pfr/actions/runs/38084756074). The post-merge `main` CI is running/should be checked before the next release.
- The OpenMC audit workflow passed on the integration branch: [audit run](https://github.com/thenextw4ng/cb-pfr/actions/runs/38084756095).

## Current scientific status

| Item | Status | Meaning |
|---|---|---|
| CB-PFR ranking software | Implemented; automated tests pass | Software functionality, not reactor validity |
| ReactorQ Studio dashboard | Integrated | Synthetic demo plus OpenMC readiness checks; it does not launch a transport calculation |
| C5G7 six-layout design-space generator | Integrated and tested | Enumerates 6 two-UO2/two-MOX permutations; not itself physical evidence |
| C5G7 transport-case preparation/runner | Integrated and tested with fixtures | Actual upstream preparation/production run still requires a compatible local model/data setup |
| Synthetic benchmark and archived trial data | Present; documented as synthetic | Supports conclusions only under its declared synthetic data-generating process |
| Production C5G7 statepoint scalar | Independently read via OpenMC 0.16.0; recorded mean/SD match | Verifies extraction and provenance, not benchmark acceptance |
| Production mesh and aggregate tallies | Exported and summarized; six plots generated | Descriptive scores and Monte Carlo uncertainty only |
| Three recovered stage34 statepoints | Read successfully, but **not demonstrated independent repetitions** | Colocated settings files are byte-identical, have no explicit seed, and outputs are nearly identical |
| Separate settings files with seeds 481730–481732 | Present, but matching statepoints are absent in those seeded directories | Cannot pair seeded inputs to recovered outputs |
| Six candidates physically evaluated and ranked | Not established | No verified candidate IDs/configuration hashes matched to statepoints |
| Legacy abstract QUBO mapped to C5G7 materials/depletion states | Blocked | No defensible mapping documented |
| CB-PFR physical validation | Not established | Cannot be inferred from successful statepoint parsing or software CI |
| Independent external replication | Not established | GitHub Actions is a reproducible audit workflow, not third-party replication |

## Critical Stage 3–4 finding

The three recovered stage34 statepoints each report 100 batches, 20 inactive batches, 1,000 particles per batch, and 80 active realizations. Their (k_\mathrm{eff}) means span only about (1.55\times10^{-15}), and the largest absolute difference among exported mesh-tally means is about (6.4\times10^{-14}). The colocated settings files share SHA-256 `ec18cf927d20edc3593b01378b7b856e3b66bbf3b5d4d511f385707b4d921baa` and contain no explicit seed. Separate settings files with seeds 481730, 481731, and 481732 have no matching statepoints in those directories. Do not count the recovered trio as independent-seed evidence.

Details: [Stage 3–4 statepoint provenance audit](stage34_statepoint_provenance_audit_2026-10-11.md).

## Remaining scientific work

1. Stage the upstream C5G7 reference source, record the exact commit, and prepare the six case directories with `scripts/run_c5g7_layout_study.py --mode prepare`. Review every generated XML and the canonical arrangement before running transport.
2. Ensure a compatible OpenMC executable, MGXS/cross-section data, and all input files are present in the actual run environment. The committed HDF5 archive does not bundle the full cross-section library.
3. Define stable candidate IDs and save each candidate's exact material layout, settings, model/material/geometry hashes, random seed, log, summary, and statepoint together.
4. Run the six intended candidates with a predeclared common computational budget. For repeatability, run genuinely independent seeds and verify the seed is paired with the statepoint it generated.
5. Predeclare benchmark reference values and acceptance tolerances from the primary C5G7 specification. Distinguish code/model verification from comparing noncanonical design variants.
6. Do not map `fresh / once_burned / twice_burned` to UO2/MOX enrichment categories. Either provide a source-backed depletion/material map or present the six-layout assembly-placement problem as a separate research formulation.
7. Only after candidate identity and physics mapping are resolved, compute physical rankings, sensitivity analyses, and reliability metrics, then update the manuscript from the verified results.

## Release language

Safe: “CB-PFR is an open research prototype with a reproducible synthetic benchmark, an independently audited C5G7/OpenMC baseline statepoint, and a separate C5G7 assembly-placement preparation pipeline. Candidate-level physical evaluation and the legacy-QUBO-to-C5G7 mapping remain unresolved.”

Unsafe without new evidence: “physically validated optimizer,” “validated reactor design,” “six candidates successfully compared,” “independent three-seed confirmation,” or any reactor-safety claim.
