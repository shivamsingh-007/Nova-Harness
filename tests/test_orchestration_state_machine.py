import pytest
from pydantic import ValidationError
from models.orchestration_state_machine import (
    OrchestrationStateMachine,
    TransitionRule,
    TransitionGuard,
    RunState,
    RunEvent,
    default_machine,
    default_transitions,
)


def make_guard(**overrides) -> TransitionGuard:
    kwargs = dict(name="retry_budget_available", description="Retry count within limit")
    kwargs.update(overrides)
    return TransitionGuard(**kwargs)


def make_transition(**overrides) -> TransitionRule:
    kwargs = dict(
        from_state=RunState.CREATED,
        event=RunEvent.START_RUN,
        to_state=RunState.ASSEMBLING_PROMPT,
    )
    kwargs.update(overrides)
    return TransitionRule(**kwargs)


def make_machine(**overrides) -> OrchestrationStateMachine:
    kwargs = dict(
        machine_id="test-machine",
        initial_state=RunState.CREATED,
        terminal_states=[RunState.SUCCEEDED, RunState.FAILED, RunState.CANCELLED],
        transitions=default_transitions(),
    )
    kwargs.update(overrides)
    return OrchestrationStateMachine(**kwargs)


class TestTransitionGuard:
    def test_valid_guard(self):
        g = make_guard()
        assert g.name == "retry_budget_available"

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_guard(name="")
        assert "guard name must not be empty" in str(exc.value)


class TestTransitionRule:
    def test_valid_transition(self):
        t = make_transition()
        assert t.from_state == RunState.CREATED
        assert t.event == RunEvent.START_RUN

    def test_with_guards(self):
        t = make_transition(guards=[make_guard()])
        assert len(t.guards) == 1

    def test_default_no_guards(self):
        t = make_transition()
        assert t.guards == []

    def test_terminal_to_non_terminal(self):
        t = make_transition(from_state=RunState.FAILED, event=RunEvent.CANCEL_RUN, to_state=RunState.CANCELLED)
        assert t.from_state == RunState.FAILED

    def test_all_states_accessible(self):
        for s in RunState:
            t = make_transition(from_state=s)
            assert t.from_state == s

    def test_all_events_accessible(self):
        for e in RunEvent:
            t = make_transition(event=e)
            assert t.event == e


