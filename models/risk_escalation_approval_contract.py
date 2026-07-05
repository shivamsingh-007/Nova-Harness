from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class RiskCategory(str, Enum):
    policy = "policy"
    safety = "safety"
    security = "security"
    privacy = "privacy"
    financial = "financial"
    legal = "legal"
    quality = "quality"
    operational = "operational"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class EscalationTriggerType(str, Enum):
    risk_threshold = "risk_threshold"
    budget_overrun = "budget_overrun"
    policy_exception = "policy_exception"
    uncertainty_exceeded = "uncertainty_exceeded"
    approval_required_action = "approval_required_action"
    stalled_execution = "stalled_execution"
    manual_request = "manual_request"


class ApprovalStatus(str, Enum):
    not_required = "not_required"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    timed_out = "timed_out"
    withdrawn = "withdrawn"


class EscalationDisposition(str, Enum):
    proceed = "proceed"
    proceed_with_constraints = "proceed_with_constraints"
    pause_for_review = "pause_for_review"
    return_for_rework = "return_for_rework"
    reject = "reject"
    escalate_further = "escalate_further"


class RiskAssessmentRecord(BaseModel):
    risk_assessment_id: str = Field(min_length=1)
    scope_ref: str = Field(min_length=1)
    scope_type: Optional[str] = None
    risk_category: RiskCategory
    risk_level: RiskLevel
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    uncertainty_score: float = Field(default=0.0, ge=0.0, le=100.0)
    trigger_reasons: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    assessed_by: Optional[str] = None
    assessed_at: datetime = Field(default_factory=datetime.now)

    @field_validator("risk_assessment_id")
    @classmethod
    def risk_assessment_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("risk_assessment_id must not be blank")
        return v.strip()

    @field_validator("scope_ref")
    @classmethod
    def scope_ref_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("scope_ref must not be blank")
        return v.strip()


