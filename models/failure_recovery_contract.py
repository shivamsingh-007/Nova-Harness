from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class FailureCategory(str, Enum):
    TOOL = "tool"
    MODEL = "model"
    POLICY = "policy"
    VALIDATION = "validation"
    CHECKPOINT = "checkpoint"
    STORAGE = "storage"
    NETWORK = "network"
    AUTH = "auth"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class FailureSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Recoverability(str, Enum):
    RECOVERABLE = "recoverable"
    PARTIALLY_RECOVERABLE = "partially_recoverable"
    NON_RECOVERABLE = "non_recoverable"
    UNKNOWN = "unknown"


class RecoveryAction(str, Enum):
    RETRY = "retry"
    SKIP = "skip"
    ESCALATE = "escalate"
    PAUSE = "pause"
    ABORT = "abort"
    RESTART_FROM_CHECKPOINT = "restart_from_checkpoint"


class ExceptionOrigin(str, Enum):
    AGENT = "agent"
    TOOL = "tool"
    MODEL = "model"
    USER = "user"
    SYSTEM = "system"
    EXTERNAL_SERVICE = "external_service"


class FailureCauseRef(BaseModel):
    cause_id: str
    cause_type: str
    detail_ref: Optional[str] = None

    @field_validator("cause_id", "cause_type")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class RetryPolicyRef(BaseModel):
    policy_id: str
    policy_name: str
    max_attempts: Optional[int] = None

    @field_validator("policy_id", "policy_name")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("max_attempts")
    @classmethod
    def non_negative(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("max_attempts must be non-negative")
        return v


class FailureRecord(BaseModel):
    failure_id: str
    category: FailureCategory
    severity: FailureSeverity
    origin: ExceptionOrigin
    summary: str
    description: Optional[str] = None
    recoverability: Recoverability = Recoverability.UNKNOWN
    causes: List[FailureCauseRef] = Field(default_factory=list)
    related_run_id: Optional[str] = None
    related_task_id: Optional[str] = None
    related_tool_call_id: Optional[str] = None
    related_model_call_id: Optional[str] = None
    related_checkpoint_id: Optional[str] = None

    @field_validator("failure_id", "summary")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class RecoveryDecisionRecord(BaseModel):
    decision_id: str
    failure_id: str
    action: RecoveryAction
    reason: str
    retry_policy_ref: Optional[RetryPolicyRef] = None
    requires_human_review: bool = False
    next_checkpoint_id: Optional[str] = None
    next_step_ref: Optional[str] = None

    @field_validator("decision_id", "failure_id", "reason")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def restart_checkpoint_needs_next_checkpoint(self):
        if self.action == RecoveryAction.RESTART_FROM_CHECKPOINT and not self.next_checkpoint_id:
            raise ValueError("RESTART_FROM_CHECKPOINT requires next_checkpoint_id")
        return self


class FailureDecisionEnvelope(BaseModel):
    envelope_id: str
    failure: FailureRecord
    recovery_decision: RecoveryDecisionRecord

    @field_validator("envelope_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def decision_failure_id_matches(self):
        if self.recovery_decision.failure_id != self.failure.failure_id:
            raise ValueError("recovery_decision.failure_id must match failure.failure_id")
        return self

    @model_validator(mode="after")
    def recoverability_not_contradict_action(self):
        rec = self.failure.recoverability
        action = self.recovery_decision.action
        if rec == Recoverability.NON_RECOVERABLE and action in (
            RecoveryAction.RETRY,
            RecoveryAction.RESTART_FROM_CHECKPOINT,
        ):
            raise ValueError("NON_RECOVERABLE failure must not use RETRY or RESTART_FROM_CHECKPOINT")
        return self

    @model_validator(mode="after")
    def restart_checkpoint_has_failure_checkpoint(self):
        if self.recovery_decision.action == RecoveryAction.RESTART_FROM_CHECKPOINT:
            if not self.failure.related_checkpoint_id and not self.recovery_decision.next_checkpoint_id:
                raise ValueError(
                    "RESTART_FROM_CHECKPOINT requires failure.related_checkpoint_id "
                    "or recovery_decision.next_checkpoint_id"
                )
        return self
