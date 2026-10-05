"""Construct and inspect the abstract seven-position QUBO."""
from cbpfr.qubo import CoreSpec, build_usmanov_style_qubo, enumerate_feasible_candidates

spec = CoreSpec(
    name="toy",
    positions=tuple(f"p{i}" for i in range(7)),
    boundary=frozenset(f"p{i}" for i in range(6)),
    inner=frozenset({"p6"}),
    edges=tuple((f"p{i}", f"p{(i + 1) % 6}") for i in range(6)),
    inventory=(3, 3, 1),
)
model = build_usmanov_style_qubo(spec)
print("binary variables:", model.variable_count)
print("exact feasible candidates:", len(enumerate_feasible_candidates(model)))
