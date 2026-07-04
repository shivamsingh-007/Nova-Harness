from harness.state_driver import StateDriver, TransitionRecord
from models.orchestration_state_machine import RunState, RunEvent, default_machine


def make_driver() -> StateDriver:
    return StateDriver(machine=default_machine())


class TestInitialState:
    def test_starts_at_created(self):
        d = make_driver()
        assert d.current_state_id == RunState.CREATED

    def test_not_terminal(self):
        d = make_driver()
        assert not d.is_terminal

    def test_available_events_from_created(self):
        d = make_driver()
        events = d.available_events()
        assert RunEvent.START_RUN in events
        assert RunEvent.CANCEL_RUN in events


class TestTriggerBasic:
    def test_start_run_transitions_to_assembling_prompt(self):
        d = make_driver()
        result = d.trigger(RunEvent.START_RUN)
        assert result == RunState.ASSEMBLING_PROMPT
        assert d.current_state_id == RunState.ASSEMBLING_PROMPT

    def test_cancel_from_created(self):
        d = make_driver()
        result = d.trigger(RunEvent.CANCEL_RUN)
        assert result == RunState.CANCELLED
        assert d.is_terminal

    def test_terminal_state_rejects_events(self):
        d = make_driver()
        d.trigger(RunEvent.CANCEL_RUN)
        assert d.is_terminal
        import pytest
        with pytest.raises(ValueError, match="terminal state"):
            d.trigger(RunEvent.START_RUN)

    def test_invalid_event_raises(self):
        d = make_driver()
        import pytest
        with pytest.raises(ValueError, match="no transition"):
            d.trigger(RunEvent.TOOL_COMPLETED)


class TestHistory:
    def test_starts_empty(self):
        d = make_driver()
        assert len(d.history) == 0

    def test_records_transition(self):
        d = make_driver()
        d.trigger(RunEvent.START_RUN)
        assert len(d.history) == 1
        r = d.history[0]
        assert r.from_state == RunState.CREATED
        assert r.event == RunEvent.START_RUN
        assert r.to_state == RunState.ASSEMBLING_PROMPT
        assert r.decision == "allowed"
        assert isinstance(r.timestamp, str) and len(r.timestamp) > 0

    def test_records_multiple(self):
        d = make_driver()
        d.trigger(RunEvent.START_RUN)
        d.trigger(RunEvent.CANCEL_RUN)
        assert len(d.history) == 2
        assert d.history[1].to_state == RunState.CANCELLED


class TestGuards:
    def test_guard_rejection_raises_and_records(self):
        d = make_driver()
        # Navigate to RETRY_PENDING
        d.trigger(RunEvent.START_RUN)
        d.trigger(RunEvent.PROMPT_READY)
        d.trigger(RunEvent.MODEL_RESPONSE_RECEIVED)
        d.trigger(RunEvent.TOOL_CALL_REQUESTED)
        d.trigger(RunEvent.TOOL_APPROVED_OR_NOT_REQUIRED)
        d.trigger(RunEvent.TOOL_FAILED_RETRYABLE)
        before = len(d.history)

        import pytest
        with pytest.raises(ValueError, match="guard.*retry_budget"):
            d.trigger(
                RunEvent.RETRY_ALLOWED,
                guard_results={"retry_budget_available": False},
            )
        assert len(d.history) == before + 1
        r = d.history[-1]
        assert r.to_state == RunState.RETRY_PENDING  # stayed put
        assert r.decision == "blocked by guard: retry_budget_available"
        assert r.guard_results == {"retry_budget_available": False}

    def test_guard_acceptance_allows_transition(self):
        d = make_driver()
        # Go to RETRY_PENDING first
        d.trigger(RunEvent.START_RUN)
        d.trigger(RunEvent.PROMPT_READY)
        d.trigger(RunEvent.MODEL_RESPONSE_RECEIVED)
        d.trigger(RunEvent.TOOL_CALL_REQUESTED)
        d.trigger(RunEvent.TOOL_APPROVED_OR_NOT_REQUIRED)
        d.trigger(RunEvent.TOOL_FAILED_RETRYABLE)
        assert d.current_state_id == RunState.RETRY_PENDING

        result = d.trigger(
            RunEvent.RETRY_ALLOWED,
            guard_results={"retry_budget_available": True},
        )
        assert result == RunState.ASSEMBLING_PROMPT

    def test_guard_not_needed_when_no_guards_on_transition(self):
        d = make_driver()
        result = d.trigger(RunEvent.START_RUN)
        assert result == RunState.ASSEMBLING_PROMPT


class TestFullHappyPath:
    def test_full_success_sequence(self):
        d = make_driver()
        assert d.current_state_id == RunState.CREATED

        sequence = [
            (RunEvent.START_RUN, RunState.ASSEMBLING_PROMPT),
            (RunEvent.PROMPT_READY, RunState.MODEL_PENDING),
            (RunEvent.MODEL_RESPONSE_RECEIVED, RunState.MODEL_COMPLETED),
            (RunEvent.NO_TOOL_NEEDED, RunState.VERIFYING),
            (RunEvent.VERIFICATION_PASSED, RunState.SUCCEEDED),
        ]
        for event, expected in sequence:
            result = d.trigger(event)
            assert result == expected, f"expected {expected.value}, got {result.value}"

        assert d.is_terminal
        assert d.current_state_id == RunState.SUCCEEDED
        assert len(d.history) == len(sequence)


