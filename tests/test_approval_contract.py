import pytest
from pydantic import ValidationError
from models.approval_contract import (
    RiskLevel,
    ApprovalActionType,
    ApprovalStatus,
    ReviewerDecisionType,
    EscalationReason,
    ApprovalPolicy,
    ApprovalEvidence,
    ApprovalRequest,
    ReviewerDecision,
    EscalationRecord,
    ApprovalOutcome,
)


class TestEnums:
    def test_risk_level_values(self):
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_approval_action_type_present(self):
        expected = {
            "TOOL_EXECUTION", "EXTERNAL_MESSAGE", "DATA_MUTATION",
            "PERMISSION_CHANGE", "FINANCIAL_ACTION", "POLICY_OVERRIDE",
            "PRODUCTION_DEPLOYMENT", "UNKNOWN",
        }
        assert set(ApprovalActionType.__members__) == expected

    def test_approval_status_values(self):
        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.ESCALATED.value == "escalated"

    def test_reviewer_decision_type_values(self):
        assert ReviewerDecisionType.APPROVE.value == "approve"
        assert ReviewerDecisionType.ABSTAIN.value == "abstain"

    def test_escalation_reason_values(self):
        assert EscalationReason.TIMEOUT.value == "timeout"
        assert EscalationReason.POLICY_TRIGGER.value == "policy_trigger"


class TestApprovalPolicy:
    def test_valid_low_risk(self):
        policy = ApprovalPolicy(
            policy_id="pol-exec-01", action_type=ApprovalActionType.TOOL_EXECUTION,
            minimum_risk_level_for_approval=RiskLevel.LOW, timeout_seconds=300,
            allowed_reviewer_roles=[],
        )
        assert policy.policy_id == "pol-exec-01"
        assert policy.require_evidence is True

    def test_high_risk_with_roles(self):
        policy = ApprovalPolicy(
            policy_id="pol-deploy-01", action_type=ApprovalActionType.PRODUCTION_DEPLOYMENT,
            minimum_risk_level_for_approval=RiskLevel.CRITICAL, timeout_seconds=600,
            allowed_reviewer_roles=["senior_engineer", "tech_lead"],
        )
        assert "senior_engineer" in policy.allowed_reviewer_roles

    def test_high_risk_missing_roles_raises(self):
        with pytest.raises(ValidationError) as exc:
            ApprovalPolicy(
                policy_id="pol-bad", action_type=ApprovalActionType.DATA_MUTATION,
                minimum_risk_level_for_approval=RiskLevel.CRITICAL, timeout_seconds=300,
                allowed_reviewer_roles=[],
            )
        assert "allowed_reviewer_roles must not be empty for high/critical risk policies" in str(exc.value)

    def test_low_risk_no_roles_valid(self):
        policy = ApprovalPolicy(
            policy_id="pol-low", action_type=ApprovalActionType.TOOL_EXECUTION,
            minimum_risk_level_for_approval=RiskLevel.LOW, timeout_seconds=60,
            allowed_reviewer_roles=[],
        )
        assert policy.minimum_risk_level_for_approval == RiskLevel.LOW

    def test_empty_policy_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            ApprovalPolicy(policy_id="  ", action_type=ApprovalActionType.UNKNOWN,
                           minimum_risk_level_for_approval=RiskLevel.LOW, timeout_seconds=60)
        assert "policy_id must not be empty" in str(exc.value)

    def test_zero_timeout_raises(self):
        with pytest.raises(ValidationError) as exc:
            ApprovalPolicy(policy_id="p", action_type=ApprovalActionType.TOOL_EXECUTION,
                           minimum_risk_level_for_approval=RiskLevel.LOW, timeout_seconds=0)
        assert "timeout_seconds must be at least 1" in str(exc.value)


class TestApprovalEvidence:
    def test_valid(self):
        ev = ApprovalEvidence(evidence_id="ev-001", label="Tool diff",
                              content="edit_file: src/main.py: +15 -3 lines")
        assert ev.content_type == "text"

    def test_empty_evidence_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            ApprovalEvidence(evidence_id="  ", label="x", content="x")
        assert "must not be empty" in str(exc.value)

    def test_empty_label_raises(self):
        with pytest.raises(ValidationError) as exc:
            ApprovalEvidence(evidence_id="e1", label="  ", content="x")
        assert "must not be empty" in str(exc.value)

    def test_empty_content_raises(self):
        with pytest.raises(ValidationError) as exc:
            ApprovalEvidence(evidence_id="e1", label="x", content="  ")
        assert "must not be empty" in str(exc.value)


