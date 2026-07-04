import pytest
from pydantic import ValidationError
from models.approval_safety import (
    RiskLevel,
    SafetyAction,
    ResourceType,
    ApprovalRequirement,
    ActionRiskRule,
    ApprovalRequest,
    SafetyDecision,
    ApprovalSafetyPolicy,
    v1_default_safety_policy,
)


def make_approval_req(**overrides) -> ApprovalRequirement:
    kwargs = dict(require_human=True, reason_required=True)
    kwargs.update(overrides)
    return ApprovalRequirement(**kwargs)


def make_rule(**overrides) -> ActionRiskRule:
    kwargs = dict(rule_id="rule-1", action_name="read_file",
                  resource_type=ResourceType.FILESYSTEM, risk_level=RiskLevel.LOW,
                  safety_action=SafetyAction.ALLOW, rationale="Safe read-only action.")
    kwargs.update(overrides)
    return ActionRiskRule(**kwargs)


def make_request(**overrides) -> ApprovalRequest:
    kwargs = dict(request_id="req-001", run_id="run-001", action_name="edit_file",
                  risk_level=RiskLevel.MEDIUM, reason="Fix bug in parser",
                  requested_by_agent="agent-01",
                  requested_arguments_summary="Edit src/parser.py line 42")
    kwargs.update(overrides)
    return ApprovalRequest(**kwargs)


def make_decision(**overrides) -> SafetyDecision:
    kwargs = dict(decision_id="dec-001", run_id="run-001", action_name="edit_file",
                  risk_level=RiskLevel.MEDIUM, safety_action=SafetyAction.REQUIRE_APPROVAL,
                  approved=True, approver_id="user-01",
                  decision_reason="Approved: bug fix in parser")
    kwargs.update(overrides)
    return SafetyDecision(**kwargs)


def make_policy(**overrides) -> ApprovalSafetyPolicy:
    kwargs = dict(policy_id="pol-test", rules=[make_rule()])
    kwargs.update(overrides)
    return ApprovalSafetyPolicy(**kwargs)


class TestRiskLevel:
    def test_all_values_present(self):
        assert len(RiskLevel) == 4
        assert RiskLevel.CRITICAL.value == "critical"


class TestSafetyAction:
    def test_all_values_present(self):
        assert len(SafetyAction) == 3
        assert SafetyAction.BLOCK.value == "block"


class TestResourceType:
    def test_all_values_present(self):
        assert len(ResourceType) == 5
        assert ResourceType.EXTERNAL_SIDE_EFFECT.value == "external_side_effect"


class TestApprovalRequirement:
    def test_minimal(self):
        req = ApprovalRequirement()
        assert req.require_human is False
        assert req.reason_required is True

    def test_full(self):
        req = make_approval_req(approver_role="security_lead", expires_in_seconds=300)
        assert req.approver_role == "security_lead"
        assert req.expires_in_seconds == 300

    def test_zero_expiration_invalid(self):
        with pytest.raises(ValidationError):
            make_approval_req(expires_in_seconds=0)

    def test_negative_expiration_invalid(self):
        with pytest.raises(ValidationError):
            make_approval_req(expires_in_seconds=-1)

    def test_no_expiration_valid(self):
        req = make_approval_req()
        assert req.expires_in_seconds is None


