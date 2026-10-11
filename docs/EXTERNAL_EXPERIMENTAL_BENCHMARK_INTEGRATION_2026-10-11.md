# External experimental benchmark integration — 2026-10-11

## Decision

External experimental results can reduce the need to repeat measurements and can test whether a calculation method is credible on a comparable system. They cannot be treated as direct experimental validation of the ReactorQ/Usmanov fuel-loading candidates unless reactor type, geometry, material/depletion state, operating condition, measured quantity, normalization, and uncertainty are sufficiently matched.

This review found useful published reactor-physics experiments, but did **not** find an open numerical dataset that is directly interchangeable with the current C5G7 UO2/MOX assembly-placement study. Therefore no external numbers have been copied into the C5G7 results table, and no experimental-validation status is upgraded.

## Source register

### 1. OECD/NEA International Handbook of Evaluated Reactor Physics Experiments (IRPhE)

- Source: https://www.oecd-nea.org/jcms/pl_20279/irphe-handbook
- Catalog record: https://www.oecd-nea.org/tools/abstract/detail/nea-1765
- Role: high-quality evaluated reactor-physics experimental benchmark specifications, including measurements and uncertainty evaluation.
- Access: the handbook is distributed through an access request; some data are restricted. Do not claim access to or reproduce data not actually obtained.
- Compatibility with current C5G7 model: **candidate external methodology/benchmark source, not yet directly comparable**. Select a specific case only after obtaining its primary specification and confirming physical similarity and observables.

### 2. Chiesa et al. (2015), TRIGA Mark II neutron-flux distribution

- DOI: https://doi.org/10.1016/j.anucene.2015.07.011
- Publisher page: https://www.sciencedirect.com/science/article/abs/pii/S0306454915003709
- Institutional record: https://www.boa.unimib.it/handle/10281/89066
- Reported method: neutron activation of Al-Co samples; integral and fast flux measurements at multiple positions; comparison with an MCNP5 model.
- Role: a published example of experimental neutron-flux measurement and computational comparison.
- Compatibility: **not a direct C5G7 validation dataset**. TRIGA Mark II uses a different reactor design and fuel/moderator system. The institutional record lists no full-text file, and the publisher page is an abstract page; raw numerical measurements and uncertainties were not extracted in this integration pass.

### 3. Borio di Tigliole et al. (2010), Pavia TRIGA Mark II first critical configuration

- DOI: https://doi.org/10.1016/j.pnucene.2009.11.002
- Institutional record: https://iris.unipv.it/handle/11571/223598
- Role: reports comparison of calculated reactor critical parameters and flux distributions with experimental/operational data.
- Compatibility: **methodological precedent only** until full primary data, uncertainties, and comparable model definitions are obtained.

### 4. C5G7 OECD/NEA computational benchmark

- Specification entry point: https://www.oecd-nea.org/jcms/pl_13548/benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation
- Role: computational transport-code benchmark; useful for verifying implementation and comparing specified transport quantities.
- Important boundary: C5G7 is not itself a physical-reactor experiment. Agreement with C5G7 reference calculations cannot be described as experimental physical validation.

## Integration rule

Only enter a datum into a quantitative validation table if the source record contains all of:
1. primary source and exact table/figure/page;
2. measured quantity and units;
3. configuration and operating conditions;
4. uncertainty and its definition;
5. transformation/normalization performed by this project;
6. an explicit compatibility assessment with the simulated observable.

If any item is missing, retain the source as a literature/methodology citation and do not invent a point estimate or uncertainty.

## Reproducible conclusion for the current project

External literature establishes that experimental flux and critical-parameter measurements exist and are used to benchmark neutron-transport calculations. The presently accessible source records do not provide a complete, directly comparable, machine-readable dataset for the current C5G7 candidate layouts. Consequently, external literature strengthens the validation plan and background, but does not close the project-specific experimental-validation claim. The current claim status remains **NOT ESTABLISHED**.
