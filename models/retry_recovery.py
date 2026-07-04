from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class FailureClass(str, Enum):
    TRANSIENT_INFRA = "transient_infra"
    RATE_LIMIT = "rate_limit"
    MODEL_OUTPUT_INVALID = "model_output_invalid"
    TOOL_INPUT_INVALID = "tool_input_invalid"
    TOOL_EXECUTION_FAILED = "tool_execution_failed"
    VERIFICATION_FAILED = "verification_failed"
    APPROVAL_REJECTED = "approval_rejected"
    NON_RETRYABLE_POLICY = "non_retryable_policy"
    UNKNOWN = "unknown"


class RecoveryAction(str, Enum):
    RETRY = "retry"
    RESUME_FROM_CHECKPOINT = "resume_from_checkpoint"
    REPLAN = "replan"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    FAIL_TERMINAL = "fail_terminal"


class BackoffStrategy(str, Enum):
    NONE = "none"
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    EXPONENTIAL_WITH_JITTER = "exponential_with_jitter"


class RetryRule(BaseModel):
    failure_class: FailureClass
    max_attempts: int
    backoff_strategy: BackoffStrategy = BackoffStrategy.NONE
    base_delay_seconds: float = 0.0
    max_delay_seconds: float = 0.0
    respect_retry_after: bool = False
    allowed_actions: List[RecoveryAction] = Field(default_factory=lambda: [RecoveryAction.RETRY])
    requires_idempotency: bool = False

    @field_validator("max_attempts")
    @classmethod
    def non_negative_attempts(cls, value: int) -> int:
        if value < 0:
            raise ValueError("max_attempts must be non-negative")
        return value

    @field_validator("base_delay_seconds", "max_delay_seconds")
    @classmethod
    def non_negative_delay(cls, value: float) -> float:
        if value < 0:
            raise ValueError("delay seconds must be non-negative")
        return value

    @model_validator(mode="after")
    def max_delay_ge_base_delay(self):
        if self.max_delay_seconds > 0 and self.base_delay_seconds > self.max_delay_seconds:
            raise ValueError("max_delay_seconds must be >= base_delay_seconds")
        return self

    @model_validator(mode="after")
    def retry_action_allowed_when_idempotent(self):
        retry_in_allowed = RecoveryAction.RETRY in self.allowed_actions
        if self.requires_idempotency and retry_in_allowed:
            raise ValueError("requires_idempotency rules must not include RETRY in allowed_actions; retry only with guaranteed idempotency")
        return self


class RecoveryDecision(BaseModel):
    failure_class: FailureClass
    chosen_action: RecoveryAction
    reason: str
    retry_after_seconds: Optional[float] = None
    resume_from_checkpoint_id: Optional[str] = None

    @field_validator("reason")
    @classmethod
    def non_empty_reason(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("reason must not be empty")
        return value

    @field_validator("retry_after_seconds")
    @classmethod
    def non_negative_retry_after(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value < 0:
            raise ValueError("retry_after_seconds must be non-negative")
        return value


class RetryRecoveryPolicy(BaseModel):
    policy_id: str
    rules: List[RetryRule] = Field(default_factory=list)
    default_unknown_rule: RetryRule

    @field_validator("policy_id")
    @classmethod
    def non_empty_policy_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("policy_id must not be empty")
        return value

    @model_validator(mode="after")
    def unique_failure_classes(self):
        seen = set()
        for rule in self.rules:
            if rule.failure_class in seen:
                raise ValueError(f"duplicate failure_class: {rule.failure_class.value}")
            seen.add(rule.failure_class)
        return self

    @model_validator(mode="after")
    def default_unknown_not_in_rules(self):
        if self.default_unknown_rule.failure_class in [r.failure_class for r in self.rules]:
            raise ValueError("default_unknown_rule failure_class must not appear in rules")
        return self


def v1_default_policy() -> RetryRecoveryPolicy:
    return RetryRecoveryPolicy(
        policy_id="retry-recovery-v1",
        rules=[
            RetryRule(
                failure_class=FailureClass.TRANSIENT_INFRA,
                max_attempts=3,
                backoff_strategy=BackoffStrategy.EXPONENTIAL_WITH_JITTER,
                base_delay_seconds=1.0,
                max_delay_seconds=30.0,
                allowed_actions=[RecoveryAction.RETRY, RecoveryAction.RESUME_FROM_CHECKPOINT],
            ),
            RetryRule(
                failure_class=FailureClass.RATE_LIMIT,
                max_attempts=3,
                backoff_strategy=BackoffStrategy.EXPONENTIAL_WITH_JITTER,
                base_delay_seconds=1.0,
                max_delay_seconds=30.0,
                respect_retry_after=True,
                allowed_actions=[RecoveryAction.RETRY],
            ),
            RetryRule(
                failure_class=FailureClass.MODEL_OUTPUT_INVALID,
                max_attempts=2,
                backoff_strategy=BackoffStrategy.FIXED,
                base_delay_seconds=1.0,
                max_delay_seconds=1.0,
                allowed_actions=[RecoveryAction.RETRY, RecoveryAction.REPLAN],
            ),
            RetryRule(
                failure_class=FailureClass.TOOL_INPUT_INVALID,
                max_attempts=0,
                backoff_strategy=BackoffStrategy.NONE,
                allowed_actions=[RecoveryAction.REPLAN],
            ),
            RetryRule(
                failure_class=FailureClass.TOOL_EXECUTION_FAILED,
                max_attempts=2,
                backoff_strategy=BackoffStrategy.EXPONENTIAL_WITH_JITTER,
                base_delay_seconds=1.0,
                max_delay_seconds=10.0,
                requires_idempotency=True,
                allowed_actions=[RecoveryAction.RESUME_FROM_CHECKPOINT, RecoveryAction.REPLAN],
            ),
            RetryRule(
                failure_class=FailureClass.VERIFICATION_FAILED,
                max_attempts=1,
                backoff_strategy=BackoffStrategy.NONE,
                allowed_actions=[RecoveryAction.RETRY, RecoveryAction.REPLAN],
            ),
            RetryRule(
                failure_class=FailureClass.APPROVAL_REJECTED,
                max_attempts=0,
                backoff_strategy=BackoffStrategy.NONE,
                allowed_actions=[RecoveryAction.REPLAN, RecoveryAction.ESCALATE_TO_HUMAN, RecoveryAction.FAIL_TERMINAL],
            ),
            RetryRule(
                failure_class=FailureClass.NON_RETRYABLE_POLICY,
                max_attempts=0,
                backoff_strategy=BackoffStrategy.NONE,
                allowed_actions=[RecoveryAction.FAIL_TERMINAL],
            ),
        ],
        default_unknown_rule=RetryRule(
            failure_class=FailureClass.UNKNOWN,
            max_attempts=1,
            backoff_strategy=BackoffStrategy.FIXED,
            base_delay_seconds=1.0,
            max_delay_seconds=1.0,
            allowed_actions=[RecoveryAction.RETRY, RecoveryAction.ESCALATE_TO_HUMAN],
        ),
    )
