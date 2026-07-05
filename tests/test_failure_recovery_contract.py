import pytest
from pydantic import ValidationError
from models.failure_recovery_contract import (
    FailureCategory, FailureSeverity, Recoverability, RecoveryAction, ExceptionOrigin,
    FailureCauseRef, RetryPolicyRef, FailureRecord,
    RecoveryDecisionRecord, FailureDecisionEnvelope,
)


def make_cause(**overrides) -> FailureCauseRef:
    defaults = dict(cause_id="cause-001", cause_type="timeout")
    defaults.update(overrides)
    return FailureCauseRef(**defaults)


def make_retry_policy(**overrides) -> RetryPolicyRef:
    defaults = dict(policy_id="rp-001", policy_name="default_retry")
    defaults.update(overrides)
    return RetryPolicyRef(**defaults)


def make_failure(**overrides) -> FailureRecord:
    defaults = dict(failure_id="fail-001", category=FailureCategory.TOOL,
                    severity=FailureSeverity.HIGH, origin=ExceptionOrigin.TOOL,
                    summary="Tool read_file timed out")
    defaults.update(overrides)
    return FailureRecord(**defaults)


def make_decision(**overrides) -> RecoveryDecisionRecord:
    defaults = dict(decision_id="dec-001", failure_id="fail-001",
                    action=RecoveryAction.RETRY, reason="Transient error, retry allowed")
    defaults.update(overrides)
    return RecoveryDecisionRecord(**defaults)


def make_envelope(**overrides) -> FailureDecisionEnvelope:
    defaults = dict(envelope_id="env-001", failure=make_failure(),
                    recovery_decision=make_decision())
    defaults.update(overrides)
    return FailureDecisionEnvelope(**defaults)


class TestEnums:
    def test_failure_category_values(self):
        assert FailureCategory.TOOL.value == "tool"
        assert FailureCategory.MODEL.value == "model"
        assert FailureCategory.POLICY.value == "policy"
        assert FailureCategory.VALIDATION.value == "validation"
        assert FailureCategory.CHECKPOINT.value == "checkpoint"
        assert FailureCategory.STORAGE.value == "storage"
        assert FailureCategory.NETWORK.value == "network"
        assert FailureCategory.AUTH.value == "auth"
        assert FailureCategory.SYSTEM.value == "system"
        assert FailureCategory.UNKNOWN.value == "unknown"
        assert len(FailureCategory) == 10

    def test_failure_severity_values(self):
        assert FailureSeverity.LOW.value == "low"
        assert FailureSeverity.MEDIUM.value == "medium"
        assert FailureSeverity.HIGH.value == "high"
        assert FailureSeverity.CRITICAL.value == "critical"
        assert len(FailureSeverity) == 4

    def test_recoverability_values(self):
        assert Recoverability.RECOVERABLE.value == "recoverable"
        assert Recoverability.PARTIALLY_RECOVERABLE.value == "partially_recoverable"
        assert Recoverability.NON_RECOVERABLE.value == "non_recoverable"
        assert Recoverability.UNKNOWN.value == "unknown"
        assert len(Recoverability) == 4

    def test_recovery_action_values(self):
        assert RecoveryAction.RETRY.value == "retry"
        assert RecoveryAction.SKIP.value == "skip"
        assert RecoveryAction.ESCALATE.value == "escalate"
        assert RecoveryAction.PAUSE.value == "pause"
        assert RecoveryAction.ABORT.value == "abort"
        assert RecoveryAction.RESTART_FROM_CHECKPOINT.value == "restart_from_checkpoint"
        assert len(RecoveryAction) == 6

    def test_exception_origin_values(self):
        assert ExceptionOrigin.AGENT.value == "agent"
        assert ExceptionOrigin.TOOL.value == "tool"
        assert ExceptionOrigin.MODEL.value == "model"
        assert ExceptionOrigin.USER.value == "user"
        assert ExceptionOrigin.SYSTEM.value == "system"
        assert ExceptionOrigin.EXTERNAL_SERVICE.value == "external_service"
        assert len(ExceptionOrigin) == 6


class TestFailureCauseRef:
    def test_valid(self):
        c = make_cause()
        assert c.cause_id == "cause-001"

    def test_with_detail_ref(self):
        c = make_cause(detail_ref="trace://t-001/step-3")
        assert c.detail_ref == "trace://t-001/step-3"

    def test_blank_cause_id_raises(self):
        with pytest.raises(ValidationError):
            make_cause(cause_id="")

    def test_blank_cause_type_raises(self):
        with pytest.raises(ValidationError):
            make_cause(cause_type="")

    def test_causes_order_preserved(self):
        causes = [make_cause(cause_id="c-2"), make_cause(cause_id="c-1")]
        assert [c.cause_id for c in causes] == ["c-2", "c-1"]


