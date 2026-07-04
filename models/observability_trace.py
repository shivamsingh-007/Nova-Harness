from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class StepType(str, Enum):
    PROMPT_ASSEMBLY = "prompt_assembly"
    CONTEXT_SELECTION = "context_selection"
    TOOL_EXECUTION = "tool_execution"
    VERIFICATION = "verification"
    POLICY_CHECK = "policy_check"
    RETRY = "retry"
    APPROVAL = "approval"


class TraceEventStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class PolicyOutcomeType(str, Enum):
    ALLOWED = "allowed"
    REQUIRED_APPROVAL = "required_approval"
    BLOCKED = "blocked"
    ESCALATED = "escalated"


class ToolTrace(BaseModel):
    tool_name: str
    argument_summary: str
    status: TraceEventStatus
    latency_seconds: float
    error: Optional[str] = None

    @field_validator("tool_name", "argument_summary")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("latency_seconds")
    @classmethod
    def non_negative_latency(cls, value: float) -> float:
        if value < 0:
            raise ValueError("latency_seconds must be non-negative")
        return value


class PolicyTrace(BaseModel):
    policy_name: str
    outcome: PolicyOutcomeType
    risk_level: Optional[str] = None
    reason: str

    @field_validator("policy_name", "reason")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class VerificationTrace(BaseModel):
    check_name: str
    status: TraceEventStatus
    summary: Optional[str] = None

    @field_validator("check_name")
    @classmethod
    def non_empty_check_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("check_name must not be empty")
        return value


class RetryTrace(BaseModel):
    attempt: int
    max_attempts: int
    reason: str
    backoff_delay_seconds: Optional[float] = None

    @field_validator("reason")
    @classmethod
    def non_empty_reason(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("reason must not be empty")
        return value

    @field_validator("attempt", "max_attempts")
    @classmethod
    def non_negative_int(cls, value: int) -> int:
        if value < 0:
            raise ValueError("must be non-negative")
        return value

    @model_validator(mode="after")
    def attempt_within_max(self):
        if self.max_attempts > 0 and self.attempt > self.max_attempts:
            raise ValueError("attempt must not exceed max_attempts")
        return self

    @field_validator("backoff_delay_seconds")
    @classmethod
    def non_negative_delay(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value < 0:
            raise ValueError("backoff_delay_seconds must be non-negative")
        return value


class StepTrace(BaseModel):
    step_id: str
    step_index: int
    step_type: StepType
    status: TraceEventStatus
    started_at: str
    finished_at: Optional[str] = None
    latency_seconds: Optional[float] = None
    tool: Optional[ToolTrace] = None
    policy: Optional[PolicyTrace] = None
    verification: Optional[VerificationTrace] = None
    retry: Optional[RetryTrace] = None
    context_item_ids: List[str] = Field(default_factory=list)

    @field_validator("step_id")
    @classmethod
    def non_empty_step_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("step_id must not be empty")
        return value

    @field_validator("step_index")
    @classmethod
    def non_negative_index(cls, value: int) -> int:
        if value < 0:
            raise ValueError("step_index must be non-negative")
        return value

    @field_validator("latency_seconds")
    @classmethod
    def non_negative_latency(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value < 0:
            raise ValueError("latency_seconds must be non-negative")
        return value

    @model_validator(mode="after")
    def finished_at_for_terminal_status(self):
        if self.status in (TraceEventStatus.SUCCESS, TraceEventStatus.FAILURE, TraceEventStatus.BLOCKED):
            if not self.finished_at:
                raise ValueError("finished_at is required for terminal statuses")
            if self.latency_seconds is None:
                raise ValueError("latency_seconds is required for terminal statuses")
        return self


class TraceSummary(BaseModel):
    total_steps: int
    successful_steps: int
    failed_steps: int
    blocked_steps: int
    total_tool_calls: int
    total_policy_checks: int
    policy_blocks: int
    total_retries: int
    total_verification_checks: int
    verification_failures: int
    total_latency_seconds: float

    @field_validator(
        "total_steps", "successful_steps", "failed_steps", "blocked_steps",
        "total_tool_calls", "total_policy_checks", "policy_blocks",
        "total_retries", "total_verification_checks", "verification_failures",
    )
    @classmethod
    def non_negative_int(cls, value: int) -> int:
        if value < 0:
            raise ValueError("must be non-negative")
        return value

    @field_validator("total_latency_seconds")
    @classmethod
    def non_negative_latency(cls, value: float) -> float:
        if value < 0:
            raise ValueError("total_latency_seconds must be non-negative")
        return value

    @model_validator(mode="after")
    def step_counts_consistent(self):
        if self.successful_steps + self.failed_steps + self.blocked_steps > self.total_steps:
            raise ValueError("sum of successful, failed, and blocked steps must not exceed total_steps")
        return self


class RunTrace(BaseModel):
    run_id: str
    task_id: str
    prompt_assembly_id: Optional[str] = None
    steps: List[StepTrace]
    terminal_status: TraceEventStatus
    total_latency_seconds: float
    started_at: str
    finished_at: Optional[str] = None
    summary: Optional[TraceSummary] = None

    @field_validator("run_id", "task_id")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("total_latency_seconds")
    @classmethod
    def non_negative_latency(cls, value: float) -> float:
        if value < 0:
            raise ValueError("total_latency_seconds must be non-negative")
        return value

    @model_validator(mode="after")
    def at_least_one_step(self):
        if not self.steps:
            raise ValueError("run trace must contain at least one step")
        return self

    @model_validator(mode="after")
    def steps_have_monotonic_indexes(self):
        for i, step in enumerate(self.steps):
            if step.step_index != i:
                raise ValueError(f"step_index must be sequential starting at 0; expected {i}, got {step.step_index}")
        return self

    @model_validator(mode="after")
    def finished_at_for_terminal_run(self):
        if self.terminal_status in (TraceEventStatus.SUCCESS, TraceEventStatus.FAILURE, TraceEventStatus.BLOCKED):
            if not self.finished_at:
                raise ValueError("finished_at is required for terminal run statuses")
        return self

    @model_validator(mode="after")
    def summary_steps_match(self):
        if self.summary is not None:
            if self.summary.total_steps != len(self.steps):
                raise ValueError("summary total_steps must match the number of steps in the trace")
        return self
