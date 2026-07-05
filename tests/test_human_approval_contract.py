import pytest
from pydantic import ValidationError
from models.human_approval_contract import (
    ApprovalStatus,
    ApprovalDecisionType,
    ApprovalReasonType,
    RiskTier,
    EscalationStatus,
    ApproverRef,
    ApprovalContext,
    ApprovalRequest,
    ApprovalDecision,
    EscalationStep,
    ApprovalEnvelope,
)


class TestEnums:
    def test_approval_status_values(self):
        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.DENIED.value == "denied"
        assert ApprovalStatus.EXPIRED.value == "expired"
        assert ApprovalStatus.ESCALATED.value == "escalated"
        assert ApprovalStatus.CANCELLED.value == "cancelled"

    def test_approval_decision_type_values(self):
        assert ApprovalDecisionType.APPROVE.value == "approve"
        assert ApprovalDecisionType.DENY.value == "deny"
        assert ApprovalDecisionType.ESCALATE.value == "escalate"
        assert ApprovalDecisionType.OVERRIDE.value == "override"

    def test_approval_reason_type_values(self):
        assert ApprovalReasonType.POLICY_TRIGGER.value == "policy_trigger"
        assert ApprovalReasonType.HIGH_RISK_ACTION.value == "high_risk_action"
        assert ApprovalReasonType.SENSITIVE_DATA_ACCESS.value == "sensitive_data_access"
        assert ApprovalReasonType.SCOPE_EXPANSION.value == "scope_expansion"
        assert ApprovalReasonType.UNKNOWN_CONDITION.value == "unknown_condition"

    def test_risk_tier_values(self):
        assert RiskTier.LOW.value == "low"
        assert RiskTier.MODERATE.value == "moderate"
        assert RiskTier.HIGH.value == "high"
        assert RiskTier.CRITICAL.value == "critical"

    def test_escalation_status_values(self):
        assert EscalationStatus.NOT_ESCALATED.value == "not_escalated"
        assert EscalationStatus.IN_PROGRESS.value == "in_progress"
        assert EscalationStatus.RESOLVED.value == "resolved"
        assert EscalationStatus.TIMED_OUT.value == "timed_out"


class TestApproverRef:
    def test_valid(self):
        ref = ApproverRef(approver_id="u-42", approver_role="security_lead")
        assert ref.approver_id == "u-42"
        assert ref.approver_role == "security_lead"

    def test_valid_with_display_name(self):
        ref = ApproverRef(approver_id="u-7", approver_role="admin", display_name="Alice")
        assert ref.display_name == "Alice"

    def test_empty_approver_id_raises(self):
        with pytest.raises(ValueError):
            ApproverRef(approver_id="", approver_role="admin")

    def test_empty_role_raises(self):
        with pytest.raises(ValueError):
            ApproverRef(approver_id="u-1", approver_role="")


class TestApprovalContext:
    def test_valid_minimal(self):
        ctx = ApprovalContext(
            subject_ref="tool://td-storage/delete",
            summary="Delete production backup",
            risk_tier=RiskTier.CRITICAL,
        )
        assert ctx.policy_ref is None
        assert ctx.evidence_refs == []
        assert ctx.rollback_plan is None

    def test_valid_full(self):
        ctx = ApprovalContext(
            subject_ref="tool://td-storage/delete",
            summary="Delete production backup container",
            policy_ref="pol-dlp",
            risk_tier=RiskTier.CRITICAL,
            evidence_refs=["sig-del-001", "sig-del-002"],
            rollback_plan="Restore from snapshot snap-042",
        )
        assert ctx.policy_ref == "pol-dlp"
        assert ctx.rollback_plan == "Restore from snapshot snap-042"

    def test_empty_subject_ref_raises(self):
        with pytest.raises(ValueError):
            ApprovalContext(subject_ref="", summary="test", risk_tier=RiskTier.LOW)

    def test_empty_summary_raises(self):
        with pytest.raises(ValueError):
            ApprovalContext(subject_ref="ref://1", summary="", risk_tier=RiskTier.LOW)


