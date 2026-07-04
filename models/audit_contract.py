from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class AuditEventType(str, Enum):
    RUN_STARTED = "run_started"
    RUN_COMPLETED = "run_completed"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    TOOL_REQUESTED = "tool_requested"
    TOOL_EXECUTED = "tool_executed"
    MODEL_CALLED = "model_called"
    GUARDRAIL_EVALUATED = "guardrail_evaluated"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_DECIDED = "approval_decided"
    QUALITY_GATE_DECIDED = "quality_gate_decided"
    ERROR_RECORDED = "error_recorded"
    CHECKPOINT_CREATED = "checkpoint_created"


class ActorType(str, Enum):
    USER = "user"
    AGENT = "agent"
    REVIEWER = "reviewer"
    SYSTEM = "system"
    SERVICE = "service"


class ResourceType(str, Enum):
    RUN = "run"
    STEP = "step"
    TOOL = "tool"
    MODEL = "model"
    POLICY = "policy"
    APPROVAL = "approval"
    CHECKPOINT = "checkpoint"
    OUTPUT = "output"
    DATA_OBJECT = "data_object"


class TraceContext(BaseModel):
    trace_id: str
    run_id: str
    session_id: Optional[str] = None
    step_id: Optional[str] = None
    parent_event_id: Optional[str] = None
    environment: str

    @field_validator("trace_id", "run_id", "environment")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def validate_parent_not_self(self):
        if self.parent_event_id is not None and self.parent_event_id == self.trace_id:
            raise ValueError("parent_event_id must not equal trace_id")
        return self


class ActorRef(BaseModel):
    actor_id: str
    actor_type: ActorType
    role: Optional[str] = None

    @field_validator("actor_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class ResourceRef(BaseModel):
    resource_id: str
    resource_type: ResourceType
    label: Optional[str] = None

    @field_validator("resource_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class EvidenceRef(BaseModel):
    evidence_id: str
    source_type: str
    source_ref: str
    digest: Optional[str] = None

    @field_validator("evidence_id", "source_type", "source_ref")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("digest")
    @classmethod
    def validate_digest_if_provided(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("digest must be non-empty if provided")
        return value


class ProvenanceLink(BaseModel):
    link_id: str
    from_event_id: str
    to_event_id: str
    relationship_type: str

    @field_validator("link_id", "from_event_id", "to_event_id", "relationship_type")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def validate_no_self_link(self):
        if self.from_event_id == self.to_event_id:
            raise ValueError("from_event_id must not equal to_event_id")
        return self


class DecisionLineage(BaseModel):
    lineage_id: str
    input_refs: List[ResourceRef] = Field(default_factory=list)
    evidence_refs: List[EvidenceRef] = Field(default_factory=list)
    policy_refs: List[ResourceRef] = Field(default_factory=list)
    output_refs: List[ResourceRef] = Field(default_factory=list)

    @field_validator("lineage_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def validate_at_least_one_ref(self):
        if not self.input_refs and not self.evidence_refs and not self.policy_refs and not self.output_refs:
            raise ValueError("decision lineage must have at least one reference")
        return self


class AuditEvent(BaseModel):
    event_id: str
    event_type: AuditEventType
    occurred_at: str
    trace_context: TraceContext
    actor: ActorRef
    target_resource: ResourceRef
    action_summary: str
    outcome: str
    decision_lineage: Optional[DecisionLineage] = None

    @field_validator("event_id", "occurred_at", "action_summary", "outcome")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class AuditEnvelope(BaseModel):
    envelope_id: str
    event: AuditEvent
    provenance_links: List[ProvenanceLink] = Field(default_factory=list)
    integrity_hash: Optional[str] = None

    @field_validator("envelope_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("integrity_hash")
    @classmethod
    def validate_hash_if_provided(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("integrity_hash must be non-empty if provided")
        return value
