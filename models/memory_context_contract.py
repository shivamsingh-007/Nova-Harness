from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class MemoryScope(str, Enum):
    SESSION = "session"
    TASK = "task"
    PROJECT = "project"
    USER = "user"
    SYSTEM = "system"


class MemoryStatus(str, Enum):
    ACTIVE = "active"
    STALE = "stale"
    ARCHIVED = "archived"
    DELETED = "deleted"


class RetrievalSourceType(str, Enum):
    VECTOR_SEARCH = "vector_search"
    KEYWORD_SEARCH = "keyword_search"
    MANUAL_IMPORT = "manual_import"
    TOOL_OUTPUT = "tool_output"
    USER_PROVIDED = "user_provided"


class ContextTrustLevel(str, Enum):
    TRUSTED = "trusted"
    INTERNAL_UNVERIFIED = "internal_unverified"
    EXTERNAL_UNTRUSTED = "external_untrusted"


class MemoryItemRef(BaseModel):
    memory_id: str
    scope: MemoryScope
    status: MemoryStatus
    source_type: RetrievalSourceType
    source_ref: str
    summary: str
    trust_level: ContextTrustLevel
    confidence: Optional[float] = None

    @field_validator("memory_id", "source_ref", "summary")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("confidence")
    @classmethod
    def confidence_in_range(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("confidence must be between 0 and 1")
        return v


class RetrievalHitRef(BaseModel):
    hit_id: str
    memory_id: str
    rank: int
    score: Optional[float] = None
    matched_query: Optional[str] = None

    @field_validator("hit_id", "memory_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("rank")
    @classmethod
    def positive_rank(cls, v: int) -> int:
        if v < 1:
            raise ValueError("rank must be positive")
        return v

    @field_validator("score")
    @classmethod
    def score_in_range(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("score must be between 0 and 1")
        return v


class ContextSnapshotBlock(BaseModel):
    block_id: str
    block_type: str
    content_ref: str
    trust_level: ContextTrustLevel
    origin_ref: Optional[str] = None

    @field_validator("block_id", "block_type", "content_ref")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class MemoryRetentionPolicy(BaseModel):
    retention_policy_id: str
    keep_until: Optional[str] = None
    expire_after_days: Optional[int] = None
    promote_to_project_memory: bool = False
    summarize_before_store: bool = True

    @field_validator("retention_policy_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("expire_after_days")
    @classmethod
    def non_negative_expiry(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("expire_after_days must be non-negative")
        return v


class RetrievalSnapshot(BaseModel):
    snapshot_id: str
    run_id: str
    task_id: Optional[str] = None
    trace_id: Optional[str] = None
    query: str
    hits: List[RetrievalHitRef] = Field(default_factory=list)
    memory_items: List[MemoryItemRef] = Field(default_factory=list)

    @field_validator("snapshot_id", "run_id", "query")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def hits_hit_ids_ordered(self):
        ids = [h.hit_id for h in self.hits]
        if len(ids) != len(set(ids)):
            raise ValueError("hit_ids must be unique within the snapshot")
        return self

    @model_validator(mode="after")
    def memory_item_ids_unique(self):
        ids = [m.memory_id for m in self.memory_items]
        if len(ids) != len(set(ids)):
            raise ValueError("memory_ids must be unique within the snapshot")
        return self


class ContextStateEnvelope(BaseModel):
    envelope_id: str
    session_id: str
    agent_id: str
    snapshot: RetrievalSnapshot
    context_blocks: List[ContextSnapshotBlock] = Field(default_factory=list)
    retention_policy: Optional[MemoryRetentionPolicy] = None

    @field_validator("envelope_id", "session_id", "agent_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def context_block_ids_unique(self):
        ids = [b.block_id for b in self.context_blocks]
        if len(ids) != len(set(ids)):
            raise ValueError("context_block_ids must be unique within the envelope")
        return self
