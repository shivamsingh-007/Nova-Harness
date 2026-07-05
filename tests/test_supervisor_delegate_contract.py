import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from models.supervisor_delegate_contract import (
    DelegationReason, DelegateRoleType, DelegationStatus, DelegationOutcome, ReturnDisposition,
    DelegationRequest, DelegationContextSlice, DelegationConstraintSet,
    DelegateSelectionRecord, DelegationAssignment, DelegationReturnRecord,
    SupervisorReviewRecord, DelegationEnvelope,
)


NOW = datetime.now(timezone.utc)


def make_request(**overrides) -> DelegationRequest:
    defaults = dict(
        delegation_id="del-001", supervisor_agent_id="agent-super-001",
        delegation_reason=DelegationReason.SPECIALIZED_CAPABILITY_REQUIRED,
        requested_role=DelegateRoleType.CODER,
        objective="Implement user auth model",
        acceptance_criteria=["User model with email", "Password hashing"],
        created_at=NOW,
    )
    defaults.update(overrides)
    return DelegationRequest(**defaults)


def make_context(**overrides) -> DelegationContextSlice:
    defaults = dict(
        context_slice_id="ctx-001", task_ref="task-auth-001",
        artifact_refs=["specs/auth.md"],
    )
    defaults.update(overrides)
    return DelegationContextSlice(**defaults)


def make_constraints(**overrides) -> DelegationConstraintSet:
    defaults = dict(
        constraint_id="cst-001", time_budget_ms=60000, write_permissions=True,
        must_not_delegate_further=True,
    )
    defaults.update(overrides)
    return DelegationConstraintSet(**defaults)


def make_selection(**overrides) -> DelegateSelectionRecord:
    defaults = dict(
        selection_id="sel-001",
        selected_role=DelegateRoleType.CODER,
        candidate_roles=[DelegateRoleType.CODER, DelegateRoleType.SPECIALIST],
        selection_reason="Coder role matches objective",
        selection_confidence=0.9,
    )
    defaults.update(overrides)
    return DelegateSelectionRecord(**defaults)


def make_assignment(**overrides) -> DelegationAssignment:
    defaults = dict(
        assignment_id="asn-001",
        delegation_request=make_request(),
        context_slice=make_context(),
        constraints=make_constraints(),
        selection=make_selection(selected_delegate_id="agent-coder-001"),
        status=DelegationStatus.DRAFT,
    )
    defaults.update(overrides)
    return DelegationAssignment(**defaults)


def make_return(**overrides) -> DelegationReturnRecord:
    defaults = dict(
        return_id="ret-001", assignment_id="asn-001",
        delegate_agent_id="agent-coder-001",
        outcome=DelegationOutcome.SUCCESS,
        result_summary="Created auth model with bcrypt",
        output_refs=["src/models/user.py", "src/auth/hash.py"],
        evidence_refs=["test_output/test_auth.py"],
        confidence=0.9,
        returned_at=NOW,
    )
    defaults.update(overrides)
    return DelegationReturnRecord(**defaults)


def make_review(**overrides) -> SupervisorReviewRecord:
    defaults = dict(
        review_id="rev-001", assignment_id="asn-001",
        return_id="ret-001", reviewer_agent_id="agent-super-001",
        disposition=ReturnDisposition.ACCEPT,
        accepted_output_refs=["src/models/user.py", "src/auth/hash.py"],
        integration_notes="Merged into main branch",
        reviewed_at=NOW,
    )
    defaults.update(overrides)
    return SupervisorReviewRecord(**defaults)


def make_envelope(**overrides) -> DelegationEnvelope:
    defaults = dict(
        envelope_id="env-del-001",
        delegation_request=make_request(),
        delegation_assignment=make_assignment(),
    )
    defaults.update(overrides)
    return DelegationEnvelope(**defaults)


