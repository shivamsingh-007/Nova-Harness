import pytest
from datetime import datetime
from models.clarification_resolution_contract import (
    GapType, GapSeverity, ResolutionMethod, ResolutionStatus,
    ClarificationDisposition,
    MissingInfoGapRecord, ClarificationQuestionRecord,
    ResolutionAttemptRecord, FieldResolutionRecord,
    ResolutionPolicyRecord, ClarificationSessionRecord,
    ClarificationDecisionRecord, ClarificationResolutionEnvelope,
)


# ── Helpers ──────────────────────────────────────────────────────────────

def make_gap(blocking=False, severity=GapSeverity.medium, **kw):
    return MissingInfoGapRecord(
        gap_id=kw.get("gap_id", "gap-001"),
        intake_id=kw.get("intake_id", "intake-001"),
        field_name=kw.get("field_name", "deadline"),
        gap_type=kw.get("gap_type", GapType.missing_required),
        gap_severity=severity,
        blocking=blocking,
        gap_summary=kw.get("gap_summary", "Deadline is missing"),
    )


def make_question(gap_id="gap-001", **kw):
    return ClarificationQuestionRecord(
        question_id=kw.get("question_id", "q-001"),
        gap_id=gap_id,
        field_name=kw.get("field_name", "deadline"),
        question_text=kw.get("question_text", "What is the deadline?"),
        question_order=kw.get("question_order", 0),
    )


def make_attempt(gap_id="gap-001", method=ResolutionMethod.ask_user, **kw):
    return ResolutionAttemptRecord(
        attempt_id=kw.get("attempt_id", "att-001"),
        gap_id=gap_id,
        resolution_method=method,
        proposed_value_ref=kw.get("proposed_value_ref", "2026-07-07"),
        confidence=kw.get("confidence"),
        attempt_reason=kw.get("attempt_reason"),
    )


def make_field_resolution(gap_id="gap-001", status=ResolutionStatus.resolved, **kw):
    return FieldResolutionRecord(
        field_resolution_id=kw.get("fr_id", "fr-001"),
        gap_id=gap_id,
        resolution_method=kw.get("method", ResolutionMethod.ask_user),
        resolution_status=status,
        resolved_value_ref=kw.get("resolved_value_ref", "2026-07-07"),
        notes=kw.get("notes"),
    )


def make_policy(**kw):
    return ResolutionPolicyRecord(
        policy_id=kw.get("policy_id", "pol-001"),
        field_name=kw.get("field_name", "deadline"),
        required=kw.get("required", True),
        allow_default=kw.get("allow_default", False),
        allow_inference=kw.get("allow_inference", False),
        allow_defer=kw.get("allow_defer", False),
        escalation_threshold=kw.get("escalation_threshold"),
        max_attempts=kw.get("max_attempts"),
    )


def make_session(gap_ids=None, active_qs=None, completed_qs=None, **kw):
    return ClarificationSessionRecord(
        clarification_session_id=kw.get("sid", "cs-001"),
        intake_id=kw.get("intake_id", "intake-001"),
        related_gap_ids=gap_ids if gap_ids is not None else ["gap-001"],
        active_question_ids=active_qs if active_qs is not None else [],
        completed_question_ids=completed_qs if completed_qs is not None else [],
        session_status=kw.get("status", "in_progress"),
    )


def make_decision(disposition=ClarificationDisposition.ready_to_proceed, **kw):
    return ClarificationDecisionRecord(
        decision_id=kw.get("did", "dec-001"),
        clarification_session_id=kw.get("sid", "cs-001"),
        clarification_disposition=disposition,
        remaining_open_gap_ids=kw.get("open_gaps", []),
        decision_reason=kw.get("reason", "All gaps resolved"),
    )


def make_envelope(**kw):
    gaps = kw.get("gaps", [make_gap()])
    questions = kw.get("questions", [])
    attempts = kw.get("attempts", [])
    field_resolutions = kw.get("field_resolutions", [make_field_resolution()])
    policies = kw.get("policies", [make_policy()])
    session = kw.get("session") or make_session(
        gap_ids=[g.gap_id for g in gaps],
        active_qs=[q.question_id for q in questions if kw.get("active_questions", False)],
    )
    decision = kw.get("decision") or make_decision()
    return ClarificationResolutionEnvelope(
        envelope_id=kw.get("eid", "env-clar-001"),
        gaps=gaps,
        questions=questions,
        attempts=attempts,
        field_resolutions=field_resolutions,
        policies=policies,
        session=session,
        decision=decision,
    )


