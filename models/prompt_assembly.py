from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class InstructionLayerType(str, Enum):
    SYSTEM = "system"
    GLOBAL = "global"
    REPOSITORY = "repository"
    TASK = "task"


class ContextBlockType(str, Enum):
    FILE = "file"
    FAILURE = "failure"
    DOC = "doc"
    SUMMARY = "summary"


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class InstructionLayer(BaseModel):
    layer_id: str
    layer_type: InstructionLayerType
    title: str
    content: str
    priority: int = 0

    @field_validator("layer_id")
    @classmethod
    def non_empty_layer_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("layer_id must not be empty")
        return value

    @field_validator("title")
    @classmethod
    def non_empty_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be empty")
        return value

    @field_validator("content")
    @classmethod
    def non_empty_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content must not be empty")
        return value


class ContextBlock(BaseModel):
    block_id: str
    block_type: ContextBlockType
    title: str
    content: str
    source_ref: Optional[str] = None
    priority: int = 0

    @field_validator("block_id")
    @classmethod
    def non_empty_block_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("block_id must not be empty")
        return value

    @field_validator("title")
    @classmethod
    def non_empty_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be empty")
        return value

    @field_validator("content")
    @classmethod
    def non_empty_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content must not be empty")
        return value


class ToolExposure(BaseModel):
    tool_name: str
    description: str
    input_schema_summary: str
    requires_approval: bool = False

    @field_validator("tool_name")
    @classmethod
    def non_empty_tool_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("tool_name must not be empty")
        return value


class ConstraintBlock(BaseModel):
    title: str
    rules: List[str] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def non_empty_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be empty")
        return value

    @model_validator(mode="after")
    def non_empty_rules(self):
        if not self.rules:
            raise ValueError("constraint block must have at least one rule")
        return self


class VerificationBlock(BaseModel):
    summary: Optional[str] = None
    required_checks: List[str] = Field(default_factory=list)
    done_definition: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def meaningful_content(self):
        if not self.required_checks and not self.done_definition:
            raise ValueError("verification block must have at least one required_check or done_definition item")
        return self


class MessageBlock(BaseModel):
    role: MessageRole
    content: str

    @field_validator("content")
    @classmethod
    def non_empty_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message content must not be empty")
        return value


class PromptAssembly(BaseModel):
    assembly_id: str
    run_id: str
    instruction_layers: List[InstructionLayer] = Field(default_factory=list)
    context_blocks: List[ContextBlock] = Field(default_factory=list)
    tool_exposures: List[ToolExposure] = Field(default_factory=list)
    constraints: List[ConstraintBlock] = Field(default_factory=list)
    verification: Optional[VerificationBlock] = None
    messages: List[MessageBlock] = Field(default_factory=list)

    @field_validator("assembly_id")
    @classmethod
    def non_empty_assembly_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("assembly_id must not be empty")
        return value

    @field_validator("run_id")
    @classmethod
    def non_empty_run_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("run_id must not be empty")
        return value

    @model_validator(mode="after")
    def at_least_one_instruction_layer(self):
        if not self.instruction_layers:
            raise ValueError("prompt assembly must have at least one instruction layer")
        return self

    @model_validator(mode="after")
    def at_least_one_message_block(self):
        if not self.messages:
            raise ValueError("prompt assembly must have at least one message block")
        return self

    @model_validator(mode="after")
    def unique_tool_names(self):
        seen = set()
        for t in self.tool_exposures:
            if t.tool_name in seen:
                raise ValueError(f"duplicate tool_name: {t.tool_name}")
            seen.add(t.tool_name)
        return self
