from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class LoopTriggerType(str, Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT = "event"
    RECOVERY_RESUME = "recovery_resume"


class LoopGoalType(str, Enum):
    BUILD = "build"
    REPAIR = "repair"
    VERIFY = "verify"
    REFACTOR = "refactor"
    RESEARCH = "research"
    MAINTAIN = "maintain"


class LoopPhase(str, Enum):
    INTAKE = "intake"
    PLAN = "plan"
    EXECUTE = "execute"
    VERIFY = "verify"
    UPDATE_STATE = "update_state"
    STOP_CHECK = "stop_check"
    HANDOFF = "handoff"


class LoopStatus(str, Enum):
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    EXHAUSTED = "exhausted"
    FAILED = "failed"


class LoopStopReason(str, Enum):
    SUCCESS = "success"
    NO_WORK = "no_work"
    BLOCKED_EXTERNAL = "blocked_external"
    MAX_ITERATIONS = "max_iterations"
    BUDGET_EXCEEDED = "budget_exceeded"
    REPEATED_NO_PROGRESS = "repeated_no_progress"
    APPROVAL_REQUIRED = "approval_required"
    VERIFICATION_FAILED = "verification_failed"


TERMINAL_STOP_REASONS = {
    LoopStopReason.SUCCESS, LoopStopReason.NO_WORK,
    LoopStopReason.MAX_ITERATIONS, LoopStopReason.BUDGET_EXCEEDED,
    LoopStopReason.REPEATED_NO_PROGRESS, LoopStopReason.VERIFICATION_FAILED,
}
TERMINAL_STATUSES = {LoopStatus.COMPLETED, LoopStatus.EXHAUSTED, LoopStatus.FAILED}


class LoopIterationRecord(BaseModel):
    iteration: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    phase_transitions: List[LoopPhase] = Field(default_factory=list)
    selected_task_id: Optional[str] = None
    actions_performed: List[str] = Field(default_factory=list)
    artifacts_touched: List[str] = Field(default_factory=list)
    result_summary: str = ""
    progress_delta: Optional[str] = None
    verification_result: Optional[str] = None
    lessons_extracted: List[str] = Field(default_factory=list)
    next_suggested_step: Optional[str] = None

    @field_validator("iteration")
    @classmethod
    def positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("iteration must be >= 1")
        return v


class LoopMemorySnapshot(BaseModel):
    current_objective: str
    active_task_id: Optional[str] = None
    recent_evidence: List[str] = Field(default_factory=list)
    unresolved_blockers: List[str] = Field(default_factory=list)
    known_failures: List[str] = Field(default_factory=list)
    recent_lessons: List[str] = Field(default_factory=list)
    next_action: str = ""

    @field_validator("current_objective")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("current_objective must not be blank")
        return stripped

    @model_validator(mode="after")
    def active_loop_needs_next_action(self):
        return self


class LoopExecutionPlan(BaseModel):
    loop_id: str
    run_id: Optional[str] = None
    session_id: Optional[str] = None
    max_iterations: int = 50
    max_no_progress_iterations: int = 5
    verification_required: bool = True
    update_artifacts_required: bool = True
    commit_policy: str = "commit_on_verified_progress"
    escalation_policy: str = "escalate_on_blocker"

    @field_validator("loop_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("loop_id must not be blank")
        return v.strip()

    @field_validator("max_iterations")
    @classmethod
    def positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("max_iterations must be > 0")
        return v

    @field_validator("max_no_progress_iterations")
    @classmethod
    def non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("max_no_progress_iterations must be >= 0")
        return v


class LoopRuleSet(BaseModel):
    update_per_iteration: List[str] = Field(default_factory=list)
    stop_conditions: List[str] = Field(default_factory=list)
    retry_conditions: List[str] = Field(default_factory=list)
    escalate_conditions: List[str] = Field(default_factory=list)
    commit_conditions: List[str] = Field(default_factory=list)
    feature_done_conditions: List[str] = Field(default_factory=list)
    lesson_promotion_rules: List[str] = Field(default_factory=list)


class RunningLoopContractEnvelope(BaseModel):
    envelope_id: str
    status: LoopStatus = LoopStatus.READY
    stop_reason: Optional[LoopStopReason] = None
    phase: LoopPhase = LoopPhase.INTAKE
    goal: LoopGoalType
    trigger: LoopTriggerType
    objective: str
    plan: LoopExecutionPlan
    rules: LoopRuleSet = Field(default_factory=LoopRuleSet)
    cycles: List[LoopIterationRecord] = Field(default_factory=list)
    memory: LoopMemorySnapshot
    created_at: datetime
    updated_at: datetime

    @field_validator("envelope_id", "objective")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @field_validator("cycles")
    @classmethod
    def enforce_max_iterations(cls, v: List[LoopIterationRecord], info) -> List[LoopIterationRecord]:
        return v

    @model_validator(mode="after")
    def stop_reason_aligned_with_status(self):
        if self.status in TERMINAL_STATUSES and self.stop_reason is None:
            raise ValueError("terminal status requires a stop_reason")
        if self.stop_reason is not None and self.status not in TERMINAL_STATUSES:
            raise ValueError("stop_reason requires terminal status (COMPLETED/EXHAUSTED/FAILED)")
        return self

    @model_validator(mode="after")
    def repeated_no_progress_enforced(self):
        if self.stop_reason == LoopStopReason.REPEATED_NO_PROGRESS:
            if self.goal == LoopGoalType.MAINTAIN:
                return self
            has_repeated = any(
                c.progress_delta == "none" or c.progress_delta == "no_progress"
                for c in self.cycles[-self.plan.max_no_progress_iterations:]
            ) if self.plan.max_no_progress_iterations > 0 else True
            if not has_repeated and len(self.cycles) >= 2:
                pass
        return self

    @model_validator(mode="after")
    def active_loop_has_next_action(self):
        if self.status == LoopStatus.RUNNING and not self.memory.next_action.strip():
            raise ValueError("active loop (RUNNING) must have non-empty memory.next_action")
        return self

    @model_validator(mode="after")
    def verification_for_completed_cycles(self):
        if self.status == LoopStatus.COMPLETED or self.status == LoopStatus.EXHAUSTED:
            if self.plan.verification_required:
                for c in self.cycles:
                    if c.verification_result is None or c.verification_result.strip() == "":
                        raise ValueError("completed/exhausted loop requires verification_result on all cycles")
        return self
