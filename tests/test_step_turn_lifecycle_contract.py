import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from models.step_turn_lifecycle_contract import (
    StepTriggerType, StepPhase, StepStatus, StepOutcome, StepStopReason,
    StepSelectionContext, StepIntent, StepActionRecord,
    StepVerificationRecord, StepStateDelta, StepArtifactUpdateRecord,
    StepLifecycleRecord, StepTurnEnvelope,
)


NOW = datetime.now(timezone.utc)


def make_ctx(**overrides) -> StepSelectionContext:
    defaults = dict(step_id="step-001", loop_id="loop-001")
    defaults.update(overrides)
    return StepSelectionContext(**defaults)


def make_intent(**overrides) -> StepIntent:
    defaults = dict(intent_id="int-001", objective="Implement auth model",
                    acceptance_criteria=["User model has email"])
    defaults.update(overrides)
    return StepIntent(**defaults)


def make_action(**overrides) -> StepActionRecord:
    defaults = dict(action_id="act-001", phase=StepPhase.ACT,
                    action_type="tool_call", started_at=NOW)
    defaults.update(overrides)
    return StepActionRecord(**defaults)


def make_ver(passed: bool = True, **overrides) -> StepVerificationRecord:
    defaults = dict(verification_id="ver-001", passed=passed)
    defaults.update(overrides)
    return StepVerificationRecord(**defaults)


def make_delta(**overrides) -> StepStateDelta:
    defaults = dict()
    defaults.update(overrides)
    return StepStateDelta(**defaults)


def make_artifacts(**overrides) -> StepArtifactUpdateRecord:
    defaults = dict()
    defaults.update(overrides)
    return StepArtifactUpdateRecord(**defaults)


def make_step(**overrides) -> StepLifecycleRecord:
    defaults = dict(
        step_id="step-001", status=StepStatus.RUNNING,
        current_phase=StepPhase.PLAN, trigger_type=StepTriggerType.LOOP_ITERATION,
        selection_context=make_ctx(), intent=make_intent(),
        started_at=NOW,
    )
    defaults.update(overrides)
    return StepLifecycleRecord(**defaults)


def make_envelope(**overrides) -> StepTurnEnvelope:
    defaults = dict(envelope_id="env-step-001", loop_id="loop-001",
                    step=make_step())
    defaults.update(overrides)
    return StepTurnEnvelope(**defaults)


class TestEnums:
    def test_step_trigger_type(self):
        assert StepTriggerType.LOOP_ITERATION.value == "loop_iteration"
        assert StepTriggerType.MANUAL_RESUME.value == "manual_resume"
        assert StepTriggerType.RECOVERY_RESUME.value == "recovery_resume"
        assert StepTriggerType.DELEGATION_RETURN.value == "delegation_return"
        assert StepTriggerType.SCHEDULED_TICK.value == "scheduled_tick"
        assert StepTriggerType.EXTERNAL_EVENT.value == "external_event"
        assert len(StepTriggerType) == 6

    def test_step_phase(self):
        assert StepPhase.SELECT.value == "select"
        assert StepPhase.CLOSE.value == "close"
        assert len(StepPhase) == 8

    def test_step_status(self):
        assert StepStatus.COMPLETED.value == "completed"
        assert StepStatus.FAILED.value == "failed"
        assert len(StepStatus) == 7

    def test_step_outcome(self):
        assert StepOutcome.HANDOFF_REQUIRED.value == "handoff_required"
        assert StepOutcome.APPROVAL_REQUIRED.value == "approval_required"
        assert len(StepOutcome) == 6

    def test_step_stop_reason(self):
        assert StepStopReason.VERIFIED_SUCCESS.value == "verified_success"
        assert StepStopReason.EXTERNAL_BLOCKER.value == "external_blocker"
        assert len(StepStopReason) == 10


class TestStepSelectionContext:
    def test_valid(self):
        c = make_ctx()
        assert c.step_id == "step-001"

    def test_blank_step_id_raises(self):
        with pytest.raises(ValidationError):
            make_ctx(step_id="")

    def test_blank_loop_id_raises(self):
        with pytest.raises(ValidationError):
            make_ctx(loop_id="")

    def test_with_dependencies(self):
        c = make_ctx(blocking_dependencies=["task-001"])
        assert c.blocking_dependencies[0] == "task-001"


