# Reproducibility

## What is verified

- The supplied 1,000-trial synthetic result table can be audited from the released trial-level CSV.
- The lightweight software smoke tests exercise QUBO energy consistency, conservative ranking, and fail-closed uncertainty handling.
- The MC/DC C5G7 execution record documents real simulator execution and repeatability checks.

## What is not claimed

The archived 1,000-trial generator is **not turnkey in this release**. Its original execution path expects additional components (`cbpfr.experiments`, `config/toy_core_7.json`, and related historical experiment utilities) that are not part of the supplied workspace. Consequently, the repository does not claim a fresh end-to-end reproduction of the reported 1,000 trials.

The physical simulator record is execution evidence, not CB-PFR physical validation. A defensible physical study requires a traceable QUBO-to-physics mapping and a documented model/data provenance.

## Audit commands

```bash
python -m unittest discover -s tests -v
python -m py_compile src/cbpfr/*.py scripts/*.py
python scripts/audit_recorded_results.py
```
