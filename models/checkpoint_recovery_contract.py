from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class CheckpointStatus(str, Enum):
    CREATED = "created"
    RESUMABLE = "resumable"
    RESTORED = "restored"
    STALE = "stale"
    INVALID = "invalid"
    SUPERSEDED = "superseded"


class CheckpointBoundaryType(str, Enum):
    TASK_UNIT_COMPLETED = "task_unit_completed"
    TOOL_PHASE_COMPLETED = "tool_phase_completed"
    MODEL_PHASE_COMPLETED = "model_phase_completed"
    APPROVAL_WAIT = "approval_wait"
    USER_INPUT_WAIT = "user_input_wait"
    MANUAL_PAUSE = "manual_pause"


class RecoveryDisposition(str, Enum):
    RESUME = "resume"
    RESTART_UNIT = "restart_unit"
    ESCALATE = "escalate"
    ABORT = "abort"


class SnapshotConsistencyLevel(str, Enum):
    PARTIAL = "partial"
    CONSISTENT = "consistent"
    VERIFIED = "verified"


class CheckpointProgress(BaseModel):
    completed_units: int = 0
    remaining_units: Optional[int] = None
    last_completed_unit_ref: Optional[str] = None
    next_unit_ref: Optional[str] = None
    progress_note: Optional[str] = None

    @field_validator("completed_units", "remaining_units")
    @classmethod
    def non_negative(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("must be non-negative")
        return v


class StateSnapshotRef(BaseModel):
    snapshot_ref_id: str
    snapshot_uri: str
    snapshot_hash: Optional[str] = None
    serialization_format: str
    size_bytes: Optional[int] = None

    @field_validator("snapshot_ref_id", "snapshot_uri", "serialization_format")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("size_bytes")
    @classmethod
    def non_negative(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("size_bytes must be non-negative")
        return v


class RecoveryPolicy(BaseModel):
    disposition: RecoveryDisposition
    resume_from_unit_ref: Optional[str] = None
    max_restore_attempts: int = 3
    requires_validation_before_resume: bool = True

    @field_validator("max_restore_attempts")
    @classmethod
    def at_least_one(cls, v: int) -> int:
        if v < 1:
            raise ValueError("max_restore_attempts must be at least 1")
        return v

    @model_validator(mode="after")
    def resume_needs_unit_ref(self):
        if self.disposition in (RecoveryDisposition.RESUME, RecoveryDisposition.RESTART_UNIT):
            if not self.resume_from_unit_ref:
                raise ValueError(f"disposition '{self.disposition.value}' requires resume_from_unit_ref")
        return self


class RestoreAttempt(BaseModel):
    attempt_id: str
    attempted_at: str
    outcome: str
    note: Optional[str] = None

    @field_validator("attempt_id", "attempted_at", "outcome")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class CheckpointRecord(BaseModel):
    checkpoint_id: str
    session_id: str
    run_id: str
    task_id: Optional[str] = None
    trace_id: Optional[str] = None
    agent_id: str
    status: CheckpointStatus
    boundary_type: CheckpointBoundaryType
    consistency_level: SnapshotConsistencyLevel
    progress: CheckpointProgress
    snapshot: StateSnapshotRef
    recovery_policy: RecoveryPolicy
    restore_attempts: List[RestoreAttempt] = Field(default_factory=list)

    @field_validator("checkpoint_id", "session_id", "run_id", "agent_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def invalid_or_failed_restore_blocks_resume(self):
        if self.status in (CheckpointStatus.INVALID, CheckpointStatus.STALE):
            if self.recovery_policy.disposition == RecoveryDisposition.RESUME:
                raise ValueError(f"checkpoints with status '{self.status.value}' must not allow RESUME disposition")
        return self


class SessionRecoveryEnvelope(BaseModel):
    envelope_id: str
    checkpoint: CheckpointRecord

    @field_validator("envelope_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped
