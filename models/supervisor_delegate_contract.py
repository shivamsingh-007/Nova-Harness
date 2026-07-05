from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class DelegationReason(str, Enum):
    SPECIALIZED_CAPABILITY_REQUIRED = "specialized_capability_required"
    CONTEXT_ISOLATION_REQUIRED = "context_isolation_required"
    VERIFICATION_NEEDED = "verification_needed"
    PARALLELIZABLE_SUBTASK = "parallelizable_subtask"
    BUDGET_OPTIMIZATION = "budget_optimization"
    POLICY_SEPARATION = "policy_separation"
    HUMAN_LIKE_REVIEW_PATTERN = "human_like_review_pattern"


class DelegateRoleType(str, Enum):
    SPECIALIST = "specialist"
    REVIEWER = "reviewer"
    VERIFIER = "verifier"
    RETRIEVER = "retriever"
    CODER = "coder"
    PLANNER = "planner"
    SUMMARIZER = "summarizer"
    TOOL_OPERATOR = "tool_operator"


class DelegationStatus(str, Enum):
    DRAFT = "draft"
    ASSIGNED = "assigned"
    RUNNING = "running"
    RETURNED = "returned"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REROUTED = "rerouted"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


RETURNED_STATUSES = {DelegationStatus.RETURNED}
REVIEWED_STATUSES = {DelegationStatus.ACCEPTED, DelegationStatus.REJECTED, DelegationStatus.REROUTED}
TERMINAL_DELEGATION_STATUSES = {DelegationStatus.ACCEPTED, DelegationStatus.REJECTED, DelegationStatus.REROUTED, DelegationStatus.CANCELLED, DelegationStatus.EXPIRED}