class TestOrchestrationStateMachine:
    def test_valid_default_machine(self):
        m = make_machine()
        assert m.machine_id == "test-machine"
        assert m.initial_state == RunState.CREATED
        assert len(m.transitions) > 0

    def test_default_machine_factory(self):
        m = default_machine("harness-v1")
        assert m.machine_id == "harness-v1"
        assert m.initial_state == RunState.CREATED
        assert RunState.SUCCEEDED in m.terminal_states
        assert RunState.FAILED in m.terminal_states
        assert RunState.CANCELLED in m.terminal_states

    def test_empty_machine_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_machine(machine_id="")
        assert "machine_id must not be empty" in str(exc.value)

    def test_initial_state_terminal_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_machine(initial_state=RunState.SUCCEEDED)
        assert "initial_state must not be a terminal state" in str(exc.value)

    def test_duplicate_terminal_states_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_machine(terminal_states=[RunState.SUCCEEDED, RunState.SUCCEEDED])
        assert "terminal_states must be unique" in str(exc.value)

    def test_duplicate_transition_pair_raises(self):
        t1 = make_transition()
        t2 = make_transition()
        with pytest.raises(ValidationError) as exc:
            make_machine(transitions=[t1, t2])
        assert "duplicate transition pair" in str(exc.value)

    def test_unique_transition_pair_is_valid(self):
        t1 = make_transition(from_state=RunState.CREATED, event=RunEvent.START_RUN, to_state=RunState.SUCCEEDED)
        t2 = make_transition(from_state=RunState.CREATED, event=RunEvent.CANCEL_RUN, to_state=RunState.CANCELLED)
        m = make_machine(terminal_states=[RunState.SUCCEEDED, RunState.FAILED, RunState.CANCELLED], transitions=[t1, t2])
        assert len(m.transitions) == 2

    def test_non_terminal_state_missing_outgoing_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_machine(transitions=[])
        assert "non-terminal states without outgoing transitions" in str(exc.value)

    def test_default_machine_has_all_non_terminal_outgoing(self):
        m = make_machine()
        terminal_set = set(m.terminal_states)
        states_with_outgoing = {t.from_state for t in m.transitions}
        for s in RunState:
            if s not in terminal_set:
                assert s in states_with_outgoing, f"{s} missing outgoing transition"

    def test_default_transition_count(self):
        m = make_machine()
        # 15 main transitions + 9 cancel transitions = 24
        assert len(m.transitions) == 24

    def test_created_to_assembling(self):
        m = make_machine()
        found = any(
            t.from_state == RunState.CREATED and t.event == RunEvent.START_RUN and t.to_state == RunState.ASSEMBLING_PROMPT
            for t in m.transitions
        )
        assert found

    def test_verifying_to_succeeded(self):
        m = make_machine()
        found = any(
            t.from_state == RunState.VERIFYING and t.event == RunEvent.VERIFICATION_PASSED and t.to_state == RunState.SUCCEEDED
            for t in m.transitions
        )
        assert found

    def test_retry_allowed_to_assembling(self):
        m = make_machine()
        found = any(
            t.from_state == RunState.RETRY_PENDING and t.event == RunEvent.RETRY_ALLOWED and t.to_state == RunState.ASSEMBLING_PROMPT
            for t in m.transitions
        )
        assert found

    def test_retry_transition_has_retry_budget_guard(self):
        m = make_machine()
        for t in m.transitions:
            if t.from_state == RunState.RETRY_PENDING and t.event == RunEvent.RETRY_ALLOWED:
                assert any(g.name == "retry_budget_available" for g in t.guards)
                return
        pytest.fail("RETRY_PENDING -> retry_allowed transition not found")

    def test_approval_granted_has_approval_gate_guard(self):
        m = make_machine()
        for t in m.transitions:
            if t.from_state == RunState.AWAITING_APPROVAL and t.event == RunEvent.APPROVAL_GRANTED:
                assert any(g.name == "approval_granted_if_required" for g in t.guards)
                return
        pytest.fail("AWAITING_APPROVAL -> approval_granted transition not found")

    def test_cancel_from_all_non_terminal(self):
        m = make_machine()
        terminal_set = set(m.terminal_states)
        for s in RunState:
            if s not in terminal_set:
                found = any(
                    t.from_state == s and t.event == RunEvent.CANCEL_RUN and t.to_state == RunState.CANCELLED
                    for t in m.transitions
                )
                assert found, f"cancel_run from {s} missing"

    def test_custom_terminal_states(self):
        m = make_machine(terminal_states=[RunState.SUCCEEDED, RunState.FAILED, RunState.CANCELLED])
        assert len(m.terminal_states) == 3

    def test_custom_initial_state(self):
        m = make_machine(initial_state=RunState.ASSEMBLING_PROMPT)
        assert m.initial_state == RunState.ASSEMBLING_PROMPT


