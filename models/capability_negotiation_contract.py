from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class CapabilityCategory(str, Enum):
    tooling = "tooling"
    model_behavior = "model_behavior"
    skill_support = "skill_support"
    output_format = "output_format"
    context_window = "context_window"
    safety_control = "safety_control"
    integration = "integration"
    interaction_mode = "interaction_mode"


class CompatibilityStatus(str, Enum):
    compatible = "compatible"
    partially_compatible = "partially_compatible"
    incompatible = "incompatible"
    unknown = "unknown"


class NegotiationMode(str, Enum):
    strict_intersection = "strict_intersection"
    best_effort = "best_effort"
    required_only = "required_only"
    manual_override = "manual_override"


class RequirementLevel(str, Enum):
    required = "required"
    preferred = "preferred"
    optional = "optional"


class NegotiationDisposition(str, Enum):
    proceed = "proceed"
    proceed_with_fallbacks = "proceed_with_fallbacks"
    reroute = "reroute"
    reject = "reject"
    escalate = "escalate"


class CapabilityDeclaration(BaseModel):
    declaration_id: str = Field(min_length=1)
    party_ref: str = Field(min_length=1)
    party_type: Optional[str] = None
    capability_category: CapabilityCategory
    schema_version: str = Field(default="1.0")
    declared_at: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None

    @field_validator("declaration_id")
    @classmethod
    def declaration_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("declaration_id must not be blank")
        return v.strip()

    @field_validator("party_ref")
    @classmethod
    def party_ref_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("party_ref must not be blank")
        return v.strip()


