import unittest

from cbpfr.experiment import (
    CandidateEvaluation,
    EvaluationProvenance,
    ExperimentContractError,
    ExperimentSpec,
    MetricObservation,
    bundle_sha256,
    run_ranked_experiment,
)
from cbpfr.qubo import CoreSpec, build_usmanov_style_qubo, enumerate_feasible_candidates
from cbpfr.ranking import MetricLimit


class ExperimentContractTests(unittest.TestCase):
    def setUp(self):
        spec = CoreSpec(
            name="two-position-contract-fixture",
            positions=("A", "B"),
            boundary=frozenset(),
            inner=frozenset(),
            edges=(),
            inventory=(1, 1, 0),
            description="Unit-test fixture only; not a reactor geometry.",
        )
        self.model = build_usmanov_style_qubo(spec)
        self.candidates = enumerate_feasible_candidates(self.model)
        self.metrics = [
            MetricLimit(
                name="keff",
                lower=0.9,
                upper=1.1,
                z=1.0,
                scale=0.1,
                units="dimensionless",
                uncertainty_kind="MC standard deviation",
            )
        ]
        self.spec = ExperimentSpec(
            experiment_id="test-run-001",
            formulation_id="abstract-burnup-qubo-v1",
            candidate_encoding_id="one-hot-burnup-state-v1",
            optimizer_name="exact enumeration",
            optimizer_class="classical_exact",
            code_revision="test-revision",
        )

    def _evaluation(self, candidate, *, source_kind="synthetic", source_reference="fixture.csv"):
        return CandidateEvaluation(
            candidate_id=candidate.candidate_id,
            metrics={
                "keff": MetricObservation(
                    mean=1.0,
                    uncertainty=0.001,
                    units="dimensionless",
                    uncertainty_kind="MC standard deviation",
                )
            },
            provenance=EvaluationProvenance(
                source_kind=source_kind,
                source_reference=source_reference,
                uncertainty_note="test fixture; not a physical result",
            ),
        )

    def _run(self, evaluations=None):
        evaluations = evaluations or [self._evaluation(c) for c in self.candidates]
        return run_ranked_experiment(
            spec=self.spec,
            model=self.model,
            candidates=self.candidates,
            evaluations=evaluations,
            metrics=self.metrics,
            uniform_margins={"keff": 0.01},
        )

    def test_complete_contract_emits_versioned_bundle_and_provenance(self):
        result = self._run()
        self.assertEqual(result["schema_version"], "cbpfr.experiment.v1")
        self.assertEqual(result["formulation"]["formulation_id"], "abstract-burnup-qubo-v1")
        self.assertEqual(result["evidence"]["source_kind"], "synthetic")
        self.assertFalse(result["evidence"]["physical_simulation_performed"])
        self.assertFalse(result["evidence"]["physical_validation_established"])
        self.assertTrue(result["rankings"])
        self.assertTrue(all(row["source_kind"] == "synthetic" for row in result["rankings"]))
        self.assertTrue(all(row["physical_simulation_performed"] is False for row in result["rankings"]))
        self.assertEqual(len(bundle_sha256(result)), 64)

    def test_openmc_provenance_requires_hash_model_revision_and_seed(self):
        with self.assertRaisesRegex(ExperimentContractError, "source_sha256"):
            EvaluationProvenance(
                source_kind="openmc_statepoint",
                source_reference="statepoint.100.h5",
            )

    def test_openmc_record_is_explicitly_identified_as_simulator_evidence(self):
        evaluation = CandidateEvaluation(
            candidate_id=self.candidates[0].candidate_id,
            metrics={
                "keff": MetricObservation(1.0, 0.001, "dimensionless", "MC standard deviation")
            },
            provenance=EvaluationProvenance(
                source_kind="openmc_statepoint",
                source_reference="statepoint.100.h5",
                source_sha256="a" * 64,
                model_id="c5g7-2x2",
                model_revision="abc123",
                seed=101,
                settings={"batches": 100},
                uncertainty_note="within-run Monte Carlo standard deviation",
            ),
        )
        evaluations = [evaluation] + [
            CandidateEvaluation(
                candidate_id=c.candidate_id,
                metrics={"keff": MetricObservation(1.0, 0.001, "dimensionless", "MC standard deviation")},
                provenance=EvaluationProvenance(
                    source_kind="openmc_statepoint",
                    source_reference=f"statepoint-{i}.h5",
                    source_sha256=f"{i + 1:064x}",
                    model_id="c5g7-2x2",
                    model_revision="abc123",
                    seed=101 + i,
                    settings={"batches": 100},
                    uncertainty_note="within-run Monte Carlo standard deviation",
                ),
            )
            for i, c in enumerate(self.candidates[1:], start=1)
        ]
        result = self._run(evaluations)
        self.assertTrue(result["evidence"]["physical_simulation_performed"])
        self.assertTrue(all(row["physical_simulation_performed"] for row in result["rankings"]))
        self.assertEqual(result["rankings"][0]["evaluation_provenance"]["model_revision"], "abc123")

    def test_rejects_missing_candidate_evaluation(self):
        with self.assertRaisesRegex(ExperimentContractError, "IDs must match exactly"):
            self._run([self._evaluation(self.candidates[0])])

    def test_rejects_duplicate_evaluation(self):
        evaluations = [self._evaluation(c) for c in self.candidates]
        evaluations.append(self._evaluation(self.candidates[0], source_reference="duplicate.csv"))
        with self.assertRaisesRegex(ExperimentContractError, "duplicate evaluation"):
            self._run(evaluations)

    def test_rejects_mixed_evidence_sources(self):
        evaluations = [self._evaluation(c) for c in self.candidates]
        evaluations[0] = self._evaluation(self.candidates[0], source_kind="mock")
        with self.assertRaisesRegex(ExperimentContractError, "do not mix source kinds"):
            self._run(evaluations)

    def test_rejects_unit_mismatch(self):
        evaluations = [self._evaluation(c) for c in self.candidates]
        bad = self.candidates[0]
        evaluations[0] = CandidateEvaluation(
            candidate_id=bad.candidate_id,
            metrics={"keff": MetricObservation(1.0, 0.001, "barn", "MC standard deviation")},
            provenance=EvaluationProvenance(source_kind="synthetic", source_reference="fixture.csv"),
        )
        with self.assertRaisesRegex(ExperimentContractError, "units"):
            self._run(evaluations)

    def test_rejects_uncertainty_semantics_mismatch(self):
        evaluations = [self._evaluation(c) for c in self.candidates]
        bad = self.candidates[0]
        evaluations[0] = CandidateEvaluation(
            candidate_id=bad.candidate_id,
            metrics={"keff": MetricObservation(1.0, 0.001, "dimensionless", "between-seed standard deviation")},
            provenance=EvaluationProvenance(source_kind="synthetic", source_reference="fixture.csv"),
        )
        with self.assertRaisesRegex(ExperimentContractError, "uncertainty kind"):
            self._run(evaluations)

    def test_rejects_ambiguous_metric_limit_units(self):
        bad_metrics = [MetricLimit(name="keff", lower=0.9, upper=1.1)]
        with self.assertRaisesRegex(ExperimentContractError, "declare units"):
            run_ranked_experiment(
                spec=self.spec,
                model=self.model,
                candidates=self.candidates,
                evaluations=[self._evaluation(c) for c in self.candidates],
                metrics=bad_metrics,
                uniform_margins={"keff": 0.01},
            )

    def test_bundle_hash_is_deterministic(self):
        result = self._run()
        self.assertEqual(bundle_sha256(result), bundle_sha256(result))
        changed = dict(result)
        changed["extra"] = "mutation"
        self.assertNotEqual(bundle_sha256(result), bundle_sha256(changed))


if __name__ == "__main__":
    unittest.main()