class RiskThresholdPolicy(BaseModel):
    threshold_policy_id: str = Field(min_length=1)
    risk_category: Optional[RiskCategory] = None
    minimum_risk_level: RiskLevel
    minimum_risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    uncertainty_threshold: float = Field(default=50.0, ge=0.0, le=100.0)
    trigger_type: EscalationTriggerType
    requires_human_approval: bool = False
    default_disposition: Optional[EscalationDisposition] = None
    timeout_sla_seconds: Optional[int] = Field(default=None, ge=0)
    applicable_scope_types: List[str] = Field(default_factory=list)

    @field_validator("threshold_policy_id")
    @classmethod
    def threshold_policy_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("threshold_policy_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def requires_approval_blocks_auto_proceed(self) -> "RiskThresholdPolicy":
        if self.requires_human_approval and self.default_disposition == EscalationDisposition.proceed:
            raise ValueError("requires_human_approval=True cannot have default_disposition=proceed")
        return self

    @model_validator(mode="after")
    def high_critical_require_human_approval(self) -> "RiskThresholdPolicy":
        if self.minimum_risk_level in (RiskLevel.high, RiskLevel.critical) and not self.requires_human_approval:
            raise ValueError("minimum_risk_level high/critical requires requires_human_approval=True")
        return self


class EscalationRequestRecord(BaseModel):
    escalation_request_id: str = Field(min_length=1)
    scope_ref: str = Field(min_length=1)
    trigger_type: EscalationTriggerType
    trigger_ref: Optional[str] = None
    risk_assessment_ref: Optional[str] = None
    summary: str = Field(min_length=1)
    requested_disposition: Optional[EscalationDisposition] = None
    requested_at: datetime = Field(default_factory=datetime.now)
    requester_ref: Optional[str] = None

    @field_validator("escalation_request_id")
    @classmethod
    def escalation_request_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("escalation_request_id must not be blank")
        return v.strip()

    @field_validator("scope_ref")
    @classmethod
    def er_scope_ref_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("scope_ref must not be blank")
        return v.strip()

    @field_validator("summary")
    @classmethod
    def summary_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("summary must not be blank")
        return v.strip()


class ApprovalRequirementRecord(BaseModel):
    approval_requirement_id: str = Field(min_length=1)
    escalation_request_id: str = Field(min_length=1)
    approval_scope: Optional[str] = None
    required_role_ids: List[str] = Field(default_factory=list)
    required_approver_count: int = Field(default=1, ge=1)
    allow_parallel_approval: bool = False
    approval_deadline: Optional[datetime] = None
    approval_instructions: Optional[str] = None

    @field_validator("approval_requirement_id")
    @classmethod
    def approval_requirement_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("approval_requirement_id must not be blank")
        return v.strip()

    @field_validator("escalation_request_id")
    @classmethod
    def ar_escalation_request_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("escalation_request_id must not be blank")
        return v.strip()


class HumanApprovalRecord(BaseModel):
    approval_id: str = Field(min_length=1)
    approval_requirement_id: str = Field(min_length=1)
    approver_ref: Optional[str] = None
    approval_status: ApprovalStatus
    decision_notes: Optional[str] = None
    imposed_constraints: List[str] = Field(default_factory=list)
    decided_at: datetime = Field(default_factory=datetime.now)

    @field_validator("approval_id")
    @classmethod
    def approval_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("approval_id must not be blank")
        return v.strip()

    @field_validator("approval_requirement_id")
    @classmethod
    def ha_approval_requirement_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("approval_requirement_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def approved_or_rejected_requires_approver_and_reason(self) -> "HumanApprovalRecord":
        if self.approval_status in (ApprovalStatus.approved, ApprovalStatus.rejected):
            if not self.approver_ref:
                raise ValueError("approved/rejected requires approver_ref")
            if not self.decision_notes:
                raise ValueError("approved/rejected requires decision_notes")
        return self


class EscalationPathRecord(BaseModel):
    path_id: str = Field(min_length=1)
    escalation_request_id: str = Field(min_length=1)
    primary_approver_refs: List[str] = Field(default_factory=list)
    fallback_approver_refs: List[str] = Field(default_factory=list)
    escalation_order: int = Field(default=0, ge=0)
    auto_escalate_on_timeout: bool = False
    next_timeout_sla_seconds: Optional[int] = Field(default=None, ge=0)
    path_notes: Optional[str] = None

    @field_validator("path_id")
    @classmethod
    def path_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("path_id must not be blank")
        return v.strip()

    @field_validator("escalation_request_id")
    @classmethod
    def ep_escalation_request_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("escalation_request_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def timeout_path_needs_sla(self) -> "EscalationPathRecord":
        if self.auto_escalate_on_timeout and self.next_timeout_sla_seconds is None:
            raise ValueError("auto_escalate_on_timeout requires next_timeout_sla_seconds")
        return self


class EscalationDecisionRecord(BaseModel):
    decision_id: str = Field(min_length=1)
    escalation_request_id: str = Field(min_length=1)
    approval_status: ApprovalStatus
    escalation_disposition: EscalationDisposition
    final_decider_ref: Optional[str] = None
    decision_reason: Optional[str] = None
    resume_constraints: List[str] = Field(default_factory=list)
    followup_actions: List[str] = Field(default_factory=list)
    decided_at: datetime = Field(default_factory=datetime.now)

    @field_validator("decision_id")
    @classmethod
    def decision_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("decision_id must not be blank")
        return v.strip()

    @field_validator("escalation_request_id")
    @classmethod
    def ed_escalation_request_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("escalation_request_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def approved_rejected_requires_decider_and_reason(self) -> "EscalationDecisionRecord":
        if self.approval_status in (ApprovalStatus.approved, ApprovalStatus.rejected):
            if not self.final_decider_ref:
                raise ValueError("approved/rejected requires final_decider_ref")
            if not self.decision_reason:
                raise ValueError("approved/rejected requires decision_reason")
        return self

    @model_validator(mode="after")
    def proceed_with_constraints_requires_resume_constraints(self) -> "EscalationDecisionRecord":
        if self.escalation_disposition == EscalationDisposition.proceed_with_constraints:
            if not self.resume_constraints:
                raise ValueError("proceed_with_constraints requires resume_constraints")
        return self


class RiskEscalationApprovalEnvelope(BaseModel):
    envelope_id: str = Field(min_length=1)
    risk_assessment: RiskAssessmentRecord
    threshold_policy: Optional[RiskThresholdPolicy] = None
    escalation_request: Optional[EscalationRequestRecord] = None
    approval_requirement: Optional[ApprovalRequirementRecord] = None
    approval_records: List[HumanApprovalRecord] = Field(default_factory=list)
    escalation_path: Optional[EscalationPathRecord] = None
    decision: Optional[EscalationDecisionRecord] = None

    @field_validator("envelope_id")
    @classmethod
    def envelope_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("envelope_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def requires_human_approval_blocks_auto_proceed(self) -> "RiskEscalationApprovalEnvelope":
        tp = self.threshold_policy
        if tp and tp.requires_human_approval:
            decision = self.decision
            if decision and decision.escalation_disposition == EscalationDisposition.proceed:
                approval_records = self.approval_records
                approved_count = sum(1 for r in approval_records if r.approval_status == ApprovalStatus.approved)
                req = self.approval_requirement
                needed = req.required_approver_count if req else 1
                if approved_count < needed:
                    raise ValueError("requires_human_approval=True but insufficient approved records to proceed")
        return self

    @model_validator(mode="after")
    def timed_out_requires_escalation_path(self) -> "RiskEscalationApprovalEnvelope":
        ar = self.approval_records
        has_timed_out = any(r.approval_status == ApprovalStatus.timed_out for r in ar)
        if has_timed_out and self.escalation_path is None:
            raise ValueError("timed_out approval requires escalation_path")
        return self

    @model_validator(mode="after")
    def parallel_approval_count_must_match(self) -> "RiskEscalationApprovalEnvelope":
        req = self.approval_requirement
        if req and req.allow_parallel_approval:
            if len(self.approval_records) < req.required_approver_count:
                pass
        return self
