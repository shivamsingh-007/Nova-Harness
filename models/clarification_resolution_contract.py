from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class GapType(str, Enum):
    missing_required = "missing_required"
    missing_optional = "missing_optional"
    ambiguous_value = "ambiguous_value"
    invalid_value = "invalid_value"
    conflicting_values = "conflicting_values"
    unsupported_request = "unsupported_request"


class GapSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    blocking = "blocking"


class ResolutionMethod(str, Enum):
    ask_user = "ask_user"
    infer_from_context = "infer_from_context"
    apply_default = "apply_default"
    manual_override = "manual_override"
    defer = "defer"
    escalate = "escalate"


class ResolutionStatus(str, Enum):
    open = "open"
    question_issued = "question_issued"
    answered = "answered"
    resolved = "resolved"
    deferred = "deferred"
    escalated = "escalated"
    closed_unresolved = "closed_unresolved"


class ClarificationDisposition(str, Enum):
    ready_to_proceed = "ready_to_proceed"
    proceed_with_gaps = "proceed_with_gaps"
    awaiting_response = "awaiting_response"
    rejected = "rejected"
    escalated = "escalated"


class MissingInfoGapRecord(BaseModel):
    gap_id: str = Field(min_length=1)
    intake_id: str = Field(min_length=1)
    field_name: str = Field(min_length=1)
    gap_type: GapType
    gap_severity: GapSeverity
    blocking: bool = False
    gap_summary: str = Field(min_length=1)
    candidate_values: List[str] = Field(default_factory=list)
    detected_at: datetime = Field(default_factory=datetime.now)

    @field_validator("gap_id")
    @classmethod
    def gap_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("gap_id must not be blank")
        return v.strip()

    @field_validator("intake_id")
    @classmethod
    def intake_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("intake_id must not be blank")
        return v.strip()

    @field_validator("field_name")
    @classmethod
    def field_name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field_name must not be blank")
        return v.strip()

    @field_validator("gap_summary")
    @classmethod
    def gap_summary_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("gap_summary must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def blocking_severity_consistency(self) -> "MissingInfoGapRecord":
        if self.gap_severity == GapSeverity.blocking and not self.blocking:
            raise ValueError("blocking severity must have blocking=True")
        return self


class ClarificationQuestionRecord(BaseModel):
    question_id: str = Field(min_length=1)
    gap_id: str = Field(min_length=1)
    field_name: str = Field(min_length=1)
    question_text: str = Field(min_length=1)
    question_order: int = Field(default=0, ge=0)
    response_type: Optional[str] = None
    recommended_examples: List[str] = Field(default_factory=list)
    issued_at: datetime = Field(default_factory=datetime.now)

    @field_validator("question_id")
    @classmethod
    def question_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("question_id must not be blank")
        return v.strip()

    @field_validator("gap_id")
    @classmethod
    def q_gap_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("gap_id must not be blank")
        return v.strip()

    @field_validator("field_name")
    @classmethod
    def q_field_name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field_name must not be blank")
        return v.strip()

    @field_validator("question_text")
    @classmethod
    def question_text_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("question_text must not be blank")
        return v.strip()


class ResolutionAttemptRecord(BaseModel):
    attempt_id: str = Field(min_length=1)
    gap_id: str = Field(min_length=1)
    resolution_method: ResolutionMethod
    attempt_input_ref: Optional[str] = None
    proposed_value_ref: Optional[str] = None
    confidence: Optional[float] = Field(default=None)
    attempt_reason: Optional[str] = None
    attempted_at: datetime = Field(default_factory=datetime.now)

    @field_validator("attempt_id")
    @classmethod
    def attempt_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("attempt_id must not be blank")
        return v.strip()

    @field_validator("gap_id")
    @classmethod
    def a_gap_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("gap_id must not be blank")
        return v.strip()

    @field_validator("confidence")
    @classmethod
    def confidence_must_be_bounded(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v

    @model_validator(mode="after")
    def resolved_attempt_needs_value(self) -> "ResolutionAttemptRecord":
        if self.resolution_method in (
            ResolutionMethod.ask_user,
            ResolutionMethod.infer_from_context,
            ResolutionMethod.apply_default,
            ResolutionMethod.manual_override,
        ):
            if not self.proposed_value_ref:
                raise ValueError(f"{self.resolution_method} attempt must include proposed_value_ref")
        return self


class FieldResolutionRecord(BaseModel):
    field_resolution_id: str = Field(min_length=1)
    gap_id: str = Field(min_length=1)
    resolved_value_ref: Optional[str] = None
    resolution_method: ResolutionMethod
    resolution_status: ResolutionStatus
    approved_by: Optional[str] = None
    notes: Optional[str] = None
    resolved_at: datetime = Field(default_factory=datetime.now)

    @field_validator("field_resolution_id")
    @classmethod
    def field_resolution_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field_resolution_id must not be blank")
        return v.strip()

    @field_validator("gap_id")
    @classmethod
    def fr_gap_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("gap_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def resolved_status_needs_value_or_notes(self) -> "FieldResolutionRecord":
        resolved_states = {
            ResolutionStatus.resolved,
            ResolutionStatus.deferred,
            ResolutionStatus.escalated,
            ResolutionStatus.closed_unresolved,
        }
        if self.resolution_status in resolved_states:
            if not self.resolved_value_ref and not self.notes:
                raise ValueError(f"{self.resolution_status} state requires resolved_value_ref or notes")
        return self


class ResolutionPolicyRecord(BaseModel):
    policy_id: str = Field(min_length=1)
    field_name: str = Field(min_length=1)
    required: bool = True
    allow_default: bool = False
    allow_inference: bool = False
    allow_defer: bool = False
    escalation_threshold: Optional[int] = Field(default=None)
    max_attempts: Optional[int] = Field(default=None)

    @field_validator("policy_id")
    @classmethod
    def policy_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("policy_id must not be blank")
        return v.strip()

    @field_validator("field_name")
    @classmethod
    def p_field_name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field_name must not be blank")
        return v.strip()

    @field_validator("max_attempts")
    @classmethod
    def max_attempts_must_be_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1:
            raise ValueError("max_attempts must be >= 1")
        return v

    @field_validator("escalation_threshold")
    @classmethod
    def escalation_threshold_must_be_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1:
            raise ValueError("escalation_threshold must be >= 1")
        return v

    @model_validator(mode="after")
    def required_field_disallows_defer_without_policy(self) -> "ResolutionPolicyRecord":
        if self.required and self.allow_defer:
            if not self.escalation_threshold:
                raise ValueError("required fields with allow_defer must set escalation_threshold")
        return self


class ClarificationSessionRecord(BaseModel):
    clarification_session_id: str = Field(min_length=1)
    intake_id: str = Field(min_length=1)
    related_gap_ids: List[str] = Field(default_factory=list)
    active_question_ids: List[str] = Field(default_factory=list)
    completed_question_ids: List[str] = Field(default_factory=list)
    session_status: str = "in_progress"
    started_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator("clarification_session_id")
    @classmethod
    def session_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("clarification_session_id must not be blank")
        return v.strip()

    @field_validator("intake_id")
    @classmethod
    def s_intake_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("intake_id must not be blank")
        return v.strip()

    @field_validator("session_status")
    @classmethod
    def session_status_must_be_valid(cls, v: str) -> str:
        allowed = {"in_progress", "completed", "escalated", "closed"}
        if v not in allowed:
            raise ValueError(f"session_status must be one of {allowed}")
        return v

    @model_validator(mode="after")
    def no_overlap_in_question_ids(self) -> "ClarificationSessionRecord":
        overlap = set(self.active_question_ids) & set(self.completed_question_ids)
        if overlap:
            raise ValueError(f"question ids cannot be both active and completed: {overlap}")
        return self


class ClarificationDecisionRecord(BaseModel):
    decision_id: str = Field(min_length=1)
    clarification_session_id: str = Field(min_length=1)
    clarification_disposition: ClarificationDisposition
    remaining_open_gap_ids: List[str] = Field(default_factory=list)
    decision_reason: Optional[str] = None
    proceeding_constraints: List[str] = Field(default_factory=list)
    decided_at: datetime = Field(default_factory=datetime.now)

    @field_validator("decision_id")
    @classmethod
    def decision_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("decision_id must not be blank")
        return v.strip()

    @field_validator("clarification_session_id")
    @classmethod
    def cd_session_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("clarification_session_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def rejected_or_escalated_needs_reason(self) -> "ClarificationDecisionRecord":
        if self.clarification_disposition in (
            ClarificationDisposition.rejected,
            ClarificationDisposition.escalated,
        ):
            if not self.decision_reason:
                raise ValueError("rejected/escalated disposition must include decision_reason")
        return self


class ClarificationResolutionEnvelope(BaseModel):
    envelope_id: str = Field(min_length=1)
    gaps: List[MissingInfoGapRecord] = Field(default_factory=list)
    questions: List[ClarificationQuestionRecord] = Field(default_factory=list)
    attempts: List[ResolutionAttemptRecord] = Field(default_factory=list)
    field_resolutions: List[FieldResolutionRecord] = Field(default_factory=list)
    policies: List[ResolutionPolicyRecord] = Field(default_factory=list)
    session: ClarificationSessionRecord
    decision: ClarificationDecisionRecord

    @field_validator("envelope_id")
    @classmethod
    def envelope_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("envelope_id must not be blank")
        return v.strip()

    def _valid_gap_ids(self) -> set:
        return {g.gap_id for g in self.gaps}

    def _valid_question_ids(self) -> set:
        return {q.question_id for q in self.questions}

    @model_validator(mode="after")
    def questions_reference_valid_gaps(self) -> "ClarificationResolutionEnvelope":
        valid_ids = self._valid_gap_ids()
        for q in self.questions:
            if q.gap_id not in valid_ids:
                raise ValueError(f"question '{q.question_id}' references unknown gap '{q.gap_id}'")
        return self

    @model_validator(mode="after")
    def attempts_reference_valid_gaps(self) -> "ClarificationResolutionEnvelope":
        valid_ids = self._valid_gap_ids()
        for a in self.attempts:
            if a.gap_id not in valid_ids:
                raise ValueError(f"attempt '{a.attempt_id}' references unknown gap '{a.gap_id}'")
        return self

    @model_validator(mode="after")
    def field_resolutions_reference_valid_gaps(self) -> "ClarificationResolutionEnvelope":
        valid_ids = self._valid_gap_ids()
        for fr in self.field_resolutions:
            if fr.gap_id not in valid_ids:
                raise ValueError(f"field_resolution '{fr.field_resolution_id}' references unknown gap '{fr.gap_id}'")
        return self

    @model_validator(mode="after")
    def session_gaps_reference_valid_gaps(self) -> "ClarificationResolutionEnvelope":
        valid_ids = self._valid_gap_ids()
        for gid in self.session.related_gap_ids:
            if gid not in valid_ids:
                raise ValueError(f"session references unknown gap '{gid}'")
        return self

    @model_validator(mode="after")
    def session_questions_reference_valid_questions(self) -> "ClarificationResolutionEnvelope":
        valid_ids = self._valid_question_ids()
        for qid in self.session.active_question_ids:
            if qid not in valid_ids:
                raise ValueError(f"session active question '{qid}' references unknown question")
        for qid in self.session.completed_question_ids:
            if qid not in valid_ids:
                raise ValueError(f"session completed question '{qid}' references unknown question")
        return self

    @model_validator(mode="after")
    def decision_open_gaps_reference_valid_gaps(self) -> "ClarificationResolutionEnvelope":
        valid_ids = self._valid_gap_ids()
        for gid in self.decision.remaining_open_gap_ids:
            if gid not in valid_ids:
                raise ValueError(f"decision references unknown gap '{gid}'")
        return self

    @model_validator(mode="after")
    def awaiting_response_needs_open_questions(self) -> "ClarificationResolutionEnvelope":
        if self.decision.clarification_disposition == ClarificationDisposition.awaiting_response:
            if not self.session.active_question_ids:
                raise ValueError(
                    "awaiting_response disposition requires at least one active question"
                )
        return self

    @model_validator(mode="after")
    def ready_to_proceed_no_unresolved_blocking_gaps(self) -> "ClarificationResolutionEnvelope":
        if self.decision.clarification_disposition in (
            ClarificationDisposition.ready_to_proceed,
            ClarificationDisposition.proceed_with_gaps,
        ):
            resolved_gap_ids = {fr.gap_id for fr in self.field_resolutions
                                if fr.resolution_status in (
                                    ResolutionStatus.resolved,
                                    ResolutionStatus.deferred,
                                    ResolutionStatus.escalated,
                                    ResolutionStatus.closed_unresolved,
                                )}
            for gap in self.gaps:
                if gap.blocking and gap.gap_id not in resolved_gap_ids:
                    raise ValueError(
                        f"cannot proceed with unresolved blocking gap '{gap.gap_id}'"
                    )
        return self
