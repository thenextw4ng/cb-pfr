# Validation evidence matrix

| Claim | Evidence | Status | Remaining action |
|---|---|---|---|
| A fresh OpenMC calculation ran | [Actions run 38112118549](https://github.com/thenextw4ng/cb-pfr/actions/runs/38112118549), statepoint artifact and run log | PASS for execution only | None for this smoke run |
| Raw statepoint structure passes the quick-check audit | `raw_hdf5_audit.json`: 22 passed, 0 failed | PASS | Keep audit scope explicit |
| Four-position QUBO has exactly six feasible layouts | `src/cbpfr/c5g7_design_qubo.py`, `tests/test_c5g7_design_qubo.py` | PASS at source/test level | Confirm current CI |
| QUBO energy equals expanded upper-triangular form | Exact 16-vector enumeration in tests | PASS at source/test level | Confirm current CI |
| Published C5G7 reference exists | Song et al. 2020, Table 1; OECD/NEA specification | PASS for source identification | Review exact case/model correspondence |
| (k_{eff}) matches reference within an accepted tolerance | Low-stat run differs by -0.013747; uncertainty is large; model identity gate blocked | BLOCKED | Corrected high-budget multi-seed run and signed model audit |
| Local assembly fission peaking matches published pin power | Observables differ | BLOCKED | Extract comparable reference assembly/pin data and align mapping/normalization |
| Correlated mesh-bin uncertainty is propagated | New independent-replicate aggregation path | NOT RUN for multi-seed physical data | Run at least three unique seeds and aggregate |
| Legacy burnup QUBO maps to C5G7 material states | Existing mapping audit says `NO_DEFENSIBLE_MAPPING_FOUND` | BLOCKED | Document and independently review physically meaningful state/material mapping |
| Experimental physical validation achieved | No suitable direct physical experiment data identified | BLOCKED | Identify a relevant experiment with provenance and measurement uncertainty |
| UI-ready research API exists | `docs/api.md`, `app.py`, CB-PFR Python modules | PASS for research prototype only | Stabilize versioned run/result schema before production UI |

## Status semantics

`PASS` applies only to the stated narrow claim. It does not transfer from execution to validation. `BLOCKED` means a specific required evidence item is missing or incomparable. `NOT RUN` means a planned analysis has not been executed.
