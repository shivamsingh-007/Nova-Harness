import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from models.handoff_return_envelope_contract import (
    HandoffType, HandoffStatus, OwnershipMode, ReturnStatus, ReturnOutcome,
    HandoffRequest, HandoffContextPacket, HandoffConstraintPacket,
    HandoffOwnershipRecord, HandoffActionList, ReturnPayload,
    ReturnReviewRecord, HandoffReturnEnvelope,
    WRITE_OWNERSHIP_MODES, READ_ONLY_OWNERSHIP_MODES,
)

NOW = datetime.now(timezone.utc)


def make_handoff(**overrides) -> HandoffRequest:
    defaults = dict(handoff_id="hf-001", from_agent_id="agent-mgr-01",
                    to_agent_id="agent-coder-01",
                    handoff_type=HandoffType.DELEGATE_WORK,
                    objective="Generate user auth module",
                    acceptance_criteria=["code compiles", "tests pass"],
                    issued_at=NOW)
    defaults.update(overrides)
    return HandoffRequest(**defaults)


def make_context(**overrides) -> HandoffContextPacket:
    defaults = dict(context_packet_id="ctx-001",
                    task_ref="task-auth-042",
                    feature_ref="feature-user-auth",
                    state_refs=["state/run-42.json"],
                    artifact_refs=["specs/auth.md"],
                    context_summary="Auth module with JWT and OAuth2")
    defaults.update(overrides)
    return HandoffContextPacket(**defaults)


def make_constraint(**overrides) -> HandoffConstraintPacket:
    defaults = dict(constraint_packet_id="con-001",
                    time_budget="30min", cost_budget="5000tokens",
                    must_verify=True)
    defaults.update(overrides)
    return HandoffConstraintPacket(**defaults)


def make_ownership(**overrides) -> HandoffOwnershipRecord:
    defaults = dict(ownership_id="own-001",
                    ownership_mode=OwnershipMode.TEMPORARY_EXECUTION,
                    writer_agent_id="agent-coder-01",
                    read_only_agent_ids=["agent-mgr-01"],
                    ownership_reason="Code generation subtask")
    defaults.update(overrides)
    return HandoffOwnershipRecord(**defaults)


def make_action_list(**overrides) -> HandoffActionList:
    defaults = dict(action_list_id="al-001",
                    actions=["implement auth", "write tests", "run linter"],
                    pending_questions=["OAuth provider?"],
                    completion_checklist=["tests pass", "types check"])
    defaults.update(overrides)
    return HandoffActionList(**defaults)


def make_return(**overrides) -> ReturnPayload:
    defaults = dict(return_id="ret-001", handoff_id="hf-001",
                    from_agent_id="agent-coder-01", to_agent_id="agent-mgr-01",
                    return_status=ReturnStatus.SUBMITTED,
                    return_outcome=ReturnOutcome.SUCCESS,
                    result_summary="Auth module generated",
                    output_refs=["src/auth.py", "tests/test_auth.py"],
                    evidence_refs=["test_output.json", "lint_report.json"],
                    completed_actions=["implement auth", "write tests"],
                    confidence=0.95,
                    submitted_at=NOW)
    defaults.update(overrides)
    return ReturnPayload(**defaults)


def make_review(**overrides) -> ReturnReviewRecord:
    defaults = dict(review_id="rev-001", return_id="ret-001",
                    reviewer_agent_id="agent-mgr-01",
                    decision=ReturnStatus.ACCEPTED,
                    decision_reason="All criteria met",
                    accepted_output_refs=["src/auth.py"],
                    reviewed_at=NOW)
    defaults.update(overrides)
    return ReturnReviewRecord(**defaults)


def make_envelope(handoff=None, **overrides) -> HandoffReturnEnvelope:
    hf = handoff or make_handoff()
    data = dict(envelope_id="env-hf-001", handoff_request=hf,
                context_packet=make_context(),
                constraint_packet=make_constraint(),
                ownership_record=make_ownership(),
                action_list=make_action_list())
    data.update(overrides)
    return HandoffReturnEnvelope(**data)