class TestApprovalRequest:
    def test_valid_pending(self):
        ctx = ApprovalContext(subject_ref="tool://td-storage/delete", summary="Delete backup", risk_tier=RiskTier.HIGH)
        req = ApprovalRequest(
            approval_request_id="ar-1",
            run_id="run-001",
            requested_by="agent-admin",
            reason_type=ApprovalReasonType.HIGH_RISK_ACTION,
            status=ApprovalStatus.PENDING,
            context=ctx,
            eligible_approvers=[ApproverRef(approver_id="u-42", approver_role="security_lead")],
            expires_at="2026-07-04T18:00:00Z",
        )
        assert req.status == ApprovalStatus.PENDING
        assert len(req.eligible_approvers) == 1
        assert req.expires_at is not None

    def test_valid_approved(self):
        ctx = ApprovalContext(subject_ref="tool://td-search/read", summary="Search docs", risk_tier=RiskTier.LOW)
        req = ApprovalRequest(
            approval_request_id="ar-2",
            run_id="run-002",
            requested_by="agent-reader",
            reason_type=ApprovalReasonType.POLICY_TRIGGER,
            status=ApprovalStatus.APPROVED,
            context=ctx,
            eligible_approvers=[ApproverRef(approver_id="u-7", approver_role="admin")],
        )
        assert req.status == ApprovalStatus.APPROVED

    def test_empty_request_id_raises(self):
        ctx = ApprovalContext(subject_ref="ref://1", summary="test", risk_tier=RiskTier.LOW)
        with pytest.raises(ValueError):
            ApprovalRequest(
                approval_request_id="",
                run_id="run-1", requested_by="agent-x",
                reason_type=ApprovalReasonType.POLICY_TRIGGER,
                status=ApprovalStatus.PENDING,
                context=ctx,
                eligible_approvers=[ApproverRef(approver_id="u-1", approver_role="admin")],
            )

    def test_empty_run_id_raises(self):
        ctx = ApprovalContext(subject_ref="ref://1", summary="test", risk_tier=RiskTier.LOW)
        with pytest.raises(ValueError):
            ApprovalRequest(
                approval_request_id="ar-3",
                run_id="", requested_by="agent-x",
                reason_type=ApprovalReasonType.POLICY_TRIGGER,
                status=ApprovalStatus.PENDING,
                context=ctx,
                eligible_approvers=[ApproverRef(approver_id="u-1", approver_role="admin")],
            )

    def test_empty_requested_by_raises(self):
        ctx = ApprovalContext(subject_ref="ref://1", summary="test", risk_tier=RiskTier.LOW)
        with pytest.raises(ValueError):
            ApprovalRequest(
                approval_request_id="ar-4",
                run_id="run-1", requested_by="",
                reason_type=ApprovalReasonType.POLICY_TRIGGER,
                status=ApprovalStatus.PENDING,
                context=ctx,
                eligible_approvers=[ApproverRef(approver_id="u-1", approver_role="admin")],
            )

    def test_pending_without_approvers_raises(self):
        ctx = ApprovalContext(subject_ref="ref://1", summary="test", risk_tier=RiskTier.LOW)
        with pytest.raises(ValueError):
            ApprovalRequest(
                approval_request_id="ar-5",
                run_id="run-1", requested_by="agent-x",
                reason_type=ApprovalReasonType.POLICY_TRIGGER,
                status=ApprovalStatus.PENDING,
                context=ctx,
            )

    def test_non_pending_without_approvers_ok(self):
        ctx = ApprovalContext(subject_ref="ref://1", summary="test", risk_tier=RiskTier.LOW)
        req = ApprovalRequest(
            approval_request_id="ar-6",
            run_id="run-1", requested_by="agent-x",
            reason_type=ApprovalReasonType.POLICY_TRIGGER,
            status=ApprovalStatus.APPROVED,
            context=ctx,
        )
        assert req.status == ApprovalStatus.APPROVED


