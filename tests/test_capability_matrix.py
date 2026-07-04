import pytest
from pydantic import ValidationError
from models.capability_matrix import (
    CapabilityVerb,
    ToolRiskLevel,
    PermissionEffect,
    ExecutionEnvironment,
    ScopeConstraint,
    ToolDescriptor,
    CapabilityGrant,
    ToolPermissionRule,
    CapabilityMatrix,
    ToolAccessRequest,
    AuthorizationDecision,
)


class TestEnums:
    def test_capability_verb_values(self):
        assert CapabilityVerb.READ.value == "read"
        assert CapabilityVerb.ESCALATE.value == "escalate"

    def test_tool_risk_level_values(self):
        assert ToolRiskLevel.LOW.value == "low"
        assert ToolRiskLevel.CRITICAL.value == "critical"

    def test_permission_effect_values(self):
        assert PermissionEffect.ALLOW.value == "allow"
        assert PermissionEffect.REQUIRE_APPROVAL.value == "require_approval"

    def test_execution_environment_values(self):
        assert ExecutionEnvironment.DEVELOPMENT.value == "development"
        assert ExecutionEnvironment.PRODUCTION.value == "production"


class TestScopeConstraint:
    def test_valid(self):
        sc = ScopeConstraint(scope_type="path", scope_value="src/")
        assert sc.description is None

    def test_with_description(self):
        sc = ScopeConstraint(scope_type="tenant", scope_value="tenant-abc", description="ACME Corp tenant")
        assert sc.description == "ACME Corp tenant"

    def test_empty_type_raises(self):
        with pytest.raises(ValidationError) as exc:
            ScopeConstraint(scope_type="  ", scope_value="x")
        assert "must not be empty" in str(exc.value)

    def test_empty_value_raises(self):
        with pytest.raises(ValidationError) as exc:
            ScopeConstraint(scope_type="path", scope_value="  ")
        assert "must not be empty" in str(exc.value)


class TestToolDescriptor:
    def test_valid(self):
        td = ToolDescriptor(
            tool_id="edit-file", tool_name="EditFile", description="Edit files on disk",
            risk_level=ToolRiskLevel.MEDIUM,
            supported_verbs=[CapabilityVerb.READ, CapabilityVerb.WRITE],
        )
        assert td.tool_id == "edit-file"
        assert td.destructive is False

    def test_destructive_high_risk(self):
        td = ToolDescriptor(
            tool_id="delete-resource", tool_name="DeleteResource",
            description="Deletes cloud resources",
            risk_level=ToolRiskLevel.CRITICAL,
            supported_verbs=[CapabilityVerb.DELETE],
            destructive=True,
        )
        assert td.destructive is True

    def test_empty_tool_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            ToolDescriptor(tool_id="  ", tool_name="T", description="x",
                           risk_level=ToolRiskLevel.LOW, supported_verbs=[CapabilityVerb.READ])
        assert "must not be empty" in str(exc.value)

    def test_empty_tool_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            ToolDescriptor(tool_id="t", tool_name="  ", description="x",
                           risk_level=ToolRiskLevel.LOW, supported_verbs=[CapabilityVerb.READ])
        assert "must not be empty" in str(exc.value)

    def test_empty_verbs_raises(self):
        with pytest.raises(ValidationError) as exc:
            ToolDescriptor(tool_id="t", tool_name="T", description="x",
                           risk_level=ToolRiskLevel.LOW, supported_verbs=[])
        assert "supported_verbs must not be empty for registered tools" in str(exc.value)

    def test_destructive_low_risk_raises(self):
        with pytest.raises(ValidationError) as exc:
            ToolDescriptor(
                tool_id="t", tool_name="T", description="x",
                risk_level=ToolRiskLevel.LOW, supported_verbs=[CapabilityVerb.DELETE],
                destructive=True,
            )
        assert "destructive tools must have risk_level HIGH or CRITICAL" in str(exc.value)