class TestActionRiskRule:
    def test_minimal_allow_rule(self):
        rule = make_rule()
        assert rule.rule_id == "rule-1"
        assert rule.safety_action == SafetyAction.ALLOW

    def test_approval_rule_with_requirement(self):
        rule = make_rule(rule_id="rule-2", safety_action=SafetyAction.REQUIRE_APPROVAL,
                         approval_requirement=make_approval_req())
        assert rule.safety_action == SafetyAction.REQUIRE_APPROVAL

    def test_approval_rule_without_requirement_raises(self):
        with pytest.raises(ValidationError):
            make_rule(rule_id="rule-3", safety_action=SafetyAction.REQUIRE_APPROVAL,
                      approval_requirement=None)

    def test_block_rule(self):
        rule = make_rule(rule_id="rule-4", safety_action=SafetyAction.BLOCK)
        assert rule.safety_action == SafetyAction.BLOCK

    def test_empty_rule_id_raises(self):
        with pytest.raises(ValidationError):
            make_rule(rule_id="  ")

    def test_empty_action_name_raises(self):
        with pytest.raises(ValidationError):
            make_rule(action_name="  ")

    def test_empty_rationale_raises(self):
        with pytest.raises(ValidationError):
            make_rule(rationale="  ")

    def test_all_risk_levels_accepted(self):
        for rl in RiskLevel:
            rule = make_rule(rule_id=f"rule-{rl.value}", risk_level=rl)
            assert rule.risk_level == rl

    def test_all_resource_types_accepted(self):
        for rt in ResourceType:
            hosts = ["docs.python.org"] if rt == ResourceType.NETWORK else []
            secrets = ["api_key"] if rt == ResourceType.SECRET else []
            ap_req = make_approval_req() if rt == ResourceType.SECRET else None
            sa = SafetyAction.REQUIRE_APPROVAL if rt == ResourceType.SECRET else SafetyAction.ALLOW
            rule = make_rule(rule_id=f"rule-{rt.value}", resource_type=rt,
                             allowed_hosts=hosts, allowed_secret_names=secrets,
                             safety_action=sa, approval_requirement=ap_req)
            assert rule.resource_type == rt

    def test_network_allow_without_hosts_raises(self):
        with pytest.raises(ValidationError):
            make_rule(rule_id="rule-net", resource_type=ResourceType.NETWORK,
                      safety_action=SafetyAction.ALLOW, allowed_hosts=[])

    def test_network_allow_with_hosts_valid(self):
        rule = make_rule(rule_id="rule-net2", resource_type=ResourceType.NETWORK,
                         safety_action=SafetyAction.ALLOW,
                         allowed_hosts=["docs.python.org"])
        assert "docs.python.org" in rule.allowed_hosts

    def test_secret_rule_without_names_raises(self):
        with pytest.raises(ValidationError):
            make_rule(rule_id="rule-sec", resource_type=ResourceType.SECRET,
                      safety_action=SafetyAction.REQUIRE_APPROVAL,
                      allowed_secret_names=[],
                      approval_requirement=make_approval_req())

    def test_secret_rule_with_names_valid(self):
        rule = make_rule(rule_id="rule-sec2", resource_type=ResourceType.SECRET,
                         safety_action=SafetyAction.REQUIRE_APPROVAL,
                         allowed_secret_names=["api_key"],
                         approval_requirement=make_approval_req())
        assert "api_key" in rule.allowed_secret_names

    def test_path_prefixes_default_empty(self):
        rule = make_rule()
        assert rule.allowed_path_prefixes == []

    def test_path_prefixes_set(self):
        rule = make_rule(allowed_path_prefixes=["/workspace/src"])
        assert rule.allowed_path_prefixes == ["/workspace/src"]

    def test_network_block_with_allowlist_valid(self):
        rule = make_rule(rule_id="rule-net3", resource_type=ResourceType.NETWORK,
                         safety_action=SafetyAction.BLOCK, allowed_hosts=[])
        assert rule.safety_action == SafetyAction.BLOCK

    def test_network_require_approval_without_hosts_valid(self):
        rule = make_rule(rule_id="rule-net4", resource_type=ResourceType.NETWORK,
                         safety_action=SafetyAction.REQUIRE_APPROVAL,
                         allowed_hosts=[],
                         approval_requirement=make_approval_req())
        assert rule.safety_action == SafetyAction.REQUIRE_APPROVAL


class TestApprovalRequest:
    def test_minimal(self):
        req = make_request()
        assert req.request_id == "req-001"
        assert req.risk_level == RiskLevel.MEDIUM

    def test_empty_request_id_raises(self):
        with pytest.raises(ValidationError):
            make_request(request_id="  ")

    def test_empty_run_id_raises(self):
        with pytest.raises(ValidationError):
            make_request(run_id="  ")

    def test_empty_action_name_raises(self):
        with pytest.raises(ValidationError):
            make_request(action_name="  ")

    def test_empty_reason_raises(self):
        with pytest.raises(ValidationError):
            make_request(reason="  ")

    def test_empty_agent_raises(self):
        with pytest.raises(ValidationError):
            make_request(requested_by_agent="  ")

    def test_empty_arguments_summary_raises(self):
        with pytest.raises(ValidationError):
            make_request(requested_arguments_summary="  ")

    def test_with_expires_at(self):
        req = make_request(expires_at="2025-04-01T12:00:00Z")
        assert req.expires_at == "2025-04-01T12:00:00Z"

    def test_all_risk_levels_accepted(self):
        for rl in RiskLevel:
            req = make_request(request_id=f"req-{rl.value}", risk_level=rl)
            assert req.risk_level == rl


