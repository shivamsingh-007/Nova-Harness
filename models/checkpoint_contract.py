from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CheckpointType(str, Enum):
    MANUAL = "manual"
    STEP_BOUNDARY = "step_boundary"
    PRE_SIDEEFFECT = "pre_sideeffect"
    POST_VERIFICATION = "post_verification"
    FAILURE_RECOVERY = "failure_recovery"


class ResumeDisposition(str, Enum):
    RESUME_FROM_CHECKPOINT = "resume_from_checkpoint"
    RESTART_STEP = "restart_step"
    REQUIRE_REVALIDATION = "require_revalidation"
    ABORT_RESUME = "abort_resume"


class StepReplaySafety(str, Enum):
    REPLAY_SAFE = "replay_safe"
    REQUIRES_IDEMPOTENCY_KEY = "requires_idempotency_key"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"
    NOT_REPLAYABLE = "not_replayable"


class StateSnapshotRef(BaseModel):
    snapshot_id: str
    storage_uri: str
    checksum: Optional[str] = None

    @field_validator("snapshot_id", "storage_uri")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class SideEffectMarker(BaseModel):
    marker_id: str
    step_id: str
    operation_name: str
    idempotency_key: Optional[str] = None
    side_effect_committed: bool = False
    external_reference: Optional[str] = None

    @field_validator("marker_id", "step_id", "operation_name")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def validate_idempotency_for_requires(self):
        if self.side_effect_committed and self.idempotency_key is None:
            raise ValueError("committed side effects must have an idempotency_key")
        return self

    @model_validator(mode="after")
    def validate_committed_step_ref(self):
        if self.side_effect_committed and not self.step_id:
            raise ValueError("committed side effect must have a non-empty step_id")
        return self


class CheckpointedStep(BaseModel):
    step_id: str
    step_name: str
    replay_safety: StepReplaySafety
    status: str
    side_effect_markers: List[SideEffectMarker] = Field(default_factory=list)

    @field_validator("step_id", "step_name")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def validate_idempotency_keys(self):
        if self.replay_safety == StepReplaySafety.REQUIRES_IDEMPOTENCY_KEY:
            for marker in self.side_effect_markers:
                if marker.idempotency_key is None:
                    raise ValueError(
                        "steps with REQUIRES_IDEMPOTENCY_KEY must have idempotency_key on all side effect markers"
                    )
        return self

    @model_validator(mode="after")
    def validate_not_replayable_no_auto_resume(self):
        if self.replay_safety == StepReplaySafety.NOT_REPLAYABLE:
            if self.status == "completed":
                pass
        return self


class WorkingSessionState(BaseModel):
    session_id: str
    run_id: str
    status: SessionStatus
    current_step_id: Optional[str] = None
    current_plan_summary: Optional[str] = None
    completed_step_ids: List[str] = Field(default_factory=list)
    active_context_refs: List[str] = Field(default_factory=list)
    tool_result_refs: List[str] = Field(default_factory=list)

    @field_validator("session_id", "run_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def validate_current_step_when_active(self):
        if self.status == SessionStatus.ACTIVE and self.current_step_id is None:
            raise ValueError("ACTIVE session must have a current_step_id")
        return self


class CheckpointRecord(BaseModel):
    checkpoint_id: str
    session_id: str
    run_id: str
    checkpoint_type: CheckpointType
    created_at: str
    state_snapshot: StateSnapshotRef
    checkpointed_steps: List[CheckpointedStep] = Field(default_factory=list)
    notes: Optional[str] = None

    @field_validator("checkpoint_id", "session_id", "run_id", "created_at")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class ResumeRequest(BaseModel):
    request_id: str
    session_id: str
    run_id: str
    checkpoint_id: str
    requested_by: str
    reason: Optional[str] = None

    @field_validator("request_id", "session_id", "run_id", "checkpoint_id", "requested_by")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class RecoveryDecision(BaseModel):
    decision_id: str
    request_id: str
    disposition: ResumeDisposition
    target_step_id: Optional[str] = None
    requires_revalidation: bool = False
    rationale: str

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
    def validate_abort_no_target(self):
        if self.disposition == ResumeDisposition.ABORT_RESUME and self.target_step_id is not None:
            raise ValueError("ABORT_RESUME must not include a target_step_id")
        return self

    @model_validator(mode="after")
    def validate_requires_target(self):
        if self.disposition in (ResumeDisposition.RESUME_FROM_CHECKPOINT, ResumeDisposition.RESTART_STEP):
            if self.target_step_id is None:
                raise ValueError(f"{self.disposition.value} requires a target_step_id")
        return self
