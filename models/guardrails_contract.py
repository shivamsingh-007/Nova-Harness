from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class GuardrailDirection(str, Enum):
    INPUT = "input"
    OUTPUT = "output"


class GuardrailAction(str, Enum):
    ALLOW = "allow"
    SANITIZE = "sanitize"
    REJECT = "reject"
    ESCALATE = "escalate"
    REQUIRE_CONFIRMATION = "require_confirmation"


class ContentSourceType(str, Enum):
    USER = "user"
    RETRIEVED_CONTEXT = "retrieved_context"
    TOOL_OUTPUT = "tool_output"
    WEB_CONTENT = "web_content"
    MODEL_OUTPUT = "model_output"
    SYSTEM_PROMPT = "system_prompt"


class RiskCategory(str, Enum):
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK = "jailbreak"
    DATA_EXFILTRATION = "data_exfiltration"
    PII = "pii"
    POLICY_VIOLATION = "policy_violation"
    UNSAFE_CODE = "unsafe_code"
    UNTRUSTED_INSTRUCTION = "untrusted_instruction"
    SCHEMA_VIOLATION = "schema_violation"
    UNKNOWN = "unknown"


class GuardrailRule(BaseModel):
    rule_id: str
    direction: GuardrailDirection
    risk_category: RiskCategory
    action: GuardrailAction
    enabled: bool = True
    description: Optional[str] = None

    @field_validator("rule_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("rule_id must not be empty")
        return value


class InputPayload(BaseModel):
    payload_id: str
    source_type: ContentSourceType
    content: str
    source_label: Optional[str] = None

    @field_validator("payload_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("payload_id must not be empty")
        return value

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content must not be empty")
        return value


class OutputPayload(BaseModel):
    payload_id: str
    content: str
    intended_for_user: bool = True
    intended_for_tool: bool = False
    format_label: Optional[str] = None

    @field_validator("payload_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("payload_id must not be empty")
        return value

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content must not be empty")
        return value

    @model_validator(mode="after")
    def validate_tool_user_not_both(self):
        if not self.intended_for_user and not self.intended_for_tool:
            raise ValueError("at least one of intended_for_user or intended_for_tool must be True")
        return self


class GuardrailEvidence(BaseModel):
    evidence_type: str
    detail: str
    matched_text: Optional[str] = None

    @field_validator("evidence_type", "detail")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class GuardrailEvaluation(BaseModel):
    evaluation_id: str
    payload_id: str
    direction: GuardrailDirection
    action: GuardrailAction
    blocked: bool
    triggered_rules: List[str] = Field(default_factory=list)
    detected_risks: List[RiskCategory] = Field(default_factory=list)
    evidence: List[GuardrailEvidence] = Field(default_factory=list)

    @field_validator("evaluation_id", "payload_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def validate_blocked_has_rules(self):
        if self.blocked and not self.triggered_rules:
            raise ValueError("blocked=True requires at least one triggered_rules entry")
        return self

    @model_validator(mode="after")
    def validate_reject_has_rules(self):
        if self.action == GuardrailAction.REJECT and not self.triggered_rules:
            raise ValueError("REJECT action requires at least one triggered_rules entry")
        return self


class SanitizedOutput(BaseModel):
    output_id: str
    sanitized_content: str
    redactions_applied: List[str] = Field(default_factory=list)
    schema_valid: bool = True

    @field_validator("output_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("output_id must not be empty")
        return value

    @field_validator("sanitized_content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("sanitized_content must not be empty")
        return value


class GuardrailDecision(BaseModel):
    decision_id: str
    payload_id: str
    final_action: GuardrailAction
    rationale: str
    should_audit: bool = False

    @field_validator("decision_id", "payload_id")
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


class GuardrailPolicy(BaseModel):
    policy_id: str
    input_rules: List[GuardrailRule] = Field(default_factory=list)
    output_rules: List[GuardrailRule] = Field(default_factory=list)
    allowed_output_formats: List[str] = Field(default_factory=list)
    require_schema_validation: bool = True

    @field_validator("policy_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("policy_id must not be empty")
        return value

    @model_validator(mode="after")
    def validate_allowed_formats_when_schema_required(self):
        if self.require_schema_validation and not self.allowed_output_formats:
            raise ValueError("allowed_output_formats must not be empty when require_schema_validation=True")
        return self
