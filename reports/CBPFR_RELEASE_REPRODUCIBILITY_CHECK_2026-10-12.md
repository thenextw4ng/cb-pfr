# CB-PFR release reproducibility check — 2026-10-12

## Result

**PASS — archived record/provenance consistency checks.** This is a software/data-integrity result, not a certificate of physical model validity.

## Exact artifact checked

- Local artifact: `cbpfr-high-budget-raw.zip`
- Archive SHA-256: `be48b17c2c336a97d08673d191457b9c695853759180116f5382f636b4c93019`
- ZIP entries: 565
- Embedded source table: `results/c5g7_six_layout_confirmation_2026-10-12/run_level_results.csv`
- Embedded source table rows: 18
- Embedded source table SHA-256: `3eb5d575cc5076ead39de04907beddd25fa2310465b508208579bbd4a5c0192d`
- `CASE_RESULT.json` records: 18
- Common MGXS SHA-256: `a4328a7b012321fbe8f661745aa135f0a2eecd34cf475429e160865204acb129`

## Checks executed against archive bytes

A read-only Python audit was executed against the local ZIP. It independently recomputed the archive and embedded-CSV SHA-256 values, then compared all 18 embedded CSV rows against the corresponding `CASE_RESULT.json` records.

| Check | Result |
|---|---|
| Embedded source CSV exists and has 18 rows | PASS |
| Exactly 18 `CASE_RESULT.json` records | PASS |
| All 18 source rows match case records by round/layout, candidate, seed, statepoint hash, MGXS hash, keff mean and standard deviation | PASS |
| Six expected layouts, three seed rounds (820000, 830000, 840000) | PASS |
| 18 unique seeds and 18 unique statepoint hashes | PASS |
| One common MGXS hash across the campaign | PASS |
| Every case marked completed; XML settings match 7,000 batches, 500 inactive, 10,000 particles/batch | PASS |
| XML seed equals recorded run seed | PASS |

The archive audit confirms internal consistency and provenance metadata. It does **not** prove that the geometry/material mapping is correct, that all spatial tallies are physically validated, or that source convergence and an acceptance criterion have been independently certified.

## Automated software tests

The recorded GitHub Actions workflow for commit `4a8402b4b0252b843b8418fa101b51073ca21ff6` passed on Python 3.10, 3.11, and 3.12:
https://github.com/thenextw4ng/cb-pfr/actions/runs/38267223867

## Release disposition

The archive integrity/provenance check and recorded CI are green. Keep the frozen protocol unchanged. The comparison readiness gate remains fail-closed; no physical winner, full reactor validation, quantum advantage, or CB-PFR superiority is claimed. The package is suitable for a reproducible methodological/software handoff with the stated scientific claim boundary.
