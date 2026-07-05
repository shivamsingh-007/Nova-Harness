import pytest
from pydantic import ValidationError
from models.policy_decision_contract import (
    PolicyDecisionStatus, ApprovalRequirement, EscalationLevel, PolicyScope,
    PolicyRuleRef, DecisionCondition, ApprovalActorRef,
    PolicyDecisionRecord, ApprovalGateRecord, PolicyDecisionEnvelope,
)


def make_rule_ref(**overrides) -> PolicyRuleRef:
    defaults = dict(rule_id="rule-001", rule_name="no_delete_protected_paths")
    defaults.update(overrides)
    return PolicyRuleRef(**defaults)


def make_condition(**overrides) -> DecisionCondition:
    defaults = dict(condition_id="cond-001", description="File is in protected paths list", satisfied=True)
    defaults.update(overrides)
    return DecisionCondition(**defaults)


def make_actor(**overrides) -> ApprovalActorRef:
    defaults = dict(actor_id="user-042", actor_type="human", display_name="Alice")
    defaults.update(overrides)
    return ApprovalActorRef(**defaults)


def make_decision(**overrides) -> PolicyDecisionRecord:
    defaults = dict(
        decision_id="pd-001", scope=PolicyScope.TOOL_CALL,
        status=PolicyDecisionStatus.ALLOW, reason="Action is permitted by policy",
    )
    defaults.update(overrides)
    return PolicyDecisionRecord(**defaults)


def make_gate(**overrides) -> ApprovalGateRecord:
    defaults = dict(gate_id="gate-001", decision_id="pd-001", approved=True, approval_actor=make_actor(), approval_note="Looks good")
    defaults.update(overrides)
    return ApprovalGateRecord(**defaults)


def make_envelope(**overrides) -> PolicyDecisionEnvelope:
    defaults = dict(
        envelope_id="env-001", run_id="run-001", agent_id="agent-code",
        decision=make_decision(),
    )
    defaults.update(overrides)
    return PolicyDecisionEnvelope(**defaults)


class TestEnums:
    def test_policy_decision_status_values(self):
        assert PolicyDecisionStatus.ALLOW.value == "allow"
        assert PolicyDecisionStatus.BLOCK.value == "block"
        assert PolicyDecisionStatus.REQUIRE_APPROVAL.value == "require_approval"
        assert PolicyDecisionStatus.ESCALATE.value == "escalate"
        assert PolicyDecisionStatus.DEFER.value == "defer"
        assert len(PolicyDecisionStatus) == 5

    def test_approval_requirement_values(self):
        assert ApprovalRequirement.NONE.value == "none"
        assert ApprovalRequirement.HUMAN_REVIEW.value == "human_review"
        assert ApprovalRequirement.OWNER_APPROVAL.value == "owner_approval"
        assert ApprovalRequirement.SECURITY_APPROVAL.value == "security_approval"
        assert ApprovalRequirement.FINANCE_APPROVAL.value == "finance_approval"
        assert len(ApprovalRequirement) == 5

    def test_escalation_level_values(self):
        assert EscalationLevel.NONE.value == "none"
        assert EscalationLevel.TEAM_LEAD.value == "team_lead"
        assert EscalationLevel.STAFF.value == "staff"
        assert EscalationLevel.SECURITY.value == "security"
        assert EscalationLevel.EXECUTIVE.value == "executive"
        assert len(EscalationLevel) == 5

    def test_policy_scope_values(self):
        assert PolicyScope.TASK.value == "task"
        assert PolicyScope.TOOL_CALL.value == "tool_call"
        assert PolicyScope.MODEL_CALL.value == "model_call"
        assert PolicyScope.CHECKPOINT.value == "checkpoint"
        assert PolicyScope.SESSION.value == "session"
        assert PolicyScope.RESOURCE.value == "resource"
        assert len(PolicyScope) == 6


