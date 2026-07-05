import json
import pytest
from pydantic import ValidationError
from models.tool_permission_contract import (
    ToolActionType,
    ToolRiskLevel,
    ApprovalRequirement,
    NetworkAccessLevel,
    FilesystemAccessLevel,
    CredentialMode,
    ToolDescriptor,
    ExecutionConstraint,
    CapabilityGrant,
    ToolInvocationRequest,
    PermissionDecision,
)


class TestEnums:
    def test_tool_action_type_values(self):
        assert ToolActionType.READ.value == "read"
        assert ToolActionType.WRITE.value == "write"
        assert ToolActionType.DELETE.value == "delete"
        assert ToolActionType.EXECUTE.value == "execute"
        assert ToolActionType.EXPORT.value == "export"
        assert ToolActionType.SEND.value == "send"
        assert ToolActionType.DELEGATE.value == "delegate"

    def test_tool_risk_level_values(self):
        assert ToolRiskLevel.LOW.value == "low"
        assert ToolRiskLevel.MODERATE.value == "moderate"
        assert ToolRiskLevel.HIGH.value == "high"
        assert ToolRiskLevel.CRITICAL.value == "critical"

    def test_approval_requirement_values(self):
        assert ApprovalRequirement.NONE.value == "none"
        assert ApprovalRequirement.OPTIONAL.value == "optional"
        assert ApprovalRequirement.REQUIRED.value == "required"

    def test_network_access_level_values(self):
        assert NetworkAccessLevel.NONE.value == "none"
        assert NetworkAccessLevel.RESTRICTED.value == "restricted"
        assert NetworkAccessLevel.FULL.value == "full"

    def test_filesystem_access_level_values(self):
        assert FilesystemAccessLevel.NONE.value == "none"
        assert FilesystemAccessLevel.SANDBOX_ONLY.value == "sandbox_only"
        assert FilesystemAccessLevel.SCOPED_PATHS.value == "scoped_paths"

    def test_credential_mode_values(self):
        assert CredentialMode.NONE.value == "none"
        assert CredentialMode.SCOPED_EPHEMERAL.value == "scoped_ephemeral"
        assert CredentialMode.PREBOUND_REFERENCE.value == "prebound_reference"


class TestToolDescriptor:
    def test_valid_minimal(self):
        td = ToolDescriptor(tool_id="td-1", tool_name="searcher", risk_level=ToolRiskLevel.LOW)
        assert td.tool_id == "td-1"
        assert td.tool_name == "searcher"
        assert td.risk_level == ToolRiskLevel.LOW
        assert td.supported_actions == []

    def test_valid_with_actions(self):
        td = ToolDescriptor(
            tool_id="td-2",
            tool_name="executor",
            version="1.0",
            description="Runs code",
            supported_actions=[ToolActionType.READ, ToolActionType.EXECUTE],
            risk_level=ToolRiskLevel.HIGH,
        )
        assert ToolActionType.READ in td.supported_actions
        assert ToolActionType.EXECUTE in td.supported_actions
        assert td.version == "1.0"

    def test_empty_tool_id_raises(self):
        with pytest.raises(ValueError):
            ToolDescriptor(tool_id="  ", tool_name="searcher", risk_level=ToolRiskLevel.LOW)

    def test_empty_tool_name_raises(self):
        with pytest.raises(ValueError):
            ToolDescriptor(tool_id="td-3", tool_name="", risk_level=ToolRiskLevel.LOW)