class TestStepIntent:
    def test_valid(self):
        i = make_intent()
        assert i.intent_id == "int-001"

    def test_blank_intent_id_raises(self):
        with pytest.raises(ValidationError):
            make_intent(intent_id="")

    def test_blank_objective_raises(self):
        with pytest.raises(ValidationError):
            make_intent(objective="")

    def test_empty_acceptance_criteria_raises(self):
        with pytest.raises(ValidationError, match="acceptance_criteria must not be empty"):
            make_intent(acceptance_criteria=[])

    def test_delegation_allowed(self):
        i = make_intent(delegation_allowed=True)
        assert i.delegation_allowed is True

    def test_with_expected_output(self):
        i = make_intent(expected_output="auth model code")
        assert i.expected_output == "auth model code"


class TestStepActionRecord:
    def test_valid(self):
        a = make_action()
        assert a.action_id == "act-001"

    def test_blank_action_id_raises(self):
        with pytest.raises(ValidationError):
            make_action(action_id="")

    def test_with_model_call(self):
        a = make_action(action_type="model_call", related_model_call_id="mc-001")
        assert a.related_model_call_id == "mc-001"


class TestStepVerificationRecord:
    def test_valid(self):
        v = make_ver()
        assert v.verification_id == "ver-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValidationError):
            make_ver(verification_id="")

    def test_confidence_range_low_raises(self):
        with pytest.raises(ValidationError, match="confidence must be between"):
            make_ver(confidence=-0.1)

    def test_confidence_range_high_raises(self):
        with pytest.raises(ValidationError, match="confidence must be between"):
            make_ver(confidence=1.1)

    def test_passed_with_low_confidence_raises(self):
        with pytest.raises(ValidationError, match="passed verification requires confidence"):
            make_ver(passed=True, confidence=0.3)

    def test_passed_with_high_confidence_valid(self):
        v = make_ver(passed=True, confidence=0.9)
        assert v.passed is True

    def test_failure_with_requires_escalation(self):
        v = make_ver(passed=False, requires_escalation=True)
        assert v.requires_escalation is True


class TestStepStateDelta:
    def test_empty_valid(self):
        d = make_delta()
        assert d.next_action == ""

    def test_with_next_action(self):
        d = make_delta(next_action="Implement JWT")
        assert d.next_action == "Implement JWT"


class TestStepArtifactUpdateRecord:
    def test_empty_valid(self):
        a = make_artifacts()
        assert a.updated_todo is False

    def test_with_updates(self):
        a = make_artifacts(updated_todo=True, updated_state=True)
        assert a.updated_todo is True
        assert a.updated_state is True


class TestStepLifecycleRecord:
    def test_valid(self):
        s = make_step()
        assert s.step_id == "step-001"

    def test_blank_step_id_raises(self):
        with pytest.raises(ValidationError):
            make_step(step_id="")

    def test_terminal_status_needs_ended_at(self):
        with pytest.raises(ValidationError, match="terminal status requires ended_at"):
            make_step(status=StepStatus.COMPLETED, ended_at=None)

    def test_terminal_status_with_ended_at_valid(self):
        s = make_step(status=StepStatus.COMPLETED, ended_at=NOW)
        assert s.ended_at is not None

    def test_completed_success_needs_verification_passed(self):
        with pytest.raises(ValidationError, match=r"completed\+success requires verification"):
            make_step(status=StepStatus.COMPLETED, outcome=StepOutcome.SUCCESS,
                      ended_at=NOW, verification=None)

    def test_completed_success_with_verification_valid(self):
        s = make_step(status=StepStatus.COMPLETED, outcome=StepOutcome.SUCCESS,
                      ended_at=NOW, verification=make_ver(passed=True))
        assert s.verification.passed is True

    def test_failure_outcome_needs_stop_reason(self):
        with pytest.raises(ValidationError, match="failure/no_progress outcomes require stop_reason"):
            make_step(outcome=StepOutcome.FAILURE, stop_reason=None)

    def test_failure_outcome_with_stop_reason_valid(self):
        s = make_step(outcome=StepOutcome.FAILURE,
                      stop_reason=StepStopReason.VERIFICATION_FAILED)
        assert s.stop_reason == StepStopReason.VERIFICATION_FAILED

    def test_no_progress_needs_stop_reason(self):
        with pytest.raises(ValidationError, match="failure/no_progress outcomes require stop_reason"):
            make_step(outcome=StepOutcome.NO_PROGRESS, stop_reason=None)

    def test_no_progress_needs_next_step_hint(self):
        with pytest.raises(ValidationError, match="no_progress requires non-empty next_step_hint"):
            make_step(outcome=StepOutcome.NO_PROGRESS,
                      stop_reason=StepStopReason.REPEATED_NO_PROGRESS,
                      next_step_hint="")

    def test_no_progress_with_hint_valid(self):
        s = make_step(outcome=StepOutcome.NO_PROGRESS,
                      stop_reason=StepStopReason.REPEATED_NO_PROGRESS,
                      next_step_hint="Escalate to human")
        assert s.next_step_hint == "Escalate to human"

    def test_state_delta_requires_artifact_updates(self):
        with pytest.raises(ValidationError, match="state-changing steps must record artifact updates"):
            make_step(status=StepStatus.COMPLETED, ended_at=NOW,
                      outcome=StepOutcome.SUCCESS,
                      verification=make_ver(passed=True),
                      state_delta=StepStateDelta(next_action="Do X"))

    def test_state_delta_with_artifact_updates_valid(self):
        s = make_step(status=StepStatus.COMPLETED, ended_at=NOW,
                      outcome=StepOutcome.SUCCESS,
                      verification=make_ver(passed=True),
                      state_delta=StepStateDelta(next_action="Do X"),
                      artifact_updates=StepArtifactUpdateRecord(updated_loop_memory=True))
        assert s.state_delta.next_action == "Do X"

    def test_delegation_request_without_allowed_raises(self):
        with pytest.raises(ValidationError, match="delegation_request requires"):
            make_step(actions=[make_action(action_type="delegation_request")],
                      intent=make_intent(delegation_allowed=False))

    def test_delegation_request_with_allowed_valid(self):
        s = make_step(actions=[make_action(action_type="delegation_request")],
                      intent=make_intent(delegation_allowed=True))
        assert s.actions[0].action_type == "delegation_request"