class TestEnums:
    def test_delegation_reason(self):
        assert DelegationReason.SPECIALIZED_CAPABILITY_REQUIRED.value == "specialized_capability_required"
        assert DelegationReason.HUMAN_LIKE_REVIEW_PATTERN.value == "human_like_review_pattern"
        assert len(DelegationReason) == 7

    def test_delegate_role_type(self):
        assert DelegateRoleType.CODER.value == "coder"
        assert DelegateRoleType.TOOL_OPERATOR.value == "tool_operator"
        assert len(DelegateRoleType) == 8

    def test_delegation_status(self):
        assert DelegationStatus.RETURNED.value == "returned"
        assert DelegationStatus.EXPIRED.value == "expired"
        assert len(DelegationStatus) == 9

    def test_delegation_outcome(self):
        assert DelegationOutcome.NO_RESULT.value == "no_result"
        assert len(DelegationOutcome) == 5

    def test_return_disposition(self):
        assert ReturnDisposition.ACCEPT.value == "accept"
        assert ReturnDisposition.DISCARD.value == "discard"
        assert len(ReturnDisposition) == 6


class TestDelegationRequest:
    def test_valid(self):
        r = make_request()
        assert r.delegation_id == "del-001"

    def test_blank_delegation_id_raises(self):
        with pytest.raises(ValidationError):
            make_request(delegation_id="")

    def test_blank_supervisor_id_raises(self):
        with pytest.raises(ValidationError):
            make_request(supervisor_agent_id="")

    def test_blank_objective_raises(self):
        with pytest.raises(ValidationError):
            make_request(objective="")

    def test_empty_acceptance_criteria_raises(self):
        with pytest.raises(ValidationError, match="acceptance_criteria must not be empty"):
            make_request(acceptance_criteria=[])

    def test_with_parent_refs(self):
        r = make_request(parent_run_id="run-001", parent_step_id="step-005")
        assert r.parent_run_id == "run-001"
        assert r.parent_step_id == "step-005"

    def test_with_requested_delegate(self):
        r = make_request(requested_delegate_id="agent-coder-001")
        assert r.requested_delegate_id == "agent-coder-001"

    def test_priority_default(self):
        r = make_request(priority="high")
        assert r.priority == "high"


class TestDelegationContextSlice:
    def test_valid(self):
        c = make_context()
        assert c.context_slice_id == "ctx-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValidationError):
            make_context(context_slice_id="")

    def test_no_refs_raises(self):
        with pytest.raises(ValidationError, match="context_slice must contain at least one reference"):
            make_context(task_ref=None, artifact_refs=[], relevant_state_refs=[],
                         prompt_refs=[], memory_refs=[], policy_refs=[])

    def test_self_contained_valid(self):
        c = make_context(task_ref=None, artifact_refs=[], relevant_state_refs=[],
                         prompt_refs=[], memory_refs=[], policy_refs=[],
                         self_contained=True)
        assert c.self_contained is True

    def test_with_policy_refs(self):
        c = make_context(policy_refs=["policy/coding.md"])
        assert c.policy_refs[0] == "policy/coding.md"

    def test_with_excluded(self):
        c = make_context(excluded_refs=["secrets/credentials.json"])
        assert c.excluded_refs[0] == "secrets/credentials.json"

    def test_max_context_tokens(self):
        c = make_context(max_context_tokens=8000)
        assert c.max_context_tokens == 8000


class TestDelegationConstraintSet:
    def test_valid(self):
        c = make_constraints()
        assert c.constraint_id == "cst-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValidationError):
            make_constraints(constraint_id="")

    def test_tool_lists(self):
        c = make_constraints(tool_allowlist=["read", "write"], tool_denylist=["delete"])
        assert "read" in c.tool_allowlist
        assert "delete" in c.tool_denylist

    def test_default_must_not_delegate_further(self):
        c = make_constraints()
        assert c.must_not_delegate_further is True

    def test_approval_required(self):
        c = make_constraints(approval_required=True)
        assert c.approval_required is True

    def test_cost_budget(self):
        c = make_constraints(cost_budget=50.0)
        assert c.cost_budget == 50.0


