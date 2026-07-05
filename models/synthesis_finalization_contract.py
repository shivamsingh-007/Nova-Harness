from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum


class SynthesisInputType(str, Enum):
    branch_output = "branch_output"
    delegate_return = "delegate_return"
    verification_report = "verification_report"
    review_note = "review_note"
    artifact_ref = "artifact_ref"
    state_delta = "state_delta"
    evidence_bundle = "evidence_bundle"


class NormalizationMode(str, Enum):
    identity = "identity"
    schema_map = "schema_map"
    rank_and_filter = "rank_and_filter"
    deduplicate = "deduplicate"
    canonicalize = "canonicalize"


class SynthesisPolicy(str, Enum):
    merge_all_accepted = "merge_all_accepted"
    merge_ranked_subset = "merge_ranked_subset"
    verification_first = "verification_first"
    majority_supported = "majority_supported"
    manual_editorial_review = "manual_editorial_review"


class FinalizationStatus(str, Enum):
    draft = "draft"
    in_synthesis = "in_synthesis"
    validated = "validated"
    approved = "approved"
    rejected = "rejected"
    needs_rework = "needs_rework"
    released = "released"


class FinalDisposition(str, Enum):
    accept = "accept"
    accept_with_caveats = "accept_with_caveats"
    return_for_rework = "return_for_rework"
    reject = "reject"
    escalate = "escalate"


class SynthesisSourceRecord(BaseModel):
    source_id: str = Field(min_length=1)
    source_type: SynthesisInputType
    source_ref: str = Field(min_length=1)
    origin_agent_id: Optional[str] = None
    origin_role_id: Optional[str] = None
    eligibility_status: str = Field(min_length=1)
    selection_reason: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    priority: Optional[str] = None
    evidence_refs: List[str] = Field(default_factory=list)

    @field_validator("source_id")
    @classmethod
    def source_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("source_id must not be blank")
        return v.strip()

    @field_validator("source_ref")
    @classmethod
    def source_ref_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("source_ref must not be blank")
        return v.strip()

    @field_validator("eligibility_status")
    @classmethod
    def eligibility_status_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("eligibility_status must not be blank")
        return v.strip()


class NormalizationRecord(BaseModel):
    normalization_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    normalization_mode: NormalizationMode
    input_ref: str = Field(min_length=1)
    normalized_ref: str = Field(min_length=1)
    schema_version: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("normalization_id")
    @classmethod
    def normalization_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("normalization_id must not be blank")
        return v.strip()

    @field_validator("source_id")
    @classmethod
    def norm_source_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("source_id must not be blank")
        return v.strip()

    @field_validator("input_ref")
    @classmethod
    def input_ref_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("input_ref must not be blank")
        return v.strip()

    @field_validator("normalized_ref")
    @classmethod
    def normalized_ref_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("normalized_ref must not be blank")
        return v.strip()


class SynthesisConflictRecord(BaseModel):
    conflict_id: str = Field(min_length=1)
    source_ids: List[str] = Field(min_length=2)
    conflict_type: Optional[str] = None
    conflict_summary: str = Field(min_length=1)
    resolution_strategy: Optional[str] = None
    resolved: bool = False
    resolution_notes: Optional[str] = None
    review_required: bool = False

    @field_validator("conflict_id")
    @classmethod
    def conflict_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("conflict_id must not be blank")
        return v.strip()

    @field_validator("source_ids")
    @classmethod
    def conflict_source_ids_must_be_unique(cls, v: List[str]) -> List[str]:
        if len(v) != len(set(v)):
            raise ValueError("source_ids in conflict must be unique")
        return v

    @field_validator("conflict_summary")
    @classmethod
    def conflict_summary_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("conflict_summary must not be blank")
        return v.strip()


class SynthesisDecisionRecord(BaseModel):
    decision_id: str = Field(min_length=1)
    synthesis_policy: SynthesisPolicy
    selected_source_ids: List[str] = Field(default_factory=list)
    rejected_source_ids: List[str] = Field(default_factory=list)
    conflict_ids: List[str] = Field(default_factory=list)
    decision_reason: Optional[str] = None
    editorial_notes: Optional[str] = None
    decision_made_at: Optional[datetime] = None

    @field_validator("decision_id")
    @classmethod
    def decision_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("decision_id must not be blank")
        return v.strip()