class TestEnums:
    def test_handoff_type_values(self):
        assert HandoffType.DELEGATE_WORK.value == "delegate_work"
        assert HandoffType.RETURN_TO_SUPERVISOR.value == "return_to_supervisor"
        assert len(HandoffType) == 6

    def test_handoff_status_values(self):
        assert HandoffStatus.DRAFT.value == "draft"
        assert HandoffStatus.CANCELLED.value == "cancelled"
        assert len(HandoffStatus) == 8

    def test_ownership_mode_values(self):
        assert OwnershipMode.FULL_TRANSFER.value == "full_transfer"
        assert OwnershipMode.REVIEW_ONLY.value == "review_only"
        assert len(OwnershipMode) == 4

    def test_write_ownership_modes(self):
        assert OwnershipMode.FULL_TRANSFER in WRITE_OWNERSHIP_MODES
        assert OwnershipMode.READ_ONLY_ASSIST not in WRITE_OWNERSHIP_MODES

    def test_read_only_ownership_modes(self):
        assert OwnershipMode.READ_ONLY_ASSIST in READ_ONLY_OWNERSHIP_MODES
        assert OwnershipMode.FULL_TRANSFER not in READ_ONLY_OWNERSHIP_MODES

    def test_return_status_values(self):
        assert ReturnStatus.SUBMITTED.value == "submitted"
        assert ReturnStatus.NEEDS_FOLLOWUP.value == "needs_followup"
        assert len(ReturnStatus) == 5

    def test_return_outcome_values(self):
        assert ReturnOutcome.SUCCESS.value == "success"
        assert ReturnOutcome.NOT_APPLICABLE.value == "not_applicable"
        assert len(ReturnOutcome) == 5


class TestHandoffRequest:
    def test_valid(self):
        h = make_handoff()
        assert h.handoff_id == "hf-001"
        assert h.handoff_type == HandoffType.DELEGATE_WORK

    def test_blank_handoff_id_raises(self):
        with pytest.raises(ValidationError):
            make_handoff(handoff_id="  ")

    def test_blank_from_agent_id_raises(self):
        with pytest.raises(ValidationError):
            make_handoff(from_agent_id="  ")

    def test_blank_objective_raises(self):
        with pytest.raises(ValidationError):
            make_handoff(objective="  ")

    def test_no_target_raises(self):
        with pytest.raises(ValidationError):
            make_handoff(to_agent_id=None, target_role=None)

    def test_target_role_as_alternative(self):
        h = make_handoff(to_agent_id=None, target_role="coder")
        assert h.target_role == "coder"
        assert h.to_agent_id is None

    def test_empty_acceptance_criteria_raises(self):
        with pytest.raises(ValidationError):
            make_handoff(acceptance_criteria=[])

    def test_priority_optional(self):
        h = make_handoff(priority="high")
        assert h.priority == "high"

    def test_parent_run_step_optional(self):
        h = make_handoff(parent_run_id="run-042", parent_step_id="step-03")
        assert h.parent_run_id == "run-042"


class TestHandoffContextPacket:
    def test_valid(self):
        c = make_context()
        assert c.context_packet_id == "ctx-001"

    def test_blank_packet_id_raises(self):
        with pytest.raises(ValidationError):
            make_context(context_packet_id="  ")

    def test_excluded_context_refs(self):
        c = make_context(excluded_context_refs=["secrets.json", "config.toml"])
        assert len(c.excluded_context_refs) == 2

    def test_all_refs_default_empty(self):
        c = make_context(state_refs=[], artifact_refs=[], prompt_refs=[])
        assert c.state_refs == []


class TestHandoffConstraintPacket:
    def test_valid(self):
        c = make_constraint()
        assert c.time_budget == "30min"

    def test_blank_packet_id_raises(self):
        with pytest.raises(ValidationError):
            make_constraint(constraint_packet_id="  ")

    def test_tool_constraints(self):
        c = make_constraint(tool_constraints=["read_only"])
        assert "read_only" in c.tool_constraints

    def test_must_not_delegate_further(self):
        c = make_constraint(must_not_delegate_further=True)
        assert c.must_not_delegate_further is True

    def test_deadline_optional(self):
        c = make_constraint(deadline="2026-07-06T12:00:00Z")
        assert c.deadline is not None


