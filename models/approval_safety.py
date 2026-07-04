from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SafetyAction(str, Enum):
    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    BLOCK = "block"


class ResourceType(str, Enum):
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    SECRET = "secret"
    PROCESS = "process"
    EXTERNAL_SIDE_EFFECT = "external_side_effect"


class ApprovalRequirement(BaseModel):
    require_human: bool = False
    approver_role: Optional[str] = None
    reason_required: bool = True
    expires_in_seconds: Optional[int] = None

    @field_validator("expires_in_seconds")
    @classmethod
    def positive_expiration(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value <= 0:
            raise ValueError("expires_in_seconds must be positive")
        return value


class ActionRiskRule(BaseModel):
    rule_id: str
    action_name: str
    resource_type: ResourceType
    risk_level: RiskLevel
    safety_action: SafetyAction
    rationale: str
    allowed_path_prefixes: List[str] = Field(default_factory=list)
    allowed_hosts: List[str] = Field(default_factory=list)
    allowed_secret_names: List[str] = Field(default_factory=list)
    approval_requirement: Optional[ApprovalRequirement] = None

    @field_validator("rule_id", "action_name", "rationale")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def approval_requirement_required_when_require_approval(self):
        if self.safety_action == SafetyAction.REQUIRE_APPROVAL and not self.approval_requirement:
            raise ValueError("approval_requirement is required when safety_action is REQUIRE_APPROVAL")
        return self

    @model_validator(mode="after")
    def network_scope_with_allowlist(self):
        if self.resource_type == ResourceType.NETWORK and self.safety_action == SafetyAction.ALLOW:
            if not self.allowed_hosts:
                raise ValueError("network ALLOW rules must specify allowed_hosts")
        return self

    @model_validator(mode="after")
    def secret_scope_with_allowlist(self):
        if self.resource_type == ResourceType.SECRET:
            if not self.allowed_secret_names:
                raise ValueError("secret access rules must specify allowed_secret_names")
        return self


class ApprovalRequest(BaseModel):
    request_id: str
    run_id: str
    action_name: str
    risk_level: RiskLevel
    reason: str
    requested_by_agent: str
    requested_arguments_summary: str
    expires_at: Optional[str] = None

    @field_validator("request_id", "run_id", "action_name", "reason", "requested_by_agent",
                     "requested_arguments_summary")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class SafetyDecision(BaseModel):
    decision_id: str
    run_id: str
    action_name: str
    risk_level: RiskLevel
    safety_action: SafetyAction
    approved: Optional[bool] = None
    approver_id: Optional[str] = None
    decision_reason: str

    @field_validator("decision_id", "run_id", "action_name", "decision_reason")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def approver_id_when_approved(self):
        if self.approved is True and not self.approver_id:
            raise ValueError("approver_id is required when approved is True")
        return self

    @model_validator(mode="after")
    def block_does_not_override(self):
        if self.safety_action == SafetyAction.BLOCK and self.approved is True:
            raise ValueError("cannot override BLOCK safety action with approved=True")
        return self


class ApprovalSafetyPolicy(BaseModel):
    policy_id: str
    rules: List[ActionRiskRule] = Field(default_factory=list)

    @field_validator("policy_id")
    @classmethod
    def non_empty_policy_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("policy_id must not be empty")
        return value

    @model_validator(mode="after")
    def unique_rule_ids(self):
        seen = set()
        for rule in self.rules:
            if rule.rule_id in seen:
                raise ValueError(f"duplicate rule_id: {rule.rule_id}")
            seen.add(rule.rule_id)
        return self


def v1_default_safety_policy() -> ApprovalSafetyPolicy:
    return ApprovalSafetyPolicy(
        policy_id="approval-safety-v1",
        rules=[
            ActionRiskRule(
                rule_id="read-workspace-files",
                action_name="read_file",
                resource_type=ResourceType.FILESYSTEM,
                risk_level=RiskLevel.LOW,
                safety_action=SafetyAction.ALLOW,
                rationale="Reading workspace files is safe and scoped to project directory.",
                allowed_path_prefixes=["/workspace"],
            ),
            ActionRiskRule(
                rule_id="search-list-files",
                action_name="search_files",
                resource_type=ResourceType.FILESYSTEM,
                risk_level=RiskLevel.LOW,
                safety_action=SafetyAction.ALLOW,
                rationale="Searching and listing files is read-only and low risk.",
                allowed_path_prefixes=["/workspace"],
            ),
            ActionRiskRule(
                rule_id="run-tests-lint-typecheck",
                action_name="run_command",
                resource_type=ResourceType.PROCESS,
                risk_level=RiskLevel.LOW,
                safety_action=SafetyAction.ALLOW,
                rationale="Running tests, lint, and typecheck inside sandbox is safe.",
            ),
            ActionRiskRule(
                rule_id="edit-workspace-files",
                action_name="edit_file",
                resource_type=ResourceType.FILESYSTEM,
                risk_level=RiskLevel.MEDIUM,
                safety_action=SafetyAction.REQUIRE_APPROVAL,
                rationale="Editing files can introduce errors or overwrite work.",
                allowed_path_prefixes=["/workspace"],
                approval_requirement=ApprovalRequirement(
                    require_human=True,
                    reason_required=True,
                ),
            ),
            ActionRiskRule(
                rule_id="delete-files",
                action_name="delete_file",
                resource_type=ResourceType.FILESYSTEM,
                risk_level=RiskLevel.HIGH,
                safety_action=SafetyAction.REQUIRE_APPROVAL,
                rationale="File deletion is irreversible and high risk.",
                allowed_path_prefixes=["/workspace"],
                approval_requirement=ApprovalRequirement(
                    require_human=True,
                    reason_required=True,
                ),
            ),
            ActionRiskRule(
                rule_id="access-secrets",
                action_name="read_secret",
                resource_type=ResourceType.SECRET,
                risk_level=RiskLevel.CRITICAL,
                safety_action=SafetyAction.REQUIRE_APPROVAL,
                rationale="Secrets access can leak credentials and tokens.",
                allowed_secret_names=["api_key", "token", "password"],
                approval_requirement=ApprovalRequirement(
                    require_human=True,
                    reason_required=True,
                    approver_role="security_lead",
                ),
            ),
            ActionRiskRule(
                rule_id="arbitrary-network",
                action_name="network_request",
                resource_type=ResourceType.NETWORK,
                risk_level=RiskLevel.HIGH,
                safety_action=SafetyAction.BLOCK,
                rationale="Network requests to arbitrary hosts are blocked for safety.",
                allowed_hosts=[],
            ),
            ActionRiskRule(
                rule_id="allowlisted-docs-network",
                action_name="network_request",
                resource_type=ResourceType.NETWORK,
                risk_level=RiskLevel.MEDIUM,
                safety_action=SafetyAction.ALLOW,
                rationale="Network requests to allowlisted documentation hosts are permitted.",
                allowed_hosts=["docs.python.org", "pypi.org", "npmjs.com"],
            ),
            ActionRiskRule(
                rule_id="deployment-changes",
                action_name="deploy",
                resource_type=ResourceType.EXTERNAL_SIDE_EFFECT,
                risk_level=RiskLevel.CRITICAL,
                safety_action=SafetyAction.REQUIRE_APPROVAL,
                rationale="Deployments affect production and are irreversible.",
                approval_requirement=ApprovalRequirement(
                    require_human=True,
                    reason_required=True,
                    approver_role="deployment_lead",
                    expires_in_seconds=300,
                ),
            ),
            ActionRiskRule(
                rule_id="credential-file-access",
                action_name="read_file",
                resource_type=ResourceType.FILESYSTEM,
                risk_level=RiskLevel.CRITICAL,
                safety_action=SafetyAction.BLOCK,
                rationale="Access to credential files is blocked entirely.",
                allowed_path_prefixes=["/workspace/.env", "/workspace/credentials"],
            ),
        ],
    )
