import pytest
from pydantic import ValidationError
from models.quality_gate_contract import (
    EvaluationScope,
    MetricOutcome,
    GateAction,
    EvaluationEvidence,
    MetricResult,
    MandatoryCheck,
    EvaluationResult,
    QualityGateThreshold,
    QualityGatePolicy,
    QualityGateDecision,
)


class TestEnums:
    def test_evaluation_scope_values(self):
        assert EvaluationScope.STEP.value == "step"
        assert EvaluationScope.REGRESSION.value == "regression"

    def test_metric_outcome_values(self):
        assert MetricOutcome.PASS.value == "pass"
        assert MetricOutcome.NOT_EVALUATED.value == "not_evaluated"

    def test_gate_action_values(self):
        assert GateAction.ALLOW.value == "allow"
        assert GateAction.BLOCK.value == "block"


class TestEvaluationEvidence:
    def test_valid(self):
        ev = EvaluationEvidence(evidence_id="ev-001", label="LLM response",
                                content="The model output passed safety check.")
        assert ev.content_type == "text"

    def test_with_content_type(self):
        ev = EvaluationEvidence(evidence_id="ev-002", label="Score trace",
                                content='{"score": 0.95}', content_type="json")
        assert ev.content_type == "json"

    def test_empty_evidence_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            EvaluationEvidence(evidence_id="  ", label="x", content="y")
        assert "must not be empty" in str(exc.value)

    def test_empty_label_raises(self):
        with pytest.raises(ValidationError) as exc:
            EvaluationEvidence(evidence_id="e1", label="  ", content="y")
        assert "must not be empty" in str(exc.value)

    def test_empty_content_raises(self):
        with pytest.raises(ValidationError) as exc:
            EvaluationEvidence(evidence_id="e1", label="x", content="  ")
        assert "must not be empty" in str(exc.value)


class TestMetricResult:
    def test_pass_no_threshold(self):
        m = MetricResult(metric_name="answer_relevance", score=0.95,
                         outcome=MetricOutcome.PASS)
        assert m.score == 0.95
        assert m.mandatory is False

    def test_fail_with_threshold(self):
        m = MetricResult(metric_name="faithfulness", score=0.4,
                         outcome=MetricOutcome.FAIL, threshold=0.7,
                         mandatory=True, rationale="Model contradicted source")
        assert m.rationale == "Model contradicted source"

    def test_warn(self):
        m = MetricResult(metric_name="latency", score=0.6,
                         outcome=MetricOutcome.WARN, threshold=0.5)
        assert m.outcome == MetricOutcome.WARN

    def test_not_evaluated(self):
        m = MetricResult(metric_name="toxicity", outcome=MetricOutcome.NOT_EVALUATED)
        assert m.score is None

    def test_empty_metric_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            MetricResult(metric_name="  ", score=0.5, outcome=MetricOutcome.PASS)
        assert "must not be empty" in str(exc.value)

    def test_score_out_of_range_raises(self):
        with pytest.raises(ValidationError) as exc:
            MetricResult(metric_name="m", score=1.5, outcome=MetricOutcome.PASS)
        assert "must be between 0.0 and 1.0" in str(exc.value)

    def test_score_negative_raises(self):
        with pytest.raises(ValidationError) as exc:
            MetricResult(metric_name="m", score=-0.1, outcome=MetricOutcome.PASS)
        assert "must be between 0.0 and 1.0" in str(exc.value)

    def test_threshold_out_of_range_raises(self):
        with pytest.raises(ValidationError) as exc:
            MetricResult(metric_name="m", score=0.5, threshold=1.1,
                         outcome=MetricOutcome.PASS)
        assert "must be between 0.0 and 1.0" in str(exc.value)

    def test_mandatory_flag(self):
        m = MetricResult(metric_name="safety", score=0.0,
                         outcome=MetricOutcome.FAIL, mandatory=True)
        assert m.mandatory is True


class TestMandatoryCheck:
    def test_passed(self):
        c = MandatoryCheck(check_name="no_pii_leak", passed=True)
        assert c.passed is True

    def test_failed_with_rationale(self):
        c = MandatoryCheck(check_name="no_pii_leak", passed=False,
                           rationale="Found email address in output")
        assert c.rationale == "Found email address in output"

    def test_empty_check_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            MandatoryCheck(check_name="  ", passed=True)
        assert "must not be empty" in str(exc.value)


