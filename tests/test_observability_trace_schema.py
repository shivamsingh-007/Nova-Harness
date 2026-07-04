import pytest
from pydantic import ValidationError
from models.observability_trace import (
    StepType, TraceEventStatus, PolicyOutcomeType,
    ToolTrace, PolicyTrace, VerificationTrace, RetryTrace,
    StepTrace, TraceSummary, RunTrace,
)


def make_tool_trace(**overrides) -> ToolTrace:
    kwargs = dict(tool_name="write_file", argument_summary="Write solution.py",
                  status=TraceEventStatus.SUCCESS, latency_seconds=0.5)
    kwargs.update(overrides)
    return ToolTrace(**kwargs)


def make_policy_trace(**overrides) -> PolicyTrace:
    kwargs = dict(policy_name="approval-safety-v1", outcome=PolicyOutcomeType.ALLOWED,
                  risk_level="low", reason="Read-only file access")
    kwargs.update(overrides)
    return PolicyTrace(**kwargs)


def make_verification_trace(**overrides) -> VerificationTrace:
    kwargs = dict(check_name="File exists", status=TraceEventStatus.SUCCESS,
                  summary="solution.py found")
    kwargs.update(overrides)
    return VerificationTrace(**kwargs)


def make_retry_trace(**overrides) -> RetryTrace:
    kwargs = dict(attempt=1, max_attempts=3, reason="Transient HTTP 503",
                  backoff_delay_seconds=2.0)
    kwargs.update(overrides)
    return RetryTrace(**kwargs)


def make_step_trace(**overrides) -> StepTrace:
    kwargs = dict(step_id="step-001", step_index=0, step_type=StepType.TOOL_EXECUTION,
                  status=TraceEventStatus.SUCCESS, started_at="2025-04-01T10:00:00Z",
                  finished_at="2025-04-01T10:00:01Z", latency_seconds=1.0)
    kwargs.update(overrides)
    return StepTrace(**kwargs)


def make_summary(**overrides) -> TraceSummary:
    kwargs = dict(total_steps=3, successful_steps=3, failed_steps=0, blocked_steps=0,
                  total_tool_calls=1, total_policy_checks=0, policy_blocks=0,
                  total_retries=0, total_verification_checks=0, verification_failures=0,
                  total_latency_seconds=3.5)
    kwargs.update(overrides)
    return TraceSummary(**kwargs)


def make_run_trace(**overrides) -> RunTrace:
    kwargs = dict(run_id="run-001", task_id="task-add",
                  terminal_status=TraceEventStatus.SUCCESS,
                  total_latency_seconds=3.5,
                  started_at="2025-04-01T10:00:00Z",
                  finished_at="2025-04-01T10:00:04Z",
                  steps=[make_step_trace()])
    kwargs.update(overrides)
    return RunTrace(**kwargs)


class TestStepType:
    def test_all_values_present(self):
        assert len(StepType) == 7
        assert StepType.APPROVAL.value == "approval"


class TestTraceEventStatus:
    def test_all_values_present(self):
        assert len(TraceEventStatus) == 4
        assert TraceEventStatus.BLOCKED.value == "blocked"


class TestPolicyOutcomeType:
    def test_all_values_present(self):
        assert len(PolicyOutcomeType) == 4
        assert PolicyOutcomeType.ESCALATED.value == "escalated"


class TestToolTrace:
    def test_minimal(self):
        t = make_tool_trace()
        assert t.tool_name == "write_file"
        assert t.latency_seconds == 0.5

    def test_empty_tool_name_raises(self):
        with pytest.raises(ValidationError):
            make_tool_trace(tool_name="  ")

    def test_empty_argument_summary_raises(self):
        with pytest.raises(ValidationError):
            make_tool_trace(argument_summary="  ")

    def test_negative_latency_raises(self):
        with pytest.raises(ValidationError):
            make_tool_trace(latency_seconds=-0.1)

    def test_zero_latency_valid(self):
        t = make_tool_trace(latency_seconds=0.0)
        assert t.latency_seconds == 0.0

    def test_with_error(self):
        t = make_tool_trace(status=TraceEventStatus.FAILURE,
                            error="File not found")
        assert t.error == "File not found"

    def test_all_statuses_accepted(self):
        for s in TraceEventStatus:
            t = make_tool_trace(status=s)
            assert t.status == s


class TestPolicyTrace:
    def test_minimal(self):
        p = make_policy_trace()
        assert p.outcome == PolicyOutcomeType.ALLOWED

    def test_empty_policy_name_raises(self):
        with pytest.raises(ValidationError):
            make_policy_trace(policy_name="  ")

    def test_empty_reason_raises(self):
        with pytest.raises(ValidationError):
            make_policy_trace(reason="  ")

    def test_risk_level_optional(self):
        p = make_policy_trace(risk_level=None)
        assert p.risk_level is None

    def test_all_outcomes_accepted(self):
        for o in PolicyOutcomeType:
            p = make_policy_trace(outcome=o)
            assert p.outcome == o


