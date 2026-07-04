from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class CapabilityVerb(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    APPROVE = "approve"
    SEND = "send"
    ESCALATE = "escalate"


class ToolRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PermissionEffect(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class ExecutionEnvironment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ScopeConstraint(BaseModel):
    scope_type: str
    scope_value: str
    description: Optional[str] = None

    @field_validator("scope_type", "scope_value")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class ToolDescriptor(BaseModel):
    tool_id: str
    tool_name: str
    description: str
    risk_level: ToolRiskLevel
    supported_verbs: List[CapabilityVerb] = Field(default_factory=list)
    destructive: bool = False

    @field_validator("tool_id", "tool_name", "description")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def validate_supported_verbs(self):
        if not self.supported_verbs:
            raise ValueError("supported_verbs must not be empty for registered tools")
        return self

    @model_validator(mode="after")
    def validate_destructive_risk(self):
        if self.destructive and self.risk_level not in (ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL):
            raise ValueError("destructive tools must have risk_level HIGH or CRITICAL")
        return self


class CapabilityGrant(BaseModel):
    grant_id: str
    agent_identity: str
    tool_id: str
    allowed_verbs: List[CapabilityVerb] = Field(default_factory=list)
    scope_constraints: List[ScopeConstraint] = Field(default_factory=list)
    environments: List[ExecutionEnvironment] = Field(default_factory=list)
    approval_required: bool = False
    enabled: bool = True

    @field_validator("grant_id", "agent_identity", "tool_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def validate_environments(self):
        if not self.environments:
            raise ValueError("environments must not be empty")
        return self

    @model_validator(mode="after")
    def validate_verbs(self):
        if not self.allowed_verbs:
            raise ValueError("allowed_verbs must not be empty")
        return self

    @model_validator(mode="after")
    def validate_approval_destructive(self):
        if not self.approval_required:
            for verb in self.allowed_verbs:
                if verb in (CapabilityVerb.DELETE, CapabilityVerb.SEND):
                    raise ValueError(
                        f"DELETE/SEND verbs require approval_required=True, got approval_required=False"
                    )
        return self


class ToolPermissionRule(BaseModel):
    rule_id: str
    tool_id: str
    effect: PermissionEffect
    applies_to_agent_identity: str
    verbs: List[CapabilityVerb] = Field(default_factory=list)
    environments: List[ExecutionEnvironment] = Field(default_factory=list)
    rationale: Optional[str] = None

    @field_validator("rule_id", "tool_id", "applies_to_agent_identity")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def validate_environments(self):
        if not self.environments:
            raise ValueError("environments must not be empty")
        return self


class CapabilityMatrix(BaseModel):
    matrix_id: str
    tool_descriptors: List[ToolDescriptor] = Field(default_factory=list)
    grants: List[CapabilityGrant] = Field(default_factory=list)
    rules: List[ToolPermissionRule] = Field(default_factory=list)
    default_effect: PermissionEffect = PermissionEffect.DENY

    @field_validator("matrix_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("matrix_id must not be empty")
        return value


class ToolAccessRequest(BaseModel):
    request_id: str
    run_id: str
    step_id: str
    agent_identity: str
    tool_id: str
    requested_verb: CapabilityVerb
    environment: ExecutionEnvironment
    requested_scope: List[ScopeConstraint] = Field(default_factory=list)

    @field_validator("request_id", "run_id", "step_id", "agent_identity", "tool_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class AuthorizationDecision(BaseModel):
    decision_id: str
    request_id: str
    allowed: bool
    effect: PermissionEffect
    matched_rule_ids: List[str] = Field(default_factory=list)
    rationale: str
    approval_required: bool = False

    @field_validator("decision_id", "request_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("rationale")
    @classmethod
    def validate_rationale(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("rationale must not be empty")
        return value

    @model_validator(mode="after")
    def validate_require_approval_consistency(self):
        if self.effect == PermissionEffect.REQUIRE_APPROVAL and not self.approval_required:
            raise ValueError("effect=REQUIRE_APPROVAL requires approval_required=True")
        return self

    @model_validator(mode="after")
    def validate_matched_rules(self):
        if self.effect != PermissionEffect.DENY and not self.matched_rule_ids:
            raise ValueError("non-DENY decisions must have at least one matched_rule_ids entry")
        return self
