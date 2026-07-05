from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class PolicyDecisionStatus(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    REQUIRE_APPROVAL = "require_approval"
    ESCALATE = "escalate"
    DEFER = "defer"


class ApprovalRequirement(str, Enum):
    NONE = "none"
    HUMAN_REVIEW = "human_review"
    OWNER_APPROVAL = "owner_approval"
    SECURITY_APPROVAL = "security_approval"
    FINANCE_APPROVAL = "finance_approval"


class EscalationLevel(str, Enum):
    NONE = "none"
    TEAM_LEAD = "team_lead"
    STAFF = "staff"
    SECURITY = "security"
    EXECUTIVE = "executive"


class PolicyScope(str, Enum):
    TASK = "task"
    TOOL_CALL = "tool_call"
    MODEL_CALL = "model_call"
    CHECKPOINT = "checkpoint"
    SESSION = "session"
    RESOURCE = "resource"


class PolicyRuleRef(BaseModel):
    rule_id: str
    rule_name: str
    version: Optional[str] = None

    @field_validator("rule_id", "rule_name")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class DecisionCondition(BaseModel):
    condition_id: str
    description: str
    satisfied: bool

    @field_validator("condition_id", "description")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class ApprovalActorRef(BaseModel):
    actor_id: str
    actor_type: str
    display_name: Optional[str] = None

    @field_validator("actor_id", "actor_type")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class PolicyDecisionRecord(BaseModel):
    decision_id: str
    scope: PolicyScope
    status: PolicyDecisionStatus
    reason: str
    rule_refs: List[PolicyRuleRef] = Field(default_factory=list)
    conditions: List[DecisionCondition] = Field(default_factory=list)
    approval_requirement: ApprovalRequirement = ApprovalRequirement.NONE
    escalation_level: EscalationLevel = EscalationLevel.NONE
    next_action: Optional[str] = None

    @field_validator("decision_id", "reason")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def block_must_not_be_approved(self):
        if self.status == PolicyDecisionStatus.BLOCK:
            if self.approval_requirement != ApprovalRequirement.NONE:
                raise ValueError("BLOCK decision must not have an approval requirement")
        return self

    @model_validator(mode="after")
    def require_approval_needs_next_action(self):
        if self.status == PolicyDecisionStatus.REQUIRE_APPROVAL and not self.next_action:
            raise ValueError("REQUIRE_APPROVAL decision must specify next_action")
        return self

    @model_validator(mode="after")
    def escalate_not_none_level(self):
        if self.status == PolicyDecisionStatus.ESCALATE and self.escalation_level == EscalationLevel.NONE:
            raise ValueError("ESCALATE decision must specify a non-NONE escalation_level")
        return self


class ApprovalGateRecord(BaseModel):
    gate_id: str
    decision_id: str
    approved: bool
    approval_actor: Optional[ApprovalActorRef] = None
    approval_note: Optional[str] = None
    approved_at: Optional[str] = None

    @field_validator("gate_id", "decision_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def approved_needs_actor_or_note(self):
        if self.approved:
            if not self.approval_actor and not self.approval_note:
                raise ValueError("approved gate must have an approval_actor or approval_note")
        return self


class PolicyDecisionEnvelope(BaseModel):
    envelope_id: str
    run_id: str
    task_id: Optional[str] = None
    trace_id: Optional[str] = None
    agent_id: str
    decision: PolicyDecisionRecord
    approval_gate: Optional[ApprovalGateRecord] = None

    @field_validator("envelope_id", "run_id", "agent_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def approval_gate_matches_decision(self):
        if self.approval_gate is not None:
            if self.approval_gate.decision_id != self.decision.decision_id:
                raise ValueError("approval_gate.decision_id must match decision.decision_id")
        return self