class TestRetryPolicyRef:
    def test_valid(self):
        r = make_retry_policy()
        assert r.policy_id == "rp-001"

    def test_with_max_attempts(self):
        r = make_retry_policy(max_attempts=3)
        assert r.max_attempts == 3

    def test_max_attempts_zero_valid(self):
        r = make_retry_policy(max_attempts=0)
        assert r.max_attempts == 0

    def test_max_attempts_negative_raises(self):
        with pytest.raises(ValidationError, match="max_attempts"):
            make_retry_policy(max_attempts=-1)

    def test_blank_policy_id_raises(self):
        with pytest.raises(ValidationError):
            make_retry_policy(policy_id="")

    def test_blank_policy_name_raises(self):
        with pytest.raises(ValidationError):
            make_retry_policy(policy_name="")


class TestFailureRecord:
    def test_valid(self):
        f = make_failure()
        assert f.failure_id == "fail-001"

    def test_all_categories(self):
        for c in FailureCategory:
            f = make_failure(category=c)
            assert f.category == c

    def test_all_severities(self):
        for s in FailureSeverity:
            f = make_failure(severity=s)
            assert f.severity == s

    def test_all_origins(self):
        for o in ExceptionOrigin:
            f = make_failure(origin=o)
            assert f.origin == o

    def test_all_recoverabilities(self):
        for r in Recoverability:
            f = make_failure(recoverability=r)
            assert f.recoverability == r

    def test_default_recoverability(self):
        f = make_failure()
        assert f.recoverability == Recoverability.UNKNOWN

    def test_with_description(self):
        f = make_failure(description="Connection to API timed out after 30s")
        assert f.description == "Connection to API timed out after 30s"

    def test_with_causes(self):
        f = make_failure(causes=[make_cause()])
        assert len(f.causes) == 1

    def test_with_all_related_refs(self):
        f = make_failure(related_run_id="run-001", related_task_id="t-001",
                         related_tool_call_id="tc-001", related_model_call_id="mc-001",
                         related_checkpoint_id="chk-001")
        assert f.related_run_id == "run-001"
        assert f.related_task_id == "t-001"
        assert f.related_tool_call_id == "tc-001"
        assert f.related_model_call_id == "mc-001"
        assert f.related_checkpoint_id == "chk-001"

    def test_blank_failure_id_raises(self):
        with pytest.raises(ValidationError):
            make_failure(failure_id="")

    def test_blank_summary_raises(self):
        with pytest.raises(ValidationError):
            make_failure(summary="")


class TestRecoveryDecisionRecord:
    def test_valid(self):
        d = make_decision()
        assert d.decision_id == "dec-001"

    def test_all_actions(self):
        for a in RecoveryAction:
            kwargs = dict(action=a, reason="test")
            if a == RecoveryAction.RESTART_FROM_CHECKPOINT:
                kwargs["next_checkpoint_id"] = "chk-002"
            d = make_decision(**kwargs)
            assert d.action == a

    def test_with_retry_policy(self):
        d = make_decision(retry_policy_ref=make_retry_policy())
        assert d.retry_policy_ref.policy_id == "rp-001"

    def test_requires_human_review_default_false(self):
        d = make_decision()
        assert d.requires_human_review is False

    def test_requires_human_review_true(self):
        d = make_decision(requires_human_review=True)
        assert d.requires_human_review is True

    def test_with_next_checkpoint_and_step(self):
        d = make_decision(next_checkpoint_id="chk-002", next_step_ref="step-003")
        assert d.next_checkpoint_id == "chk-002"
        assert d.next_step_ref == "step-003"

    def test_restart_checkpoint_needs_next_checkpoint_id(self):
        with pytest.raises(ValidationError, match="RESTART_FROM_CHECKPOINT"):
            make_decision(action=RecoveryAction.RESTART_FROM_CHECKPOINT)

    def test_restart_checkpoint_with_next_checkpoint_valid(self):
        d = make_decision(action=RecoveryAction.RESTART_FROM_CHECKPOINT, next_checkpoint_id="chk-002")
        assert d.next_checkpoint_id == "chk-002"

    def test_blank_decision_id_raises(self):
        with pytest.raises(ValidationError):
            make_decision(decision_id="")

    def test_blank_failure_id_raises(self):
        with pytest.raises(ValidationError):
            make_decision(failure_id="")

    def test_blank_reason_raises(self):
        with pytest.raises(ValidationError):
            make_decision(reason="")


