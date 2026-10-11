# EUREKA! ITB 2026 — evidence-aligned manuscript wording

This text is a claim-safe replacement for any passage implying that all planned physical simulations, quantum-annealing runs, or experimental validation have already succeeded. It is based only on artifacts currently recorded in this repository as of 2026-10-11.

## Suggested title

**Formulasi QUBO untuk Optimasi Konfigurasi Fuel Loading dan Audit Validasi Neutronik Berbasis OpenMC: Studi Komputasional Eksploratif**

Use the original stronger title only if the manuscript clearly identifies the Usmanov mapping, actual optimizer, and validation evidence that supports it.

## Abstract

Penelitian ini mengevaluasi alur komputasional untuk menghubungkan formulasi optimasi berbasis Quadratic Unconstrained Binary Optimization (QUBO) dengan analisis transport neutron menggunakan OpenMC pada studi konfigurasi fuel loading. Implementasi perangkat lunak mencakup formulasi QUBO terpisah untuk penempatan empat assembly dengan kendala tepat dua UO2 dan dua MOX, enumerasi enam konfigurasi feasible, serta audit provenance dan integritas artefak simulasi. Sebanyak 18 perhitungan transport eksploratif pada enam konfigurasi dan tiga seed per konfigurasi telah direkam menggunakan struktur grup energi C5G7 yang telah dikoreksi. Hasil tersebut menunjukkan bahwa pipeline transport dan ekstraksi tally dapat dijalankan, tetapi anggaran simulasi masih bersifat smoke-test dan belum memenuhi kriteria penerimaan benchmark. Audit juga menemukan bahwa formulasi penempatan UO2/MOX tersebut belum memiliki pemetaan material/deplesi yang dapat dipertanggungjawabkan ke formulasi keadaan burnup fresh, once-burned, dan twice-burned. Pengulangan optimizer quantum annealing beserta frekuensi solusi dan Hamming distance belum dibuktikan oleh artefak yang tersedia. Karena itu, penelitian ini melaporkan hasil sebagai studi komputasional eksploratif dan audit validasi, bukan sebagai demonstrasi keunggulan quantum annealing atau validasi eksperimen fisik reaktor.

## Results wording

- The software QUBO formulation is verified for its declared four-position/two-MOX constraint by exact enumeration; this is a software/formulation result.
- OpenMC execution is evidenced by 18 exploratory transport runs. Execution and raw-artifact integrity do not imply benchmark acceptance.
- The corrected-group UMMU summary recorded mean k-effective 1.18610263, between-seed sample standard deviation 0.00386340, and standard error 0.00223053 over three runs. These low-budget values are descriptive only; they must not be presented as accepted agreement with the C5G7 reference.
- The mesh flux tally exists in the six-layout smoke artifacts, but a validated spatial flux map, uncertainty treatment, and benchmark-grade convergence have not been established.
- The current local fission-rate observable is an assembly-integrated proxy and is not comparable to the reference maximum normalized pin power 2.498. Do not report these as a direct validation comparison.
- CB-PFR synthetic benchmark rates are 0.857 (QUBO-only), 0.933 (point-estimate), 0.976 (CB-PFR), and 0.966 (uniform margin) across 1,000 synthetic trials per method. These results are conditional on the declared synthetic data-generating process and are not physical validation.

## Limitations

The current evidence does not establish: (1) a defensible mapping from the legacy burnup-state QUBO to C5G7 materials; (2) benchmark-grade convergence or accepted agreement with the C5G7 reference; (3) an equivalent pin-power/assembly-power comparison; (4) actual repeated quantum-annealing execution and raw optimizer samples; or (5) experimental validation of the candidate fuel-loading layouts. Published TRIGA Mark II neutron-flux experiments provide relevant methodological context, but they concern a different reactor design and are not substituted for direct C5G7 measurements. Accessed bibliographic records did not expose the full numerical data and uncertainties required for a quantitative comparison.

## Conclusion wording

The work establishes a reproducible software and exploratory transport workflow, together with an explicit audit of the evidence needed for stronger physical claims. The QUBO cardinality constraint, OpenMC execution, artifact provenance, and synthetic CB-PFR benchmark are supported within their stated scopes. However, the current evidence is insufficient to conclude that the proposed optimizer has been validated against a physical reactor experiment, that the Usmanov burnup-state formulation is physically represented by the C5G7 material model, or that quantum annealing outperforms classical methods. These claims require corresponding model mappings, optimizer samples, comparable observables, and independently reviewed benchmark or experimental data.

## Suggested source citations

- OECD/NEA, International Handbook of Evaluated Reactor Physics Experiments (IRPhE): https://www.oecd-nea.org/jcms/pl_20279/irphe-handbook
- Chiesa et al. (2015), “Measurement and simulation of the neutron flux distribution in the TRIGA Mark II reactor core,” DOI: 10.1016/j.anucene.2015.07.011; institutional record: https://www.boa.unimib.it/handle/10281/89066
- OECD/NEA, C5G7 benchmark specification: https://www.oecd-nea.org/jcms/pl_13548/benchmark-on-deterministic-transport-calculations-without-spatial-homogenisation