class DelegationOutcome(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    BLOCKED = "blocked"
    NO_RESULT = "no_result"


class ReturnDisposition(str, Enum):
    ACCEPT = "accept"
    ACCEPT_WITH_MODIFICATION = "accept_with_modification"
    RETRY_SAME_DELEGATE = "retry_same_delegate"
    REROUTE_TO_OTHER_DELEGATE = "reroute_to_other_delegate"
    ESCALATE = "escalate"
    DISCARD = "discard"


ACCEPT_DISPOSITIONS = {ReturnDisposition.ACCEPT, ReturnDisposition.ACCEPT_WITH_MODIFICATION}
RETRY_OR_REROUTE_DISPOSITIONS = {ReturnDisposition.RETRY_SAME_DELEGATE, ReturnDisposition.REROUTE_TO_OTHER_DELEGATE}


class DelegationRequest(BaseModel):
    delegation_id: str
    parent_run_id: Optional[str] = None
    parent_step_id: Optional[str] = None
    supervisor_agent_id: str
    delegation_reason: DelegationReason
    requested_role: DelegateRoleType
    requested_delegate_id: Optional[str] = None
    objective: str
    expected_output: str = ""
    acceptance_criteria: List[str] = Field(default_factory=list)
    priority: str = "medium"
    created_at: datetime

    @field_validator("delegation_id", "supervisor_agent_id", "objective")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def acceptance_criteria_required(self):
        if not self.acceptance_criteria:
            raise ValueError("acceptance_criteria must not be empty")
        return self


class DelegationContextSlice(BaseModel):
    context_slice_id: str
    task_ref: Optional[str] = None
    feature_ref: Optional[str] = None
    relevant_state_refs: List[str] = Field(default_factory=list)
    artifact_refs: List[str] = Field(default_factory=list)
    prompt_refs: List[str] = Field(default_factory=list)
    memory_refs: List[str] = Field(default_factory=list)
    policy_refs: List[str] = Field(default_factory=list)
    max_context_tokens: Optional[int] = None
    excluded_refs: List[str] = Field(default_factory=list)
    self_contained: bool = False

    @field_validator("context_slice_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def at_least_one_ref_unless_self_contained(self):
        if self.self_contained:
            return self
        has_ref = bool(
            self.task_ref or self.feature_ref
            or self.relevant_state_refs or self.artifact_refs
            or self.prompt_refs or self.memory_refs
            or self.policy_refs
        )
        if not has_ref:
            raise ValueError("context_slice must contain at least one reference unless self_contained=True")
        return self


class DelegationConstraintSet(BaseModel):
    constraint_id: str
    time_budget_ms: Optional[int] = None
    cost_budget: Optional[float] = None
    tool_allowlist: List[str] = Field(default_factory=list)
    tool_denylist: List[str] = Field(default_factory=list)
    write_permissions: bool = False
    network_permissions: bool = False
    approval_required: bool = False
    must_verify: bool = True
    must_not_delegate_further: bool = True
    allowed_output_types: List[str] = Field(default_factory=list)

    @field_validator("constraint_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class DelegateSelectionRecord(BaseModel):
    selection_id: str
    candidate_roles: List[DelegateRoleType] = Field(default_factory=list)
    candidate_delegate_ids: List[str] = Field(default_factory=list)
    selected_delegate_id: Optional[str] = None
    selected_role: DelegateRoleType
    selection_reason: str = ""
    selection_confidence: float = 1.0
    fallback_delegate_ids: List[str] = Field(default_factory=list)

    @field_validator("selection_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @field_validator("selection_confidence")
    @classmethod
    def in_range(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v


class DelegationAssignment(BaseModel):
    assignment_id: str
    delegation_request: DelegationRequest
    context_slice: DelegationContextSlice
    constraints: DelegationConstraintSet
    selection: DelegateSelectionRecord
    child_run_id: Optional[str] = None
    child_session_id: Optional[str] = None
    status: DelegationStatus = DelegationStatus.DRAFT
    started_at: Optional[datetime] = None
    deadline_at: Optional[datetime] = None

    @field_validator("assignment_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def returned_requires_return_record(self):
        if self.status in RETURNED_STATUSES:
            pass
        return self

    @model_validator(mode="after")
    def running_status_requires_selected(self):
        if self.status == DelegationStatus.RUNNING and self.selection.selected_delegate_id is None:
            raise ValueError("RUNNING status requires a selected delegate")
        return self


class DelegationReturnRecord(BaseModel):
    return_id: str
    assignment_id: str
    delegate_agent_id: str
    outcome: DelegationOutcome
    result_summary: str = ""
    output_refs: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    changed_artifact_refs: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    suggested_next_action: str = ""
    returned_at: datetime

    @field_validator("return_id", "assignment_id", "delegate_agent_id")
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


class SupervisorReviewRecord(BaseModel):
    review_id: str
    assignment_id: str
    return_id: str
    reviewer_agent_id: str
    disposition: ReturnDisposition
    accepted_output_refs: List[str] = Field(default_factory=list)
    rejection_reason: str = ""
    retry_reason: str = ""
    reroute_reason: str = ""
    integration_notes: str = ""
    reviewed_at: datetime

    @field_validator("review_id", "assignment_id", "return_id", "reviewer_agent_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def accept_requires_outputs_or_notes(self):
        if self.disposition in ACCEPT_DISPOSITIONS:
            if not self.accepted_output_refs and not self.integration_notes.strip():
                raise ValueError("accept disposition requires accepted_output_refs or integration_notes")
        return self

    @model_validator(mode="after")
    def retry_requires_reason(self):
        if self.disposition == ReturnDisposition.RETRY_SAME_DELEGATE and not self.retry_reason.strip():
            raise ValueError("retry_same_delegate requires retry_reason")
        return self

    @model_validator(mode="after")
    def reroute_requires_reason(self):
        if self.disposition == ReturnDisposition.REROUTE_TO_OTHER_DELEGATE and not self.reroute_reason.strip():
            raise ValueError("reroute_to_other_delegate requires reroute_reason")
        return self


class DelegationEnvelope(BaseModel):
    envelope_id: str
    delegation_request: DelegationRequest
    delegation_assignment: DelegationAssignment
    delegation_return: Optional[DelegationReturnRecord] = None
    supervisor_review: Optional[SupervisorReviewRecord] = None

    @field_validator("envelope_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def returned_status_requires_return_record(self):
        if self.delegation_assignment.status in RETURNED_STATUSES and self.delegation_return is None:
            raise ValueError("RETURNED status requires DelegationReturnRecord")
        return self

    @model_validator(mode="after")
    def reviewed_status_requires_supervisor_review(self):
        if self.delegation_assignment.status in REVIEWED_STATUSES and self.supervisor_review is None:
            raise ValueError("ACCEPTED/REJECTED/REROUTED status requires SupervisorReviewRecord")
        return self

    @model_validator(mode="after")
    def return_and_review_consistency(self):
        r = self.delegation_return
        s = self.supervisor_review
        if r is not None and s is not None:
            if s.return_id != r.return_id:
                raise ValueError("supervisor_review.return_id must match delegation_return.return_id")
        return self

    @model_validator(mode="after")
    def nested_delegation_blocked(self):
        if self.delegation_assignment.constraints.must_not_delegate_further:
            pass
        return self