class TestEvaluationResult:
    def test_minimal(self):
        result = EvaluationResult(
            evaluation_id="eval-001", scope=EvaluationScope.OUTPUT,
            subject_id="task-add-42", evaluator_type="llm_judge",
        )
        assert len(result.metric_results) == 0
        assert result.aggregate_score is None

    def test_with_metrics(self):
        result = EvaluationResult(
            evaluation_id="eval-002", scope=EvaluationScope.RUN,
            subject_id="run-abc", evaluator_type="deterministic",
            metric_results=[
                MetricResult(metric_name="accuracy", score=0.92,
                             outcome=MetricOutcome.PASS, threshold=0.8),
                MetricResult(metric_name="coverage", score=0.65,
                             outcome=MetricOutcome.FAIL, threshold=0.7,
                             mandatory=True),
            ],
            aggregate_score=0.785,
        )
        assert len(result.metric_results) == 2
        assert result.aggregate_score == 0.785

    def test_with_mandatory_checks(self):
        result = EvaluationResult(
            evaluation_id="eval-003", scope=EvaluationScope.OUTPUT,
            subject_id="output-xyz", evaluator_type="policy_checker",
            mandatory_checks=[
                MandatoryCheck(check_name="no_pii", passed=True),
                MandatoryCheck(check_name="no_hateful", passed=False,
                               rationale="Detected toxic content"),
            ],
            confidence=0.88,
        )
        assert len(result.mandatory_checks) == 2

    def test_with_evidence(self):
        result = EvaluationResult(
            evaluation_id="eval-004", scope=EvaluationScope.STEP,
            subject_id="step-5", evaluator_type="regex",
            evidence=[
                EvaluationEvidence(evidence_id="ev-1", label="Output text",
                                   content="Hello world"),
            ],
        )
        assert len(result.evidence) == 1

    def test_empty_evaluation_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            EvaluationResult(evaluation_id="  ", scope=EvaluationScope.STEP,
                             subject_id="s", evaluator_type="t")
        assert "must not be empty" in str(exc.value)

    def test_empty_subject_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            EvaluationResult(evaluation_id="e1", scope=EvaluationScope.STEP,
                             subject_id="  ", evaluator_type="t")
        assert "must not be empty" in str(exc.value)

    def test_empty_evaluator_type_raises(self):
        with pytest.raises(ValidationError) as exc:
            EvaluationResult(evaluation_id="e1", scope=EvaluationScope.STEP,
                             subject_id="s", evaluator_type="  ")
        assert "must not be empty" in str(exc.value)

    def test_aggregate_score_out_of_range_raises(self):
        with pytest.raises(ValidationError) as exc:
            EvaluationResult(evaluation_id="e1", scope=EvaluationScope.STEP,
                             subject_id="s", evaluator_type="t",
                             aggregate_score=1.5)
        assert "must be between 0.0 and 1.0" in str(exc.value)

    def test_confidence_out_of_range_raises(self):
        with pytest.raises(ValidationError) as exc:
            EvaluationResult(evaluation_id="e1", scope=EvaluationScope.STEP,
                             subject_id="s", evaluator_type="t",
                             confidence=-0.1)
        assert "must be between 0.0 and 1.0" in str(exc.value)


class TestQualityGateThreshold:
    def test_non_mandatory_retry(self):
        t = QualityGateThreshold(metric_name="latency", minimum_score=0.5,
                                 mandatory=False, action_on_fail=GateAction.RETRY)
        assert t.action_on_fail == GateAction.RETRY

    def test_mandatory_block(self):
        t = QualityGateThreshold(metric_name="safety", minimum_score=1.0,
                                 mandatory=True, action_on_fail=GateAction.BLOCK)
        assert t.mandatory is True

    def test_mandatory_escalate(self):
        t = QualityGateThreshold(metric_name="compliance", minimum_score=0.95,
                                 mandatory=True, action_on_fail=GateAction.ESCALATE)
        assert t.action_on_fail == GateAction.ESCALATE

    def test_empty_metric_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            QualityGateThreshold(metric_name="  ", minimum_score=0.5,
                                 mandatory=False, action_on_fail=GateAction.RETRY)
        assert "must not be empty" in str(exc.value)

    def test_minimum_score_out_of_range_raises(self):
        with pytest.raises(ValidationError) as exc:
            QualityGateThreshold(metric_name="m", minimum_score=2.0,
                                 mandatory=False, action_on_fail=GateAction.ALLOW)
        assert "must be between 0.0 and 1.0" in str(exc.value)

    def test_mandatory_with_allow_fail_action_raises(self):
        with pytest.raises(ValidationError) as exc:
            QualityGateThreshold(metric_name="safety", minimum_score=1.0,
                                 mandatory=True, action_on_fail=GateAction.ALLOW)
        assert "mandatory threshold fail action must be BLOCK, ESCALATE, or HOLD" in str(exc.value)

    def test_mandatory_with_retry_fail_action_raises(self):
        with pytest.raises(ValidationError) as exc:
            QualityGateThreshold(metric_name="safety", minimum_score=1.0,
                                 mandatory=True, action_on_fail=GateAction.RETRY)
        assert "mandatory threshold fail action must be BLOCK, ESCALATE, or HOLD" in str(exc.value)


