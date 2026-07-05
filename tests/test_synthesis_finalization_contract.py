import pytest
from pydantic import ValidationError
from datetime import datetime, timezone

from models.synthesis_finalization_contract import (
    SynthesisInputType,
    NormalizationMode,
    SynthesisPolicy,
    FinalizationStatus,
    FinalDisposition,
    SynthesisSourceRecord,
    NormalizationRecord,
    SynthesisConflictRecord,
    SynthesisDecisionRecord,
    ValidationSummaryRecord,
    FinalizationRecord,
    SynthesisOutputRecord,
    SynthesisFinalizationEnvelope,
)


def make_source(source_id: str = "src-001", overrides: dict = None) -> SynthesisSourceRecord:
    base = {
        "source_id": source_id,
        "source_type": SynthesisInputType.branch_output,
        "source_ref": "bo-login-001",
        "origin_agent_id": "agent-coder-01",
        "eligibility_status": "accepted",
        "confidence": 0.9,
    }
    if overrides:
        base.update(overrides)
    return SynthesisSourceRecord(**base)


def make_normalization(overrides: dict = None) -> NormalizationRecord:
    base = {
        "normalization_id": "norm-001",
        "source_id": "src-001",
        "normalization_mode": NormalizationMode.schema_map,
        "input_ref": "bo-login-001",
        "normalized_ref": "norm/login-001.json",
        "notes": "Mapped to canonical auth module schema",
    }
    if overrides:
        base.update(overrides)
    return NormalizationRecord(**base)


def make_conflict(overrides: dict = None) -> SynthesisConflictRecord:
    base = {
        "conflict_id": "conf-001",
        "source_ids": ["src-001", "src-002"],
        "conflict_summary": "Two branch outputs disagree on error handling approach",
        "resolved": False,
        "review_required": True,
    }
    if overrides:
        base.update(overrides)
    return SynthesisConflictRecord(**base)


def make_decision(overrides: dict = None) -> SynthesisDecisionRecord:
    base = {
        "decision_id": "dec-001",
        "synthesis_policy": SynthesisPolicy.merge_all_accepted,
        "selected_source_ids": ["src-001", "src-002"],
        "rejected_source_ids": [],
        "decision_reason": "Both outputs are consistent and complementary",
        "decision_made_at": datetime.now(timezone.utc),
    }
    if overrides:
        base.update(overrides)
    return SynthesisDecisionRecord(**base)


def make_validation_summary(overrides: dict = None) -> ValidationSummaryRecord:
    base = {
        "validation_summary_id": "vs-001",
        "checks_passed": ["schema_check", "confidence_check", "consistency_check"],
        "checks_failed": [],
        "quality_score": 0.92,
        "review_required": False,
        "summary": "All checks passed, output is consistent and high quality",
    }
    if overrides:
        base.update(overrides)
    return ValidationSummaryRecord(**base)


def make_finalization(overrides: dict = None) -> FinalizationRecord:
    base = {
        "finalization_id": "fin-001",
        "finalization_status": FinalizationStatus.approved,
        "final_disposition": FinalDisposition.accept,
        "approved_by": "agent-mgr-01",
        "approval_reason": "Both branches completed successfully with consistent outputs",
        "release_ready": True,
        "finalized_at": datetime.now(timezone.utc),
    }
    if overrides:
        base.update(overrides)
    return FinalizationRecord(**base)


def make_output(overrides: dict = None) -> SynthesisOutputRecord:
    base = {
        "output_id": "out-001",
        "output_type": "merged_implementation",
        "result_summary": "Login and registration endpoints merged into single auth module",
        "final_output_refs": ["src/auth/login.py", "src/auth/register.py"],
        "supporting_evidence_refs": ["tests/test_login.py", "tests/test_register.py"],
        "residual_uncertainties": ["Email verification template path may need config"],
    }
    if overrides:
        base.update(overrides)
    return SynthesisOutputRecord(**base)


def make_envelope(overrides: dict = None) -> SynthesisFinalizationEnvelope:
    base = {
        "envelope_id": "env-syn-001",
        "sources": [make_source("src-001"), make_source("src-002")],
        "decision": make_decision(),
        "validation_summary": make_validation_summary(),
        "finalization": make_finalization(),
        "output": make_output(),
    }
    if overrides:
        base.update(overrides)
    return SynthesisFinalizationEnvelope(**base)


class TestSynthesisInputType:
    def test_values(self):
        assert len(SynthesisInputType) == 7
        assert SynthesisInputType.branch_output.value == "branch_output"
        assert SynthesisInputType.evidence_bundle.value == "evidence_bundle"