class TestDelegateSelectionRecord:
    def test_valid(self):
        s = make_selection()
        assert s.selection_id == "sel-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValidationError):
            make_selection(selection_id="")

    def test_confidence_range_low_raises(self):
        with pytest.raises(ValidationError, match="confidence must be between"):
            make_selection(selection_confidence=-0.1)

    def test_confidence_range_high_raises(self):
        with pytest.raises(ValidationError, match="confidence must be between"):
            make_selection(selection_confidence=1.5)

    def test_confidence_valid(self):
        s = make_selection(selection_confidence=0.75)
        assert s.selection_confidence == 0.75

    def test_with_fallbacks(self):
        s = make_selection(fallback_delegate_ids=["agent-coder-002", "agent-coder-003"])
        assert len(s.fallback_delegate_ids) == 2

    def test_candidate_roles(self):
        s = make_selection(candidate_roles=[DelegateRoleType.CODER, DelegateRoleType.PLANNER])
        assert len(s.candidate_roles) == 2


class TestDelegationAssignment:
    def test_valid(self):
        a = make_assignment()
        assert a.assignment_id == "asn-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValidationError):
            make_assignment(assignment_id="")

    def test_draft_does_not_need_delegate(self):
        a = make_assignment(status=DelegationStatus.DRAFT, selection=make_selection(selected_delegate_id=None))
        assert a.status == DelegationStatus.DRAFT

    def test_running_requires_selected_delegate(self):
        with pytest.raises(ValidationError, match="RUNNING status requires a selected delegate"):
            make_assignment(status=DelegationStatus.RUNNING,
                            selection=make_selection(selected_delegate_id=None))

    def test_with_child_run(self):
        a = make_assignment(child_run_id="child-run-001", child_session_id="child-sess-001")
        assert a.child_run_id == "child-run-001"

    def test_with_deadline(self):
        a = make_assignment(deadline_at=NOW)
        assert a.deadline_at is not None

    def test_returned_status_valid(self):
        a = make_assignment(status=DelegationStatus.RETURNED)
        assert a.status == DelegationStatus.RETURNED


class TestDelegationReturnRecord:
    def test_valid(self):
        r = make_return()
        assert r.return_id == "ret-001"

    def test_blank_return_id_raises(self):
        with pytest.raises(ValidationError):
            make_return(return_id="")

    def test_blank_assignment_id_raises(self):
        with pytest.raises(ValidationError):
            make_return(assignment_id="")

    def test_blank_delegate_id_raises(self):
        with pytest.raises(ValidationError):
            make_return(delegate_agent_id="")

    def test_confidence_range_raises(self):
        with pytest.raises(ValidationError, match="confidence must be between"):
            make_return(confidence=2.0)

    def test_with_blockers(self):
        r = make_return(outcome=DelegationOutcome.BLOCKED,
                        blockers=["API rate limit exceeded"])
        assert r.outcome == DelegationOutcome.BLOCKED

    def test_with_open_questions(self):
        r = make_return(open_questions=["Should we use bcrypt or argon2?"])
        assert len(r.open_questions) == 1

    def test_with_changed_artifacts(self):
        r = make_return(changed_artifact_refs=["src/models/user.py"])
        assert r.changed_artifact_refs[0] == "src/models/user.py"


