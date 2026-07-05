from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class AuditEventType(str, Enum):
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    TOOL_REQUESTED = "tool_requested"
    TOOL_COMPLETED = "tool_completed"
    MODEL_CALLED = "model_called"
    CHECKPOINT_CREATED = "checkpoint_created"
    CHECKPOINT_RESTORED = "checkpoint_restored"
    POLICY_DECIDED = "policy_decided"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    FAILURE_RECORDED = "failure_recorded"
    SESSION_RESUMED = "session_resumed"
    SESSION_TERMINATED = "session_terminated"


class AuditSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventDirection(str, Enum):
    INBOUND = "inbound"
    INTERNAL = "internal"
    OUTBOUND = "outbound"


class EventActorType(str, Enum):
    AGENT = "agent"
    HUMAN = "human"
    SYSTEM = "system"
    TOOL = "tool"
    POLICY_ENGINE = "policy_engine"


class EventLinkType(str, Enum):
    CAUSES = "causes"
    FOLLOWS = "follows"
    RESOLVES = "resolves"
    REPLACES = "replaces"
    REFERENCES = "references"


class AuditEventRef(BaseModel):
    ref_id: str
    ref_type: str
    ref_uri: Optional[str] = None

    @field_validator("ref_id", "ref_type")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class EventEvidenceRef(BaseModel):
    evidence_id: str
    evidence_type: str
    evidence_uri: Optional[str] = None
    evidence_hash: Optional[str] = None

    @field_validator("evidence_id", "evidence_type")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class AuditMetadata(BaseModel):
    event_id: str
    run_id: str
    task_id: Optional[str] = None
    trace_id: Optional[str] = None
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    timestamp: str
    severity: AuditSeverity = AuditSeverity.INFO
    direction: EventDirection = EventDirection.INTERNAL
    actor_type: EventActorType = EventActorType.SYSTEM
    actor_ref: Optional[AuditEventRef] = None
    parent_event_id: Optional[str] = None

    @field_validator("event_id", "run_id", "timestamp")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def parent_event_id_not_self(self):
        if self.parent_event_id is not None and self.parent_event_id == self.event_id:
            raise ValueError("parent_event_id must not equal event_id")
        return self


class AuditEventRecord(BaseModel):
    audit_type: AuditEventType
    metadata: AuditMetadata
    summary: str
    event_refs: List[AuditEventRef] = Field(default_factory=list)
    evidence_refs: List[EventEvidenceRef] = Field(default_factory=list)
    link_type: Optional[EventLinkType] = None
    redacted: bool = False
    superseded_by: Optional[str] = None

    @field_validator("summary")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("summary must not be blank")
        return stripped

    @model_validator(mode="after")
    def superseded_by_not_self(self):
        if self.superseded_by is not None and self.superseded_by == self.metadata.event_id:
            raise ValueError("superseded_by must not point to the same event")
        return self

    @model_validator(mode="after")
    def redacted_preserves_metadata(self):
        if self.redacted:
            if not self.metadata.event_id or not self.metadata.run_id or not self.metadata.timestamp:
                raise ValueError("redacted event must preserve event_id, run_id, and timestamp")
        return self


class AuditTrailEnvelope(BaseModel):
    envelope_id: str
    events: List[AuditEventRecord] = Field(default_factory=list)

    @field_validator("envelope_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def event_ids_unique(self):
        ids = [e.metadata.event_id for e in self.events]
        if len(ids) != len(set(ids)):
            raise ValueError("event_ids must be unique within the envelope")
        return self