class TestNormalizationMode:
    def test_values(self):
        assert len(NormalizationMode) == 5
        assert NormalizationMode.canonicalize.value == "canonicalize"


class TestSynthesisPolicy:
    def test_values(self):
        assert len(SynthesisPolicy) == 5
        assert SynthesisPolicy.merge_ranked_subset.value == "merge_ranked_subset"


class TestFinalizationStatus:
    def test_values(self):
        assert len(FinalizationStatus) == 7
        assert FinalizationStatus.released.value == "released"


class TestFinalDisposition:
    def test_values(self):
        assert len(FinalDisposition) == 5
        assert FinalDisposition.accept_with_caveats.value == "accept_with_caveats"


class TestSynthesisSourceRecord:
    def test_valid_source(self):
        s = make_source()
        assert s.source_id == "src-001"
        assert s.eligibility_status == "accepted"

    def test_blank_source_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_source(source_id="   ")

    def test_blank_source_ref_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_source(overrides={"source_ref": "   "})

    def test_blank_eligibility_status_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_source(overrides={"eligibility_status": "   "})

    def test_confidence_above_one_raises(self):
        with pytest.raises(ValidationError):
            make_source(overrides={"confidence": 1.5})

    def test_confidence_below_zero_raises(self):
        with pytest.raises(ValidationError):
            make_source(overrides={"confidence": -0.1})

    def test_all_input_types(self):
        for t in SynthesisInputType:
            s = make_source(overrides={"source_type": t})
            assert s.source_type == t


class TestNormalizationRecord:
    def test_valid_normalization(self):
        n = make_normalization()
        assert n.normalization_id == "norm-001"
        assert n.normalization_mode == NormalizationMode.schema_map

    def test_blank_normalization_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_normalization({"normalization_id": "   "})

    def test_blank_input_ref_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_normalization({"input_ref": "   "})

    def test_blank_normalized_ref_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_normalization({"normalized_ref": "   "})

    def test_all_modes(self):
        for m in NormalizationMode:
            n = make_normalization({"normalization_mode": m})
            assert n.normalization_mode == m


class TestSynthesisConflictRecord:
    def test_valid_conflict(self):
        c = make_conflict()
        assert c.conflict_id == "conf-001"
        assert c.resolved is False

    def test_blank_conflict_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_conflict({"conflict_id": "   "})

    def test_blank_conflict_summary_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_conflict({"conflict_summary": "   "})

    def test_duplicate_source_ids_raises(self):
        with pytest.raises(ValidationError, match="must be unique"):
            make_conflict({"source_ids": ["src-001", "src-001"]})

    def test_less_than_two_source_ids_raises(self):
        with pytest.raises(ValidationError):
            make_conflict({"source_ids": ["src-001"]})

    def test_resolved_with_notes(self):
        c = make_conflict({"resolved": True, "resolution_strategy": "take_higher_confidence",
                           "resolution_notes": "Chose src-002 output based on confidence score"})
        assert c.resolved is True


class TestSynthesisDecisionRecord:
    def test_valid_decision(self):
        d = make_decision()
        assert d.decision_id == "dec-001"
        assert d.synthesis_policy == SynthesisPolicy.merge_all_accepted

    def test_blank_decision_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_decision({"decision_id": "   "})

    def test_all_policies(self):
        for p in SynthesisPolicy:
            d = make_decision({"synthesis_policy": p})
            assert d.synthesis_policy == p

    def test_with_rejected_sources(self):
        d = make_decision({
            "rejected_source_ids": ["src-003"],
            "decision_reason": "Confidence too low for src-003",
        })
        assert "src-003" in d.rejected_source_ids


class TestValidationSummaryRecord:
    def test_valid_summary(self):
        vs = make_validation_summary()
        assert vs.validation_summary_id == "vs-001"
        assert vs.quality_score == 0.92

    def test_blank_validation_summary_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_validation_summary({"validation_summary_id": "   "})

    def test_quality_score_above_one_raises(self):
        with pytest.raises(ValidationError):
            make_validation_summary({"quality_score": 1.5})

    def test_quality_score_below_zero_raises(self):
        with pytest.raises(ValidationError):
            make_validation_summary({"quality_score": -0.1})

    def test_with_failed_checks(self):
        vs = make_validation_summary({
            "checks_failed": ["consistency_check"],
            "evidence_gaps": ["missing_performance_benchmark"],
            "review_required": True,
        })
        assert len(vs.checks_failed) == 1


