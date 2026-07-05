from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class TelemetrySignalType(str, Enum):
    LOG = "log"
    TRACE_EVENT = "trace_event"
    OBS_EVENT = "obs_event"
    AUDIT = "audit"


class EventKind(str, Enum):
    STATE_CHANGE = "state_change"
    ERROR = "error"
    POLICY_DECISION = "policy_decision"
    TOOL_CALL = "tool_call"
    MODEL_CALL = "model_call"
    RUN_START = "run_start"
    RUN_END = "run_end"
    CHECKPOINT = "checkpoint"
    RECOVERY = "recovery"
    CONFIG = "config"


class EventOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


SENSITIVE_KEYS = {"password", "passwd", "secret", "token", "api_token", "api_key", "access_key", "private_key"}


class CorrelationContext(BaseModel):
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    run_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    tool_call_id: Optional[str] = None
    model_call_id: Optional[str] = None
    checkpoint_id: Optional[str] = None
    failure_id: Optional[str] = None
    recovery_decision_id: Optional[str] = None


class TelemetryAttribute(BaseModel):
    key: str
    value: str
    type_hint: Optional[str] = None

    @field_validator("key")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("key must not be blank")
        return stripped


class TelemetryEventRecord(BaseModel):
    event_id: str
    signal_type: TelemetrySignalType
    event_kind: EventKind
    event_name: str
    timestamp: datetime
    level: Optional[LogLevel] = None
    outcome: EventOutcome = EventOutcome.UNKNOWN
    message: str = ""
    service_name: str = ""
    correlation: CorrelationContext = Field(default_factory=CorrelationContext)
    attributes: List[TelemetryAttribute] = Field(default_factory=list)
    sensitive: bool = False

    @field_validator("event_id", "event_name")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def level_outcome_consistency(self):
        if self.level in (LogLevel.ERROR, LogLevel.CRITICAL) and self.outcome != EventOutcome.FAILURE:
            raise ValueError("ERROR/CRITICAL level must have outcome=failure")
        if self.level == LogLevel.INFO and self.outcome == EventOutcome.FAILURE:
            raise ValueError("INFO level must not have outcome=failure")
        return self

    @model_validator(mode="after")
    def error_kind_needs_failure_id(self):
        if self.event_kind == EventKind.ERROR:
            has_failure_id = (
                self.correlation.failure_id is not None
                or any(a.key == "failure_id" for a in self.attributes)
            )
            if not has_failure_id:
                raise ValueError("EventKind.ERROR must have failure_id in correlation or attributes")
        return self

    @model_validator(mode="after")
    def sensitive_attrs_no_exposed_keys(self):
        if self.sensitive:
            for a in self.attributes:
                if a.key.lower() in SENSITIVE_KEYS:
                    raise ValueError(f"sensitive event must not expose attribute key: {a.key}")
        return self


class LogRecord(BaseModel):
    event: TelemetryEventRecord

    @model_validator(mode="after")
    def enforce_log_signal_type(self):
        if self.event.signal_type != TelemetrySignalType.LOG:
            raise ValueError("LogRecord must have signal_type=LOG")
        return self

    @model_validator(mode="after")
    def enforce_level_present(self):
        if self.event.level is None:
            raise ValueError("LogRecord must have a level set")
        return self


class TraceEventRecord(BaseModel):
    event: TelemetryEventRecord

    @model_validator(mode="after")
    def enforce_trace_signal_type(self):
        if self.event.signal_type != TelemetrySignalType.TRACE_EVENT:
            raise ValueError("TraceEventRecord must have signal_type=TRACE_EVENT")
        return self


class ObservabilityEnvelope(BaseModel):
    envelope_id: str
    event: TelemetryEventRecord

    @field_validator("envelope_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("envelope_id must not be blank")
        return stripped
