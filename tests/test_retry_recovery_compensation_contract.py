import pytest
from datetime import datetime, timedelta
from models.retry_recovery_compensation_contract import (
    FailureCategory, RetryStrategy, RecoveryMode,
    CompensationStatus, FailureDisposition,
    FailureRecord, RetryPolicyRecord, RetryAttemptRecord,
    RecoveryPlanRecord, RecoveryExecutionRecord,
    CompensationActionRecord, CompensationPlanRecord,
    RetryRecoveryCompensationEnvelope,
)


def make_failure(**kw):
    return FailureRecord(
        failure_id=kw.get("fid", "fail-001"),
        scope_ref=kw.get("ref", "task-001"),
        failure_category=kw.get("cat", FailureCategory.transient_error),
        failure_summary=kw.get("summary", "Connection reset by peer"),
        retryable=kw.get("retryable", True),
        side_effects_present=kw.get("sidefx", False),
        unknown_state=kw.get("unknown", False),
        evidence_refs=kw.get("evidence", ["err-001"]),
    )


def make_retry_policy(**kw):
    return RetryPolicyRecord(
        retry_policy_id=kw.get("rpid", "rp-001"),
        failure_category=kw.get("cat"),
        retry_strategy=kw.get("strategy", RetryStrategy.exponential_backoff),
        max_attempts=kw.get("max", 3),
        base_delay_ms=kw.get("delay", 1000),
        backoff_scale_factor=kw.get("scale", 2.0),
        max_delay_ms=kw.get("maxdelay"),
        jitter_enabled=kw.get("jitter", False),
        stop_conditions=kw.get("stops", []),
    )


def make_attempt(**kw):
    return RetryAttemptRecord(
        retry_attempt_id=kw.get("raid", "ra-001"),
        failure_id=kw.get("fid", "fail-001"),
        attempt_number=kw.get("num", 1),
        scheduled_delay_ms=kw.get("delay", 1000),
        started_at=kw.get("started"),
        ended_at=kw.get("ended"),
        result_status=kw.get("result", "success"),
        result_summary=kw.get("summary", "Recovered"),
    )


def make_recovery_plan(**kw):
    return RecoveryPlanRecord(
        recovery_plan_id=kw.get("rpid", "rp-001"),
        failure_id=kw.get("fid", "fail-001"),
        recovery_mode=kw.get("mode", RecoveryMode.resume_from_checkpoint),
        checkpoint_ref=kw.get("ckpt", "ckpt-001"),
        intent_state_ref=kw.get("intent"),
        prerequisites=kw.get("prereqs", []),
        requires_approval=kw.get("approval", False),
        recovery_goal=kw.get("goal", "Resume from last checkpoint"),
    )


def make_recovery_exec(**kw):
    return RecoveryExecutionRecord(
        recovery_execution_id=kw.get("reid", "re-001"),
        recovery_plan_id=kw.get("rpid", "rp-001"),
        executor_ref=kw.get("executor", "agent-alpha"),
        started_at=kw.get("started"),
        ended_at=kw.get("ended"),
        recovery_status=kw.get("status", "completed"),
        residual_risks=kw.get("risks", []),
        notes=kw.get("notes"),
    )


def make_comp_action(**kw):
    return CompensationActionRecord(
        compensation_action_id=kw.get("caid", "ca-001"),
        failure_id=kw.get("fid", "fail-001"),
        action_ref=kw.get("actref", "rollback_db_write"),
        target_side_effect_ref=kw.get("target", "db-write-001"),
        execution_order=kw.get("order", 0),
        retry_policy_ref=kw.get("rpref"),
        status=kw.get("status", CompensationStatus.completed),
        action_notes=kw.get("notes", "Rolled back"),
    )


def make_comp_plan(**kw):
    return CompensationPlanRecord(
        compensation_plan_id=kw.get("cpid", "cp-001"),
        failure_id=kw.get("fid", "fail-001"),
        actions=kw.get("actions", []),
        plan_status=kw.get("status", CompensationStatus.planned),
        escalation_on_failure=kw.get("escalate", False),
        completed_at=kw.get("completed"),
    )