class TestExecutionConstraint:
    def test_valid_minimal(self):
        ec = ExecutionConstraint(timeout_seconds=30)
        assert ec.timeout_seconds == 30
        assert ec.network_access == NetworkAccessLevel.NONE
        assert ec.filesystem_access == FilesystemAccessLevel.NONE
        assert ec.allowed_paths == []

    def test_valid_with_scoped_paths(self):
        ec = ExecutionConstraint(
            timeout_seconds=60,
            max_calls_per_run=10,
            network_access=NetworkAccessLevel.RESTRICTED,
            filesystem_access=FilesystemAccessLevel.SCOPED_PATHS,
            allowed_paths=["/tmp/sandbox", "/home/user/data"],
        )
        assert ec.max_calls_per_run == 10
        assert "/tmp/sandbox" in ec.allowed_paths

    def test_negative_timeout_raises(self):
        with pytest.raises(ValueError):
            ExecutionConstraint(timeout_seconds=-1)

    def test_zero_timeout_raises(self):
        with pytest.raises(ValueError):
            ExecutionConstraint(timeout_seconds=0)

    def test_paths_without_scoped_raises(self):
        with pytest.raises(ValueError):
            ExecutionConstraint(
                timeout_seconds=30,
                filesystem_access=FilesystemAccessLevel.NONE,
                allowed_paths=["/tmp"],
            )

    def test_sandbox_without_paths_ok(self):
        ec = ExecutionConstraint(
            timeout_seconds=30,
            filesystem_access=FilesystemAccessLevel.SANDBOX_ONLY,
        )
        assert ec.filesystem_access == FilesystemAccessLevel.SANDBOX_ONLY

    def test_scoped_without_paths_ok(self):
        ec = ExecutionConstraint(
            timeout_seconds=30,
            filesystem_access=FilesystemAccessLevel.SCOPED_PATHS,
        )
        assert ec.allowed_paths == []


class TestCapabilityGrant:
    def test_valid_minimal(self):
        ec = ExecutionConstraint(timeout_seconds=30)
        cg = CapabilityGrant(
            grant_id="g-1",
            agent_id="agent-codex",
            tool_id="td-1",
            execution_constraint=ec,
        )
        assert cg.approval_requirement == ApprovalRequirement.NONE
        assert cg.credential_mode == CredentialMode.NONE

    def test_valid_read_only_grant(self):
        ec = ExecutionConstraint(timeout_seconds=30)
        cg = CapabilityGrant(
            grant_id="g-2",
            agent_id="agent-reader",
            tool_id="td-search",
            allowed_actions=[ToolActionType.READ],
            approval_requirement=ApprovalRequirement.NONE,
            credential_mode=CredentialMode.SCOPED_EPHEMERAL,
            resource_scopes=["org:acme", "project:harness"],
            execution_constraint=ec,
        )
        assert ToolActionType.READ in cg.allowed_actions
        assert "org:acme" in cg.resource_scopes
        assert cg.credential_mode == CredentialMode.SCOPED_EPHEMERAL

    def test_empty_grant_id_raises(self):
        ec = ExecutionConstraint(timeout_seconds=30)
        with pytest.raises(ValueError):
            CapabilityGrant(
                grant_id="",
                agent_id="agent-x",
                tool_id="td-1",
                execution_constraint=ec,
            )

    def test_empty_agent_id_raises(self):
        ec = ExecutionConstraint(timeout_seconds=30)
        with pytest.raises(ValueError):
            CapabilityGrant(
                grant_id="g-3",
                agent_id="",
                tool_id="td-1",
                execution_constraint=ec,
            )

    def test_empty_tool_id_raises(self):
        ec = ExecutionConstraint(timeout_seconds=30)
        with pytest.raises(ValueError):
            CapabilityGrant(
                grant_id="g-4",
                agent_id="agent-x",
                tool_id="  ",
                execution_constraint=ec,
            )