class TestPolicyRuleRef:
    def test_valid(self):
        r = make_rule_ref()
        assert r.rule_id == "rule-001"

    def test_with_version(self):
        r = make_rule_ref(version="2.1")
        assert r.version == "2.1"

    def test_blank_rule_id_raises(self):
        with pytest.raises(ValidationError):
            make_rule_ref(rule_id="")

    def test_blank_rule_name_raises(self):
        with pytest.raises(ValidationError):
            make_rule_ref(rule_name="")


class TestDecisionCondition:
    def test_valid(self):
        c = make_condition()
        assert c.condition_id == "cond-001"
        assert c.satisfied is True

    def test_not_satisfied(self):
        c = make_condition(satisfied=False)
        assert c.satisfied is False

    def test_blank_condition_id_raises(self):
        with pytest.raises(ValidationError):
            make_condition(condition_id="")

    def test_blank_description_raises(self):
        with pytest.raises(ValidationError):
            make_condition(description="")

    def test_conditions_order_preserved(self):
        conds = [
            make_condition(condition_id="c-1"),
            make_condition(condition_id="c-2"),
            make_condition(condition_id="c-3"),
        ]
        assert [c.condition_id for c in conds] == ["c-1", "c-2", "c-3"]


class TestApprovalActorRef:
    def test_valid(self):
        a = make_actor()
        assert a.actor_id == "user-042"

    def test_blank_actor_id_raises(self):
        with pytest.raises(ValidationError):
            make_actor(actor_id="")

    def test_blank_actor_type_raises(self):
        with pytest.raises(ValidationError):
            make_actor(actor_type="")


class TestPolicyDecisionRecord:
    def test_valid_allow(self):
        d = make_decision()
        assert d.status == PolicyDecisionStatus.ALLOW

    def test_with_rule_refs_and_conditions(self):
        d = make_decision(
            rule_refs=[make_rule_ref()],
            conditions=[make_condition()],
        )
        assert len(d.rule_refs) == 1
        assert len(d.conditions) == 1

    def test_all_statuses_accepted(self):
        for s in PolicyDecisionStatus:
            kwargs = dict(status=s, reason="test")
            if s == PolicyDecisionStatus.REQUIRE_APPROVAL:
                kwargs["next_action"] = "wait_for_approval"
            if s == PolicyDecisionStatus.ESCALATE:
                kwargs["escalation_level"] = EscalationLevel.SECURITY
            d = PolicyDecisionRecord(decision_id="pd-x", scope=PolicyScope.TASK, **kwargs)
            assert d.status == s

    def test_blank_decision_id_raises(self):
        with pytest.raises(ValidationError):
            make_decision(decision_id="")

    def test_blank_reason_raises(self):
        with pytest.raises(ValidationError):
            make_decision(reason="")

    def test_block_must_not_have_approval_requirement(self):
        with pytest.raises(ValidationError, match="BLOCK"):
            make_decision(
                status=PolicyDecisionStatus.BLOCK,
                approval_requirement=ApprovalRequirement.HUMAN_REVIEW,
            )

    def test_block_with_none_approval_valid(self):
        d = make_decision(status=PolicyDecisionStatus.BLOCK)
        assert d.approval_requirement == ApprovalRequirement.NONE

    def test_require_approval_needs_next_action(self):
        with pytest.raises(ValidationError, match="next_action"):
            make_decision(status=PolicyDecisionStatus.REQUIRE_APPROVAL)

    def test_require_approval_with_next_action_valid(self):
        d = make_decision(status=PolicyDecisionStatus.REQUIRE_APPROVAL, next_action="wait_for_approval")
        assert d.next_action == "wait_for_approval"

    def test_escalate_needs_non_none_level(self):
        with pytest.raises(ValidationError, match="ESCALATE"):
            make_decision(status=PolicyDecisionStatus.ESCALATE)

    def test_escalate_with_level_valid(self):
        d = make_decision(status=PolicyDecisionStatus.ESCALATE, escalation_level=EscalationLevel.SECURITY)
        assert d.escalation_level == EscalationLevel.SECURITY

    def test_all_scopes_accepted(self):
        for s in PolicyScope:
            d = make_decision(scope=s)
            assert d.scope == s

    def test_all_approval_requirements_accepted(self):
        for a in ApprovalRequirement:
            d = make_decision(approval_requirement=a)
            assert d.approval_requirement == a


