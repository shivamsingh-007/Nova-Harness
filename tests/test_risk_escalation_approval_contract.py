import pytest
from datetime import datetime, timedelta
from models.risk_escalation_approval_contract import (
    RiskCategory, RiskLevel, EscalationTriggerType,
    ApprovalStatus, EscalationDisposition,
    RiskAssessmentRecord, RiskThresholdPolicy,
    EscalationRequestRecord, ApprovalRequirementRecord,
    HumanApprovalRecord, EscalationPathRecord,
    EscalationDecisionRecord, RiskEscalationApprovalEnvelope,
)


def make_assessment(**kw):
    return RiskAssessmentRecord(
        risk_assessment_id=kw.get("raid", "ra-001"),
        scope_ref=kw.get("ref", "task-001"),
        risk_category=kw.get("cat", RiskCategory.security),
        risk_level=kw.get("level", RiskLevel.low),
        risk_score=kw.get("score", 15.0),
        uncertainty_score=kw.get("uncertainty", 10.0),
        trigger_reasons=kw.get("reasons", ["Standard operation"]),
        evidence_refs=kw.get("evidence", ["log-001"]),
        assessed_by=kw.get("assessor", "system"),
    )


def make_threshold(**kw):
    return RiskThresholdPolicy(
        threshold_policy_id=kw.get("tpid", "tp-001"),
        risk_category=kw.get("cat"),
        minimum_risk_level=kw.get("level", RiskLevel.medium),
        minimum_risk_score=kw.get("score", 30.0),
        uncertainty_threshold=kw.get("uncertainty", 50.0),
        trigger_type=kw.get("trigger", EscalationTriggerType.risk_threshold),
        requires_human_approval=kw.get("approval", False),
        default_disposition=kw.get("disp"),
        timeout_sla_seconds=kw.get("timeout"),
        applicable_scope_types=kw.get("scopes", []),
    )


def make_escalation(**kw):
    return EscalationRequestRecord(
        escalation_request_id=kw.get("erid", "er-001"),
        scope_ref=kw.get("ref", "task-001"),
        trigger_type=kw.get("trigger", EscalationTriggerType.risk_threshold),
        trigger_ref=kw.get("tref"),
        risk_assessment_ref=kw.get("raref", "ra-001"),
        summary=kw.get("summary", "Risk threshold crossed"),
        requested_disposition=kw.get("disp"),
        requester_ref=kw.get("requester", "system"),
    )


def make_approval_requirement(**kw):
    return ApprovalRequirementRecord(
        approval_requirement_id=kw.get("arid", "ar-001"),
        escalation_request_id=kw.get("erid", "er-001"),
        approval_scope=kw.get("scope", "task_execution"),
        required_role_ids=kw.get("roles", ["security_lead"]),
        required_approver_count=kw.get("count", 1),
        allow_parallel_approval=kw.get("parallel", False),
        approval_deadline=kw.get("deadline"),
        approval_instructions=kw.get("instructions", "Review and approve or reject"),
    )


def make_human_approval(**kw):
    return HumanApprovalRecord(
        approval_id=kw.get("aid", "ha-001"),
        approval_requirement_id=kw.get("arid", "ar-001"),
        approver_ref=kw.get("approver", "user-alpha"),
        approval_status=kw.get("status", ApprovalStatus.approved),
        decision_notes=kw.get("notes", "Looks good"),
        imposed_constraints=kw.get("constraints", []),
    )


def make_path(**kw):
    return EscalationPathRecord(
        path_id=kw.get("pid", "path-001"),
        escalation_request_id=kw.get("erid", "er-001"),
        primary_approver_refs=kw.get("primary", ["security_lead"]),
        fallback_approver_refs=kw.get("fallback", ["manager"]),
        escalation_order=kw.get("order", 0),
        auto_escalate_on_timeout=kw.get("auto", False),
        next_timeout_sla_seconds=kw.get("sla"),
        path_notes=kw.get("notes"),
    )


