import pytest
from pydantic import ValidationError
from models.feedback_quality_contract import (
    FeedbackSourceType, QualityVerdict, EvaluationMethod, SignalSeverity,
    RubricRef, QualityCriterion, EvidenceRef,
    FeedbackRecord, EvaluationRecord, QualitySignalEnvelope,
)


def make_rubric(**overrides) -> RubricRef:
    defaults = dict(rubric_id="rubric-001", rubric_name="code_quality")
    defaults.update(overrides)
    return RubricRef(**defaults)


def make_criterion(**overrides) -> QualityCriterion:
    defaults = dict(criterion_id="c-001", description="Code compiles without errors")
    defaults.update(overrides)
    return QualityCriterion(**defaults)


def make_evidence(**overrides) -> EvidenceRef:
    defaults = dict(evidence_id="ev-001", evidence_type="test_result")
    defaults.update(overrides)
    return EvidenceRef(**defaults)


def make_feedback(**overrides) -> FeedbackRecord:
    defaults = dict(
        feedback_id="fb-001", source_type=FeedbackSourceType.HUMAN,
        verdict=QualityVerdict.PASS, summary="Good work",
    )
    defaults.update(overrides)
    return FeedbackRecord(**defaults)


def make_evaluation(**overrides) -> EvaluationRecord:
    defaults = dict(
        evaluation_id="eval-001", run_id="run-001",
        method=EvaluationMethod.MANUAL_REVIEW,
        feedback=make_feedback(),
    )
    defaults.update(overrides)
    return EvaluationRecord(**defaults)


def make_envelope(**overrides) -> QualitySignalEnvelope:
    defaults = dict(envelope_id="env-001")
    defaults.update(overrides)
    return QualitySignalEnvelope(**defaults)


class TestEnums:
    def test_feedback_source_type_values(self):
        assert FeedbackSourceType.HUMAN.value == "human"
        assert FeedbackSourceType.AUTOMATED.value == "automated"
        assert FeedbackSourceType.MODEL.value == "model"
        assert FeedbackSourceType.HYBRID.value == "hybrid"
        assert len(FeedbackSourceType) == 4

    def test_quality_verdict_values(self):
        assert QualityVerdict.PASS.value == "pass"
        assert QualityVerdict.PARTIAL.value == "partial"
        assert QualityVerdict.FAIL.value == "fail"
        assert QualityVerdict.UNKNOWN.value == "unknown"
        assert len(QualityVerdict) == 4

    def test_evaluation_method_values(self):
        assert EvaluationMethod.RUBRIC.value == "rubric"
        assert EvaluationMethod.HEURISTIC.value == "heuristic"
        assert EvaluationMethod.MODEL_JUDGE.value == "model_judge"
        assert EvaluationMethod.MANUAL_REVIEW.value == "manual_review"
        assert len(EvaluationMethod) == 4

    def test_signal_severity_values(self):
        assert SignalSeverity.LOW.value == "low"
        assert SignalSeverity.MEDIUM.value == "medium"
        assert SignalSeverity.HIGH.value == "high"
        assert SignalSeverity.CRITICAL.value == "critical"
        assert len(SignalSeverity) == 4


class TestRubricRef:
    def test_valid(self):
        r = make_rubric()
        assert r.rubric_id == "rubric-001"

    def test_with_version(self):
        r = make_rubric(version="2.0")
        assert r.version == "2.0"

    def test_blank_rubric_id_raises(self):
        with pytest.raises(ValidationError):
            make_rubric(rubric_id="")

    def test_blank_rubric_name_raises(self):
        with pytest.raises(ValidationError):
            make_rubric(rubric_name="")


class TestQualityCriterion:
    def test_valid(self):
        c = make_criterion()
        assert c.criterion_id == "c-001"

    def test_with_score_and_passed(self):
        c = make_criterion(score=0.9, passed=True)
        assert c.score == 0.9
        assert c.passed is True

    def test_all_defaults_none(self):
        c = make_criterion()
        assert c.score is None
        assert c.passed is None

    def test_score_at_zero(self):
        c = make_criterion(score=0.0)
        assert c.score == 0.0

    def test_score_at_one(self):
        c = make_criterion(score=1.0)
        assert c.score == 1.0

    def test_score_below_zero_raises(self):
        with pytest.raises(ValidationError, match="score"):
            make_criterion(score=-0.1)

    def test_score_above_one_raises(self):
        with pytest.raises(ValidationError, match="score"):
            make_criterion(score=1.1)

    def test_blank_criterion_id_raises(self):
        with pytest.raises(ValidationError):
            make_criterion(criterion_id="")

    def test_blank_description_raises(self):
        with pytest.raises(ValidationError):
            make_criterion(description="")

    def test_criteria_order_preserved(self):
        criteria = [
            make_criterion(criterion_id="c-3"),
            make_criterion(criterion_id="c-1"),
            make_criterion(criterion_id="c-2"),
        ]
        assert [c.criterion_id for c in criteria] == ["c-3", "c-1", "c-2"]