class TestFullFailurePath:
    def test_tool_failure_retry_then_success(self):
        d = make_driver()

        d.trigger(RunEvent.START_RUN)
        d.trigger(RunEvent.PROMPT_READY)
        d.trigger(RunEvent.MODEL_RESPONSE_RECEIVED)
        d.trigger(RunEvent.TOOL_CALL_REQUESTED)
        assert d.current_state_id == RunState.TOOL_PENDING

        d.trigger(RunEvent.TOOL_APPROVED_OR_NOT_REQUIRED)
        assert d.current_state_id == RunState.TOOL_RUNNING

        d.trigger(RunEvent.TOOL_FAILED_RETRYABLE)
        assert d.current_state_id == RunState.RETRY_PENDING

        d.trigger(RunEvent.RETRY_ALLOWED, guard_results={"retry_budget_available": True})
        assert d.current_state_id == RunState.ASSEMBLING_PROMPT

        d.trigger(RunEvent.PROMPT_READY)
        d.trigger(RunEvent.MODEL_RESPONSE_RECEIVED)
        d.trigger(RunEvent.TOOL_CALL_REQUESTED)
        d.trigger(RunEvent.TOOL_APPROVED_OR_NOT_REQUIRED)
        d.trigger(RunEvent.TOOL_COMPLETED)
        assert d.current_state_id == RunState.VERIFYING

        d.trigger(RunEvent.VERIFICATION_PASSED)
        assert d.current_state_id == RunState.SUCCEEDED
        assert d.is_terminal

    def test_tool_failure_retry_exhausted_fails(self):
        d = make_driver()

        d.trigger(RunEvent.START_RUN)
        assert d.current_state_id == RunState.ASSEMBLING_PROMPT

        d.trigger(RunEvent.PROMPT_READY)
        d.trigger(RunEvent.MODEL_RESPONSE_RECEIVED)
        d.trigger(RunEvent.TOOL_CALL_REQUESTED)
        d.trigger(RunEvent.TOOL_APPROVED_OR_NOT_REQUIRED)
        d.trigger(RunEvent.TOOL_FAILED_RETRYABLE)
        assert d.current_state_id == RunState.RETRY_PENDING

        import pytest
        with pytest.raises(ValueError, match="guard.*retry_budget"):
            d.trigger(
                RunEvent.RETRY_ALLOWED,
                guard_results={"retry_budget_available": False},
            )
        assert d.current_state_id == RunState.RETRY_PENDING

    def test_verification_failure_terminal(self):
        d = make_driver()
        d.trigger(RunEvent.START_RUN)
        d.trigger(RunEvent.PROMPT_READY)
        d.trigger(RunEvent.MODEL_RESPONSE_RECEIVED)
        d.trigger(RunEvent.NO_TOOL_NEEDED)
        assert d.current_state_id == RunState.VERIFYING

        d.trigger(RunEvent.VERIFICATION_FAILED_TERMINAL)
        assert d.current_state_id == RunState.FAILED
        assert d.is_terminal

    def test_approval_rejected_fails(self):
        d = make_driver()
        d.trigger(RunEvent.START_RUN)
        d.trigger(RunEvent.PROMPT_READY)
        d.trigger(RunEvent.MODEL_RESPONSE_RECEIVED)
        d.trigger(RunEvent.TOOL_CALL_REQUESTED)
        d.trigger(RunEvent.APPROVAL_REQUIRED)
        assert d.current_state_id == RunState.AWAITING_APPROVAL

        d.trigger(RunEvent.APPROVAL_REJECTED)
        assert d.current_state_id == RunState.FAILED
        assert d.is_terminal


class TestAvailableEvents:
    def test_terminal_has_no_events(self):
        d = make_driver()
        d.trigger(RunEvent.CANCEL_RUN)
        assert d.available_events() == []

    def test_non_terminal_has_events(self):
        d = make_driver()
        d.trigger(RunEvent.START_RUN)
        events = d.available_events()
        assert RunEvent.PROMPT_READY in events
        assert RunEvent.CANCEL_RUN in events

    def test_assembling_prompt_has_expected_events(self):
        d = make_driver()
        d.trigger(RunEvent.START_RUN)
        events = d.available_events()
        assert set(events) == {RunEvent.PROMPT_READY, RunEvent.CANCEL_RUN}

    def test_awaiting_approval_has_expected_events(self):
        d = make_driver()
        d.trigger(RunEvent.START_RUN)
        d.trigger(RunEvent.PROMPT_READY)
        d.trigger(RunEvent.MODEL_RESPONSE_RECEIVED)
        d.trigger(RunEvent.TOOL_CALL_REQUESTED)
        d.trigger(RunEvent.APPROVAL_REQUIRED)
        events = d.available_events()
        assert RunEvent.APPROVAL_GRANTED in events
        assert RunEvent.APPROVAL_REJECTED in events
        assert RunEvent.CANCEL_RUN in events


class TestCustomMachine:
    def test_custom_machine(self):
        machine = default_machine("custom")
        d = StateDriver(machine=machine)
        assert d.machine.machine_id == "custom"
        assert d.current_state_id == RunState.CREATED
