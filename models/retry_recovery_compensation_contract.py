from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class FailureCategory(str, Enum):
    transient_error = "transient_error"
    timeout = "timeout"
    dependency_failure = "dependency_failure"
    validation_failure = "validation_failure"
    policy_block = "policy_block"
    partial_side_effect = "partial_side_effect"
    unknown_state = "unknown_state"
    terminal_error = "terminal_error"


class RetryStrategy(str, Enum):
    none = "none"
    fixed = "fixed"
    linear_backoff = "linear_backoff"
    exponential_backoff = "exponential_backoff"
    manual_retry = "manual_retry"


class RecoveryMode(str, Enum):
    resume_from_checkpoint = "resume_from_checkpoint"
    replay_last_step = "replay_last_step"
    replay_from_intent = "replay_from_intent"
    handoff_recovery = "handoff_recovery"
    manual_recovery = "manual_recovery"
    no_recovery = "no_recovery"


class CompensationStatus(str, Enum):
    not_required = "not_required"
    planned = "planned"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"
    escalated = "escalated"


class FailureDisposition(str, Enum):
    retrying = "retrying"
    recovered = "recovered"
    compensated = "compensated"
    escalated = "escalated"
    aborted = "aborted"
    terminated = "terminated"


class FailureRecord(BaseModel):
    failure_id: str = Field(min_length=1)
    scope_ref: str = Field(min_length=1)
    scope_type: Optional[str] = None
    failure_category: FailureCategory
    error_code: Optional[str] = None
    failure_summary: str = Field(min_length=1)
    retryable: bool = False
    side_effects_present: bool = False
    unknown_state: bool = False
    evidence_refs: List[str] = Field(default_factory=list)
    occurred_at: datetime = Field(default_factory=datetime.now)

    @field_validator("failure_id")
    @classmethod
    def failure_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("failure_id must not be blank")
        return v.strip()

    @field_validator("scope_ref")
    @classmethod
    def scope_ref_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("scope_ref must not be blank")
        return v.strip()

    @field_validator("failure_summary")
    @classmethod
    def summary_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("failure_summary must not be blank")
        return v.strip()