class TestHandoffOwnershipRecord:
    def test_valid_temporary_execution(self):
        o = make_ownership()
        assert o.ownership_mode == OwnershipMode.TEMPORARY_EXECUTION

    def test_full_transfer_with_writer(self):
        o = make_ownership(ownership_mode=OwnershipMode.FULL_TRANSFER,
                           writer_agent_id="agent-coder-01")
        assert o.writer_agent_id == "agent-coder-01"

    def test_write_ownership_requires_writer(self):
        with pytest.raises(ValidationError, match="requires a writer_agent_id"):
            make_ownership(ownership_mode=OwnershipMode.FULL_TRANSFER,
                           writer_agent_id=None)

    def test_read_only_assist_no_writer(self):
        o = make_ownership(ownership_mode=OwnershipMode.READ_ONLY_ASSIST,
                           writer_agent_id=None)
        assert o.writer_agent_id is None

    def test_read_only_assist_with_writer_raises(self):
        with pytest.raises(ValidationError, match="read_only_assist must not assign write ownership"):
            make_ownership(ownership_mode=OwnershipMode.READ_ONLY_ASSIST,
                           writer_agent_id="agent-coder-01")

    def test_review_only_with_writer_raises(self):
        with pytest.raises(ValidationError, match="review_only must not assign write ownership"):
            make_ownership(ownership_mode=OwnershipMode.REVIEW_ONLY,
                           writer_agent_id="agent-coder-01")

    def test_review_only_valid(self):
        o = make_ownership(ownership_mode=OwnershipMode.REVIEW_ONLY,
                           writer_agent_id=None)
        assert o.ownership_mode == OwnershipMode.REVIEW_ONLY

    def test_blank_ownership_id_raises(self):
        with pytest.raises(ValidationError):
            make_ownership(ownership_id="  ")

    def test_temporary_execution_with_writer(self):
        o = make_ownership(ownership_mode=OwnershipMode.TEMPORARY_EXECUTION,
                           writer_agent_id="agent-spec-01")
        assert o.writer_agent_id == "agent-spec-01"


class TestHandoffActionList:
    def test_valid(self):
        a = make_action_list()
        assert a.action_list_id == "al-001"

    def test_blank_action_list_id_raises(self):
        with pytest.raises(ValidationError):
            make_action_list(action_list_id="  ")

    def test_pending_questions(self):
        a = make_action_list(pending_questions=["Which DB?", "Auth strategy?"])
        assert len(a.pending_questions) == 2

    def test_contingency_plans(self):
        a = make_action_list(contingency_plans=["Fallback to basic auth"])
        assert "Fallback" in a.contingency_plans[0]

    def test_next_required_decision(self):
        a = make_action_list(next_required_decision="Choose OAuth provider")
        assert a.next_required_decision is not None


class TestReturnPayload:
    def test_valid(self):
        r = make_return()
        assert r.return_id == "ret-001"
        assert r.confidence == 0.95

    def test_blank_return_id_raises(self):
        with pytest.raises(ValidationError):
            make_return(return_id="  ")

    def test_blank_handoff_id_raises(self):
        with pytest.raises(ValidationError):
            make_return(handoff_id="  ")

    def test_blank_from_agent_raises(self):
        with pytest.raises(ValidationError):
            make_return(from_agent_id="  ")

    def test_unresolved_items(self):
        r = make_return(unresolved_items=["OAuth2 flow needs review"])
        assert len(r.unresolved_items) == 1

    def test_blockers(self):
        r = make_return(blockers=["Awaiting secret key from vault"])
        assert "secret" in r.blockers[0]

    def test_confidence_out_of_range_high(self):
        with pytest.raises(ValidationError):
            make_return(confidence=1.5)

    def test_confidence_out_of_range_low(self):
        with pytest.raises(ValidationError):
            make_return(confidence=-0.1)

    def test_confidence_at_bounds(self):
        r = make_return(confidence=0.0)
        assert r.confidence == 0.0
        r2 = make_return(confidence=1.0)
        assert r2.confidence == 1.0

    def test_recommended_next_action(self):
        r = make_return(recommended_next_action="Review and merge")
        assert r.recommended_next_action == "Review and merge"


