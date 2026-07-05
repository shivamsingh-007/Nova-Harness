from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class ArtifactType(str, Enum):
    FILE = "file"
    IMAGE = "image"
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    CODE = "code"
    LOG = "log"
    ARCHIVE = "archive"
    OTHER = "other"


class ArtifactStatus(str, Enum):
    CREATED = "created"
    READY = "ready"
    MODIFIED = "modified"
    STALE = "stale"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ArtifactOriginType(str, Enum):
    USER_INPUT = "user_input"
    MODEL_GENERATED = "model_generated"
    TOOL_GENERATED = "tool_generated"
    DERIVED = "derived"
    IMPORTED = "imported"


class ArtifactVisibility(str, Enum):
    PRIVATE = "private"
    TEAM = "team"
    SHARED = "shared"
    PUBLIC = "public"


class ArtifactRef(BaseModel):
    artifact_id: str
    artifact_type: ArtifactType
    name: str
    uri: str
    mime_type: Optional[str] = None
    status: ArtifactStatus = ArtifactStatus.CREATED
    visibility: ArtifactVisibility = ArtifactVisibility.PRIVATE

    @field_validator("artifact_id", "name", "uri")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class ArtifactProvenance(BaseModel):
    provenance_id: str
    origin_type: ArtifactOriginType
    source_ref: Optional[str] = None
    created_by_run_id: Optional[str] = None
    created_by_task_id: Optional[str] = None
    created_by_tool_call_id: Optional[str] = None
    created_by_model_call_id: Optional[str] = None
    content_hash: Optional[str] = None
    parent_artifact_ids: List[str] = Field(default_factory=list)

    @field_validator("provenance_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("content_hash")
    @classmethod
    def hash_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("content_hash must not be empty")
        return v

    @field_validator("parent_artifact_ids")
    @classmethod
    def no_blank_parent_ids(cls, v: List[str]) -> List[str]:
        cleaned = [i.strip() for i in v]
        if any(not i for i in cleaned):
            raise ValueError("parent_artifact_ids must not contain blank entries")
        return cleaned


class ArtifactLifecycle(BaseModel):
    lifecycle_id: str
    retained: bool = True
    retain_until: Optional[str] = None
    archived_at: Optional[str] = None
    deleted_at: Optional[str] = None

    @field_validator("lifecycle_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class GeneratedOutputRecord(BaseModel):
    output_id: str
    artifact: ArtifactRef
    provenance: ArtifactProvenance
    lifecycle: ArtifactLifecycle
    summary: Optional[str] = None
    is_exportable: bool = True
    is_reproducible: bool = False

    @field_validator("output_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def archived_status_has_archived_at(self):
        if self.artifact.status == ArtifactStatus.ARCHIVED and not self.lifecycle.archived_at:
            raise ValueError("ARCHIVED status requires lifecycle.archived_at")
        return self

    @model_validator(mode="after")
    def deleted_status_has_deleted_at(self):
        if self.artifact.status == ArtifactStatus.DELETED and not self.lifecycle.deleted_at:
            raise ValueError("DELETED status requires lifecycle.deleted_at")
        return self


class ArtifactEnvelope(BaseModel):
    envelope_id: str
    run_id: str
    task_id: Optional[str] = None
    trace_id: Optional[str] = None
    outputs: List[GeneratedOutputRecord] = Field(default_factory=list)

    @field_validator("envelope_id", "run_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def output_ids_unique(self):
        ids = [o.output_id for o in self.outputs]
        if len(ids) != len(set(ids)):
            raise ValueError("output_ids must be unique within the envelope")
        return self