class TestApprovalRequest:
    def test_valid_low_risk(self):
        req = ApprovalRequest(
            request_id="req-001", run_id="run-001", step_id="step-3",
            action_type=ApprovalActionType.TOOL_EXECUTION, risk_level=RiskLevel.LOW,
            requested_by_agent_id="agent-01", summary="Edit src/main.py",
            proposed_action='edit_file(path="src/main.py", content=...)',
        )
        assert req.status == ApprovalStatus.PENDING

    def test_high_risk_with_roles_and_evidence(self):
        req = ApprovalRequest(
            request_id="req-002", run_id="run-001", step_id="step-5",
            action_type=ApprovalActionType.DATA_MUTATION, risk_level=RiskLevel.HIGH,
            requested_by_agent_id="agent-01",
            summary="Delete production database records",
            proposed_action="delete_from_db(table=users, where=inactive_since=2022)",
            reviewer_roles_needed=["senior_engineer"],
            evidence=[ApprovalEvidence(evidence_id="ev-001", label="SQL query",
                                       content="DELETE FROM users WHERE ...")],
        )
        assert req.risk_level == RiskLevel.HIGH
        assert len(req.evidence) == 1

    def test_high_risk_no_roles_raises(self):
        with pytest.raises(ValidationError) as exc:
            ApprovalRequest(
                request_id="req-003", run_id="run-001", step_id="step-1",
                action_type=ApprovalActionType.FINANCIAL_ACTION, risk_level=RiskLevel.CRITICAL,
                requested_by_agent_id="agent-01", summary="Transfer funds",
                proposed_action="transfer(amount=10000, to=...)",
                reviewer_roles_needed=[],
            )
        assert "reviewer_roles_needed must not be empty for high/critical risk requests" in str(exc.value)

    def test_high_risk_no_evidence_raises(self):
        with pytest.raises(ValidationError) as exc:
            ApprovalRequest(
                request_id="req-004", run_id="run-001", step_id="step-1",
                action_type=ApprovalActionType.PERMISSION_CHANGE, risk_level=RiskLevel.HIGH,
                requested_by_agent_id="agent-01", summary="Grant admin",
                proposed_action="grant_role(user=x, role=admin)",
                reviewer_roles_needed=["admin"],
                evidence=[],
            )
        assert "evidence must not be empty for high/critical risk requests" in str(exc.value)

    def test_empty_request_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            ApprovalRequest(request_id="  ", run_id="r", step_id="s",
                            action_type=ApprovalActionType.UNKNOWN, risk_level=RiskLevel.LOW,
                            requested_by_agent_id="a", summary="x", proposed_action="y")
        assert "must not be empty" in str(exc.value)

    def test_empty_summary_raises(self):
        with pytest.raises(ValidationError) as exc:
            ApprovalRequest(request_id="r", run_id="r", step_id="s",
                            action_type=ApprovalActionType.UNKNOWN, risk_level=RiskLevel.LOW,
                            requested_by_agent_id="a", summary="  ", proposed_action="y")
        assert "must not be empty" in str(exc.value)

    def test_empty_proposed_action_raises(self):
        with pytest.raises(ValidationError) as exc:
            ApprovalRequest(request_id="r", run_id="r", step_id="s",
                            action_type=ApprovalActionType.UNKNOWN, risk_level=RiskLevel.LOW,
                            requested_by_agent_id="a", summary="x", proposed_action="  ")
        assert "must not be empty" in str(exc.value)


class TestReviewerDecision:
    def test_approve(self):
        d = ReviewerDecision(decision_id="dec-001", request_id="req-001",
                             reviewer_id="user-42", reviewer_role="tech_lead",
                             decision=ReviewerDecisionType.APPROVE,
                             rationale="Changes look safe, approved for deployment")
        assert d.decision == ReviewerDecisionType.APPROVE

    def test_reject_with_rationale(self):
        d = ReviewerDecision(decision_id="dec-002", request_id="req-002",
                             reviewer_id="user-99", reviewer_role="senior_engineer",
                             decision=ReviewerDecisionType.REJECT,
                             rationale="Query would affect too many records, needs LIMIT clause")
        assert d.reviewer_role == "senior_engineer"

    def test_empty_decision_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            ReviewerDecision(decision_id="  ", request_id="r", reviewer_id="u",
                             reviewer_role="dev", decision=ReviewerDecisionType.ABSTAIN,
                             rationale="no opinion")
        assert "must not be empty" in str(exc.value)

    def test_empty_rationale_raises(self):
        with pytest.raises(ValidationError) as exc:
            ReviewerDecision(decision_id="d", request_id="r", reviewer_id="u",
                             reviewer_role="dev", decision=ReviewerDecisionType.APPROVE,
                             rationale="  ")
        assert "rationale must not be empty" in str(exc.value)