def make_envelope(**kw):
    f = kw.get("failure") or make_failure()
    rp = kw.get("retry_policy")
    attempts = kw.get("retry_attempts", [])
    rec_plan = kw.get("recovery_plan")
    rec_exec = kw.get("recovery_exec")
    comp_plan = kw.get("comp_plan")
    disp = kw.get("disp")
    risks = kw.get("risks", [])
    return RetryRecoveryCompensationEnvelope(
        envelope_id=kw.get("eid", "env-retry-001"),
        failure=f,
        retry_policy=rp,
        retry_attempts=attempts,
        recovery_plan=rec_plan,
        recovery_execution=rec_exec,
        compensation_plan=comp_plan,
        failure_disposition=disp,
        residual_risks=risks,
    )


class TestFailureCategory:
    def test_all_values(self):
        assert len(FailureCategory) == 8
        assert FailureCategory.transient_error.value == "transient_error"
        assert FailureCategory.timeout.value == "timeout"
        assert FailureCategory.dependency_failure.value == "dependency_failure"
        assert FailureCategory.validation_failure.value == "validation_failure"
        assert FailureCategory.policy_block.value == "policy_block"
        assert FailureCategory.partial_side_effect.value == "partial_side_effect"
        assert FailureCategory.unknown_state.value == "unknown_state"
        assert FailureCategory.terminal_error.value == "terminal_error"


class TestRetryStrategy:
    def test_all_values(self):
        assert len(RetryStrategy) == 5
        assert RetryStrategy.none.value == "none"
        assert RetryStrategy.fixed.value == "fixed"
        assert RetryStrategy.linear_backoff.value == "linear_backoff"
        assert RetryStrategy.exponential_backoff.value == "exponential_backoff"
        assert RetryStrategy.manual_retry.value == "manual_retry"


class TestRecoveryMode:
    def test_all_values(self):
        assert len(RecoveryMode) == 6
        assert RecoveryMode.resume_from_checkpoint.value == "resume_from_checkpoint"
        assert RecoveryMode.replay_last_step.value == "replay_last_step"
        assert RecoveryMode.replay_from_intent.value == "replay_from_intent"
        assert RecoveryMode.handoff_recovery.value == "handoff_recovery"
        assert RecoveryMode.manual_recovery.value == "manual_recovery"
        assert RecoveryMode.no_recovery.value == "no_recovery"


class TestCompensationStatus:
    def test_all_values(self):
        assert len(CompensationStatus) == 6
        assert CompensationStatus.not_required.value == "not_required"
        assert CompensationStatus.planned.value == "planned"
        assert CompensationStatus.in_progress.value == "in_progress"
        assert CompensationStatus.completed.value == "completed"
        assert CompensationStatus.failed.value == "failed"
        assert CompensationStatus.escalated.value == "escalated"


class TestFailureDisposition:
    def test_all_values(self):
        assert len(FailureDisposition) == 6
        assert FailureDisposition.retrying.value == "retrying"
        assert FailureDisposition.recovered.value == "recovered"
        assert FailureDisposition.compensated.value == "compensated"
        assert FailureDisposition.escalated.value == "escalated"
        assert FailureDisposition.aborted.value == "aborted"
        assert FailureDisposition.terminated.value == "terminated"


class TestFailureRecord:
    def test_valid(self):
        f = make_failure()
        assert f.failure_id == "fail-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValueError):
            make_failure(fid="   ")

    def test_blank_scope_ref_raises(self):
        with pytest.raises(ValueError):
            make_failure(ref="   ")

    def test_blank_summary_raises(self):
        with pytest.raises(ValueError):
            make_failure(summary="   ")

    def test_default_fields(self):
        f = FailureRecord(
            failure_id="f-001",
            scope_ref="task-001",
            failure_category=FailureCategory.timeout,
            failure_summary="Timed out",
        )
        assert f.retryable is False
        assert f.side_effects_present is False
        assert f.unknown_state is False
        assert f.evidence_refs == []


class TestRetryPolicyRecord:
    def test_valid(self):
        rp = make_retry_policy()
        assert rp.retry_policy_id == "rp-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValueError):
            make_retry_policy(rpid="   ")

    def test_none_strategy_requires_zero_attempts(self):
        with pytest.raises(ValueError):
            make_retry_policy(strategy=RetryStrategy.none, max=1)

    def test_none_strategy_zero_attempts_ok(self):
        rp = make_retry_policy(strategy=RetryStrategy.none, max=0)
        assert rp.retry_strategy == RetryStrategy.none

    def test_manual_retry_requires_positive_attempts(self):
        with pytest.raises(ValueError):
            make_retry_policy(strategy=RetryStrategy.manual_retry, max=0)

    def test_manual_retry_with_attempts_ok(self):
        rp = make_retry_policy(strategy=RetryStrategy.manual_retry, max=3)
        assert rp.max_attempts == 3