class TestEvidenceRef:
    def test_valid(self):
        e = make_evidence()
        assert e.evidence_id == "ev-001"

    def test_with_source_and_hash(self):
        e = make_evidence(source_ref="test://output-1", evidence_hash="sha256:abc")
        assert e.source_ref == "test://output-1"
        assert e.evidence_hash == "sha256:abc"

    def test_blank_evidence_id_raises(self):
        with pytest.raises(ValidationError):
            make_evidence(evidence_id="")

    def test_blank_evidence_type_raises(self):
        with pytest.raises(ValidationError):
            make_evidence(evidence_type="")

    def test_evidence_order_preserved(self):
        refs = [
            make_evidence(evidence_id="e-3"),
            make_evidence(evidence_id="e-1"),
        ]
        assert [e.evidence_id for e in refs] == ["e-3", "e-1"]


class TestFeedbackRecord:
    def test_valid(self):
        fb = make_feedback()
        assert fb.feedback_id == "fb-001"

    def test_all_source_types(self):
        for s in FeedbackSourceType:
            fb = make_feedback(source_type=s)
            assert fb.source_type == s

    def test_all_verdicts(self):
        for v in QualityVerdict:
            fb = make_feedback(verdict=v)
            assert fb.verdict == v

    def test_all_severities(self):
        for s in SignalSeverity:
            fb = make_feedback(severity=s)
            assert fb.severity == s

    def test_default_severity(self):
        fb = make_feedback()
        assert fb.severity == SignalSeverity.LOW

    def test_with_comments(self):
        fb = make_feedback(comments="Needs more error handling")
        assert fb.comments == "Needs more error handling"

    def test_with_score(self):
        fb = make_feedback(score=0.85)
        assert fb.score == 0.85

    def test_score_at_zero(self):
        fb = make_feedback(score=0.0)
        assert fb.score == 0.0

    def test_score_at_one(self):
        fb = make_feedback(score=1.0)
        assert fb.score == 1.0

    def test_score_below_zero_raises(self):
        with pytest.raises(ValidationError, match="score"):
            make_feedback(score=-0.01)

    def test_score_above_one_raises(self):
        with pytest.raises(ValidationError, match="score"):
            make_feedback(score=1.01)

    def test_with_criteria_and_evidence(self):
        fb = make_feedback(
            criteria=[make_criterion()],
            evidence_refs=[make_evidence()],
            rubric_ref=make_rubric(),
        )
        assert len(fb.criteria) == 1
        assert len(fb.evidence_refs) == 1
        assert fb.rubric_ref.rubric_id == "rubric-001"

    def test_blank_feedback_id_raises(self):
        with pytest.raises(ValidationError):
            make_feedback(feedback_id="")

    def test_blank_summary_raises(self):
        with pytest.raises(ValidationError):
            make_feedback(summary="")

    def test_pass_no_criteria_valid(self):
        fb = make_feedback()
        assert fb.verdict == QualityVerdict.PASS

    def test_pass_with_all_criteria_passed_valid(self):
        fb = make_feedback(verdict=QualityVerdict.PASS, criteria=[
            make_criterion(criterion_id="c-1", passed=True),
            make_criterion(criterion_id="c-2", passed=True),
        ])
        assert fb.verdict == QualityVerdict.PASS

    def test_pass_with_none_passed_raises(self):
        with pytest.raises(ValidationError, match="PASS"):
            make_feedback(verdict=QualityVerdict.PASS, criteria=[
                make_criterion(criterion_id="c-1", passed=False),
                make_criterion(criterion_id="c-2", passed=False),
            ])

    def test_fail_with_all_passed_raises(self):
        with pytest.raises(ValidationError, match="FAIL"):
            make_feedback(verdict=QualityVerdict.FAIL, criteria=[
                make_criterion(criterion_id="c-1", passed=True),
                make_criterion(criterion_id="c-2", passed=True),
            ])

    def test_fail_with_none_passed_valid(self):
        fb = make_feedback(verdict=QualityVerdict.FAIL, criteria=[
            make_criterion(criterion_id="c-1", passed=False),
            make_criterion(criterion_id="c-2", passed=False),
        ])
        assert fb.verdict == QualityVerdict.FAIL

    def test_partial_with_mixed_criteria_valid(self):
        fb = make_feedback(verdict=QualityVerdict.PARTIAL, criteria=[
            make_criterion(criterion_id="c-1", passed=True),
            make_criterion(criterion_id="c-2", passed=False),
        ])
        assert fb.verdict == QualityVerdict.PARTIAL

    def test_unknown_without_explicit_criteria_valid(self):
        fb = make_feedback(verdict=QualityVerdict.UNKNOWN)
        assert fb.verdict == QualityVerdict.UNKNOWN

    def test_unknown_with_explicit_criteria_raises(self):
        with pytest.raises(ValidationError, match="UNKNOWN"):
            make_feedback(verdict=QualityVerdict.UNKNOWN, criteria=[
                make_criterion(criterion_id="c-1", passed=True),
            ])

    def test_unknown_with_null_passed_criteria_valid(self):
        fb = make_feedback(verdict=QualityVerdict.UNKNOWN, criteria=[
            make_criterion(criterion_id="c-1"),
            make_criterion(criterion_id="c-2"),
        ])
        assert fb.verdict == QualityVerdict.UNKNOWN

    def test_fail_with_no_criteria_valid(self):
        fb = make_feedback(verdict=QualityVerdict.FAIL)
        assert fb.verdict == QualityVerdict.FAIL