def make_decision(**kw):
    return EscalationDecisionRecord(
        decision_id=kw.get("did", "dec-001"),
        escalation_request_id=kw.get("erid", "er-001"),
        approval_status=kw.get("status", ApprovalStatus.approved),
        escalation_disposition=kw.get("disp", EscalationDisposition.proceed),
        final_decider_ref=kw.get("decider", "user-alpha"),
        decision_reason=kw.get("reason", "Risk acceptable"),
        resume_constraints=kw.get("constraints", []),
        followup_actions=kw.get("followup", []),
    )


def make_envelope(**kw):
    ra = kw.get("assessment") or make_assessment()
    tp = kw.get("threshold")
    er = kw.get("escalation")
    req = kw.get("requirement")
    approvals = kw.get("approvals", [])
    path = kw.get("path")
    dec = kw.get("decision")
    return RiskEscalationApprovalEnvelope(
        envelope_id=kw.get("eid", "env-risk-001"),
        risk_assessment=ra,
        threshold_policy=tp,
        escalation_request=er,
        approval_requirement=req,
        approval_records=approvals,
        escalation_path=path,
        decision=dec,
    )


class TestRiskCategory:
    def test_all_values(self):
        assert len(RiskCategory) == 8
        assert RiskCategory.policy.value == "policy"
        assert RiskCategory.safety.value == "safety"
        assert RiskCategory.security.value == "security"
        assert RiskCategory.privacy.value == "privacy"
        assert RiskCategory.financial.value == "financial"
        assert RiskCategory.legal.value == "legal"
        assert RiskCategory.quality.value == "quality"
        assert RiskCategory.operational.value == "operational"


class TestRiskLevel:
    def test_all_values(self):
        assert len(RiskLevel) == 4
        assert RiskLevel.low.value == "low"
        assert RiskLevel.medium.value == "medium"
        assert RiskLevel.high.value == "high"
        assert RiskLevel.critical.value == "critical"


class TestEscalationTriggerType:
    def test_all_values(self):
        assert len(EscalationTriggerType) == 7
        assert EscalationTriggerType.risk_threshold.value == "risk_threshold"
        assert EscalationTriggerType.budget_overrun.value == "budget_overrun"
        assert EscalationTriggerType.policy_exception.value == "policy_exception"
        assert EscalationTriggerType.uncertainty_exceeded.value == "uncertainty_exceeded"
        assert EscalationTriggerType.approval_required_action.value == "approval_required_action"
        assert EscalationTriggerType.stalled_execution.value == "stalled_execution"
        assert EscalationTriggerType.manual_request.value == "manual_request"


class TestApprovalStatus:
    def test_all_values(self):
        assert len(ApprovalStatus) == 6
        assert ApprovalStatus.not_required.value == "not_required"
        assert ApprovalStatus.pending.value == "pending"
        assert ApprovalStatus.approved.value == "approved"
        assert ApprovalStatus.rejected.value == "rejected"
        assert ApprovalStatus.timed_out.value == "timed_out"
        assert ApprovalStatus.withdrawn.value == "withdrawn"


class TestEscalationDisposition:
    def test_all_values(self):
        assert len(EscalationDisposition) == 6
        assert EscalationDisposition.proceed.value == "proceed"
        assert EscalationDisposition.proceed_with_constraints.value == "proceed_with_constraints"
        assert EscalationDisposition.pause_for_review.value == "pause_for_review"
        assert EscalationDisposition.return_for_rework.value == "return_for_rework"
        assert EscalationDisposition.reject.value == "reject"
        assert EscalationDisposition.escalate_further.value == "escalate_further"


class TestRiskAssessmentRecord:
    def test_valid_assessment(self):
        a = make_assessment()
        assert a.risk_assessment_id == "ra-001"
        assert a.risk_score == 15.0
        assert a.uncertainty_score == 10.0

    def test_blank_assessment_id_raises(self):
        with pytest.raises(ValueError):
            make_assessment(raid="   ")

    def test_blank_scope_ref_raises(self):
        with pytest.raises(ValueError):
            make_assessment(ref="   ")

    def test_risk_score_bounds(self):
        with pytest.raises(ValueError):
            make_assessment(score=-1.0)
        with pytest.raises(ValueError):
            make_assessment(score=101.0)

    def test_uncertainty_score_bounds(self):
        with pytest.raises(ValueError):
            make_assessment(uncertainty=-1.0)
        with pytest.raises(ValueError):
            make_assessment(uncertainty=101.0)

    def test_default_fields(self):
        a = RiskAssessmentRecord(
            risk_assessment_id="ra-002",
            scope_ref="task-002",
            risk_category=RiskCategory.financial,
            risk_level=RiskLevel.low,
        )
        assert a.risk_score == 0.0
        assert a.uncertainty_score == 0.0
        assert a.trigger_reasons == []
        assert a.evidence_refs == []