class TestReturnReviewRecord:
    def test_valid_accepted(self):
        r = make_review()
        assert r.decision == ReturnStatus.ACCEPTED

    def test_blank_review_id_raises(self):
        with pytest.raises(ValidationError):
            make_review(review_id="  ")

    def test_blank_return_id_raises(self):
        with pytest.raises(ValidationError):
            make_review(return_id="  ")

    def test_blank_reviewer_id_raises(self):
        with pytest.raises(ValidationError):
            make_review(reviewer_agent_id="  ")

    def test_rejected_decision(self):
        r = make_review(decision=ReturnStatus.REJECTED,
                        decision_reason="Tests failing",
                        followup_required=True,
                        followup_notes="Fix test assertions")
        assert r.followup_required is True

    def test_followup_notes(self):
        r = make_review(followup_required=True,
                        followup_notes="Add edge case coverage")
        assert r.followup_notes is not None


class TestHandoffReturnEnvelope:
    def test_valid(self):
        e = make_envelope()
        assert e.envelope_id == "env-hf-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="  ")

    def test_minimal_envelope(self):
        hf = make_handoff()
        e = HandoffReturnEnvelope(envelope_id="env-min", handoff_request=hf)
        assert e.context_packet is None
        assert e.return_payload is None

    def test_envelope_with_return(self):
        rp = make_return()
        e = make_envelope(return_payload=rp)
        assert e.return_payload.return_status == ReturnStatus.SUBMITTED

    def test_envelope_with_review(self):
        rr = make_review()
        e = make_envelope(return_payload=make_return(), return_review=rr)
        assert e.return_review.decision == ReturnStatus.ACCEPTED

    def test_read_only_assist_no_write_in_envelope(self):
        ow = make_ownership(ownership_mode=OwnershipMode.READ_ONLY_ASSIST,
                            writer_agent_id=None)
        e = make_envelope(ownership_record=ow)
        assert e.ownership_record.writer_agent_id is None

    def test_read_only_assist_with_writer_in_envelope_raises(self):
        with pytest.raises(ValidationError, match="read_only_assist must not assign write ownership"):
            make_ownership(ownership_mode=OwnershipMode.READ_ONLY_ASSIST,
                           writer_agent_id="agent-coder-01")

    def test_constraint_not_delegate_preserved(self):
        cp = make_constraint(must_not_delegate_further=True)
        e = make_envelope(constraint_packet=cp)
        assert e.constraint_packet.must_not_delegate_further is True


class TestSerialization:
    def test_handoff_to_dict_and_back(self):
        h = make_handoff()
        d = h.model_dump()
        h2 = HandoffRequest(**d)
        assert h2.handoff_id == h.handoff_id

    def test_envelope_to_dict_and_back(self):
        e = make_envelope(return_payload=make_return())
        d = e.model_dump()
        e2 = HandoffReturnEnvelope(**d)
        assert e2.envelope_id == e.envelope_id
        assert e2.return_payload.return_id == e.return_payload.return_id

    def test_full_envelope_roundtrip(self):
        e = make_envelope(return_payload=make_return(),
                          return_review=make_review())
        d = e.model_dump(mode="json")
        e2 = HandoffReturnEnvelope(**d)
        assert e2.return_review.decision == ReturnStatus.ACCEPTED

    def test_json_serialization(self):
        e = make_envelope()
        j = e.model_dump_json()
        e2 = HandoffReturnEnvelope.model_validate_json(j)
        assert e2.handoff_request.objective == "Generate user auth module"


