import pytest
from pydantic import ValidationError
from models.agent_identity_contract import (
    AgentAuthorityModel,
    IdentityType,
    RunInitiatorType,
    LifecycleStatus,
    OwnerRef,
    AuthorityScope,
    DelegationContext,
    AgentIdentity,
    RunOwnership,
    AuthorityAssertion,
)


def make_owner() -> OwnerRef:
    return OwnerRef(owner_id="team-eng", owner_type="team",
                    owner_name="Engineering Team")


class TestEnums:
    def test_authority_model_values(self):
        assert AgentAuthorityModel.DELEGATED.value == "delegated"
        assert AgentAuthorityModel.AUTONOMOUS.value == "autonomous"

    def test_identity_type_values(self):
        assert IdentityType.WORKLOAD.value == "workload"
        assert IdentityType.FEDERATED.value == "federated"

    def test_run_initiator_type_values(self):
        assert RunInitiatorType.USER.value == "user"
        assert RunInitiatorType.API.value == "api"

    def test_lifecycle_status_values(self):
        assert LifecycleStatus.ACTIVE.value == "active"
        assert LifecycleStatus.REVOKED.value == "revoked"


class TestOwnerRef:
    def test_valid(self):
        owner = make_owner()
        assert owner.owner_name == "Engineering Team"

    def test_empty_owner_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            OwnerRef(owner_id="  ", owner_type="team")
        assert "must not be empty" in str(exc.value)

    def test_empty_owner_type_raises(self):
        with pytest.raises(ValidationError) as exc:
            OwnerRef(owner_id="owner-1", owner_type="  ")
        assert "must not be empty" in str(exc.value)


class TestAuthorityScope:
    def test_valid(self):
        scope = AuthorityScope(scope_id="scope-001", scope_type="tool",
                               scope_value="write_file",
                               description="Permission to write files")
        assert scope.description == "Permission to write files"

    def test_empty_scope_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            AuthorityScope(scope_id="  ", scope_type="tool", scope_value="write")
        assert "must not be empty" in str(exc.value)

    def test_empty_scope_type_raises(self):
        with pytest.raises(ValidationError) as exc:
            AuthorityScope(scope_id="s1", scope_type="  ", scope_value="write")
        assert "must not be empty" in str(exc.value)

    def test_empty_scope_value_raises(self):
        with pytest.raises(ValidationError) as exc:
            AuthorityScope(scope_id="s1", scope_type="tool", scope_value="  ")
        assert "must not be empty" in str(exc.value)


class TestDelegationContext:
    def test_empty(self):
        ctx = DelegationContext()
        assert ctx.delegated_by_principal_id is None

    def test_on_behalf_of_with_reason(self):
        ctx = DelegationContext(
            delegated_by_principal_id="user-shiva",
            on_behalf_of_user_id="user-shiva",
            delegation_reason="Task initiated via CLI",
            authority_scopes=[
                AuthorityScope(scope_id="s1", scope_type="tool",
                               scope_value="write_file"),
            ],
        )
        assert ctx.delegation_reason == "Task initiated via CLI"

    def test_on_behalf_of_no_reason_raises(self):
        with pytest.raises(ValidationError) as exc:
            DelegationContext(
                on_behalf_of_user_id="user-shiva",
            )
        assert "delegation_reason required when acting on behalf of a user" in str(exc.value)

    def test_delegated_no_scopes_raises(self):
        with pytest.raises(ValidationError) as exc:
            DelegationContext(
                delegated_by_principal_id="user-shiva",
            )
        assert "delegation must include at least one authority_scope" in str(exc.value)