class TestTransitionScenarios:
    def test_happy_path(self):
        m = make_machine()
        path = [
            (RunState.CREATED, RunEvent.START_RUN, RunState.ASSEMBLING_PROMPT),
            (RunState.ASSEMBLING_PROMPT, RunEvent.PROMPT_READY, RunState.MODEL_PENDING),
            (RunState.MODEL_PENDING, RunEvent.MODEL_RESPONSE_RECEIVED, RunState.MODEL_COMPLETED),
            (RunState.MODEL_COMPLETED, RunEvent.NO_TOOL_NEEDED, RunState.VERIFYING),
            (RunState.VERIFYING, RunEvent.VERIFICATION_PASSED, RunState.SUCCEEDED),
        ]
        for from_state, event, to_state in path:
            assert any(
                t.from_state == from_state and t.event == event and t.to_state == to_state
                for t in m.transitions
            ), f"Missing transition: {from_state} --{event}--> {to_state}"

    def test_tool_call_path(self):
        m = make_machine()
        path = [
            (RunState.MODEL_COMPLETED, RunEvent.TOOL_CALL_REQUESTED, RunState.TOOL_PENDING),
            (RunState.TOOL_PENDING, RunEvent.TOOL_APPROVED_OR_NOT_REQUIRED, RunState.TOOL_RUNNING),
            (RunState.TOOL_RUNNING, RunEvent.TOOL_COMPLETED, RunState.VERIFYING),
        ]
        for from_state, event, to_state in path:
            assert any(
                t.from_state == from_state and t.event == event and t.to_state == to_state
                for t in m.transitions
            ), f"Missing transition: {from_state} --{event}--> {to_state}"

    def test_approval_path(self):
        m = make_machine()
        path = [
            (RunState.TOOL_PENDING, RunEvent.APPROVAL_REQUIRED, RunState.AWAITING_APPROVAL),
            (RunState.AWAITING_APPROVAL, RunEvent.APPROVAL_GRANTED, RunState.TOOL_RUNNING),
        ]
        for from_state, event, to_state in path:
            assert any(
                t.from_state == from_state and t.event == event and t.to_state == to_state
                for t in m.transitions
            ), f"Missing transition: {from_state} --{event}--> {to_state}"

    def test_retry_path(self):
        m = make_machine()
        path = [
            (RunState.TOOL_RUNNING, RunEvent.TOOL_FAILED_RETRYABLE, RunState.RETRY_PENDING),
            (RunState.RETRY_PENDING, RunEvent.RETRY_ALLOWED, RunState.ASSEMBLING_PROMPT),
            (RunState.VERIFYING, RunEvent.VERIFICATION_FAILED_RETRYABLE, RunState.RETRY_PENDING),
        ]
        for from_state, event, to_state in path:
            assert any(
                t.from_state == from_state and t.event == event and t.to_state == to_state
                for t in m.transitions
            ), f"Missing transition: {from_state} --{event}--> {to_state}"

    def test_terminal_failure_path(self):
        m = make_machine()
        path = [
            (RunState.VERIFYING, RunEvent.VERIFICATION_FAILED_TERMINAL, RunState.FAILED),
            (RunState.AWAITING_APPROVAL, RunEvent.APPROVAL_REJECTED, RunState.FAILED),
        ]
        for from_state, event, to_state in path:
            assert any(
                t.from_state == from_state and t.event == event and t.to_state == to_state
                for t in m.transitions
            ), f"Missing transition: {from_state} --{event}--> {to_state}"

    def test_cancel_from_any(self):
        m = make_machine()
        non_terminal = [s for s in RunState if s not in set(m.terminal_states)]
        for s in non_terminal:
            assert any(
                t.from_state == s and t.event == RunEvent.CANCEL_RUN and t.to_state == RunState.CANCELLED
                for t in m.transitions
            ), f"cancel from {s} missing"


class TestSerialization:
    def test_machine_serialize(self):
        m = make_machine()
        data = m.model_dump()
        assert data["machine_id"] == "test-machine"
        assert data["initial_state"] == "created"
        assert len(data["transitions"]) == 24

    def test_transition_serialize(self):
        t = make_transition()
        data = t.model_dump()
        assert data["from_state"] == "created"
        assert data["event"] == "start_run"
        assert data["guards"] == []

    def test_guard_serialize(self):
        g = make_guard()
        data = g.model_dump()
        assert data["name"] == "retry_budget_available"

    def test_transition_with_guards_serialize(self):
        t = make_transition(guards=[make_guard()])
        data = t.model_dump()
        assert len(data["guards"]) == 1
        assert data["guards"][0]["name"] == "retry_budget_available"
