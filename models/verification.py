from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class CheckType(str, Enum):
    TEST = "test"
    LINT = "lint"
    TYPECHECK = "typecheck"
    SECURITY = "security"
    ACCEPTANCE = "acceptance"
    ARTIFACT = "artifact"


class CheckStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class EvidenceType(str, Enum):
    LOG = "log"
    REPORT = "report"
    FILE = "file"
    METRIC = "metric"


class VerdictStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    BLOCKED = "blocked"


class VerificationEvidence(BaseModel):
    evidence_id: str
    evidence_type: EvidenceType
    path: Optional[str] = None
    summary: Optional[str] = None
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None

    @field_validator("evidence_id")
    @classmethod
    def non_empty_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("evidence_id must not be empty")
        return value

    @model_validator(mode="after")
    def metric_evidence_has_name_and_value(self):
        if self.evidence_type == EvidenceType.METRIC:
            if not self.metric_name:
                raise ValueError("metric_name is required for METRIC evidence")
            if self.metric_value is None:
                raise ValueError("metric_value is required for METRIC evidence")
        return self


class VerificationCheck(BaseModel):
    check_id: str
    name: str
    check_type: CheckType
    blocking: bool = True
    command: Optional[str] = None
    acceptance_rule: Optional[str] = None
    status: CheckStatus = CheckStatus.PENDING
    evidence: List[VerificationEvidence] = Field(default_factory=list)
    failure_reason: Optional[str] = None

    @field_validator("check_id", "name")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def command_or_acceptance_rule(self):
        if not self.command and not self.acceptance_rule:
            raise ValueError("each check must have either command or acceptance_rule")
        return self

    @model_validator(mode="after")
    def failure_reason_when_failed(self):
        if self.status == CheckStatus.FAILED and not self.failure_reason:
            raise ValueError("failure_reason is required when status is FAILED")
        return self


class VerificationPlan(BaseModel):
    plan_id: str
    task_id: str
    checks: List[VerificationCheck] = Field(default_factory=list)

    @field_validator("plan_id")
    @classmethod
    def non_empty_plan_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("plan_id must not be empty")
        return value

    @field_validator("task_id")
    @classmethod
    def non_empty_task_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("task_id must not be empty")
        return value

    @model_validator(mode="after")
    def at_least_one_check(self):
        if not self.checks:
            raise ValueError("verification plan must contain at least one check")
        return self


class VerificationVerdict(BaseModel):
    status: VerdictStatus
    blocking_failures: List[str] = Field(default_factory=list)
    non_blocking_failures: List[str] = Field(default_factory=list)
    summary: Optional[str] = None

    @model_validator(mode="after")
    def blocking_failures_affect_verdict(self):
        if self.blocking_failures and self.status == VerdictStatus.PASS:
            raise ValueError("verdict cannot be PASS when blocking failures exist")
        return self


class VerificationResult(BaseModel):
    plan_id: str
    run_id: str
    checks: List[VerificationCheck] = Field(default_factory=list)
    verdict: VerificationVerdict
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    @field_validator("plan_id")
    @classmethod
    def non_empty_plan_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("plan_id must not be empty")
        return value

    @field_validator("run_id")
    @classmethod
    def non_empty_run_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("run_id must not be empty")
        return value

    @model_validator(mode="after")
    def finished_at_when_terminal(self):
        if self.verdict.status in (VerdictStatus.PASS, VerdictStatus.FAIL) and not self.finished_at:
            raise ValueError("finished_at is required when verdict is PASS or FAIL")
        return self