class TestStepTurnEnvelope:
    def test_valid(self):
        e = make_envelope()
        assert e.envelope_id == "env-step-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="")

    def test_blank_loop_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(loop_id="")


class TestSerialization:
    def test_step_to_dict_and_back(self):
        s = make_step()
        data = s.model_dump()
        assert data["step_id"] == "step-001"
        restored = StepLifecycleRecord(**data)
        assert restored.step_id == s.step_id

    def test_envelope_to_dict_and_back(self):
        e = make_envelope()
        data = e.model_dump()
        restored = StepTurnEnvelope(**data)
        assert restored.envelope_id == e.envelope_id


class TestIntegration:
    def test_successful_implementation_step(self):
        ctx = StepSelectionContext(step_id="s-001", loop_id="l-001",
                                   selected_task_id="task-auth-001")
        intent = StepIntent(intent_id="i-001", objective="Create auth model",
                            acceptance_criteria=["User model with email", "Password hashing"])
        action = StepActionRecord(action_id="a-001", phase=StepPhase.ACT,
                                  action_type="file_edit", started_at=NOW,
                                  summary="Created user model with bcrypt")
        ver = StepVerificationRecord(verification_id="v-001", passed=True,
                                     checks_performed=["Tests pass", "Criteria met"])
        delta = StepStateDelta(updated_task_status="done",
                               memory_changes=["Auth model complete"],
                               next_action="Implement JWT")
        arts = StepArtifactUpdateRecord(updated_todo=True, updated_loop_memory=True, updated_state=True)
        step = StepLifecycleRecord(
            step_id="s-001", status=StepStatus.COMPLETED, outcome=StepOutcome.SUCCESS,
            current_phase=StepPhase.CLOSE, trigger_type=StepTriggerType.LOOP_ITERATION,
            selection_context=ctx, intent=intent, actions=[action],
            verification=ver, state_delta=delta, artifact_updates=arts,
            started_at=NOW, ended_at=NOW, stop_reason=StepStopReason.VERIFIED_SUCCESS,
            next_step_hint="Implement JWT token generation",
        )
        env = StepTurnEnvelope(envelope_id="env-001", loop_id="l-001", step=step)
        assert env.step.verification.passed is True
        assert env.step.state_delta.next_action == "Implement JWT"

    def test_tool_failure_step(self):
        ctx = make_ctx(step_id="s-002")
        intent = make_intent(intent_id="i-002", objective="Run migration")
        action = StepActionRecord(action_id="a-002", phase=StepPhase.ACT,
                                  action_type="tool_call", started_at=NOW,
                                  related_tool_call_id="tc-001",
                                  summary="Migration tool failed")
        ver = StepVerificationRecord(verification_id="v-002", passed=False,
                                     failure_summary="Migration would drop columns",
                                     requires_retry=True)
        delta = StepStateDelta(new_blockers=["Data loss risk"],
                               memory_changes=["Migration unsafe"],
                               next_action="Revise migration script")
        arts = StepArtifactUpdateRecord(updated_loop_memory=True, updated_todo=True)
        step = StepLifecycleRecord(
            step_id="s-002", status=StepStatus.FAILED, outcome=StepOutcome.FAILURE,
            current_phase=StepPhase.STOP_CHECK, trigger_type=StepTriggerType.LOOP_ITERATION,
            selection_context=ctx, intent=intent, actions=[action],
            verification=ver, state_delta=delta, artifact_updates=arts,
            started_at=NOW, ended_at=NOW, stop_reason=StepStopReason.VERIFICATION_FAILED,
            next_step_hint="Revise migration script and retry",
        )
        env = StepTurnEnvelope(envelope_id="env-002", loop_id="l-001", step=step)
        assert env.step.verification.passed is False
        assert env.step.stop_reason == StepStopReason.VERIFICATION_FAILED

    def test_no_progress_step_escalating(self):
        ctx = make_ctx(step_id="s-003")
        intent = make_intent(intent_id="i-003", objective="Fix flaky test")
        delta = StepStateDelta(new_lessons=["Test flaky under load"],
                               next_action="Escalate to senior")
        arts = StepArtifactUpdateRecord(updated_lessons=True, updated_loop_memory=True)
        step = StepLifecycleRecord(
            step_id="s-003", status=StepStatus.FAILED, outcome=StepOutcome.NO_PROGRESS,
            current_phase=StepPhase.STOP_CHECK, trigger_type=StepTriggerType.LOOP_ITERATION,
            selection_context=ctx, intent=intent,
            state_delta=delta, artifact_updates=arts,
            started_at=NOW, ended_at=NOW, stop_reason=StepStopReason.REPEATED_NO_PROGRESS,
            next_step_hint="Escalate to senior engineer. Unable to reproduce.",
        )
        env = StepTurnEnvelope(envelope_id="env-003", loop_id="l-001", step=step)
        assert env.step.outcome == StepOutcome.NO_PROGRESS

    def test_blocked_step_waiting_for_approval(self):
        ctx = make_ctx(step_id="s-004")
        intent = make_intent(intent_id="i-004", objective="Delete deprecated endpoint")
        step = StepLifecycleRecord(
            step_id="s-004", status=StepStatus.BLOCKED,
            outcome=StepOutcome.APPROVAL_REQUIRED,
            current_phase=StepPhase.STOP_CHECK,
            trigger_type=StepTriggerType.LOOP_ITERATION,
            selection_context=ctx, intent=intent,
            started_at=NOW,
            next_step_hint="Waiting for human approval to delete endpoint",
        )
        env = StepTurnEnvelope(envelope_id="env-004", loop_id="l-001", step=step)
        assert env.step.status == StepStatus.BLOCKED

    def test_partial_progress_updating_artifacts(self):
        ctx = make_ctx(step_id="s-005", selected_task_id="task-db-001")
        intent = make_intent(intent_id="i-005", objective="Create DB migration",
                             acceptance_criteria=["Migration script written"])
        action = StepActionRecord(action_id="a-005", phase=StepPhase.ACT,
                                  action_type="file_edit", started_at=NOW,
                                  summary="Created migration skeleton")
        ver = StepVerificationRecord(verification_id="v-005", passed=True, confidence=0.8)
        delta = StepStateDelta(updated_task_status="in_progress",
                               memory_changes=["Migration skeleton created"],
                               next_action="Add indexes to migration")
        arts = StepArtifactUpdateRecord(updated_todo=True, updated_loop_memory=True,
                                        updated_state=True)
        step = StepLifecycleRecord(
            step_id="s-005", status=StepStatus.COMPLETED, outcome=StepOutcome.PARTIAL,
            current_phase=StepPhase.CLOSE, trigger_type=StepTriggerType.LOOP_ITERATION,
            selection_context=ctx, intent=intent, actions=[action],
            verification=ver, state_delta=delta, artifact_updates=arts,
            started_at=NOW, ended_at=NOW, stop_reason=StepStopReason.VERIFIED_SUCCESS,
            next_step_hint="Add indexes to migration script",
        )
        env = StepTurnEnvelope(envelope_id="env-005", loop_id="l-001", step=step)
        assert env.step.outcome == StepOutcome.PARTIAL
        assert env.step.artifact_updates.updated_todo is True