# ── Tests ────────────────────────────────────────────────────────────────

class TestGapType:
    def test_all_values(self):
        assert len(GapType) == 6
        assert GapType.missing_required.value == "missing_required"
        assert GapType.missing_optional.value == "missing_optional"
        assert GapType.ambiguous_value.value == "ambiguous_value"
        assert GapType.invalid_value.value == "invalid_value"
        assert GapType.conflicting_values.value == "conflicting_values"
        assert GapType.unsupported_request.value == "unsupported_request"


class TestGapSeverity:
    def test_all_values(self):
        assert len(GapSeverity) == 4
        assert GapSeverity.low.value == "low"
        assert GapSeverity.medium.value == "medium"
        assert GapSeverity.high.value == "high"
        assert GapSeverity.blocking.value == "blocking"


class TestResolutionMethod:
    def test_all_values(self):
        assert len(ResolutionMethod) == 6
        assert ResolutionMethod.ask_user.value == "ask_user"
        assert ResolutionMethod.infer_from_context.value == "infer_from_context"
        assert ResolutionMethod.apply_default.value == "apply_default"
        assert ResolutionMethod.manual_override.value == "manual_override"
        assert ResolutionMethod.defer.value == "defer"
        assert ResolutionMethod.escalate.value == "escalate"


class TestResolutionStatus:
    def test_all_values(self):
        assert len(ResolutionStatus) == 7
        assert ResolutionStatus.open.value == "open"
        assert ResolutionStatus.question_issued.value == "question_issued"
        assert ResolutionStatus.answered.value == "answered"
        assert ResolutionStatus.resolved.value == "resolved"
        assert ResolutionStatus.deferred.value == "deferred"
        assert ResolutionStatus.escalated.value == "escalated"
        assert ResolutionStatus.closed_unresolved.value == "closed_unresolved"


class TestClarificationDisposition:
    def test_all_values(self):
        assert len(ClarificationDisposition) == 5
        assert ClarificationDisposition.ready_to_proceed.value == "ready_to_proceed"
        assert ClarificationDisposition.proceed_with_gaps.value == "proceed_with_gaps"
        assert ClarificationDisposition.awaiting_response.value == "awaiting_response"
        assert ClarificationDisposition.rejected.value == "rejected"
        assert ClarificationDisposition.escalated.value == "escalated"


class TestMissingInfoGapRecord:
    def test_valid_gap(self):
        g = make_gap()
        assert g.gap_id == "gap-001"
        assert g.blocking is False

    def test_blank_gap_id_raises(self):
        with pytest.raises(ValueError):
            make_gap(gap_id="  ")

    def test_blank_intake_id_raises(self):
        with pytest.raises(ValueError):
            make_gap(intake_id="  ")

    def test_blank_field_name_raises(self):
        with pytest.raises(ValueError):
            make_gap(field_name="  ")

    def test_blank_gap_summary_raises(self):
        with pytest.raises(ValueError):
            make_gap(gap_summary="  ")

    def test_blocking_severity_requires_blocking_true(self):
        with pytest.raises(ValueError):
            make_gap(severity=GapSeverity.blocking, blocking=False)

    def test_blocking_severity_with_blocking_true_ok(self):
        g = make_gap(severity=GapSeverity.blocking, blocking=True)
        assert g.blocking is True
        assert g.gap_severity == GapSeverity.blocking

    def test_non_blocking_severity_with_blocking_false_ok(self):
        g = make_gap(severity=GapSeverity.low, blocking=False)
        assert g.blocking is False

    def test_candidate_values_optional(self):
        g = make_gap()
        assert g.candidate_values == []

    def test_all_gap_types(self):
        for gt in GapType:
            g = make_gap(gap_type=gt)
            assert g.gap_type == gt


