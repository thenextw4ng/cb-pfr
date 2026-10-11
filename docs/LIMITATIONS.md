# Limitations and non-claims

- This is a research software prototype, not a reactor design or safety analysis system.
- A passing CI job, successful OpenMC execution, and statepoint integrity checks do not constitute physical validation.
- The current five-minute run is deliberately low-statistics (15 active batches, 100 particles per batch) and its (k_{eff}) standard deviation is about 0.0195.
- The corrected seven-group boundaries address a known input issue, but complete geometry/material/temperature/boundary-condition/tally equivalence with the primary benchmark specification still needs independent review.
- The C5G7 reference values are computational benchmark results, not direct measurements from a physical reactor.
- The local assembly-integrated fission-rate peaking factor is not absolute power and is not the same quantity as maximum normalized pin power.
- Within-run uncertainty for the nonlinear ratio is not inferred by treating correlated mesh bins as independent. The new replicate estimator requires multiple distinct statepoints and does not capture model/nuclear-data uncertainty.
- The legacy categorical QUBO uses fresh/once-burned/twice-burned labels. No defensible mapping from those labels to C5G7 UO2/MOX compositions is established.
- The four-position exactly-two-MOX QUBO is a separate combinatorial encoding. In a six-layout design space, exact enumeration is the natural baseline; a QUBO encoding alone does not show computational advantage.
- CB-PFR bounds are operational heuristics unless their distributional assumptions and (z) values are independently justified. They are not confidence bounds by default and are not safety margins.
- No suitable experiment-specific physical dataset has been identified for a claim of experimental validation.
