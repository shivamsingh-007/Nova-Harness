from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class RunPhase(str, Enum):
    INIT = "init"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING = "waiting"
    RECOVERING = "recovering"
    FINALIZING = "finalizing"
    TERMINATED = "terminated"


class RunStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ExecutionMode(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"


class StepDependencyType(str, Enum):
    STARTS_AFTER = "starts_after"
    WAITS_FOR = "waits_for"
    DEPENDS_ON = "depends_on"
    BLOCKS = "blocks"


class RunStepRef(BaseModel):
    step_id: str
    step_type: str
    order_index: int
    status: RunStatus
    description: Optional[str] = None
    task_id: Optional[str] = None
    tool_call_id: Optional[str] = None
    model_call_id: Optional[str] = None

    @field_validator("step_id", "step_type")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("order_index")
    @classmethod
    def non_negative_index(cls, v: int) -> int:
        if v < 0:
            raise ValueError("order_index must be non-negative")
        return v


class RunBlockerRef(BaseModel):
    blocker_id: str
    blocker_type: str
    reason: str
    related_ref: Optional[str] = None

    @field_validator("blocker_id", "blocker_type", "reason")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class RunProgress(BaseModel):
    total_steps: int
    completed_steps: int = 0
    active_step_id: Optional[str] = None
    blocked_steps: int = 0
    failed_steps: int = 0

    @field_validator("total_steps", "completed_steps", "blocked_steps", "failed_steps")
    @classmethod
    def non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("must be non-negative")
        return v

    @model_validator(mode="after")
    def completed_not_exceed_total(self):
        if self.completed_steps > self.total_steps:
            raise ValueError("completed_steps must not exceed total_steps")
        return self


class ExecutionStateRecord(BaseModel):
    run_id: str
    session_id: Optional[str] = None
    task_id: Optional[str] = None
    trace_id: Optional[str] = None
    agent_id: str
    phase: RunPhase
    status: RunStatus
    mode: ExecutionMode
    steps: List[RunStepRef] = Field(default_factory=list)
    blockers: List[RunBlockerRef] = Field(default_factory=list)
    progress: RunProgress
    checkpoint_id: Optional[str] = None
    policy_decision_id: Optional[str] = None

    @field_validator("run_id", "agent_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def blocked_status_has_blockers(self):
        if self.status == RunStatus.BLOCKED and not self.blockers:
            raise ValueError("BLOCKED run status requires at least one blocker")
        return self

    @model_validator(mode="after")
    def active_step_exists(self):
        if self.progress.active_step_id is not None:
            step_ids = {s.step_id for s in self.steps}
            if self.progress.active_step_id not in step_ids:
                raise ValueError(
                    f"active_step_id '{self.progress.active_step_id}' not found in steps"
                )
        return self


class RunOrchestrationEnvelope(BaseModel):
    envelope_id: str
    run: ExecutionStateRecord

    @field_validator("envelope_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped
