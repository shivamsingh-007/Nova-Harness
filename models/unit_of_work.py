from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    NEEDS_INPUT = "needs_input"
    NEEDS_APPROVAL = "needs_approval"
    FAILED = "failed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskKind(str, Enum):
    ANALYSIS = "analysis"
    IMPLEMENTATION = "implementation"
    REVIEW = "review"
    RESEARCH = "research"
    TRANSFORMATION = "transformation"


class TaskFailureMode(str, Enum):
    STOP = "stop"
    RETRY = "retry"
    ESCALATE = "escalate"
    REQUEST_INPUT = "request_input"


class ConstraintSeverity(str, Enum):
    SOFT = "soft"
    HARD = "hard"


class TaskInputRef(BaseModel):
    input_id: str
    input_type: str
    source_ref: str
    required: bool = True

    @field_validator("input_id", "input_type", "source_ref")
    @classmethod
    def non_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class TaskOutputSpec(BaseModel):
    output_id: str
    output_type: str
    description: str
    required: bool = True

    @field_validator("output_id", "output_type", "description")
    @classmethod
    def non_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class TaskConstraint(BaseModel):
    constraint_id: str
    category: str
    description: str
    severity: ConstraintSeverity

    @field_validator("constraint_id", "category", "description")
    @classmethod
    def non_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class AcceptanceCriterion(BaseModel):
    criterion_id: str
    description: str
    required: bool = True

    @field_validator("criterion_id", "description")
    @classmethod
    def non_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class TaskSpec(BaseModel):
    task_id: str
    title: str
    task_kind: TaskKind
    objective: str
    in_scope: List[str] = Field(default_factory=list)
    out_of_scope: List[str] = Field(default_factory=list)
    inputs: List[TaskInputRef] = Field(default_factory=list)
    expected_outputs: List[TaskOutputSpec] = Field(default_factory=list)
    constraints: List[TaskConstraint] = Field(default_factory=list)
    acceptance_criteria: List[AcceptanceCriterion] = Field(default_factory=list)
    failure_mode: TaskFailureMode = TaskFailureMode.STOP
    priority: TaskPriority = TaskPriority.NORMAL

    @field_validator("task_id", "title", "objective")
    @classmethod
    def non_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("title")
    @classmethod
    def no_placeholder_title(cls, value: str) -> str:
        if value.strip().lower() in ("untitled", "tbd", "todo", "task", "new task"):
            raise ValueError("title must not be a placeholder")
        return value

    @field_validator("objective")
    @classmethod
    def no_placeholder_objective(cls, value: str) -> str:
        if value.strip().lower() in ("tbd", "todo", "objective", "goal"):
            raise ValueError("objective must not be a placeholder")
        return value

    @field_validator("in_scope", "out_of_scope")
    @classmethod
    def no_blank_items(cls, value: List[str]) -> List[str]:
        cleaned = [v.strip() for v in value]
        if any(not v for v in cleaned):
            raise ValueError("scope items must not be blank")
        return cleaned

    @model_validator(mode="after")
    def no_scope_contradiction(self):
        overlap = set(self.in_scope) & set(self.out_of_scope)
        if overlap:
            raise ValueError(f"in_scope and out_of_scope overlap: {sorted(overlap)}")
        return self

class TaskEnvelope(BaseModel):
    envelope_id: str
    run_id: str
    task: TaskSpec
    status: TaskStatus
    assigned_agent_id: Optional[str] = None
    parent_task_id: Optional[str] = None

    @field_validator("envelope_id", "run_id")
    @classmethod
    def non_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def executable_requires_acceptance_criteria(self):
        if self.status in (TaskStatus.READY, TaskStatus.RUNNING, TaskStatus.COMPLETED):
            if not self.task.acceptance_criteria:
                raise ValueError(
                    f"tasks with status '{self.status.value}' must have at least one acceptance criterion"
                )
        return self