class TestApprovalDecision:
    def test_approve(self):
        approver = ApproverRef(approver_id="u-42", approver_role="security_lead")
        dec = ApprovalDecision(
            approval_decision_id="ad-1",
            approval_request_id="ar-1",
            decided_by=approver,
            decision=ApprovalDecisionType.APPROVE,
            justification="Risk acceptable for this operation",
            decided_at="2026-07-04T14:30:00Z",
        )
        assert dec.decision == ApprovalDecisionType.APPROVE

    def test_deny(self):
        approver = ApproverRef(approver_id="u-7", approver_role="admin")
        dec = ApprovalDecision(
            approval_decision_id="ad-2",
            approval_request_id="ar-2",
            decided_by=approver,
            decision=ApprovalDecisionType.DENY,
            justification="Production delete not authorized per policy pol-dlp",
            decided_at="2026-07-04T15:00:00Z",
        )
        assert dec.decision == ApprovalDecisionType.DENY

    def test_override_with_valid_role(self):
        approver = ApproverRef(approver_id="u-99", approver_role="security_override")
        dec = ApprovalDecision(
            approval_decision_id="ad-3",
            approval_request_id="ar-3",
            decided_by=approver,
            decision=ApprovalDecisionType.OVERRIDE,
            justification="Emergency override authorized per incident INC-042",
            decided_at="2026-07-04T16:00:00Z",
        )
        assert dec.decision == ApprovalDecisionType.OVERRIDE

    def test_override_without_role_raises(self):
        approver = ApproverRef(approver_id="u-7", approver_role="viewer")
        with pytest.raises(ValueError):
            ApprovalDecision(
                approval_decision_id="ad-4",
                approval_request_id="ar-3",
                decided_by=approver,
                decision=ApprovalDecisionType.OVERRIDE,
                justification="test",
                decided_at="2026-07-04T16:00:00Z",
            )

    def test_empty_decision_id_raises(self):
        approver = ApproverRef(approver_id="u-1", approver_role="admin")
        with pytest.raises(ValueError):
            ApprovalDecision(
                approval_decision_id="",
                approval_request_id="ar-1",
                decided_by=approver,
                decision=ApprovalDecisionType.APPROVE,
                justification="ok",
                decided_at="2026-07-04T12:00:00Z",
            )

    def test_empty_request_id_raises(self):
        approver = ApproverRef(approver_id="u-1", approver_role="admin")
        with pytest.raises(ValueError):
            ApprovalDecision(
                approval_decision_id="ad-5",
                approval_request_id="",
                decided_by=approver,
                decision=ApprovalDecisionType.APPROVE,
                justification="ok",
                decided_at="2026-07-04T12:00:00Z",
            )

    def test_empty_justification_raises(self):
        approver = ApproverRef(approver_id="u-1", approver_role="admin")
        with pytest.raises(ValueError):
            ApprovalDecision(
                approval_decision_id="ad-6",
                approval_request_id="ar-1",
                decided_by=approver,
                decision=ApprovalDecisionType.APPROVE,
                justification="",
                decided_at="2026-07-04T12:00:00Z",
            )

    def test_empty_decided_at_raises(self):
        approver = ApproverRef(approver_id="u-1", approver_role="admin")
        with pytest.raises(ValueError):
            ApprovalDecision(
                approval_decision_id="ad-7",
                approval_request_id="ar-1",
                decided_by=approver,
                decision=ApprovalDecisionType.APPROVE,
                justification="ok",
                decided_at="",
            )


