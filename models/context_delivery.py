from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ContentType(str, Enum):
    FILE_SNIPPET = "file_snippet"
    ERROR_LOG = "error_log"
    TEST_FAILURE = "test_failure"
    DOC_SNIPPET = "doc_snippet"
    REPO_MAP = "repo_map"
    COMMAND_HINT = "command_hint"


class DeliveryItem(BaseModel):
    item_id: str
    content_type: ContentType
    source_path: Optional[str] = None
    title: str
    reason: str
    content: str
    priority: int = 1

    @field_validator("title", "reason", "content")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("priority")
    @classmethod
    def bounded_priority(cls, value: int) -> int:
        if value < 1 or value > 5:
            raise ValueError("priority must be between 1 and 5")
        return value


class RepoSnapshot(BaseModel):
    repo_root: str
    top_level_paths: List[str] = Field(default_factory=list)
    primary_language: Optional[str] = None
    build_system: Optional[str] = None
    test_command: Optional[str] = None
    lint_command: Optional[str] = None

    @field_validator("repo_root")
    @classmethod
    def non_empty_root(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("repo_root must not be empty")
        return value


class VerificationHints(BaseModel):
    recommended_commands: List[str] = Field(default_factory=list)
    success_signals: List[str] = Field(default_factory=list)


class ContextDeliveryBundle(BaseModel):
    task_id: str
    task_brief: str
    repo_snapshot: RepoSnapshot
    selected_files: List[DeliveryItem] = Field(default_factory=list)
    selected_failures: List[DeliveryItem] = Field(default_factory=list)
    selected_docs: List[DeliveryItem] = Field(default_factory=list)
    verification_hints: VerificationHints = Field(default_factory=VerificationHints)

    @field_validator("task_id", "task_brief")
    @classmethod
    def required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value
