from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class BudgetScope(str, Enum):
    RUN = "run"
    USER = "user"
    TENANT = "tenant"
    MODEL = "model"
    TOOL = "tool"
    ENVIRONMENT = "environment"


class LimitAction(str, Enum):
    ALLOW = "allow"
    WARN = "warn"
    THROTTLE = "throttle"
    BLOCK = "block"


class RateWindow(str, Enum):
    PER_MINUTE = "per_minute"
    PER_HOUR = "per_hour"
    PER_DAY = "per_day"
    PER_RUN = "per_run"


class TokenBudget(BaseModel):
    max_input_tokens: int
    max_output_tokens: int
    max_total_tokens: int

    @field_validator("max_input_tokens", "max_output_tokens", "max_total_tokens")
    @classmethod
    def validate_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("must be at least 1")
        return value

    @model_validator(mode="after")
    def validate_consistency(self):
        if self.max_total_tokens < self.max_input_tokens:
            raise ValueError("max_total_tokens must be >= max_input_tokens")
        if self.max_total_tokens < self.max_output_tokens:
            raise ValueError("max_total_tokens must be >= max_output_tokens")
        return self


class CostBudget(BaseModel):
    max_cost_usd: float
    warn_cost_usd: Optional[float] = None

    @field_validator("max_cost_usd")
    @classmethod
    def validate_max_cost(cls, value: float) -> float:
        if value < 0:
            raise ValueError("max_cost_usd must be non-negative")
        return value

    @field_validator("warn_cost_usd")
    @classmethod
    def validate_warn_cost(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value < 0:
            raise ValueError("warn_cost_usd must be non-negative")
        return value

    @model_validator(mode="after")
    def validate_warn_le_max(self):
        if self.warn_cost_usd is not None and self.warn_cost_usd > self.max_cost_usd:
            raise ValueError("warn_cost_usd must be <= max_cost_usd")
        return self


class RuntimeBudget(BaseModel):
    max_runtime_seconds: int
    max_steps: int
    max_retries: int

    @field_validator("max_runtime_seconds", "max_steps")
    @classmethod
    def validate_positive_int(cls, value: int) -> int:
        if value < 1:
            raise ValueError("must be at least 1")
        return value

    @field_validator("max_retries")
    @classmethod
    def validate_non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("max_retries must be non-negative")
        return value


class ToolCallBudget(BaseModel):
    max_total_tool_calls: int
    max_tool_calls_per_tool: int
    restricted_tools: List[str] = Field(default_factory=list)

    @field_validator("max_total_tool_calls", "max_tool_calls_per_tool")
    @classmethod
    def validate_positive_int(cls, value: int) -> int:
        if value < 1:
            raise ValueError("must be at least 1")
        return value


class RateLimitRule(BaseModel):
    scope: BudgetScope
    window: RateWindow
    identifier_key: str
    max_requests: Optional[int] = None
    max_tokens: Optional[int] = None
    max_cost_usd: Optional[float] = None
    action_on_exceed: LimitAction

    @field_validator("identifier_key")
    @classmethod
    def validate_identifier_key(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("identifier_key must not be empty")
        return value

    @field_validator("max_cost_usd")
    @classmethod
    def validate_max_cost(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value < 0:
            raise ValueError("max_cost_usd must be non-negative")
        return value

    @field_validator("max_requests", "max_tokens")
    @classmethod
    def validate_optional_positive(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value < 1:
            raise ValueError("must be at least 1 if provided")
        return value


class BudgetPolicy(BaseModel):
    policy_id: str
    token_budget: TokenBudget
    cost_budget: CostBudget
    runtime_budget: RuntimeBudget
    tool_call_budget: ToolCallBudget
    rate_limit_rules: List[RateLimitRule] = Field(default_factory=list)

    @field_validator("policy_id")
    @classmethod
    def validate_policy_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("policy_id must not be empty")
        return value


class BudgetUsageSnapshot(BaseModel):
    run_id: str
    input_tokens_used: int = 0
    output_tokens_used: int = 0
    total_tokens_used: int = 0
    cost_usd_used: float = 0.0
    runtime_seconds_used: int = 0
    steps_used: int = 0
    retries_used: int = 0
    tool_calls_used: int = 0

    @field_validator("run_id")
    @classmethod
    def validate_run_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("run_id must not be empty")
        return value

    @field_validator(
        "input_tokens_used", "output_tokens_used", "total_tokens_used",
        "runtime_seconds_used", "steps_used", "retries_used", "tool_calls_used",
    )
    @classmethod
    def validate_non_negative_int(cls, value: int) -> int:
        if value < 0:
            raise ValueError("must be non-negative")
        return value

    @field_validator("cost_usd_used")
    @classmethod
    def validate_non_negative_float(cls, value: float) -> float:
        if value < 0:
            raise ValueError("cost_usd_used must be non-negative")
        return value


class BudgetDecision(BaseModel):
    decision_id: str
    run_id: str
    allowed: bool
    action: LimitAction
    reason: str
    violated_rules: List[str] = Field(default_factory=list)

    @field_validator("decision_id", "run_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def validate_decision_consistency(self):
        if not self.allowed and self.action == LimitAction.ALLOW:
            raise ValueError("allowed=False and action=ALLOW are inconsistent")
        return self


class BudgetViolation(BaseModel):
    rule_id: str
    run_id: str
    scope: BudgetScope
    observed_value: float
    allowed_value: float
    action_taken: LimitAction

    @field_validator("rule_id", "run_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("observed_value", "allowed_value")
    @classmethod
    def validate_non_negative_float(cls, value: float) -> float:
        if value < 0:
            raise ValueError("must be non-negative")
        return value