class TestApprovalGateRecord:
    def test_valid_approved(self):
        g = make_gate()
        assert g.approved is True

    def test_valid_not_approved(self):
        g = make_gate(approved=False)
        assert g.approved is False

    def test_approved_needs_actor_or_note(self):
        with pytest.raises(ValidationError, match="approval_actor or approval_note"):
            ApprovalGateRecord(gate_id="g-001", decision_id="pd-001", approved=True)

    def test_approved_with_actor_only_valid(self):
        g = ApprovalGateRecord(gate_id="g-001", decision_id="pd-001", approved=True, approval_actor=make_actor())
        assert g.approved is True

    def test_approved_with_note_only_valid(self):
        g = ApprovalGateRecord(gate_id="g-001", decision_id="pd-001", approved=True, approval_note="Approved via bulk policy")
        assert g.approval_note == "Approved via bulk policy"

    def test_not_approved_no_actor_or_note_valid(self):
        g = ApprovalGateRecord(gate_id="g-001", decision_id="pd-001", approved=False)
        assert g.approved is False

    def test_blank_gate_id_raises(self):
        with pytest.raises(ValidationError):
            make_gate(gate_id="")

    def test_blank_decision_id_raises(self):
        with pytest.raises(ValidationError):
            make_gate(decision_id="")


class TestPolicyDecisionEnvelope:
    def test_valid_allow_envelope(self):
        e = make_envelope()
        assert e.decision.status == PolicyDecisionStatus.ALLOW

    def test_with_approval_gate(self):
        e = make_envelope(approval_gate=make_gate())
        assert e.approval_gate.approved is True

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="")

    def test_blank_run_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(run_id="")

    def test_blank_agent_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(agent_id="   ")

    def test_approval_gate_decision_id_mismatch_raises(self):
        with pytest.raises(ValidationError, match="decision_id"):
            make_envelope(
                decision=make_decision(decision_id="pd-001"),
                approval_gate=make_gate(decision_id="pd-999"),
            )

    def test_approval_gate_decision_id_match_valid(self):
        e = make_envelope(
            decision=make_decision(decision_id="pd-001"),
            approval_gate=make_gate(decision_id="pd-001"),
        )
        assert e.approval_gate.decision_id == "pd-001"

    def test_no_approval_gate_valid(self):
        e = make_envelope(approval_gate=None)
        assert e.approval_gate is None


class TestSerialization:
    def test_decision_to_dict_and_back(self):
        d = make_decision()
        data = d.model_dump()
        assert data["decision_id"] == "pd-001"
        assert data["status"] == "allow"
        restored = PolicyDecisionRecord(**data)
        assert restored.decision_id == d.decision_id

    def test_envelope_to_dict_and_back(self):
        e = make_envelope()
        data = e.model_dump()
        assert data["envelope_id"] == "env-001"
        restored = PolicyDecisionEnvelope(**data)
        assert restored.envelope_id == e.envelope_id


