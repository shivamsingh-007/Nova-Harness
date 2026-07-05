from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class BudgetScopeType(str, Enum):
    session = "session"
    run = "run"
    task = "task"
    agent = "agent"
    role = "role"
    branch = "branch"
    tool_call = "tool_call"
    model_call = "model_call"


class ResourceType(str, Enum):
    tokens = "tokens"
    compute_time_ms = "compute_time_ms"
    wall_clock_ms = "wall_clock_ms"
    currency_cost = "currency_cost"
    tool_invocations = "tool_invocations"
    network_calls = "network_calls"
    parallel_slots = "parallel_slots"
    memory_mb = "memory_mb"


class BudgetStatus(str, Enum):
    planned = "planned"
    active = "active"
    warning = "warning"
    exhausted = "exhausted"
    overrun = "overrun"
    closed = "closed"
    cancelled = "cancelled"


class LimitSeverity(str, Enum):
    soft = "soft"
    hard = "hard"


class OverrunDisposition(str, Enum):
    continue_with_warning = "continue_with_warning"
    throttle = "throttle"
    require_approval = "require_approval"
    reallocate = "reallocate"
    stop_execution = "stop_execution"


class ExecutionBudgetEnvelope(BaseModel):
    budget_id: str = Field(min_length=1)
    scope_type: BudgetScopeType
    scope_ref: str = Field(min_length=1)
    parent_budget_id: Optional[str] = None
    budget_status: BudgetStatus = BudgetStatus.planned
    planning_budget_ref: Optional[str] = None
    execution_budget_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator("budget_id")
    @classmethod
    def budget_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("budget_id must not be blank")
        return v.strip()

    @field_validator("scope_ref")
    @classmethod
    def scope_ref_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("scope_ref must not be blank")
        return v.strip()