class ValidationSummaryRecord(BaseModel):
    validation_summary_id: str = Field(min_length=1)
    validation_refs: List[str] = Field(default_factory=list)
    checks_passed: List[str] = Field(default_factory=list)
    checks_failed: List[str] = Field(default_factory=list)
    evidence_gaps: List[str] = Field(default_factory=list)
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    review_required: bool = False
    summary: Optional[str] = None

    @field_validator("validation_summary_id")
    @classmethod
    def validation_summary_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("validation_summary_id must not be blank")
        return v.strip()


class FinalizationRecord(BaseModel):
    finalization_id: str = Field(min_length=1)
    finalization_status: FinalizationStatus
    final_disposition: FinalDisposition
    approved_by: Optional[str] = None
    approval_reason: Optional[str] = None
    release_ready: bool = False
    followup_required: bool = False
    finalized_at: Optional[datetime] = None

    @field_validator("finalization_id")
    @classmethod
    def finalization_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("finalization_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def validate_finalization(self) -> "FinalizationRecord":
        if self.final_disposition in (FinalDisposition.return_for_rework, FinalDisposition.reject) and not self.approval_reason:
            raise ValueError("return_for_rework or reject must include approval_reason")
        if self.final_disposition in (FinalDisposition.accept, FinalDisposition.accept_with_caveats) and not self.approval_reason:
            raise ValueError("accept or accept_with_caveats must include approval_reason")
        if self.finalization_status == FinalizationStatus.released and not self.release_ready:
            raise ValueError("released status requires release_ready=True")
        return self


class SynthesisOutputRecord(BaseModel):
    output_id: str = Field(min_length=1)
    output_type: Optional[str] = None
    result_summary: str = Field(min_length=1)
    final_output_refs: List[str] = Field(default_factory=list)
    supporting_evidence_refs: List[str] = Field(default_factory=list)
    residual_uncertainties: List[str] = Field(default_factory=list)
    consumer_notes: Optional[str] = None

    @field_validator("output_id")
    @classmethod
    def output_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("output_id must not be blank")
        return v.strip()

    @field_validator("result_summary")
    @classmethod
    def result_summary_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("result_summary must not be blank")
        return v.strip()


class SynthesisFinalizationEnvelope(BaseModel):
    envelope_id: str = Field(min_length=1)
    sources: List[SynthesisSourceRecord] = Field(min_length=1)
    normalizations: List[NormalizationRecord] = Field(default_factory=list)
    conflicts: List[SynthesisConflictRecord] = Field(default_factory=list)
    decision: SynthesisDecisionRecord
    validation_summary: ValidationSummaryRecord
    finalization: FinalizationRecord
    output: SynthesisOutputRecord

    @field_validator("envelope_id")
    @classmethod
    def envelope_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("envelope_id must not be blank")
        return v.strip()

    @field_validator("sources")
    @classmethod
    def at_least_one_eligible_source(cls, v: List[SynthesisSourceRecord]) -> List[SynthesisSourceRecord]:
        eligible = [s for s in v if s.eligibility_status == "accepted"]
        if len(eligible) < 1:
            raise ValueError("at least one source must be eligible (accepted)")
        return v

    @field_validator("output")
    @classmethod
    def accept_disposition_requires_final_output_refs(cls, v: SynthesisOutputRecord, info) -> SynthesisOutputRecord:
        finalization = info.data.get("finalization")
        if finalization and finalization.final_disposition in (FinalDisposition.accept, FinalDisposition.accept_with_caveats):
            if not v.final_output_refs:
                raise ValueError("accept disposition requires at least one final_output_ref")
        return v

    @field_validator("validation_summary")
    @classmethod
    def unresolved_conflicts_force_review_or_block(cls, v: ValidationSummaryRecord, info) -> ValidationSummaryRecord:
        conflicts = info.data.get("conflicts", [])
        unresolved = [c for c in conflicts if not c.resolved]
        if unresolved:
            if not v.review_required:
                raise ValueError("unresolved conflicts must set review_required=True on validation summary")
        return v

    def check_rejected_only_cannot_approve(self) -> None:
        eligible = [s for s in self.sources if s.eligibility_status == "accepted"]
        if len(eligible) == 0 and self.finalization.finalization_status in (
            FinalizationStatus.approved, FinalizationStatus.released
        ):
            raise ValueError("rejected-only inputs cannot become approved or released outputs")

    def check_all_envelope_rules(self) -> None:
        self.check_rejected_only_cannot_approve()
