import unittest

from cbpfr.experiment import CandidateEvaluation, EvaluationProvenance, ExperimentSpec, MetricObservation
from cbpfr.pipeline import run_solver_to_physics_pipeline
from cbpfr.qubo import CoreSpec, build_usmanov_style_qubo
from cbpfr.ranking import MetricLimit
from cbpfr.solvers import candidates_from_solver_run, solve_exact
from cbpfr.experiment import ExperimentContractError


class SolverPipelineTests(unittest.TestCase):
    def setUp(self):
        core = CoreSpec(
            name="pipeline-test",
            positions=("A", "B"),
            boundary=frozenset(),
            inner=frozenset(),
            edges=(),
            inventory=(1, 1, 0),
            description="Test-only topology.",
        )
        self.model = build_usmanov_style_qubo(core)
        self.solver_run = solve_exact(self.model, max_variables=6, max_solutions=10)
        self.candidates = candidates_from_solver_run(self.solver_run)
        self.spec = ExperimentSpec(
            experiment_id="pipeline-test-01",
            formulation_id="toy-usmanov-style-v1",
            candidate_encoding_id="one-hot-three-state-v1",
            optimizer_name=self.solver_run.solver_name,
            optimizer_class=self.solver_run.solver_class,
            code_revision="unit-test",
        )
        self.metrics = [
            MetricLimit(
                name="response",
                upper=1.1,
                z=1.0,
                scale=1.0,
                units="dimensionless",
                uncertainty_kind="synthetic standard deviation",
            )
        ]
        self.evaluations = [
            CandidateEvaluation(
                candidate_id=c.candidate_id,
                metrics={
                    "response": MetricObservation(
                        mean=1.0, uncertainty=0.01, units="dimensionless",
                        uncertainty_kind="synthetic standard deviation",
                    )
                },
                provenance=EvaluationProvenance(
                    source_kind="synthetic",
                    source_reference="unit-test-fixture",
                    uncertainty_note="not physical data",
                ),
            )
            for c in self.candidates
        ]

    def test_solver_output_is_bound_into_decision_bundle(self):
        result = run_solver_to_physics_pipeline(
            spec=self.spec,
            model=self.model,
            solver_run=self.solver_run,
            candidates=self.candidates,
            evaluations=self.evaluations,
            metrics=self.metrics,
            uniform_margins={"response": 0.02},
        )
        self.assertEqual(result["solver_run"]["solver_class"], "classical_exact")
        self.assertTrue(result["pipeline"]["solver_candidate_join_validated"])
        self.assertFalse(result["pipeline"]["physics_simulator_invoked_by_pipeline"])
        self.assertEqual(len(result["decision_bundle_sha256"]), 64)
        self.assertFalse(result["evidence"]["physical_simulation_performed"])

    def test_pipeline_rejects_solver_class_mismatch(self):
        bad = self.solver_run.to_dict()
        bad["solver_class"] = "quantum_annealer"
        with self.assertRaisesRegex(ExperimentContractError, "solver class"):
            run_solver_to_physics_pipeline(
                spec=self.spec, model=self.model, solver_run=bad,
                candidates=self.candidates, evaluations=self.evaluations,
                metrics=self.metrics, uniform_margins={"response": 0.02},
            )

    def test_pipeline_rejects_tampered_solver_energy_and_lossy_vector_coercion(self):
        bad_energy = self.solver_run.to_dict()
        bad_energy["solutions"] = [dict(row) for row in bad_energy["solutions"]]
        bad_energy["solutions"][0]["qubo_energy"] += 100.0
        with self.assertRaisesRegex(ExperimentContractError, "energy does not match"):
            run_solver_to_physics_pipeline(
                spec=self.spec, model=self.model, solver_run=bad_energy,
                candidates=self.candidates, evaluations=self.evaluations,
                metrics=self.metrics, uniform_margins={"response": 0.02},
            )

        bad_vector = self.solver_run.to_dict()
        bad_vector["solutions"] = [dict(row) for row in bad_vector["solutions"]]
        bad_vector["solutions"][0]["vector"] = [0.5 if i == 0 else v for i, v in enumerate(bad_vector["solutions"][0]["vector"])]
        with self.assertRaisesRegex(ExperimentContractError, "integer binary"):
            run_solver_to_physics_pipeline(
                spec=self.spec, model=self.model, solver_run=bad_vector,
                candidates=self.candidates, evaluations=self.evaluations,
                metrics=self.metrics, uniform_margins={"response": 0.02},
            )

    def test_pipeline_rejects_candidate_not_from_solver(self):
        from cbpfr.qubo import Candidate
        bad_candidates = [Candidate("invented", self.candidates[0].vector)]
        with self.assertRaisesRegex(ExperimentContractError, "unchanged solver output"):
            run_solver_to_physics_pipeline(
                spec=self.spec, model=self.model, solver_run=self.solver_run,
                candidates=bad_candidates, evaluations=self.evaluations[:1],
                metrics=self.metrics, uniform_margins={"response": 0.02},
            )


if __name__ == "__main__":
    unittest.main()