class TestClarificationQuestionRecord:
    def test_valid_question(self):
        q = make_question()
        assert q.question_id == "q-001"

    def test_blank_question_id_raises(self):
        with pytest.raises(ValueError):
            make_question(question_id="  ")

    def test_blank_gap_id_raises(self):
        with pytest.raises(ValueError):
            make_question(gap_id="  ")

    def test_blank_field_name_raises(self):
        with pytest.raises(ValueError):
            make_question(field_name="  ")

    def test_blank_question_text_raises(self):
        with pytest.raises(ValueError):
            make_question(question_text="  ")

    def test_question_order_default_zero(self):
        q = make_question()
        assert q.question_order == 0

    def test_question_order_negative_raises(self):
        with pytest.raises(ValueError):
            make_question(question_order=-1)

    def test_recommended_examples_optional(self):
        q = make_question()
        assert q.recommended_examples == []

    def test_response_type_optional(self):
        q = make_question()
        assert q.response_type is None


class TestResolutionAttemptRecord:
    def test_valid_attempt_ask_user(self):
        a = make_attempt()
        assert a.attempt_id == "att-001"

    def test_blank_attempt_id_raises(self):
        with pytest.raises(ValueError):
            make_attempt(attempt_id="  ")

    def test_blank_gap_id_raises(self):
        with pytest.raises(ValueError):
            make_attempt(gap_id="  ")

    def test_ask_user_needs_proposed_value(self):
        with pytest.raises(ValueError):
            make_attempt(proposed_value_ref=None)

    def test_defer_does_not_need_value(self):
        a = make_attempt(method=ResolutionMethod.defer, proposed_value_ref=None)
        assert a.resolution_method == ResolutionMethod.defer

    def test_escalate_does_not_need_value(self):
        a = make_attempt(method=ResolutionMethod.escalate, proposed_value_ref=None)
        assert a.resolution_method == ResolutionMethod.escalate

    def test_infer_from_context_needs_value(self):
        with pytest.raises(ValueError):
            make_attempt(method=ResolutionMethod.infer_from_context, proposed_value_ref=None)

    def test_apply_default_needs_value(self):
        with pytest.raises(ValueError):
            make_attempt(method=ResolutionMethod.apply_default, proposed_value_ref=None)

    def test_manual_override_needs_value(self):
        with pytest.raises(ValueError):
            make_attempt(method=ResolutionMethod.manual_override, proposed_value_ref=None)

    def test_confidence_bounds(self):
        with pytest.raises(ValueError):
            make_attempt(confidence=1.5)
        with pytest.raises(ValueError):
            make_attempt(confidence=-0.1)
        a = make_attempt(confidence=0.85)
        assert a.confidence == 0.85


class TestFieldResolutionRecord:
    def test_valid_resolution(self):
        fr = make_field_resolution()
        assert fr.field_resolution_id == "fr-001"

    def test_blank_resolution_id_raises(self):
        with pytest.raises(ValueError):
            make_field_resolution(fr_id="  ")

    def test_blank_gap_id_raises(self):
        with pytest.raises(ValueError):
            make_field_resolution(gap_id="  ")

    def test_resolved_needs_value_or_notes(self):
        with pytest.raises(ValueError):
            make_field_resolution(resolved_value_ref=None, notes=None)

    def test_resolved_with_notes_ok(self):
        fr = make_field_resolution(resolved_value_ref=None, notes="Overridden by manager")
        assert fr.notes == "Overridden by manager"

    def test_deferred_needs_value_or_notes(self):
        with pytest.raises(ValueError):
            make_field_resolution(status=ResolutionStatus.deferred, resolved_value_ref=None, notes=None)

    def test_open_does_not_need_value(self):
        fr = make_field_resolution(status=ResolutionStatus.open, resolved_value_ref=None, notes=None)
        assert fr.resolution_status == ResolutionStatus.open

    def test_question_issued_does_not_need_value(self):
        fr = make_field_resolution(
            status=ResolutionStatus.question_issued, resolved_value_ref=None, notes=None
        )
        assert fr.resolution_status == ResolutionStatus.question_issued

    def test_answered_does_not_need_value(self):
        fr = make_field_resolution(
            status=ResolutionStatus.answered, resolved_value_ref=None, notes=None
        )
        assert fr.resolution_status == ResolutionStatus.answered


