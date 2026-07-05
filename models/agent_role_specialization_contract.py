from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class AgentRoleType(str, Enum):
    MANAGER = "manager"
    SPECIALIST = "specialist"
    PLANNER = "planner"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"
    VERIFIER = "verifier"
    RETRIEVER = "retriever"
    SUMMARIZER = "summarizer"
    CODER = "coder"
    TOOL_OPERATOR = "tool_operator"


class RoleStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DISABLED = "disabled"


ACTIVATABLE_ROLE_STATUSES = {RoleStatus.ACTIVE}
NON_ACTIVATABLE_ROLE_STATUSES = {RoleStatus.DISABLED}


class SpecializationType(str, Enum):
    GENERALIST = "generalist"
    DOMAIN_SPECIFIC = "domain_specific"
    TOOL_SPECIFIC = "tool_specific"
    VERIFICATION_SPECIFIC = "verification_specific"
    RETRIEVAL_SPECIFIC = "retrieval_specific"
    CODING_SPECIFIC = "coding_specific"
    COORDINATION_SPECIFIC = "coordination_specific"


MANAGER_LIKE_ROLES = {AgentRoleType.MANAGER}


class AutonomyLevel(str, Enum):
    ADVISORY_ONLY = "advisory_only"
    BOUNDED_EXECUTION = "bounded_execution"
    DELEGATION_ALLOWED = "delegation_allowed"
    SUPERVISORY = "supervisory"


SUPERVISORY_AUTONOMY_LEVEL = AutonomyLevel.SUPERVISORY


class RoleOutputType(str, Enum):
    PLAN = "plan"
    ANALYSIS = "analysis"
    IMPLEMENTATION = "implementation"
    REVIEW = "review"
    VERIFICATION_REPORT = "verification_report"
    RETRIEVAL_BUNDLE = "retrieval_bundle"
    SUMMARY = "summary"
    TOOL_RESULT = "tool_result"


class AgentRoleDefinition(BaseModel):
    role_id: str = Field(min_length=1, description="Unique identifier for the role")
    role_type: AgentRoleType
    name: str = Field(min_length=1, description="Human-readable role name")
    description: Optional[str] = None
    status: RoleStatus = RoleStatus.DRAFT
    specialization_type: SpecializationType = SpecializationType.GENERALIST
    autonomy_level: AutonomyLevel = AutonomyLevel.BOUNDED_EXECUTION
    expected_output_types: List[RoleOutputType] = Field(default_factory=list)
    owner: Optional[str] = None
    version: str = "1.0.0"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator("role_id")
    @classmethod
    def role_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("role_id must not be blank")
        return v.strip()

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def validate_supervisory_autonomy(self) -> "AgentRoleDefinition":
        if self.autonomy_level == AutonomyLevel.SUPERVISORY and self.role_type not in MANAGER_LIKE_ROLES:
            raise ValueError(
                f"supervisory autonomy is only valid for manager-like roles, got {self.role_type}"
            )
        return self


class RoleSpecializationProfile(BaseModel):
    profile_id: str = Field(min_length=1, description="Unique identifier")
    role_id: str = Field(min_length=1, description="Reference to agent role definition")
    domain_tags: List[str] = Field(default_factory=list)
    task_types: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    preferred_problem_shapes: List[str] = Field(default_factory=list)
    avoid_problem_shapes: List[str] = Field(default_factory=list)
    quality_focus: Optional[str] = None
    risk_notes: Optional[str] = None

    @field_validator("profile_id")
    @classmethod
    def profile_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("profile_id must not be blank")
        return v.strip()


