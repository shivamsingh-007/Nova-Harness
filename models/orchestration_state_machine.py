from enum import Enum
from typing import List
from pydantic import BaseModel, Field, field_validator, model_validator


class RunState(str, Enum):
    CREATED = "created"
    ASSEMBLING_PROMPT = "assembling_prompt"
    MODEL_PENDING = "model_pending"
    MODEL_COMPLETED = "model_completed"
    TOOL_PENDING = "tool_pending"
    TOOL_RUNNING = "tool_running"
    VERIFYING = "verifying"
    AWAITING_APPROVAL = "awaiting_approval"
    RETRY_PENDING = "retry_pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunEvent(str, Enum):
    START_RUN = "start_run"
    PROMPT_READY = "prompt_ready"
    MODEL_RESPONSE_RECEIVED = "model_response_received"
    TOOL_CALL_REQUESTED = "tool_call_requested"
    NO_TOOL_NEEDED = "no_tool_needed"
    TOOL_APPROVED_OR_NOT_REQUIRED = "tool_approved_or_not_required"
    APPROVAL_REQUIRED = "approval_required"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_REJECTED = "approval_rejected"
    TOOL_COMPLETED = "tool_completed"
    TOOL_FAILED_RETRYABLE = "tool_failed_retryable"
    VERIFICATION_PASSED = "verification_passed"
    VERIFICATION_FAILED_RETRYABLE = "verification_failed_retryable"
    VERIFICATION_FAILED_TERMINAL = "verification_failed_terminal"
    RETRY_ALLOWED = "retry_allowed"
    CANCEL_RUN = "cancel_run"


class TransitionGuard(BaseModel):
    name: str
    description: str

    @field_validator("name")
    @classmethod
    def non_empty_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("guard name must not be empty")
        return value


class TransitionRule(BaseModel):
    from_state: RunState
    event: RunEvent
    to_state: RunState
    guards: List[TransitionGuard] = Field(default_factory=list)


class OrchestrationStateMachine(BaseModel):
    machine_id: str
    initial_state: RunState = RunState.CREATED
    terminal_states: List[RunState] = Field(
        default_factory=lambda: [RunState.SUCCEEDED, RunState.FAILED, RunState.CANCELLED]
    )
    transitions: List[TransitionRule] = Field(default_factory=list)

    @field_validator("machine_id")
    @classmethod
    def non_empty_machine_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("machine_id must not be empty")
        return value

    @model_validator(mode="after")
    def initial_state_not_terminal(self):
        if self.initial_state in set(self.terminal_states):
            raise ValueError("initial_state must not be a terminal state")
        return self

    @model_validator(mode="after")
    def unique_terminal_states(self):
        if len(set(self.terminal_states)) != len(self.terminal_states):
            raise ValueError("terminal_states must be unique")
        return self

    @model_validator(mode="after")
    def no_duplicate_transition_pairs(self):
        seen = set()
        for t in self.transitions:
            key = (t.from_state, t.event)
            if key in seen:
                raise ValueError(f"duplicate transition pair: from_state={t.from_state}, event={t.event}")
            seen.add(key)
        return self

    @model_validator(mode="after")
    def non_terminal_states_have_outgoing(self):
        terminal_set = set(self.terminal_states)
        states_with_outgoing = {t.from_state for t in self.transitions}
        used_states = {self.initial_state} | {t.from_state for t in self.transitions} | {t.to_state for t in self.transitions}
        missing = [s.value for s in used_states if s not in terminal_set and s not in states_with_outgoing]
        if missing:
            raise ValueError(f"non-terminal states without outgoing transitions: {', '.join(missing)}")
        return self