class TestResolutionPolicyRecord:
    def test_valid_policy(self):
        p = make_policy()
        assert p.policy_id == "pol-001"

    def test_blank_policy_id_raises(self):
        with pytest.raises(ValueError):
            make_policy(policy_id="  ")

    def test_blank_field_name_raises(self):
        with pytest.raises(ValueError):
            make_policy(field_name="  ")

    def test_max_attempts_positive(self):
        with pytest.raises(ValueError):
            make_policy(max_attempts=0)
        p = make_policy(max_attempts=3)
        assert p.max_attempts == 3

    def test_escalation_threshold_positive(self):
        with pytest.raises(ValueError):
            make_policy(escalation_threshold=0)
        p = make_policy(escalation_threshold=2)
        assert p.escalation_threshold == 2

    def test_required_with_allow_defer_needs_escalation_threshold(self):
        with pytest.raises(ValueError):
            make_policy(required=True, allow_defer=True, escalation_threshold=None)

    def test_required_with_allow_defer_and_threshold_ok(self):
        p = make_policy(required=True, allow_defer=True, escalation_threshold=3)
        assert p.allow_defer is True

    def test_optional_with_allow_defer_no_threshold_ok(self):
        p = make_policy(required=False, allow_defer=True, escalation_threshold=None)
        assert p.allow_defer is True

    def test_defaults(self):
        p = make_policy()
        assert p.required is True
        assert p.allow_default is False
        assert p.allow_inference is False
        assert p.allow_defer is False


class TestClarificationSessionRecord:
    def test_valid_session(self):
        s = make_session()
        assert s.clarification_session_id == "cs-001"

    def test_blank_session_id_raises(self):
        with pytest.raises(ValueError):
            make_session(sid="  ")

    def test_blank_intake_id_raises(self):
        with pytest.raises(ValueError):
            make_session(intake_id="  ")

    def test_invalid_session_status_raises(self):
        with pytest.raises(ValueError):
            make_session(status="bogus")

    def test_valid_status_values(self):
        for st in ("in_progress", "completed", "escalated", "closed"):
            s = make_session(status=st)
            assert s.session_status == st

    def test_overlapping_active_and_completed_raises(self):
        with pytest.raises(ValueError):
            make_session(
                gap_ids=["gap-001"],
                active_qs=["q-001"],
                completed_qs=["q-001"],
            )

    def test_no_overlap_ok(self):
        s = make_session(
            gap_ids=["gap-001"],
            active_qs=["q-001"],
            completed_qs=["q-002"],
        )
        assert "q-001" in s.active_question_ids

    def test_related_gap_ids_empty_by_default(self):
        s = make_session(gap_ids=[])
        assert s.related_gap_ids == []


class TestClarificationDecisionRecord:
    def test_valid_decision(self):
        d = make_decision()
        assert d.decision_id == "dec-001"

    def test_blank_decision_id_raises(self):
        with pytest.raises(ValueError):
            make_decision(did="  ")

    def test_blank_session_id_raises(self):
        with pytest.raises(ValueError):
            make_decision(sid="  ")

    def test_rejected_needs_reason(self):
        with pytest.raises(ValueError):
            make_decision(disposition=ClarificationDisposition.rejected, reason=None)

    def test_escalated_needs_reason(self):
        with pytest.raises(ValueError):
            make_decision(disposition=ClarificationDisposition.escalated, reason=None)

    def test_ready_to_proceed_does_not_require_reason(self):
        d = make_decision(
            disposition=ClarificationDisposition.ready_to_proceed,
            reason=None,
        )
        assert d.clarification_disposition == ClarificationDisposition.ready_to_proceed

    def test_proceed_with_gaps_does_not_require_reason(self):
        d = make_decision(
            disposition=ClarificationDisposition.proceed_with_gaps,
            reason=None,
        )
        assert d.clarification_disposition == ClarificationDisposition.proceed_with_gaps

    def test_awaiting_response_does_not_require_reason(self):
        d = make_decision(
            disposition=ClarificationDisposition.awaiting_response,
            reason=None,
        )
        assert d.clarification_disposition == ClarificationDisposition.awaiting_response


