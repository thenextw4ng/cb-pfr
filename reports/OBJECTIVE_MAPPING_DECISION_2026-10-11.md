# Objective, acceptance, and QUBO-to-physics mapping decision

**Decision record:** 2026-10-11  
**Scope:** CB-PFR / C5G7 OpenMC research  
**Status:** Protocol fixed; numerical run and physical-review gates remain open. This is not official benchmark acceptance.

## 1. Separate three different claims

1. **Software verification:** code, manifests, hashes, and automated tests behave as intended.
2. **Canonical benchmark verification:** the exact canonical C5G7 model agrees with the primary specification and its reference scalar and spatial quantities under a predeclared protocol.
3. **Design optimization:** noncanonical candidate layouts are compared under a physically justified objective and hard constraints.

Passing the first does not imply the second or third.

## 2. Canonical C5G7: objective and project screening

For the canonical UMMU arrangement, the validation objective is to minimize the absolute discrepancy between the independently replicated mean (k_\mathrm{eff}) and the selected published reference, while separately verifying a compatible spatial fission-rate/power distribution.

The cited scalar reference is (k_\mathrm{eff}=1.18655) with reported standard uncertainty (9.5\) pcm. The repository's internal screening thresholds are:
- at least three independent seeds;
- common settings, unique statepoint hashes, and a common MGXS SHA-256;
- absolute mean discrepancy no greater than 100 pcm;
- absolute standardized discrepancy no greater than 2 using the reference uncertainty and the empirical across-seed standard error;
- maximum individual-run reported (k_\mathrm{eff}) standard deviation no greater than 10 pcm;
- exact model/material/boundary-condition review and a benchmark-compatible spatial tally comparison.

The numerical limits are **project screening choices**, not official OECD/NEA tolerances. A numerical pass is insufficient if the model-identity or spatial-reference gate is unresolved. Report within-run Monte Carlo uncertainty and between-seed variability separately. Three seeds are a minimal screen, not a strong calibration of the uncertainty distribution.

## 3. Six-layout study: objective template, with a blocking condition

For the separate four-position/two-UO₂/two-MOX design study, the exploratory objective template is to minimize the assembly-integrated fission-rate peaking factor:

\[
F_\mathrm{fission}=\frac{\max_a R_a}{\frac{1}{N_f}\sum_{a=1}^{N_f}R_a},
\]

where (R_a) is the integrated fission tally for fuel assembly (a). This is a relative fission-rate shape proxy, **not absolute power in watts and not a safety metric**.

The objective may only be used for a final ranking after:
1. the 51×51 mesh-to-assembly indexing and tally integration have been independently checked;
2. a design-specific acceptable (k_\mathrm{eff}) band has been justified and fixed before ranking;
3. tally uncertainty has been propagated into uncertainty for (F_\mathrm{fission});
4. the common computational budget is increased until the predeclared uncertainty/convergence criteria are met.

Do **not** apply the canonical reference (k_\mathrm{eff}=1.18655) as an automatic acceptance target for the five noncanonical arrangements: they are not official benchmark reference cases. Until the design-specific band and spatial uncertainty review are resolved, report descriptive responses and uncertainty only; do not name a winner.

## 4. Legacy QUBO mapping decision

The legacy states `fresh`, `once_burned`, and `twice_burned` denote burnup history categories. C5G7's UO₂/MOX labels denote specified material/composition families. These are different physical concepts, so no direct mapping is justified.

A defensible mapping requires an operational definition and units for each burnup category; irradiation/power history and cooling time; isotopic number densities from a documented depletion calculation or traceable source; compatible depletion-chain and nuclear-data provenance; explicit material definitions; and independent review. Without these, the correct status is **`NO_DEFENSIBLE_MAPPING_FOUND`**. The fail-closed checker `scripts/audit_c5g7_mapping_contract.py --manifest config/benchmarks/c5g7_manifest.json` reports missing provenance fields and deliberately never auto-certifies physical validity.

The four-variable QUBO in `src/cbpfr/c5g7_design_qubo.py` is retained as a separate formulation: (y_i=0) means UO₂ at position (i), (y_i=1) means MOX, with exactly two MOX positions. It encodes the material-count constraint only; it does not predict (k_\mathrm{eff}), power, or burnup.

## 5. Current execution state

- The canonical high-budget convergence workflow is running three UMMU seeds with the default profile of 7,000 batches, 100 inactive batches, and 10,000 particles per batch. This is a higher-budget numerical screen, not automatically benchmark-grade.
- The three-run screen must be followed by the model-identity and spatial-reference reviews. If uncertainty limits fail, increase histories rather than relax thresholds after observing results.
- The six-layout 18-run repeated-seed evidence currently uses smoke settings (100/10/1,000) and cannot support final physical ranking.
- The normalized MGXS workflow fixed the previous one-ULP energy-boundary difference for the 18 smoke runs; all use the production-identical MGXS hash.

## References and provenance

- Primary benchmark source: [OECD/NEA C5G7 benchmark description](https://www.oecd-nea.org/jcms/pl_13548/benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation).
- Reference-value citation and scalar audit: [physical simulator validation report](physical_simulator_validation.md).
- Machine-readable gates and definitions: `config/benchmarks/c5g7_objective_protocol.json`.
- Separate design QUBO: `src/cbpfr/c5g7_design_qubo.py`.
