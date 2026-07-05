import pytest
from pydantic import ValidationError
from datetime import datetime, timezone

from models.hybrid_task_intake_contract import (
    IntakeSourceType,
    ExtractionStatus,
    FieldResolutionStatus,
    ClarificationMode,
    IntakeDisposition,
    RawTaskIntake,
    StructuredTaskExtraction,
    ExtractedFieldRecord,
    AmbiguityRecord,
    ClarificationRequestRecord,
    IntakeValidationRecord,
    TaskIntakeDecisionRecord,
    HybridTaskIntakeEnvelope,
)


def make_raw_intake(overrides: dict = None) -> RawTaskIntake:
    base = {
        "intake_id": "intake-001",
        "source_type": IntakeSourceType.user_message,
        "raw_text": "Implement login endpoint with JWT authentication",
        "session_id": "session-042",
        "user_id": "user-shiva",
        "language": "en",
        "channel": "cli",
    }
    if overrides:
        base.update(overrides)
    return RawTaskIntake(**base)


def make_extraction(overrides: dict = None) -> StructuredTaskExtraction:
    base = {
        "extraction_id": "ext-001",
        "intake_id": "intake-001",
        "target_schema_id": "task-contract-v1",
        "extraction_status": ExtractionStatus.extracted,
        "task_type": "implementation",
        "title": "Implement login endpoint",
        "objective": "Implement login endpoint with JWT authentication",
        "constraints": ["must_not_delegate_further"],
        "deadline": "2026-07-06",
        "priority": "high",
        "requested_outputs": ["implementation", "tests"],
        "extracted_at": datetime.now(timezone.utc),
    }
    if overrides:
        base.update(overrides)
    return StructuredTaskExtraction(**base)


def make_field(overrides: dict = None) -> ExtractedFieldRecord:
    base = {
        "field_record_id": "fld-001",
        "field_name": "objective",
        "field_value_ref": "Implement login endpoint with JWT authentication",
        "resolution_status": FieldResolutionStatus.explicit,
        "confidence": 0.95,
        "source_span": "Implement login endpoint with JWT authentication",
        "extraction_reason": "Directly stated in user message",
    }
    if overrides:
        base.update(overrides)
    return ExtractedFieldRecord(**base)


def make_ambiguity(overrides: dict = None) -> AmbiguityRecord:
    base = {
        "ambiguity_id": "amb-001",
        "field_name": "deadline",
        "ambiguity_summary": "Deadline not specified in request",
        "candidate_values": ["ASAP", "end_of_sprint"],
        "impact_level": "medium",
        "clarification_needed": True,
    }
    if overrides:
        base.update(overrides)
    return AmbiguityRecord(**base)


def make_clarification(overrides: dict = None) -> ClarificationRequestRecord:
    base = {
        "clarification_id": "clr-001",
        "intake_id": "intake-001",
        "clarification_mode": ClarificationMode.ask_user,
        "questions": ["What deadline should this task have?"],
        "blocking_fields": ["deadline"],
        "recommended_defaults": {"deadline": "end_of_sprint"},
        "requested_at": datetime.now(timezone.utc),
    }
    if overrides:
        base.update(overrides)
    return ClarificationRequestRecord(**base)


def make_validation(overrides: dict = None) -> IntakeValidationRecord:
    base = {
        "validation_id": "val-001",
        "intake_id": "intake-001",
        "required_fields_checked": ["objective", "task_type", "deadline"],
        "missing_required_fields": [],
        "invalid_fields": [],
        "average_confidence": 0.92,
        "schema_valid": True,
        "review_required": False,
        "validation_summary": "All required fields present and valid",
    }
    if overrides:
        base.update(overrides)
    return IntakeValidationRecord(**base)


def make_decision(overrides: dict = None) -> TaskIntakeDecisionRecord:
    base = {
        "decision_id": "dec-001",
        "intake_id": "intake-001",
        "intake_disposition": IntakeDisposition.accepted,
        "decision_reason": "Clear request with all required fields present",
        "accepted_task_ref": "task-contract-001",
        "decided_at": datetime.now(timezone.utc),
    }
    if overrides:
        base.update(overrides)
    return TaskIntakeDecisionRecord(**base)


