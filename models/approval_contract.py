from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalActionType(str, Enum):
    TOOL_EXECUTION = "tool_execution"
    EXTERNAL_MESSAGE = "external_message"
    DATA_MUTATION = "data_mutation"
    PERMISSION_CHANGE = "permission_change"
    FINANCIAL_ACTION = "financial_action"
    POLICY_OVERRIDE = "policy_override"
    PRODUCTION_DEPLOYMENT = "production_deployment"
    UNKNOWN = "unknown"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class ReviewerDecisionType(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"
    ABSTAIN = "abstain"


class EscalationReason(str, Enum):
    TIMEOUT = "timeout"
    NO_ELIGIBLE_REVIEWER = "no_eligible_reviewer"
    HIGH_RISK_ACTION = "high_risk_action"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    POLICY_TRIGGER = "policy_trigger"
    UNKNOWN = "unknown"


class ApprovalPolicy(BaseModel):
    policy_id: str
    action_type: ApprovalActionType
    minimum_risk_level_for_approval: RiskLevel
    allowed_reviewer_roles: List[str] = Field(default_factory=list)
    timeout_seconds: int
    require_evidence: bool = True
    auto_escalate_on_timeout: bool = True

    @field_validator("policy_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("policy_id must not be empty")
        return value

    @field_validator("timeout_seconds")
    @classmethod
    def validate_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("timeout_seconds must be at least 1")
        return value

    @model_validator(mode="after")
    def validate_reviewer_roles(self):
        if self.minimum_risk_level_for_approval in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            if not self.allowed_reviewer_roles:
                raise ValueError("allowed_reviewer_roles must not be empty for high/critical risk policies")
        return self


class ApprovalEvidence(BaseModel):
    evidence_id: str
    label: str
    content: str
    content_type: str = "text"

    @field_validator("evidence_id", "label", "content")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class ApprovalRequest(BaseModel):
    request_id: str
    run_id: str
    step_id: str
    action_type: ApprovalActionType
    risk_level: RiskLevel
    requested_by_agent_id: str
    summary: str
    proposed_action: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewer_roles_needed: List[str] = Field(default_factory=list)
    evidence: List[ApprovalEvidence] = Field(default_factory=list)

    @field_validator("request_id", "run_id", "step_id", "requested_by_agent_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("summary", "proposed_action")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def validate_high_risk_roles(self):
        if self.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            if not self.reviewer_roles_needed:
                raise ValueError("reviewer_roles_needed must not be empty for high/critical risk requests")
        return self

    @model_validator(mode="after")
    def validate_high_risk_evidence(self):
        if self.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            if not self.evidence:
                raise ValueError("evidence must not be empty for high/critical risk requests")
        return self


class ReviewerDecision(BaseModel):
    decision_id: str
    request_id: str
    reviewer_id: str
    reviewer_role: str
    decision: ReviewerDecisionType
    rationale: str

    @field_validator("decision_id", "request_id", "reviewer_id", "reviewer_role")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("rationale")
    @classmethod
    def validate_rationale(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("rationale must not be empty")
        return value


class EscalationRecord(BaseModel):
    escalation_id: str
    request_id: str
    reason: EscalationReason
    escalated_to_role: str
    note: Optional[str] = None

    @field_validator("escalation_id", "request_id", "escalated_to_role")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class ApprovalOutcome(BaseModel):
    request_id: str
    final_status: ApprovalStatus
    final_decision_id: Optional[str] = None
    escalation_ids: List[str] = Field(default_factory=list)
    executable: bool = False

    @field_validator("request_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("request_id must not be empty")
        return value

    @model_validator(mode="after")
    def validate_approved_has_decision(self):
        if self.final_status == ApprovalStatus.APPROVED and self.final_decision_id is None:
            raise ValueError("APPROVED outcome must have a final_decision_id")
        return self

    @model_validator(mode="after")
    def validate_rejected_not_executable(self):
        if self.final_status in (ApprovalStatus.REJECTED, ApprovalStatus.EXPIRED,
                                 ApprovalStatus.ESCALATED, ApprovalStatus.CANCELLED):
            if self.executable:
                raise ValueError(f"{self.final_status.value} outcome must not be executable")
        return self
