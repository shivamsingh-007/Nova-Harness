from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class FailureCategory(str, Enum):
    TASK_INPUT = "task_input"
    CONTEXT_SELECTION = "context_selection"
    PROMPT_ASSEMBLY = "prompt_assembly"
    PROVIDER = "provider"
    TOOL_INVOCATION = "tool_invocation"
    SAFETY_POLICY = "safety_policy"
    APPROVAL = "approval"
    VERIFICATION = "verification"
    PERSISTENCE = "persistence"
    ORCHESTRATION = "orchestration"
    BUDGET_LIMIT = "budget_limit"
    UNKNOWN = "unknown"


class FailureSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RecoveryDisposition(str, Enum):
    RETRYABLE = "retryable"
    NON_RETRYABLE = "non_retryable"
    ESCALATE = "escalate"
    USER_ACTION_REQUIRED = "user_action_required"
    BLOCK_AND_AUDIT = "block_and_audit"


class ErrorContext(BaseModel):
    run_id: str
    trace_id: Optional[str] = None
    step_id: Optional[str] = None
    operation: str
    component: str

    @field_validator("run_id", "operation", "component")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class ErrorChainLink(BaseModel):
    code: str
    message: str
    category: FailureCategory

    @field_validator("code", "message")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class ErrorEnvelope(BaseModel):
    error_id: str
    code: str
    message: str
    category: FailureCategory
    severity: FailureSeverity
    retryable: bool
    user_safe: bool
    recovery_disposition: RecoveryDisposition
    context: ErrorContext
    details: List[str] = Field(default_factory=list)
    cause_chain: List[ErrorChainLink] = Field(default_factory=list)

    @field_validator("error_id", "code", "message")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def validate_retryable_consistency(self):
        if self.retryable and self.recovery_disposition == RecoveryDisposition.NON_RETRYABLE:
            raise ValueError("retryable=True is inconsistent with NON_RETRYABLE disposition")
        return self

    @model_validator(mode="after")
    def validate_block_and_audit_category(self):
        if self.recovery_disposition == RecoveryDisposition.BLOCK_AND_AUDIT:
            if self.category not in (FailureCategory.SAFETY_POLICY, FailureCategory.APPROVAL,
                                     FailureCategory.BUDGET_LIMIT, FailureCategory.UNKNOWN):
                raise ValueError("BLOCK_AND_AUDIT only valid for safety/approval/budget/unknown categories")
        return self

    @model_validator(mode="after")
    def validate_critical_severity(self):
        if self.severity == FailureSeverity.CRITICAL:
            if self.recovery_disposition not in (RecoveryDisposition.ESCALATE, RecoveryDisposition.BLOCK_AND_AUDIT):
                raise ValueError("CRITICAL severity should map to ESCALATE or BLOCK_AND_AUDIT")
        return self


class PublicErrorView(BaseModel):
    error_id: str
    code: str
    message: str
    category: FailureCategory
    retryable: bool

    @field_validator("error_id", "code", "message")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class FailureClassification(BaseModel):
    error_id: str
    primary_category: FailureCategory
    severity: FailureSeverity
    recovery_disposition: RecoveryDisposition
    should_trigger_alert: bool = False

    @field_validator("error_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def validate_alert_consistency(self):
        if self.should_trigger_alert and self.severity not in (FailureSeverity.ERROR, FailureSeverity.CRITICAL):
            raise ValueError("alerts should only be triggered for ERROR or CRITICAL severity")
        return self
