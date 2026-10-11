# BEAVRS experimental-validation execution plan

Date: 2026-10-11  
Project: CB-PFR / ReactorQ Studio  
Decision: BEAVRS is the selected experimental benchmark pathway.

## Why BEAVRS

The public MIT Computational Reactor Physics Group repository describes BEAVRS as a two-cycle, full-core PWR benchmark and distributes an OpenMC model generator, benchmark specifications, and measured data. The repository includes assembly loading data, a boron letdown curve, and in-core detector signals with uncertainty documentation.

- Benchmark source: https://github.com/mit-crpg/BEAVRS
- OpenMC model generator: https://github.com/mit-crpg/BEAVRS/tree/master/models/openmc
- Specifications and measurement data: https://github.com/mit-crpg/BEAVRS/tree/master/measurements
- BEAVRS uncertainty report: https://github.com/mit-crpg/BEAVRS/blob/master/beavrs_uq_report.pdf

## Selected first observable

Use a declared BEAVRS core state and compare a **like-for-like normalized in-core detector/flux distribution** only if the model tally represents the detector measurement definition and its spatial/axial locations. The exact cycle, state identifier, detector channels, normalization, excluded channels, and reference uncertainty must be frozen before examining model residuals.

A second observable may be the measured boron letdown curve, but this requires a depletion/operating-history model and should not be substituted with a static eigenvalue calculation.

## Execution gates (fail closed)

1. **Source freeze:** record the BEAVRS upstream commit, license, file hashes, OpenMC version, nuclear-data library/version and provenance.
2. **Model reproduction:** generate the full-core model from the pinned upstream model builder. Record geometry/material/settings XML and verify the selected experimental state (cycle, exposure, temperatures, boron, control-rod insertion and loading).
3. **Measurement mapping:** choose the exact published measurement file and channels; establish units, detector response, axial/radial position and uncertainty from the benchmark specification. Do not treat normalized detector signal as absolute power.
4. **Run and convergence:** run independent seeds at a declared particle/batch budget; inspect source convergence and tally statistical precision. Preserve stdout/stderr, statepoints, run settings and SHA-256 hashes.
5. **Quantitative comparison:** produce aligned measured/calculated values, residuals, normalized residuals where uncertainties are defensible, correlation/shape metrics as secondary metrics, and a predeclared acceptance rule. Propagate measurement, Monte Carlo and relevant model uncertainty separately.
6. **Independent audit:** verify the model inputs, data provenance, output hashes, extraction code and comparison table from a clean run.
7. **CB-PFR experiment:** only after the BEAVRS model/observable is qualified, define an explicit candidate decision problem and a physically valid mapping. Compare CB-PFR with QUBO-only and other baselines on the same candidate pool and compute budget. Do not infer CB-PFR effectiveness merely from validating the BEAVRS model.

## Current status

**NOT YET PHYSICALLY VALIDATED.** Selection of BEAVRS and identification of public model/measurement resources are research setup, not a completed validation result. This report does not claim that OpenMC was run against BEAVRS measurements.

## Claim boundary for Eureka! ITB

Until Gates 1–6 pass, describe this as an implementation and validation study *in progress*, not “experimentally validated” or “physically validated.” Until Gate 7 passes, do not claim CB-PFR physically improves reactor optimization.

QUBO is a mathematical optimization formulation usable by classical solvers and quantum hardware. If the project only formulates/solves QUBO classically, describe it as QUBO-based or quantum-compatible optimization; do not claim a demonstrated quantum-computing advantage without an actual quantum-device/annealer experiment and a fair comparison.

## Public source notes

The upstream BEAVRS README states that the benchmark includes measured data and associated uncertainties for hot-zero-power physics tests, boron letdown curves, and 3-D in-core flux maps. The public repository contains the OpenMC model builder and measurement data. The precise observable and case must be selected from the specifications before the comparison is implemented.