class TestRetryAttemptRecord:
    def test_valid(self):
        a = make_attempt()
        assert a.retry_attempt_id == "ra-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValueError):
            make_attempt(raid="   ")

    def test_blank_failure_id_raises(self):
        with pytest.raises(ValueError):
            make_attempt(fid="   ")


class TestRecoveryPlanRecord:
    def test_valid(self):
        rp = make_recovery_plan()
        assert rp.recovery_plan_id == "rp-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValueError):
            make_recovery_plan(rpid="   ")

    def test_blank_failure_id_raises(self):
        with pytest.raises(ValueError):
            make_recovery_plan(fid="   ")

    def test_checkpoint_recovery_requires_ref(self):
        with pytest.raises(ValueError):
            make_recovery_plan(mode=RecoveryMode.resume_from_checkpoint, ckpt=None)

    def test_checkpoint_recovery_with_ref_ok(self):
        rp = make_recovery_plan(mode=RecoveryMode.resume_from_checkpoint, ckpt="ckpt-001")
        assert rp.checkpoint_ref == "ckpt-001"

    def test_intent_replay_requires_intent_ref(self):
        with pytest.raises(ValueError):
            make_recovery_plan(mode=RecoveryMode.replay_from_intent, ckpt=None, intent=None)

    def test_intent_replay_with_ref_ok(self):
        rp = make_recovery_plan(mode=RecoveryMode.replay_from_intent, ckpt=None, intent="intent-001")
        assert rp.intent_state_ref == "intent-001"

    def test_replay_last_step_no_ref_needed(self):
        rp = make_recovery_plan(mode=RecoveryMode.replay_last_step, ckpt=None)
        assert rp.recovery_mode == RecoveryMode.replay_last_step


class TestRecoveryExecutionRecord:
    def test_valid(self):
        r = make_recovery_exec()
        assert r.recovery_execution_id == "re-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValueError):
            make_recovery_exec(reid="   ")

    def test_blank_plan_id_raises(self):
        with pytest.raises(ValueError):
            make_recovery_exec(rpid="   ")


class TestCompensationActionRecord:
    def test_valid(self):
        a = make_comp_action()
        assert a.compensation_action_id == "ca-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValueError):
            make_comp_action(caid="   ")

    def test_blank_failure_id_raises(self):
        with pytest.raises(ValueError):
            make_comp_action(fid="   ")

    def test_blank_action_ref_raises(self):
        with pytest.raises(ValueError):
            make_comp_action(actref="   ")

    def test_in_progress_requires_notes(self):
        with pytest.raises(ValueError):
            make_comp_action(status=CompensationStatus.in_progress, notes=None)

    def test_failed_requires_notes(self):
        with pytest.raises(ValueError):
            make_comp_action(status=CompensationStatus.failed, notes=None)

    def test_completed_allows_no_notes(self):
        a = make_comp_action(status=CompensationStatus.completed, notes=None)
        assert a.status == CompensationStatus.completed


class TestCompensationPlanRecord:
    def test_valid(self):
        cp = make_comp_plan()
        assert cp.compensation_plan_id == "cp-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValueError):
            make_comp_plan(cpid="   ")

    def test_blank_failure_id_raises(self):
        with pytest.raises(ValueError):
            make_comp_plan(fid="   ")

    def test_deterministic_execution_order(self):
        a1 = make_comp_action(caid="ca-1", order=0)
        a2 = make_comp_action(caid="ca-2", order=0)
        with pytest.raises(ValueError):
            make_comp_plan(actions=[a1, a2])

    def test_unique_orders_ok(self):
        a1 = make_comp_action(caid="ca-1", order=0)
        a2 = make_comp_action(caid="ca-2", order=1)
        cp = make_comp_plan(actions=[a1, a2], status=CompensationStatus.in_progress)
        assert len(cp.actions) == 2

    def test_actions_present_not_required_raises(self):
        a = make_comp_action()
        with pytest.raises(ValueError):
            make_comp_plan(actions=[a], status=CompensationStatus.not_required)


