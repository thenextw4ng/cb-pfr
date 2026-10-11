# Remaining-work audit and execution boundary — 2026-10-11

## Purpose

This is the current handoff after consolidating the conversation archives, auditing the actual OpenMC statepoints, repairing CI, and integrating ReactorQ Studio plus the C5G7 layout-study tooling. It separates completed software/evidence work from the scientific work that still cannot be claimed.

## Critical correction — standard C5G7 energy-group structure

A follow-up review on 2026-10-11 found that the upstream `materials.py` used `np.logspace(-5, 7, 8)`, which does not match the standard C5G7 seven-group boundaries `[1e-5, 0.0635, 10, 100, 1000, 500000, 1000000, 20000000]` eV. The previous endpoint-only normalization and byte-identical MGXS comparisons did not fix or detect the interior-boundary mismatch. Therefore the historical production/smoke scalar comparison with k_eff=1.18655 is withdrawn as benchmark evidence, and all earlier smoke results are retained only as pipeline/provenance evidence. The corrected runner now replaces the complete boundary list and audits the generated MGXS root attribute before transport. Corrected high-budget runs and primary-specification review are required.

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
- Added a separate raw-HDF5 statepoint parser to CI. It reads `c5g7-run/2d/statepoint.20000.h5` directly from the committed ZIP and passed 10/10 metadata, eigenvalue, mesh-dimension, and score checks on Python 3.10, 3.11, and 3.12: [raw-HDF5 audit run](https://github.com/thenextw4ng/cb-pfr/actions/runs/38096943383). Statepoint SHA-256: `0d76dc1a14a2b74a388c01883f01e5c3095480d53eee885910ca2a0c57e6b882`.
- Ran six low-budget C5G7 2×2 assembly-placement smoke tests in OpenMC 0.16.0 (100 batches, 10 inactive, 1,000 particles/batch; explicit seeds 620000–620005). A follow-up study completed 18 runs across three seed rounds (620000, 630000, 640000), with 336/336 raw-HDF5 checks passing; see `reports/c5g7_repeatability_smoke_2026-10-11.md` and the [repeatability workflow](https://github.com/thenextw4ng/cb-pfr/actions/runs/38097472734). All six completed; the shared MGXS hash was unchanged. A separate raw-HDF5 audit passed 112/112 checks across the six statepoints; the compact audit is committed as `results/c5g7_layout_smoke_2026-10-10/raw_hdf5_audit_summary.json`, with the [full audit run](https://github.com/thenextw4ng/cb-pfr/actions/runs/38097364817). Candidate CSV, pairwise summary, run manifest, and scientific limitations are committed under `results/c5g7_layout_smoke_2026-10-10/` and `reports/c5g7_smoke_run_2026-10-10.md`; full statepoints/logs remain in the [workflow artifact](https://github.com/thenextw4ng/cb-pfr/actions/runs/38085586809). These are smoke tests only, not benchmark-grade ranking or same-layout repeatability evidence.
- Full software CI passed on Python 3.10, 3.11 and 3.12 on the integration branch: [CI run](https://github.com/thenextw4ng/cb-pfr/actions/runs/38084756074). The post-merge `main` CI is running/should be checked before the next release.
- The OpenMC audit workflow passed on the integration branch: [audit run](https://github.com/thenextw4ng/cb-pfr/actions/runs/38084756095).

## Current scientific status

| Item | Status | Meaning |
|---|---|---|
| CB-PFR ranking software | Implemented; automated tests pass | Software functionality, not reactor validity |
| ReactorQ Studio dashboard | Integrated | Synthetic demo plus OpenMC readiness checks; it does not launch a transport calculation |
| C5G7 six-layout design-space generator | Integrated and tested | Enumerates 6 two-UO2/two-MOX permutations; not itself physical evidence |
| C5G7 transport-case preparation/runner | Six isolated cases prepared and six low-budget smoke runs completed against pinned upstream commit `ba41bee54320ada0b4ac39a0dd2ca3c1d090a450` | [Preparation artifact](https://github.com/thenextw4ng/cb-pfr/actions/runs/38084994157); [smoke-run artifact](https://github.com/thenextw4ng/cb-pfr/actions/runs/38085586809). Not benchmark-grade. |
| Synthetic benchmark and archived trial data | Present; documented as synthetic | Supports conclusions only under its declared synthetic data-generating process |
| Production C5G7 statepoint scalar | Independently read via OpenMC 0.16.0 and separately checked from raw HDF5; 10/10 metadata/scalar/tally checks pass | Verifies extraction and consistency, not benchmark acceptance |
| Production mesh and aggregate tallies | Exported and summarized; six plots generated | Descriptive scores and Monte Carlo uncertainty only |
| Three recovered stage34 statepoints | Read successfully, but **not demonstrated independent repetitions** | Colocated settings files are byte-identical, have no explicit seed, and outputs are nearly identical |
| Separate settings files with seeds 481730–481732 | Present, but matching statepoints are absent in those seeded directories | Cannot pair seeded inputs to recovered outputs |
| Six-layout smoke results | Completed, one low-budget run per layout, followed by three seeds/layout (18 runs total) | Explicit IDs/seeds/hashes recorded; 336/336 raw-HDF5 checks pass; descriptive only, not benchmark-grade |
| Six candidates benchmark-grade evaluated and ranked | Not established | Common high-fidelity budget, repeated independent seeds, and predeclared objective/acceptance protocol still missing |
| Legacy abstract QUBO mapped to C5G7 materials/depletion states | Blocked | No defensible mapping documented |
| CB-PFR physical validation | Not established | Cannot be inferred from successful statepoint parsing or software CI |
| Independent external replication | Not established | GitHub Actions is a reproducible audit workflow, not third-party replication |

## Critical Stage 3–4 finding

The three recovered stage34 statepoints each report 100 batches, 20 inactive batches, 1,000 particles per batch, and 80 active realizations. Their (k_\mathrm{eff}) means span only about (1.55\times10^{-15}), and the largest absolute difference among exported mesh-tally means is about (6.4\times10^{-14}). The colocated settings files share SHA-256 `ec18cf927d20edc3593b01378b7b856e3b66bbf3b5d4d511f385707b4d921baa` and contain no explicit seed. Separate settings files with seeds 481730, 481731, and 481732 have no matching statepoints in those directories. Do not count the recovered trio as independent-seed evidence.

Details: [Stage 3–4 statepoint provenance audit](stage34_statepoint_provenance_audit_2026-10-11.md).

## Remaining scientific work

1. Review the six smoke-run input cases and hashes from [the smoke workflow artifact](https://github.com/thenextw4ng/cb-pfr/actions/runs/38085586809), with special attention to the canonical production-vs-smoke materials XML difference. The source revision is pinned in `config/benchmarks/c5g7_2x2_design_space.json`.
2. Ensure a compatible OpenMC executable, MGXS/cross-section data, and all input files are present in the actual run environment. The committed HDF5 archive does not bundle the full cross-section library.
3. Define stable candidate IDs and save each candidate's exact material layout, settings, model/material/geometry hashes, random seed, log, summary, and statepoint together.
4. Increase the common computational budget for the six layouts. Three independent seeds per layout now exist only at smoke settings; repeat at a benchmark-grade budget and verify each seed is paired with its statepoint.
5. Predeclare benchmark reference values and acceptance tolerances from the primary C5G7 specification. Distinguish code/model verification from comparing noncanonical design variants.
6. Do not map `fresh / once_burned / twice_burned` to UO2/MOX enrichment categories. Either provide a source-backed depletion/material map or present the six-layout assembly-placement problem as a separate research formulation.
7. Only after candidate identity and physics mapping are resolved, compute physical rankings, sensitivity analyses, and reliability metrics, then update the manuscript from the verified results.

## Release language

Safe: “CB-PFR is an open research prototype with a reproducible synthetic benchmark, an independently audited C5G7/OpenMC baseline statepoint, and an 18-run exploratory C5G7 assembly-placement smoke study with repeated seeds. Benchmark-grade candidate evaluation and the legacy-QUBO-to-C5G7 mapping remain unresolved.”

Unsafe without new evidence: “physically validated optimizer,” “validated reactor design,” “six candidates successfully compared,” “independent three-seed confirmation,” or any reactor-safety claim.


## Follow-up implementation: validation gates and explicit design QUBO

The follow-up branch `research-gates-convergence-mapping-20261011` adds executable work for the three outstanding areas:

- `src/cbpfr/c5g7_design_qubo.py`: exact four-variable QUBO for the **separate** 2×2 UO2/MOX placement problem. The constraint `A(sum(y)-2)^2` has exactly six zero-energy assignments. Exhaustive unit tests cover all 16 binary vectors and verify the QUBO expansion.
- `config/benchmarks/c5g7_validation_protocol.json`: staged gates for model identity, canonical k-effective screening, spatial tally validation, repeated-run evaluation, and predeclared optimization objective. Thresholds are explicitly labelled project screening limits, not official OECD/NEA acceptance criteria.
- `scripts/audit_c5g7_validation_gates.py`: machine-checks common compute settings, unique seeds and statepoint hashes, MGXS consistency, HDF5 audit status, repeated-run spread, and provisional canonical scalar checks. It fails closed on data-integrity problems and never treats a scalar match as full validation.
- `reports/C5G7_VALIDATION_AND_MAPPING_PLAN.md`: scientific decision record separating code-ready work from review gates.
- Historical `reports/c5g7_input_provenance_comparison_2026-10-11.md` confirms XML file provenance, but the byte-identical MGXS result was later found to be nonstandard for C5G7: the upstream `np.logspace(-5, 7, 8)` edges do not match the official seven-group boundaries. Endpoint-only normalization did not fix the interior edges. The old scalar comparison is withdrawn; the corrected runner now replaces and audits the full standard boundary list before transport.
- `results/c5g7_smoke_validation_gate_audit_2026-10-11.json`: the 18-run smoke dataset passes data-integrity checks but correctly fails the provisional canonical scalar/precision screen.

The intermediate run budget (2,000 batches, 100 inactive, 5,000 particles/batch, three seeds/layout) is currently executing in [the dedicated workflow](https://github.com/thenextw4ng/cb-pfr/actions/runs/38100178360). It is an intermediate screen, not automatically benchmark-grade or guaranteed to be converged. A separate canonical UMMU numerical screen is also running at 7,000 batches, 100 inactive, 10,000 particles/batch, and three independent seeds ([workflow](https://github.com/thenextw4ng/cb-pfr/actions/runs/38101618802)); it evaluates the provisional scalar/precision gates but cannot by itself certify the full benchmark. The old categorical burnup-state QUBO remains unmapped to C5G7 materials. Six-layout assembly fission-rate proxy outputs are available in [the smoke report](c5g7_assembly_fission_proxy_smoke_2026-10-11.md); they are not absolute power and do not yet establish an optimization winner. Full validation still requires primary-specification review, a benchmark-compatible pin-power/spatial reference comparison, and a defensible mapping from the legacy burnup-state QUBO to physical material states. See the follow-up pull request for CI results.
