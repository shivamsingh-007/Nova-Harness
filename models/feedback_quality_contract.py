from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class FeedbackSourceType(str, Enum):
    HUMAN = "human"
    AUTOMATED = "automated"
    MODEL = "model"
    HYBRID = "hybrid"


class QualityVerdict(str, Enum):
    PASS = "pass"
    PARTIAL = "partial"
    FAIL = "fail"
    UNKNOWN = "unknown"


class EvaluationMethod(str, Enum):
    RUBRIC = "rubric"
    HEURISTIC = "heuristic"
    MODEL_JUDGE = "model_judge"
    MANUAL_REVIEW = "manual_review"


class SignalSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RubricRef(BaseModel):
    rubric_id: str
    rubric_name: str
    version: Optional[str] = None

    @field_validator("rubric_id", "rubric_name")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class QualityCriterion(BaseModel):
    criterion_id: str
    description: str
    score: Optional[float] = None
    passed: Optional[bool] = None

    @field_validator("criterion_id", "description")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("score")
    @classmethod
    def score_in_range(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("score must be between 0 and 1")
        return v


class EvidenceRef(BaseModel):
    evidence_id: str
    evidence_type: str
    source_ref: Optional[str] = None
    evidence_hash: Optional[str] = None

    @field_validator("evidence_id", "evidence_type")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class FeedbackRecord(BaseModel):
    feedback_id: str
    source_type: FeedbackSourceType
    verdict: QualityVerdict
    summary: str
    comments: Optional[str] = None
    score: Optional[float] = None
    severity: SignalSeverity = SignalSeverity.LOW
    criteria: List[QualityCriterion] = Field(default_factory=list)
    evidence_refs: List[EvidenceRef] = Field(default_factory=list)
    rubric_ref: Optional[RubricRef] = None

    @field_validator("feedback_id", "summary")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("score")
    @classmethod
    def score_in_range(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("score must be between 0 and 1")
        return v

    @model_validator(mode="after")
    def verdict_consistent_with_criteria(self):
        if not self.criteria:
            return self
        passed_list = [c.passed for c in self.criteria if c.passed is not None]
        if not passed_list:
            return self
        all_passed = all(passed_list)
        none_passed = not any(passed_list)
        if self.verdict == QualityVerdict.PASS and none_passed:
            raise ValueError("PASS verdict contradicts criteria: none passed")
        if self.verdict == QualityVerdict.FAIL and all_passed:
            raise ValueError("FAIL verdict contradicts criteria: all passed")
        return self

    @model_validator(mode="after")
    def unknown_not_with_explicit_criteria(self):
        if self.verdict != QualityVerdict.UNKNOWN:
            return self
        if self.criteria:
            explicit = [c for c in self.criteria if c.passed is not None]
            if explicit:
                raise ValueError("UNKNOWN verdict must not have explicit criterion pass/fail values")
        return self


class EvaluationRecord(BaseModel):
    evaluation_id: str
    run_id: str
    task_id: Optional[str] = None
    trace_id: Optional[str] = None
    artifact_id: Optional[str] = None
    model_call_id: Optional[str] = None
    tool_call_id: Optional[str] = None
    method: EvaluationMethod
    feedback: FeedbackRecord
    evaluator_ref: Optional[str] = None

    @field_validator("evaluation_id", "run_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def source_aligns_with_method(self):
        if self.feedback.source_type == FeedbackSourceType.HUMAN and self.method == EvaluationMethod.HEURISTIC:
            raise ValueError("HUMAN source should not use HEURISTIC method")
        if self.feedback.source_type == FeedbackSourceType.AUTOMATED and self.method == EvaluationMethod.MANUAL_REVIEW:
            raise ValueError("AUTOMATED source should not use MANUAL_REVIEW method")
        if self.feedback.source_type == FeedbackSourceType.MODEL and self.method == EvaluationMethod.HEURISTIC:
            raise ValueError("MODEL source should not use HEURISTIC method")
        return self


class QualitySignalEnvelope(BaseModel):
    envelope_id: str
    signals: List[EvaluationRecord] = Field(default_factory=list)

    @field_validator("envelope_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def evaluation_ids_unique(self):
        ids = [s.evaluation_id for s in self.signals]
        if len(ids) != len(set(ids)):
            raise ValueError("evaluation_ids must be unique within the envelope")
        return self
