from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class CriterionType(str, Enum):
    functional = "functional"
    output = "output"
    quality = "quality"
    constraint = "constraint"
    approval = "approval"
    evidence = "evidence"


class CriterionStatus(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    met = "met"
    failed = "failed"
    waived = "waived"


class DoneCheckType(str, Enum):
    quality_gate = "quality_gate"
    verification_gate = "verification_gate"
    documentation_gate = "documentation_gate"
    policy_gate = "policy_gate"
    release_gate = "release_gate"


class DoneStatus(str, Enum):
    not_checked = "not_checked"
    passed = "passed"
    failed = "failed"
    waived = "waived"


class CompletionDisposition(str, Enum):
    accepted = "accepted"
    accepted_with_caveats = "accepted_with_caveats"
    needs_rework = "needs_rework"
    rejected = "rejected"
    deferred = "deferred"


class AcceptanceCriterionRecord(BaseModel):
    criterion_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    criterion_type: CriterionType
    description: str = Field(min_length=1)
    priority: int = Field(default=0, ge=0)
    required: bool = True
    test_method: Optional[str] = None
    expected_result: Optional[str] = None
    status: CriterionStatus = CriterionStatus.not_started
    owner: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("criterion_id")
    @classmethod
    def criterion_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("criterion_id must not be blank")
        return v.strip()

    @field_validator("task_id")
    @classmethod
    def task_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("task_id must not be blank")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("description must not be blank")
        return v.strip()


class AcceptanceCriteriaSet(BaseModel):
    criteria_set_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    title: Optional[str] = None
    criteria: List[AcceptanceCriterionRecord] = Field(default_factory=list)
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    version: str = "1.0"

    @field_validator("criteria_set_id")
    @classmethod
    def criteria_set_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("criteria_set_id must not be blank")
        return v.strip()

    @field_validator("task_id")
    @classmethod
    def cs_task_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("task_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def required_criteria_not_waived_without_notes(self) -> "AcceptanceCriteriaSet":
        for c in self.criteria:
            if c.required and c.status == CriterionStatus.waived:
                if not c.notes:
                    raise ValueError(
                        f"required criterion '{c.criterion_id}' waived without notes"
                    )
        return self


class DefinitionOfDoneCheck(BaseModel):
    done_check_id: str = Field(min_length=1)
    done_check_type: DoneCheckType
    description: str = Field(min_length=1)
    required: bool = True
    validation_method: Optional[str] = None
    status: DoneStatus = DoneStatus.not_checked
    applies_to_task_types: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

    @field_validator("done_check_id")
    @classmethod
    def done_check_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("done_check_id must not be blank")
        return v.strip()

    @field_validator("description")
    @classmethod
    def dod_description_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("description must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def required_check_not_waived_without_notes(self) -> "DefinitionOfDoneCheck":
        if self.required and self.status == DoneStatus.waived:
            if not self.notes:
                raise ValueError(
                    f"required done check '{self.done_check_id}' waived without notes"
                )
        return self


class DefinitionOfDoneProfile(BaseModel):
    dod_profile_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: Optional[str] = None
    checks: List[DefinitionOfDoneCheck] = Field(default_factory=list)
    version: str = "1.0"
    owner: Optional[str] = None
    active: bool = True

    @field_validator("dod_profile_id")
    @classmethod
    def dod_profile_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("dod_profile_id must not be blank")
        return v.strip()

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()


class CompletionEvidenceRecord(BaseModel):
    evidence_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    criterion_or_check_ref: Optional[str] = None
    evidence_type: str = Field(min_length=1)
    artifact_refs: List[str] = Field(default_factory=list)
    validation_refs: List[str] = Field(default_factory=list)
    summary: str = Field(min_length=1)
    collected_at: datetime = Field(default_factory=datetime.now)

    @field_validator("evidence_id")
    @classmethod
    def evidence_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("evidence_id must not be blank")
        return v.strip()

    @field_validator("task_id")
    @classmethod
    def ev_task_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("task_id must not be blank")
        return v.strip()

    @field_validator("evidence_type")
    @classmethod
    def evidence_type_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("evidence_type must not be blank")
        return v.strip()

    @field_validator("summary")
    @classmethod
    def summary_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("summary must not be blank")
        return v.strip()


class CompletionAssessmentRecord(BaseModel):
    assessment_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    criteria_met_count: int = Field(default=0, ge=0)
    criteria_failed_count: int = Field(default=0, ge=0)
    dod_passed_count: int = Field(default=0, ge=0)
    dod_failed_count: int = Field(default=0, ge=0)
    waived_items: List[str] = Field(default_factory=list)
    open_items: List[str] = Field(default_factory=list)
    assessment_summary: Optional[str] = None
    assessed_at: datetime = Field(default_factory=datetime.now)

    @field_validator("assessment_id")
    @classmethod
    def assessment_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("assessment_id must not be blank")
        return v.strip()

    @field_validator("task_id")
    @classmethod
    def asm_task_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("task_id must not be blank")
        return v.strip()


class CompletionDecisionRecord(BaseModel):
    decision_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    completion_disposition: CompletionDisposition
    approved_by: Optional[str] = None
    decision_reason: Optional[str] = None
    release_ready: bool = False
    followup_actions: List[str] = Field(default_factory=list)
    decided_at: datetime = Field(default_factory=datetime.now)

    @field_validator("decision_id")
    @classmethod
    def decision_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("decision_id must not be blank")
        return v.strip()

    @field_validator("task_id")
    @classmethod
    def cd_task_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("task_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def rejected_or_needs_rework_needs_reason(self) -> "CompletionDecisionRecord":
        if self.completion_disposition in (
            CompletionDisposition.rejected,
            CompletionDisposition.needs_rework,
        ):
            if not self.decision_reason:
                raise ValueError("rejected/needs_rework disposition must include decision_reason")
        return self

    @model_validator(mode="after")
    def accepted_with_caveats_needs_followup(self) -> "CompletionDecisionRecord":
        if self.completion_disposition == CompletionDisposition.accepted_with_caveats:
            if not self.followup_actions and not self.decision_reason:
                raise ValueError(
                    "accepted_with_caveats must include followup_actions or decision_reason"
                )
        return self


class AcceptanceDoneEnvelope(BaseModel):
    envelope_id: str = Field(min_length=1)
    acceptance_criteria_set: AcceptanceCriteriaSet
    definition_of_done_profile: DefinitionOfDoneProfile
    evidence_records: List[CompletionEvidenceRecord] = Field(default_factory=list)
    assessment: CompletionAssessmentRecord
    decision: CompletionDecisionRecord

    @field_validator("envelope_id")
    @classmethod
    def envelope_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("envelope_id must not be blank")
        return v.strip()

    def _valid_criterion_ids(self) -> set:
        return {c.criterion_id for c in self.acceptance_criteria_set.criteria}

    def _valid_done_check_ids(self) -> set:
        return {d.done_check_id for d in self.definition_of_done_profile.checks}

    @model_validator(mode="after")
    def evidence_references_valid_criterion_or_check(self) -> "AcceptanceDoneEnvelope":
        valid_criterion_ids = self._valid_criterion_ids()
        valid_check_ids = self._valid_done_check_ids()
        for ev in self.evidence_records:
            ref = ev.criterion_or_check_ref
            if ref is not None:
                if ref not in valid_criterion_ids and ref not in valid_check_ids:
                    raise ValueError(
                        f"evidence '{ev.evidence_id}' references unknown criterion or check '{ref}'"
                    )
        return self

    @model_validator(mode="after")
    def accepted_requires_required_criteria_and_checks(self) -> "AcceptanceDoneEnvelope":
        if self.decision.completion_disposition == CompletionDisposition.accepted:
            required_criteria = [
                c for c in self.acceptance_criteria_set.criteria if c.required
            ]
            for c in required_criteria:
                if c.status not in (CriterionStatus.met, CriterionStatus.waived):
                    raise ValueError(
                        f"accepted requires required criterion '{c.criterion_id}' to be met or waived"
                    )
                if c.status == CriterionStatus.waived and not c.notes:
                    raise ValueError(
                        f"required criterion '{c.criterion_id}' waived without notes"
                    )
            required_checks = [
                d for d in self.definition_of_done_profile.checks if d.required
            ]
            for d in required_checks:
                if d.status not in (DoneStatus.passed, DoneStatus.waived):
                    raise ValueError(
                        f"accepted requires required DoD check '{d.done_check_id}' to be passed or waived"
                    )
                if d.status == DoneStatus.waived and not d.notes:
                    raise ValueError(
                        f"required DoD check '{d.done_check_id}' waived without notes"
                    )
        return self

    @model_validator(mode="after")
    def accepted_with_caveats_requires_actions(self) -> "AcceptanceDoneEnvelope":
        if self.decision.completion_disposition == CompletionDisposition.accepted_with_caveats:
            if not self.decision.followup_actions:
                raise ValueError(
                    "accepted_with_caveats must include followup_actions"
                )
        return self

    @model_validator(mode="after")
    def release_ready_requires_passed_release_gates(self) -> "AcceptanceDoneEnvelope":
        if self.decision.release_ready:
            release_checks = [
                d for d in self.definition_of_done_profile.checks
                if d.done_check_type == DoneCheckType.release_gate and d.required
            ]
            for d in release_checks:
                if d.status != DoneStatus.passed:
                    raise ValueError(
                        f"release_ready requires release gate '{d.done_check_id}' to be passed"
                    )
        return self
