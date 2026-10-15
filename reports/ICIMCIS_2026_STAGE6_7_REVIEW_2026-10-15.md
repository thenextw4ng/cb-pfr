# ICIMCIS 2026 — Stage 6–7 Scientific Writing and Reference Audit

**Date:** 2026-10-15  
**Repository branch:** `research/cbpfr-four-gate-closeout-2026-10-12`  
**Status:** Stages 6 and 7 complete for manuscript drafting; stages 8–10 remain separate closeout tasks. This report is not a submission receipt or physical-validation certificate.

## Stage 6 — Discussion, Limitations, and Conclusion

The manuscript now distinguishes the interpretation supported by the current evidence from stronger claims that remain unproven.

- The composition-only QUBO result is described as a property of the specified objective: all six feasible layouts have zero energy. It is not generalized to QUBO as a whole.
- The six-layout OpenMC means are interpreted as descriptive responses of the recorded model and tallies. The lowest mean relative fission-rate peaking proxy is not called a physically optimal or safe layout.
- The canonical UMMU scalar result (mean (k_{\mathrm{eff}}=1.1864932), difference (-5.679) pcm from the saved scalar reference, reported combined-uncertainty (z=-0.434)) is kept separate from the 18-run six-layout archive.
- The maximum 0.179% normalized assembly-distribution difference is described as a single-case consistency comparison, not a formal coverage/equivalence test. Normalization induces dependence among fractions, so published uncertainties for unnormalized assembly powers are not automatically uncertainty intervals for the normalized fractions.
- The exploratory fixed-budget ranking-and-selection comparison selected the same layout for CB-PFR and the baseline. The separate synthetic confirmatory gain of +0.4875 percentage points remained below its prespecified threshold of at least 2 percentage points. These results are not conflated with a physical-validation experiment.
- Limits now explicitly include six layouts, four variable positions, fixed reflectors, three seed rounds, a two-dimensional multigroup model, outstanding independent model-fidelity/source-convergence review, a proxy rather than an absolute-power/safety endpoint, user-declared operational bounds, and no demonstrated selection superiority.
- Follow-up evidence is stated as concrete requirements: independent model/tally review; source/eigenvalue convergence diagnostics; prospectively justified physical limits; treatment separating Monte Carlo, reference, nuclear-data, and model-form uncertainties; and a prospective equal-budget baseline comparison across multiple cases.

## Stage 7 — Related Work and references

The related-work discussion now differentiates the cited literature by role: QUBO formulation; the Usmanov in-core fuel-management study; OpenMC as the transport code; the OECD/NEA C5G7 benchmark; a published deterministic C5G7 comparison; uncertainty-reporting guidance; and statistical ranking-and-selection literature. The manuscript does not claim CB-PFR is the first method of its kind, that its components are individually unprecedented, or that it replaces statistically guaranteed ranking-and-selection methods.

### Primary-source verification record

1. **QUBO survey:** G. Kochenberger et al., “The Unconstrained Binary Quadratic Programming Problem: A Survey,” *Journal of Combinatorial Optimization* 28(1), 58–81 (2014). DOI: https://doi.org/10.1007/s10878-014-9734-0. The paper surveys the general UBQP problem and solution methods; it supports broad formulation context, not a CB-PFR novelty claim.
2. **In-core fuel management:** S. R. Usmanov et al., “Quantum and Quantum-Inspired Optimization for an In-Core Fuel Management Problem,” *Journal of Physics: Conference Series* 2701, 012031 (2024). DOI: https://doi.org/10.1088/1742-6596/2701/1/012031. The author/title/publication details match the published record; the manuscript explicitly says the current binary material-placement case does not reproduce its burnup-state formulation.
3. **OpenMC:** P. K. Romano et al., “OpenMC: A State-of-the-Art Monte Carlo Code for Research and Development,” *Annals of Nuclear Energy* 82, 90–97 (2015). DOI: https://doi.org/10.1016/j.anucene.2014.07.048.
4. **C5G7 primary specification:** E. E. Lewis et al., *Benchmark Specification for Deterministic 2-D/3-D MOX Fuel Assembly Transport Calculations without Spatial Homogenisation (C5G7 MOX)*, OECD/NEA Tech. Rep. NEA/NSC/DOC(2001)4 (2001). Official PDF: https://www.oecd-nea.org/science/wprs/eg3drtb/NEA-C5G7MOX.PDF.
5. **Published C5G7 reference comparison:** P. Song et al., “GPU-Based Two-Level CMFD Accelerating Two-Dimensional MOC Neutron Transport Calculation,” *Frontiers in Energy Research* 8, article 124 (2020). DOI: https://doi.org/10.3389/fenrg.2020.00124. The publisher page reports the C5G7 scalar and assembly/pin power comparison. It is treated as context for a single-case comparison, not as a head-to-head CB-PFR baseline.
6. **Uncertainty reporting:** B. N. Taylor and C. E. Kuyatt, *Guidelines for Evaluating and Expressing the Uncertainty of NIST Measurement Results*, NIST Technical Note 1297 (1994). Official NIST record: https://doi.org/10.6028/NIST.tn.1297. This supports careful distinction of uncertainty components and assumptions; it does not certify the project's operational bounds.
7. **Statistical ranking-and-selection:** S.-H. Kim and B. L. Nelson, “Selecting the Best System,” in *Simulation*, *Handbooks in Operations Research and Management Science*, vol. 13, pp. 501–534 (2006). DOI: https://doi.org/10.1016/S0927-0507(06)13017-0. Used to distinguish CB-PFR's deterministic screening rule from statistical selection procedures.

## Build and local PDF audit

- IEEEtran conference class; A4; 6 pages including references.
- BibTeX bibliography processed using `IEEEtran.bst`; all cited keys resolved in the final build.
- PDF title present; author metadata blank; conference author block remains anonymous.
- Fonts embedded; rendered pages 1–6 were reviewed as a montage; no obvious clipped tables or equations were observed.
- The source compiles locally. The generated PDF is a review draft, not a confirmed EDAS upload.
- The repository's software-release/tag/license/dependency/archived-artifact reconciliation is not claimed complete here; that belongs to Stage 10.

## Claim boundary

This manuscript supports a bounded methodological/software contribution and a limited C5G7/OpenMC case study. It does **not** claim full physical validation, reactor safety qualification, physically optimal fuel selection, calibrated uncertainty coverage, superiority over a fair baseline, quantum-hardware use, or quantum advantage.