class TestRetryRecoveryCompensationEnvelope:
    def test_valid(self):
        e = make_envelope()
        assert e.envelope_id == "env-retry-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValueError):
            make_envelope(eid="   ")

    def test_none_strategy_no_attempts(self):
        rp = make_retry_policy(strategy=RetryStrategy.none, max=0)
        a = make_attempt()
        with pytest.raises(ValueError):
            make_envelope(retry_policy=rp, retry_attempts=[a])

    def test_none_strategy_no_attempts_ok(self):
        rp = make_retry_policy(strategy=RetryStrategy.none, max=0)
        e = make_envelope(retry_policy=rp, retry_attempts=[])
        assert len(e.retry_attempts) == 0

    def test_unknown_state_blocks_recovered(self):
        f = make_failure(unknown=True)
        with pytest.raises(ValueError):
            make_envelope(failure=f, disp=FailureDisposition.recovered)

    def test_unknown_state_blocks_compensated(self):
        f = make_failure(unknown=True)
        with pytest.raises(ValueError):
            make_envelope(failure=f, disp=FailureDisposition.compensated)

    def test_unknown_state_allows_escalated(self):
        f = make_failure(unknown=True)
        e = make_envelope(failure=f, disp=FailureDisposition.escalated)
        assert e.failure_disposition == FailureDisposition.escalated

    def test_compensation_failed_not_completed(self):
        a = make_comp_action(caid="ca-1", status=CompensationStatus.failed, notes="Failed", order=0)
        cp = make_comp_plan(actions=[a], status=CompensationStatus.completed)
        f = make_failure(sidefx=True)
        with pytest.raises(ValueError):
            make_envelope(failure=f, comp_plan=cp)

    def test_compensation_failed_allowed_as_failed(self):
        a = make_comp_action(caid="ca-1", status=CompensationStatus.failed, notes="Failed", order=0)
        cp = make_comp_plan(actions=[a], status=CompensationStatus.failed)
        f = make_failure(sidefx=True)
        e = make_envelope(failure=f, comp_plan=cp)
        assert e.compensation_plan.plan_status == CompensationStatus.failed