class TestSafetyDecision:
    def test_approved(self):
        d = make_decision()
        assert d.approved is True
        assert d.approver_id == "user-01"

    def test_denied(self):
        d = make_decision(approved=False, approver_id="user-01",
                          decision_reason="Rejected: unsafe change")
        assert d.approved is False

    def test_blocked(self):
        d = make_decision(safety_action=SafetyAction.BLOCK, approved=None,
                          approver_id=None,
                          decision_reason="Blocked by policy: credential access")
        assert d.safety_action == SafetyAction.BLOCK
        assert d.approved is None

    def test_approved_without_approver_id_raises(self):
        with pytest.raises(ValidationError):
            make_decision(approved=True, approver_id=None)

    def test_denied_without_approver_id_valid(self):
        d = make_decision(approved=False, approver_id=None,
                          decision_reason="Rejected by policy")
        assert d.approved is False

    def test_empty_decision_id_raises(self):
        with pytest.raises(ValidationError):
            make_decision(decision_id="  ")

    def test_empty_run_id_raises(self):
        with pytest.raises(ValidationError):
            make_decision(run_id="  ")

    def test_empty_action_name_raises(self):
        with pytest.raises(ValidationError):
            make_decision(action_name="  ")

    def test_empty_reason_raises(self):
        with pytest.raises(ValidationError):
            make_decision(decision_reason="  ")

    def test_block_override_with_approved_raises(self):
        with pytest.raises(ValidationError):
            make_decision(safety_action=SafetyAction.BLOCK, approved=True,
                          approver_id="user-01",
                          decision_reason="Try to override block")

    def test_block_with_approved_false_valid(self):
        d = make_decision(safety_action=SafetyAction.BLOCK, approved=False,
                          approver_id="user-01",
                          decision_reason="Confirmed block")
        assert d.approved is False

    def test_block_with_approved_none_valid(self):
        d = make_decision(safety_action=SafetyAction.BLOCK, approved=None,
                          approver_id=None,
                          decision_reason="Blocked by policy")
        assert d.approved is None


class TestApprovalSafetyPolicy:
    def test_minimal_policy(self):
        p = make_policy()
        assert p.policy_id == "pol-test"
        assert len(p.rules) == 1

    def test_multiple_rules(self):
        p = make_policy(rules=[
            make_rule(rule_id="rule-1"),
            make_rule(rule_id="rule-2", action_name="write_file",
                      risk_level=RiskLevel.MEDIUM,
                      safety_action=SafetyAction.REQUIRE_APPROVAL,
                      approval_requirement=make_approval_req()),
        ])
        assert len(p.rules) == 2

    def test_empty_policy_id_raises(self):
        with pytest.raises(ValidationError):
            make_policy(policy_id="  ")

    def test_duplicate_rule_ids_raises(self):
        with pytest.raises(ValidationError):
            make_policy(rules=[
                make_rule(rule_id="rule-dup"),
                make_rule(rule_id="rule-dup"),
            ])

    def test_unique_rule_ids_valid(self):
        p = make_policy(rules=[
            make_rule(rule_id="rule-1"),
            make_rule(rule_id="rule-2"),
            make_rule(rule_id="rule-3"),
        ])
        assert len(p.rules) == 3

    def test_no_rules_valid(self):
        p = ApprovalSafetyPolicy(policy_id="pol-empty")
        assert len(p.rules) == 0


class TestV1DefaultSafetyPolicy:
    def test_creates_successfully(self):
        p = v1_default_safety_policy()
        assert p.policy_id == "approval-safety-v1"

    def test_has_10_rules(self):
        p = v1_default_safety_policy()
        assert len(p.rules) == 10

    def test_allow_read(self):
        p = v1_default_safety_policy()
        r = [x for x in p.rules if x.rule_id == "read-workspace-files"][0]
        assert r.safety_action == SafetyAction.ALLOW

    def test_edit_requires_approval(self):
        p = v1_default_safety_policy()
        r = [x for x in p.rules if x.rule_id == "edit-workspace-files"][0]
        assert r.safety_action == SafetyAction.REQUIRE_APPROVAL

    def test_delete_high_risk(self):
        p = v1_default_safety_policy()
        r = [x for x in p.rules if x.rule_id == "delete-files"][0]
        assert r.risk_level == RiskLevel.HIGH

    def test_secrets_critical_with_role(self):
        p = v1_default_safety_policy()
        r = [x for x in p.rules if x.rule_id == "access-secrets"][0]
        assert r.risk_level == RiskLevel.CRITICAL
        assert r.approval_requirement.approver_role == "security_lead"

    def test_arbitrary_network_blocked(self):
        p = v1_default_safety_policy()
        r = [x for x in p.rules if x.rule_id == "arbitrary-network"][0]
        assert r.safety_action == SafetyAction.BLOCK

    def test_allowlisted_network_allowed(self):
        p = v1_default_safety_policy()
        r = [x for x in p.rules if x.rule_id == "allowlisted-docs-network"][0]
        assert r.safety_action == SafetyAction.ALLOW
        assert "pypi.org" in r.allowed_hosts

    def test_deployment_has_expiration(self):
        p = v1_default_safety_policy()
        r = [x for x in p.rules if x.rule_id == "deployment-changes"][0]
        assert r.approval_requirement.expires_in_seconds == 300

    def test_credential_file_blocked(self):
        p = v1_default_safety_policy()
        r = [x for x in p.rules if x.rule_id == "credential-file-access"][0]
        assert r.safety_action == SafetyAction.BLOCK
