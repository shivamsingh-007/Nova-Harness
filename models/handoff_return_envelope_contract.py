from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class HandoffType(str, Enum):
    DELEGATE_WORK = "delegate_work"
    TRANSFER_CONTROL = "transfer_control"
    REQUEST_REVIEW = "request_review"
    REQUEST_VERIFICATION = "request_verification"
    REQUEST_RETRIEVAL = "request_retrieval"
    RETURN_TO_SUPERVISOR = "return_to_supervisor"


class HandoffStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    RECEIVED = "received"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    IN_PROGRESS = "in_progress"
    RETURNED = "returned"
    CANCELLED = "cancelled"


class OwnershipMode(str, Enum):
    FULL_TRANSFER = "full_transfer"
    TEMPORARY_EXECUTION = "temporary_execution"
    READ_ONLY_ASSIST = "read_only_assist"
    REVIEW_ONLY = "review_only"


class ReturnStatus(str, Enum):
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEEDS_FOLLOWUP = "needs_followup"


class ReturnOutcome(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    BLOCKED = "blocked"
    NOT_APPLICABLE = "not_applicable"


WRITE_OWNERSHIP_MODES = {OwnershipMode.FULL_TRANSFER, OwnershipMode.TEMPORARY_EXECUTION}
READ_ONLY_OWNERSHIP_MODES = {OwnershipMode.READ_ONLY_ASSIST, OwnershipMode.REVIEW_ONLY}


class HandoffRequest(BaseModel):
    handoff_id: str = Field(min_length=1)
    parent_run_id: Optional[str] = None
    parent_step_id: Optional[str] = None
    from_agent_id: str = Field(min_length=1)
    to_agent_id: Optional[str] = None
    target_role: Optional[str] = None
    handoff_type: HandoffType
    objective: str = Field(min_length=1)
    summary: Optional[str] = None
    acceptance_criteria: List[str] = Field(min_length=1)
    priority: Optional[str] = None
    issued_at: datetime = Field(default_factory=datetime.now)

    @model_validator(mode="after")
    def validate_target(self) -> "HandoffRequest":
        if not self.to_agent_id and not self.target_role:
            raise ValueError("either to_agent_id or target_role must be set")
        return self

    @field_validator("handoff_id")
    @classmethod
    def handoff_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("handoff_id must not be blank")
        return v.strip()

    @field_validator("from_agent_id")
    @classmethod
    def from_agent_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("from_agent_id must not be blank")
        return v.strip()

    @field_validator("objective")
    @classmethod
    def objective_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("objective must not be blank")
        return v.strip()


class HandoffContextPacket(BaseModel):
    context_packet_id: str = Field(min_length=1)
    task_ref: Optional[str] = None
    feature_ref: Optional[str] = None
    state_refs: List[str] = Field(default_factory=list)
    artifact_refs: List[str] = Field(default_factory=list)
    prompt_refs: List[str] = Field(default_factory=list)
    memory_refs: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    excluded_context_refs: List[str] = Field(default_factory=list)
    context_summary: Optional[str] = None

    @field_validator("context_packet_id")
    @classmethod
    def packet_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("context_packet_id must not be blank")
        return v.strip()


class HandoffConstraintPacket(BaseModel):
    constraint_packet_id: str = Field(min_length=1)
    time_budget: Optional[str] = None
    cost_budget: Optional[str] = None
    tool_constraints: List[str] = Field(default_factory=list)
    permission_constraints: List[str] = Field(default_factory=list)
    must_verify: bool = False
    must_not_delegate_further: bool = False
    required_output_types: List[str] = Field(default_factory=list)
    approval_requirements: List[str] = Field(default_factory=list)
    deadline: Optional[str] = None

    @field_validator("constraint_packet_id")
    @classmethod
    def constraint_packet_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("constraint_packet_id must not be blank")
        return v.strip()


class HandoffOwnershipRecord(BaseModel):
    ownership_id: str = Field(min_length=1)
    ownership_mode: OwnershipMode
    current_owner_agent_id: Optional[str] = None
    writer_agent_id: Optional[str] = None
    read_only_agent_ids: List[str] = Field(default_factory=list)
    ownership_reason: Optional[str] = None
    ownership_effective_from: datetime = Field(default_factory=datetime.now)
    ownership_effective_until: Optional[datetime] = None

    @field_validator("ownership_id")
    @classmethod
    def ownership_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("ownership_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def validate_write_ownership(self) -> "HandoffOwnershipRecord":
        if self.ownership_mode in WRITE_OWNERSHIP_MODES and not self.writer_agent_id:
            raise ValueError(
                f"ownership_mode {self.ownership_mode.value} requires a writer_agent_id"
            )
        return self

    @model_validator(mode="after")
    def validate_read_only_assist(self) -> "HandoffOwnershipRecord":
        if self.ownership_mode == OwnershipMode.READ_ONLY_ASSIST and self.writer_agent_id:
            raise ValueError(
                "read_only_assist must not assign write ownership"
            )
        return self

    @model_validator(mode="after")
    def validate_review_only(self) -> "HandoffOwnershipRecord":
        if self.ownership_mode == OwnershipMode.REVIEW_ONLY and self.writer_agent_id:
            raise ValueError(
                "review_only must not assign write ownership"
            )
        return self


class HandoffActionList(BaseModel):
    action_list_id: str = Field(min_length=1)
    actions: List[str] = Field(default_factory=list)
    pending_questions: List[str] = Field(default_factory=list)
    contingency_plans: List[str] = Field(default_factory=list)
    next_required_decision: Optional[str] = None
    completion_checklist: List[str] = Field(default_factory=list)

    @field_validator("action_list_id")
    @classmethod
    def action_list_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("action_list_id must not be blank")
        return v.strip()


class ReturnPayload(BaseModel):
    return_id: str = Field(min_length=1)
    handoff_id: str = Field(min_length=1)
    from_agent_id: str = Field(min_length=1)
    to_agent_id: Optional[str] = None
    return_status: ReturnStatus = ReturnStatus.SUBMITTED
    return_outcome: ReturnOutcome = ReturnOutcome.SUCCESS
    result_summary: Optional[str] = None
    output_refs: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    completed_actions: List[str] = Field(default_factory=list)
    unresolved_items: List[str] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    recommended_next_action: Optional[str] = None
    submitted_at: datetime = Field(default_factory=datetime.now)

    @field_validator("return_id")
    @classmethod
    def return_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("return_id must not be blank")
        return v.strip()

    @field_validator("handoff_id")
    @classmethod
    def handoff_id_in_return_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("handoff_id in return must not be blank")
        return v.strip()

    @field_validator("from_agent_id")
    @classmethod
    def from_agent_in_return_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("from_agent_id in return must not be blank")
        return v.strip()


class ReturnReviewRecord(BaseModel):
    review_id: str = Field(min_length=1)
    return_id: str = Field(min_length=1)
    reviewer_agent_id: str = Field(min_length=1)
    decision: ReturnStatus
    decision_reason: Optional[str] = None
    accepted_output_refs: List[str] = Field(default_factory=list)
    followup_required: bool = False
    followup_notes: Optional[str] = None
    reviewed_at: datetime = Field(default_factory=datetime.now)

    @field_validator("review_id")
    @classmethod
    def review_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("review_id must not be blank")
        return v.strip()

    @field_validator("return_id")
    @classmethod
    def return_id_in_review_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("return_id in review must not be blank")
        return v.strip()

    @field_validator("reviewer_agent_id")
    @classmethod
    def reviewer_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("reviewer_agent_id must not be blank")
        return v.strip()

class HandoffReturnEnvelope(BaseModel):
    envelope_id: str = Field(min_length=1)
    handoff_request: HandoffRequest
    context_packet: Optional[HandoffContextPacket] = None
    constraint_packet: Optional[HandoffConstraintPacket] = None
    ownership_record: Optional[HandoffOwnershipRecord] = None
    action_list: Optional[HandoffActionList] = None
    return_payload: Optional[ReturnPayload] = None
    return_review: Optional[ReturnReviewRecord] = None

    @field_validator("envelope_id")
    @classmethod
    def envelope_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("envelope_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def submitted_requires_return_payload(self) -> "HandoffReturnEnvelope":
        rp = self.return_payload
        if rp and rp.return_status == ReturnStatus.SUBMITTED:
            return self
        return self

    @model_validator(mode="after")
    def review_decision_requires_review_record(self) -> "HandoffReturnEnvelope":
        rp = self.return_payload
        rr = self.return_review
        if rr and rr.decision in (ReturnStatus.ACCEPTED, ReturnStatus.REJECTED):
            pass
        return self

    @model_validator(mode="after")
    def must_not_delegate_further_preserved(self) -> "HandoffReturnEnvelope":
        cp = self.constraint_packet
        if cp and cp.must_not_delegate_further:
            pass
        return self

    @model_validator(mode="after")
    def full_transfer_sets_current_owner(self) -> "HandoffReturnEnvelope":
        ow = self.ownership_record
        hr = self.handoff_request
        if ow and ow.ownership_mode == OwnershipMode.FULL_TRANSFER:
            if ow.current_owner_agent_id and ow.writer_agent_id:
                pass
        return self

    @model_validator(mode="after")
    def read_only_assist_no_write(self) -> "HandoffReturnEnvelope":
        ow = self.ownership_record
        if ow and ow.ownership_mode == OwnershipMode.READ_ONLY_ASSIST:
            if ow.writer_agent_id:
                raise ValueError(
                    "read_only_assist must not assign write ownership to the assisting agent"
                )
        return self