class TestEscalationStep:
    def test_valid_minimal(self):
        step = EscalationStep(
            escalation_step_id="es-1",
            approval_request_id="ar-1",
            to_role="security_lead",
            escalation_status=EscalationStatus.IN_PROGRESS,
        )
        assert step.from_role is None
        assert step.note is None

    def test_valid_full(self):
        step = EscalationStep(
            escalation_step_id="es-2",
            approval_request_id="ar-1",
            from_role="admin",
            to_role="security_lead",
            escalation_status=EscalationStatus.RESOLVED,
            note="Security lead approved after initial admin deferral",
        )
        assert step.from_role == "admin"
        assert step.note is not None

    def test_empty_step_id_raises(self):
        with pytest.raises(ValueError):
            EscalationStep(
                escalation_step_id="",
                approval_request_id="ar-1",
                to_role="admin",
                escalation_status=EscalationStatus.NOT_ESCALATED,
            )

    def test_empty_request_id_raises(self):
        with pytest.raises(ValueError):
            EscalationStep(
                escalation_step_id="es-3",
                approval_request_id="",
                to_role="admin",
                escalation_status=EscalationStatus.NOT_ESCALATED,
            )

    def test_empty_to_role_raises(self):
        with pytest.raises(ValueError):
            EscalationStep(
                escalation_step_id="es-4",
                approval_request_id="ar-1",
                to_role="",
                escalation_status=EscalationStatus.NOT_ESCALATED,
            )


