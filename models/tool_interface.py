from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class ExecutionMode(str, Enum):
    READ_ONLY = "read_only"
    MUTATING = "mutating"
    EXECUTION = "execution"


class ApprovalState(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ToolStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    BLOCKED = "blocked"


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None
    requires_approval: bool = False
    execution_mode: ExecutionMode
    tags: List[str] = Field(default_factory=list)
    enabled: bool = True

    @field_validator("name", "description")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("input_schema")
    @classmethod
    def input_schema_must_be_nonempty(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        if not value:
            raise ValueError("input_schema must not be empty")
        return value


class ToolInvocation(BaseModel):
    invocation_id: str
    tool_name: str
    arguments: Dict[str, Any]
    requested_by_task_id: str
    requested_by_agent: str
    approval_state: ApprovalState = ApprovalState.NOT_REQUIRED

    @field_validator("invocation_id", "tool_name", "requested_by_task_id", "requested_by_agent")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def check_approval_state_policy(self):
        if self.approval_state == ApprovalState.APPROVED:
            raise ValueError("invocation cannot start as already approved; set PENDING and approve later")
        return self


class ToolResult(BaseModel):
    invocation_id: str
    tool_name: str
    status: ToolStatus
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    artifacts: List[str] = Field(default_factory=list)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    @field_validator("invocation_id", "tool_name")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def check_result_consistency(self):
        if self.status == ToolStatus.SUCCESS:
            if not self.output and not self.artifacts:
                raise ValueError("successful result must have output or artifacts")
        if self.status == ToolStatus.ERROR:
            if not self.error:
                raise ValueError("error status must include an error message")
        if self.status == ToolStatus.BLOCKED:
            if not self.error:
                raise ValueError("blocked status must include an error message")
        return self
