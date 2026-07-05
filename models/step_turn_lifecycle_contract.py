from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class StepTriggerType(str, Enum):
    LOOP_ITERATION = "loop_iteration"
    MANUAL_RESUME = "manual_resume"
    RECOVERY_RESUME = "recovery_resume"
    DELEGATION_RETURN = "delegation_return"
    SCHEDULED_TICK = "scheduled_tick"
    EXTERNAL_EVENT = "external_event"


class StepPhase(str, Enum):
    SELECT = "select"
    PREPARE = "prepare"
    PLAN = "plan"
    ACT = "act"
    VERIFY = "verify"
    UPDATE = "update"
    STOP_CHECK = "stop_check"
    CLOSE = "close"


PHASE_ORDER = [
    StepPhase.SELECT, StepPhase.PREPARE, StepPhase.PLAN,
    StepPhase.ACT, StepPhase.VERIFY, StepPhase.UPDATE,
    StepPhase.STOP_CHECK, StepPhase.CLOSE,
]


class StepStatus(str, Enum):
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_STATUSES = {StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.CANCELLED}


class StepOutcome(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    NO_PROGRESS = "no_progress"
    HANDOFF_REQUIRED = "handoff_required"
    APPROVAL_REQUIRED = "approval_required"


class StepStopReason(str, Enum):
    VERIFIED_SUCCESS = "verified_success"
    VERIFICATION_FAILED = "verification_failed"
    TOOL_FAILURE = "tool_failure"
    POLICY_BLOCK = "policy_block"
    BUDGET_EXCEEDED = "budget_exceeded"
    NEEDS_HUMAN_INPUT = "needs_human_input"
    NEEDS_SUBAGENT = "needs_subagent"
    REPEATED_NO_PROGRESS = "repeated_no_progress"
    LOOP_TERMINATION = "loop_termination"
    EXTERNAL_BLOCKER = "external_blocker"


class StepSelectionContext(BaseModel):
    step_id: str
    loop_id: str
    run_id: Optional[str] = None
    iteration_id: Optional[str] = None
    selected_task_id: Optional[str] = None
    selected_feature_id: Optional[str] = None
    selection_reason: str = ""
    priority: str = "medium"
    blocking_dependencies: List[str] = Field(default_factory=list)
    input_refs: List[str] = Field(default_factory=list)

    @field_validator("step_id", "loop_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class StepIntent(BaseModel):
    intent_id: str
    objective: str
    expected_output: str = ""
    acceptance_criteria: List[str] = Field(default_factory=list)
    verification_mode: str = "auto"
    allowed_actions: List[str] = Field(default_factory=list)
    forbidden_actions: List[str] = Field(default_factory=list)
    budget_hint: Optional[str] = None
    delegation_allowed: bool = False

    @field_validator("intent_id", "objective")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def acceptance_criteria_required(self):
        if len(self.acceptance_criteria) == 0:
            raise ValueError("acceptance_criteria must not be empty for executable work")
        return self


class StepActionRecord(BaseModel):
    action_id: str
    phase: StepPhase
    action_type: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: str = "completed"
    related_tool_call_id: Optional[str] = None
    related_model_call_id: Optional[str] = None
    artifact_refs: List[str] = Field(default_factory=list)
    summary: str = ""

    @field_validator("action_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class StepVerificationRecord(BaseModel):
    verification_id: str
    verification_mode: str = "auto"
    evidence_refs: List[str] = Field(default_factory=list)
    checks_performed: List[str] = Field(default_factory=list)
    passed: bool = False
    confidence: float = 1.0
    failure_summary: str = ""
    requires_retry: bool = False
    requires_escalation: bool = False

    @field_validator("verification_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @field_validator("confidence")
    @classmethod
    def in_range(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v

    @model_validator(mode="after")
    def passed_needs_confidence(self):
        if self.passed and self.confidence < 0.5:
            raise ValueError("passed verification requires confidence >= 0.5")
        return self


class StepStateDelta(BaseModel):
    updated_task_status: Optional[str] = None
    updated_feature_status: Optional[str] = None
    memory_changes: List[str] = Field(default_factory=list)
    state_changes: List[str] = Field(default_factory=list)
    new_blockers: List[str] = Field(default_factory=list)
    resolved_blockers: List[str] = Field(default_factory=list)
    new_lessons: List[str] = Field(default_factory=list)
    next_action: str = ""

    @model_validator(mode="after")
    def state_delta_with_updates(self):
        has_any = bool(
            self.updated_task_status or self.updated_feature_status
            or self.memory_changes or self.state_changes
            or self.new_blockers or self.resolved_blockers
            or self.new_lessons or self.next_action
        )
        return self


class StepArtifactUpdateRecord(BaseModel):
    updated_loop_execution: bool = False
    updated_loop_memory: bool = False
    updated_todo: bool = False
    updated_features: bool = False
    updated_lessons: bool = False
    updated_state: bool = False
    updated_prompts: bool = False
    updated_agent_rules: bool = False
    updated_git_policy: bool = False
    update_summary: str = ""


class StepLifecycleRecord(BaseModel):
    step_id: str
    status: StepStatus
    outcome: Optional[StepOutcome] = None
    current_phase: StepPhase
    trigger_type: StepTriggerType
    selection_context: StepSelectionContext
    intent: StepIntent
    actions: List[StepActionRecord] = Field(default_factory=list)
    verification: Optional[StepVerificationRecord] = None
    state_delta: StepStateDelta = Field(default_factory=StepStateDelta)
    artifact_updates: StepArtifactUpdateRecord = Field(default_factory=StepArtifactUpdateRecord)
    started_at: datetime
    ended_at: Optional[datetime] = None
    stop_reason: Optional[StepStopReason] = None
    next_step_hint: str = ""

    @field_validator("step_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("step_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def terminal_status_requires_ended_at(self):
        if self.status in TERMINAL_STATUSES and self.ended_at is None:
            raise ValueError("terminal status requires ended_at")
        return self

    @model_validator(mode="after")
    def completed_success_needs_verification(self):
        if self.status == StepStatus.COMPLETED and self.outcome == StepOutcome.SUCCESS:
            v = self.verification
            if v is None or not v.passed:
                raise ValueError("completed+success requires verification.passed=True")
        return self

    @model_validator(mode="after")
    def failure_outcome_needs_stop_reason(self):
        if self.outcome in (StepOutcome.FAILURE, StepOutcome.NO_PROGRESS) and self.stop_reason is None:
            raise ValueError("failure/no_progress outcomes require stop_reason")
        return self

    @model_validator(mode="after")
    def no_progress_needs_next_step_hint(self):
        if self.outcome == StepOutcome.NO_PROGRESS:
            if not self.next_step_hint.strip():
                raise ValueError("no_progress requires non-empty next_step_hint")
        return self

    @model_validator(mode="after")
    def state_delta_requires_artifact_updates(self):
        has_delta = bool(
            self.state_delta.updated_task_status
            or self.state_delta.updated_feature_status
            or self.state_delta.memory_changes
            or self.state_delta.state_changes
            or self.state_delta.new_blockers
            or self.state_delta.resolved_blockers
            or self.state_delta.new_lessons
            or self.state_delta.next_action
        )
        has_updates = any((
            self.artifact_updates.updated_loop_execution,
            self.artifact_updates.updated_loop_memory,
            self.artifact_updates.updated_todo,
            self.artifact_updates.updated_features,
            self.artifact_updates.updated_lessons,
            self.artifact_updates.updated_state,
        ))
        if has_delta and not has_updates:
            raise ValueError("state-changing steps must record artifact updates")
        return self

    @model_validator(mode="after")
    def delegation_request_needs_allowed(self):
        for a in self.actions:
            if a.action_type == "delegation_request" and not self.intent.delegation_allowed:
                raise ValueError("delegation_request requires delegation_allowed=True")
        return self


class StepTurnEnvelope(BaseModel):
    envelope_id: str
    loop_id: str
    run_id: Optional[str] = None
    step: StepLifecycleRecord

    @field_validator("envelope_id", "loop_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()