class TestApprovalEnvelope:
    def test_valid_minimal(self):
        ctx = ApprovalContext(subject_ref="tool://td-search/read", summary="Search docs", risk_tier=RiskTier.LOW)
        req = ApprovalRequest(
            approval_request_id="ar-1",
            run_id="run-001",
            requested_by="agent-reader",
            reason_type=ApprovalReasonType.POLICY_TRIGGER,
            status=ApprovalStatus.APPROVED,
            context=ctx,
        )
        env = ApprovalEnvelope(envelope_id="env-1", request=req)
        assert env.decision is None
        assert env.escalation_steps == []

    def test_valid_with_decision(self):
        ctx = ApprovalContext(subject_ref="tool://td-storage/delete", summary="Delete backup", risk_tier=RiskTier.CRITICAL)
        req = ApprovalRequest(
            approval_request_id="ar-2",
            run_id="run-002",
            requested_by="agent-admin",
            reason_type=ApprovalReasonType.HIGH_RISK_ACTION,
            status=ApprovalStatus.APPROVED,
            context=ctx,
            eligible_approvers=[ApproverRef(approver_id="u-42", approver_role="security_lead")],
        )
        approver = ApproverRef(approver_id="u-42", approver_role="security_lead")
        dec = ApprovalDecision(
            approval_decision_id="ad-1",
            approval_request_id="ar-2",
            decided_by=approver,
            decision=ApprovalDecisionType.APPROVE,
            justification="Approved with rollback plan",
            decided_at="2026-07-04T14:00:00Z",
        )
        env = ApprovalEnvelope(envelope_id="env-2", request=req, decision=dec)
        assert env.decision.decision == ApprovalDecisionType.APPROVE

    def test_decision_request_id_mismatch_raises(self):
        ctx = ApprovalContext(subject_ref="ref://1", summary="test", risk_tier=RiskTier.LOW)
        req = ApprovalRequest(
            approval_request_id="ar-1", run_id="run-1", requested_by="agent-x",
            reason_type=ApprovalReasonType.POLICY_TRIGGER,
            status=ApprovalStatus.PENDING,
            context=ctx,
            eligible_approvers=[ApproverRef(approver_id="u-1", approver_role="admin")],
        )
        approver = ApproverRef(approver_id="u-1", approver_role="admin")
        dec = ApprovalDecision(
            approval_decision_id="ad-1",
            approval_request_id="ar-WRONG",
            decided_by=approver,
            decision=ApprovalDecisionType.APPROVE,
            justification="test",
            decided_at="2026-07-04T12:00:00Z",
        )
        with pytest.raises(ValueError):
            ApprovalEnvelope(envelope_id="env-3", request=req, decision=dec)

    def test_escalation_step_request_id_mismatch_raises(self):
        ctx = ApprovalContext(subject_ref="ref://1", summary="test", risk_tier=RiskTier.LOW)
        req = ApprovalRequest(
            approval_request_id="ar-1", run_id="run-1", requested_by="agent-x",
            reason_type=ApprovalReasonType.POLICY_TRIGGER,
            status=ApprovalStatus.PENDING,
            context=ctx,
            eligible_approvers=[ApproverRef(approver_id="u-1", approver_role="admin")],
        )
        step = EscalationStep(
            escalation_step_id="es-1",
            approval_request_id="ar-WRONG",
            to_role="admin",
            escalation_status=EscalationStatus.IN_PROGRESS,
        )
        with pytest.raises(ValueError):
            ApprovalEnvelope(envelope_id="env-4", request=req, escalation_steps=[step])

    def test_escalate_decision_requires_steps(self):
        ctx = ApprovalContext(subject_ref="ref://1", summary="test", risk_tier=RiskTier.HIGH)
        req = ApprovalRequest(
            approval_request_id="ar-5",
            run_id="run-5", requested_by="agent-x",
            reason_type=ApprovalReasonType.HIGH_RISK_ACTION,
            status=ApprovalStatus.ESCALATED,
            context=ctx,
            eligible_approvers=[ApproverRef(approver_id="u-1", approver_role="admin")],
        )
        approver = ApproverRef(approver_id="u-1", approver_role="admin")
        dec = ApprovalDecision(
            approval_decision_id="ad-5",
            approval_request_id="ar-5",
            decided_by=approver,
            decision=ApprovalDecisionType.ESCALATE,
            justification="Needs higher authority",
            decided_at="2026-07-04T12:00:00Z",
        )
        with pytest.raises(ValueError):
            ApprovalEnvelope(envelope_id="env-5", request=req, decision=dec)

    def test_escalate_decision_with_steps_ok(self):
        ctx = ApprovalContext(subject_ref="ref://1", summary="test", risk_tier=RiskTier.HIGH)
        req = ApprovalRequest(
            approval_request_id="ar-6",
            run_id="run-6", requested_by="agent-x",
            reason_type=ApprovalReasonType.HIGH_RISK_ACTION,
            status=ApprovalStatus.ESCALATED,
            context=ctx,
            eligible_approvers=[ApproverRef(approver_id="u-1", approver_role="admin")],
        )
        approver = ApproverRef(approver_id="u-1", approver_role="admin")
        dec = ApprovalDecision(
            approval_decision_id="ad-6",
            approval_request_id="ar-6",
            decided_by=approver,
            decision=ApprovalDecisionType.ESCALATE,
            justification="Needs security lead",
            decided_at="2026-07-04T12:00:00Z",
        )
        step = EscalationStep(
            escalation_step_id="es-6",
            approval_request_id="ar-6",
            from_role="admin",
            to_role="security_lead",
            escalation_status=EscalationStatus.IN_PROGRESS,
        )
        env = ApprovalEnvelope(envelope_id="env-6", request=req, decision=dec, escalation_steps=[step])
        assert env.decision.decision == ApprovalDecisionType.ESCALATE
        assert len(env.escalation_steps) == 1

    def test_expired_request_with_approve_raises(self):
        ctx = ApprovalContext(subject_ref="ref://1", summary="test", risk_tier=RiskTier.LOW)
        req = ApprovalRequest(
            approval_request_id="ar-7", run_id="run-7", requested_by="agent-x",
            reason_type=ApprovalReasonType.POLICY_TRIGGER,
            status=ApprovalStatus.EXPIRED,
            context=ctx,
        )
        approver = ApproverRef(approver_id="u-1", approver_role="admin")
        dec = ApprovalDecision(
            approval_decision_id="ad-7",
            approval_request_id="ar-7",
            decided_by=approver,
            decision=ApprovalDecisionType.APPROVE,
            justification="Late approval",
            decided_at="2026-07-04T12:00:00Z",
        )
        with pytest.raises(ValueError):
            ApprovalEnvelope(envelope_id="env-7", request=req, decision=dec)

    def test_expired_request_with_deny_ok(self):
        ctx = ApprovalContext(subject_ref="ref://1", summary="test", risk_tier=RiskTier.LOW)
        req = ApprovalRequest(
            approval_request_id="ar-8", run_id="run-8", requested_by="agent-x",
            reason_type=ApprovalReasonType.POLICY_TRIGGER,
            status=ApprovalStatus.EXPIRED,
            context=ctx,
        )
        approver = ApproverRef(approver_id="u-1", approver_role="admin")
        dec = ApprovalDecision(
            approval_decision_id="ad-8",
            approval_request_id="ar-8",
            decided_by=approver,
            decision=ApprovalDecisionType.DENY,
            justification="Expired without action",
            decided_at="2026-07-04T12:00:00Z",
        )
        env = ApprovalEnvelope(envelope_id="env-8", request=req, decision=dec)
        assert env.decision.decision == ApprovalDecisionType.DENY

    def test_empty_envelope_id_raises(self):
        ctx = ApprovalContext(subject_ref="ref://1", summary="test", risk_tier=RiskTier.LOW)
        req = ApprovalRequest(
            approval_request_id="ar-9", run_id="run-9", requested_by="agent-x",
            reason_type=ApprovalReasonType.POLICY_TRIGGER,
            status=ApprovalStatus.APPROVED,
            context=ctx,
        )
        with pytest.raises(ValueError):
            ApprovalEnvelope(envelope_id="", request=req)


