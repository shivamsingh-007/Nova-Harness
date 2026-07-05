from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class RouteTargetType(str, Enum):
    DIRECT_EXECUTOR = "direct_executor"
    SPECIALIST_AGENT = "specialist_agent"
    VERIFIER_AGENT = "verifier_agent"
    REVIEWER_AGENT = "reviewer_agent"
    TOOL_PATH = "tool_path"
    FALLBACK_PATH = "fallback_path"
    HUMAN_APPROVAL_GATE = "human_approval_gate"
    BLOCKED = "blocked"


ROUTE_NEEDS_APPROVAL = {RouteTargetType.HUMAN_APPROVAL_GATE, RouteTargetType.BLOCKED}


class RoutingStrategy(str, Enum):
    RULE_BASED = "rule_based"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    MANUAL_OVERRIDE = "manual_override"
    FALLBACK_ONLY = "fallback_only"


class ArbitrationPolicy(str, Enum):
    HIGHEST_SCORE = "highest_score"
    PRIORITY_FIRST = "priority_first"
    LOWEST_COST_MEETING_THRESHOLD = "lowest_cost_meeting_threshold"
    SAFEST_ROUTE = "safest_route"
    VERIFICATION_FIRST = "verification_first"
    HUMAN_OVERRIDE = "human_override"


class RoutingDecisionStatus(str, Enum):
    DRAFT = "draft"
    EVALUATED = "evaluated"
    SELECTED = "selected"
    DISPATCHED = "dispatched"
    REROUTED = "rerouted"
    REJECTED = "rejected"
    BLOCKED = "blocked"


DISPATCHED_STATUSES = {RoutingDecisionStatus.DISPATCHED}
FINAL_ROUTING_STATUSES = {
    RoutingDecisionStatus.DISPATCHED, RoutingDecisionStatus.REROUTED,
    RoutingDecisionStatus.REJECTED, RoutingDecisionStatus.BLOCKED,
}