class TestSupervisorReviewRecord:
    def test_valid_accept(self):
        r = make_review()
        assert r.review_id == "rev-001"

    def test_blank_review_id_raises(self):
        with pytest.raises(ValidationError):
            make_review(review_id="")

    def test_blank_reviewer_id_raises(self):
        with pytest.raises(ValidationError):
            make_review(reviewer_agent_id="")

    def test_accept_missing_outputs_and_notes_raises(self):
        with pytest.raises(ValidationError, match="accept disposition requires"):
            make_review(disposition=ReturnDisposition.ACCEPT,
                        accepted_output_refs=[], integration_notes="")

    def test_accept_with_integration_notes_valid(self):
        r = make_review(disposition=ReturnDisposition.ACCEPT,
                        accepted_output_refs=[], integration_notes="Manually verified")
        assert r.integration_notes == "Manually verified"

    def test_retry_requires_reason(self):
        with pytest.raises(ValidationError, match="retry_same_delegate requires retry_reason"):
            make_review(disposition=ReturnDisposition.RETRY_SAME_DELEGATE,
                        retry_reason="")

    def test_retry_with_reason_valid(self):
        r = make_review(disposition=ReturnDisposition.RETRY_SAME_DELEGATE,
                        retry_reason="Output did not meet quality bar")
        assert r.retry_reason == "Output did not meet quality bar"

    def test_reroute_requires_reason(self):
        with pytest.raises(ValidationError, match="reroute_to_other_delegate requires reroute_reason"):
            make_review(disposition=ReturnDisposition.REROUTE_TO_OTHER_DELEGATE,
                        reroute_reason="")

    def test_reroute_with_reason_valid(self):
        r = make_review(disposition=ReturnDisposition.REROUTE_TO_OTHER_DELEGATE,
                        reroute_reason="Current delegate lacks DB expertise")
        assert r.reroute_reason == "Current delegate lacks DB expertise"

    def test_accept_with_modification_valid(self):
        r = make_review(disposition=ReturnDisposition.ACCEPT_WITH_MODIFICATION,
                        accepted_output_refs=["src/models/user.py"],
                        integration_notes="Needs minor refactor")
        assert r.disposition == ReturnDisposition.ACCEPT_WITH_MODIFICATION

    def test_escalate_valid(self):
        r = make_review(disposition=ReturnDisposition.ESCALATE,
                        integration_notes="Requires human security review")
        assert r.disposition == ReturnDisposition.ESCALATE

    def test_discard_valid(self):
        r = make_review(disposition=ReturnDisposition.DISCARD,
                        rejection_reason="Output was incorrect")
        assert r.rejection_reason == "Output was incorrect"


class TestDelegationEnvelope:
    def test_valid_draft(self):
        e = make_envelope()
        assert e.envelope_id == "env-del-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="")

    def test_returned_status_requires_return_record(self):
        with pytest.raises(ValidationError, match="RETURNED status requires DelegationReturnRecord"):
            make_envelope(delegation_assignment=make_assignment(status=DelegationStatus.RETURNED))

    def test_returned_with_return_record_valid(self):
        ret = make_return()
        e = make_envelope(
            delegation_assignment=make_assignment(status=DelegationStatus.RETURNED),
            delegation_return=ret,
        )
        assert e.delegation_return.return_id == "ret-001"

    def test_accepted_requires_review(self):
        with pytest.raises(ValidationError, match="ACCEPTED/REJECTED/REROUTED status requires SupervisorReviewRecord"):
            make_envelope(
                delegation_assignment=make_assignment(
                    status=DelegationStatus.ACCEPTED,
                    selection=make_selection(selected_delegate_id="agent-coder-001"),
                ),
                delegation_return=make_return(),
            )

    def test_accepted_with_review_valid(self):
        e = make_envelope(
            delegation_assignment=make_assignment(
                status=DelegationStatus.ACCEPTED,
                selection=make_selection(selected_delegate_id="agent-coder-001"),
            ),
            delegation_return=make_return(),
            supervisor_review=make_review(),
        )
        assert e.supervisor_review.disposition == ReturnDisposition.ACCEPT

    def test_rejected_with_review_valid(self):
        e = make_envelope(
            delegation_assignment=make_assignment(
                status=DelegationStatus.REJECTED,
                selection=make_selection(selected_delegate_id="agent-coder-001"),
            ),
            delegation_return=make_return(
                outcome=DelegationOutcome.FAILURE,
                confidence=0.3,
            ),
            supervisor_review=make_review(
                disposition=ReturnDisposition.DISCARD,
                rejection_reason="Output was incorrect",
            ),
        )
        assert e.delegation_assignment.status == DelegationStatus.REJECTED

    def test_return_and_review_id_mismatch_raises(self):
        with pytest.raises(ValidationError, match="supervisor_review.return_id must match"):
            make_envelope(
                delegation_assignment=make_assignment(
                    status=DelegationStatus.ACCEPTED,
                    selection=make_selection(selected_delegate_id="agent-coder-001"),
                ),
                delegation_return=make_return(return_id="ret-001"),
                supervisor_review=make_review(return_id="ret-999"),
            )

    def test_rerouted_with_review_valid(self):
        e = make_envelope(
            delegation_assignment=make_assignment(
                status=DelegationStatus.REROUTED,
                selection=make_selection(selected_delegate_id="agent-coder-001"),
            ),
            delegation_return=make_return(),
            supervisor_review=make_review(
                disposition=ReturnDisposition.REROUTE_TO_OTHER_DELEGATE,
                reroute_reason="Need database specialist",
                integration_notes="Assigning to agent-db-001",
            ),
        )
        assert e.delegation_assignment.status == DelegationStatus.REROUTED