class TestAgentIdentity:
    def test_active_with_review(self):
        identity = AgentIdentity(
            agent_id="agent-codex-v2",
            agent_name="Codex Agent v2",
            identity_type=IdentityType.WORKLOAD,
            authority_model=AgentAuthorityModel.BOUNDED,
            owner=make_owner(),
            lifecycle_status=LifecycleStatus.ACTIVE,
            review_due_at="2026-09-01T00:00:00Z",
        )
        assert identity.credential_reference is None

    def test_autonomous(self):
        identity = AgentIdentity(
            agent_id="agent-cicd-pipeline",
            agent_name="CI/CD Pipeline Agent",
            identity_type=IdentityType.SERVICE_PRINCIPAL,
            authority_model=AgentAuthorityModel.AUTONOMOUS,
            owner=make_owner(),
            lifecycle_status=LifecycleStatus.ACTIVE,
            review_due_at="2026-12-01T00:00:00Z",
            credential_reference="vault://cicd-agent-key",
        )
        assert identity.credential_reference == "vault://cicd-agent-key"

    def test_revoked_no_review_ok(self):
        identity = AgentIdentity(
            agent_id="agent-deprecated",
            agent_name="Deprecated Agent",
            identity_type=IdentityType.API_KEY,
            authority_model=AgentAuthorityModel.DELEGATED,
            owner=make_owner(),
            lifecycle_status=LifecycleStatus.REVOKED,
        )
        assert identity.lifecycle_status == LifecycleStatus.REVOKED

    def test_expired_no_review_ok(self):
        identity = AgentIdentity(
            agent_id="agent-expired",
            agent_name="Expired Agent",
            identity_type=IdentityType.WORKLOAD,
            authority_model=AgentAuthorityModel.BOUNDED,
            owner=make_owner(),
            lifecycle_status=LifecycleStatus.EXPIRED,
        )
        assert identity.lifecycle_status == LifecycleStatus.EXPIRED

    def test_active_missing_review_raises(self):
        with pytest.raises(ValidationError) as exc:
            AgentIdentity(
                agent_id="agent-no-review",
                agent_name="No Review Agent",
                identity_type=IdentityType.WORKLOAD,
                authority_model=AgentAuthorityModel.BOUNDED,
                owner=make_owner(),
                lifecycle_status=LifecycleStatus.ACTIVE,
            )
        assert "ACTIVE or SUSPENDED identities must have a review_due_at" in str(exc.value)

    def test_suspended_missing_review_raises(self):
        with pytest.raises(ValidationError) as exc:
            AgentIdentity(
                agent_id="agent-suspend",
                agent_name="Suspended No Review",
                identity_type=IdentityType.WORKLOAD,
                authority_model=AgentAuthorityModel.DELEGATED,
                owner=make_owner(),
                lifecycle_status=LifecycleStatus.SUSPENDED,
            )
        assert "ACTIVE or SUSPENDED identities must have a review_due_at" in str(exc.value)

    def test_empty_agent_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            AgentIdentity(
                agent_id="  ", agent_name="n",
                identity_type=IdentityType.WORKLOAD,
                authority_model=AgentAuthorityModel.BOUNDED,
                owner=make_owner(),
                lifecycle_status=LifecycleStatus.ACTIVE,
                review_due_at="2026-09-01T00:00:00Z",
            )
        assert "must not be empty" in str(exc.value)

    def test_empty_agent_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            AgentIdentity(
                agent_id="a", agent_name="  ",
                identity_type=IdentityType.WORKLOAD,
                authority_model=AgentAuthorityModel.BOUNDED,
                owner=make_owner(),
                lifecycle_status=LifecycleStatus.ACTIVE,
                review_due_at="2026-09-01T00:00:00Z",
            )
        assert "must not be empty" in str(exc.value)


class TestRunOwnership:
    def test_system_initiated(self):
        owner = RunOwnership(
            run_id="run-001", agent_id="agent-cicd",
            initiator_type=RunInitiatorType.SYSTEM,
            requested_by_id="system-scheduler",
            owning_principal_id="team-eng",
        )
        assert owner.delegation_context is None

    def test_user_initiated_with_delegation(self):
        owner = RunOwnership(
            run_id="run-002", agent_id="agent-codex",
            initiator_type=RunInitiatorType.USER,
            requested_by_id="user-shiva",
            owning_principal_id="user-shiva",
            delegation_context=DelegationContext(
                delegated_by_principal_id="user-shiva",
                on_behalf_of_user_id="user-shiva",
                delegation_reason="Manual run via CLI",
                authority_scopes=[
                    AuthorityScope(scope_id="s1", scope_type="tool",
                                   scope_value="write_file"),
                ],
            ),
        )
        assert owner.delegation_context is not None

    def test_schedule_initiated(self):
        owner = RunOwnership(
            run_id="run-003", agent_id="agent-cron",
            initiator_type=RunInitiatorType.SCHEDULE,
            requested_by_id="system-cron",
            owning_principal_id="team-platform",
        )
        assert owner.initiator_type == RunInitiatorType.SCHEDULE

    def test_user_initiated_no_delegation_raises(self):
        with pytest.raises(ValidationError) as exc:
            RunOwnership(
                run_id="run-004", agent_id="agent-codex",
                initiator_type=RunInitiatorType.USER,
                requested_by_id="user-shiva",
                owning_principal_id="user-shiva",
            )
        assert "USER-initiated runs must have a delegation_context" in str(exc.value)

    def test_empty_run_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            RunOwnership(run_id="  ", agent_id="a",
                         initiator_type=RunInitiatorType.SYSTEM,
                         requested_by_id="r", owning_principal_id="o")
        assert "must not be empty" in str(exc.value)

    def test_empty_agent_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            RunOwnership(run_id="r", agent_id="  ",
                         initiator_type=RunInitiatorType.SYSTEM,
                         requested_by_id="r", owning_principal_id="o")
        assert "must not be empty" in str(exc.value)

    def test_empty_requested_by_raises(self):
        with pytest.raises(ValidationError) as exc:
            RunOwnership(run_id="r", agent_id="a",
                         initiator_type=RunInitiatorType.SYSTEM,
                         requested_by_id="  ", owning_principal_id="o")
        assert "must not be empty" in str(exc.value)

    def test_empty_owning_principal_raises(self):
        with pytest.raises(ValidationError) as exc:
            RunOwnership(run_id="r", agent_id="a",
                         initiator_type=RunInitiatorType.SYSTEM,
                         requested_by_id="r", owning_principal_id="  ")
        assert "must not be empty" in str(exc.value)


