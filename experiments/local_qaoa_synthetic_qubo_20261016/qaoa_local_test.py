"""Local statevector QAOA validation for the stored n=10 QUBO baseline.

This program intentionally has no IBM Quantum imports or service calls.  It
loads the already-stored coefficients, validates the QUBO-to-Ising algebra for
every computational basis state, then optimizes and samples a local,
statevector simulation of standard X-mixer QAOA.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
from scipy.optimize import differential_evolution


ROOT = Path(__file__).resolve().parent
BASELINE_PATH = ROOT / "qubo_baseline_results.json"
RESULT_PATH = ROOT / "qaoa_local_test_results.json"

# Fixed, reported simulation choices.  The seed is used for both optimization
# and final finite-shot sampling so the run is reproducible.
QAOA_DEPTH = 2
SEED = 20261016
SHOTS = 4096
MAPPING_TOLERANCE = 1e-9


def load_instance() -> dict:
    """Load the stored n=10 baseline without generating any coefficients."""
    baseline = json.loads(BASELINE_PATH.read_text())
    return next(instance for instance in baseline["instances"] if instance["n"] == 10)


def make_problem(instance: dict) -> dict:
    """Expand the stored upper-triangular coefficients and derive H_C.

    The original objective is
        f(x) = sum_i h_i x_i + sum_{i<j} w_ij x_i x_j,
    and the minimized cost is f(x) + A(sum_i x_i-k)^2.  Expanding the penalty
    yields a constant A*k^2, linear terms a_i = h_i+A(1-2*k), and pair terms
    b_ij = w_ij+2*A.  With x_i=(1-Z_i)/2, the Ising Hamiltonian is
        H_C = c I + sum_i g_i Z_i + sum_{i<j} J_ij Z_i Z_j,
    where c=A*k^2+sum(a_i)/2+sum(b_ij)/4,
          g_i=-a_i/2-sum_{j != i} b_ij/4, and J_ij=b_ij/4.
    """
    n = instance["n"]
    k = instance["cardinality"]
    h = tuple(instance["linear_coefficients"])
    upper = instance["pair_coefficients_upper_triangle"]

    pair_objective = {
        (i, j): upper[i][j - i - 1]
        for i in range(n)
        for j in range(i + 1, n)
    }
    objective_abs_bound = sum(abs(value) for value in h) + sum(
        abs(value) for value in pair_objective.values()
    )
    penalty_a = 2 * objective_abs_bound + 1

    linear_qubo = tuple(value + penalty_a * (1 - 2 * k) for value in h)
    pair_qubo = {
        pair: value + 2 * penalty_a for pair, value in pair_objective.items()
    }
    ising_constant = penalty_a * k * k + sum(linear_qubo) / 2 + sum(pair_qubo.values()) / 4
    ising_linear = tuple(
        -linear_qubo[i] / 2
        - sum(
            pair_qubo[(min(i, j), max(i, j))] / 4
            for j in range(n)
            if j != i
        )
        for i in range(n)
    )
    ising_pair = {pair: value / 4 for pair, value in pair_qubo.items()}

    return {
        "n": n,
        "k": k,
        "h": h,
        "pair_objective": pair_objective,
        "penalty_a": penalty_a,
        "objective_abs_bound": objective_abs_bound,
        "linear_qubo": linear_qubo,
        "pair_qubo": pair_qubo,
        "ising_constant": ising_constant,
        "ising_linear": ising_linear,
        "ising_pair": ising_pair,
    }


def objective_energy(bits: tuple[int, ...], problem: dict) -> float:
    return sum(problem["h"][i] * bits[i] for i in range(problem["n"])) + sum(
        coefficient * bits[i] * bits[j]
        for (i, j), coefficient in problem["pair_objective"].items()
    )


def penalized_qubo_energy(bits: tuple[int, ...], problem: dict) -> float:
    return objective_energy(bits, problem) + problem["penalty_a"] * (sum(bits) - problem["k"]) ** 2


def ising_energy(bits: tuple[int, ...], problem: dict) -> float:
    z = tuple(1 - 2 * value for value in bits)
    return (
        problem["ising_constant"]
        + sum(problem["ising_linear"][i] * z[i] for i in range(problem["n"]))
        + sum(
            coefficient * z[i] * z[j]
            for (i, j), coefficient in problem["ising_pair"].items()
        )
    )


def validate_mapping(problem: dict) -> dict:
    """Exhaustively check all 2^10 bitstrings at the requested tolerance."""
    errors = []
    for bits in itertools.product((0, 1), repeat=problem["n"]):
        errors.append(abs(penalized_qubo_energy(bits, problem) - ising_energy(bits, problem)))

    max_error = max(errors)
    if max_error > MAPPING_TOLERANCE:
        raise AssertionError(
            f"QUBO/Ising equivalence failed: {max_error} > {MAPPING_TOLERANCE}"
        )
    return {
        "bitstrings_checked": len(errors),
        "maximum_absolute_energy_error": max_error,
        "tolerance": MAPPING_TOLERANCE,
        "verification": "PASS",
    }


def bits_from_index(index: int, n: int) -> tuple[int, ...]:
    """Use qubit i as bit i (least-significant bit) in the local simulator."""
    return tuple((index >> i) & 1 for i in range(n))


def cost_spectrum(problem: dict) -> np.ndarray:
    """Diagonal spectrum of the derived Ising cost Hamiltonian H_C."""
    return np.array(
        [
            ising_energy(bits_from_index(index, problem["n"]), problem)
            for index in range(2 ** problem["n"])
        ],
        dtype=float,
    )


def apply_x_mixer(state: np.ndarray, beta: float, n: int) -> None:
    """Apply exp(-i*beta*sum_i X_i) in place to a statevector."""
    cosine = np.cos(beta)
    sine = np.sin(beta)
    for qubit in range(n):
        stride = 1 << qubit
        for start in range(0, state.size, 2 * stride):
            lower = np.arange(start, start + stride)
            upper = lower + stride
            lower_values = state[lower].copy()
            upper_values = state[upper].copy()
            state[lower] = cosine * lower_values - 1j * sine * upper_values
            state[upper] = cosine * upper_values - 1j * sine * lower_values


def qaoa_state(parameters: np.ndarray, energies: np.ndarray, n: int, depth: int) -> np.ndarray:
    """Return the exact local statevector for the standard cost/X-mixer QAOA."""
    gamma = parameters[:depth]
    beta = parameters[depth:]
    energy_scale = max(float(np.max(np.abs(energies))), 1.0)
    state = np.full(2**n, 1 / np.sqrt(2**n), dtype=complex)
    for layer in range(depth):
        # gamma is dimensionless during optimization; division simply rescales
        # the physical cost-unitary angle and does not alter H_C.
        state *= np.exp(-1j * gamma[layer] * energies / energy_scale)
        apply_x_mixer(state, beta[layer], n)
    return state


def run_qaoa(problem: dict, exact_optimum: float) -> dict:
    energies = cost_spectrum(problem)
    n = problem["n"]

    def expected_penalized_energy(parameters: np.ndarray) -> float:
        probabilities = np.abs(qaoa_state(parameters, energies, n, QAOA_DEPTH)) ** 2
        return float(np.dot(probabilities, energies))

    # The full Hamiltonian (including the constant term) is used in the cost
    # unitary.  Bounds are on the rescaled gamma coordinates described above.
    result = differential_evolution(
        expected_penalized_energy,
        bounds=[(-np.pi, np.pi)] * QAOA_DEPTH + [(-np.pi / 2, np.pi / 2)] * QAOA_DEPTH,
        seed=SEED,
        maxiter=60,
        popsize=10,
        tol=1e-9,
        atol=1e-9,
        polish=True,
        updating="immediate",
        workers=1,
    )
    state = qaoa_state(result.x, energies, n, QAOA_DEPTH)
    probabilities = np.abs(state) ** 2
    rng = np.random.default_rng(SEED)
    sampled_indices = rng.choice(2**n, size=SHOTS, p=probabilities)
    counts = np.bincount(sampled_indices, minlength=2**n)

    observed = [index for index, count in enumerate(counts) if count]
    best_index = min(observed, key=lambda index: (energies[index], -counts[index], index))
    best_bits = bits_from_index(best_index, n)
    best_objective = objective_energy(best_bits, problem)
    feasible_samples = sum(
        int(count)
        for index, count in enumerate(counts)
        if sum(bits_from_index(index, n)) == problem["k"]
    )
    energy_scale = max(float(np.max(np.abs(energies))), 1.0)
    best_is_feasible = sum(best_bits) == problem["k"]

    return {
        "simulator": "local NumPy statevector simulator",
        "qaoa_depth_p": QAOA_DEPTH,
        "seed": SEED,
        "shots": SHOTS,
        "optimizer": {
            "name": "scipy.optimize.differential_evolution",
            "success": bool(result.success),
            "message": str(result.message),
            "function_evaluations": int(result.nfev),
            "rescaled_gamma": result.x[:QAOA_DEPTH].tolist(),
            "physical_gamma": (result.x[:QAOA_DEPTH] / energy_scale).tolist(),
            "beta": result.x[QAOA_DEPTH:].tolist(),
        },
        "expected_penalized_energy": expected_penalized_energy(result.x),
        "sampled_best": {
            "bits": list(best_bits),
            "count": int(counts[best_index]),
            "penalized_energy": float(energies[best_index]),
            "objective_energy": float(best_objective),
            "feasible": best_is_feasible,
            "ones": int(sum(best_bits)),
            "objective_gap_to_exact_if_feasible": (
                float(best_objective - exact_optimum) if best_is_feasible else None
            ),
        },
        "sampled_feasible_shots": feasible_samples,
        "sampled_feasibility_rate": feasible_samples / SHOTS,
        "exact_constrained_optimum": exact_optimum,
        "exact_optimum_reached_by_sampled_best": bool(
            best_is_feasible and best_objective == exact_optimum
        ),
    }


def main() -> None:
    instance = load_instance()
    problem = make_problem(instance)
    mapping = validate_mapping(problem)
    qaoa = run_qaoa(problem, float(instance["exact_optimum"]))

    report = {
        "title": "Local QAOA validation using stored n=10 QUBO baseline coefficients",
        "baseline_file": BASELINE_PATH.name,
        "hardware_submission": False,
        "penalty": {
            "A": problem["penalty_a"],
            "cardinality_k": problem["k"],
            "objective_absolute_coefficient_bound": problem["objective_abs_bound"],
        },
        "ising_mapping_validation": mapping,
        "local_qaoa": qaoa,
        "note": (
            "Local simulator result only. It is neither a quantum-advantage claim "
            "nor physical validation of CB-PFR."
        ),
    }
    RESULT_PATH.write_text(json.dumps(report, indent=2) + "\n")

    print("Loaded stored baseline: qubo_baseline_results.json (n=10)")
    print("Penalty A:", problem["penalty_a"])
    print("QUBO/Ising bitstrings checked:", mapping["bitstrings_checked"])
    print("Maximum QUBO/Ising energy error:", mapping["maximum_absolute_energy_error"])
    print("Mapping tolerance:", mapping["tolerance"])
    print("Mapping verification:", mapping["verification"])
    print("Local simulator:", qaoa["simulator"])
    print("QAOA depth p:", qaoa["qaoa_depth_p"])
    print("Seed:", qaoa["seed"])
    print("Shots:", qaoa["shots"])
    print("Expected penalized energy:", qaoa["expected_penalized_energy"])
    print("Sampled best bits:", qaoa["sampled_best"]["bits"])
    print("Sampled best penalized energy:", qaoa["sampled_best"]["penalized_energy"])
    print("Sampled best objective energy:", qaoa["sampled_best"]["objective_energy"])
    print("Sampled best feasible:", qaoa["sampled_best"]["feasible"])
    print("Sampled feasibility rate:", qaoa["sampled_feasibility_rate"])
    print("Exact constrained optimum:", qaoa["exact_constrained_optimum"])
    print("Exact optimum reached by sampled best:", qaoa["exact_optimum_reached_by_sampled_best"])
    print("Saved:", RESULT_PATH.name)


if __name__ == "__main__":
    main()