class TestSerialization:
    def test_request_to_dict_and_back(self):
        r = make_request()
        data = r.model_dump()
        restored = DelegationRequest(**data)
        assert restored.delegation_id == r.delegation_id

    def test_envelope_to_dict_and_back(self):
        e = make_envelope()
        data = e.model_dump()
        restored = DelegationEnvelope(**data)
        assert restored.envelope_id == e.envelope_id

    def test_full_envelope_roundtrip(self):
        e = make_envelope(
            delegation_assignment=make_assignment(
                status=DelegationStatus.ACCEPTED,
                selection=make_selection(selected_delegate_id="agent-coder-001"),
            ),
            delegation_return=make_return(),
            supervisor_review=make_review(),
        )
        data = e.model_dump()
        restored = DelegationEnvelope(**data)
        assert restored.supervisor_review.review_id == "rev-001"
        assert restored.delegation_assignment.status == DelegationStatus.ACCEPTED


class TestIntegration:
    def test_supervisor_delegates_coding_task_and_accepts(self):
        req = DelegationRequest(
            delegation_id="del-int-001", supervisor_agent_id="agent-super-001",
            delegation_reason=DelegationReason.SPECIALIZED_CAPABILITY_REQUIRED,
            requested_role=DelegateRoleType.CODER,
            objective="Implement user auth endpoints",
            expected_output="REST API with register, login, logout",
            acceptance_criteria=["POST /register creates user", "POST /login returns JWT"],
            created_at=NOW,
        )
        ctx = DelegationContextSlice(
            context_slice_id="ctx-int-001", task_ref="task-auth-002",
            artifact_refs=["specs/api.md"],
        )
        cst = DelegationConstraintSet(
            constraint_id="cst-int-001", time_budget_ms=300000,
            write_permissions=True, must_not_delegate_further=True,
        )
        sel = DelegateSelectionRecord(
            selection_id="sel-int-001",
            selected_role=DelegateRoleType.CODER,
            candidate_roles=[DelegateRoleType.CODER],
            selected_delegate_id="agent-coder-007",
            selection_reason="Coder available and matched auth objective",
            selection_confidence=0.85,
        )
        asn = DelegationAssignment(
            assignment_id="asn-int-001", delegation_request=req,
            context_slice=ctx, constraints=cst, selection=sel,
            status=DelegationStatus.RUNNING, started_at=NOW,
        )
        ret = DelegationReturnRecord(
            return_id="ret-int-001", assignment_id="asn-int-001",
            delegate_agent_id="agent-coder-007",
            outcome=DelegationOutcome.SUCCESS,
            result_summary="Implemented auth endpoints with JWT",
            output_refs=["src/api/auth.py", "src/middleware/jwt.py"],
            evidence_refs=["test_output/test_auth_api.py"],
            confidence=0.95, returned_at=NOW,
        )
        rev = SupervisorReviewRecord(
            review_id="rev-int-001", assignment_id="asn-int-001",
            return_id="ret-int-001", reviewer_agent_id="agent-super-001",
            disposition=ReturnDisposition.ACCEPT,
            accepted_output_refs=["src/api/auth.py", "src/middleware/jwt.py"],
            integration_notes="Merged to main. All tests pass.",
            reviewed_at=NOW,
        )
        env = DelegationEnvelope(
            envelope_id="env-int-001", delegation_request=req,
            delegation_assignment=asn, delegation_return=ret,
            supervisor_review=rev,
        )
        assert env.delegation_assignment.status == DelegationStatus.RUNNING
        assert env.delegation_return.outcome == DelegationOutcome.SUCCESS
        assert env.supervisor_review.disposition == ReturnDisposition.ACCEPT

    def test_delegate_returns_partial_with_blocker(self):
        req = make_request(delegation_id="del-int-002", objective="Set up CI pipeline",
                           acceptance_criteria=["GitHub Actions config", "Tests run on push"])
        ctx = make_context(context_slice_id="ctx-int-002", task_ref="task-ci-001")
        cst = make_constraints(constraint_id="cst-int-002", network_permissions=True)
        sel = make_selection(selection_id="sel-int-002", selected_role=DelegateRoleType.TOOL_OPERATOR,
                             selected_delegate_id="agent-ci-001")
        asn = make_assignment(assignment_id="asn-int-002", delegation_request=req,
                              context_slice=ctx, constraints=cst, selection=sel,
                              status=DelegationStatus.RUNNING, started_at=NOW)
        ret = DelegationReturnRecord(
            return_id="ret-int-002", assignment_id="asn-int-002",
            delegate_agent_id="agent-ci-001",
            outcome=DelegationOutcome.PARTIAL,
            result_summary="Created workflow file, but runner auth not configured",
            output_refs=[".github/workflows/ci.yml"],
            evidence_refs=["test_output/ci_dry_run.log"],
            blockers=["GitHub runner does not have access to registry"],
            confidence=0.6, returned_at=NOW,
        )
        rev = SupervisorReviewRecord(
            review_id="rev-int-002", assignment_id="asn-int-002",
            return_id="ret-int-002", reviewer_agent_id="agent-super-001",
            disposition=ReturnDisposition.RETRY_SAME_DELEGATE,
            retry_reason="Runner access needs to be configured",
            integration_notes="Will provide registry credentials",
            reviewed_at=NOW,
        )
        env = DelegationEnvelope(
            envelope_id="env-int-002", delegation_request=req,
            delegation_assignment=asn, delegation_return=ret,
            supervisor_review=rev,
        )
        assert env.delegation_return.blockers[0] == "GitHub runner does not have access to registry"
        assert env.supervisor_review.disposition == ReturnDisposition.RETRY_SAME_DELEGATE

    def test_supervisor_rejects_low_quality_retries(self):
        req = make_request(delegation_id="del-int-003", objective="Write API documentation",
                           requested_role=DelegateRoleType.SUMMARIZER,
                           acceptance_criteria=["All endpoints documented", "Examples included"])
        ctx = make_context(context_slice_id="ctx-int-003", task_ref="task-doc-001",
                           artifact_refs=["src/api/routes.py"])
        cst = make_constraints(constraint_id="cst-int-003")
        sel = make_selection(selection_id="sel-int-003", selected_role=DelegateRoleType.SUMMARIZER,
                             selected_delegate_id="agent-doc-001")
        asn = make_assignment(assignment_id="asn-int-003", delegation_request=req,
                              context_slice=ctx, constraints=cst, selection=sel,
                              status=DelegationStatus.RETURNED)
        ret = DelegationReturnRecord(
            return_id="ret-int-003", assignment_id="asn-int-003",
            delegate_agent_id="agent-doc-001",
            outcome=DelegationOutcome.PARTIAL,
            result_summary="Draft created but missing examples",
            output_refs=["docs/api.md"],
            evidence_refs=[],
            confidence=0.4, returned_at=NOW,
        )
        rev = SupervisorReviewRecord(
            review_id="rev-int-003", assignment_id="asn-int-003",
            return_id="ret-int-003", reviewer_agent_id="agent-super-001",
            disposition=ReturnDisposition.RETRY_SAME_DELEGATE,
            retry_reason="Documentation lacks examples for endpoints",
            integration_notes="Delegate to add curl examples",
            reviewed_at=NOW,
        )
        env = DelegationEnvelope(
            envelope_id="env-int-003", delegation_request=req,
            delegation_assignment=asn, delegation_return=ret,
            supervisor_review=rev,
        )
        assert env.delegation_return.confidence == 0.4
        assert env.supervisor_review.retry_reason == "Documentation lacks examples for endpoints"

    def test_supervisor_reroutes_to_different_specialist(self):
        req = make_request(delegation_id="del-int-004", objective="Optimize DB queries",
                           requested_role=DelegateRoleType.SPECIALIST,
                           acceptance_criteria=["Query time < 100ms", "Indexes created"])
        ctx = make_context(context_slice_id="ctx-int-004", task_ref="task-db-002",
                           artifact_refs=["src/db/queries.py"])
        cst = make_constraints(constraint_id="cst-int-004")
        sel = make_selection(selection_id="sel-int-004", selected_role=DelegateRoleType.SPECIALIST,
                             selected_delegate_id="agent-general-001",
                             fallback_delegate_ids=["agent-db-specialist-001"])
        asn = make_assignment(assignment_id="asn-int-004", delegation_request=req,
                              context_slice=ctx, constraints=cst, selection=sel,
                              status=DelegationStatus.REROUTED)
        ret = DelegationReturnRecord(
            return_id="ret-int-004", assignment_id="asn-int-004",
            delegate_agent_id="agent-general-001",
            outcome=DelegationOutcome.FAILURE,
            result_summary="Generalist could not optimize queries",
            evidence_refs=["perf_report.log"],
            confidence=0.3, returned_at=NOW,
        )
        rev = SupervisorReviewRecord(
            review_id="rev-int-004", assignment_id="asn-int-004",
            return_id="ret-int-004", reviewer_agent_id="agent-super-001",
            disposition=ReturnDisposition.REROUTE_TO_OTHER_DELEGATE,
            reroute_reason="Generalist lacks DB expertise, rerouting to DB specialist",
            integration_notes="Assigning to agent-db-specialist-001",
            reviewed_at=NOW,
        )
        env = DelegationEnvelope(
            envelope_id="env-int-004", delegation_request=req,
            delegation_assignment=asn, delegation_return=ret,
            supervisor_review=rev,
        )
        assert env.delegation_assignment.status == DelegationStatus.REROUTED
        assert env.supervisor_review.reroute_reason == "Generalist lacks DB expertise, rerouting to DB specialist"

    def test_verification_delegate_returns_evidence(self):
        req = make_request(delegation_id="del-int-005",
                           supervisor_agent_id="agent-super-001",
                           delegation_reason=DelegationReason.VERIFICATION_NEEDED,
                           requested_role=DelegateRoleType.VERIFIER,
                           objective="Verify auth endpoint security",
                           acceptance_criteria=["No SQL injection", "No hardcoded secrets", "JWT properly validated"],
                           created_at=NOW)
        ctx = make_context(context_slice_id="ctx-int-005", task_ref="task-auth-003",
                           artifact_refs=["src/api/auth.py"])
        cst = make_constraints(constraint_id="cst-int-005", tool_allowlist=["read", "static_analysis"])
        sel = make_selection(selection_id="sel-int-005", selected_role=DelegateRoleType.VERIFIER,
                             selected_delegate_id="agent-verifier-001")
        asn = make_assignment(assignment_id="asn-int-005", delegation_request=req,
                              context_slice=ctx, constraints=cst, selection=sel,
                              status=DelegationStatus.ACCEPTED)
        ret = DelegationReturnRecord(
            return_id="ret-int-005", assignment_id="asn-int-005",
            delegate_agent_id="agent-verifier-001",
            outcome=DelegationOutcome.SUCCESS,
            result_summary="Verified auth endpoint security. No vulnerabilities found.",
            output_refs=["audit_report/auth_security.md"],
            evidence_refs=["scan_output/semgrep_results.json", "scan_output/secrets_scan.txt"],
            confidence=0.98, returned_at=NOW,
        )
        rev = SupervisorReviewRecord(
            review_id="rev-int-005", assignment_id="asn-int-005",
            return_id="ret-int-005", reviewer_agent_id="agent-super-001",
            disposition=ReturnDisposition.ACCEPT,
            accepted_output_refs=["audit_report/auth_security.md"],
            integration_notes="Security verified, proceeding to deployment",
            reviewed_at=NOW,
        )
        env = DelegationEnvelope(
            envelope_id="env-int-005", delegation_request=req,
            delegation_assignment=asn, delegation_return=ret,
            supervisor_review=rev,
        )
        assert env.delegation_request.delegation_reason == DelegationReason.VERIFICATION_NEEDED
        assert len(env.delegation_return.evidence_refs) == 2
        assert env.supervisor_review.disposition == ReturnDisposition.ACCEPT
