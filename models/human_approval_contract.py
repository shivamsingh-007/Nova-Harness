from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class ApprovalDecisionType(str, Enum):
    APPROVE = "approve"
    DENY = "deny"
    ESCALATE = "escalate"
    OVERRIDE = "override"


class ApprovalReasonType(str, Enum):
    POLICY_TRIGGER = "policy_trigger"
    HIGH_RISK_ACTION = "high_risk_action"
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"
    SCOPE_EXPANSION = "scope_expansion"
    UNKNOWN_CONDITION = "unknown_condition"


class RiskTier(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class EscalationStatus(str, Enum):
    NOT_ESCALATED = "not_escalated"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    TIMED_OUT = "timed_out"


class ApproverRef(BaseModel):
    approver_id: str
    approver_role: str
    display_name: Optional[str] = None

    @model_validator(mode="after")
    def check_non_empty(self):
        if not self.approver_id.strip():
            raise ValueError("approver_id must be non-empty")
        if not self.approver_role.strip():
            raise ValueError("approver_role must be non-empty")
        return self


class ApprovalContext(BaseModel):
    subject_ref: str
    summary: str
    policy_ref: Optional[str] = None
    risk_tier: RiskTier
    evidence_refs: List[str] = Field(default_factory=list)
    rollback_plan: Optional[str] = None

    @model_validator(mode="after")
    def check_non_empty(self):
        if not self.subject_ref.strip():
            raise ValueError("subject_ref must be non-empty")
        if not self.summary.strip():
            raise ValueError("summary must be non-empty")
        return self


class ApprovalRequest(BaseModel):
    approval_request_id: str
    run_id: str
    requested_by: str
    reason_type: ApprovalReasonType
    status: ApprovalStatus
    context: ApprovalContext
    eligible_approvers: List[ApproverRef] = Field(default_factory=list)
    expires_at: Optional[str] = None

    @model_validator(mode="after")
    def check_non_empty(self):
        if not self.approval_request_id.strip():
            raise ValueError("approval_request_id must be non-empty")
        if not self.run_id.strip():
            raise ValueError("run_id must be non-empty")
        if not self.requested_by.strip():
            raise ValueError("requested_by must be non-empty")
        return self

    @model_validator(mode="after")
    def check_eligible_approvers_for_pending(self):
        if self.status == ApprovalStatus.PENDING and not self.eligible_approvers:
            raise ValueError("PENDING requests must have at least one eligible_approver")
        return self


class ApprovalDecision(BaseModel):
    approval_decision_id: str
    approval_request_id: str
    decided_by: ApproverRef
    decision: ApprovalDecisionType
    justification: str
    decided_at: str

    @model_validator(mode="after")
    def check_non_empty(self):
        if not self.approval_decision_id.strip():
            raise ValueError("approval_decision_id must be non-empty")
        if not self.approval_request_id.strip():
            raise ValueError("approval_request_id must be non-empty")
        if not self.justification.strip():
            raise ValueError("justification must be non-empty")
        if not self.decided_at.strip():
            raise ValueError("decided_at must be non-empty")
        return self

    @model_validator(mode="after")
    def check_override_restricted(self):
        if self.decision == ApprovalDecisionType.OVERRIDE and "override" not in self.decided_by.approver_role.lower():
            raise ValueError("OVERRIDE decision requires an approver_role containing 'override' or higher authority")
        return self


class EscalationStep(BaseModel):
    escalation_step_id: str
    approval_request_id: str
    from_role: Optional[str] = None
    to_role: str
    escalation_status: EscalationStatus
    note: Optional[str] = None

    @model_validator(mode="after")
    def check_non_empty(self):
        if not self.escalation_step_id.strip():
            raise ValueError("escalation_step_id must be non-empty")
        if not self.approval_request_id.strip():
            raise ValueError("approval_request_id must be non-empty")
        if not self.to_role.strip():
            raise ValueError("to_role must be non-empty")
        return self


class ApprovalEnvelope(BaseModel):
    envelope_id: str
    request: ApprovalRequest
    decision: Optional[ApprovalDecision] = None
    escalation_steps: List[EscalationStep] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_non_empty(self):
        if not self.envelope_id.strip():
            raise ValueError("envelope_id must be non-empty")
        return self

    @model_validator(mode="after")
    def check_decision_matches_request(self):
        if self.decision is not None and self.decision.approval_request_id != self.request.approval_request_id:
            raise ValueError("decision.approval_request_id must match request.approval_request_id")
        return self

    @model_validator(mode="after")
    def check_escalation_matches_request(self):
        for step in self.escalation_steps:
            if step.approval_request_id != self.request.approval_request_id:
                raise ValueError("escalation_step.approval_request_id must match request.approval_request_id")
        return self

    @model_validator(mode="after")
    def check_escalated_decision_has_steps(self):
        if self.decision is not None and self.decision.decision == ApprovalDecisionType.ESCALATE and not self.escalation_steps:
            raise ValueError("ESCALATE decision must have at least one escalation_step")
        return self

    @model_validator(mode="after")
    def check_expired_not_allowed(self):
        if self.request.status == ApprovalStatus.EXPIRED and self.decision is not None and self.decision.decision in (
            ApprovalDecisionType.APPROVE, ApprovalDecisionType.OVERRIDE,
        ):
            raise ValueError("EXPIRED request must not have APPROVE or OVERRIDE decision")
        return self