class RoleCapabilityProfile(BaseModel):
    capability_profile_id: str = Field(min_length=1)
    role_id: str = Field(min_length=1)
    allowed_tools: List[str] = Field(default_factory=list)
    allowed_skill_ids: List[str] = Field(default_factory=list)
    allowed_model_classes: List[str] = Field(default_factory=list)
    allowed_context_types: List[str] = Field(default_factory=list)
    can_delegate: bool = False
    can_verify: bool = False
    can_modify_artifacts: bool = False
    can_request_approval: bool = False
    max_budget_scope: Optional[str] = None
    delegation_boundaries: Optional[str] = None

    @field_validator("capability_profile_id")
    @classmethod
    def cap_profile_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("capability_profile_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def validate_delegation_boundaries(self) -> "RoleCapabilityProfile":
        if self.can_delegate and not self.delegation_boundaries:
            raise ValueError("can_delegate roles must specify delegation_boundaries")
        return self


class RoleConstraintProfile(BaseModel):
    constraint_profile_id: str = Field(min_length=1)
    role_id: str = Field(min_length=1)
    forbidden_tools: List[str] = Field(default_factory=list)
    forbidden_actions: List[str] = Field(default_factory=list)
    approval_required_actions: List[str] = Field(default_factory=list)
    must_not_write_without_verification: bool = False
    must_not_delegate_further: bool = False
    sensitive_data_restrictions: Optional[str] = None
    environment_restrictions: Optional[str] = None

    @field_validator("constraint_profile_id")
    @classmethod
    def constraint_profile_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("constraint_profile_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def validate_constraints_consistent(self) -> "RoleConstraintProfile":
        if self.must_not_delegate_further and not self.must_not_write_without_verification:
            pass
        return self


class RolePromptProfile(BaseModel):
    prompt_profile_id: str = Field(min_length=1)
    role_id: str = Field(min_length=1)
    system_prompt_ref: Optional[str] = None
    prompt_fragments: List[str] = Field(default_factory=list)
    instruction_pack_refs: List[str] = Field(default_factory=list)
    style_notes: Optional[str] = None
    reasoning_constraints: Optional[str] = None
    handoff_template_ref: Optional[str] = None

    @field_validator("prompt_profile_id")
    @classmethod
    def prompt_profile_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("prompt_profile_id must not be blank")
        return v.strip()


class RoleEvaluationProfile(BaseModel):
    evaluation_profile_id: str = Field(min_length=1)
    role_id: str = Field(min_length=1)
    success_criteria: List[str] = Field(default_factory=list)
    failure_modes: List[str] = Field(default_factory=list)
    required_evidence_types: List[str] = Field(default_factory=list)
    quality_metrics: List[str] = Field(default_factory=list)
    review_policy: Optional[str] = None

    @field_validator("evaluation_profile_id")
    @classmethod
    def eval_profile_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("evaluation_profile_id must not be blank")
        return v.strip()


class RoleAssignmentRecord(BaseModel):
    assignment_id: str = Field(min_length=1)
    role_id: str = Field(min_length=1)
    agent_id: str = Field(min_length=1)
    run_id: Optional[str] = None
    session_id: Optional[str] = None
    assigned_by: Optional[str] = None
    assignment_reason: Optional[str] = None
    active_from: datetime = Field(default_factory=datetime.now)
    active_until: Optional[datetime] = None
    override_refs: List[str] = Field(default_factory=list)

    @field_validator("assignment_id")
    @classmethod
    def assignment_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("assignment_id must not be blank")
        return v.strip()

    @field_validator("role_id")
    @classmethod
    def role_id_in_assignment_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("role_id in assignment must not be blank")
        return v.strip()

    @field_validator("agent_id")
    @classmethod
    def agent_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("agent_id must not be blank")
        return v.strip()


class AgentRoleEnvelope(BaseModel):
    envelope_id: str = Field(min_length=1)
    role_definition: AgentRoleDefinition
    specialization_profile: Optional[RoleSpecializationProfile] = None
    capability_profile: Optional[RoleCapabilityProfile] = None
    constraint_profile: Optional[RoleConstraintProfile] = None
    prompt_profile: Optional[RolePromptProfile] = None
    evaluation_profile: Optional[RoleEvaluationProfile] = None
    assignment_record: Optional[RoleAssignmentRecord] = None

    @field_validator("envelope_id")
    @classmethod
    def envelope_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("envelope_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def active_role_requires_capability_and_constraint(self) -> "AgentRoleEnvelope":
        role = self.role_definition
        if role.status == RoleStatus.ACTIVE:
            if self.capability_profile is None:
                raise ValueError("active roles must have a capability_profile")
            if self.constraint_profile is None:
                raise ValueError("active roles must have a constraint_profile")
        return self

    @model_validator(mode="after")
    def artifact_modifying_roles_need_verification_boundary(self) -> "AgentRoleEnvelope":
        cap = self.capability_profile
        if cap and cap.can_modify_artifacts:
            con = self.constraint_profile
            if not con or not con.must_not_write_without_verification:
                if not cap.can_verify:
                    raise ValueError(
                        "roles with can_modify_artifacts=true must define "
                        "verification or approval boundaries"
                    )
        return self

    @model_validator(mode="after")
    def forbidden_tools_not_in_allowed(self) -> "AgentRoleEnvelope":
        cap = self.capability_profile
        con = self.constraint_profile
        if cap is not None and con is not None:
            for ft in con.forbidden_tools:
                if ft in cap.allowed_tools:
                    raise ValueError(f"forbidden tool '{ft}' cannot appear in allowed_tools")
        return self

    @model_validator(mode="after")
    def assignment_must_reference_active_role(self) -> "AgentRoleEnvelope":
        if self.assignment_record is not None:
            if self.role_definition.status not in ACTIVATABLE_ROLE_STATUSES:
                raise ValueError(
                    "assignment records must reference an active role, "
                    f"got status {self.role_definition.status}"
                )
        return self