class TestClarificationResolutionEnvelope:
    def test_valid_envelope(self):
        env = make_envelope()
        assert env.envelope_id == "env-clar-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValueError):
            make_envelope(eid="  ")

    def test_question_references_unknown_gap_raises(self):
        q = make_question(gap_id="gap-999")
        with pytest.raises(ValueError):
            make_envelope(questions=[q])

    def test_attempt_references_unknown_gap_raises(self):
        a = make_attempt(gap_id="gap-999")
        with pytest.raises(ValueError):
            make_envelope(attempts=[a])

    def test_field_resolution_references_unknown_gap_raises(self):
        fr = make_field_resolution(gap_id="gap-999")
        with pytest.raises(ValueError):
            make_envelope(field_resolutions=[fr])

    def test_session_references_unknown_gap_raises(self):
        with pytest.raises(ValueError):
            make_envelope(
                gaps=[make_gap()],
                session=make_session(gap_ids=["gap-999"]),
            )

    def test_session_active_question_references_unknown_raises(self):
        q = make_question()
        with pytest.raises(ValueError):
            make_envelope(
                gaps=[make_gap()],
                questions=[q],
                field_resolutions=[make_field_resolution()],
                session=make_session(
                    gap_ids=["gap-001"],
                    active_qs=["q-999"],
                ),
            )

    def test_session_completed_question_references_unknown_raises(self):
        q = make_question()
        with pytest.raises(ValueError):
            make_envelope(
                gaps=[make_gap()],
                questions=[q],
                field_resolutions=[make_field_resolution()],
                session=make_session(
                    gap_ids=["gap-001"],
                    completed_qs=["q-999"],
                ),
            )

    def test_decision_open_gap_references_unknown_raises(self):
        with pytest.raises(ValueError):
            make_envelope(
                decision=make_decision(open_gaps=["gap-999"]),
            )

    def test_awaiting_response_no_active_questions_raises(self):
        with pytest.raises(ValueError):
            make_envelope(
                decision=make_decision(
                    disposition=ClarificationDisposition.awaiting_response,
                ),
            )

    def test_awaiting_response_with_active_questions_ok(self):
        q = make_question()
        env = make_envelope(
            gaps=[make_gap()],
            questions=[q],
            field_resolutions=[make_field_resolution()],
            session=make_session(
                gap_ids=["gap-001"],
                active_qs=[q.question_id],
            ),
            decision=make_decision(
                disposition=ClarificationDisposition.awaiting_response,
                active_questions=True,
            ),
        )
        assert env.decision.clarification_disposition == ClarificationDisposition.awaiting_response

    def test_ready_to_proceed_with_unresolved_blocking_gap_raises(self):
        gap = make_gap(gap_id="gap-blocking", blocking=True, severity=GapSeverity.blocking)
        with pytest.raises(ValueError):
            make_envelope(
                gaps=[gap],
                field_resolutions=[],
                session=make_session(gap_ids=["gap-blocking"]),
            )

    def test_proceed_with_gaps_with_unresolved_blocking_gap_raises(self):
        gap = make_gap(gap_id="gap-blocking", blocking=True, severity=GapSeverity.blocking)
        with pytest.raises(ValueError):
            make_envelope(
                gaps=[gap],
                field_resolutions=[],
                session=make_session(gap_ids=["gap-blocking"]),
                decision=make_decision(
                    disposition=ClarificationDisposition.proceed_with_gaps,
                ),
            )

    def test_ready_to_proceed_with_non_blocking_gap_ok(self):
        gap = make_gap(gap_id="gap-nonb", blocking=False)
        env = make_envelope(
            gaps=[gap],
            field_resolutions=[],
            session=make_session(gap_ids=["gap-nonb"]),
            decision=make_decision(
                disposition=ClarificationDisposition.ready_to_proceed,
            ),
        )
        assert env.decision.clarification_disposition == ClarificationDisposition.ready_to_proceed

    def test_blocking_gap_resolved_ok(self):
        gap = make_gap(gap_id="gap-blocking", blocking=True, severity=GapSeverity.blocking)
        fr = make_field_resolution(gap_id="gap-blocking")
        env = make_envelope(
            gaps=[gap],
            field_resolutions=[fr],
            session=make_session(gap_ids=["gap-blocking"]),
            decision=make_decision(
                disposition=ClarificationDisposition.ready_to_proceed,
            ),
        )
        assert len(env.field_resolutions) == 1