def make_envelope(overrides: dict = None) -> HybridTaskIntakeEnvelope:
    base = {
        "envelope_id": "env-intake-001",
        "raw_intake": make_raw_intake(),
        "structured_extraction": make_extraction(),
        "fields": [
            make_field(),
            make_field({"field_record_id": "fld-002", "field_name": "deadline",
                        "resolution_status": FieldResolutionStatus.missing,
                        "field_value_ref": None, "extraction_reason": None}),
        ],
        "validation": make_validation(),
        "decision": make_decision(),
    }
    if overrides:
        base.update(overrides)
    return HybridTaskIntakeEnvelope(**base)


class TestIntakeSourceType:
    def test_values(self):
        assert len(IntakeSourceType) == 5


class TestExtractionStatus:
    def test_values(self):
        assert len(ExtractionStatus) == 6


class TestFieldResolutionStatus:
    def test_values(self):
        assert len(FieldResolutionStatus) == 5


class TestClarificationMode:
    def test_values(self):
        assert len(ClarificationMode) == 4


class TestIntakeDisposition:
    def test_values(self):
        assert len(IntakeDisposition) == 5


class TestRawTaskIntake:
    def test_valid_raw(self):
        r = make_raw_intake()
        assert r.intake_id == "intake-001"
        assert r.raw_text == "Implement login endpoint with JWT authentication"

    def test_blank_intake_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_raw_intake({"intake_id": "   "})

    def test_no_raw_content_raises(self):
        with pytest.raises(ValidationError, match="raw_text or raw_artifact_refs must be provided"):
            make_raw_intake({"raw_text": None, "raw_artifact_refs": []})

    def test_artifact_refs_suffice(self):
        r = make_raw_intake({"raw_text": None, "raw_artifact_refs": ["specs/auth.md"]})
        assert r.raw_artifact_refs == ["specs/auth.md"]

    def test_all_source_types(self):
        for st in IntakeSourceType:
            r = make_raw_intake({"source_type": st})
            assert r.source_type == st


class TestStructuredTaskExtraction:
    def test_valid_extraction(self):
        e = make_extraction()
        assert e.extraction_id == "ext-001"
        assert e.target_schema_id == "task-contract-v1"

    def test_blank_extraction_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_extraction({"extraction_id": "   "})

    def test_blank_target_schema_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_extraction({"target_schema_id": "   "})

    def test_all_extraction_statuses(self):
        for st in ExtractionStatus:
            e = make_extraction({"extraction_status": st})
            assert e.extraction_status == st


class TestExtractedFieldRecord:
    def test_valid_field(self):
        f = make_field()
        assert f.field_name == "objective"
        assert f.confidence == 0.95

    def test_blank_field_record_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_field({"field_record_id": "   "})

    def test_blank_field_name_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_field({"field_name": "   "})

    def test_confidence_above_one_raises(self):
        with pytest.raises(ValidationError):
            make_field({"confidence": 1.5})

    def test_missing_field_with_value_raises(self):
        with pytest.raises(ValidationError, match="missing fields must not have a field_value_ref"):
            make_field({"resolution_status": FieldResolutionStatus.missing, "field_value_ref": "something"})

    def test_missing_field_without_value_ok(self):
        f = make_field({"resolution_status": FieldResolutionStatus.missing, "field_value_ref": None})
        assert f.resolution_status == FieldResolutionStatus.missing


class TestAmbiguityRecord:
    def test_valid_ambiguity(self):
        a = make_ambiguity()
        assert a.ambiguity_id == "amb-001"
        assert a.clarification_needed is True

    def test_blank_ambiguity_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_ambiguity({"ambiguity_id": "   "})

    def test_blank_field_name_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_ambiguity({"field_name": "   "})

    def test_blank_summary_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_ambiguity({"ambiguity_summary": "   "})


