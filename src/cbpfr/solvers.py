"""Solver adapters for CB-PFR's QUBO optimization layer.

The core package has no mandatory quantum-hardware dependency. Exact enumeration
is a classical reference solver. The optional Ocean adapter can connect the same
QUBO to a user-supplied sampler, including simulated annealing or a real quantum
annealer. Solver class is explicit in every result; no quantum advantage claim
is inferred from using QUBO notation or an Ocean API.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import product
import math
import time
from typing import Any, Mapping, Sequence

from .qubo import Candidate, QuboModel


SOLVER_CLASSES = {
    "classical_exact",
    "classical_heuristic",
    "classical_simulated_annealing",
    "classical_simulated_quantum_annealing",
    "quantum_annealer",
    "external",
}


class SolverContractError(ValueError):
    """Raised when a solver invocation or its metadata is invalid."""


@dataclass(frozen=True)
class SolverSolution:
    candidate_id: str
    vector: tuple[int, ...]
    qubo_energy: float
    feasible: bool
    constraint_violations: Mapping[str, int]
    sample_count: int = 1


@dataclass(frozen=True)
class SolverRun:
    schema_version: str
    solver_name: str
    solver_class: str
    solver_backend: str
    variable_count: int
    reads_requested: int
    elapsed_seconds: float
    solutions: tuple[SolverSolution, ...]
    metadata: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _validate_run_args(solver_name: str, solver_class: str, reads: int) -> None:
    if not isinstance(solver_name, str) or not solver_name.strip():
        raise SolverContractError("solver_name must be non-empty")
    if solver_class not in SOLVER_CLASSES:
        raise SolverContractError(f"solver_class must be one of {sorted(SOLVER_CLASSES)}")
    if isinstance(reads, bool) or not isinstance(reads, int) or reads < 1:
        raise SolverContractError("reads must be a positive integer")


def _solution(model: QuboModel, vector: Sequence[int], sample_count: int = 1) -> SolverSolution:
    normalized = tuple(vector)
    if any(isinstance(v, bool) or not isinstance(v, int) or v not in (0, 1) for v in normalized):
        raise SolverContractError("solver sample must contain only integer binary values 0 or 1")
    if isinstance(sample_count, bool) or not isinstance(sample_count, int) or sample_count < 1:
        raise SolverContractError("sample_count must be a positive integer")
    violations = model.constraint_violations(normalized)
    return SolverSolution(
        candidate_id="qubo-" + "".join(str(v) for v in normalized),
        vector=normalized,
        qubo_energy=float(model.energy(normalized)),
        feasible=all(value == 0 for value in violations.values()),
        constraint_violations=violations,
        sample_count=int(sample_count),
    )


def solve_exact(
    model: QuboModel,
    *,
    max_variables: int = 24,
    max_solutions: int = 20,
) -> SolverRun:
    """Classical exhaustive reference solve; safe only for small binary models."""
    if isinstance(max_variables, bool) or not isinstance(max_variables, int) or max_variables < 1:
        raise SolverContractError("max_variables must be a positive integer")
    if isinstance(max_solutions, bool) or not isinstance(max_solutions, int) or max_solutions < 1:
        raise SolverContractError("max_solutions must be a positive integer")
    n = model.variable_count
    if n > max_variables:
        raise SolverContractError(
            f"exact enumeration blocked at {n} variables; configured maximum is {max_variables}"
        )
    started = time.perf_counter()
    best: list[tuple[float, tuple[int, ...], bool, Mapping[str, int]]] = []
    for vector in product((0, 1), repeat=n):
        energy = float(model.energy(vector))
        feasible = model.is_feasible(vector)
        best.append((energy, tuple(vector), feasible, model.constraint_violations(vector)))
    best.sort(key=lambda row: (not row[2], row[0], row[1]))
    # The primary output is the lowest-energy feasible solution if one exists;
    # infeasible samples remain available only when no feasible state exists.
    feasible_rows = [row for row in best if row[2]]
    chosen = (feasible_rows or best)[:max_solutions]
    solutions = tuple(
        SolverSolution(
            candidate_id="qubo-" + "".join(str(v) for v in vector),
            vector=vector,
            qubo_energy=energy,
            feasible=feasible,
            constraint_violations=violations,
        )
        for energy, vector, feasible, violations in chosen
    )
    return SolverRun(
        schema_version="cbpfr.solver-run.v1",
        solver_name="Exact binary enumeration",
        solver_class="classical_exact",
        solver_backend="built-in-python",
        variable_count=n,
        reads_requested=2**n,
        elapsed_seconds=time.perf_counter() - started,
        solutions=solutions,
        metadata={
            "states_evaluated": 2**n,
            "selection_rule": "feasible-first, then increasing QUBO energy",
            "is_quantum_hardware": False,
            "quantum_advantage_established": False,
        },
    )


def model_to_upper_triangular_qubo(model: QuboModel) -> tuple[dict[tuple[int, int], float], float]:
    """Convert the repository's upper-triangular matrix to a sampler QUBO dict.

    Returns (Q, offset). Most samplers ignore constants when finding a minimizer;
    add the offset back when comparing reported energies to QuboModel.energy().
    """
    q: dict[tuple[int, int], float] = {}
    n = model.variable_count
    for i in range(n):
        for j in range(i, n):
            value = float(model.q_upper[i][j])
            if not math.isfinite(value):
                raise SolverContractError("QUBO coefficients must be finite")
            if value != 0.0:
                q[(i, j)] = value
    return q, float(model.offset)


def solve_with_ocean_sampler(
    model: QuboModel,
    *,
    sampler: Any,
    solver_name: str,
    solver_class: str,
    num_reads: int = 100,
    seed: int | None = None,
) -> SolverRun:
    """Run an explicitly supplied D-Wave Ocean-compatible sampler.

    Pass dimod.SimulatedAnnealingSampler for classical simulated annealing,
    or DWaveSampler/EmbeddingComposite for an actual quantum-annealer backend.
    This function does not create credentials, select a cloud solver, or infer
    that a QPU was used: the caller must state solver_class truthfully.
    """
    _validate_run_args(solver_name, solver_class, num_reads)
    if sampler is None or not callable(getattr(sampler, "sample_qubo", None)):
        raise SolverContractError("sampler must expose a callable sample_qubo method")
    q, offset = model_to_upper_triangular_qubo(model)
    kwargs: dict[str, Any] = {"num_reads": num_reads}
    if seed is not None:
        if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
            raise SolverContractError("seed must be a nonnegative integer")
        # Not all Ocean samplers accept seed; only pass it if advertised.
        import inspect
        try:
            parameters = inspect.signature(sampler.sample_qubo).parameters
        except (TypeError, ValueError):
            parameters = {}
        if "seed" in parameters:
            kwargs["seed"] = seed
    started = time.perf_counter()
    sample_set = sampler.sample_qubo(q, **kwargs)
    elapsed = time.perf_counter() - started
    try:
        rows = sample_set.data(fields=["sample", "energy", "num_occurrences"])
    except Exception as exc:
        raise SolverContractError("sampler result must be a dimod-compatible SampleSet") from exc
    aggregated: dict[tuple[int, ...], int] = {}
    for row in rows:
        sample = row.sample
        try:
            raw_vector = tuple(sample[i] for i in range(model.variable_count))
        except (KeyError, IndexError, TypeError) as exc:
            raise SolverContractError("sampler returned a sample with missing variables") from exc
        try:
            valid_vector = all(not isinstance(value, bool) and math.isfinite(float(value))
                               and float(value) in (0.0, 1.0) for value in raw_vector)
        except (TypeError, ValueError, OverflowError):
            valid_vector = False
        if not valid_vector:
            raise SolverContractError("sampler returned a non-binary sample")
        vector = tuple(int(value) for value in raw_vector)
        occurrences = row.num_occurrences
        try:
            count_value = float(occurrences)
            valid_count = (not isinstance(occurrences, bool) and math.isfinite(count_value)
                           and count_value.is_integer() and count_value >= 1)
        except (TypeError, ValueError, OverflowError):
            valid_count = False
        if not valid_count:
            raise SolverContractError("sampler num_occurrences must be a positive integer")
        aggregated[vector] = aggregated.get(vector, 0) + int(count_value)
    if not aggregated:
        raise SolverContractError("sampler returned no samples")
    ordered = sorted(
        aggregated.items(),
        key=lambda item: (not model.is_feasible(item[0]), model.energy(item[0]), item[0]),
    )
    solutions = tuple(_solution(model, vector, count) for vector, count in ordered)
    return SolverRun(
        schema_version="cbpfr.solver-run.v1",
        solver_name=solver_name,
        solver_class=solver_class,
        solver_backend=type(sampler).__module__ + "." + type(sampler).__qualname__,
        variable_count=model.variable_count,
        reads_requested=num_reads,
        elapsed_seconds=elapsed,
        solutions=solutions,
        metadata={
            "seed": seed,
            "returned_unique_samples": len(solutions),
            "total_occurrences": sum(aggregated.values()),
            "qubo_constant_offset": offset,
            "energy_recomputed_with_model_offset": True,
            "is_quantum_hardware": solver_class == "quantum_annealer",
            "quantum_advantage_established": False,
            "warning": "solver_class is caller-declared; preserve backend logs and cloud/QPU metadata as evidence",
        },
    )


def candidates_from_solver_run(run: SolverRun, *, feasible_only: bool = True) -> list[Candidate]:
    """Convert a solver record into candidates for the physical-evaluation stage."""
    return [
        Candidate(solution.candidate_id, solution.vector)
        for solution in run.solutions
        if solution.feasible or not feasible_only
    ]