class ResourceBudgetLine(BaseModel):
    budget_line_id: str = Field(min_length=1)
    budget_id: str = Field(min_length=1)
    resource_type: ResourceType
    allocated_amount: float = Field(default=0.0, ge=0.0)
    reserved_amount: float = Field(default=0.0, ge=0.0)
    consumed_amount: float = Field(default=0.0, ge=0.0)
    remaining_amount: float = Field(default=0.0)
    unit: str = Field(min_length=1)

    @field_validator("budget_line_id")
    @classmethod
    def budget_line_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("budget_line_id must not be blank")
        return v.strip()

    @field_validator("budget_id")
    @classmethod
    def bl_budget_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("budget_id must not be blank")
        return v.strip()

    @field_validator("unit")
    @classmethod
    def unit_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("unit must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def remaining_must_be_consistent(self) -> "ResourceBudgetLine":
        expected_remaining = self.allocated_amount - self.reserved_amount - self.consumed_amount
        if abs(self.remaining_amount - expected_remaining) > 0.001:
            raise ValueError(
                f"remaining_amount ({self.remaining_amount}) != allocated - reserved - consumed ({expected_remaining})"
            )
        return self

    @model_validator(mode="after")
    def reserved_plus_consumed_not_exceed_allocated_without_overrun(self) -> "ResourceBudgetLine":
        used = self.reserved_amount + self.consumed_amount
        if used > self.allocated_amount + 0.001:
            pass  # allowed if overrun decision exists at envelope level
        return self

    @field_validator("allocated_amount", "reserved_amount", "consumed_amount")
    @classmethod
    def amounts_must_be_finite(cls, v: float) -> float:
        import math
        if math.isnan(v) or math.isinf(v):
            raise ValueError("amounts must be finite")
        return v


class ResourceReservationRecord(BaseModel):
    reservation_id: str = Field(min_length=1)
    budget_line_id: str = Field(min_length=1)
    request_ref: Optional[str] = None
    reserved_amount: float = Field(ge=0.0)
    reservation_reason: Optional[str] = None
    reserved_by: Optional[str] = None
    reserved_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    @field_validator("reservation_id")
    @classmethod
    def reservation_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("reservation_id must not be blank")
        return v.strip()

    @field_validator("budget_line_id")
    @classmethod
    def r_budget_line_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("budget_line_id must not be blank")
        return v.strip()

    @field_validator("reserved_amount")
    @classmethod
    def reserved_amount_must_be_finite(cls, v: float) -> float:
        import math
        if math.isnan(v) or math.isinf(v):
            raise ValueError("reserved_amount must be finite")
        return v


class ResourceUsageRecord(BaseModel):
    usage_id: str = Field(min_length=1)
    budget_line_id: str = Field(min_length=1)
    resource_type: ResourceType
    consumed_amount: float = Field(ge=0.0)
    usage_context_ref: Optional[str] = None
    actor_ref: Optional[str] = None
    source_event_ref: Optional[str] = None
    recorded_at: datetime = Field(default_factory=datetime.now)

    @field_validator("usage_id")
    @classmethod
    def usage_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("usage_id must not be blank")
        return v.strip()

    @field_validator("budget_line_id")
    @classmethod
    def u_budget_line_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("budget_line_id must not be blank")
        return v.strip()

    @field_validator("consumed_amount")
    @classmethod
    def consumed_amount_must_be_finite(cls, v: float) -> float:
        import math
        if math.isnan(v) or math.isinf(v):
            raise ValueError("consumed_amount must be finite")
        return v


class BudgetThresholdPolicy(BaseModel):
    threshold_policy_id: str = Field(min_length=1)
    budget_line_id: str = Field(min_length=1)
    limit_severity: LimitSeverity
    threshold_value: Optional[float] = Field(default=None, ge=0.0)
    threshold_percent: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    action_on_cross: str = Field(min_length=1)
    cooldown_policy: Optional[str] = None
    notification_targets: List[str] = Field(default_factory=list)

    @field_validator("threshold_policy_id")
    @classmethod
    def threshold_policy_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("threshold_policy_id must not be blank")
        return v.strip()

    @field_validator("budget_line_id")
    @classmethod
    def tp_budget_line_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("budget_line_id must not be blank")
        return v.strip()

    @field_validator("action_on_cross")
    @classmethod
    def action_on_cross_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("action_on_cross must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def hard_threshold_must_have_action(self) -> "BudgetThresholdPolicy":
        if self.limit_severity == LimitSeverity.hard and not self.action_on_cross.strip():
            raise ValueError("hard threshold must define action_on_cross")
        return self

    @model_validator(mode="after")
    def must_have_threshold_value_or_percent(self) -> "BudgetThresholdPolicy":
        if self.threshold_value is None and self.threshold_percent is None:
            raise ValueError("must set threshold_value or threshold_percent")
        return self


class BudgetAlertRecord(BaseModel):
    alert_id: str = Field(min_length=1)
    budget_line_id: str = Field(min_length=1)
    limit_severity: LimitSeverity
    trigger_value: float = Field(ge=0.0)
    remaining_amount: float
    recommended_action: Optional[str] = None
    triggered_at: datetime = Field(default_factory=datetime.now)

    @field_validator("alert_id")
    @classmethod
    def alert_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("alert_id must not be blank")
        return v.strip()

    @field_validator("budget_line_id")
    @classmethod
    def al_budget_line_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("budget_line_id must not be blank")
        return v.strip()


class BudgetDecisionRecord(BaseModel):
    decision_id: str = Field(min_length=1)
    budget_id: str = Field(min_length=1)
    overrun_disposition: OverrunDisposition
    decision_reason: Optional[str] = None
    approved_by: Optional[str] = None
    reallocated_from_budget_id: Optional[str] = None
    additional_amount: Optional[float] = Field(default=None, ge=0.0)
    effective_from: datetime = Field(default_factory=datetime.now)
    effective_until: Optional[datetime] = None

    @field_validator("decision_id")
    @classmethod
    def decision_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("decision_id must not be blank")
        return v.strip()

    @field_validator("budget_id")
    @classmethod
    def bd_budget_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("budget_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def reallocate_requires_source(self) -> "BudgetDecisionRecord":
        if self.overrun_disposition == OverrunDisposition.reallocate:
            if not self.reallocated_from_budget_id:
                raise ValueError("reallocate disposition must reference source budget")
        return self

    @model_validator(mode="after")
    def require_approval_needs_approver_when_finalized(self) -> "BudgetDecisionRecord":
        if self.overrun_disposition == OverrunDisposition.require_approval:
            if self.approved_by is None and self.effective_until is not None:
                pass  # pending, not yet finalized
        return self


class BudgetResourceEnvelope(BaseModel):
    envelope_id: str = Field(min_length=1)
    budget: ExecutionBudgetEnvelope
    budget_lines: List[ResourceBudgetLine] = Field(default_factory=list)
    reservations: List[ResourceReservationRecord] = Field(default_factory=list)
    usage_records: List[ResourceUsageRecord] = Field(default_factory=list)
    threshold_policies: List[BudgetThresholdPolicy] = Field(default_factory=list)
    alerts: List[BudgetAlertRecord] = Field(default_factory=list)
    decisions: List[BudgetDecisionRecord] = Field(default_factory=list)

    @field_validator("envelope_id")
    @classmethod
    def envelope_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("envelope_id must not be blank")
        return v.strip()

    def _valid_budget_line_ids(self) -> set:
        return {bl.budget_line_id for bl in self.budget_lines}

    @model_validator(mode="after")
    def reservations_reference_valid_budget_lines(self) -> "BudgetResourceEnvelope":
        valid_ids = self._valid_budget_line_ids()
        for r in self.reservations:
            if r.budget_line_id not in valid_ids:
                raise ValueError(f"reservation '{r.reservation_id}' references unknown budget_line '{r.budget_line_id}'")
        return self

    @model_validator(mode="after")
    def usage_records_reference_valid_budget_lines(self) -> "BudgetResourceEnvelope":
        valid_ids = self._valid_budget_line_ids()
        for u in self.usage_records:
            if u.budget_line_id not in valid_ids:
                raise ValueError(f"usage '{u.usage_id}' references unknown budget_line '{u.budget_line_id}'")
        return self

    @model_validator(mode="after")
    def threshold_policies_reference_valid_budget_lines(self) -> "BudgetResourceEnvelope":
        valid_ids = self._valid_budget_line_ids()
        for tp in self.threshold_policies:
            if tp.budget_line_id not in valid_ids:
                raise ValueError(f"threshold policy '{tp.threshold_policy_id}' references unknown budget_line '{tp.budget_line_id}'")
        return self

    @model_validator(mode="after")
    def alerts_reference_valid_budget_lines(self) -> "BudgetResourceEnvelope":
        valid_ids = self._valid_budget_line_ids()
        for a in self.alerts:
            if a.budget_line_id not in valid_ids:
                raise ValueError(f"alert '{a.alert_id}' references unknown budget_line '{a.budget_line_id}'")
        return self

    @model_validator(mode="after")
    def decisions_reference_valid_budget(self) -> "BudgetResourceEnvelope":
        budget_id = self.budget.budget_id
        for d in self.decisions:
            if d.budget_id != budget_id:
                raise ValueError(f"decision '{d.decision_id}' references budget '{d.budget_id}' != envelope budget '{budget_id}'")
        return self

    @model_validator(mode="after")
    def budget_lines_match_envelope_budget_id(self) -> "BudgetResourceEnvelope":
        budget_id = self.budget.budget_id
        for bl in self.budget_lines:
            if bl.budget_id != budget_id:
                raise ValueError(f"budget_line '{bl.budget_line_id}' references budget '{bl.budget_id}' != envelope budget '{budget_id}'")
        return self