class TestEvaluationRecord:
    def test_valid(self):
        ev = make_evaluation()
        assert ev.evaluation_id == "eval-001"

    def test_all_methods(self):
        pairs = [
            (EvaluationMethod.RUBRIC, FeedbackSourceType.HYBRID),
            (EvaluationMethod.HEURISTIC, FeedbackSourceType.AUTOMATED),
            (EvaluationMethod.MODEL_JUDGE, FeedbackSourceType.MODEL),
            (EvaluationMethod.MANUAL_REVIEW, FeedbackSourceType.HUMAN),
        ]
        for method, source in pairs:
            fb = make_feedback(source_type=source, verdict=QualityVerdict.PASS, summary="ok")
            ev = make_evaluation(method=method, feedback=fb)
            assert ev.method == method
            assert ev.feedback.source_type == source

    def test_with_all_links(self):
        ev = make_evaluation(
            task_id="t-001", trace_id="trace-001",
            artifact_id="art-001", model_call_id="mc-001",
            tool_call_id="tc-001", evaluator_ref="human://reviewer-42",
        )
        assert ev.task_id == "t-001"
        assert ev.trace_id == "trace-001"
        assert ev.artifact_id == "art-001"
        assert ev.model_call_id == "mc-001"
        assert ev.tool_call_id == "tc-001"
        assert ev.evaluator_ref == "human://reviewer-42"

    def test_blank_evaluation_id_raises(self):
        with pytest.raises(ValidationError):
            make_evaluation(evaluation_id="")

    def test_blank_run_id_raises(self):
        with pytest.raises(ValidationError):
            make_evaluation(run_id="")

    def test_human_source_not_with_heuristic(self):
        with pytest.raises(ValidationError, match="HUMAN"):
            EvaluationRecord(
                evaluation_id="eval-x", run_id="run-x",
                method=EvaluationMethod.HEURISTIC,
                feedback=make_feedback(source_type=FeedbackSourceType.HUMAN),
            )

    def test_human_source_with_manual_review_valid(self):
        ev = make_evaluation(method=EvaluationMethod.MANUAL_REVIEW)
        assert ev.method == EvaluationMethod.MANUAL_REVIEW

    def test_automated_source_not_with_manual_review(self):
        with pytest.raises(ValidationError, match="AUTOMATED"):
            EvaluationRecord(
                evaluation_id="eval-x", run_id="run-x",
                method=EvaluationMethod.MANUAL_REVIEW,
                feedback=make_feedback(source_type=FeedbackSourceType.AUTOMATED),
            )

    def test_automated_source_with_heuristic_valid(self):
        ev = EvaluationRecord(
            evaluation_id="eval-x", run_id="run-x",
            method=EvaluationMethod.HEURISTIC,
            feedback=make_feedback(source_type=FeedbackSourceType.AUTOMATED),
        )
        assert ev.method == EvaluationMethod.HEURISTIC

    def test_model_source_not_with_heuristic(self):
        with pytest.raises(ValidationError, match="MODEL"):
            EvaluationRecord(
                evaluation_id="eval-x", run_id="run-x",
                method=EvaluationMethod.HEURISTIC,
                feedback=make_feedback(source_type=FeedbackSourceType.MODEL),
            )

    def test_model_source_with_model_judge_valid(self):
        ev = EvaluationRecord(
            evaluation_id="eval-x", run_id="run-x",
            method=EvaluationMethod.MODEL_JUDGE,
            feedback=make_feedback(source_type=FeedbackSourceType.MODEL),
        )
        assert ev.method == EvaluationMethod.MODEL_JUDGE

    def test_hybrid_source_all_methods_valid(self):
        for m in EvaluationMethod:
            ev = EvaluationRecord(
                evaluation_id=f"eval-{m.value}", run_id="run-x",
                method=m,
                feedback=make_feedback(source_type=FeedbackSourceType.HYBRID),
            )
            assert ev.method == m