class TestCapabilityGrant:
    def test_valid(self):
        grant = CapabilityGrant(
            grant_id="g-001", agent_identity="agent-code", tool_id="search-code",
            allowed_verbs=[CapabilityVerb.READ],
            environments=[ExecutionEnvironment.DEVELOPMENT, ExecutionEnvironment.STAGING],
        )
        assert grant.enabled is True

    def test_with_scope(self):
        grant = CapabilityGrant(
            grant_id="g-002", agent_identity="agent-swe", tool_id="edit-file",
            allowed_verbs=[CapabilityVerb.READ, CapabilityVerb.WRITE],
            environments=[ExecutionEnvironment.DEVELOPMENT],
            scope_constraints=[ScopeConstraint(scope_type="path", scope_value="src/")],
        )
        assert len(grant.scope_constraints) == 1

    def test_empty_grant_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            CapabilityGrant(grant_id="  ", agent_identity="a", tool_id="t",
                            allowed_verbs=[CapabilityVerb.READ],
                            environments=[ExecutionEnvironment.DEVELOPMENT])
        assert "must not be empty" in str(exc.value)

    def test_empty_environments_raises(self):
        with pytest.raises(ValidationError) as exc:
            CapabilityGrant(grant_id="g", agent_identity="a", tool_id="t",
                            allowed_verbs=[CapabilityVerb.READ], environments=[])
        assert "environments must not be empty" in str(exc.value)

    def test_empty_verbs_raises(self):
        with pytest.raises(ValidationError) as exc:
            CapabilityGrant(grant_id="g", agent_identity="a", tool_id="t",
                            allowed_verbs=[], environments=[ExecutionEnvironment.DEVELOPMENT])
        assert "allowed_verbs must not be empty" in str(exc.value)

    def test_delete_without_approval_raises(self):
        with pytest.raises(ValidationError) as exc:
            CapabilityGrant(
                grant_id="g", agent_identity="a", tool_id="t",
                allowed_verbs=[CapabilityVerb.DELETE],
                environments=[ExecutionEnvironment.DEVELOPMENT],
                approval_required=False,
            )
        assert "DELETE/SEND verbs require approval_required=True" in str(exc.value)

    def test_send_without_approval_raises(self):
        with pytest.raises(ValidationError) as exc:
            CapabilityGrant(
                grant_id="g", agent_identity="a", tool_id="t",
                allowed_verbs=[CapabilityVerb.SEND],
                environments=[ExecutionEnvironment.DEVELOPMENT],
                approval_required=False,
            )
        assert "DELETE/SEND verbs require approval_required=True" in str(exc.value)

    def test_disabled_grant(self):
        grant = CapabilityGrant(
            grant_id="g", agent_identity="a", tool_id="t",
            allowed_verbs=[CapabilityVerb.READ],
            environments=[ExecutionEnvironment.DEVELOPMENT],
            enabled=False,
        )
        assert grant.enabled is False


class TestToolPermissionRule:
    def test_valid(self):
        rule = ToolPermissionRule(
            rule_id="r-001", tool_id="edit-file", effect=PermissionEffect.ALLOW,
            applies_to_agent_identity="agent-swe",
            verbs=[CapabilityVerb.READ, CapabilityVerb.WRITE],
            environments=[ExecutionEnvironment.DEVELOPMENT],
            rationale="Allow read/write in dev",
        )
        assert rule.effect == PermissionEffect.ALLOW

    def test_empty_rule_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            ToolPermissionRule(rule_id="  ", tool_id="t", effect=PermissionEffect.DENY,
                               applies_to_agent_identity="a", environments=[ExecutionEnvironment.DEVELOPMENT])
        assert "must not be empty" in str(exc.value)

    def test_empty_environments_raises(self):
        with pytest.raises(ValidationError) as exc:
            ToolPermissionRule(rule_id="r", tool_id="t", effect=PermissionEffect.DENY,
                               applies_to_agent_identity="a", environments=[])
        assert "environments must not be empty" in str(exc.value)


class TestCapabilityMatrix:
    def test_valid_default_deny(self):
        matrix = CapabilityMatrix(matrix_id="matrix-default")
        assert matrix.default_effect == PermissionEffect.DENY

    def test_with_tools_and_grants(self):
        matrix = CapabilityMatrix(
            matrix_id="matrix-swe",
            tool_descriptors=[
                ToolDescriptor(tool_id="search", tool_name="Search", description="Search code",
                               risk_level=ToolRiskLevel.LOW,
                               supported_verbs=[CapabilityVerb.READ, CapabilityVerb.EXECUTE]),
            ],
            grants=[
                CapabilityGrant(grant_id="g1", agent_identity="agent-code", tool_id="search",
                                allowed_verbs=[CapabilityVerb.READ],
                                environments=[ExecutionEnvironment.DEVELOPMENT]),
            ],
        )
        assert len(matrix.tool_descriptors) == 1
        assert len(matrix.grants) == 1

    def test_empty_matrix_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            CapabilityMatrix(matrix_id="  ")
        assert "matrix_id must not be empty" in str(exc.value)