class TestFinalizationRecord:
    def test_valid_finalization(self):
        f = make_finalization()
        assert f.finalization_id == "fin-001"
        assert f.finalization_status == FinalizationStatus.approved

    def test_blank_finalization_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_finalization({"finalization_id": "   "})

    def test_rework_without_reason_raises(self):
        with pytest.raises(ValidationError, match="must include approval_reason"):
            make_finalization({
                "final_disposition": FinalDisposition.return_for_rework,
                "approval_reason": None,
            })

    def test_reject_without_reason_raises(self):
        with pytest.raises(ValidationError, match="must include approval_reason"):
            make_finalization({
                "final_disposition": FinalDisposition.reject,
                "approval_reason": None,
            })

    def test_accept_without_reason_raises(self):
        with pytest.raises(ValidationError, match="must include approval_reason"):
            make_finalization({
                "final_disposition": FinalDisposition.accept,
                "approval_reason": None,
            })

    def test_accept_with_caveats_without_reason_raises(self):
        with pytest.raises(ValidationError, match="must include approval_reason"):
            make_finalization({
                "final_disposition": FinalDisposition.accept_with_caveats,
                "approval_reason": None,
            })

    def test_released_without_release_ready_raises(self):
        with pytest.raises(ValidationError, match="released status requires release_ready=True"):
            make_finalization({
                "finalization_status": FinalizationStatus.released,
                "release_ready": False,
            })

    def test_released_with_release_ready_ok(self):
        f = make_finalization({
            "finalization_status": FinalizationStatus.released,
            "release_ready": True,
        })
        assert f.finalization_status == FinalizationStatus.released

    def test_all_statuses(self):
        for st in FinalizationStatus:
            if st == FinalizationStatus.released:
                f = make_finalization({"finalization_status": st, "release_ready": True})
            else:
                f = make_finalization({"finalization_status": st})
            assert f.finalization_status == st

    def test_all_dispositions(self):
        for d in FinalDisposition:
            reason = "Reason for disposition"
            f = make_finalization({"final_disposition": d, "approval_reason": reason})
            assert f.final_disposition == d


class TestSynthesisOutputRecord:
    def test_valid_output(self):
        o = make_output()
        assert o.output_id == "out-001"
        assert len(o.final_output_refs) == 2

    def test_blank_output_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_output({"output_id": "   "})

    def test_blank_result_summary_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_output({"result_summary": "   "})

    def test_with_residual_uncertainties(self):
        o = make_output({"residual_uncertainties": ["Email template path unclear", "Rate limit config pending"]})
        assert len(o.residual_uncertainties) == 2


class TestSynthesisFinalizationEnvelope:
    def test_valid_envelope(self):
        env = make_envelope()
        assert env.envelope_id == "env-syn-001"
        assert len(env.sources) == 2

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_envelope({"envelope_id": "   "})

    def test_no_eligible_sources_raises(self):
        with pytest.raises(ValidationError, match="at least one source must be eligible"):
            make_envelope({
                "sources": [
                    make_source("src-001", {"eligibility_status": "rejected"}),
                    make_source("src-002", {"eligibility_status": "rejected"}),
                ]
            })

    def test_accept_disposition_without_output_refs_raises(self):
        with pytest.raises(ValidationError, match="accept disposition requires at least one final_output_ref"):
            make_envelope({
                "output": make_output({"final_output_refs": []}),
            })

    def test_unresolved_conflicts_must_set_review_required(self):
        with pytest.raises(ValidationError, match="unresolved conflicts must set review_required"):
            make_envelope({
                "conflicts": [make_conflict()],
            })

    def test_unresolved_conflicts_with_review_required_ok(self):
        env = make_envelope({
            "conflicts": [make_conflict()],
            "validation_summary": make_validation_summary({"review_required": True}),
        })
        assert len(env.conflicts) == 1
        assert env.validation_summary.review_required is True

    def test_resolved_conflicts_no_review_required_ok(self):
        env = make_envelope({
            "conflicts": [make_conflict({"resolved": True, "review_required": False})],
        })
        assert env.conflicts[0].resolved is True

    def test_released_envelope_ok(self):
        env = make_envelope({
            "finalization": make_finalization({
                "finalization_status": FinalizationStatus.released,
                "release_ready": True,
            }),
        })
        assert env.finalization.finalization_status == FinalizationStatus.released

    def test_rejected_only_cannot_be_approved(self):
        env = make_envelope()
        for s in env.sources:
            s.eligibility_status = "rejected"
        with pytest.raises(ValueError, match="rejected-only inputs cannot become approved"):
            env.check_rejected_only_cannot_approve()