class TestFailureDecisionEnvelope:
    def test_valid(self):
        e = make_envelope()
        assert e.envelope_id == "env-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="")

    def test_decision_failure_id_mismatch_raises(self):
        with pytest.raises(ValidationError, match="failure_id"):
            make_envelope(
                failure=make_failure(failure_id="fail-001"),
                recovery_decision=make_decision(failure_id="fail-999"),
            )

    def test_decision_failure_id_match_valid(self):
        e = make_envelope(
            failure=make_failure(failure_id="fail-001"),
            recovery_decision=make_decision(failure_id="fail-001"),
        )
        assert e.recovery_decision.failure_id == "fail-001"

    def test_non_recoverable_with_retry_raises(self):
        with pytest.raises(ValidationError, match="NON_RECOVERABLE"):
            make_envelope(
                failure=make_failure(recoverability=Recoverability.NON_RECOVERABLE),
                recovery_decision=make_decision(action=RecoveryAction.RETRY),
            )

    def test_non_recoverable_with_restart_checkpoint_raises(self):
        with pytest.raises(ValidationError, match="NON_RECOVERABLE"):
            make_envelope(
                failure=make_failure(recoverability=Recoverability.NON_RECOVERABLE),
                recovery_decision=make_decision(action=RecoveryAction.RESTART_FROM_CHECKPOINT, next_checkpoint_id="chk-002"),
            )

    def test_non_recoverable_with_skip_valid(self):
        e = make_envelope(
            failure=make_failure(recoverability=Recoverability.NON_RECOVERABLE),
            recovery_decision=make_decision(action=RecoveryAction.SKIP),
        )
        assert e.recovery_decision.action == RecoveryAction.SKIP

    def test_recoverable_with_retry_valid(self):
        e = make_envelope(
            failure=make_failure(recoverability=Recoverability.RECOVERABLE),
            recovery_decision=make_decision(action=RecoveryAction.RETRY),
        )
        assert e.recovery_decision.action == RecoveryAction.RETRY

    def test_restart_checkpoint_no_failure_or_decision_checkpoint_raises(self):
        with pytest.raises(ValidationError, match="RESTART_FROM_CHECKPOINT"):
            make_envelope(
                failure=make_failure(related_checkpoint_id=None),
                recovery_decision=make_decision(
                    action=RecoveryAction.RESTART_FROM_CHECKPOINT,
                    next_checkpoint_id=None,
                    failure_id="fail-001",
                ),
            )

    def test_restart_checkpoint_with_failure_checkpoint_valid(self):
        e = make_envelope(
            failure=make_failure(failure_id="fail-001", related_checkpoint_id="chk-001"),
            recovery_decision=make_decision(
                action=RecoveryAction.RESTART_FROM_CHECKPOINT,
                next_checkpoint_id="chk-002",
                failure_id="fail-001",
            ),
        )
        assert e.failure.related_checkpoint_id == "chk-001"

    def test_recoverable_with_pause_valid(self):
        e = make_envelope(
            failure=make_failure(recoverability=Recoverability.RECOVERABLE),
            recovery_decision=make_decision(action=RecoveryAction.PAUSE),
        )
        assert e.recovery_decision.action == RecoveryAction.PAUSE


class TestSerialization:
    def test_failure_to_dict_and_back(self):
        f = make_failure()
        data = f.model_dump()
        assert data["failure_id"] == "fail-001"
        assert data["category"] == "tool"
        restored = FailureRecord(**data)
        assert restored.failure_id == f.failure_id

    def test_envelope_to_dict_and_back(self):
        e = make_envelope()
        data = e.model_dump()
        assert data["envelope_id"] == "env-001"
        restored = FailureDecisionEnvelope(**data)
        assert restored.envelope_id == e.envelope_id
        assert restored.failure.failure_id == "fail-001"