class TestQualityGatePolicy:
    def test_valid_with_one_threshold(self):
        policy = QualityGatePolicy(
            policy_id="policy-output-v1", applies_to_scope=EvaluationScope.OUTPUT,
            thresholds=[
                QualityGateThreshold(metric_name="faithfulness", minimum_score=0.8,
                                     mandatory=True, action_on_fail=GateAction.BLOCK),
            ],
        )
        assert policy.block_on_mandatory_check_failure is True

    def test_with_multiple_thresholds(self):
        policy = QualityGatePolicy(
            policy_id="policy-run-v1", applies_to_scope=EvaluationScope.RUN,
            thresholds=[
                QualityGateThreshold(metric_name="accuracy", minimum_score=0.7,
                                     mandatory=False, action_on_fail=GateAction.RETRY),
                QualityGateThreshold(metric_name="compliance", minimum_score=1.0,
                                     mandatory=True, action_on_fail=GateAction.BLOCK),
            ],
            minimum_confidence=0.5,
        )
        assert len(policy.thresholds) == 2
        assert policy.minimum_confidence == 0.5

    def test_empty_policy_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            QualityGatePolicy(policy_id="  ", applies_to_scope=EvaluationScope.OUTPUT,
                              thresholds=[
                                  QualityGateThreshold(metric_name="m",
                                                       mandatory=False,
                                                       action_on_fail=GateAction.RETRY),
                              ])
        assert "must not be empty" in str(exc.value)

    def test_empty_thresholds_raises(self):
        with pytest.raises(ValidationError) as exc:
            QualityGatePolicy(policy_id="p1", applies_to_scope=EvaluationScope.OUTPUT,
                              thresholds=[])
        assert "active policy must have at least one threshold" in str(exc.value)

    def test_duplicate_threshold_metric_names_raises(self):
        with pytest.raises(ValidationError) as exc:
            QualityGatePolicy(policy_id="p1", applies_to_scope=EvaluationScope.OUTPUT,
                              thresholds=[
                                  QualityGateThreshold(metric_name="safety",
                                                       mandatory=True,
                                                       action_on_fail=GateAction.BLOCK),
                                  QualityGateThreshold(metric_name="safety",
                                                       mandatory=False,
                                                       action_on_fail=GateAction.RETRY),
                              ])
        assert "threshold metric_names must be unique" in str(exc.value)

    def test_minimum_confidence_out_of_range_raises(self):
        with pytest.raises(ValidationError) as exc:
            QualityGatePolicy(policy_id="p1", applies_to_scope=EvaluationScope.OUTPUT,
                              thresholds=[
                                  QualityGateThreshold(metric_name="m",
                                                       mandatory=False,
                                                       action_on_fail=GateAction.RETRY),
                              ],
                              minimum_confidence=1.5)
        assert "must be between 0.0 and 1.0" in str(exc.value)