class TestExampleScenarios:
    def test_missing_required_deadline_resolved(self):
        gap = MissingInfoGapRecord(
            gap_id="gap-001",
            intake_id="intake-001",
            field_name="deadline",
            gap_type=GapType.missing_required,
            gap_severity=GapSeverity.blocking,
            blocking=True,
            gap_summary="Deadline is missing from request",
            detected_at=datetime(2026, 7, 5, 9, 0, 0),
        )
        q = ClarificationQuestionRecord(
            question_id="q-001",
            gap_id="gap-001",
            field_name="deadline",
            question_text="By when does this task need to be completed?",
            question_order=0,
            response_type="date",
            recommended_examples=["2026-07-10", "end_of_sprint"],
            issued_at=datetime(2026, 7, 5, 9, 0, 5),
        )
        att = ResolutionAttemptRecord(
            attempt_id="att-001",
            gap_id="gap-001",
            resolution_method=ResolutionMethod.ask_user,
            proposed_value_ref="2026-07-10",
            confidence=0.95,
            attempt_reason="User answered deadline question",
            attempted_at=datetime(2026, 7, 5, 9, 0, 30),
        )
        fr = FieldResolutionRecord(
            field_resolution_id="fr-001",
            gap_id="gap-001",
            resolved_value_ref="2026-07-10",
            resolution_method=ResolutionMethod.ask_user,
            resolution_status=ResolutionStatus.resolved,
            notes="User explicitly provided deadline",
            resolved_at=datetime(2026, 7, 5, 9, 0, 30),
        )
        pol = ResolutionPolicyRecord(
            policy_id="pol-001",
            field_name="deadline",
            required=True,
            allow_default=True,
            allow_inference=False,
            allow_defer=False,
        )
        sess = ClarificationSessionRecord(
            clarification_session_id="cs-001",
            intake_id="intake-001",
            related_gap_ids=["gap-001"],
            active_question_ids=[],
            completed_question_ids=["q-001"],
            session_status="completed",
            started_at=datetime(2026, 7, 5, 9, 0, 0),
            updated_at=datetime(2026, 7, 5, 9, 0, 30),
        )
        dec = ClarificationDecisionRecord(
            decision_id="dec-001",
            clarification_session_id="cs-001",
            clarification_disposition=ClarificationDisposition.ready_to_proceed,
            remaining_open_gap_ids=[],
            decision_reason="All gaps resolved via user clarification",
            decided_at=datetime(2026, 7, 5, 9, 0, 35),
        )
        env = ClarificationResolutionEnvelope(
            envelope_id="env-clar-001",
            gaps=[gap],
            questions=[q],
            attempts=[att],
            field_resolutions=[fr],
            policies=[pol],
            session=sess,
            decision=dec,
        )
        assert env.decision.clarification_disposition == ClarificationDisposition.ready_to_proceed

    def test_ambiguous_output_format_clarified(self):
        gap = MissingInfoGapRecord(
            gap_id="gap-002",
            intake_id="intake-002",
            field_name="output_format",
            gap_type=GapType.ambiguous_value,
            gap_severity=GapSeverity.medium,
            blocking=False,
            gap_summary="Output format not specified — could be JSON, YAML, or plain text",
            candidate_values=["JSON", "YAML", "plain_text"],
            detected_at=datetime(2026, 7, 5, 10, 0, 0),
        )
        q = ClarificationQuestionRecord(
            question_id="q-002",
            gap_id="gap-002",
            field_name="output_format",
            question_text="Which output format do you prefer?",
            question_order=0,
            response_type="choice",
            recommended_examples=["JSON", "YAML", "plain_text"],
            issued_at=datetime(2026, 7, 5, 10, 0, 5),
        )
        att = ResolutionAttemptRecord(
            attempt_id="att-002",
            gap_id="gap-002",
            resolution_method=ResolutionMethod.ask_user,
            proposed_value_ref="JSON",
            confidence=0.98,
            attempt_reason="User selected JSON from options",
            attempted_at=datetime(2026, 7, 5, 10, 0, 20),
        )
        fr = FieldResolutionRecord(
            field_resolution_id="fr-002",
            gap_id="gap-002",
            resolved_value_ref="JSON",
            resolution_method=ResolutionMethod.ask_user,
            resolution_status=ResolutionStatus.resolved,
            resolved_at=datetime(2026, 7, 5, 10, 0, 20),
        )
        pol = ResolutionPolicyRecord(
            policy_id="pol-002",
            field_name="output_format",
            required=False,
            allow_default=True,
            allow_inference=False,
            allow_defer=False,
        )
        sess = ClarificationSessionRecord(
            clarification_session_id="cs-002",
            intake_id="intake-002",
            related_gap_ids=["gap-002"],
            active_question_ids=[],
            completed_question_ids=["q-002"],
            session_status="completed",
            started_at=datetime(2026, 7, 5, 10, 0, 0),
            updated_at=datetime(2026, 7, 5, 10, 0, 20),
        )
        dec = ClarificationDecisionRecord(
            decision_id="dec-002",
            clarification_session_id="cs-002",
            clarification_disposition=ClarificationDisposition.ready_to_proceed,
            remaining_open_gap_ids=[],
            decision_reason="Output format clarified to JSON",
            decided_at=datetime(2026, 7, 5, 10, 0, 25),
        )
        env = ClarificationResolutionEnvelope(
            envelope_id="env-clar-002",
            gaps=[gap],
            questions=[q],
            attempts=[att],
            field_resolutions=[fr],
            policies=[pol],
            session=sess,
            decision=dec,
        )
        assert env.decision.clarification_disposition == ClarificationDisposition.ready_to_proceed

    def test_optional_field_deferred_proceed_with_gaps(self):
        gap = MissingInfoGapRecord(
            gap_id="gap-003",
            intake_id="intake-003",
            field_name="deadline",
            gap_type=GapType.missing_optional,
            gap_severity=GapSeverity.low,
            blocking=False,
            gap_summary="Deadline is optional but not provided",
            detected_at=datetime(2026, 7, 5, 11, 0, 0),
        )
        fr = FieldResolutionRecord(
            field_resolution_id="fr-003",
            gap_id="gap-003",
            resolution_method=ResolutionMethod.defer,
            resolution_status=ResolutionStatus.deferred,
            notes="Optional deadline — proceeding without one",
            resolved_at=datetime(2026, 7, 5, 11, 0, 10),
        )
        pol = ResolutionPolicyRecord(
            policy_id="pol-003",
            field_name="deadline",
            required=False,
            allow_default=True,
            allow_defer=True,
            escalation_threshold=3,
        )
        sess = ClarificationSessionRecord(
            clarification_session_id="cs-003",
            intake_id="intake-003",
            related_gap_ids=["gap-003"],
            active_question_ids=[],
            completed_question_ids=[],
            session_status="completed",
            started_at=datetime(2026, 7, 5, 11, 0, 0),
            updated_at=datetime(2026, 7, 5, 11, 0, 10),
        )
        dec = ClarificationDecisionRecord(
            decision_id="dec-003",
            clarification_session_id="cs-003",
            clarification_disposition=ClarificationDisposition.proceed_with_gaps,
            remaining_open_gap_ids=["gap-003"],
            decision_reason="Optional deadline deferred — proceeding with gaps",
            proceeding_constraints=["deadline will be set when available"],
            decided_at=datetime(2026, 7, 5, 11, 0, 15),
        )
        env = ClarificationResolutionEnvelope(
            envelope_id="env-clar-003",
            gaps=[gap],
            questions=[],
            attempts=[],
            field_resolutions=[fr],
            policies=[pol],
            session=sess,
            decision=dec,
        )
        assert env.decision.clarification_disposition == ClarificationDisposition.proceed_with_gaps

    def test_conflicting_values_escalated(self):
        gap = MissingInfoGapRecord(
            gap_id="gap-004",
            intake_id="intake-004",
            field_name="priority",
            gap_type=GapType.conflicting_values,
            gap_severity=GapSeverity.blocking,
            blocking=True,
            gap_summary="Priority specified as both 'high' and 'low' in different sources",
            candidate_values=["high", "low"],
            detected_at=datetime(2026, 7, 5, 12, 0, 0),
        )
        question = ClarificationQuestionRecord(
            question_id="q-004",
            gap_id="gap-004",
            field_name="priority",
            question_text="Priority is both 'high' and 'low'. Which is correct?",
            question_order=0,
            response_type="choice",
            recommended_examples=["high", "low"],
            issued_at=datetime(2026, 7, 5, 12, 0, 5),
        )
        att = ResolutionAttemptRecord(
            attempt_id="att-004",
            gap_id="gap-004",
            resolution_method=ResolutionMethod.escalate,
            attempt_reason="Question issued, escalated after no timely response",
            attempted_at=datetime(2026, 7, 5, 12, 0, 5),
        )
        fr = FieldResolutionRecord(
            field_resolution_id="fr-004",
            gap_id="gap-004",
            resolution_method=ResolutionMethod.escalate,
            resolution_status=ResolutionStatus.escalated,
            notes="Escalated to manager — conflicting priority values unresolved",
            resolved_at=datetime(2026, 7, 5, 12, 5, 0),
        )
        pol = ResolutionPolicyRecord(
            policy_id="pol-004",
            field_name="priority",
            required=True,
            allow_default=False,
            allow_inference=False,
            allow_defer=False,
        )
        sess = ClarificationSessionRecord(
            clarification_session_id="cs-004",
            intake_id="intake-004",
            related_gap_ids=["gap-004"],
            active_question_ids=[],
            completed_question_ids=["q-004"],
            session_status="escalated",
            started_at=datetime(2026, 7, 5, 12, 0, 0),
            updated_at=datetime(2026, 7, 5, 12, 5, 0),
        )
        dec = ClarificationDecisionRecord(
            decision_id="dec-004",
            clarification_session_id="cs-004",
            clarification_disposition=ClarificationDisposition.escalated,
            remaining_open_gap_ids=["gap-004"],
            decision_reason="Conflicting priority values could not be resolved",
            decided_at=datetime(2026, 7, 5, 12, 5, 5),
        )
        env = ClarificationResolutionEnvelope(
            envelope_id="env-clar-004",
            gaps=[gap],
            questions=[question],
            attempts=[att],
            field_resolutions=[fr],
            policies=[pol],
            session=sess,
            decision=dec,
        )
        assert env.decision.clarification_disposition == ClarificationDisposition.escalated

    def test_unsupported_request_rejected(self):
        gap = MissingInfoGapRecord(
            gap_id="gap-005",
            intake_id="intake-005",
            field_name="request_type",
            gap_type=GapType.unsupported_request,
            gap_severity=GapSeverity.blocking,
            blocking=True,
            gap_summary="Request for network infrastructure access is outside agent scope",
            candidate_values=[],
            detected_at=datetime(2026, 7, 5, 14, 0, 0),
        )
        question = ClarificationQuestionRecord(
            question_id="q-005",
            gap_id="gap-005",
            field_name="request_type",
            question_text="This request requires infrastructure access that is outside my scope. "
                          "Can you rephrase as a code-level task?",
            question_order=0,
            response_type="free_text",
            recommended_examples=["Deploy application code", "Write configuration script"],
            issued_at=datetime(2026, 7, 5, 14, 0, 5),
        )
        att = ResolutionAttemptRecord(
            attempt_id="att-005",
            gap_id="gap-005",
            resolution_method=ResolutionMethod.escalate,
            attempt_reason="Asked user to rephrase, user confirmed cannot — escalating",
            attempted_at=datetime(2026, 7, 5, 14, 0, 5),
        )
        fr = FieldResolutionRecord(
            field_resolution_id="fr-005",
            gap_id="gap-005",
            resolution_method=ResolutionMethod.ask_user,
            resolution_status=ResolutionStatus.closed_unresolved,
            notes="User confirmed request cannot be rephrased — rejected",
            resolved_at=datetime(2026, 7, 5, 14, 5, 0),
        )
        pol = ResolutionPolicyRecord(
            policy_id="pol-005",
            field_name="request_type",
            required=True,
            allow_default=False,
            allow_inference=False,
            allow_defer=False,
        )
        sess = ClarificationSessionRecord(
            clarification_session_id="cs-005",
            intake_id="intake-005",
            related_gap_ids=["gap-005"],
            active_question_ids=[],
            completed_question_ids=["q-005"],
            session_status="closed",
            started_at=datetime(2026, 7, 5, 14, 0, 0),
            updated_at=datetime(2026, 7, 5, 14, 5, 0),
        )
        dec = ClarificationDecisionRecord(
            decision_id="dec-005",
            clarification_session_id="cs-005",
            clarification_disposition=ClarificationDisposition.rejected,
            remaining_open_gap_ids=["gap-005"],
            decision_reason="Unsupported request type — rejected after clarification attempt",
            decided_at=datetime(2026, 7, 5, 14, 5, 5),
        )
        env = ClarificationResolutionEnvelope(
            envelope_id="env-clar-005",
            gaps=[gap],
            questions=[question],
            attempts=[att],
            field_resolutions=[fr],
            policies=[pol],
            session=sess,
            decision=dec,
        )
        assert env.decision.clarification_disposition == ClarificationDisposition.rejected