class TestToolInvocationRequest:
    def test_valid_minimal(self):
        req = ToolInvocationRequest(
            request_id="req-1",
            run_id="run-abc",
            agent_id="agent-codex",
            tool_id="td-search",
            action=ToolActionType.READ,
            justification="Need to find user records",
        )
        assert req.request_id == "req-1"
        assert req.action == ToolActionType.READ
        assert req.resource_target is None
        assert req.tenant_id is None

    def test_valid_with_optional_fields(self):
        req = ToolInvocationRequest(
            request_id="req-2",
            run_id="run-def",
            agent_id="agent-deleter",
            tool_id="td-storage",
            action=ToolActionType.DELETE,
            resource_target="blob://containers/old-logs",
            tenant_id="tenant-acme",
            justification="Cleanup old logs per retention policy",
        )
        assert req.resource_target == "blob://containers/old-logs"
        assert req.tenant_id == "tenant-acme"

    def test_empty_request_id_raises(self):
        with pytest.raises(ValueError):
            ToolInvocationRequest(
                request_id="",
                run_id="run-abc",
                agent_id="agent-x",
                tool_id="td-1",
                action=ToolActionType.READ,
                justification="test",
            )

    def test_empty_run_id_raises(self):
        with pytest.raises(ValueError):
            ToolInvocationRequest(
                request_id="req-3",
                run_id="",
                agent_id="agent-x",
                tool_id="td-1",
                action=ToolActionType.READ,
                justification="test",
            )

    def test_empty_agent_id_raises(self):
        with pytest.raises(ValueError):
            ToolInvocationRequest(
                request_id="req-4",
                run_id="run-abc",
                agent_id="",
                tool_id="td-1",
                action=ToolActionType.READ,
                justification="test",
            )

    def test_empty_tool_id_raises(self):
        with pytest.raises(ValueError):
            ToolInvocationRequest(
                request_id="req-5",
                run_id="run-abc",
                agent_id="agent-x",
                tool_id="",
                action=ToolActionType.READ,
                justification="test",
            )

    def test_empty_justification_raises(self):
        with pytest.raises(ValueError):
            ToolInvocationRequest(
                request_id="req-6",
                run_id="run-abc",
                agent_id="agent-x",
                tool_id="td-1",
                action=ToolActionType.READ,
                justification="   ",
            )


class TestPermissionDecision:
    def test_allowed_decision(self):
        d = PermissionDecision(
            decision_id="dec-1",
            request_id="req-1",
            allowed=True,
            reason="Action READ on td-search is granted by g-1",
            matched_grant_id="g-1",
            approval_required=False,
        )
        assert d.allowed is True
        assert d.matched_grant_id == "g-1"

    def test_denied_decision(self):
        d = PermissionDecision(
            decision_id="dec-2",
            request_id="req-2",
            allowed=False,
            reason="No matching grant found for agent-deleter on td-storage with DELETE action",
        )
        assert d.allowed is False
        assert d.matched_grant_id is None
        assert d.approval_required is False

    def test_approval_required(self):
        d = PermissionDecision(
            decision_id="dec-3",
            request_id="req-3",
            allowed=True,
            reason="Grant g-2 matches but approval is required for DELETE",
            matched_grant_id="g-2",
            approval_required=True,
        )
        assert d.approval_required is True

    def test_empty_decision_id_raises(self):
        with pytest.raises(ValueError):
            PermissionDecision(
                decision_id="",
                request_id="req-1",
                allowed=True,
                reason="ok",
            )

    def test_empty_request_id_raises(self):
        with pytest.raises(ValueError):
            PermissionDecision(
                decision_id="dec-4",
                request_id="",
                allowed=True,
                reason="ok",
            )

    def test_empty_reason_raises(self):
        with pytest.raises(ValueError):
            PermissionDecision(
                decision_id="dec-5",
                request_id="req-1",
                allowed=True,
                reason="",
            )


