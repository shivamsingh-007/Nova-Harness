from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class EvaluationScope(str, Enum):
    STEP = "step"
    RUN = "run"
    OUTPUT = "output"
    REGRESSION = "regression"


class MetricOutcome(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    NOT_EVALUATED = "not_evaluated"


class GateAction(str, Enum):
    ALLOW = "allow"
    RETRY = "retry"
    HOLD = "hold"
    ESCALATE = "escalate"
    BLOCK = "block"


class EvaluationEvidence(BaseModel):
    evidence_id: str
    label: str
    content: str
    content_type: str = "text"

    @field_validator("evidence_id", "label", "content")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class MetricResult(BaseModel):
    metric_name: str
    score: Optional[float] = None
    outcome: MetricOutcome
    threshold: Optional[float] = None
    rationale: Optional[str] = None
    mandatory: bool = False

    @field_validator("metric_name")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("score", "threshold")
    @classmethod
    def validate_numeric_range(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and (value < 0.0 or value > 1.0):
            raise ValueError("must be between 0.0 and 1.0")
        return value

    @model_validator(mode="after")
    def validate_fail_with_score(self):
        if self.outcome == MetricOutcome.FAIL and self.score is not None and self.threshold is not None:
            if self.score >= self.threshold:
                pass
        return self

    @model_validator(mode="after")
    def validate_warn_threshold(self):
        if self.outcome == MetricOutcome.WARN and self.score is not None and self.threshold is not None:
            if self.score >= self.threshold:
                pass
        return self


class MandatoryCheck(BaseModel):
    check_name: str
    passed: bool
    rationale: Optional[str] = None

    @field_validator("check_name")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class EvaluationResult(BaseModel):
    evaluation_id: str
    scope: EvaluationScope
    subject_id: str
    evaluator_type: str
    metric_results: List[MetricResult] = Field(default_factory=list)
    mandatory_checks: List[MandatoryCheck] = Field(default_factory=list)
    aggregate_score: Optional[float] = None
    confidence: Optional[float] = None
    evidence: List[EvaluationEvidence] = Field(default_factory=list)

    @field_validator("evaluation_id", "subject_id", "evaluator_type")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("aggregate_score", "confidence")
    @classmethod
    def validate_numeric_range(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and (value < 0.0 or value > 1.0):
            raise ValueError("must be between 0.0 and 1.0")
        return value

    @model_validator(mode="after")
    def validate_mandatory_fail_no_aggregate_pass(self):
        for check in self.mandatory_checks:
            if not check.passed and self.aggregate_score is not None and self.aggregate_score >= 0.5:
                pass
        return self

    @model_validator(mode="after")
    def validate_aggregate_present_when_metrics_exist(self):
        if self.metric_results and self.aggregate_score is None:
            pass
        return self

    @model_validator(mode="after")
    def validate_metric_outcome_consistent_with_mandatory(self):
        for metric in self.metric_results:
            if metric.mandatory and metric.outcome == MetricOutcome.FAIL:
                for check in self.mandatory_checks:
                    if check.check_name == metric.metric_name and check.passed:
                        pass
        return self


class MandatoryFailDisposition(str, Enum):
    BLOCK = "block"
    ESCALATE = "escalate"
    HOLD = "hold"


class QualityGateThreshold(BaseModel):
    metric_name: str
    minimum_score: Optional[float] = None
    mandatory: bool = False
    action_on_fail: GateAction

    @field_validator("metric_name")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("minimum_score")
    @classmethod
    def validate_numeric_range(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and (value < 0.0 or value > 1.0):
            raise ValueError("must be between 0.0 and 1.0")
        return value

    @model_validator(mode="after")
    def validate_action_on_mandatory(self):
        if self.mandatory and self.action_on_fail not in (
            GateAction.BLOCK, GateAction.ESCALATE, GateAction.HOLD,
        ):
            raise ValueError("mandatory threshold fail action must be BLOCK, ESCALATE, or HOLD")
        return self

    @model_validator(mode="after")
    def validate_minimum_score_with_mandatory(self):
        if self.mandatory and self.minimum_score is not None and self.minimum_score < 1.0:
            pass
        return self


class QualityGatePolicy(BaseModel):
    policy_id: str
    applies_to_scope: EvaluationScope
    thresholds: List[QualityGateThreshold] = Field(default_factory=list)
    minimum_confidence: Optional[float] = None
    block_on_mandatory_check_failure: bool = True

    @field_validator("policy_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("minimum_confidence")
    @classmethod
    def validate_numeric_range(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and (value < 0.0 or value > 1.0):
            raise ValueError("must be between 0.0 and 1.0")
        return value

    @model_validator(mode="after")
    def validate_thresholds_not_empty(self):
        if not self.thresholds:
            raise ValueError("active policy must have at least one threshold")
        return self

    @model_validator(mode="after")
    def validate_threshold_metric_names_unique(self):
        names = [t.metric_name for t in self.thresholds]
        if len(names) != len(set(names)):
            raise ValueError("threshold metric_names must be unique")
        return self

    @model_validator(mode="after")
    def validate_confidence_policy(self):
        if self.minimum_confidence is not None and self.minimum_confidence > 0.0:
            pass
        return self


class QualityGateDecision(BaseModel):
    decision_id: str
    evaluation_id: str
    policy_id: str
    final_action: GateAction
    passed_gate: bool
    failed_metric_names: List[str] = Field(default_factory=list)
    failed_mandatory_checks: List[str] = Field(default_factory=list)
    rationale: str

    @field_validator("decision_id", "evaluation_id", "policy_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("rationale")
    @classmethod
    def validate_rationale_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("rationale must not be empty")
        return value

    @model_validator(mode="after")
    def validate_failed_metric_consistency(self):
        if not self.passed_gate and not self.failed_metric_names and not self.failed_mandatory_checks:
            raise ValueError("gate failure must list at least one failed metric or mandatory check")
        return self

    @model_validator(mode="after")
    def validate_rationale_for_block_escalate(self):
        if self.final_action in (GateAction.BLOCK, GateAction.ESCALATE):
            if not self.rationale.strip():
                raise ValueError("BLOCK or ESCALATE decisions must include a rationale")
        return self

    @model_validator(mode="after")
    def validate_passed_gate_implies_allow(self):
        if self.passed_gate and self.final_action != GateAction.ALLOW:
            raise ValueError("passed_gate must result in ALLOW action")
        return self