class TestToolAccessRequest:
    def test_valid(self):
        req = ToolAccessRequest(
            request_id="ar-001", run_id="run-001", step_id="step-3",
            agent_identity="agent-swe", tool_id="edit-file",
            requested_verb=CapabilityVerb.WRITE,
            environment=ExecutionEnvironment.DEVELOPMENT,
        )
        assert req.requested_verb == CapabilityVerb.WRITE

    def test_with_scope(self):
        req = ToolAccessRequest(
            request_id="ar-002", run_id="run-001", step_id="step-4",
            agent_identity="agent-swe", tool_id="edit-file",
            requested_verb=CapabilityVerb.DELETE,
            environment=ExecutionEnvironment.PRODUCTION,
            requested_scope=[ScopeConstraint(scope_type="path", scope_value="src/")],
        )
        assert len(req.requested_scope) == 1

    def test_empty_request_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            ToolAccessRequest(request_id="  ", run_id="r", step_id="s",
                              agent_identity="a", tool_id="t",
                              requested_verb=CapabilityVerb.READ,
                              environment=ExecutionEnvironment.DEVELOPMENT)
        assert "must not be empty" in str(exc.value)

    def test_empty_agent_identity_raises(self):
        with pytest.raises(ValidationError) as exc:
            ToolAccessRequest(request_id="r", run_id="r", step_id="s",
                              agent_identity="  ", tool_id="t",
                              requested_verb=CapabilityVerb.READ,
                              environment=ExecutionEnvironment.DEVELOPMENT)
        assert "must not be empty" in str(exc.value)


class TestAuthorizationDecision:
    def test_allowed(self):
        d = AuthorizationDecision(
            decision_id="dec-001", request_id="ar-001",
            allowed=True, effect=PermissionEffect.ALLOW,
            matched_rule_ids=["r-001"],
            rationale="grant g-001 allows read in dev",
        )
        assert d.allowed is True

    def test_denied_default(self):
        d = AuthorizationDecision(
            decision_id="dec-002", request_id="ar-002",
            allowed=False, effect=PermissionEffect.DENY,
            matched_rule_ids=[],
            rationale="no matching grant found, default-deny",
        )
        assert d.allowed is False

    def test_require_approval(self):
        d = AuthorizationDecision(
            decision_id="dec-003", request_id="ar-003",
            allowed=False, effect=PermissionEffect.REQUIRE_APPROVAL,
            matched_rule_ids=["r-prod-write"],
            rationale="production write requires approval",
            approval_required=True,
        )
        assert d.approval_required is True

    def test_empty_decision_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            AuthorizationDecision(decision_id="  ", request_id="r", allowed=True,
                                  effect=PermissionEffect.ALLOW, rationale="ok",
                                  matched_rule_ids=["r1"])
        assert "must not be empty" in str(exc.value)

    def test_empty_rationale_raises(self):
        with pytest.raises(ValidationError) as exc:
            AuthorizationDecision(decision_id="d", request_id="r", allowed=True,
                                  effect=PermissionEffect.ALLOW, rationale="  ",
                                  matched_rule_ids=["r1"])
        assert "rationale must not be empty" in str(exc.value)

    def test_require_approval_missing_flag_raises(self):
        with pytest.raises(ValidationError) as exc:
            AuthorizationDecision(
                decision_id="d", request_id="r", allowed=False,
                effect=PermissionEffect.REQUIRE_APPROVAL,
                matched_rule_ids=["r1"], rationale="needs approval",
                approval_required=False,
            )
        assert "effect=REQUIRE_APPROVAL requires approval_required=True" in str(exc.value)

    def test_allow_without_matched_rules_raises(self):
        with pytest.raises(ValidationError) as exc:
            AuthorizationDecision(
                decision_id="d", request_id="r", allowed=True,
                effect=PermissionEffect.ALLOW,
                matched_rule_ids=[], rationale="allowed",
            )
        assert "non-DENY decisions must have at least one matched_rule_ids entry" in str(exc.value)


class TestSerialization:
    def test_matrix_to_json(self):
        matrix = CapabilityMatrix(
            matrix_id="matrix-test",
            tool_descriptors=[
                ToolDescriptor(tool_id="search", tool_name="Search", description="Search code",
                               risk_level=ToolRiskLevel.LOW,
                               supported_verbs=[CapabilityVerb.READ]),
            ],
        )
        json_str = matrix.model_dump_json()
        assert "matrix-test" in json_str
        assert "search" in json_str

    def test_decision_roundtrip(self):
        d = AuthorizationDecision(decision_id="d1", request_id="r1", allowed=True,
                                  effect=PermissionEffect.ALLOW, matched_rule_ids=["r1"],
                                  rationale="granted")
        dumped = d.model_dump()
        assert dumped["allowed"] is True
        assert dumped["effect"] == "allow"
