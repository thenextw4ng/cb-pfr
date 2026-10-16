# C5G7 V2a Artifact-Inventory Audit and Claim Boundary — 2026-10-16

## Status

**Artifact inventory: PASS. Final scientific selection analysis: PENDING.**

This is an inventory and workflow-gate audit, not a substitute for the repository's full per-artifact hash/seed-ledger analysis or source-convergence review.

## Evidence inspected

All five V2a shard workflows on `research/c5g7-b0-prereg-b1-pilot-20261015` completed with conclusion `success`:

| Shard | GitHub Actions run | Result | Artifacts |
|---|---:|---|---:|
| 0 | [38769481470](https://github.com/thenextw4ng/cb-pfr/actions/runs/38769481470) | success | 240 |
| 1 | [38769485693](https://github.com/thenextw4ng/cb-pfr/actions/runs/38769485693) | success | 240 |
| 2 | [38769489040](https://github.com/thenextw4ng/cb-pfr/actions/runs/38769489040) | success | 240 |
| 3 | [38769492881](https://github.com/thenextw4ng/cb-pfr/actions/runs/38769492881) | success | 240 |
| 4 | [38769496757](https://github.com/thenextw4ng/cb-pfr/actions/runs/38769496757) | success | 240 |

The artifact inventory was paginated and checked across all five runs.

- 1,200 artifacts total; 1,200 unique artifact IDs and names.
- Zero expired artifacts at audit time.
- Zero artifact names outside the expected V2a pattern.
- Exactly 200 artifacts for each of the six layouts: `MMUU`, `MUMU`, `MUUM`, `UMMU`, `UMUM`, `UUMM`.
- 200 unique seed/pool identifiers; each pool has exactly one artifact for each of the six layouts.
- All 1,200 artifact names encode the same low-budget profile: 800 batches, 500 inactive batches, 2,000 particles per batch, one thread, source profile `good`.

The V2a shard workflow's successful run gate includes automated assertions for OpenMC 0.16.0, completed case identity/seed, raw-statepoint audit status `PASS`, a geometry-derived 24×24 entropy mesh, required tally-balance scores, and zero log warnings of “Fission source site(s) outside of entropy box.” A green workflow means these scripted checks passed; it does not certify convergence or validate a real reactor.

## Cross-campaign dependency is still incomplete

The production workflow [38769477847](https://github.com/thenextw4ng/cb-pfr/actions/runs/38769477847) was still running at the audit snapshot:

- P1–P4 high-budget reference set: 57/60 successful; 3 P4 jobs still in progress.
- P5: 5 jobs in progress.
- P6: 2 jobs in progress and 3 queued.
- The full 75-run production workflow has not completed; no final aggregation result was found in the latest workflow-run inventory.

The repository analyzer `scripts/analyze_c5g7_v2a_selection.py` requires the full 1,200 V2a observations, all 60 P1–P4 high-budget reference rows, and the frozen seed ledger. The separate equal-budget policy replay also requires exactly 1,200 V2a rows and 60 reference rows. Therefore no final candidate-ranking, empirical-regret, or policy-comparison result is asserted in this report.

## Evidence-bounded scientific claims

### Supported now

1. A preregistered, matched-pool low-budget C5G7/OpenMC dataset has been generated for six fuel-placement layouts: 200 observations per layout across 200 common seed pools.
2. All five V2a shard workflows passed their scripted per-run gates, and the GitHub Actions artifact inventory is complete and balanced.
3. The data are suitable inputs for a subsequent audit of low-budget candidate screening, after the full artifact/hash/seed-ledger analyzer runs against the completed high-budget references.

### Not established by this audit

- That every OpenMC run is converged. The workflow records source diagnostics as non-certifying; convergence certification remains false.
- Which layout is physically best, or that one selection policy outperforms another. The required final analyzer and policy replay have not produced final outputs here.
- Experimental validation of a real reactor, official C5G7 benchmark acceptance, or universal physical superiority.
- Quantum advantage. V2a is an OpenMC transport campaign, not a quantum-hardware comparison.

## Required closeout

1. Allow the production workflow to complete.
2. Run and inspect `analyze_c5g7_night_campaign.py` and `analyze_c5g7_v2a_selection.py`; require all planned run IDs, settings, unique statepoint hashes, consistent MGXS hash, and seed-ledger checks to pass.
3. Run the equal-budget selection-policy replay with the resulting 1,200-row and 60-row CSV inputs.
4. Report convergence diagnostics separately; do not upgrade operational screens to convergence certification.

## Reproducibility pointers

- V2a final analyzer: [scripts/analyze_c5g7_v2a_selection.py](https://github.com/thenextw4ng/cb-pfr/blob/research/c5g7-b0-prereg-b1-pilot-20261015/scripts/analyze_c5g7_v2a_selection.py)
- Equal-budget policy replay: [scripts/run_equal_budget_c5g7_selection.py](https://github.com/thenextw4ng/cb-pfr/blob/research/c5g7-b0-prereg-b1-pilot-20261015/scripts/run_equal_budget_c5g7_selection.py)
- Preregistered protocol: [CBPFR_C5G7_CONVERGENCE_SELECTION_QUBO_PROTOCOL_2026-10-16.md](https://github.com/thenextw4ng/cb-pfr/blob/research/c5g7-b0-prereg-b1-pilot-20261015/docs/experiments/CBPFR_C5G7_CONVERGENCE_SELECTION_QUBO_PROTOCOL_2026-10-16.md)
- Production workflow: [run 38769477847](https://github.com/thenextw4ng/cb-pfr/actions/runs/38769477847)