class TestSerialization:
    def test_request_roundtrip(self):
        ctx = ApprovalContext(subject_ref="tool://td-search/read", summary="Search", risk_tier=RiskTier.LOW)
        req = ApprovalRequest(
            approval_request_id="ar-rt",
            run_id="run-rt",
            requested_by="agent-x",
            reason_type=ApprovalReasonType.POLICY_TRIGGER,
            status=ApprovalStatus.PENDING,
            context=ctx,
            eligible_approvers=[ApproverRef(approver_id="u-1", approver_role="admin")],
        )
        raw = req.model_dump()
        restored = ApprovalRequest(**raw)
        assert restored.approval_request_id == req.approval_request_id
        assert restored.context.risk_tier == RiskTier.LOW

    def test_envelope_roundtrip(self):
        ctx = ApprovalContext(subject_ref="tool://td-storage/delete", summary="Delete", risk_tier=RiskTier.CRITICAL)
        req = ApprovalRequest(
            approval_request_id="ar-env",
            run_id="run-env",
            requested_by="agent-admin",
            reason_type=ApprovalReasonType.HIGH_RISK_ACTION,
            status=ApprovalStatus.PENDING,
            context=ctx,
            eligible_approvers=[ApproverRef(approver_id="u-42", approver_role="security_lead")],
        )
        approver = ApproverRef(approver_id="u-42", approver_role="security_lead")
        dec = ApprovalDecision(
            approval_decision_id="ad-env",
            approval_request_id="ar-env",
            decided_by=approver,
            decision=ApprovalDecisionType.DENY,
            justification="Not authorized",
            decided_at="2026-07-04T12:00:00Z",
        )
        step = EscalationStep(
            escalation_step_id="es-env",
            approval_request_id="ar-env",
            from_role="security_lead",
            to_role="security_override",
            escalation_status=EscalationStatus.NOT_ESCALATED,
        )
        env = ApprovalEnvelope(envelope_id="env-rt", request=req, decision=dec, escalation_steps=[step])
        raw = env.model_dump()
        restored = ApprovalEnvelope(**raw)
        assert restored.envelope_id == env.envelope_id
        assert restored.decision.decision == ApprovalDecisionType.DENY
        assert len(restored.escalation_steps) == 1