class TestIntegration:
    def test_recoverable_tool_failure_with_retry(self):
        causes = [FailureCauseRef(cause_id="cause-001", cause_type="timeout",
                                  detail_ref="trace://step-3")]
        failure = FailureRecord(
            failure_id="fail-tool", category=FailureCategory.TOOL,
            severity=FailureSeverity.HIGH, origin=ExceptionOrigin.TOOL,
            summary="Tool read_file timed out after 30s",
            description="Connection to file service timed out",
            recoverability=Recoverability.RECOVERABLE,
            causes=causes,
            related_run_id="run-001", related_task_id="t-001",
            related_tool_call_id="tc-001",
        )
        retry_policy = RetryPolicyRef(policy_id="rp-default", policy_name="default_retry", max_attempts=3)
        decision = RecoveryDecisionRecord(
            decision_id="dec-tool", failure_id="fail-tool",
            action=RecoveryAction.RETRY, reason="Transient timeout, retry with backoff",
            retry_policy_ref=retry_policy,
        )
        env = FailureDecisionEnvelope(envelope_id="env-tool", failure=failure, recovery_decision=decision)
        assert env.failure.category == FailureCategory.TOOL
        assert env.failure.recoverability == Recoverability.RECOVERABLE
        assert env.recovery_decision.action == RecoveryAction.RETRY
        assert env.recovery_decision.retry_policy_ref.max_attempts == 3

    def test_non_recoverable_policy_failure_with_pause(self):
        failure = FailureRecord(
            failure_id="fail-policy", category=FailureCategory.POLICY,
            severity=FailureSeverity.CRITICAL, origin=ExceptionOrigin.SYSTEM,
            summary="Policy violation: delete on protected path",
            recoverability=Recoverability.NON_RECOVERABLE,
            related_run_id="run-001", related_task_id="t-001",
        )
        decision = RecoveryDecisionRecord(
            decision_id="dec-policy", failure_id="fail-policy",
            action=RecoveryAction.PAUSE, reason="Cannot retry policy violation, pause for human review",
            requires_human_review=True,
        )
        env = FailureDecisionEnvelope(envelope_id="env-policy", failure=failure, recovery_decision=decision)
        assert env.failure.recoverability == Recoverability.NON_RECOVERABLE
        assert env.recovery_decision.action == RecoveryAction.PAUSE
        assert env.recovery_decision.requires_human_review is True

    def test_model_failure_requiring_human_review(self):
        causes = [
            FailureCauseRef(cause_id="cause-001", cause_type="hallucination_detected"),
            FailureCauseRef(cause_id="cause-002", cause_type="low_confidence", detail_ref="model://mc-001"),
        ]
        failure = FailureRecord(
            failure_id="fail-model", category=FailureCategory.MODEL,
            severity=FailureSeverity.MEDIUM, origin=ExceptionOrigin.MODEL,
            summary="Model output failed confidence threshold",
            description="Score 0.32 below required 0.70",
            recoverability=Recoverability.UNKNOWN,
            causes=causes,
            related_run_id="run-001", related_model_call_id="mc-001",
        )
        decision = RecoveryDecisionRecord(
            decision_id="dec-model", failure_id="fail-model",
            action=RecoveryAction.ESCALATE,
            reason="Model output quality uncertain, escalate for human review",
            requires_human_review=True,
        )
        env = FailureDecisionEnvelope(envelope_id="env-model", failure=failure, recovery_decision=decision)
        assert env.failure.recoverability == Recoverability.UNKNOWN
        assert len(env.failure.causes) == 2
        assert env.recovery_decision.requires_human_review is True

    def test_validation_failure_escalating_to_abort(self):
        failure = FailureRecord(
            failure_id="fail-val", category=FailureCategory.VALIDATION,
            severity=FailureSeverity.HIGH, origin=ExceptionOrigin.AGENT,
            summary="Generated code failed security validation",
            description="SQL injection pattern detected in output",
            recoverability=Recoverability.NON_RECOVERABLE,
            related_run_id="run-001", related_task_id="t-001",
        )
        decision = RecoveryDecisionRecord(
            decision_id="dec-val", failure_id="fail-val",
            action=RecoveryAction.ABORT,
            reason="Security validation failure cannot be retried",
        )
        env = FailureDecisionEnvelope(envelope_id="env-val", failure=failure, recovery_decision=decision)
        assert env.failure.category == FailureCategory.VALIDATION
        assert env.recovery_decision.action == RecoveryAction.ABORT

    def test_checkpoint_failure_restarting_from_checkpoint(self):
        failure = FailureRecord(
            failure_id="fail-chk", category=FailureCategory.CHECKPOINT,
            severity=FailureSeverity.MEDIUM, origin=ExceptionOrigin.SYSTEM,
            summary="Checkpoint write failed mid-execution",
            recoverability=Recoverability.PARTIALLY_RECOVERABLE,
            related_run_id="run-001", related_checkpoint_id="chk-001",
        )
        decision = RecoveryDecisionRecord(
            decision_id="dec-chk", failure_id="fail-chk",
            action=RecoveryAction.RESTART_FROM_CHECKPOINT,
            reason="Previous checkpoint valid, restart from safe state",
            next_checkpoint_id="chk-001", next_step_ref="step-002",
        )
        env = FailureDecisionEnvelope(envelope_id="env-chk", failure=failure, recovery_decision=decision)
        assert env.failure.category == FailureCategory.CHECKPOINT
        assert env.recovery_decision.action == RecoveryAction.RESTART_FROM_CHECKPOINT
        assert env.recovery_decision.next_checkpoint_id == "chk-001"
        assert env.recovery_decision.next_step_ref == "step-002"