class CapabilityRequirementRecord(BaseModel):
    requirement_id: str = Field(min_length=1)
    declaration_id: str = Field(min_length=1)
    capability_name: str = Field(min_length=1)
    requirement_level: RequirementLevel
    required_values: List[str] = Field(default_factory=list)
    minimum_version: Optional[str] = None
    maximum_version: Optional[str] = None
    constraint_notes: Optional[str] = None

    @field_validator("requirement_id")
    @classmethod
    def requirement_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("requirement_id must not be blank")
        return v.strip()

    @field_validator("declaration_id")
    @classmethod
    def req_declaration_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("declaration_id must not be blank")
        return v.strip()

    @field_validator("capability_name")
    @classmethod
    def capability_name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("capability_name must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def version_constraints_coherent(self) -> "CapabilityRequirementRecord":
        if self.minimum_version and self.maximum_version:
            if self.minimum_version > self.maximum_version:
                raise ValueError(f"minimum_version ({self.minimum_version}) > maximum_version ({self.maximum_version})")
        return self


class CapabilityOfferRecord(BaseModel):
    offer_id: str = Field(min_length=1)
    declaration_id: str = Field(min_length=1)
    capability_name: str = Field(min_length=1)
    supported_values: List[str] = Field(default_factory=list)
    supported_version: Optional[str] = None
    limits: List[str] = Field(default_factory=list)
    conditions: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

    @field_validator("offer_id")
    @classmethod
    def offer_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("offer_id must not be blank")
        return v.strip()

    @field_validator("declaration_id")
    @classmethod
    def off_declaration_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("declaration_id must not be blank")
        return v.strip()

    @field_validator("capability_name")
    @classmethod
    def off_capability_name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("capability_name must not be blank")
        return v.strip()


class CompatibilityEvaluationRecord(BaseModel):
    evaluation_id: str = Field(min_length=1)
    request_declaration_id: str = Field(min_length=1)
    offer_declaration_id: str = Field(min_length=1)
    compatibility_status: CompatibilityStatus
    matched_requirement_ids: List[str] = Field(default_factory=list)
    unmatched_requirement_ids: List[str] = Field(default_factory=list)
    score: float = Field(default=0.0, ge=0.0, le=100.0)
    evaluation_notes: Optional[str] = None
    evaluated_at: datetime = Field(default_factory=datetime.now)

    @field_validator("evaluation_id")
    @classmethod
    def evaluation_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("evaluation_id must not be blank")
        return v.strip()

    @field_validator("request_declaration_id")
    @classmethod
    def eval_req_decl_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("request_declaration_id must not be blank")
        return v.strip()

    @field_validator("offer_declaration_id")
    @classmethod
    def eval_off_decl_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("offer_declaration_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def compatible_requires_no_unmatched_required(self) -> "CompatibilityEvaluationRecord":
        if self.compatibility_status == CompatibilityStatus.compatible:
            if self.unmatched_requirement_ids:
                raise ValueError("compatible status but unmatched_requirement_ids present")
        return self

    @model_validator(mode="after")
    def incompatible_must_have_unmatched(self) -> "CompatibilityEvaluationRecord":
        if self.compatibility_status == CompatibilityStatus.incompatible:
            if not self.unmatched_requirement_ids:
                raise ValueError("incompatible status but no unmatched_requirement_ids")
        return self


class NegotiatedCapabilitySet(BaseModel):
    negotiated_set_id: str = Field(min_length=1)
    evaluation_id: str = Field(min_length=1)
    negotiation_mode: NegotiationMode
    negotiated_capabilities: List[str] = Field(default_factory=list)
    required_satisfied: List[str] = Field(default_factory=list)
    optional_satisfied: List[str] = Field(default_factory=list)
    session_effective_from: Optional[datetime] = None
    session_effective_until: Optional[datetime] = None

    @field_validator("negotiated_set_id")
    @classmethod
    def negotiated_set_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("negotiated_set_id must not be blank")
        return v.strip()

    @field_validator("evaluation_id")
    @classmethod
    def ns_evaluation_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("evaluation_id must not be blank")
        return v.strip()


class CompatibilityGapRecord(BaseModel):
    gap_id: str = Field(min_length=1)
    evaluation_id: str = Field(min_length=1)
    capability_name: str = Field(min_length=1)
    gap_summary: str = Field(min_length=1)
    blocking: bool = False
    fallback_options: List[str] = Field(default_factory=list)
    resolution_notes: Optional[str] = None

    @field_validator("gap_id")
    @classmethod
    def gap_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("gap_id must not be blank")
        return v.strip()

    @field_validator("evaluation_id")
    @classmethod
    def gap_evaluation_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("evaluation_id must not be blank")
        return v.strip()

    @field_validator("capability_name")
    @classmethod
    def gap_capability_name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("capability_name must not be blank")
        return v.strip()

    @field_validator("gap_summary")
    @classmethod
    def gap_summary_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("gap_summary must not be blank")
        return v.strip()


class NegotiationDecisionRecord(BaseModel):
    decision_id: str = Field(min_length=1)
    evaluation_id: str = Field(min_length=1)
    negotiated_set_id: Optional[str] = None
    negotiation_disposition: NegotiationDisposition
    decision_reason: Optional[str] = None
    selected_fallbacks: List[str] = Field(default_factory=list)
    approved_override_ref: Optional[str] = None
    decided_at: datetime = Field(default_factory=datetime.now)

    @field_validator("decision_id")
    @classmethod
    def decision_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("decision_id must not be blank")
        return v.strip()

    @field_validator("evaluation_id")
    @classmethod
    def nd_evaluation_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("evaluation_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def incompatible_proceed_requires_override(self) -> "NegotiationDecisionRecord":
        if self.negotiation_disposition == NegotiationDisposition.proceed:
            pass
        return self

    @model_validator(mode="after")
    def proceed_with_fallbacks_requires_fallbacks(self) -> "NegotiationDecisionRecord":
        if self.negotiation_disposition == NegotiationDisposition.proceed_with_fallbacks:
            if not self.selected_fallbacks:
                raise ValueError("proceed_with_fallbacks requires selected_fallbacks")
        return self

    @model_validator(mode="after")
    def reroute_or_reject_requires_reason(self) -> "NegotiationDecisionRecord":
        if self.negotiation_disposition in (NegotiationDisposition.reroute, NegotiationDisposition.reject):
            if not self.decision_reason:
                raise ValueError("reroute/reject requires decision_reason")
        return self


class CapabilityNegotiationEnvelope(BaseModel):
    envelope_id: str = Field(min_length=1)
    request_declaration: CapabilityDeclaration
    offer_declaration: CapabilityDeclaration
    evaluation: CompatibilityEvaluationRecord
    negotiated_set: Optional[NegotiatedCapabilitySet] = None
    gaps: List[CompatibilityGapRecord] = Field(default_factory=list)
    decision: Optional[NegotiationDecisionRecord] = None

    @field_validator("envelope_id")
    @classmethod
    def envelope_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("envelope_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def incompatible_no_proceed_without_override(self) -> "CapabilityNegotiationEnvelope":
        if self.evaluation.compatibility_status == CompatibilityStatus.incompatible:
            d = self.decision
            if d and d.negotiation_disposition == NegotiationDisposition.proceed:
                if not d.approved_override_ref:
                    raise ValueError("incompatible cannot proceed without approved_override_ref")
        return self

    @model_validator(mode="after")
    def proceed_with_fallbacks_needs_gaps(self) -> "CapabilityNegotiationEnvelope":
        d = self.decision
        if d and d.negotiation_disposition == NegotiationDisposition.proceed_with_fallbacks:
            if not self.gaps:
                raise ValueError("proceed_with_fallbacks decision but no gaps recorded")
        return self