class TestAuthorityAssertion:
    def test_bounded_with_scopes(self):
        assertion = AuthorityAssertion(
            assertion_id="aa-001", run_id="run-001", agent_id="agent-codex",
            authority_model=AgentAuthorityModel.BOUNDED,
            effective_scopes=[
                AuthorityScope(scope_id="s1", scope_type="tool",
                               scope_value="read_file"),
                AuthorityScope(scope_id="s2", scope_type="tool",
                               scope_value="write_file",
                               description="Write files under /workspace"),
            ],
            expires_at="2026-07-04T18:00:00Z",
        )
        assert len(assertion.effective_scopes) == 2
        assert assertion.expires_at == "2026-07-04T18:00:00Z"

    def test_delegated_with_scopes(self):
        assertion = AuthorityAssertion(
            assertion_id="aa-002", run_id="run-002", agent_id="agent-codex",
            authority_model=AgentAuthorityModel.DELEGATED,
            effective_scopes=[
                AuthorityScope(scope_id="s1", scope_type="tool",
                               scope_value="read_file"),
            ],
        )
        assert assertion.authority_model == AgentAuthorityModel.DELEGATED

    def test_empty_scopes_raises(self):
        with pytest.raises(ValidationError) as exc:
            AuthorityAssertion(
                assertion_id="aa-003", run_id="run-003", agent_id="agent-x",
                authority_model=AgentAuthorityModel.AUTONOMOUS,
                effective_scopes=[],
            )
        assert "authority assertion must have at least one effective_scope" in str(exc.value)

    def test_empty_assertion_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            AuthorityAssertion(assertion_id="  ", run_id="r", agent_id="a",
                               authority_model=AgentAuthorityModel.BOUNDED,
                               effective_scopes=[
                                   AuthorityScope(scope_id="s1", scope_type="t",
                                                  scope_value="v"),
                               ])
        assert "must not be empty" in str(exc.value)

    def test_empty_run_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            AuthorityAssertion(assertion_id="a", run_id="  ", agent_id="a",
                               authority_model=AgentAuthorityModel.BOUNDED,
                               effective_scopes=[
                                   AuthorityScope(scope_id="s1", scope_type="t",
                                                  scope_value="v"),
                               ])
        assert "must not be empty" in str(exc.value)

    def test_empty_agent_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            AuthorityAssertion(assertion_id="a", run_id="r", agent_id="  ",
                               authority_model=AgentAuthorityModel.BOUNDED,
                               effective_scopes=[
                                   AuthorityScope(scope_id="s1", scope_type="t",
                                                  scope_value="v"),
                               ])
        assert "must not be empty" in str(exc.value)


class TestSerialization:
    def test_identity_to_json(self):
        identity = AgentIdentity(
            agent_id="agent-01", agent_name="My Agent",
            identity_type=IdentityType.WORKLOAD,
            authority_model=AgentAuthorityModel.BOUNDED,
            owner=OwnerRef(owner_id="team-a", owner_type="team"),
            lifecycle_status=LifecycleStatus.ACTIVE,
            review_due_at="2026-09-01T00:00:00Z",
        )
        json_str = identity.model_dump_json()
        assert "agent-01" in json_str
        assert "bounded" in json_str

    def test_ownership_roundtrip(self):
        owner = RunOwnership(
            run_id="run-001", agent_id="agent-a",
            initiator_type=RunInitiatorType.SYSTEM,
            requested_by_id="req-1", owning_principal_id="team-a",
        )
        dumped = owner.model_dump()
        assert dumped["initiator_type"] == "system"

    def test_assertion_roundtrip(self):
        assertion = AuthorityAssertion(
            assertion_id="a1", run_id="r1", agent_id="a1",
            authority_model=AgentAuthorityModel.AUTONOMOUS,
            effective_scopes=[
                AuthorityScope(scope_id="s1", scope_type="tool",
                               scope_value="*"),
            ],
        )
        dumped = assertion.model_dump()
        assert dumped["authority_model"] == "autonomous"