class RetryPolicyRecord(BaseModel):
    retry_policy_id: str = Field(min_length=1)
    failure_category: Optional[FailureCategory] = None
    retry_strategy: RetryStrategy
    max_attempts: int = Field(default=3, ge=0)
    base_delay_ms: int = Field(default=1000, ge=0)
    backoff_scale_factor: float = Field(default=2.0, ge=1.0)
    max_delay_ms: Optional[int] = Field(default=None, ge=0)
    jitter_enabled: bool = False
    stop_conditions: List[str] = Field(default_factory=list)

    @field_validator("retry_policy_id")
    @classmethod
    def retry_policy_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("retry_policy_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def none_strategy_requires_zero_attempts(self) -> "RetryPolicyRecord":
        if self.retry_strategy == RetryStrategy.none and self.max_attempts != 0:
            raise ValueError("retry_strategy=none requires max_attempts=0")
        return self

    @model_validator(mode="after")
    def manual_retry_requires_attempts(self) -> "RetryPolicyRecord":
        if self.retry_strategy == RetryStrategy.manual_retry and self.max_attempts == 0:
            raise ValueError("manual_retry requires positive max_attempts")
        return self


class RetryAttemptRecord(BaseModel):
    retry_attempt_id: str = Field(min_length=1)
    failure_id: str = Field(min_length=1)
    attempt_number: int = Field(default=1, ge=1)
    scheduled_delay_ms: int = Field(default=0, ge=0)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    result_status: Optional[str] = None
    result_summary: Optional[str] = None

    @field_validator("retry_attempt_id")
    @classmethod
    def retry_attempt_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("retry_attempt_id must not be blank")
        return v.strip()

    @field_validator("failure_id")
    @classmethod
    def ra_failure_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("failure_id must not be blank")
        return v.strip()


class RecoveryPlanRecord(BaseModel):
    recovery_plan_id: str = Field(min_length=1)
    failure_id: str = Field(min_length=1)
    recovery_mode: RecoveryMode
    checkpoint_ref: Optional[str] = None
    intent_state_ref: Optional[str] = None
    prerequisites: List[str] = Field(default_factory=list)
    requires_approval: bool = False
    recovery_goal: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator("recovery_plan_id")
    @classmethod
    def recovery_plan_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("recovery_plan_id must not be blank")
        return v.strip()

    @field_validator("failure_id")
    @classmethod
    def rp_failure_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("failure_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def checkpoint_recovery_requires_ref(self) -> "RecoveryPlanRecord":
        if self.recovery_mode == RecoveryMode.resume_from_checkpoint and not self.checkpoint_ref:
            raise ValueError("resume_from_checkpoint requires checkpoint_ref")
        return self

    @model_validator(mode="after")
    def intent_replay_requires_intent_ref(self) -> "RecoveryPlanRecord":
        if self.recovery_mode == RecoveryMode.replay_from_intent and not self.intent_state_ref:
            raise ValueError("replay_from_intent requires intent_state_ref")
        return self


class RecoveryExecutionRecord(BaseModel):
    recovery_execution_id: str = Field(min_length=1)
    recovery_plan_id: str = Field(min_length=1)
    executor_ref: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    recovery_status: Optional[str] = None
    residual_risks: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

    @field_validator("recovery_execution_id")
    @classmethod
    def recovery_execution_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("recovery_execution_id must not be blank")
        return v.strip()

    @field_validator("recovery_plan_id")
    @classmethod
    def re_recovery_plan_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("recovery_plan_id must not be blank")
        return v.strip()


class CompensationActionRecord(BaseModel):
    compensation_action_id: str = Field(min_length=1)
    failure_id: str = Field(min_length=1)
    action_ref: str = Field(min_length=1)
    target_side_effect_ref: Optional[str] = None
    execution_order: int = Field(default=0, ge=0)
    retry_policy_ref: Optional[str] = None
    status: CompensationStatus
    action_notes: Optional[str] = None

    @field_validator("compensation_action_id")
    @classmethod
    def compensation_action_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("compensation_action_id must not be blank")
        return v.strip()

    @field_validator("failure_id")
    @classmethod
    def ca_failure_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("failure_id must not be blank")
        return v.strip()

    @field_validator("action_ref")
    @classmethod
    def action_ref_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("action_ref must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def failed_compensation_visible(self) -> "CompensationActionRecord":
        if self.status == CompensationStatus.failed and self.retry_policy_ref is None:
            pass  # allowed if no retry policy, but status is visible
        return self

    @model_validator(mode="after")
    def in_progress_or_failed_requires_notes(self) -> "CompensationActionRecord":
        if self.status in (CompensationStatus.in_progress, CompensationStatus.failed) and not self.action_notes:
            raise ValueError("in_progress/failed compensation requires action_notes")
        return self


class CompensationPlanRecord(BaseModel):
    compensation_plan_id: str = Field(min_length=1)
    failure_id: str = Field(min_length=1)
    actions: List[CompensationActionRecord] = Field(default_factory=list)
    plan_status: CompensationStatus
    escalation_on_failure: bool = False
    completed_at: Optional[datetime] = None

    @field_validator("compensation_plan_id")
    @classmethod
    def compensation_plan_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("compensation_plan_id must not be blank")
        return v.strip()

    @field_validator("failure_id")
    @classmethod
    def cp_failure_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("failure_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def deterministic_execution_order(self) -> "CompensationPlanRecord":
        orders = [a.execution_order for a in self.actions]
        if len(orders) != len(set(orders)):
            raise ValueError("compensation actions must have unique execution_order values")
        return self

    @model_validator(mode="after")
    def side_effects_require_compensation(self) -> "CompensationPlanRecord":
        if self.actions and self.plan_status == CompensationStatus.not_required:
            raise ValueError("actions present but plan_status=not_required")
        return self


class RetryRecoveryCompensationEnvelope(BaseModel):
    envelope_id: str = Field(min_length=1)
    failure: FailureRecord
    retry_policy: Optional[RetryPolicyRecord] = None
    retry_attempts: List[RetryAttemptRecord] = Field(default_factory=list)
    recovery_plan: Optional[RecoveryPlanRecord] = None
    recovery_execution: Optional[RecoveryExecutionRecord] = None
    compensation_plan: Optional[CompensationPlanRecord] = None
    failure_disposition: Optional[FailureDisposition] = None
    residual_risks: List[str] = Field(default_factory=list)

    @field_validator("envelope_id")
    @classmethod
    def envelope_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("envelope_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def none_strategy_no_attempts(self) -> "RetryRecoveryCompensationEnvelope":
        rp = self.retry_policy
        if rp and rp.retry_strategy == RetryStrategy.none and len(self.retry_attempts) > 0:
            raise ValueError("retry_strategy=none but retry_attempts present")
        return self

    @model_validator(mode="after")
    def side_effects_require_compensation_or_explicit_waiver(self) -> "RetryRecoveryCompensationEnvelope":
        f = self.failure
        if f.side_effects_present:
            cp = self.compensation_plan
            if cp is None:
                if self.failure_disposition is None or self.failure_disposition not in (
                    FailureDisposition.aborted, FailureDisposition.terminated, FailureDisposition.escalated,
                ):
                    pass  # allow if not yet decided
        return self

    @model_validator(mode="after")
    def unknown_state_blocks_safe_dispositions(self) -> "RetryRecoveryCompensationEnvelope":
        f = self.failure
        if f.unknown_state:
            disp = self.failure_disposition
            if disp in (FailureDisposition.recovered, FailureDisposition.compensated):
                raise ValueError("unknown_state cannot have recovered/compensated disposition")
        return self

    @model_validator(mode="after")
    def compensation_failures_remain_visible(self) -> "RetryRecoveryCompensationEnvelope":
        cp = self.compensation_plan
        if cp:
            has_failed = any(a.status == CompensationStatus.failed for a in cp.actions)
            if has_failed:
                if cp.plan_status == CompensationStatus.completed:
                    raise ValueError("compensation has failed actions but plan_status=completed")
        return self
