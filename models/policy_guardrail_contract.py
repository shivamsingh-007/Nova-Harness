from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class EvaluationTargetType(str, Enum):
    PROMPT = "prompt"
    TOOL_INVOCATION = "tool_invocation"
    MEMORY_ACCESS = "memory_access"
    MODEL_OUTPUT = "model_output"
    WORKFLOW_STEP = "workflow_step"


class PolicyDecisionType(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    MODIFY = "modify"
    REVIEW = "review"
    QUARANTINE = "quarantine"
    DEFER = "defer"


class FindingSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ObligationType(str, Enum):
    REQUIRE_APPROVAL = "require_approval"
    MASK_CONTENT = "mask_content"
    REDUCE_SCOPE = "reduce_scope"
    DOWNGRADE_TOOL = "downgrade_tool"
    RETRY_WITH_CONSTRAINTS = "retry_with_constraints"
    LOG_ONLY = "log_only"


class PolicyRef(BaseModel):
    policy_id: str
    policy_name: str
    policy_version: Optional[str] = None

    @model_validator(mode="after")
    def check_non_empty(self):
        if not self.policy_id.strip():
            raise ValueError("policy_id must be non-empty")
        if not self.policy_name.strip():
            raise ValueError("policy_name must be non-empty")
        return self


class EvidenceSignal(BaseModel):
    signal_id: str
    signal_type: str
    source_ref: str
    summary: str
    confidence: Optional[float] = None

    @model_validator(mode="after")
    def check_non_empty(self):
        if not self.signal_id.strip():
            raise ValueError("signal_id must be non-empty")
        if not self.signal_type.strip():
            raise ValueError("signal_type must be non-empty")
        if not self.source_ref.strip():
            raise ValueError("source_ref must be non-empty")
        if not self.summary.strip():
            raise ValueError("summary must be non-empty")
        return self

    @model_validator(mode="after")
    def check_confidence_range(self):
        if self.confidence is not None and not (0 <= self.confidence <= 1):
            raise ValueError("confidence must be between 0 and 1 inclusive")
        return self


class GuardrailFinding(BaseModel):
    finding_id: str
    severity: FindingSeverity
    category: str
    summary: str
    evidence_signals: List[EvidenceSignal] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_non_empty(self):
        if not self.finding_id.strip():
            raise ValueError("finding_id must be non-empty")
        if not self.category.strip():
            raise ValueError("category must be non-empty")
        if not self.summary.strip():
            raise ValueError("summary must be non-empty")
        return self

    @model_validator(mode="after")
    def check_high_critical_should_have_signals(self):
        if self.severity in (FindingSeverity.HIGH, FindingSeverity.CRITICAL) and not self.evidence_signals:
            raise ValueError(
                "HIGH and CRITICAL findings must include at least one evidence signal"
            )
        return self


class DecisionObligation(BaseModel):
    obligation_type: ObligationType
    parameters: List[str] = Field(default_factory=list)


class PolicyEvaluation(BaseModel):
    evaluation_id: str
    target_type: EvaluationTargetType
    target_ref: str
    policy: PolicyRef
    findings: List[GuardrailFinding] = Field(default_factory=list)
    risk_level: RiskLevel
    rationale: str

    @model_validator(mode="after")
    def check_non_empty(self):
        if not self.evaluation_id.strip():
            raise ValueError("evaluation_id must be non-empty")
        if not self.target_ref.strip():
            raise ValueError("target_ref must be non-empty")
        if not self.rationale.strip():
            raise ValueError("rationale must be non-empty")
        return self


class GuardrailDecisionEnvelope(BaseModel):
    decision_id: str
    evaluation: PolicyEvaluation
    decision: PolicyDecisionType
    obligations: List[DecisionObligation] = Field(default_factory=list)
    execution_allowed: bool
    decided_by: str

    @model_validator(mode="after")
    def check_non_empty(self):
        if not self.decision_id.strip():
            raise ValueError("decision_id must be non-empty")
        if not self.decided_by.strip():
            raise ValueError("decided_by must be non-empty")
        return self

    @model_validator(mode="after")
    def check_restrictive_decisions_not_allow(self):
        if self.decision in (
            PolicyDecisionType.DENY,
            PolicyDecisionType.QUARANTINE,
        ) and self.execution_allowed:
            raise ValueError("DENY and QUARANTINE decisions must set execution_allowed=False")
        return self