class TestIntegration:
    def test_read_only_search_tool_grant(self):
        ec = ExecutionConstraint(
            timeout_seconds=30,
            network_access=NetworkAccessLevel.RESTRICTED,
            filesystem_access=FilesystemAccessLevel.NONE,
        )
        tool = ToolDescriptor(
            tool_id="td-search",
            tool_name="search_index",
            description="Read-only search index",
            supported_actions=[ToolActionType.READ],
            risk_level=ToolRiskLevel.LOW,
        )
        grant = CapabilityGrant(
            grant_id="g-search",
            agent_id="agent-reader",
            tool_id="td-search",
            allowed_actions=[ToolActionType.READ],
            resource_scopes=["index:docs"],
            execution_constraint=ec,
        )
        req = ToolInvocationRequest(
            request_id="req-search",
            run_id="run-001",
            agent_id="agent-reader",
            tool_id="td-search",
            action=ToolActionType.READ,
            justification="Search documentation",
        )
        assert req.action in tool.supported_actions
        assert req.action in grant.allowed_actions
        decision = PermissionDecision(
            decision_id="dec-search",
            request_id="req-search",
            allowed=True,
            reason="READ on search_index granted by g-search",
            matched_grant_id="g-search",
        )
        assert decision.allowed is True

    def test_code_execution_sandbox_constraint(self):
        ec = ExecutionConstraint(
            timeout_seconds=120,
            max_calls_per_run=5,
            network_access=NetworkAccessLevel.NONE,
            filesystem_access=FilesystemAccessLevel.SANDBOX_ONLY,
        )
        tool = ToolDescriptor(
            tool_id="td-codex",
            tool_name="code_runner",
            supported_actions=[ToolActionType.READ, ToolActionType.EXECUTE],
            risk_level=ToolRiskLevel.HIGH,
        )
        grant = CapabilityGrant(
            grant_id="g-codex",
            agent_id="agent-coder",
            tool_id="td-codex",
            allowed_actions=[ToolActionType.READ, ToolActionType.EXECUTE],
            approval_requirement=ApprovalRequirement.OPTIONAL,
            execution_constraint=ec,
        )
        req = ToolInvocationRequest(
            request_id="req-codex",
            run_id="run-002",
            agent_id="agent-coder",
            tool_id="td-codex",
            action=ToolActionType.EXECUTE,
            justification="Execute Python script for data transformation",
        )
        assert req.action in tool.supported_actions
        assert req.action in grant.allowed_actions
        assert grant.execution_constraint.filesystem_access == FilesystemAccessLevel.SANDBOX_ONLY

    def test_high_risk_delete_requires_approval(self):
        ec = ExecutionConstraint(timeout_seconds=30)
        tool = ToolDescriptor(
            tool_id="td-storage",
            tool_name="object_store",
            supported_actions=[ToolActionType.READ, ToolActionType.WRITE, ToolActionType.DELETE],
            risk_level=ToolRiskLevel.CRITICAL,
        )
        grant = CapabilityGrant(
            grant_id="g-storage",
            agent_id="agent-admin",
            tool_id="td-storage",
            allowed_actions=[ToolActionType.READ, ToolActionType.WRITE, ToolActionType.DELETE],
            approval_requirement=ApprovalRequirement.REQUIRED,
            execution_constraint=ec,
        )
        req = ToolInvocationRequest(
            request_id="req-delete",
            run_id="run-003",
            agent_id="agent-admin",
            tool_id="td-storage",
            action=ToolActionType.DELETE,
            resource_target="blob://containers/backup-2025",
            justification="Remove obsolete backup",
        )
        decision = PermissionDecision(
            decision_id="dec-delete",
            request_id="req-delete",
            allowed=True,
            reason="Grant g-storage matches but DELETE requires approval",
            matched_grant_id="g-storage",
            approval_required=True,
        )
        assert decision.approval_required is True
        assert req.action in tool.supported_actions
        assert req.action in grant.allowed_actions

    def test_unknown_tool_denied(self):
        req = ToolInvocationRequest(
            request_id="req-unknown",
            run_id="run-004",
            agent_id="agent-x",
            tool_id="td-unknown",
            action=ToolActionType.EXECUTE,
            justification="Attempt unknown tool",
        )
        decision = PermissionDecision(
            decision_id="dec-unknown",
            request_id="req-unknown",
            allowed=False,
            reason="No matching grant or tool registration found for td-unknown",
        )
        assert decision.allowed is False

    def test_network_restricted_api_tool_grant(self):
        ec = ExecutionConstraint(
            timeout_seconds=60,
            network_access=NetworkAccessLevel.RESTRICTED,
            filesystem_access=FilesystemAccessLevel.NONE,
            max_calls_per_run=100,
        )
        tool = ToolDescriptor(
            tool_id="td-api",
            tool_name="external_api_client",
            description="Call external APIs with restricted network",
            supported_actions=[ToolActionType.READ, ToolActionType.SEND],
            risk_level=ToolRiskLevel.MODERATE,
        )
        grant = CapabilityGrant(
            grant_id="g-api",
            agent_id="agent-fetcher",
            tool_id="td-api",
            allowed_actions=[ToolActionType.READ, ToolActionType.SEND],
            credential_mode=CredentialMode.PREBOUND_REFERENCE,
            resource_scopes=["api:weather", "api:maps"],
            execution_constraint=ec,
        )
        req = ToolInvocationRequest(
            request_id="req-api",
            run_id="run-005",
            agent_id="agent-fetcher",
            tool_id="td-api",
            action=ToolActionType.READ,
            tenant_id="tenant-weather",
            justification="Fetch weather data",
        )
        assert req.action in tool.supported_actions
        assert req.action in grant.allowed_actions
        assert grant.credential_mode == CredentialMode.PREBOUND_REFERENCE
        assert grant.execution_constraint.network_access == NetworkAccessLevel.RESTRICTED

    def test_deny_default_no_decision(self):
        req = ToolInvocationRequest(
            request_id="req-deny",
            run_id="run-006",
            agent_id="agent-x",
            tool_id="td-unregistered",
            action=ToolActionType.WRITE,
            justification="No grant exists",
        )
        decision = PermissionDecision(
            decision_id="dec-deny",
            request_id="req-deny",
            allowed=False,
            reason="Default deny: no capability grant matches agent-x on td-unregistered",
        )
        assert decision.allowed is False

    def test_all_actions_accepted(self):
        for action in ToolActionType:
            td = ToolDescriptor(
                tool_id=f"td-{action.value}",
                tool_name=f"tool_{action.value}",
                supported_actions=[action],
                risk_level=ToolRiskLevel.LOW,
            )
            assert action in td.supported_actions

    def test_all_risk_levels_accepted(self):
        for risk in ToolRiskLevel:
            td = ToolDescriptor(
                tool_id=f"td-{risk.value}",
                tool_name=f"tool_{risk.value}",
                risk_level=risk,
            )
            assert td.risk_level == risk


