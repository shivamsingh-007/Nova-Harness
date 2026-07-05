from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class ContextBlockType(str, Enum):
    SYSTEM_INSTRUCTION = "system_instruction"
    USER_INPUT = "user_input"
    MEMORY = "memory"
    RETRIEVAL = "retrieval"
    TOOL_OUTPUT = "tool_output"
    POLICY_NOTE = "policy_note"
    SUMMARY = "summary"


class ContextTrustLevel(str, Enum):
    TRUSTED = "trusted"
    INTERNAL_UNVERIFIED = "internal_unverified"
    EXTERNAL_UNTRUSTED = "external_untrusted"


class PromptRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ModelProviderType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    GOOGLE = "google"
    OTHER = "other"


class FinishReason(str, Enum):
    STOP = "stop"
    LENGTH = "length"
    TOOL_CALL = "tool_call"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"


class ModelRef(BaseModel):
    model_ref_id: str
    provider: ModelProviderType
    model_name: str
    model_version: Optional[str] = None

    @field_validator("model_ref_id", "model_name")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class ContextProvenance(BaseModel):
    provenance_id: str
    source_type: str
    source_ref: str
    timestamp: Optional[str] = None
    confidence: Optional[float] = None

    @field_validator("provenance_id", "source_type", "source_ref")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("confidence")
    @classmethod
    def in_range(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v


class PromptContextBlock(BaseModel):
    block_id: str
    block_type: ContextBlockType
    role: PromptRole
    content_ref: str
    trust_level: ContextTrustLevel
    provenance: Optional[ContextProvenance] = None

    @field_validator("block_id", "content_ref")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class GenerationConfig(BaseModel):
    temperature: Optional[float] = None
    max_output_tokens: Optional[int] = None
    top_p: Optional[float] = None
    stop_sequences: List[str] = Field(default_factory=list)

    @field_validator("temperature")
    @classmethod
    def valid_range(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 2.0):
            raise ValueError("temperature must be between 0.0 and 2.0")
        return v

    @field_validator("top_p")
    @classmethod
    def valid_top_p(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("top_p must be between 0.0 and 1.0")
        return v

    @field_validator("max_output_tokens")
    @classmethod
    def positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1:
            raise ValueError("max_output_tokens must be at least 1")
        return v


class ModelResponseSummary(BaseModel):
    response_ref: str
    finish_reason: FinishReason
    output_ref: Optional[str] = None
    prompt_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: Optional[int] = None

    @field_validator("response_ref")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("prompt_tokens", "output_tokens", "latency_ms")
    @classmethod
    def non_negative(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("must be non-negative")
        return v


class ModelCallEnvelope(BaseModel):
    call_id: str
    run_id: str
    task_id: Optional[str] = None
    trace_id: Optional[str] = None
    agent_id: str
    model: ModelRef
    prompt_blocks: List[PromptContextBlock] = Field(default_factory=list)
    generation_config: GenerationConfig = Field(default_factory=GenerationConfig)
    response: ModelResponseSummary
    policy_ref: Optional[str] = None

    @field_validator("call_id", "run_id", "agent_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