class TestRiskThresholdPolicy:
    def test_valid_threshold(self):
        t = make_threshold()
        assert t.threshold_policy_id == "tp-001"

    def test_blank_threshold_policy_id_raises(self):
        with pytest.raises(ValueError):
            make_threshold(tpid="   ")

    def test_requires_approval_blocks_auto_proceed(self):
        with pytest.raises(ValueError):
            make_threshold(approval=True, disp=EscalationDisposition.proceed)

    def test_requires_approval_allows_pause(self):
        t = make_threshold(approval=True, disp=EscalationDisposition.pause_for_review)
        assert t.requires_human_approval

    def test_high_critical_requires_human_approval(self):
        with pytest.raises(ValueError):
            make_threshold(level=RiskLevel.high, approval=False)
        with pytest.raises(ValueError):
            make_threshold(level=RiskLevel.critical, approval=False)

    def test_low_medium_allows_no_approval(self):
        t = make_threshold(level=RiskLevel.low, approval=False)
        assert not t.requires_human_approval
        t2 = make_threshold(level=RiskLevel.medium, approval=False)
        assert not t2.requires_human_approval


class TestEscalationRequestRecord:
    def test_valid_escalation_request(self):
        e = make_escalation()
        assert e.escalation_request_id == "er-001"

    def test_blank_request_id_raises(self):
        with pytest.raises(ValueError):
            make_escalation(erid="   ")

    def test_blank_scope_ref_raises(self):
        with pytest.raises(ValueError):
            make_escalation(ref="   ")

    def test_blank_summary_raises(self):
        with pytest.raises(ValueError):
            make_escalation(summary="   ")


class TestApprovalRequirementRecord:
    def test_valid_requirement(self):
        r = make_approval_requirement()
        assert r.approval_requirement_id == "ar-001"

    def test_blank_requirement_id_raises(self):
        with pytest.raises(ValueError):
            make_approval_requirement(arid="   ")

    def test_blank_escalation_request_id_raises(self):
        with pytest.raises(ValueError):
            make_approval_requirement(erid="   ")

    def test_required_approver_count_must_be_positive(self):
        with pytest.raises(ValueError):
            make_approval_requirement(count=0)
        with pytest.raises(ValueError):
            make_approval_requirement(count=-1)


class TestHumanApprovalRecord:
    def test_valid_approval(self):
        a = make_human_approval()
        assert a.approval_id == "ha-001"

    def test_blank_approval_id_raises(self):
        with pytest.raises(ValueError):
            make_human_approval(aid="   ")

    def test_blank_approval_requirement_id_raises(self):
        with pytest.raises(ValueError):
            make_human_approval(arid="   ")

    def test_approved_requires_approver_and_reason(self):
        with pytest.raises(ValueError):
            make_human_approval(approver=None, notes="")
        with pytest.raises(ValueError):
            make_human_approval(approver="user-alpha", notes="")
        with pytest.raises(ValueError):
            make_human_approval(approver=None, notes="Approved")

    def test_rejected_requires_approver_and_reason(self):
        with pytest.raises(ValueError):
            make_human_approval(status=ApprovalStatus.rejected, approver=None, notes="Rejected")
        with pytest.raises(ValueError):
            make_human_approval(status=ApprovalStatus.rejected, notes="")

    def test_pending_allows_no_approver(self):
        a = make_human_approval(status=ApprovalStatus.pending, approver=None, notes=None)
        assert a.approval_status == ApprovalStatus.pending

    def test_not_required_allows_no_approver(self):
        a = make_human_approval(status=ApprovalStatus.not_required, approver=None, notes=None)
        assert a.approval_status == ApprovalStatus.not_required

    def test_timed_out_allows_no_approver(self):
        a = make_human_approval(status=ApprovalStatus.timed_out, approver=None, notes=None)
        assert a.approval_status == ApprovalStatus.timed_out

    def test_withdrawn_allows_no_approver(self):
        a = make_human_approval(status=ApprovalStatus.withdrawn, approver=None, notes=None)
        assert a.approval_status == ApprovalStatus.withdrawn