class RoutingOutcome(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    NO_ELIGIBLE_ROUTE = "no_eligible_route"
    FALLBACK_USED = "fallback_used"
    MANUAL_INTERVENTION_REQUIRED = "manual_intervention_required"


class RoutingInputRecord(BaseModel):
    routing_id: str
    run_id: Optional[str] = None
    step_id: Optional[str] = None
    task_id: Optional[str] = None
    feature_id: Optional[str] = None
    request_summary: str
    task_type: str = ""
    risk_level: str = "low"
    requires_verification: bool = False
    requires_tooling: bool = False
    requires_specialization: bool = False
    budget_hint: Optional[str] = None
    latency_hint: Optional[str] = None
    input_refs: List[str] = Field(default_factory=list)

    @field_validator("routing_id", "request_summary")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class RouteCandidate(BaseModel):
    candidate_id: str
    target_type: RouteTargetType
    target_id: str
    target_role: str = ""
    capability_tags: List[str] = Field(default_factory=list)
    estimated_cost: Optional[float] = None
    estimated_latency: Optional[float] = None
    risk_fit: str = "medium"
    supports_verification: bool = False
    requires_approval: bool = False
    availability_status: str = "available"
    notes: str = ""

    @field_validator("candidate_id", "target_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class RouteScoreRecord(BaseModel):
    score_id: str
    candidate_id: str
    strategy: RoutingStrategy = RoutingStrategy.RULE_BASED
    capability_score: float = 1.0
    policy_score: float = 1.0
    cost_score: float = 1.0
    latency_score: float = 1.0
    risk_score: float = 1.0
    overall_score: float = 1.0
    threshold_passed: bool = True
    reason_summary: str = ""

    @field_validator("score_id", "candidate_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @field_validator("capability_score", "policy_score", "cost_score",
                     "latency_score", "risk_score", "overall_score")
    @classmethod
    def in_range(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("score must be between 0.0 and 1.0")
        return v


class RoutingConstraintSet(BaseModel):
    constraint_id: str
    allowed_target_types: List[RouteTargetType] = Field(default_factory=list)
    disallowed_target_ids: List[str] = Field(default_factory=list)
    max_cost: Optional[float] = None
    max_latency_ms: Optional[float] = None
    must_verify: bool = False
    must_use_specialist: bool = False
    must_avoid_network: bool = False
    must_require_approval_for_sensitive: bool = False
    fallback_required: bool = True
    manual_override_allowed: bool = True

    @field_validator("constraint_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def high_risk_constraints(self):
        return self


class RoutingDecisionRecord(BaseModel):
    decision_id: str
    routing_id: str
    selected_candidate_id: Optional[str] = None
    selected_target_type: Optional[RouteTargetType] = None
    selected_target_id: Optional[str] = None
    strategy_used: RoutingStrategy
    decision_status: RoutingDecisionStatus
    decision_reason: str = ""
    confidence: float = 1.0
    dispatched_at: Optional[datetime] = None
    expected_next_contract: str = ""

    @field_validator("decision_id", "routing_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @field_validator("confidence")
    @classmethod
    def in_range(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v

    @model_validator(mode="after")
    def selected_has_candidate(self):
        if self.decision_status in (RoutingDecisionStatus.SELECTED, RoutingDecisionStatus.DISPATCHED):
            if self.selected_candidate_id is None:
                raise ValueError("SELECTED/DISPATCHED status requires a selected_candidate_id")
        return self

    @model_validator(mode="after")
    def blocked_or_no_route_needs_reason(self):
        if self.decision_status in (RoutingDecisionStatus.BLOCKED, RoutingDecisionStatus.REJECTED):
            if not self.decision_reason.strip():
                raise ValueError("BLOCKED/REJECTED status requires decision_reason")
        return self


class ArbitrationRecord(BaseModel):
    arbitration_id: str
    routing_id: str
    policy: ArbitrationPolicy
    competing_candidate_ids: List[str] = Field(default_factory=list)
    tie_break_reason: str = ""
    selected_candidate_id: Optional[str] = None
    review_required: bool = False
    review_notes: str = ""

    @field_validator("arbitration_id", "routing_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def requires_at_least_two_competing(self):
        if len(self.competing_candidate_ids) < 2:
            raise ValueError("arbitration requires at least 2 competing candidates")
        return self

    @model_validator(mode="after")
    def tie_break_needs_reason(self):
        if self.selected_candidate_id and not self.tie_break_reason.strip():
            raise ValueError("arbitration with selection requires tie_break_reason")
        return self


class RoutingFallbackRecord(BaseModel):
    fallback_id: str
    routing_id: str
    trigger_reason: str
    fallback_candidate_id: Optional[str] = None
    fallback_target_type: Optional[RouteTargetType] = None
    fallback_notes: str = ""
    manual_intervention_required: bool = False

    @field_validator("fallback_id", "routing_id", "trigger_reason")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class RoutingEnvelope(BaseModel):
    envelope_id: str
    routing_input: RoutingInputRecord
    candidates: List[RouteCandidate] = Field(default_factory=list)
    scores: List[RouteScoreRecord] = Field(default_factory=list)
    constraints: RoutingConstraintSet
    decision: Optional[RoutingDecisionRecord] = None
    arbitration: Optional[ArbitrationRecord] = None
    fallback: Optional[RoutingFallbackRecord] = None

    @field_validator("envelope_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def at_least_one_candidate_unless_no_route(self):
        outcome_hint = None
        if self.decision:
            pass
        if not self.candidates:
            if self.decision and self.decision.decision_status == RoutingDecisionStatus.BLOCKED:
                return self
            raise ValueError("at least one RouteCandidate is required unless outcome is no_eligible_route")
        return self

    @model_validator(mode="after")
    def selected_candidate_must_exist(self):
        if self.decision and self.decision.selected_candidate_id:
            found = any(
                c.candidate_id == self.decision.selected_candidate_id
                for c in self.candidates
            )
            if not found:
                raise ValueError("selected_candidate_id must reference an existing candidate")
        return self

    @model_validator(mode="after")
    def dispatched_requires_decision(self):
        if self.decision and self.decision.decision_status in DISPATCHED_STATUSES:
            pass
        return self

    @model_validator(mode="after")
    def fallback_requires_decision(self):
        if self.fallback and self.decision is None:
            raise ValueError("fallback requires a RoutingDecisionRecord")
        return self

    @model_validator(mode="after")
    def verification_constraint_for_high_risk(self):
        if self.routing_input.risk_level == "high":
            if self.constraints.must_verify:
                if self.decision and self.decision.selected_target_type:
                    sel = self.decision.selected_target_type
                    if sel not in (RouteTargetType.VERIFIER_AGENT, RouteTargetType.DIRECT_EXECUTOR):
                        pass
        return self