class TestIntegrationExamples:
    def test_two_accepted_outputs_merged(self):
        env = make_envelope()
        assert env.finalization.final_disposition == FinalDisposition.accept
        assert len(env.output.final_output_refs) >= 1

    def test_ranked_subset_with_rejected_source(self):
        env = make_envelope({
            "envelope_id": "env-syn-002",
            "sources": [
                make_source("src-001", {"confidence": 0.95}),
                make_source("src-002", {"confidence": 0.85}),
                make_source("src-003", {"confidence": 0.45}),
            ],
            "decision": make_decision({
                "decision_id": "dec-002",
                "synthesis_policy": SynthesisPolicy.merge_ranked_subset,
                "selected_source_ids": ["src-001", "src-002"],
                "rejected_source_ids": ["src-003"],
                "decision_reason": "src-003 confidence too low (0.45 < 0.5 threshold)",
            }),
        })
        assert len(env.decision.rejected_source_ids) == 1
        assert env.decision.synthesis_policy == SynthesisPolicy.merge_ranked_subset

    def test_unresolved_conflict_needs_rework(self):
        env = make_envelope({
            "envelope_id": "env-syn-003",
            "sources": [
                make_source("src-001", {"source_ref": "output-A", "confidence": 0.8}),
                make_source("src-002", {"source_ref": "output-B", "confidence": 0.7}),
            ],
            "conflicts": [make_conflict()],
            "validation_summary": make_validation_summary({
                "validation_summary_id": "vs-003",
                "review_required": True,
                "quality_score": 0.5,
                "summary": "Unresolved conflict between src-001 and src-002 on error handling",
            }),
            "finalization": make_finalization({
                "finalization_id": "fin-003",
                "finalization_status": FinalizationStatus.needs_rework,
                "final_disposition": FinalDisposition.return_for_rework,
                "approval_reason": "Conflicts must be resolved before finalization",
                "release_ready": False,
            }),
        })
        assert env.finalization.finalization_status == FinalizationStatus.needs_rework
        assert env.validation_summary.review_required is True

    def test_verification_first_synthesis(self):
        env = make_envelope({
            "envelope_id": "env-syn-004",
            "sources": [
                make_source("src-001", {"source_type": SynthesisInputType.verification_report,
                                         "source_ref": "report-security.md", "confidence": 0.95}),
                make_source("src-002", {"source_type": SynthesisInputType.verification_report,
                                         "source_ref": "report-perf.md", "confidence": 0.88}),
            ],
            "decision": make_decision({
                "decision_id": "dec-004",
                "synthesis_policy": SynthesisPolicy.verification_first,
                "selected_source_ids": ["src-001", "src-002"],
                "decision_reason": "Both verification reports passed",
            }),
        })
        assert env.decision.synthesis_policy == SynthesisPolicy.verification_first
        assert len(env.decision.selected_source_ids) == 2

    def test_caveats_and_residual_uncertainties(self):
        env = make_envelope({
            "envelope_id": "env-syn-005",
            "finalization": make_finalization({
                "finalization_id": "fin-005",
                "finalization_status": FinalizationStatus.approved,
                "final_disposition": FinalDisposition.accept_with_caveats,
                "approval_reason": "Output accepted but email verification template needs config fix",
                "release_ready": True,
                "followup_required": True,
            }),
            "output": make_output({
                "output_id": "out-005",
                "residual_uncertainties": ["Email verification template path may need config"],
                "consumer_notes": "Verify EMAIL_TEMPLATE_PATH env var before deploying",
            }),
        })
        assert env.finalization.final_disposition == FinalDisposition.accept_with_caveats
        assert env.finalization.followup_required is True
        assert len(env.output.residual_uncertainties) == 1


class TestEdgeCases:
    def test_confidence_none_allowed(self):
        s = make_source(overrides={"confidence": None})
        assert s.confidence is None

    def test_empty_evidence_refs_allowed(self):
        s = make_source(overrides={"evidence_refs": []})
        assert s.evidence_refs == []

    def test_normalization_notes_optional(self):
        n = make_normalization({"notes": None})
        assert n.notes is None

    def test_decision_with_all_fields(self):
        d = make_decision({
            "editorial_notes": "Manually reviewed both outputs, consistent",
        })
        assert d.editorial_notes is not None

    def test_validation_with_evidence_gaps(self):
        vs = make_validation_summary({
            "evidence_gaps": ["No load test results"],
        })
        assert "No load test results" in vs.evidence_gaps

    def test_output_empty_uncertainties_allowed(self):
        o = make_output({"residual_uncertainties": []})
        assert o.residual_uncertainties == []

    def test_source_with_all_types(self):
        s = make_source(overrides={
            "source_type": SynthesisInputType.state_delta,
            "priority": "high",
            "selection_reason": "Contains critical state changes",
        })
        assert s.priority == "high"