class TestQualitySignalEnvelope:
    def test_valid_empty(self):
        e = make_envelope()
        assert e.signals == []

    def test_with_signals(self):
        e = make_envelope(signals=[make_evaluation()])
        assert len(e.signals) == 1

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="")

    def test_duplicate_evaluation_ids_raises(self):
        with pytest.raises(ValidationError, match="evaluation_ids"):
            make_envelope(signals=[
                make_evaluation(evaluation_id="eval-001"),
                make_evaluation(evaluation_id="eval-001", feedback=make_feedback(feedback_id="fb-999")),
            ])

    def test_unique_evaluation_ids_valid(self):
        e = make_envelope(signals=[
            make_evaluation(evaluation_id="eval-001"),
            make_evaluation(evaluation_id="eval-002"),
        ])
        assert len(e.signals) == 2

    def test_signals_order_preserved(self):
        e = make_envelope(signals=[
            make_evaluation(evaluation_id="eval-b"),
            make_evaluation(evaluation_id="eval-a"),
        ])
        assert [s.evaluation_id for s in e.signals] == ["eval-b", "eval-a"]


class TestSerialization:
    def test_feedback_to_dict_and_back(self):
        fb = make_feedback()
        data = fb.model_dump()
        assert data["feedback_id"] == "fb-001"
        assert data["verdict"] == "pass"
        restored = FeedbackRecord(**data)
        assert restored.feedback_id == fb.feedback_id

    def test_envelope_to_dict_and_back(self):
        e = make_envelope(signals=[make_evaluation()])
        data = e.model_dump()
        assert data["envelope_id"] == "env-001"
        restored = QualitySignalEnvelope(**data)
        assert len(restored.signals) == 1