class TestVerificationTrace:
    def test_minimal(self):
        v = make_verification_trace()
        assert v.check_name == "File exists"

    def test_empty_check_name_raises(self):
        with pytest.raises(ValidationError):
            make_verification_trace(check_name="  ")

    def test_summary_optional(self):
        v = make_verification_trace(summary=None)
        assert v.summary is None

    def test_failure_status(self):
        v = make_verification_trace(status=TraceEventStatus.FAILURE,
                                    summary="File not found")
        assert v.status == TraceEventStatus.FAILURE


class TestRetryTrace:
    def test_minimal(self):
        r = make_retry_trace()
        assert r.attempt == 1
        assert r.max_attempts == 3

    def test_empty_reason_raises(self):
        with pytest.raises(ValidationError):
            make_retry_trace(reason="  ")

    def test_negative_attempt_raises(self):
        with pytest.raises(ValidationError):
            make_retry_trace(attempt=-1)

    def test_negative_max_attempts_raises(self):
        with pytest.raises(ValidationError):
            make_retry_trace(max_attempts=-1)

    def test_attempt_exceeds_max_raises(self):
        with pytest.raises(ValidationError):
            make_retry_trace(attempt=4, max_attempts=3)

    def test_attempt_equal_max_valid(self):
        r = make_retry_trace(attempt=3, max_attempts=3)
        assert r.attempt == 3

    def test_zero_max_attempts_valid(self):
        r = make_retry_trace(attempt=0, max_attempts=0, reason="No retry allowed")
        assert r.max_attempts == 0

    def test_negative_backoff_delay_raises(self):
        with pytest.raises(ValidationError):
            make_retry_trace(backoff_delay_seconds=-1.0)

    def test_backoff_delay_none_valid(self):
        r = make_retry_trace(backoff_delay_seconds=None)
        assert r.backoff_delay_seconds is None


class TestStepTrace:
    def test_minimal(self):
        s = make_step_trace()
        assert s.step_id == "step-001"
        assert s.step_index == 0

    def test_empty_step_id_raises(self):
        with pytest.raises(ValidationError):
            make_step_trace(step_id="  ")

    def test_negative_step_index_raises(self):
        with pytest.raises(ValidationError):
            make_step_trace(step_index=-1)

    def test_negative_latency_raises(self):
        with pytest.raises(ValidationError):
            make_step_trace(latency_seconds=-0.5)

    def test_success_without_finished_at_raises(self):
        with pytest.raises(ValidationError):
            make_step_trace(finished_at=None, latency_seconds=None)

    def test_failure_without_finished_at_raises(self):
        with pytest.raises(ValidationError):
            make_step_trace(status=TraceEventStatus.FAILURE,
                            finished_at=None, latency_seconds=None)

    def test_blocked_without_finished_at_raises(self):
        with pytest.raises(ValidationError):
            make_step_trace(status=TraceEventStatus.BLOCKED,
                            finished_at=None, latency_seconds=None)

    def test_skipped_without_finished_at_valid(self):
        s = make_step_trace(status=TraceEventStatus.SKIPPED,
                            finished_at=None, latency_seconds=None)
        assert s.status == TraceEventStatus.SKIPPED
        assert s.finished_at is None

    def test_with_tool(self):
        s = make_step_trace(tool=make_tool_trace())
        assert s.tool.tool_name == "write_file"

    def test_with_policy(self):
        s = make_step_trace(policy=make_policy_trace())
        assert s.policy.outcome == PolicyOutcomeType.ALLOWED

    def test_with_verification(self):
        s = make_step_trace(verification=make_verification_trace())
        assert s.verification.check_name == "File exists"

    def test_with_retry(self):
        s = make_step_trace(retry=make_retry_trace())
        assert s.retry.attempt == 1

    def test_with_context_item_ids(self):
        s = make_step_trace(context_item_ids=["file:solution.py", "doc:python-guide"])
        assert len(s.context_item_ids) == 2

    def test_all_step_types_accepted(self):
        for st in StepType:
            s = make_step_trace(step_id=f"step-{st.value}", step_type=st)
            assert s.step_type == st

    def test_context_item_ids_default_empty(self):
        s = make_step_trace()
        assert s.context_item_ids == []