class TestExampleScenarios:
    def test_transient_dependency_failure_retried_successfully(self):
        f = FailureRecord(
            failure_id="fail-transient",
            scope_ref="task-dep-call",
            failure_category=FailureCategory.transient_error,
            failure_summary="Dependency service returned 503",
            retryable=True,
            evidence_refs=["http-503-001"],
        )
        rp = RetryPolicyRecord(
            retry_policy_id="rp-transient",
            failure_category=FailureCategory.transient_error,
            retry_strategy=RetryStrategy.exponential_backoff,
            max_attempts=3,
            base_delay_ms=500,
            backoff_scale_factor=2.0,
            max_delay_ms=10000,
            jitter_enabled=True,
        )
        a1 = RetryAttemptRecord(
            retry_attempt_id="ra-trans-1", failure_id="fail-transient",
            attempt_number=1, scheduled_delay_ms=500,
            started_at=datetime.now(), ended_at=datetime.now(),
            result_status="success", result_summary="Retry succeeded",
        )
        e = RetryRecoveryCompensationEnvelope(
            envelope_id="env-transient",
            failure=f,
            retry_policy=rp,
            retry_attempts=[a1],
            failure_disposition=FailureDisposition.recovered,
        )
        assert e.retry_policy.retry_strategy == RetryStrategy.exponential_backoff
        assert len(e.retry_attempts) == 1

    def test_timeout_recovered_from_checkpoint(self):
        f = FailureRecord(
            failure_id="fail-timeout",
            scope_ref="task-long-run",
            failure_category=FailureCategory.timeout,
            failure_summary="Execution timed out after 30s",
            retryable=False,
            side_effects_present=True,
        )
        rp = RetryPolicyRecord(
            retry_policy_id="rp-timeout",
            failure_category=FailureCategory.timeout,
            retry_strategy=RetryStrategy.none,
            max_attempts=0,
        )
        plan = RecoveryPlanRecord(
            recovery_plan_id="rec-plan-timeout",
            failure_id="fail-timeout",
            recovery_mode=RecoveryMode.resume_from_checkpoint,
            checkpoint_ref="ckpt-step-004",
            recovery_goal="Resume from last known checkpoint",
        )
        exec_rec = RecoveryExecutionRecord(
            recovery_execution_id="rec-exec-timeout",
            recovery_plan_id="rec-plan-timeout",
            executor_ref="agent-alpha",
            recovery_status="completed",
            residual_risks=["Possible duplicate writes"],
        )
        e = RetryRecoveryCompensationEnvelope(
            envelope_id="env-timeout",
            failure=f,
            retry_policy=rp,
            recovery_plan=plan,
            recovery_execution=exec_rec,
            failure_disposition=FailureDisposition.recovered,
        )
        assert e.recovery_plan.checkpoint_ref == "ckpt-step-004"
        assert e.recovery_plan.recovery_mode == RecoveryMode.resume_from_checkpoint

    def test_partial_side_effect_requiring_compensation(self):
        f = FailureRecord(
            failure_id="fail-sidefx",
            scope_ref="task-db-write",
            failure_category=FailureCategory.partial_side_effect,
            failure_summary="DB write succeeded but subsequent step failed",
            retryable=False,
            side_effects_present=True,
        )
        a1 = CompensationActionRecord(
            compensation_action_id="ca-rollback",
            failure_id="fail-sidefx",
            action_ref="rollback_db_write",
            target_side_effect_ref="db-write-003",
            execution_order=0,
            retry_policy_ref="rp-comp-retry",
            status=CompensationStatus.completed,
            action_notes="Rolled back write #003",
        )
        cp = CompensationPlanRecord(
            compensation_plan_id="cp-sidefx",
            failure_id="fail-sidefx",
            actions=[a1],
            plan_status=CompensationStatus.completed,
            completed_at=datetime.now(),
        )
        e = RetryRecoveryCompensationEnvelope(
            envelope_id="env-sidefx",
            failure=f,
            compensation_plan=cp,
            failure_disposition=FailureDisposition.compensated,
        )
        assert len(e.compensation_plan.actions) == 1
        assert e.failure_disposition == FailureDisposition.compensated

    def test_compensation_action_failure_escalated(self):
        f = FailureRecord(
            failure_id="fail-comp-fail",
            scope_ref="task-multi-write",
            failure_category=FailureCategory.partial_side_effect,
            failure_summary="Multiple side effects, compensation failed",
            retryable=False,
            side_effects_present=True,
        )
        a1 = CompensationActionRecord(
            compensation_action_id="ca-comp-1",
            failure_id="fail-comp-fail",
            action_ref="rollback_api_call",
            target_side_effect_ref="api-call-002",
            execution_order=0,
            status=CompensationStatus.failed,
            action_notes="Compensation call failed with 500",
        )
        cp = CompensationPlanRecord(
            compensation_plan_id="cp-comp-fail",
            failure_id="fail-comp-fail",
            actions=[a1],
            plan_status=CompensationStatus.failed,
            escalation_on_failure=True,
        )
        e = RetryRecoveryCompensationEnvelope(
            envelope_id="env-comp-fail",
            failure=f,
            compensation_plan=cp,
            failure_disposition=FailureDisposition.escalated,
        )
        assert e.compensation_plan.escalation_on_failure
        assert e.failure_disposition == FailureDisposition.escalated

    def test_unknown_state_failure_requiring_manual_recovery(self):
        f = FailureRecord(
            failure_id="fail-unknown",
            scope_ref="task-state-loss",
            failure_category=FailureCategory.unknown_state,
            failure_summary="Agent state corrupted, cannot determine last action",
            retryable=False,
            side_effects_present=True,
            unknown_state=True,
        )
        rp = RetryPolicyRecord(
            retry_policy_id="rp-unknown",
            retry_strategy=RetryStrategy.manual_retry,
            max_attempts=1,
        )
        plan = RecoveryPlanRecord(
            recovery_plan_id="rec-plan-unknown",
            failure_id="fail-unknown",
            recovery_mode=RecoveryMode.manual_recovery,
            requires_approval=True,
            recovery_goal="Manual inspection and recovery",
        )
        e = RetryRecoveryCompensationEnvelope(
            envelope_id="env-unknown",
            failure=f,
            retry_policy=rp,
            recovery_plan=plan,
            failure_disposition=FailureDisposition.escalated,
        )
        assert e.failure.unknown_state
        assert e.recovery_plan.recovery_mode == RecoveryMode.manual_recovery
        assert e.failure_disposition == FailureDisposition.escalated