class TestEscalationPathRecord:
    def test_valid_path(self):
        p = make_path()
        assert p.path_id == "path-001"

    def test_blank_path_id_raises(self):
        with pytest.raises(ValueError):
            make_path(pid="   ")

    def test_blank_escalation_request_id_raises(self):
        with pytest.raises(ValueError):
            make_path(erid="   ")

    def test_timeout_path_requires_sla(self):
        with pytest.raises(ValueError):
            make_path(auto=True, sla=None)

    def test_timeout_path_with_sla_ok(self):
        p = make_path(auto=True, sla=300)
        assert p.auto_escalate_on_timeout
        assert p.next_timeout_sla_seconds == 300

    def test_no_timeout_no_sla_ok(self):
        p = make_path(auto=False, sla=None)
        assert not p.auto_escalate_on_timeout


class TestEscalationDecisionRecord:
    def test_valid_decision(self):
        d = make_decision()
        assert d.decision_id == "dec-001"

    def test_blank_decision_id_raises(self):
        with pytest.raises(ValueError):
            make_decision(did="   ")

    def test_blank_escalation_request_id_raises(self):
        with pytest.raises(ValueError):
            make_decision(erid="   ")

    def test_approved_requires_decider_and_reason(self):
        with pytest.raises(ValueError):
            make_decision(decider=None, reason="")
        with pytest.raises(ValueError):
            make_decision(decider="user-alpha", reason="")
        with pytest.raises(ValueError):
            make_decision(decider=None, reason="Approved")

    def test_rejected_requires_decider_and_reason(self):
        with pytest.raises(ValueError):
            make_decision(status=ApprovalStatus.rejected, disp=EscalationDisposition.reject, decider=None, reason="Rejected")
        with pytest.raises(ValueError):
            make_decision(status=ApprovalStatus.rejected, disp=EscalationDisposition.reject, reason="")

    def test_proceed_with_constraints_requires_resume_constraints(self):
        with pytest.raises(ValueError):
            make_decision(disp=EscalationDisposition.proceed_with_constraints, constraints=[])

    def test_proceed_with_constraints_with_constraints_ok(self):
        d = make_decision(disp=EscalationDisposition.proceed_with_constraints, constraints=["audit_log", "rate_limit"])
        assert len(d.resume_constraints) == 2

    def test_proceed_allows_empty_constraints(self):
        d = make_decision(disp=EscalationDisposition.proceed, constraints=[])
        assert d.escalation_disposition == EscalationDisposition.proceed


