from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class ToolActionType(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    EXPORT = "export"
    SEND = "send"
    DELEGATE = "delegate"


class ToolRiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalRequirement(str, Enum):
    NONE = "none"
    OPTIONAL = "optional"
    REQUIRED = "required"


class NetworkAccessLevel(str, Enum):
    NONE = "none"
    RESTRICTED = "restricted"
    FULL = "full"


class FilesystemAccessLevel(str, Enum):
    NONE = "none"
    SANDBOX_ONLY = "sandbox_only"
    SCOPED_PATHS = "scoped_paths"


class CredentialMode(str, Enum):
    NONE = "none"
    SCOPED_EPHEMERAL = "scoped_ephemeral"
    PREBOUND_REFERENCE = "prebound_reference"


class ToolDescriptor(BaseModel):
    tool_id: str
    tool_name: str
    version: Optional[str] = None
    description: Optional[str] = None
    supported_actions: List[ToolActionType] = Field(default_factory=list)
    risk_level: ToolRiskLevel

    @model_validator(mode="after")
    def check_non_empty(self):
        if not self.tool_id.strip():
            raise ValueError("tool_id must be non-empty")
        if not self.tool_name.strip():
            raise ValueError("tool_name must be non-empty")
        return self


class ExecutionConstraint(BaseModel):
    timeout_seconds: int
    max_calls_per_run: Optional[int] = None
    network_access: NetworkAccessLevel = NetworkAccessLevel.NONE
    filesystem_access: FilesystemAccessLevel = FilesystemAccessLevel.NONE
    allowed_paths: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_timeout_positive(self):
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        return self

    @model_validator(mode="after")
    def check_paths_require_scoped(self):
        if self.allowed_paths and self.filesystem_access != FilesystemAccessLevel.SCOPED_PATHS:
            raise ValueError("allowed_paths requires filesystem_access to be scoped_paths")
        return self


class CapabilityGrant(BaseModel):
    grant_id: str
    agent_id: str
    tool_id: str
    allowed_actions: List[ToolActionType] = Field(default_factory=list)
    approval_requirement: ApprovalRequirement = ApprovalRequirement.NONE
    credential_mode: CredentialMode = CredentialMode.NONE
    resource_scopes: List[str] = Field(default_factory=list)
    execution_constraint: ExecutionConstraint

    @model_validator(mode="after")
    def check_non_empty(self):
        if not self.grant_id.strip():
            raise ValueError("grant_id must be non-empty")
        if not self.agent_id.strip():
            raise ValueError("agent_id must be non-empty")
        if not self.tool_id.strip():
            raise ValueError("tool_id must be non-empty")
        return self


class ToolInvocationRequest(BaseModel):
    request_id: str
    run_id: str
    agent_id: str
    tool_id: str
    action: ToolActionType
    resource_target: Optional[str] = None
    tenant_id: Optional[str] = None
    justification: str

    @model_validator(mode="after")
    def check_non_empty(self):
        if not self.request_id.strip():
            raise ValueError("request_id must be non-empty")
        if not self.run_id.strip():
            raise ValueError("run_id must be non-empty")
        if not self.agent_id.strip():
            raise ValueError("agent_id must be non-empty")
        if not self.tool_id.strip():
            raise ValueError("tool_id must be non-empty")
        if not self.justification.strip():
            raise ValueError("justification must be non-empty")
        return self


class PermissionDecision(BaseModel):
    decision_id: str
    request_id: str
    allowed: bool
    reason: str
    matched_grant_id: Optional[str] = None
    approval_required: bool = False

    @model_validator(mode="after")
    def check_non_empty(self):
        if not self.decision_id.strip():
            raise ValueError("decision_id must be non-empty")
        if not self.request_id.strip():
            raise ValueError("request_id must be non-empty")
        if not self.reason.strip():
            raise ValueError("reason must be non-empty")
        return self