def default_transitions() -> List[TransitionRule]:
    retry_budget = [TransitionGuard(name="retry_budget_available", description="Retry count has not exceeded max_retries")]
    approval_gate = [TransitionGuard(name="approval_granted_if_required", description="Approval has been granted by the required approver")]
    return [
        TransitionRule(from_state=RunState.CREATED, event=RunEvent.START_RUN, to_state=RunState.ASSEMBLING_PROMPT),
        TransitionRule(from_state=RunState.ASSEMBLING_PROMPT, event=RunEvent.PROMPT_READY, to_state=RunState.MODEL_PENDING),
        TransitionRule(from_state=RunState.MODEL_PENDING, event=RunEvent.MODEL_RESPONSE_RECEIVED, to_state=RunState.MODEL_COMPLETED),
        TransitionRule(from_state=RunState.MODEL_COMPLETED, event=RunEvent.TOOL_CALL_REQUESTED, to_state=RunState.TOOL_PENDING),
        TransitionRule(from_state=RunState.MODEL_COMPLETED, event=RunEvent.NO_TOOL_NEEDED, to_state=RunState.VERIFYING),
        TransitionRule(from_state=RunState.TOOL_PENDING, event=RunEvent.TOOL_APPROVED_OR_NOT_REQUIRED, to_state=RunState.TOOL_RUNNING),
        TransitionRule(from_state=RunState.TOOL_PENDING, event=RunEvent.APPROVAL_REQUIRED, to_state=RunState.AWAITING_APPROVAL),
        TransitionRule(from_state=RunState.AWAITING_APPROVAL, event=RunEvent.APPROVAL_GRANTED, to_state=RunState.TOOL_RUNNING, guards=approval_gate),
        TransitionRule(from_state=RunState.AWAITING_APPROVAL, event=RunEvent.APPROVAL_REJECTED, to_state=RunState.FAILED),
        TransitionRule(from_state=RunState.TOOL_RUNNING, event=RunEvent.TOOL_COMPLETED, to_state=RunState.VERIFYING),
        TransitionRule(from_state=RunState.TOOL_RUNNING, event=RunEvent.TOOL_FAILED_RETRYABLE, to_state=RunState.RETRY_PENDING),
        TransitionRule(from_state=RunState.VERIFYING, event=RunEvent.VERIFICATION_PASSED, to_state=RunState.SUCCEEDED),
        TransitionRule(from_state=RunState.VERIFYING, event=RunEvent.VERIFICATION_FAILED_RETRYABLE, to_state=RunState.RETRY_PENDING),
        TransitionRule(from_state=RunState.VERIFYING, event=RunEvent.VERIFICATION_FAILED_TERMINAL, to_state=RunState.FAILED),
        TransitionRule(from_state=RunState.RETRY_PENDING, event=RunEvent.RETRY_ALLOWED, to_state=RunState.ASSEMBLING_PROMPT, guards=retry_budget),
        # Cancel from every non-terminal state
        TransitionRule(from_state=RunState.CREATED, event=RunEvent.CANCEL_RUN, to_state=RunState.CANCELLED),
        TransitionRule(from_state=RunState.ASSEMBLING_PROMPT, event=RunEvent.CANCEL_RUN, to_state=RunState.CANCELLED),
        TransitionRule(from_state=RunState.MODEL_PENDING, event=RunEvent.CANCEL_RUN, to_state=RunState.CANCELLED),
        TransitionRule(from_state=RunState.MODEL_COMPLETED, event=RunEvent.CANCEL_RUN, to_state=RunState.CANCELLED),
        TransitionRule(from_state=RunState.TOOL_PENDING, event=RunEvent.CANCEL_RUN, to_state=RunState.CANCELLED),
        TransitionRule(from_state=RunState.TOOL_RUNNING, event=RunEvent.CANCEL_RUN, to_state=RunState.CANCELLED),
        TransitionRule(from_state=RunState.VERIFYING, event=RunEvent.CANCEL_RUN, to_state=RunState.CANCELLED),
        TransitionRule(from_state=RunState.AWAITING_APPROVAL, event=RunEvent.CANCEL_RUN, to_state=RunState.CANCELLED),
        TransitionRule(from_state=RunState.RETRY_PENDING, event=RunEvent.CANCEL_RUN, to_state=RunState.CANCELLED),
    ]


def default_machine(machine_id: str = "harness-v1") -> OrchestrationStateMachine:
    return OrchestrationStateMachine(
        machine_id=machine_id,
        initial_state=RunState.CREATED,
        terminal_states=[RunState.SUCCEEDED, RunState.FAILED, RunState.CANCELLED],
        transitions=default_transitions(),
    )