class TestEscalationRecord:
    def test_timeout_escalation(self):
        esc = EscalationRecord(escalation_id="esc-001", request_id="req-001",
                               reason=EscalationReason.TIMEOUT, escalated_to_role="senior_engineer",
                               note="Request timed out after 300s")
        assert esc.reason == EscalationReason.TIMEOUT

    def test_without_note(self):
        esc = EscalationRecord(escalation_id="esc-002", request_id="req-002",
                               reason=EscalationReason.HIGH_RISK_ACTION,
                               escalated_to_role="tech_lead")
        assert esc.note is None

    def test_empty_escalation_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            EscalationRecord(escalation_id="  ", request_id="r",
                             reason=EscalationReason.UNKNOWN, escalated_to_role="dev")
        assert "must not be empty" in str(exc.value)


class TestApprovalOutcome:
    def test_approved_with_decision(self):
        outcome = ApprovalOutcome(request_id="req-001", final_status=ApprovalStatus.APPROVED,
                                  final_decision_id="dec-001", executable=True)
        assert outcome.executable is True

    def test_rejected_not_executable(self):
        outcome = ApprovalOutcome(request_id="req-002", final_status=ApprovalStatus.REJECTED,
                                  final_decision_id="dec-002", executable=False)
        assert outcome.executable is False

    def test_approved_missing_decision_raises(self):
        with pytest.raises(ValidationError) as exc:
            ApprovalOutcome(request_id="req-003", final_status=ApprovalStatus.APPROVED,
                            final_decision_id=None, executable=True)
        assert "APPROVED outcome must have a final_decision_id" in str(exc.value)

    def test_rejected_executable_raises(self):
        with pytest.raises(ValidationError) as exc:
            ApprovalOutcome(request_id="req-004", final_status=ApprovalStatus.REJECTED,
                            final_decision_id="dec-003", executable=True)
        assert "rejected outcome must not be executable" in str(exc.value)

    def test_expired_not_executable(self):
        with pytest.raises(ValidationError) as exc:
            ApprovalOutcome(request_id="req-005", final_status=ApprovalStatus.EXPIRED,
                            executable=True)
        assert "expired outcome must not be executable" in str(exc.value)

    def test_escalated_not_executable(self):
        with pytest.raises(ValidationError) as exc:
            ApprovalOutcome(request_id="req-006", final_status=ApprovalStatus.ESCALATED,
                            executable=True)
        assert "escalated outcome must not be executable" in str(exc.value)

    def test_cancelled_not_executable(self):
        with pytest.raises(ValidationError) as exc:
            ApprovalOutcome(request_id="req-007", final_status=ApprovalStatus.CANCELLED,
                            executable=True)
        assert "cancelled outcome must not be executable" in str(exc.value)

    def test_with_escalation_ids(self):
        outcome = ApprovalOutcome(request_id="req-008", final_status=ApprovalStatus.ESCALATED,
                                  escalation_ids=["esc-001", "esc-002"], executable=False)
        assert len(outcome.escalation_ids) == 2

    def test_pending_no_decision(self):
        outcome = ApprovalOutcome(request_id="req-009", final_status=ApprovalStatus.PENDING,
                                  executable=False)
        assert outcome.final_decision_id is None

    def test_empty_request_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            ApprovalOutcome(request_id="  ", final_status=ApprovalStatus.PENDING)
        assert "request_id must not be empty" in str(exc.value)


class TestSerialization:
    def test_request_to_json(self):
        req = ApprovalRequest(
            request_id="req-001", run_id="run-001", step_id="step-1",
            action_type=ApprovalActionType.TOOL_EXECUTION, risk_level=RiskLevel.MEDIUM,
            requested_by_agent_id="agent-01", summary="Edit file",
            proposed_action="edit_file(path=x, content=y)",
        )
        json_str = req.model_dump_json()
        assert "req-001" in json_str
        assert "tool_execution" in json_str

    def test_outcome_roundtrip(self):
        outcome = ApprovalOutcome(request_id="req-001", final_status=ApprovalStatus.APPROVED,
                                  final_decision_id="dec-001", executable=True)
        dumped = outcome.model_dump()
        assert dumped["executable"] is True
        assert dumped["final_status"] == "approved"
