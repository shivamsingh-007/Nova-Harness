from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class MemoryType(str, Enum):
    SESSION = "session"
    WORKING = "working"
    LONG_TERM = "long_term"


class MemoryScopeType(str, Enum):
    RUN = "run"
    SESSION = "session"
    USER = "user"
    PROJECT = "project"
    WORKSPACE = "workspace"
    TENANT = "tenant"
    SYSTEM = "system"


class SensitivityLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    RESTRICTED = "restricted"


class RetentionClass(str, Enum):
    EPHEMERAL = "ephemeral"
    SHORT_LIVED = "short_lived"
    STANDARD = "standard"
    EXTENDED = "extended"
    LEGAL_HOLD = "legal_hold"


class MemoryLifecycleStatus(str, Enum):
    ACTIVE = "active"
    INVALIDATED = "invalidated"
    SUPPRESSED = "suppressed"
    TOMBSTONED = "tombstoned"
    EXPIRED = "expired"
    QUARANTINED = "quarantined"


class MemoryPurpose(str, Enum):
    TASK_CONTINUITY = "task_continuity"
    USER_PREFERENCE = "user_preference"
    PROJECT_CONTEXT = "project_context"
    SAFETY_SIGNAL = "safety_signal"
    OPERATIONAL_STATE = "operational_state"


class ExecutionContext(BaseModel):
    run_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    workspace_id: Optional[str] = None
    tenant_id: Optional[str] = None
    actor_role: Optional[str] = None


class MemoryScope(BaseModel):
    scope_type: MemoryScopeType
    scope_id: str

    @field_validator("scope_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class RetentionPolicy(BaseModel):
    retention_class: RetentionClass
    ttl_seconds: Optional[int] = None
    expires_at: Optional[str] = None
    allow_user_delete: bool = True
    allow_admin_delete: bool = True

    @field_validator("ttl_seconds")
    @classmethod
    def validate_positive_ttl(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value <= 0:
            raise ValueError("ttl_seconds must be positive if provided")
        return value

    @model_validator(mode="after")
    def validate_retention_for_session_working(self):
        if self.retention_class in (RetentionClass.EPHEMERAL, RetentionClass.SHORT_LIVED):
            pass
        return self


class MemoryRecord(BaseModel):
    memory_id: str
    memory_type: MemoryType
    purpose: MemoryPurpose
    scope: MemoryScope
    sensitivity: SensitivityLevel
    lifecycle_status: MemoryLifecycleStatus
    content_ref: str
    provenance_ref: Optional[str] = None
    retention_policy: RetentionPolicy

    @field_validator("memory_id", "content_ref")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def validate_session_working_not_long_retention(self):
        if self.memory_type in (MemoryType.SESSION, MemoryType.WORKING):
            if self.retention_policy.retention_class in (
                RetentionClass.EXTENDED, RetentionClass.LEGAL_HOLD,
            ):
                raise ValueError("SESSION or WORKING memory must not use EXTENDED or LEGAL_HOLD retention")
        return self

    @model_validator(mode="after")
    def validate_long_term_requires_longer_retention(self):
        if self.memory_type == MemoryType.LONG_TERM:
            if self.retention_policy.retention_class in (
                RetentionClass.EPHEMERAL, RetentionClass.SHORT_LIVED,
            ):
                raise ValueError("LONG_TERM memory must not use EPHEMERAL or SHORT_LIVED retention")
        return self

    @model_validator(mode="after")
    def validate_non_active_not_retrievable(self):
        if self.lifecycle_status in (
            MemoryLifecycleStatus.INVALIDATED,
            MemoryLifecycleStatus.SUPPRESSED,
            MemoryLifecycleStatus.TOMBSTONED,
            MemoryLifecycleStatus.EXPIRED,
            MemoryLifecycleStatus.QUARANTINED,
        ):
            pass
        return self

    @model_validator(mode="after")
    def validate_purpose_for_long_term(self):
        if self.memory_type == MemoryType.LONG_TERM:
            pass
        return self


class MemoryAccessDecision(BaseModel):
    decision_id: str
    memory_id: str
    allowed: bool
    reason: str
    execution_context: ExecutionContext

    @field_validator("decision_id", "memory_id", "reason")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value
