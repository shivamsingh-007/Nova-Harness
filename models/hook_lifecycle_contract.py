from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class HookPointType(str, Enum):
    PRE_LOOP = "pre_loop"
    POST_LOOP = "post_loop"
    PRE_STEP = "pre_step"
    POST_STEP = "post_step"
    PRE_PLAN = "pre_plan"
    POST_PLAN = "post_plan"
    PRE_MODEL_CALL = "pre_model_call"
    POST_MODEL_CALL = "post_model_call"
    PRE_TOOL_CALL = "pre_tool_call"
    POST_TOOL_CALL = "post_tool_call"
    PRE_VERIFY = "pre_verify"
    POST_VERIFY = "post_verify"
    PRE_DELEGATE = "pre_delegate"
    POST_DELEGATE = "post_delegate"
    ON_FAILURE = "on_failure"
    ON_RECOVERY = "on_recovery"
    PRE_ARTIFACT_UPDATE = "pre_artifact_update"
    POST_ARTIFACT_UPDATE = "post_artifact_update"


class HookExecutionMode(str, Enum):
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    ORDERED_CHAIN = "ordered_chain"
    FIRST_MATCH = "first_match"
    MANUAL_ONLY = "manual_only"


class HookEffectType(str, Enum):
    OBSERVE = "observe"
    MODIFY = "modify"
    BLOCK = "block"
    ANNOTATE = "annotate"
    EMIT_EVENT = "emit_event"
    REQUEST_ESCALATION = "request_escalation"


MODIFYING_EFFECTS = {HookEffectType.MODIFY, HookEffectType.BLOCK}
BLOCKING_EFFECTS = {HookEffectType.BLOCK}


class HookResultStatus(str, Enum):
    PASS_THROUGH = "pass_through"
    MODIFIED = "modified"
    BLOCKED = "blocked"
    FAILED = "failed"
    SKIPPED = "skipped"


class HookFailurePolicy(str, Enum):
    FAIL_OPEN = "fail_open"
    FAIL_CLOSED = "fail_closed"
    LOG_AND_CONTINUE = "log_and_continue"
    ESCALATE = "escalate"


class HookPointSpec(BaseModel):
    hook_point_id: str
    hook_point_type: HookPointType
    description: str = ""
    trigger_condition: str = ""
    allowed_effects: List[HookEffectType] = Field(default_factory=list)
    execution_mode: HookExecutionMode = HookExecutionMode.SYNCHRONOUS
    input_schema_ref: str = ""
    output_schema_ref: str = ""
    state_boundary_notes: str = ""

    @field_validator("hook_point_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class HookHandlerManifest(BaseModel):
    handler_id: str
    name: str = ""
    version: str = ""
    hook_point_type: HookPointType
    description: str = ""
    effect_type: HookEffectType
    priority: int = 0
    enabled: bool = True
    permission_profile_ref: str = ""
    failure_policy: HookFailurePolicy = HookFailurePolicy.LOG_AND_CONTINUE
    implementation_ref: str = ""
    owner: str = ""
    tags: List[str] = Field(default_factory=list)

    @field_validator("handler_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def fail_closed_on_approved_points(self):
        return self


class HookContextEnvelope(BaseModel):
    context_id: str
    run_id: Optional[str] = None
    loop_id: Optional[str] = None
    step_id: Optional[str] = None
    task_id: Optional[str] = None
    event_ref: str = ""
    input_refs: List[str] = Field(default_factory=list)
    state_snapshot_refs: List[str] = Field(default_factory=list)
    artifact_refs: List[str] = Field(default_factory=list)
    policy_refs: List[str] = Field(default_factory=list)
    sensitive: bool = False
    read_only_fields: List[str] = Field(default_factory=list)

    @field_validator("context_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def sensitive_context_restricts_writable(self):
        if self.sensitive:
            pass
        return self


class HookMutationProposal(BaseModel):
    proposal_id: str
    handler_id: str
    target_field: str
    proposed_value_ref: str = ""
    reason: str = ""
    requires_approval: bool = False
    safe_to_apply: bool = True

    @field_validator("proposal_id", "handler_id", "target_field")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class HookResultRecord(BaseModel):
    result_id: str
    handler_id: str
    hook_point_type: HookPointType
    status: HookResultStatus
    effect_type: HookEffectType
    message: str = ""
    mutation_proposals: List[HookMutationProposal] = Field(default_factory=list)
    emitted_event_refs: List[str] = Field(default_factory=list)
    block_reason: str = ""
    escalation_requested: bool = False
    started_at: datetime
    ended_at: Optional[datetime] = None

    @field_validator("result_id", "handler_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def modify_effect_requires_proposals(self):
        if self.effect_type == HookEffectType.MODIFY and not self.mutation_proposals:
            raise ValueError("MODIFY effect requires at least one mutation proposal")
        return self

    @model_validator(mode="after")
    def blocked_status_requires_block_reason(self):
        if self.status == HookResultStatus.BLOCKED and not self.block_reason.strip():
            raise ValueError("BLOCKED status requires block_reason")
        return self

    @model_validator(mode="after")
    def mutation_proposals_within_boundary(self):
        return self


class HookChainExecutionRecord(BaseModel):
    chain_id: str
    hook_point_type: HookPointType
    registered_handler_ids: List[str] = Field(default_factory=list)
    executed_handler_ids: List[str] = Field(default_factory=list)
    execution_order: List[str] = Field(default_factory=list)
    chain_status: str = "completed"
    final_effect: Optional[HookEffectType] = None
    stopped_by_handler_id: Optional[str] = None
    aggregated_notes: str = ""

    @field_validator("chain_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def ordered_chain_has_order(self):
        if self.execution_order:
            pass
        return self


class HookRegistrationRecord(BaseModel):
    registration_id: str
    handler_id: str
    hook_point_type: HookPointType
    registration_scope: str = "local"
    enabled: bool = True
    registered_at: datetime
    conditions: str = ""
    override_rules: str = ""

    @field_validator("registration_id", "handler_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class HookLifecycleEnvelope(BaseModel):
    envelope_id: str
    hook_point: HookPointSpec
    handler_manifest: Optional[HookHandlerManifest] = None
    context: Optional[HookContextEnvelope] = None
    result: Optional[HookResultRecord] = None
    chain_execution: Optional[HookChainExecutionRecord] = None
    registration: Optional[HookRegistrationRecord] = None

    @field_validator("envelope_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def disabled_handler_needs_override(self):
        if self.handler_manifest and not self.handler_manifest.enabled:
            pass
        return self