class TestClarificationRequestRecord:
    def test_valid_clarification(self):
        c = make_clarification()
        assert c.clarification_id == "clr-001"
        assert c.clarification_mode == ClarificationMode.ask_user

    def test_blank_clarification_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_clarification({"clarification_id": "   "})

    def test_all_modes(self):
        for m in ClarificationMode:
            c = make_clarification({"clarification_mode": m})
            assert c.clarification_mode == m


class TestIntakeValidationRecord:
    def test_valid_validation(self):
        v = make_validation()
        assert v.validation_id == "val-001"
        assert v.schema_valid is True

    def test_blank_validation_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_validation({"validation_id": "   "})

    def test_average_confidence_above_one_raises(self):
        with pytest.raises(ValidationError):
            make_validation({"average_confidence": 1.5})

    def test_with_missing_and_invalid_fields(self):
        v = make_validation({
            "missing_required_fields": ["deadline"],
            "invalid_fields": ["priority"],
            "schema_valid": False,
            "review_required": True,
        })
        assert "deadline" in v.missing_required_fields


class TestTaskIntakeDecisionRecord:
    def test_valid_decision(self):
        d = make_decision()
        assert d.intake_disposition == IntakeDisposition.accepted

    def test_blank_decision_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_decision({"decision_id": "   "})

    def test_accepted_must_have_reason(self):
        with pytest.raises(ValidationError, match="accepted disposition must include decision_reason"):
            make_decision({"intake_disposition": IntakeDisposition.accepted, "decision_reason": None})

    def test_accepted_with_gaps_must_have_reason(self):
        with pytest.raises(ValidationError, match="accepted disposition must include decision_reason"):
            make_decision({"intake_disposition": IntakeDisposition.accepted_with_gaps, "decision_reason": None})


class TestHybridTaskIntakeEnvelope:
    def test_valid_envelope(self):
        env = make_envelope()
        assert env.envelope_id == "env-intake-001"
        assert len(env.fields) == 2

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_envelope({"envelope_id": "   "})

    def test_ambiguity_unknown_field_raises(self):
        with pytest.raises(ValidationError, match="references unknown field"):
            make_envelope({
                "ambiguities": [make_ambiguity({"field_name": "nonexistent_field"})],
            })

    def test_ambiguity_valid_field_ok(self):
        env = make_envelope({
            "ambiguities": [make_ambiguity({"field_name": "deadline"})],
        })
        assert len(env.ambiguities) == 1

    def test_accepted_without_schema_valid_raises(self):
        with pytest.raises(ValidationError, match="accepted disposition requires schema_valid"):
            make_envelope({
                "validation": make_validation({"schema_valid": False}),
            })

    def test_accepted_with_gaps_without_schema_valid_raises(self):
        with pytest.raises(ValidationError, match="accepted disposition requires schema_valid"):
            make_envelope({
                "decision": make_decision({"intake_disposition": IntakeDisposition.accepted_with_gaps}),
                "validation": make_validation({"schema_valid": False}),
            })

    def test_clarification_required_missing_request_raises(self):
        with pytest.raises(ValidationError, match="clarification_required must include a clarification_request"):
            make_envelope({
                "decision": make_decision({
                    "intake_disposition": IntakeDisposition.clarification_required,
                    "decision_reason": "Needs clarification on deadline",
                }),
            })

    def test_clarification_required_with_request_ok(self):
        env = make_envelope({
            "decision": make_decision({
                "intake_disposition": IntakeDisposition.clarification_required,
                "decision_reason": "Needs clarification on deadline",
            }),
            "clarification_request": make_clarification(),
            "validation": make_validation({"schema_valid": False}),
        })
        assert env.decision.intake_disposition == IntakeDisposition.clarification_required

    def test_missing_required_fields_block_acceptance(self):
        with pytest.raises(ValidationError, match="missing required fields block unconditional acceptance"):
            make_envelope({
                "validation": make_validation({"missing_required_fields": ["deadline"]}),
            })