class TestSerialization:
    def test_descriptor_to_json(self):
        td = ToolDescriptor(
            tool_id="td-json",
            tool_name="json_tool",
            supported_actions=[ToolActionType.READ],
            risk_level=ToolRiskLevel.LOW,
        )
        data = td.model_dump()
        assert data["tool_id"] == "td-json"
        assert "read" in data["supported_actions"]

    def test_invocation_request_roundtrip(self):
        req = ToolInvocationRequest(
            request_id="req-round",
            run_id="run-round",
            agent_id="agent-round",
            tool_id="td-round",
            action=ToolActionType.SEND,
            justification="Roundtrip test",
            tenant_id="tenant-round",
        )
        raw = req.model_dump()
        restored = ToolInvocationRequest(**raw)
        assert restored.request_id == req.request_id
        assert restored.action == req.action
        assert restored.tenant_id == req.tenant_id

    def test_decision_roundtrip(self):
        d = PermissionDecision(
            decision_id="dec-round",
            request_id="req-round",
            allowed=False,
            reason="No grant",
            matched_grant_id="g-nonexistent",
            approval_required=False,
        )
        raw = d.model_dump()
        restored = PermissionDecision(**raw)
        assert restored.allowed is False
        assert restored.matched_grant_id == "g-nonexistent"