class TestRiskEscalationApprovalEnvelope:
    def test_valid_envelope(self):
        e = make_envelope()
        assert e.envelope_id == "env-risk-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValueError):
            make_envelope(eid="   ")

    def test_low_risk_no_threshold_passes(self):
        e = make_envelope(threshold=None, escalation=None)
        assert e.envelope_id == "env-risk-001"

    def test_requires_human_approval_blocks_auto_proceed(self):
        ra = make_assessment(level=RiskLevel.high, score=75.0)
        tp = make_threshold(level=RiskLevel.high, approval=True, disp=EscalationDisposition.pause_for_review, score=50.0)
        er = make_escalation()
        req = make_approval_requirement()
        dec = make_decision(disp=EscalationDisposition.proceed, decider="user-alpha", reason="Looks fine")
        with pytest.raises(ValueError):
            make_envelope(assessment=ra, threshold=tp, escalation=er, requirement=req, approvals=[], decision=dec)

    def test_requires_human_approval_with_approvals_ok(self):
        ra = make_assessment(level=RiskLevel.high, score=75.0)
        tp = make_threshold(level=RiskLevel.high, approval=True, disp=EscalationDisposition.pause_for_review, score=50.0)
        er = make_escalation()
        req = make_approval_requirement()
        ha = make_human_approval()
        dec = make_decision(disp=EscalationDisposition.proceed, decider="user-alpha", reason="Approved by security")
        e = make_envelope(assessment=ra, threshold=tp, escalation=er, requirement=req, approvals=[ha], decision=dec)
        assert e.envelope_id == "env-risk-001"

    def test_timed_out_requires_escalation_path(self):
        ra = make_assessment(level=RiskLevel.medium, score=40.0)
        tp = make_threshold(level=RiskLevel.medium, approval=True, disp=EscalationDisposition.pause_for_review, score=30.0)
        er = make_escalation()
        req = make_approval_requirement()
        ha = make_human_approval(status=ApprovalStatus.timed_out, approver=None, notes=None)
        dec = make_decision(status=ApprovalStatus.timed_out, disp=EscalationDisposition.escalate_further, decider="system", reason="Timed out")
        with pytest.raises(ValueError):
            make_envelope(assessment=ra, threshold=tp, escalation=er, requirement=req, approvals=[ha], decision=dec)

    def test_timed_out_with_path_ok(self):
        ra = make_assessment(level=RiskLevel.medium, score=40.0)
        tp = make_threshold(level=RiskLevel.medium, approval=True, disp=EscalationDisposition.pause_for_review, score=30.0)
        er = make_escalation()
        req = make_approval_requirement()
        ha = make_human_approval(status=ApprovalStatus.timed_out, approver=None, notes=None)
        pa = make_path(auto=True, sla=600)
        dec = make_decision(status=ApprovalStatus.timed_out, disp=EscalationDisposition.escalate_further, decider="system", reason="Timed out, escalating")
        e = make_envelope(assessment=ra, threshold=tp, escalation=er, requirement=req, approvals=[ha], path=pa, decision=dec)
        assert e.envelope_id == "env-risk-001"