class TestIntegration:
    def test_high_risk_tool_action_approval_request(self):
        ctx = ApprovalContext(
            subject_ref="tool://td-storage/delete",
            summary="Delete production backup container prod-backup-2025",
            policy_ref="pol-dlp",
            risk_tier=RiskTier.CRITICAL,
            evidence_refs=["sig-del-001", "sig-del-002"],
            rollback_plan="Restore from snapshot snap-042",
        )
        req = ApprovalRequest(
            approval_request_id="ar-int-1",
            run_id="run-101",
            requested_by="agent-admin",
            reason_type=ApprovalReasonType.HIGH_RISK_ACTION,
            status=ApprovalStatus.PENDING,
            context=ctx,
            eligible_approvers=[
                ApproverRef(approver_id="u-42", approver_role="security_lead"),
                ApproverRef(approver_id="u-7", approver_role="admin"),
            ],
            expires_at="2026-07-04T18:00:00Z",
        )
        assert req.context.risk_tier == RiskTier.CRITICAL
        assert len(req.eligible_approvers) == 2

    def test_approved_by_eligible_reviewer(self):
        ctx = ApprovalContext(subject_ref="tool://td-search/read", summary="Full index search", risk_tier=RiskTier.MODERATE)
        req = ApprovalRequest(
            approval_request_id="ar-int-2",
            run_id="run-102",
            requested_by="agent-reader",
            reason_type=ApprovalReasonType.POLICY_TRIGGER,
            status=ApprovalStatus.APPROVED,
            context=ctx,
            eligible_approvers=[ApproverRef(approver_id="u-7", approver_role="admin")],
        )
        approver = ApproverRef(approver_id="u-7", approver_role="admin")
        dec = ApprovalDecision(
            approval_decision_id="ad-int-2",
            approval_request_id="ar-int-2",
            decided_by=approver,
            decision=ApprovalDecisionType.APPROVE,
            justification="Allowlisted search action; no sensitive data exposed",
            decided_at="2026-07-04T14:30:00Z",
        )
        env = ApprovalEnvelope(envelope_id="env-int-2", request=req, decision=dec)
        assert env.decision.decision == ApprovalDecisionType.APPROVE
        assert env.decision.decided_by.approver_id == "u-7"

    def test_denied_sensitive_data_access(self):
        ctx = ApprovalContext(
            subject_ref="memory://mem-042",
            summary="Cross-tenant memory access request",
            policy_ref="pol-mem",
            risk_tier=RiskTier.HIGH,
            evidence_refs=["sig-mem-001"],
        )
        req = ApprovalRequest(
            approval_request_id="ar-int-3",
            run_id="run-103",
            requested_by="agent-fetcher",
            reason_type=ApprovalReasonType.SENSITIVE_DATA_ACCESS,
            status=ApprovalStatus.DENIED,
            context=ctx,
            eligible_approvers=[ApproverRef(approver_id="u-42", approver_role="security_lead")],
        )
        approver = ApproverRef(approver_id="u-42", approver_role="security_lead")
        dec = ApprovalDecision(
            approval_decision_id="ad-int-3",
            approval_request_id="ar-int-3",
            decided_by=approver,
            decision=ApprovalDecisionType.DENY,
            justification="Cross-tenant access not permitted without explicit data sharing agreement",
            decided_at="2026-07-04T15:00:00Z",
        )
        env = ApprovalEnvelope(envelope_id="env-int-3", request=req, decision=dec)
        assert env.decision.decision == ApprovalDecisionType.DENY
        assert env.request.status == ApprovalStatus.DENIED

    def test_escalated_critical_request_to_higher_authority(self):
        ctx = ApprovalContext(
            subject_ref="tool://td-codex/execute",
            summary="Execute untrusted Python script in production",
            policy_ref="pol-codex",
            risk_tier=RiskTier.CRITICAL,
            evidence_refs=["sig-codex-001"],
            rollback_plan="Sandbox discard; no persistent side effects",
        )
        req = ApprovalRequest(
            approval_request_id="ar-int-4",
            run_id="run-104",
            requested_by="agent-coder",
            reason_type=ApprovalReasonType.HIGH_RISK_ACTION,
            status=ApprovalStatus.ESCALATED,
            context=ctx,
            eligible_approvers=[
                ApproverRef(approver_id="u-42", approver_role="security_lead"),
                ApproverRef(approver_id="u-7", approver_role="admin"),
            ],
        )
        approver = ApproverRef(approver_id="u-7", approver_role="admin")
        dec = ApprovalDecision(
            approval_decision_id="ad-int-4",
            approval_request_id="ar-int-4",
            decided_by=approver,
            decision=ApprovalDecisionType.ESCALATE,
            justification="Admin lacks authority for production code execution; escalating",
            decided_at="2026-07-04T16:00:00Z",
        )
        step = EscalationStep(
            escalation_step_id="es-int-4",
            approval_request_id="ar-int-4",
            from_role="admin",
            to_role="security_lead",
            escalation_status=EscalationStatus.IN_PROGRESS,
            note="Escalated by admin due to critical risk tier",
        )
        env = ApprovalEnvelope(envelope_id="env-int-4", request=req, decision=dec, escalation_steps=[step])
        assert env.decision.decision == ApprovalDecisionType.ESCALATE
        assert len(env.escalation_steps) == 1
        assert env.escalation_steps[0].to_role == "security_lead"

    def test_expired_request_blocks_execution(self):
        ctx = ApprovalContext(subject_ref="tool://td-storage/delete", summary="Delete old backup", risk_tier=RiskTier.HIGH)
        req = ApprovalRequest(
            approval_request_id="ar-int-5",
            run_id="run-105",
            requested_by="agent-admin",
            reason_type=ApprovalReasonType.HIGH_RISK_ACTION,
            status=ApprovalStatus.EXPIRED,
            context=ctx,
            eligible_approvers=[ApproverRef(approver_id="u-42", approver_role="security_lead")],
            expires_at="2026-07-04T12:00:00Z",
        )
        assert req.status == ApprovalStatus.EXPIRED
        with pytest.raises(ValueError):
            approver = ApproverRef(approver_id="u-42", approver_role="security_lead")
            dec = ApprovalDecision(
                approval_decision_id="ad-int-5",
                approval_request_id="ar-int-5",
                decided_by=approver,
                decision=ApprovalDecisionType.APPROVE,
                justification="Late approval",
                decided_at="2026-07-04T14:00:00Z",
            )
            ApprovalEnvelope(envelope_id="env-int-5", request=req, decision=dec)

    def test_all_status_values_accepted(self):
        ctx = ApprovalContext(subject_ref="ref://1", summary="test", risk_tier=RiskTier.LOW)
        for status in ApprovalStatus:
            approvers = []
            if status == ApprovalStatus.PENDING:
                approvers = [ApproverRef(approver_id="u-1", approver_role="admin")]
            req = ApprovalRequest(
                approval_request_id=f"ar-{status.value}",
                run_id="run-1",
                requested_by="agent-x",
                reason_type=ApprovalReasonType.POLICY_TRIGGER,
                status=status,
                context=ctx,
                eligible_approvers=approvers,
            )
            assert req.status == status

    def test_all_decision_types_accepted(self):
        ctx = ApprovalContext(subject_ref="ref://1", summary="test", risk_tier=RiskTier.LOW)
        req = ApprovalRequest(
            approval_request_id="ar-all-dec",
            run_id="run-1", requested_by="agent-x",
            reason_type=ApprovalReasonType.POLICY_TRIGGER,
            status=ApprovalStatus.APPROVED,
            context=ctx,
        )
        for dtype in ApprovalDecisionType:
            role = "admin"
            if dtype == ApprovalDecisionType.OVERRIDE:
                role = "security_override"
            approver = ApproverRef(approver_id="u-1", approver_role=role)
            dec = ApprovalDecision(
                approval_decision_id=f"ad-{dtype.value}",
                approval_request_id="ar-all-dec",
                decided_by=approver,
                decision=dtype,
                justification=f"Test {dtype.value}",
                decided_at="2026-07-04T12:00:00Z",
            )
            assert dec.decision == dtype

    def test_all_reason_types_accepted(self):
        ctx = ApprovalContext(subject_ref="ref://1", summary="test", risk_tier=RiskTier.LOW)
        for rtype in ApprovalReasonType:
            req = ApprovalRequest(
                approval_request_id=f"ar-{rtype.value}",
                run_id="run-1",
                requested_by="agent-x",
                reason_type=rtype,
                status=ApprovalStatus.PENDING,
                context=ctx,
                eligible_approvers=[ApproverRef(approver_id="u-1", approver_role="admin")],
            )
            assert req.reason_type == rtype
