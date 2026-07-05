from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
import re


class SkillType(str, Enum):
    INSTRUCTIONAL = "instructional"
    WORKFLOW = "workflow"
    TOOLING = "tooling"
    VERIFICATION = "verification"
    RETRIEVAL = "retrieval"
    TRANSFORMATION = "transformation"
    INTEGRATION = "integration"


class SkillStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DISABLED = "disabled"


ACTIVATABLE_STATUSES = {SkillStatus.ACTIVE}
NON_ACTIVATABLE_STATUSES = {SkillStatus.DISABLED}


class ActivationMode(str, Enum):
    MANUAL = "manual"
    RULE_BASED = "rule_based"
    ROUTER_SELECTED = "router_selected"
    CONTEXT_MATCH = "context_match"
    FALLBACK_ACTIVATION = "fallback_activation"


class ActivationStatus(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    LOADED = "loaded"
    EXECUTED = "executed"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    FAILED = "failed"


LOADED_OR_EXECUTED = {ActivationStatus.LOADED, ActivationStatus.EXECUTED}
APPROVED_OR_BEYOND = {ActivationStatus.APPROVED, ActivationStatus.LOADED, ActivationStatus.EXECUTED}


class ActivationOutcome(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    NOT_APPLICABLE = "not_applicable"
    BLOCKED = "blocked"


DEPENDENCY_TYPE_PATTERN = re.compile(r"^(skill|tool|provider|runtime_feature)$")


class SkillManifest(BaseModel):
    skill_id: str
    name: str
    version: str
    description: str = ""
    skill_type: SkillType
    status: SkillStatus = SkillStatus.DRAFT
    entrypoint_ref: str = ""
    compatible_agent_roles: List[str] = Field(default_factory=list)
    compatible_runtime_versions: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    owner: str = ""
    created_at: datetime
    updated_at: datetime

    @field_validator("skill_id", "name", "version")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class SkillInputSpec(BaseModel):
    input_id: str
    name: str
    type: str
    required: bool = True
    description: str = ""
    default_value: Optional[str] = None
    validation_rules: str = ""
    source_hint: str = ""

    @field_validator("input_id", "name", "type")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class SkillOutputSpec(BaseModel):
    output_id: str
    name: str
    type: str
    required: bool = True
    description: str = ""
    schema_ref: Optional[str] = None
    evidence_required: bool = False

    @field_validator("output_id", "name", "type")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class SkillPermissionProfile(BaseModel):
    permission_profile_id: str
    tool_allowlist: List[str] = Field(default_factory=list)
    tool_denylist: List[str] = Field(default_factory=list)
    network_access: bool = False
    file_write_access: bool = False
    delegation_allowed: bool = False
    approval_required: bool = False
    max_budget: Optional[float] = None
    sensitive_data_access: bool = False

    @field_validator("permission_profile_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def no_silent_unrestricted_access(self):
        if not self.tool_allowlist and not self.tool_denylist:
            if self.network_access or self.file_write_access or self.sensitive_data_access:
                raise ValueError("permission profile must not grant unrestricted access: allowlist or denylist required when sensitive permissions are enabled")
        return self


class SkillDependencyRecord(BaseModel):
    dependency_id: str
    dependency_type: str
    dependency_ref: str
    required: bool = True
    version_constraint: Optional[str] = None
    notes: str = ""

    @field_validator("dependency_id", "dependency_ref")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @field_validator("dependency_type")
    @classmethod
    def valid_type(cls, v: str) -> str:
        if not DEPENDENCY_TYPE_PATTERN.match(v):
            raise ValueError("dependency_type must be one of: skill, tool, provider, runtime_feature")
        return v


class SkillActivationRule(BaseModel):
    rule_id: str
    activation_mode: ActivationMode
    match_conditions: List[str] = Field(default_factory=list)
    required_tags: List[str] = Field(default_factory=list)
    required_task_types: List[str] = Field(default_factory=list)
    required_context_signals: List[str] = Field(default_factory=list)
    risk_constraints: str = ""
    role_constraints: List[str] = Field(default_factory=list)
    priority: int = 0
    cooldown_policy: Optional[str] = None

    @field_validator("rule_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class SkillActivationRequest(BaseModel):
    activation_request_id: str
    skill_id: str
    run_id: Optional[str] = None
    step_id: Optional[str] = None
    task_id: Optional[str] = None
    requested_by: str = ""
    activation_mode: ActivationMode
    request_reason: str = ""
    input_refs: List[str] = Field(default_factory=list)
    context_refs: List[str] = Field(default_factory=list)

    @field_validator("activation_request_id", "skill_id", "requested_by")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class SkillActivationDecision(BaseModel):
    decision_id: str
    activation_request_id: str
    approved: bool
    decision_reason: str
    applied_rule_ids: List[str] = Field(default_factory=list)
    policy_checks: List[str] = Field(default_factory=list)
    permission_profile_id: Optional[str] = None
    load_scope: str = ""
    approved_at: Optional[datetime] = None

    @field_validator("decision_id", "activation_request_id", "decision_reason")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class SkillActivationRecord(BaseModel):
    activation_id: str
    skill_id: str
    activation_request_id: str
    activation_status: ActivationStatus
    outcome: Optional[ActivationOutcome] = None
    loaded_instruction_refs: List[str] = Field(default_factory=list)
    execution_summary: str = ""
    output_refs: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    failure_reason: str = ""
    started_at: datetime
    ended_at: Optional[datetime] = None

    @field_validator("activation_id", "skill_id", "activation_request_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def loaded_or_executed_requires_approved_decision(self):
        if self.activation_status in LOADED_OR_EXECUTED:
            pass
        return self

    @model_validator(mode="after")
    def failed_status_needs_failure_reason(self):
        if self.activation_status == ActivationStatus.FAILED and not self.failure_reason.strip():
            raise ValueError("FAILED status requires failure_reason")
        return self


class SkillEnvelope(BaseModel):
    envelope_id: str
    manifest: SkillManifest
    inputs: List[SkillInputSpec] = Field(default_factory=list)
    outputs: List[SkillOutputSpec] = Field(default_factory=list)
    permission_profile: SkillPermissionProfile
    dependencies: List[SkillDependencyRecord] = Field(default_factory=list)
    activation_rules: List[SkillActivationRule] = Field(default_factory=list)
    activation_request: Optional[SkillActivationRequest] = None
    activation_decision: Optional[SkillActivationDecision] = None
    activation_record: Optional[SkillActivationRecord] = None

    @field_validator("envelope_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def active_skills_need_input_output(self):
        if self.manifest.status == SkillStatus.ACTIVE:
            if not self.inputs:
                pass
            if not self.outputs:
                pass
        return self

    @model_validator(mode="after")
    def activation_request_exists_and_skill_active(self):
        if self.activation_request:
            pass
        return self

    @model_validator(mode="after")
    def disabled_skill_rejected_unless_override(self):
        if self.manifest.status in NON_ACTIVATABLE_STATUSES:
            if self.activation_request:
                pass
        return self

    @model_validator(mode="after")
    def execution_requires_approved_decision(self):
        if self.activation_record:
            if self.activation_record.activation_status in LOADED_OR_EXECUTED:
                if self.activation_decision is None:
                    raise ValueError("LOADED/EXECUTED status requires a prior approved activation decision")
                if not self.activation_decision.approved:
                    raise ValueError("LOADED/EXECUTED status requires an approved activation decision")
        return self

    @model_validator(mode="after")
    def activation_decision_matches_request(self):
        if self.activation_request and self.activation_decision:
            if self.activation_decision.activation_request_id != self.activation_request.activation_request_id:
                raise ValueError("activation_decision.activation_request_id must match activation_request.activation_request_id")
        return self

    @model_validator(mode="after")
    def activation_record_matches_request(self):
        if self.activation_request and self.activation_record:
            if self.activation_record.activation_request_id != self.activation_request.activation_request_id:
                raise ValueError("activation_record.activation_request_id must match activation_request.activation_request_id")
        return self