class TestIntegration:
    def test_human_review_pass_with_rubric_refs(self):
        rubric = RubricRef(rubric_id="rubric-001", rubric_name="code_quality", version="1.0")
        criteria = [
            QualityCriterion(criterion_id="c-1", description="Code compiles", score=1.0, passed=True),
            QualityCriterion(criterion_id="c-2", description="Tests pass", score=0.95, passed=True),
            QualityCriterion(criterion_id="c-3", description="No lint errors", score=0.9, passed=True),
        ]
        fb = FeedbackRecord(
            feedback_id="fb-human-pass", source_type=FeedbackSourceType.HUMAN,
            verdict=QualityVerdict.PASS, summary="Code review approved",
            comments="All checks passed", score=0.95, severity=SignalSeverity.LOW,
            criteria=criteria, rubric_ref=rubric,
        )
        ev = EvaluationRecord(
            evaluation_id="eval-human-pass", run_id="run-001", task_id="t-001",
            artifact_id="art-001", method=EvaluationMethod.MANUAL_REVIEW,
            feedback=fb, evaluator_ref="human://reviewer-alice",
        )
        env = QualitySignalEnvelope(envelope_id="env-human-pass", signals=[ev])
        assert env.signals[0].feedback.verdict == QualityVerdict.PASS
        assert env.signals[0].feedback.rubric_ref.rubric_name == "code_quality"
        assert env.signals[0].feedback.score == 0.95
        assert len(env.signals[0].feedback.criteria) == 3

    def test_model_judge_partial_evaluation(self):
        criteria = [
            QualityCriterion(criterion_id="c-1", description="Relevant to query", score=0.8, passed=True),
            QualityCriterion(criterion_id="c-2", description="Complete answer", score=0.5, passed=False),
            QualityCriterion(criterion_id="c-3", description="No hallucinations", score=0.9, passed=True),
        ]
        fb = FeedbackRecord(
            feedback_id="fb-model-partial", source_type=FeedbackSourceType.MODEL,
            verdict=QualityVerdict.PARTIAL, summary="Partially answered; missing details",
            score=0.73, severity=SignalSeverity.MEDIUM, criteria=criteria,
        )
        ev = EvaluationRecord(
            evaluation_id="eval-model-partial", run_id="run-001", task_id="t-001",
            model_call_id="mc-001", method=EvaluationMethod.MODEL_JUDGE,
            feedback=fb, evaluator_ref="model://judge-v2",
        )
        env = QualitySignalEnvelope(envelope_id="env-model-partial", signals=[ev])
        assert env.signals[0].feedback.verdict == QualityVerdict.PARTIAL
        assert env.signals[0].feedback.source_type == FeedbackSourceType.MODEL
        assert env.signals[0].method == EvaluationMethod.MODEL_JUDGE

    def test_automated_fail_with_evidence_refs(self):
        criteria = [
            QualityCriterion(criterion_id="c-1", description="File exists", score=1.0, passed=True),
            QualityCriterion(criterion_id="c-2", description="Size within limit", score=0.0, passed=False),
            QualityCriterion(criterion_id="c-3", description="No sensitive content", score=0.0, passed=False),
        ]
        evidence = [
            EvidenceRef(evidence_id="ev-size", evidence_type="file_check",
                        source_ref="check://size-limit", evidence_hash="sha256:s1"),
            EvidenceRef(evidence_id="ev-sensitive", evidence_type="scan_result",
                        source_ref="scan://secret-detection", evidence_hash="sha256:s2"),
        ]
        fb = FeedbackRecord(
            feedback_id="fb-auto-fail", source_type=FeedbackSourceType.AUTOMATED,
            verdict=QualityVerdict.FAIL, summary="Automated checks failed",
            score=0.33, severity=SignalSeverity.HIGH,
            criteria=criteria, evidence_refs=evidence,
        )
        ev = EvaluationRecord(
            evaluation_id="eval-auto-fail", run_id="run-001", task_id="t-001",
            artifact_id="art-001", tool_call_id="tc-001",
            method=EvaluationMethod.HEURISTIC, feedback=fb,
        )
        env = QualitySignalEnvelope(envelope_id="env-auto-fail", signals=[ev])
        assert env.signals[0].feedback.verdict == QualityVerdict.FAIL
        assert len(env.signals[0].feedback.evidence_refs) == 2
        assert env.signals[0].feedback.severity == SignalSeverity.HIGH

    def test_hybrid_review_with_mixed_criteria_outcomes(self):
        criteria = [
            QualityCriterion(criterion_id="c-1", description="Functional correctness", score=0.9, passed=True),
            QualityCriterion(criterion_id="c-2", description="Code style", score=0.6, passed=False),
            QualityCriterion(criterion_id="c-3", description="Documentation", score=0.7, passed=True),
            QualityCriterion(criterion_id="c-4", description="Performance", score=0.4, passed=False),
        ]
        fb = FeedbackRecord(
            feedback_id="fb-hybrid", source_type=FeedbackSourceType.HYBRID,
            verdict=QualityVerdict.PARTIAL, summary="Mixed results: functional but needs style and perf work",
            score=0.65, severity=SignalSeverity.MEDIUM, criteria=criteria,
        )
        ev = EvaluationRecord(
            evaluation_id="eval-hybrid", run_id="run-001", task_id="t-001",
            artifact_id="art-001", method=EvaluationMethod.RUBRIC,
            feedback=fb, evaluator_ref="hybrid://auto+human",
        )
        env = QualitySignalEnvelope(envelope_id="env-hybrid", signals=[ev])
        assert env.signals[0].feedback.verdict == QualityVerdict.PARTIAL
        assert env.signals[0].feedback.source_type == FeedbackSourceType.HYBRID
        assert env.signals[0].method == EvaluationMethod.RUBRIC

    def test_unknown_verdict_needing_more_information(self):
        fb = FeedbackRecord(
            feedback_id="fb-unknown", source_type=FeedbackSourceType.AUTOMATED,
            verdict=QualityVerdict.UNKNOWN, summary="Insufficient data to evaluate",
            severity=SignalSeverity.LOW,
        )
        ev = EvaluationRecord(
            evaluation_id="eval-unknown", run_id="run-001", task_id="t-001",
            method=EvaluationMethod.HEURISTIC, feedback=fb,
        )
        env = QualitySignalEnvelope(envelope_id="env-unknown", signals=[ev])
        assert env.signals[0].feedback.verdict == QualityVerdict.UNKNOWN
        assert env.signals[0].feedback.criteria == []
