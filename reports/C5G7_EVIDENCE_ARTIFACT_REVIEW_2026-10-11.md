# C5G7 evidence artifact review — 2026-10-11

## Scope

This review inspects the downloadable artifacts for workflow run 38104812849 (corrected-group six-layout smoke repeatability) and workflow run 38084209709 (archived baseline statepoint audit). It does not run transport or claim physical validation.

## Corrected-group six-layout study: artifact inspection

- Workflow: https://github.com/thenextw4ng/cb-pfr/actions/runs/38104812849
- Artifact: `c5g7-layout-repeatability-smoke`
- Artifact ID: `11689430730`
- ZIP SHA-256: `16ab7ac4b19dac6e757662ee6acf5e6fc0f295ff8734e718bc6e15c8d71bab65`
- ZIP size: 8,063,435 bytes; 575 members.
- Includes three seed rounds (620000, 630000, 640000), 18 statepoint HDF5 files, 18 settings files, build/transport logs, case summaries, per-round raw-HDF5 audits, and run-level plus aggregate analyses.
- Each round includes six candidate cases, uses 100 total batches, 10 inactive batches, 1,000 particles per batch, and one thread.
- The six candidate statepoints within each round have unique hashes; the three rounds share the corrected MGXS hash `a4328a7b012321fbe8f661745aa135f0a2eecd34cf475429e160865204acb129`.
- The raw-HDF5 audit records 108/108 checks passing in each round (324/324 across the three rounds).
- The run-level analysis reports 18 unique statepoint hashes and 18 distinct seeds. The rank correlation between the three k-effective ranking rounds is 0.943, 1.000, and 0.943 for the three round pairs. This is descriptive stability from only three smoke-budget repetitions, not strong statistical calibration.

### Correct interpretation

These are completed, integrity-audited *exploratory* corrected-group transport runs. Their settings are not benchmark-grade convergence settings. The fission-peaking scalar is a relative fission-rate shape proxy, not absolute power, a safety metric, or an approved final optimization objective. The run analysis itself blocks acceptance because no design-specific k-effective band or benchmark-grade convergence has been established. Do not select a winner from this dataset.

## Archived 20,000-batch baseline audit: artifact inspection

- Workflow: https://github.com/thenextw4ng/cb-pfr/actions/runs/38084209709
- Artifact: `openmc-statepoint-audit`
- Artifact ID: `11681725452`
- ZIP SHA-256: `1ec35fad35f838a791ee5d8fdba22a6d1c8593387c94f21b03a47b40bbb5b5c1`
- ZIP size: 952,825 bytes; 20 members.
- The audit metadata reports OpenMC 0.16.0, 20,000 batches, 500 inactive batches, 10,000 particles per batch, 19,500 realizations, and (k_{eff}=1.1863941447\pm0.0000561134).
- The audit's artifact inventory records the original baseline statepoint path as `c5g7-run/2d/statepoint.20000.h5`, size 1,158,736 bytes, SHA-256 `0d76dc1a14a2b74a388c01883f01e5c3095480d53eee885910ca2a0c57e6b882`.
- Important packaging distinction: the downloaded `openmc-statepoint-audit` ZIP contains derived audits, CSVs, plots, and an inventory, but does not itself contain the raw 20,000-batch HDF5 statepoint. To claim that the baseline is independently reproducible from the public release, the raw statepoint must be reachable through the repository's archived source evidence or a retained artifact, and its hash must match the inventory.

### Scientific blocker remains

The historical baseline MGXS used nonstandard log-spaced group boundaries. The project's validation report correctly withdraws the earlier scalar-to-reference agreement as benchmark evidence. The 20,000-batch result is useful archived execution/statepoint evidence, but it must not be presented as a verified standard-C5G7 benchmark until a corrected-group run and model-identity review pass.

## Canonical high-budget run status at review time

Workflow: https://github.com/thenextw4ng/cb-pfr/actions/runs/38103032861

At the latest status check during this review, the `canonical-screen` job was still `in_progress`; the step running three independent canonical UMMU cases was still running, numerical aggregation was pending, and no workflow artifact was yet available. This report therefore records no result for that run. Recheck the workflow and inspect its uploaded statepoints/audit before changing the gate status.

## Immediate next actions

1. Recheck and preserve the high-budget canonical workflow output; inspect raw HDF5 audits, settings, seeds, hashes, convergence diagnostics, and the aggregate gate report.
2. Review the corrected model against the primary C5G7 specification, including geometry, boundary conditions, compositions, nuclear-data provenance, MGXS energy boundaries, and the precise reference problem.
3. Independently verify the spatial mapping from mesh indices to assembly positions and retain a geometry-linked test or visual evidence. Existing synthetic-block unit tests verify array slicing but do not alone establish physical orientation.
4. Define and justify a design-specific (k_{eff}) acceptance band before ranking noncanonical layouts. Do not transfer the canonical reference value automatically to all variants.
5. Run the six layouts at a common justified higher budget, retain every raw statepoint and manifest, and propagate uncertainty to the fission-peaking objective. If the results remain inconclusive, report them as such.
6. Keep the legacy burnup-state QUBO mapping blocked unless traceable depletion/material evidence is produced. The C5G7 UO₂/MOX placement QUBO is a separate formulation.

## Current safe conclusion

The repository has a reproducible synthetic CB-PFR benchmark, passing software CI, a complete corrected-group 18-run exploratory C5G7 artifact, and an audited archived 20,000-batch statepoint summary. The historical baseline is not standard-C5G7 benchmark evidence because of its nonstandard MGXS group structure. The corrected smoke study is not benchmark-grade candidate validation. No physical CB-PFR effectiveness, reactor-safety improvement, quantum advantage, or best-layout claim is established.