class TestQualityGateDecision:
    def test_allowed(self):
        d = QualityGateDecision(
            decision_id="gd-001", evaluation_id="eval-001", policy_id="policy-v1",
            final_action=GateAction.ALLOW, passed_gate=True,
            rationale="All metrics passed thresholds",
        )
        assert d.passed_gate is True

    def test_blocked(self):
        d = QualityGateDecision(
            decision_id="gd-002", evaluation_id="eval-001", policy_id="policy-v1",
            final_action=GateAction.BLOCK, passed_gate=False,
            failed_metric_names=["faithfulness"],
            failed_mandatory_checks=["no_pii"],
            rationale="Faithfulness below threshold and PII detected",
        )
        assert d.final_action == GateAction.BLOCK

    def test_escalate(self):
        d = QualityGateDecision(
            decision_id="gd-003", evaluation_id="eval-002", policy_id="policy-v1",
            final_action=GateAction.ESCALATE, passed_gate=False,
            failed_metric_names=["coherence"],
            rationale="Low confidence result requires human review",
        )
        assert d.final_action == GateAction.ESCALATE

    def test_retry(self):
        d = QualityGateDecision(
            decision_id="gd-004", evaluation_id="eval-003", policy_id="policy-v1",
            final_action=GateAction.RETRY, passed_gate=False,
            failed_metric_names=["latency"],
            rationale="Latency exceeded threshold, retrying",
        )
        assert d.final_action == GateAction.RETRY

    def test_hold(self):
        d = QualityGateDecision(
            decision_id="gd-005", evaluation_id="eval-004", policy_id="policy-v1",
            final_action=GateAction.HOLD, passed_gate=False,
            failed_metric_names=["confidence"],
            rationale="Confidence too low, holding for review",
        )
        assert d.final_action == GateAction.HOLD

    def test_empty_decision_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            QualityGateDecision(decision_id="  ", evaluation_id="e",
                                policy_id="p", final_action=GateAction.ALLOW,
                                passed_gate=True, rationale="ok")
        assert "must not be empty" in str(exc.value)

    def test_empty_evaluation_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            QualityGateDecision(decision_id="d", evaluation_id="  ",
                                policy_id="p", final_action=GateAction.ALLOW,
                                passed_gate=True, rationale="ok")
        assert "must not be empty" in str(exc.value)

    def test_empty_policy_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            QualityGateDecision(decision_id="d", evaluation_id="e",
                                policy_id="  ", final_action=GateAction.ALLOW,
                                passed_gate=True, rationale="ok")
        assert "must not be empty" in str(exc.value)

    def test_empty_rationale_raises(self):
        with pytest.raises(ValidationError) as exc:
            QualityGateDecision(decision_id="d", evaluation_id="e",
                                policy_id="p", final_action=GateAction.ALLOW,
                                passed_gate=True, rationale="  ")
        assert "rationale must not be empty" in str(exc.value)

    def test_block_without_rationale_raises(self):
        with pytest.raises(ValidationError):
            QualityGateDecision(decision_id="d", evaluation_id="e",
                                policy_id="p", final_action=GateAction.BLOCK,
                                passed_gate=False,
                                failed_metric_names=["safety"],
                                rationale="  ")

    def test_passed_gate_must_allow(self):
        with pytest.raises(ValidationError) as exc:
            QualityGateDecision(decision_id="d", evaluation_id="e",
                                policy_id="p", final_action=GateAction.BLOCK,
                                passed_gate=True, rationale="contradiction")
        assert "passed_gate must result in ALLOW action" in str(exc.value)

    def test_gate_failure_must_list_reason(self):
        with pytest.raises(ValidationError) as exc:
            QualityGateDecision(decision_id="d", evaluation_id="e",
                                policy_id="p", final_action=GateAction.BLOCK,
                                passed_gate=False,
                                rationale="Blocked but no details")
        assert "gate failure must list at least one failed metric or mandatory check" in str(exc.value)

    def test_escalate_with_rationale(self):
        d = QualityGateDecision(
            decision_id="gd-006", evaluation_id="eval-005", policy_id="policy-v1",
            final_action=GateAction.ESCALATE, passed_gate=False,
            failed_metric_names=["safety"],
            rationale="Safety score too low, escalating to human",
        )
        assert len(d.rationale) > 0


class TestSerialization:
    def test_evaluation_result_to_json(self):
        result = EvaluationResult(
            evaluation_id="eval-001", scope=EvaluationScope.OUTPUT,
            subject_id="task-42", evaluator_type="llm_judge",
            metric_results=[
                MetricResult(metric_name="accuracy", score=0.95,
                             outcome=MetricOutcome.PASS, threshold=0.8),
            ],
            aggregate_score=0.95,
        )
        json_str = result.model_dump_json()
        assert "eval-001" in json_str
        assert "accuracy" in json_str

    def test_decision_roundtrip(self):
        d = QualityGateDecision(
            decision_id="gd-001", evaluation_id="eval-001", policy_id="policy-v1",
            final_action=GateAction.ALLOW, passed_gate=True,
            rationale="All checks passed",
        )
        dumped = d.model_dump()
        assert dumped["final_action"] == "allow"
        assert dumped["passed_gate"] is True

    def test_policy_roundtrip(self):
        policy = QualityGatePolicy(
            policy_id="p1", applies_to_scope=EvaluationScope.RUN,
            thresholds=[
                QualityGateThreshold(metric_name="accuracy", minimum_score=0.7,
                                     mandatory=False, action_on_fail=GateAction.RETRY),
            ],
        )
        dumped = policy.model_dump()
        assert dumped["applies_to_scope"] == "run"
        assert dumped["block_on_mandatory_check_failure"] is True

    def test_metric_result_with_mandatory(self):
        m = MetricResult(metric_name="safety", score=0.0,
                         outcome=MetricOutcome.FAIL, mandatory=True)
        dumped = m.model_dump()
        assert dumped["mandatory"] is True

    def test_evidence_roundtrip(self):
        ev = EvaluationEvidence(evidence_id="ev-1", label="output",
                                content="test content", content_type="text")
        dumped = ev.model_dump()
        assert dumped["content_type"] == "text"
