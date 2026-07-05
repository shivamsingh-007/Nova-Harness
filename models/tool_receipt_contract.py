from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class InvocationStatus(str, Enum):
    REQUESTED = "requested"
    EXECUTED = "executed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class SideEffectType(str, Enum):
    NONE = "none"
    READ_ONLY = "read_only"
    STATE_MUTATION = "state_mutation"
    EXTERNAL_SEND = "external_send"
    FILE_WRITE = "file_write"
    DATA_EXPORT = "data_export"


class IntegrityMode(str, Enum):
    NONE = "none"
    HASH_ONLY = "hash_only"
    SIGNED = "signed"
    CHAINED = "chained"


class ToolInvocationRef(BaseModel):
    request_id: str
    run_id: str
    task_id: Optional[str] = None
    trace_id: Optional[str] = None
    agent_id: str
    tool_id: str
    action: str

    @field_validator("request_id", "run_id", "agent_id", "tool_id", "action")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class ExecutionTiming(BaseModel):
    requested_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None

    @field_validator("requested_at")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("duration_ms")
    @classmethod
    def non_negative(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("duration_ms must be non-negative")
        return v


class ResultReference(BaseModel):
    result_ref_id: str
    result_type: str
    content_ref: Optional[str] = None
    content_hash: Optional[str] = None
    item_count: Optional[int] = None

    @field_validator("result_ref_id", "result_type")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("item_count")
    @classmethod
    def non_negative_count(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("item_count must be non-negative")
        return v


class SideEffectSummary(BaseModel):
    side_effect_type: SideEffectType
    target_refs: List[str] = Field(default_factory=list)
    summary: str

    @field_validator("summary")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("summary must not be blank")
        return stripped

    @field_validator("target_refs")
    @classmethod
    def no_blank_refs(cls, v: List[str]) -> List[str]:
        cleaned = [r.strip() for r in v]
        if any(not r for r in cleaned):
            raise ValueError("target_refs must not contain blank entries")
        return cleaned


class IntegrityMetadata(BaseModel):
    integrity_mode: IntegrityMode = IntegrityMode.NONE
    canonical_hash: Optional[str] = None
    signature_ref: Optional[str] = None
    previous_receipt_hash: Optional[str] = None

    @model_validator(mode="after")
    def integrity_fields_aligned(self):
        if self.integrity_mode == IntegrityMode.SIGNED and not self.signature_ref:
            raise ValueError("SIGNED integrity mode requires a signature_ref")
        if self.integrity_mode == IntegrityMode.CHAINED and not self.previous_receipt_hash:
            raise ValueError("CHAINED integrity mode requires previous_receipt_hash")
        if self.integrity_mode == IntegrityMode.HASH_ONLY and not self.canonical_hash:
            raise ValueError("HASH_ONLY integrity mode requires canonical_hash")
        return self


class ToolExecutionResult(BaseModel):
    status: InvocationStatus
    outcome_summary: str
    result_references: List[ResultReference] = Field(default_factory=list)
    side_effects: List[SideEffectSummary] = Field(default_factory=list)
    error_code: Optional[str] = None
    error_summary: Optional[str] = None

    @field_validator("outcome_summary")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("outcome_summary must not be blank")
        return stripped

    @model_validator(mode="after")
    def failure_should_have_error_info(self):
        if self.status in (InvocationStatus.FAILED, InvocationStatus.TIMED_OUT, InvocationStatus.BLOCKED):
            if not self.error_summary:
                raise ValueError(f"status '{self.status.value}' requires an error_summary")
        return self


class ToolInvocationReceipt(BaseModel):
    receipt_id: str
    invocation: ToolInvocationRef
    timing: ExecutionTiming
    execution_result: ToolExecutionResult
    policy_decision_ref: Optional[str] = None
    approval_ref: Optional[str] = None
    integrity: IntegrityMetadata = Field(default_factory=IntegrityMetadata)

    @field_validator("receipt_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def completed_at_not_before_started_at(self):
        if self.timing.started_at and self.timing.completed_at:
            if self.timing.completed_at < self.timing.started_at:
                raise ValueError("completed_at must not be earlier than started_at")
        return self


class ReceiptEnvelope(BaseModel):
    envelope_id: str
    receipt: ToolInvocationReceipt

    @field_validator("envelope_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped
