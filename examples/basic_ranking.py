"""Minimal CB-PFR API example using an abstract toy candidate set."""

from cbpfr.qubo import CoreSpec, build_usmanov_style_qubo, enumerate_feasible_candidates
from cbpfr.ranking import MetricLimit, PhysicalEstimate, rank_all_methods

spec = CoreSpec(
    name="toy",
    positions=tuple(f"p{i}" for i in range(7)),
    boundary=frozenset(f"p{i}" for i in range(6)),
    inner=frozenset({"p6"}),
    edges=tuple((f"p{i}", f"p{(i + 1) % 6}") for i in range(6)),
    inventory=(3, 3, 1),
)
model = build_usmanov_style_qubo(spec)
candidates = enumerate_feasible_candidates(model)[:4]
metric = MetricLimit(name="response", upper=1.0, z=1.0, scale=1.0, uncertainty_kind="known_se")
estimates = {
    c.candidate_id: PhysicalEstimate(c.candidate_id, {"response": (0.9, 0.02)})
    for c in candidates
}
ranked = rank_all_methods(model, candidates, estimates, [metric], {"response": 0.0})
print("CB-PFR selection:", ranked["cb_pfr"][0].candidate.candidate_id)
