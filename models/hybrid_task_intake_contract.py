from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class IntakeSourceType(str, Enum):
    user_message = "user_message"
    form_submission = "form_submission"
    api_payload = "api_payload"
    artifact_upload = "artifact_upload"
    mixed_input = "mixed_input"


class ExtractionStatus(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    extracted = "extracted"
    partially_extracted = "partially_extracted"
    failed = "failed"
    needs_review = "needs_review"


class FieldResolutionStatus(str, Enum):
    explicit = "explicit"
    inferred = "inferred"
    missing = "missing"
    ambiguous = "ambiguous"
    invalid = "invalid"


class ClarificationMode(str, Enum):
    ask_user = "ask_user"
    auto_repair = "auto_repair"
    route_to_review = "route_to_review"
    defer_until_context_available = "defer_until_context_available"


class IntakeDisposition(str, Enum):
    accepted = "accepted"
    accepted_with_gaps = "accepted_with_gaps"
    clarification_required = "clarification_required"
    rejected = "rejected"
    escalated = "escalated"


class RawTaskIntake(BaseModel):
    intake_id: str = Field(min_length=1)
    source_type: IntakeSourceType
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    received_at: datetime = Field(default_factory=datetime.now)
    raw_text: Optional[str] = None
    raw_artifact_refs: List[str] = Field(default_factory=list)
    language: Optional[str] = None
    channel: Optional[str] = None
    source_metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("intake_id")
    @classmethod
    def intake_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("intake_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def raw_content_must_exist(self) -> "RawTaskIntake":
        if not self.raw_text and not self.raw_artifact_refs:
            raise ValueError("raw_text or raw_artifact_refs must be provided")
        return self


class ExtractedFieldRecord(BaseModel):
    field_record_id: str = Field(min_length=1)
    field_name: str = Field(min_length=1)
    field_value_ref: Optional[str] = None
    resolution_status: FieldResolutionStatus
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    source_span: Optional[str] = None
    extraction_reason: Optional[str] = None
    validation_notes: Optional[str] = None

    @field_validator("field_record_id")
    @classmethod
    def field_record_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field_record_id must not be blank")
        return v.strip()

    @field_validator("field_name")
    @classmethod
    def field_name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field_name must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def missing_field_not_resolved(self) -> "ExtractedFieldRecord":
        if self.resolution_status == FieldResolutionStatus.missing and self.field_value_ref is not None:
            raise ValueError("missing fields must not have a field_value_ref")
        return self


class StructuredTaskExtraction(BaseModel):
    extraction_id: str = Field(min_length=1)
    intake_id: str = Field(min_length=1)
    target_schema_id: str = Field(min_length=1)
    extraction_status: ExtractionStatus
    task_type: Optional[str] = None
    title: Optional[str] = None
    objective: Optional[str] = None
    constraints: List[str] = Field(default_factory=list)
    deadline: Optional[str] = None
    priority: Optional[str] = None
    requested_outputs: List[str] = Field(default_factory=list)
    extracted_at: Optional[datetime] = None

    @field_validator("extraction_id")
    @classmethod
    def extraction_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("extraction_id must not be blank")
        return v.strip()

    @field_validator("intake_id")
    @classmethod
    def ext_intake_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("intake_id must not be blank")
        return v.strip()

    @field_validator("target_schema_id")
    @classmethod
    def target_schema_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("target_schema_id must not be blank")
        return v.strip()


class AmbiguityRecord(BaseModel):
    ambiguity_id: str = Field(min_length=1)
    field_name: str = Field(min_length=1)
    ambiguity_summary: str = Field(min_length=1)
    candidate_values: List[str] = Field(default_factory=list)
    impact_level: Optional[str] = None
    clarification_needed: bool = False

    @field_validator("ambiguity_id")
    @classmethod
    def ambiguity_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("ambiguity_id must not be blank")
        return v.strip()

    @field_validator("field_name")
    @classmethod
    def amb_field_name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field_name must not be blank")
        return v.strip()

    @field_validator("ambiguity_summary")
    @classmethod
    def ambiguity_summary_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("ambiguity_summary must not be blank")
        return v.strip()


class ClarificationRequestRecord(BaseModel):
    clarification_id: str = Field(min_length=1)
    intake_id: str = Field(min_length=1)
    clarification_mode: ClarificationMode
    questions: List[str] = Field(default_factory=list)
    blocking_fields: List[str] = Field(default_factory=list)
    recommended_defaults: Dict[str, str] = Field(default_factory=dict)
    requested_at: Optional[datetime] = None

    @field_validator("clarification_id")
    @classmethod
    def clarification_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("clarification_id must not be blank")
        return v.strip()

    @field_validator("intake_id")
    @classmethod
    def cl_intake_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("intake_id must not be blank")
        return v.strip()


class IntakeValidationRecord(BaseModel):
    validation_id: str = Field(min_length=1)
    intake_id: str = Field(min_length=1)
    required_fields_checked: List[str] = Field(default_factory=list)
    missing_required_fields: List[str] = Field(default_factory=list)
    invalid_fields: List[str] = Field(default_factory=list)
    average_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    schema_valid: bool = False
    review_required: bool = False
    validation_summary: Optional[str] = None

    @field_validator("validation_id")
    @classmethod
    def validation_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("validation_id must not be blank")
        return v.strip()

    @field_validator("intake_id")
    @classmethod
    def val_intake_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("intake_id must not be blank")
        return v.strip()


class TaskIntakeDecisionRecord(BaseModel):
    decision_id: str = Field(min_length=1)
    intake_id: str = Field(min_length=1)
    intake_disposition: IntakeDisposition
    decision_reason: Optional[str] = None
    accepted_task_ref: Optional[str] = None
    clarification_ref: Optional[str] = None
    escalation_ref: Optional[str] = None
    decided_at: Optional[datetime] = None

    @field_validator("decision_id")
    @classmethod
    def decision_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("decision_id must not be blank")
        return v.strip()

    @field_validator("intake_id")
    @classmethod
    def dec_intake_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("intake_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def validate_decision(self) -> "TaskIntakeDecisionRecord":
        if self.intake_disposition in (IntakeDisposition.accepted, IntakeDisposition.accepted_with_gaps):
            if not self.decision_reason:
                raise ValueError("accepted disposition must include decision_reason")
        return self


class HybridTaskIntakeEnvelope(BaseModel):
    envelope_id: str = Field(min_length=1)
    raw_intake: RawTaskIntake
    structured_extraction: StructuredTaskExtraction
    fields: List[ExtractedFieldRecord] = Field(default_factory=list)
    ambiguities: List[AmbiguityRecord] = Field(default_factory=list)
    clarification_request: Optional[ClarificationRequestRecord] = None
    validation: IntakeValidationRecord
    decision: TaskIntakeDecisionRecord

    @field_validator("envelope_id")
    @classmethod
    def envelope_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("envelope_id must not be blank")
        return v.strip()

    @field_validator("ambiguities")
    @classmethod
    def ambiguities_must_reference_valid_fields(cls, v: List[AmbiguityRecord], info) -> List[AmbiguityRecord]:
        if not info.data.get("fields"):
            return v
        valid_field_names = {f.field_name for f in info.data["fields"]}
        for amb in v:
            if amb.field_name not in valid_field_names:
                raise ValueError(f"ambiguity references unknown field '{amb.field_name}'")
        return v

    @field_validator("decision")
    @classmethod
    def accepted_requires_schema_valid(cls, v: TaskIntakeDecisionRecord, info) -> TaskIntakeDecisionRecord:
        validation = info.data.get("validation")
        if v.intake_disposition in (IntakeDisposition.accepted, IntakeDisposition.accepted_with_gaps):
            if validation and not validation.schema_valid:
                raise ValueError("accepted disposition requires schema_valid=True")
        return v

    @field_validator("decision")
    @classmethod
    def clarification_requires_request(cls, v: TaskIntakeDecisionRecord, info) -> TaskIntakeDecisionRecord:
        if v.intake_disposition == IntakeDisposition.clarification_required:
            clarification = info.data.get("clarification_request")
            if not clarification:
                raise ValueError("clarification_required must include a clarification_request")
        return v

    @field_validator("decision")
    @classmethod
    def missing_required_fields_block_unconditional_acceptance(
        cls, v: TaskIntakeDecisionRecord, info
    ) -> TaskIntakeDecisionRecord:
        validation = info.data.get("validation")
        if v.intake_disposition == IntakeDisposition.accepted:
            if validation and validation.missing_required_fields:
                raise ValueError("missing required fields block unconditional acceptance")
        return v
