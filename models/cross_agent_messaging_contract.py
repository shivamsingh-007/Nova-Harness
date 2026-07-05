from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class MessageIntentType(str, Enum):
    REQUEST_ACTION = "request_action"
    INFORM = "inform"
    HANDOFF = "handoff"
    RETURN_RESULT = "return_result"
    REQUEST_REVIEW = "request_review"
    REQUEST_VERIFICATION = "request_verification"
    ASK_CLARIFICATION = "ask_clarification"
    SIGNAL_BLOCKER = "signal_blocker"
    EMIT_EVENT = "emit_event"
    CANCEL = "cancel"


class MessageTransportMode(str, Enum):
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    FIRE_AND_FORGET = "fire_and_forget"


class MessageDeliveryStatus(str, Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    PROCESSED = "processed"
    FAILED = "failed"
    EXPIRED = "expired"
    REJECTED = "rejected"


ACKNOWLEDGED_STATUSES = {MessageDeliveryStatus.ACKNOWLEDGED}
FAILED_STATUSES = {MessageDeliveryStatus.FAILED, MessageDeliveryStatus.REJECTED}


class MessagePriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class AudienceType(str, Enum):
    SINGLE_AGENT = "single_agent"
    ROLE_GROUP = "role_group"
    SUPERVISOR_ONLY = "supervisor_only"
    GRAPH_NODE = "graph_node"
    BROADCAST_LIMITED = "broadcast_limited"


class AgentMessageHeader(BaseModel):
    message_id: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    intent_type: MessageIntentType
    transport_mode: MessageTransportMode = MessageTransportMode.ASYNCHRONOUS
    priority: MessagePriority = MessagePriority.NORMAL
    sender_agent_id: str = Field(min_length=1)
    sender_role_id: Optional[str] = None
    trace_id: Optional[str] = None
    run_id: Optional[str] = None
    step_id: Optional[str] = None
    graph_id: Optional[str] = None
    handoff_id: Optional[str] = None
    delegation_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    @field_validator("message_id")
    @classmethod
    def message_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message_id must not be blank")
        return v.strip()

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("schema_version must not be blank")
        return v.strip()

    @field_validator("sender_agent_id")
    @classmethod
    def sender_agent_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("sender_agent_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def expires_after_created(self) -> "AgentMessageHeader":
        if self.expires_at is not None and self.created_at is not None:
            if self.expires_at <= self.created_at:
                raise ValueError("expires_at must be later than created_at")
        return self


class MessageAudience(BaseModel):
    audience_id: str = Field(min_length=1)
    audience_type: AudienceType
    target_agent_ids: List[str] = Field(default_factory=list)
    target_role_ids: List[str] = Field(default_factory=list)
    target_node_ids: List[str] = Field(default_factory=list)
    explicit_audience_note: Optional[str] = None

    @field_validator("audience_id")
    @classmethod
    def audience_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("audience_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def audience_must_be_specified(self) -> "MessageAudience":
        if (not self.target_agent_ids and not self.target_role_ids
                and not self.target_node_ids):
            raise ValueError("audience must specify at least one target")
        return self

    @model_validator(mode="after")
    def broadcast_limited_must_be_bounded(self) -> "MessageAudience":
        if self.audience_type == AudienceType.BROADCAST_LIMITED:
            n_targets = (len(self.target_agent_ids) + len(self.target_role_ids)
                         + len(self.target_node_ids))
            if n_targets == 0:
                raise ValueError("broadcast_limited must resolve to a bounded audience")
        return self


class MessagePayload(BaseModel):
    payload_id: str = Field(min_length=1)
    summary: Optional[str] = None
    data_refs: List[str] = Field(default_factory=list)
    artifact_refs: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    instruction_refs: List[str] = Field(default_factory=list)
    question_list: List[str] = Field(default_factory=list)
    requested_actions: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    expected_response_type: Optional[str] = None

    @field_validator("payload_id")
    @classmethod
    def payload_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("payload_id must not be blank")
        return v.strip()


class MessageDeliveryPolicy(BaseModel):
    delivery_policy_id: str = Field(min_length=1)
    requires_ack: bool = False
    timeout_ms: Optional[int] = Field(default=None, ge=0)
    max_retries: int = Field(default=0, ge=0)
    retry_backoff_policy: Optional[str] = None
    expiry_behavior: Optional[str] = None
    idempotency_key: Optional[str] = None

    @field_validator("delivery_policy_id")
    @classmethod
    def policy_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("delivery_policy_id must not be blank")
        return v.strip()


class MessageAcknowledgement(BaseModel):
    ack_id: str = Field(min_length=1)
    message_id: str = Field(min_length=1)
    receiver_agent_id: str = Field(min_length=1)
    delivery_status: MessageDeliveryStatus
    received_at: datetime = Field(default_factory=datetime.now)
    processing_note: Optional[str] = None

    @field_validator("ack_id")
    @classmethod
    def ack_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("ack_id must not be blank")
        return v.strip()

    @field_validator("message_id")
    @classmethod
    def message_id_in_ack_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message_id in ack must not be blank")
        return v.strip()

    @field_validator("receiver_agent_id")
    @classmethod
    def receiver_agent_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("receiver_agent_id must not be blank")
        return v.strip()


class MessageFailureRecord(BaseModel):
    failure_id: str = Field(min_length=1)
    message_id: str = Field(min_length=1)
    failure_stage: str = Field(min_length=1)
    failure_reason: str = Field(min_length=1)
    retryable: bool = False
    rejected_by: Optional[str] = None
    diagnostic_refs: List[str] = Field(default_factory=list)
    failed_at: datetime = Field(default_factory=datetime.now)

    @field_validator("failure_id")
    @classmethod
    def failure_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("failure_id must not be blank")
        return v.strip()

    @field_validator("message_id")
    @classmethod
    def message_id_in_failure_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message_id in failure must not be blank")
        return v.strip()

    @field_validator("failure_stage")
    @classmethod
    def failure_stage_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("failure_stage must not be blank")
        return v.strip()

    @field_validator("failure_reason")
    @classmethod
    def failure_reason_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("failure_reason must not be blank")
        return v.strip()


class CrossAgentMessage(BaseModel):
    header: AgentMessageHeader
    audience: MessageAudience
    payload: MessagePayload
    delivery_policy: MessageDeliveryPolicy = MessageDeliveryPolicy(
        delivery_policy_id="default")
    acknowledgement: Optional[MessageAcknowledgement] = None
    failure_record: Optional[MessageFailureRecord] = None

    @model_validator(mode="after")
    def fire_and_forget_no_ack(self) -> "CrossAgentMessage":
        if (self.header.transport_mode == MessageTransportMode.FIRE_AND_FORGET
                and self.delivery_policy.requires_ack):
            raise ValueError("fire_and_forget must not require acknowledgement")
        return self

    @model_validator(mode="after")
    def ack_status_requires_ack_record(self) -> "CrossAgentMessage":
        dp = self.delivery_policy
        ack = self.acknowledgement
        if dp.requires_ack and ack is None:
            if self.header.transport_mode != MessageTransportMode.FIRE_AND_FORGET:
                pass
        return self

    @model_validator(mode="after")
    def acknowledged_status_needs_record(self) -> "CrossAgentMessage":
        ack = self.acknowledgement
        if ack and ack.delivery_status in ACKNOWLEDGED_STATUSES:
            return self
        return self

    @model_validator(mode="after")
    def failed_status_needs_record(self) -> "CrossAgentMessage":
        fr = self.failure_record
        if fr is not None:
            return self
        return self

    @model_validator(mode="after")
    def retryable_async_should_have_idempotency(self) -> "CrossAgentMessage":
        dp = self.delivery_policy
        h = self.header
        if (dp.max_retries > 0
                and h.transport_mode == MessageTransportMode.ASYNCHRONOUS
                and not dp.idempotency_key):
            pass
        return self


class CrossAgentMessageEnvelope(BaseModel):
    envelope_id: str = Field(min_length=1)
    message: CrossAgentMessage

    @field_validator("envelope_id")
    @classmethod
    def envelope_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("envelope_id must not be blank")
        return v.strip()