class TestExampleScenarios:
    def test_low_risk_action_proceeds_automatically(self):
        ra = RiskAssessmentRecord(
            risk_assessment_id="ra-low",
            scope_ref="task-low-risk",
            risk_category=RiskCategory.quality,
            risk_level=RiskLevel.low,
            risk_score=5.0,
            uncertainty_score=5.0,
            trigger_reasons=["Minor code formatting change"],
            evidence_refs=["code-review-001"],
            assessed_by="system",
        )
        tp = RiskThresholdPolicy(
            threshold_policy_id="tp-auto",
            minimum_risk_level=RiskLevel.medium,
            minimum_risk_score=30.0,
            uncertainty_threshold=50.0,
            trigger_type=EscalationTriggerType.risk_threshold,
            requires_human_approval=False,
            default_disposition=EscalationDisposition.proceed,
        )
        e = RiskEscalationApprovalEnvelope(
            envelope_id="env-low-risk",
            risk_assessment=ra,
            threshold_policy=tp,
        )
        assert e.risk_assessment.risk_level == RiskLevel.low
        assert e.threshold_policy.requires_human_approval is False

    def test_high_risk_action_pauses_for_human_approval(self):
        ra = RiskAssessmentRecord(
            risk_assessment_id="ra-high",
            scope_ref="task-high-risk",
            risk_category=RiskCategory.security,
            risk_level=RiskLevel.high,
            risk_score=75.0,
            uncertainty_score=20.0,
            trigger_reasons=["Database access with sensitive PII"],
            evidence_refs=["data-flow-003"],
            assessed_by="system",
        )
        tp = RiskThresholdPolicy(
            threshold_policy_id="tp-approval",
            minimum_risk_level=RiskLevel.high,
            minimum_risk_score=50.0,
            uncertainty_threshold=50.0,
            trigger_type=EscalationTriggerType.risk_threshold,
            requires_human_approval=True,
            default_disposition=EscalationDisposition.pause_for_review,
            timeout_sla_seconds=3600,
        )
        er = EscalationRequestRecord(
            escalation_request_id="er-high",
            scope_ref="task-high-risk",
            trigger_type=EscalationTriggerType.risk_threshold,
            risk_assessment_ref="ra-high",
            summary="High-risk security action requires approval",
            requester_ref="system",
        )
        req = ApprovalRequirementRecord(
            approval_requirement_id="ar-high",
            escalation_request_id="er-high",
            required_role_ids=["security_lead"],
            required_approver_count=1,
        )
        e = RiskEscalationApprovalEnvelope(
            envelope_id="env-high-risk",
            risk_assessment=ra,
            threshold_policy=tp,
            escalation_request=er,
            approval_requirement=req,
        )
        assert e.risk_assessment.risk_level == RiskLevel.high
        assert e.escalation_request.trigger_type == EscalationTriggerType.risk_threshold

    def test_budget_overrun_triggers_escalation_and_approved_increase(self):
        ra = RiskAssessmentRecord(
            risk_assessment_id="ra-budget",
            scope_ref="task-overrun",
            risk_category=RiskCategory.financial,
            risk_level=RiskLevel.medium,
            risk_score=45.0,
            uncertainty_score=15.0,
            trigger_reasons=["Token budget exceeded by 40%"],
            evidence_refs=["budget-alert-003"],
            assessed_by="system",
        )
        tp = RiskThresholdPolicy(
            threshold_policy_id="tp-budget",
            minimum_risk_level=RiskLevel.medium,
            minimum_risk_score=30.0,
            uncertainty_threshold=50.0,
            trigger_type=EscalationTriggerType.budget_overrun,
            requires_human_approval=True,
            default_disposition=EscalationDisposition.pause_for_review,
        )
        er = EscalationRequestRecord(
            escalation_request_id="er-budget",
            scope_ref="task-overrun",
            trigger_type=EscalationTriggerType.budget_overrun,
            trigger_ref="budget-alert-003",
            risk_assessment_ref="ra-budget",
            summary="Budget overrun on task-overrun, 40% above allocation",
            requester_ref="budget_enforcer",
        )
        req = ApprovalRequirementRecord(
            approval_requirement_id="ar-budget",
            escalation_request_id="er-budget",
            required_role_ids=["manager"],
            required_approver_count=1,
            approval_instructions="Review budget overrun and approve increase or reject",
        )
        ha = HumanApprovalRecord(
            approval_id="ha-budget",
            approval_requirement_id="ar-budget",
            approver_ref="manager-alpha",
            approval_status=ApprovalStatus.approved,
            decision_notes="Approved additional 20K token allocation",
            imposed_constraints=["Add monitoring on token usage"],
        )
        dec = EscalationDecisionRecord(
            decision_id="dec-budget",
            escalation_request_id="er-budget",
            approval_status=ApprovalStatus.approved,
            escalation_disposition=EscalationDisposition.proceed_with_constraints,
            final_decider_ref="manager-alpha",
            decision_reason="Budget increase approved with monitoring constraint",
            resume_constraints=["Add monitoring on token usage"],
            followup_actions=["Log budget increase decision"],
        )
        e = RiskEscalationApprovalEnvelope(
            envelope_id="env-budget-overrun",
            risk_assessment=ra,
            threshold_policy=tp,
            escalation_request=er,
            approval_requirement=req,
            approval_records=[ha],
            decision=dec,
        )
        assert e.decision.escalation_disposition == EscalationDisposition.proceed_with_constraints
        assert "Add monitoring on token usage" in e.decision.resume_constraints

    def test_stalled_approval_times_out_and_escalates_to_fallback(self):
        ra = RiskAssessmentRecord(
            risk_assessment_id="ra-timeout",
            scope_ref="task-timeout",
            risk_category=RiskCategory.operational,
            risk_level=RiskLevel.medium,
            risk_score=35.0,
            uncertainty_score=60.0,
            trigger_reasons=["Stalled execution pending approval"],
            evidence_refs=["timer-002"],
            assessed_by="system",
        )
        tp = RiskThresholdPolicy(
            threshold_policy_id="tp-timeout",
            minimum_risk_level=RiskLevel.medium,
            minimum_risk_score=20.0,
            uncertainty_threshold=50.0,
            trigger_type=EscalationTriggerType.stalled_execution,
            requires_human_approval=True,
            default_disposition=EscalationDisposition.pause_for_review,
            timeout_sla_seconds=1800,
        )
        er = EscalationRequestRecord(
            escalation_request_id="er-timeout",
            scope_ref="task-timeout",
            trigger_type=EscalationTriggerType.stalled_execution,
            risk_assessment_ref="ra-timeout",
            summary="Approval stalled for 30 minutes, escalating",
            requester_ref="scheduler",
        )
        req = ApprovalRequirementRecord(
            approval_requirement_id="ar-timeout",
            escalation_request_id="er-timeout",
            required_role_ids=["lead"],
            required_approver_count=1,
            approval_deadline=datetime.now() + timedelta(hours=1),
        )
        ha = HumanApprovalRecord(
            approval_id="ha-timeout",
            approval_requirement_id="ar-timeout",
            approval_status=ApprovalStatus.timed_out,
        )
        pa = EscalationPathRecord(
            path_id="path-timeout",
            escalation_request_id="er-timeout",
            primary_approver_refs=["lead-alpha"],
            fallback_approver_refs=["manager-beta"],
            escalation_order=1,
            auto_escalate_on_timeout=True,
            next_timeout_sla_seconds=900,
            path_notes="Escalate to manager if lead does not respond in 30 min",
        )
        dec = EscalationDecisionRecord(
            decision_id="dec-timeout",
            escalation_request_id="er-timeout",
            approval_status=ApprovalStatus.timed_out,
            escalation_disposition=EscalationDisposition.escalate_further,
            final_decider_ref="system",
            decision_reason="Primary approver timed out, escalating to fallback",
            followup_actions=["Notify manager-beta of escalation"],
        )
        e = RiskEscalationApprovalEnvelope(
            envelope_id="env-timeout",
            risk_assessment=ra,
            threshold_policy=tp,
            escalation_request=er,
            approval_requirement=req,
            approval_records=[ha],
            escalation_path=pa,
            decision=dec,
        )
        assert e.decision.escalation_disposition == EscalationDisposition.escalate_further
        assert e.escalation_path.auto_escalate_on_timeout

    def test_rejected_risky_action_returned_for_rework(self):
        ra = RiskAssessmentRecord(
            risk_assessment_id="ra-reject",
            scope_ref="task-risky",
            risk_category=RiskCategory.safety,
            risk_level=RiskLevel.critical,
            risk_score=92.0,
            uncertainty_score=10.0,
            trigger_reasons=["Unsafe file system operation in production"],
            evidence_refs=["fs-audit-007"],
            assessed_by="system",
        )
        tp = RiskThresholdPolicy(
            threshold_policy_id="tp-reject",
            minimum_risk_level=RiskLevel.high,
            minimum_risk_score=70.0,
            uncertainty_threshold=30.0,
            trigger_type=EscalationTriggerType.risk_threshold,
            requires_human_approval=True,
            default_disposition=EscalationDisposition.pause_for_review,
        )
        er = EscalationRequestRecord(
            escalation_request_id="er-reject",
            scope_ref="task-risky",
            trigger_type=EscalationTriggerType.risk_threshold,
            risk_assessment_ref="ra-reject",
            summary="Critical safety risk in production FS operation",
            requester_ref="system",
        )
        req = ApprovalRequirementRecord(
            approval_requirement_id="ar-reject",
            escalation_request_id="er-reject",
            required_role_ids=["safety_officer", "senior_engineer"],
            required_approver_count=2,
            allow_parallel_approval=True,
        )
        ha1 = HumanApprovalRecord(
            approval_id="ha-reject-1",
            approval_requirement_id="ar-reject",
            approver_ref="safety-officer-alpha",
            approval_status=ApprovalStatus.rejected,
            decision_notes="Operation is unsafe — must use sandboxed alternative",
            imposed_constraints=["Must use read-only mode first"],
        )
        dec = EscalationDecisionRecord(
            decision_id="dec-reject",
            escalation_request_id="er-reject",
            approval_status=ApprovalStatus.rejected,
            escalation_disposition=EscalationDisposition.return_for_rework,
            final_decider_ref="safety-officer-alpha",
            decision_reason="Safety officer rejected the action — unsafe production FS operation",
            resume_constraints=["Must use read-only mode first"],
            followup_actions=["Redesign to use sandboxed FS", "Re-assess after changes"],
        )
        e = RiskEscalationApprovalEnvelope(
            envelope_id="env-reject",
            risk_assessment=ra,
            threshold_policy=tp,
            escalation_request=er,
            approval_requirement=req,
            approval_records=[ha1],
            decision=dec,
        )
        assert e.decision.escalation_disposition == EscalationDisposition.return_for_rework
        assert "safety-officer-alpha" in e.decision.final_decider_ref