class TestIntegration:
    def test_allow_decision_with_rule_refs(self):
        decision = PolicyDecisionRecord(
            decision_id="pd-allow", scope=PolicyScope.TOOL_CALL, status=PolicyDecisionStatus.ALLOW,
            reason="File read is permitted for all agents",
            rule_refs=[PolicyRuleRef(rule_id="rule-007", rule_name="allow_read_access", version="1.2")],
        )
        env = PolicyDecisionEnvelope(envelope_id="env-allow", run_id="run-001", agent_id="agent-code", decision=decision)
        assert env.decision.status == PolicyDecisionStatus.ALLOW
        assert env.decision.rule_refs[0].rule_name == "allow_read_access"

    def test_block_decision_with_reason_and_rule_refs(self):
        decision = PolicyDecisionRecord(
            decision_id="pd-block", scope=PolicyScope.TOOL_CALL, status=PolicyDecisionStatus.BLOCK,
            reason="File path src/secrets/prod.env is in protected paths list",
            rule_refs=[PolicyRuleRef(rule_id="rule-003", rule_name="block_protected_paths", version="2.0")],
            conditions=[DecisionCondition(condition_id="cond-001", description="Target path matches protected pattern", satisfied=True)],
        )
        env = PolicyDecisionEnvelope(envelope_id="env-block", run_id="run-001", task_id="t-001", agent_id="agent-code", decision=decision)
        assert env.decision.status == PolicyDecisionStatus.BLOCK
        assert env.task_id == "t-001"
        assert env.decision.conditions[0].satisfied is True

    def test_require_approval_decision_with_next_action(self):
        decision = PolicyDecisionRecord(
            decision_id="pd-req", scope=PolicyScope.TOOL_CALL, status=PolicyDecisionStatus.REQUIRE_APPROVAL,
            reason="Deleting API endpoint requires human approval",
            approval_requirement=ApprovalRequirement.OWNER_APPROVAL,
            next_action="notify_api_team_lead",
            rule_refs=[PolicyRuleRef(rule_id="rule-012", rule_name="delete_endpoint_requires_approval")],
        )
        gate = ApprovalGateRecord(gate_id="gate-req", decision_id="pd-req", approved=False)
        env = PolicyDecisionEnvelope(envelope_id="env-req", run_id="run-002", agent_id="agent-code", decision=decision, approval_gate=gate)
        assert env.decision.status == PolicyDecisionStatus.REQUIRE_APPROVAL
        assert env.decision.next_action == "notify_api_team_lead"
        assert env.approval_gate.approved is False

    def test_escalated_decision_with_approval_gate(self):
        decision = PolicyDecisionRecord(
            decision_id="pd-esc", scope=PolicyScope.SESSION, status=PolicyDecisionStatus.ESCALATE,
            reason="Session exceeded budget threshold, requires security review",
            escalation_level=EscalationLevel.SECURITY,
            rule_refs=[PolicyRuleRef(rule_id="rule-020", rule_name="budget_exceeded_escalation")],
        )
        gate = ApprovalGateRecord(
            gate_id="gate-esc", decision_id="pd-esc", approved=True,
            approval_actor=ApprovalActorRef(actor_id="sec-user", actor_type="human", display_name="Security Lead"),
            approval_note="Reviewed and approved session continuation",
            approved_at="2026-07-04T11:00:00Z",
        )
        env = PolicyDecisionEnvelope(envelope_id="env-esc", run_id="run-003", agent_id="agent-code", decision=decision, approval_gate=gate)
        assert env.decision.escalation_level == EscalationLevel.SECURITY
        assert env.approval_gate.approved_at == "2026-07-04T11:00:00Z"
        assert env.approval_gate.approval_actor.display_name == "Security Lead"

    def test_deferred_decision_waiting_on_conditions(self):
        decision = PolicyDecisionRecord(
            decision_id="pd-def", scope=PolicyScope.TASK, status=PolicyDecisionStatus.DEFER,
            reason="Waiting for resource quota to become available",
            conditions=[
                DecisionCondition(condition_id="cond-001", description="Enough disk space available", satisfied=False),
                DecisionCondition(condition_id="cond-002", description="API rate limit reset", satisfied=True),
            ],
            next_action="recheck_in_60s",
        )
        env = PolicyDecisionEnvelope(envelope_id="env-def", run_id="run-004", agent_id="agent-code", decision=decision)
        assert env.decision.status == PolicyDecisionStatus.DEFER
        assert len(env.decision.conditions) == 2
        assert env.decision.conditions[0].satisfied is False
        assert env.decision.next_action == "recheck_in_60s"
