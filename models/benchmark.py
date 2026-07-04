from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class TaskType(str, Enum):
    CODING = "coding"
    DEBUGGING = "debugging"
    REFACTOR = "refactor"
    REPORT = "report"


class GraderType(str, Enum):
    DETERMINISTIC = "deterministic"
    LLM_JUDGE = "llm_judge"
    HUMAN = "human"


class MetricName(str, Enum):
    TASK_SUCCESS = "task_success"
    TOOL_SUCCESS = "tool_success"
    LATENCY_SECONDS = "latency_seconds"
    COST_USD = "cost_usd"
    RETRY_COUNT = "retry_count"
    SAFETY_VIOLATIONS = "safety_violations"
    VERIFICATION_PASS = "verification_pass"


class VerdictStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"


class TaskReference(BaseModel):
    reference_id: str
    description: str
    expected_artifacts: List[str] = Field(default_factory=list)
    reference_notes: Optional[str] = None

    @field_validator("reference_id", "description")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class BenchmarkTask(BaseModel):
    task_id: str
    name: str
    task_type: TaskType
    prompt: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    reference: Optional[TaskReference] = None
    tags: List[str] = Field(default_factory=list)

    @field_validator("task_id", "name", "prompt")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class GraderDefinition(BaseModel):
    grader_id: str
    name: str
    grader_type: GraderType
    rubric: Optional[str] = None
    pass_condition: str

    @field_validator("grader_id", "name", "pass_condition")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class MetricResult(BaseModel):
    metric_name: MetricName
    value: float
    unit: Optional[str] = None
    threshold: Optional[float] = None
    passed: Optional[bool] = None

    @field_validator("value")
    @classmethod
    def non_negative_metric_value(cls, value: float, info) -> float:
        non_neg = {MetricName.LATENCY_SECONDS, MetricName.COST_USD,
                   MetricName.RETRY_COUNT, MetricName.SAFETY_VIOLATIONS}
        metric_name = info.data.get("metric_name")
        if metric_name in non_neg and value < 0:
            raise ValueError(f"{metric_name.value} must be non-negative")
        return value


class BenchmarkRun(BaseModel):
    run_id: str
    suite_id: str
    task_id: str
    harness_version: str
    model_name: str
    graders: List[GraderDefinition] = Field(default_factory=list)
    metrics: List[MetricResult] = Field(default_factory=list)
    verdict: VerdictStatus
    notes: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    @field_validator("run_id", "suite_id", "task_id", "harness_version", "model_name")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def at_least_one_grader(self):
        if not self.graders:
            raise ValueError("benchmark run must have at least one grader")
        return self

    @model_validator(mode="after")
    def at_least_one_metric(self):
        if not self.metrics:
            raise ValueError("benchmark run must have at least one metric")
        return self

    @model_validator(mode="after")
    def finished_at_for_completed_runs(self):
        if self.verdict in (VerdictStatus.PASS, VerdictStatus.FAIL) and not self.finished_at:
            raise ValueError("finished_at is required when verdict is PASS or FAIL")
        return self


class BenchmarkSummary(BaseModel):
    suite_id: str
    total_runs: int
    pass_rate: float
    average_latency_seconds: Optional[float] = None
    average_cost_usd: Optional[float] = None
    total_safety_violations: int = 0

    @field_validator("suite_id")
    @classmethod
    def non_empty_suite_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("suite_id must not be empty")
        return value

    @field_validator("pass_rate")
    @classmethod
    def between_zero_and_one(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("pass_rate must be between 0 and 1")
        return value

    @field_validator("total_runs")
    @classmethod
    def non_negative_runs(cls, value: int) -> int:
        if value < 0:
            raise ValueError("total_runs must be non-negative")
        return value

    @field_validator("total_safety_violations")
    @classmethod
    def non_negative_violations(cls, value: int) -> int:
        if value < 0:
            raise ValueError("total_safety_violations must be non-negative")
        return value


class BenchmarkSuite(BaseModel):
    suite_id: str
    name: str
    tasks: List[BenchmarkTask] = Field(default_factory=list)
    summary: Optional[BenchmarkSummary] = None

    @field_validator("suite_id", "name")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def at_least_one_task(self):
        if not self.tasks:
            raise ValueError("benchmark suite must contain at least one task")
        return self