class TestTraceSummary:
    def test_minimal(self):
        s = make_summary()
        assert s.total_steps == 3
        assert s.successful_steps == 3

    def test_negative_total_steps_raises(self):
        with pytest.raises(ValidationError):
            make_summary(total_steps=-1)

    def test_negative_successful_steps_raises(self):
        with pytest.raises(ValidationError):
            make_summary(successful_steps=-1)

    def test_negative_total_latency_raises(self):
        with pytest.raises(ValidationError):
            make_summary(total_latency_seconds=-1.0)

    def test_steps_exceed_total_raises(self):
        with pytest.raises(ValidationError):
            make_summary(successful_steps=5, failed_steps=1,
                         blocked_steps=1, total_steps=3)

    def test_steps_within_total_valid(self):
        s = make_summary(successful_steps=2, failed_steps=1,
                         blocked_steps=0, total_steps=3)
        assert s.successful_steps == 2

    def test_all_zero_valid(self):
        s = make_summary(total_steps=0, successful_steps=0, failed_steps=0,
                         blocked_steps=0, total_tool_calls=0,
                         total_policy_checks=0, policy_blocks=0,
                         total_retries=0, total_verification_checks=0,
                         verification_failures=0, total_latency_seconds=0.0)
        assert s.total_steps == 0

    def test_defaults_zero(self):
        s = TraceSummary(
            total_steps=1, successful_steps=1, failed_steps=0, blocked_steps=0,
            total_tool_calls=0, total_policy_checks=0, policy_blocks=0,
            total_retries=0, total_verification_checks=0, verification_failures=0,
            total_latency_seconds=1.0,
        )
        assert s.policy_blocks == 0


class TestRunTrace:
    def test_minimal(self):
        r = make_run_trace()
        assert r.run_id == "run-001"
        assert r.terminal_status == TraceEventStatus.SUCCESS

    def test_empty_run_id_raises(self):
        with pytest.raises(ValidationError):
            make_run_trace(run_id="  ")

    def test_empty_task_id_raises(self):
        with pytest.raises(ValidationError):
            make_run_trace(task_id="  ")

    def test_negative_total_latency_raises(self):
        with pytest.raises(ValidationError):
            make_run_trace(total_latency_seconds=-1.0)

    def test_no_steps_raises(self):
        with pytest.raises(ValidationError):
            make_run_trace(steps=[])

    def test_non_sequential_step_index_raises(self):
        with pytest.raises(ValidationError):
            make_run_trace(steps=[
                make_step_trace(step_id="step-a", step_index=0),
                make_step_trace(step_id="step-b", step_index=2),
            ])

    def test_sequential_step_indexes_valid(self):
        r = make_run_trace(steps=[
            make_step_trace(step_id="step-0", step_index=0),
            make_step_trace(step_id="step-1", step_index=1),
        ])
        assert len(r.steps) == 2

    def test_success_without_finished_at_raises(self):
        with pytest.raises(ValidationError):
            make_run_trace(finished_at=None)

    def test_failure_without_finished_at_raises(self):
        with pytest.raises(ValidationError):
            make_run_trace(terminal_status=TraceEventStatus.FAILURE,
                           finished_at=None)

    def test_blocked_without_finished_at_raises(self):
        with pytest.raises(ValidationError):
            make_run_trace(terminal_status=TraceEventStatus.BLOCKED,
                           finished_at=None)

    def test_skipped_terminal_without_finished_at_valid(self):
        r = make_run_trace(terminal_status=TraceEventStatus.SKIPPED,
                           finished_at=None)
        assert r.terminal_status == TraceEventStatus.SKIPPED

    def test_with_prompt_assembly_id(self):
        r = make_run_trace(prompt_assembly_id="asm-abc123")
        assert r.prompt_assembly_id == "asm-abc123"

    def test_with_summary(self):
        steps = [make_step_trace(step_id=f"s{i}", step_index=i) for i in range(3)]
        r = make_run_trace(steps=steps, summary=make_summary(total_steps=3))
        assert r.summary.total_steps == 3

    def test_summary_total_mismatch_raises(self):
        with pytest.raises(ValidationError):
            make_run_trace(steps=[
                make_step_trace(step_id="step-0", step_index=0),
                make_step_trace(step_id="step-1", step_index=1),
            ], summary=make_summary(total_steps=3))

    def test_summary_total_matches_valid(self):
        r = make_run_trace(steps=[
            make_step_trace(step_id="step-0", step_index=0),
            make_step_trace(step_id="step-1", step_index=1),
            make_step_trace(step_id="step-2", step_index=2),
        ], summary=make_summary(total_steps=3))
        assert r.summary.total_steps == 3

    def test_multiple_step_types(self):
        steps = [
            make_step_trace(step_id="s1", step_index=0,
                            step_type=StepType.POLICY_CHECK,
                            policy=make_policy_trace()),
            make_step_trace(step_id="s2", step_index=1,
                            step_type=StepType.TOOL_EXECUTION,
                            tool=make_tool_trace()),
            make_step_trace(step_id="s3", step_index=2,
                            step_type=StepType.VERIFICATION,
                            verification=make_verification_trace()),
        ]
        r = make_run_trace(steps=steps)
        assert len(r.steps) == 3

    def test_all_terminal_statuses_accepted(self):
        for s in TraceEventStatus:
            ft = "2025-04-01T10:00:04Z" if s in (
                TraceEventStatus.SUCCESS, TraceEventStatus.FAILURE,
                TraceEventStatus.BLOCKED) else None
            r = make_run_trace(terminal_status=s, finished_at=ft)
            assert r.terminal_status == s