class TestIntegration:
    def test_coding_task_handoff_and_successful_return(self):
        hf = HandoffRequest(
            handoff_id="hf-integ-001", from_agent_id="agent-mgr-01",
            to_agent_id="agent-coder-01",
            handoff_type=HandoffType.DELEGATE_WORK,
            objective="Implement API rate limiter",
            acceptance_criteria=["rate limiting works", "tests pass"],
        )
        ctx = HandoffContextPacket(
            context_packet_id="ctx-integ", task_ref="task-rate-limit",
            artifact_refs=["specs/rate_limit.md"],
        )
        cp = HandoffConstraintPacket(
            constraint_packet_id="con-integ", time_budget="20min",
            must_verify=True, must_not_delegate_further=True,
        )
        ow = HandoffOwnershipRecord(
            ownership_id="own-integ", ownership_mode=OwnershipMode.TEMPORARY_EXECUTION,
            writer_agent_id="agent-coder-01",
        )
        al = HandoffActionList(
            action_list_id="al-integ",
            actions=["implement limiter", "write tests", "benchmark"],
        )
        rp = ReturnPayload(
            return_id="ret-integ", handoff_id="hf-integ-001",
            from_agent_id="agent-coder-01", to_agent_id="agent-mgr-01",
            return_status=ReturnStatus.SUBMITTED,
            return_outcome=ReturnOutcome.SUCCESS,
            result_summary="Rate limiter implemented with token bucket",
            output_refs=["src/limiter.py", "tests/test_limiter.py"],
            evidence_refs=["test_output.json", "benchmark.json"],
            completed_actions=["implement limiter", "write tests"],
            confidence=0.9,
        )
        e = HandoffReturnEnvelope(
            envelope_id="env-integ", handoff_request=hf,
            context_packet=ctx, constraint_packet=cp,
            ownership_record=ow, action_list=al,
            return_payload=rp,
        )
        assert e.return_payload.return_outcome == ReturnOutcome.SUCCESS
        assert e.constraint_packet.must_not_delegate_further is True

    def test_review_handoff_read_only_ownership(self):
        hf = HandoffRequest(
            handoff_id="hf-review", from_agent_id="agent-mgr-01",
            to_agent_id="agent-reviewer-01",
            handoff_type=HandoffType.REQUEST_REVIEW,
            objective="Review auth module implementation",
            acceptance_criteria=["all review items checked"],
        )
        ow = HandoffOwnershipRecord(
            ownership_id="own-review", ownership_mode=OwnershipMode.REVIEW_ONLY,
            writer_agent_id=None,
            read_only_agent_ids=["agent-reviewer-01"],
        )
        rp = ReturnPayload(
            return_id="ret-review", handoff_id="hf-review",
            from_agent_id="agent-reviewer-01", to_agent_id="agent-mgr-01",
            return_status=ReturnStatus.SUBMITTED,
            return_outcome=ReturnOutcome.SUCCESS,
            result_summary="Review complete, minor style issues found",
            output_refs=["review_report.md"],
            evidence_refs=["diff_highlights.md"],
            confidence=0.85,
        )
        rr = ReturnReviewRecord(
            review_id="rev-review", return_id="ret-review",
            reviewer_agent_id="agent-mgr-01",
            decision=ReturnStatus.ACCEPTED,
            decision_reason="Issues are minor, can proceed",
        )
        e = HandoffReturnEnvelope(
            envelope_id="env-review", handoff_request=hf,
            ownership_record=ow, return_payload=rp, return_review=rr,
        )
        assert e.ownership_record.ownership_mode == OwnershipMode.REVIEW_ONLY
        assert e.return_review.decision == ReturnStatus.ACCEPTED

    def test_verification_handoff_with_evidence_and_unresolved(self):
        hf = HandoffRequest(
            handoff_id="hf-verify", from_agent_id="agent-mgr-01",
            to_agent_id="agent-verifier-01",
            handoff_type=HandoffType.REQUEST_VERIFICATION,
            objective="Verify auth module meets security standards",
            acceptance_criteria=["all security checks pass"],
        )
        rp = ReturnPayload(
            return_id="ret-verify", handoff_id="hf-verify",
            from_agent_id="agent-verifier-01", to_agent_id="agent-mgr-01",
            return_status=ReturnStatus.SUBMITTED,
            return_outcome=ReturnOutcome.PARTIAL,
            result_summary="3 of 4 checks passed",
            evidence_refs=["security_scan.json", "dependency_audit.json"],
            unresolved_items=["JWT secret rotation not implemented"],
            confidence=0.75,
            recommended_next_action="Implement secret rotation",
        )
        e = HandoffReturnEnvelope(
            envelope_id="env-verify", handoff_request=hf,
            return_payload=rp,
        )
        assert e.return_payload.return_outcome == ReturnOutcome.PARTIAL
        assert len(e.return_payload.unresolved_items) == 1

    def test_blocked_handoff_with_contingency(self):
        hf = make_handoff(handoff_id="hf-blocked")
        rp = ReturnPayload(
            return_id="ret-blocked", handoff_id="hf-blocked",
            from_agent_id="agent-coder-01", to_agent_id="agent-mgr-01",
            return_status=ReturnStatus.SUBMITTED,
            return_outcome=ReturnOutcome.BLOCKED,
            result_summary="Blocked on API key provisioning",
            blockers=["Secret vault not reachable"],
            confidence=0.3,
            recommended_next_action="Provision API key manually",
        )
        e = HandoffReturnEnvelope(
            envelope_id="env-blocked", handoff_request=hf,
            return_payload=rp,
        )
        assert "Secret vault" in e.return_payload.blockers[0]
        assert e.return_payload.confidence == 0.3

    def test_full_transfer_with_accepted_return_review(self):
        hf = HandoffRequest(
            handoff_id="hf-transfer", from_agent_id="agent-mgr-01",
            to_agent_id="agent-coder-01",
            handoff_type=HandoffType.TRANSFER_CONTROL,
            objective="Take over refactoring task completely",
            acceptance_criteria=["refactoring complete", "regression tests pass"],
        )
        ow = HandoffOwnershipRecord(
            ownership_id="own-transfer", ownership_mode=OwnershipMode.FULL_TRANSFER,
            current_owner_agent_id="agent-coder-01",
            writer_agent_id="agent-coder-01",
        )
        rp = ReturnPayload(
            return_id="ret-transfer", handoff_id="hf-transfer",
            from_agent_id="agent-coder-01", to_agent_id="agent-mgr-01",
            return_status=ReturnStatus.SUBMITTED,
            return_outcome=ReturnOutcome.SUCCESS,
            result_summary="Refactoring complete",
            output_refs=["src/refactored/"],
            evidence_refs=["regression_test_output.json"],
            confidence=0.98,
        )
        rr = ReturnReviewRecord(
            review_id="rev-transfer", return_id="ret-transfer",
            reviewer_agent_id="agent-mgr-01",
            decision=ReturnStatus.ACCEPTED,
            decision_reason="All criteria satisfied",
            accepted_output_refs=["src/refactored/"],
        )
        e = HandoffReturnEnvelope(
            envelope_id="env-transfer", handoff_request=hf,
            ownership_record=ow, return_payload=rp, return_review=rr,
        )
        assert e.ownership_record.current_owner_agent_id == "agent-coder-01"
        assert e.return_review.decision == ReturnStatus.ACCEPTED

    def test_retrieval_handoff(self):
        hf = HandoffRequest(
            handoff_id="hf-retrieve", from_agent_id="agent-coder-01",
            target_role="retriever",
            handoff_type=HandoffType.REQUEST_RETRIEVAL,
            objective="Find API documentation for JWT library",
            acceptance_criteria=["relevant docs returned"],
        )
        rp = ReturnPayload(
            return_id="ret-retrieve", handoff_id="hf-retrieve",
            from_agent_id="agent-retriever-01", to_agent_id="agent-coder-01",
            return_status=ReturnStatus.SUBMITTED,
            return_outcome=ReturnOutcome.SUCCESS,
            result_summary="Found JWT docs v2.1",
            output_refs=["docs/jwt_v2.1.md"],
            evidence_refs=["search_results.json"],
            confidence=0.9,
        )
        e = HandoffReturnEnvelope(
            envelope_id="env-retrieve", handoff_request=hf,
            return_payload=rp,
        )
        assert e.handoff_request.target_role == "retriever"
        assert e.handoff_request.to_agent_id is None