class TestIntegrationExamples:
    def test_clear_request_accepted(self):
        env = make_envelope()
        assert env.decision.intake_disposition == IntakeDisposition.accepted
        assert env.validation.schema_valid is True

    def test_ambiguous_request_clarification(self):
        env = make_envelope({
            "envelope_id": "env-intake-002",
            "fields": [
                make_field(),
                make_field({"field_record_id": "fld-002", "field_name": "deadline",
                            "resolution_status": FieldResolutionStatus.ambiguous, "confidence": 0.3}),
            ],
            "ambiguities": [make_ambiguity({"field_name": "deadline"})],
            "validation": make_validation({
                "missing_required_fields": ["deadline"],
                "average_confidence": 0.6,
                "schema_valid": False,
            }),
            "decision": make_decision({
                "decision_id": "dec-002",
                "intake_disposition": IntakeDisposition.clarification_required,
                "decision_reason": "Deadline is ambiguous, needs clarification",
            }),
            "clarification_request": make_clarification(),
        })
        assert env.decision.intake_disposition == IntakeDisposition.clarification_required
        assert env.validation.schema_valid is False

    def test_partial_extraction_accepted_with_gaps(self):
        env = make_envelope({
            "envelope_id": "env-intake-003",
            "fields": [
                make_field(),
            make_field({"field_record_id": "fld-002", "field_name": "deadline",
                             "resolution_status": FieldResolutionStatus.missing,
                             "field_value_ref": None, "extraction_reason": None}),
            ],
            "validation": make_validation({
                "missing_required_fields": ["deadline"],
                "average_confidence": 0.75,
                "schema_valid": True,
            }),
            "decision": make_decision({
                "decision_id": "dec-003",
                "intake_disposition": IntakeDisposition.accepted_with_gaps,
                "decision_reason": "Objective clear, deadline missing but can use default",
            }),
        })
        assert env.decision.intake_disposition == IntakeDisposition.accepted_with_gaps
        assert "deadline" in env.validation.missing_required_fields

    def test_invalid_extraction_rejected(self):
        env = make_envelope({
            "envelope_id": "env-intake-004",
            "fields": [
                make_field({"field_record_id": "fld-001", "field_name": "objective",
                            "resolution_status": FieldResolutionStatus.invalid, "confidence": 0.1}),
            ],
            "validation": make_validation({
                "invalid_fields": ["objective"],
                "average_confidence": 0.1,
                "schema_valid": False,
                "review_required": True,
            }),
            "decision": make_decision({
                "decision_id": "dec-004",
                "intake_disposition": IntakeDisposition.rejected,
                "decision_reason": "Objective field invalid, cannot proceed",
            }),
        })
        assert env.decision.intake_disposition == IntakeDisposition.rejected
        assert env.validation.schema_valid is False

    def test_mixed_input_with_artifact_refs(self):
        env = make_envelope({
            "envelope_id": "env-intake-005",
            "raw_intake": make_raw_intake({
                "intake_id": "intake-005",
                "source_type": IntakeSourceType.mixed_input,
                "raw_text": "Implement the auth module following the attached spec",
                "raw_artifact_refs": ["specs/auth_module.md"],
                "session_id": "session-050",
            }),
            "fields": [
                make_field(),
                make_field({"field_record_id": "fld-002", "field_name": "deadline",
                             "resolution_status": FieldResolutionStatus.missing,
                             "field_value_ref": None, "extraction_reason": None}),
            ],
            "validation": make_validation({
                "average_confidence": 0.85,
                "schema_valid": True,
            }),
            "decision": make_decision({
                "decision_id": "dec-005",
                "decision_reason": "Clear objective with spec artifact; deadline deferred",
            }),
        })
        assert env.raw_intake.source_type == IntakeSourceType.mixed_input
        assert "specs/auth_module.md" in env.raw_intake.raw_artifact_refs
