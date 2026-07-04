from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class ToolCallStatus(str, Enum):
    REQUESTED = "requested"
    STARTED = "started"
    SUCCESS = "success"
    ERROR = "error"
    BLOCKED = "blocked"


class ArtifactType(str, Enum):
    FILE = "file"
    LOG = "log"
    DIFF = "diff"
    TEST_REPORT = "test_report"


class RetryState(BaseModel):
    retry_count: int = 0
    max_retries: int = 0
    last_error: Optional[str] = None
    last_attempt_at: Optional[str] = None

    @field_validator("retry_count")
    @classmethod
    def retry_count_within_bounds(cls, value: int, info) -> int:
        # max_retries may not be set yet at field level; model_validator handles the cross-check
        return value


class ResumePointer(BaseModel):
    next_step_id: Optional[str] = None
    last_checkpoint_id: Optional[str] = None
    can_resume: bool = True
    resume_reason: Optional[str] = None

    @model_validator(mode="after")
    def reason_required_when_blocked(self):
        if not self.can_resume and not self.resume_reason:
            raise ValueError("resume_reason is required when can_resume is False")
        return self


class ToolCallRecord(BaseModel):
    tool_call_id: str
    tool_name: str
    status: ToolCallStatus
    arguments: Dict[str, Any] = Field(default_factory=dict)
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    @field_validator("tool_call_id")
    @classmethod
    def non_empty_tool_call_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("tool_call_id must not be empty")
        return value

    @field_validator("tool_name")
    @classmethod
    def non_empty_tool_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("tool_name must not be empty")
        return value

    @model_validator(mode="after")
    def error_required_when_errored(self):
        if self.status == ToolCallStatus.ERROR and not self.error:
            raise ValueError("error must be set when status is ERROR")
        return self


class ArtifactRecord(BaseModel):
    artifact_id: str
    artifact_type: ArtifactType
    path: str
    description: Optional[str] = None
    created_at: Optional[str] = None

    @field_validator("artifact_id")
    @classmethod
    def non_empty_artifact_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("artifact_id must not be empty")
        return value

    @field_validator("path")
    @classmethod
    def non_empty_path(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("path must not be empty")
        return value


class StepRecord(BaseModel):
    step_id: str
    name: str
    status: StepStatus
    tool_calls: List[ToolCallRecord] = Field(default_factory=list)
    artifacts: List[ArtifactRecord] = Field(default_factory=list)
    retry: RetryState = Field(default_factory=RetryState)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    @field_validator("step_id")
    @classmethod
    def non_empty_step_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("step_id must not be empty")
        return value

    @field_validator("name")
    @classmethod
    def non_empty_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be empty")
        return value

    @model_validator(mode="after")
    def finished_at_for_terminal_steps(self):
        if self.status in (StepStatus.SUCCESS, StepStatus.FAILED) and not self.finished_at:
            raise ValueError("finished_at is required for SUCCESS or FAILED steps")
        return self

    @model_validator(mode="after")
    def retry_count_within_max(self):
        if self.retry.retry_count > self.retry.max_retries:
            raise ValueError("retry_count must not exceed max_retries")
        return self


class CheckpointRecord(BaseModel):
    checkpoint_id: str
    run_id: str
    step_id: Optional[str] = None
    summary: Optional[str] = None
    created_at: str
    state_version: int = 1

    @field_validator("checkpoint_id")
    @classmethod
    def non_empty_checkpoint_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("checkpoint_id must not be empty")
        return value

    @field_validator("run_id")
    @classmethod
    def non_empty_run_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("run_id must not be empty")
        return value

    @field_validator("created_at")
    @classmethod
    def non_empty_created_at(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("created_at must not be empty")
        return value


class RunState(BaseModel):
    run_id: str
    task_id: str
    status: RunStatus
    steps: List[StepRecord] = Field(default_factory=list)
    checkpoints: List[CheckpointRecord] = Field(default_factory=list)
    resume: ResumePointer = Field(default_factory=ResumePointer)
    created_at: str
    updated_at: str

    @field_validator("run_id")
    @classmethod
    def non_empty_run_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("run_id must not be empty")
        return value

    @field_validator("task_id")
    @classmethod
    def non_empty_task_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("task_id must not be empty")
        return value

    @field_validator("created_at")
    @classmethod
    def non_empty_created_at(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("created_at must not be empty")
        return value

    @field_validator("updated_at")
    @classmethod
    def non_empty_updated_at(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("updated_at must not be empty")
        return value
