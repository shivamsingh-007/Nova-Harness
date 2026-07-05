import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from models.agent_role_specialization_contract import (
    AgentRoleType, RoleStatus, SpecializationType, AutonomyLevel, RoleOutputType,
    AgentRoleDefinition, RoleSpecializationProfile, RoleCapabilityProfile,
    RoleConstraintProfile, RolePromptProfile, RoleEvaluationProfile,
    RoleAssignmentRecord, AgentRoleEnvelope,
    ACTIVATABLE_ROLE_STATUSES, NON_ACTIVATABLE_ROLE_STATUSES,
    MANAGER_LIKE_ROLES, SUPERVISORY_AUTONOMY_LEVEL,
)

NOW = datetime.now(timezone.utc)


def make_role_def(**overrides) -> AgentRoleDefinition:
    defaults = dict(role_id="role-coder-001", role_type=AgentRoleType.CODER,
                    name="Coding Specialist", status=RoleStatus.ACTIVE,
                    specialization_type=SpecializationType.CODING_SPECIFIC,
                    autonomy_level=AutonomyLevel.BOUNDED_EXECUTION,
                    expected_output_types=[RoleOutputType.IMPLEMENTATION],
                    version="1.0.0", created_at=NOW, updated_at=NOW)
    defaults.update(overrides)
    return AgentRoleDefinition(**defaults)


def make_specialization(**overrides) -> RoleSpecializationProfile:
    defaults = dict(profile_id="spec-001", role_id="role-coder-001",
                    domain_tags=["python", "backend"],
                    task_types=["code generation", "refactoring"],
                    strengths=["fast code generation", "type safety"],
                    weaknesses=["limited domain knowledge"],
                    quality_focus="correctness")
    defaults.update(overrides)
    return RoleSpecializationProfile(**defaults)


def make_capability(**overrides) -> RoleCapabilityProfile:
    defaults = dict(capability_profile_id="cap-001", role_id="role-coder-001",
                    allowed_tools=["read", "write", "execute"],
                    allowed_skill_ids=["skill-py-codegen"],
                    can_verify=True)
    defaults.update(overrides)
    return RoleCapabilityProfile(**defaults)


def make_constraint(**overrides) -> RoleConstraintProfile:
    defaults = dict(constraint_profile_id="con-001", role_id="role-coder-001",
                    forbidden_tools=["deploy", "delete"],
                    must_not_write_without_verification=True)
    defaults.update(overrides)
    return RoleConstraintProfile(**defaults)


def make_prompt(**overrides) -> RolePromptProfile:
    defaults = dict(prompt_profile_id="prompt-001", role_id="role-coder-001",
                    system_prompt_ref="prompts/coder_system_v1.md",
                    instruction_pack_refs=["packs/coding_standards_v2"],
                    handoff_template_ref="templates/coder_handoff.md")
    defaults.update(overrides)
    return RolePromptProfile(**defaults)


def make_evaluation(**overrides) -> RoleEvaluationProfile:
    defaults = dict(evaluation_profile_id="eval-001", role_id="role-coder-001",
                    success_criteria=["code compiles", "tests pass"],
                    failure_modes=["syntax errors", "security vulnerabilities"],
                    required_evidence_types=["test_output", "coverage_report"],
                    quality_metrics=["correctness", "performance"],
                    review_policy="peer_review_required")
    defaults.update(overrides)
    return RoleEvaluationProfile(**defaults)


def make_assignment(**overrides) -> RoleAssignmentRecord:
    defaults = dict(assignment_id="assign-001", role_id="role-coder-001",
                    agent_id="agent-003", run_id="run-042",
                    assigned_by="orchestrator",
                    assignment_reason="Code generation subtask")
    defaults.update(overrides)
    return RoleAssignmentRecord(**defaults)


def make_envelope(role_def=None, assignment=None, **overrides) -> AgentRoleEnvelope:
    rd = role_def or make_role_def()
    data = dict(envelope_id="env-001", role_definition=rd,
                specialization_profile=make_specialization(),
                capability_profile=make_capability(),
                constraint_profile=make_constraint(),
                prompt_profile=make_prompt(),
                evaluation_profile=make_evaluation(),
                assignment_record=assignment)
    data.update(overrides)
    return AgentRoleEnvelope(**data)


class TestEnums:
    def test_agent_role_type_values(self):
        assert AgentRoleType.MANAGER.value == "manager"
        assert AgentRoleType.CODER.value == "coder"
        assert len(AgentRoleType) == 10

    def test_role_status_values(self):
        assert RoleStatus.ACTIVE.value == "active"
        assert RoleStatus.DISABLED.value == "disabled"
        assert len(RoleStatus) == 4

    def test_activatable_statuses(self):
        assert RoleStatus.ACTIVE in ACTIVATABLE_ROLE_STATUSES
        assert RoleStatus.DISABLED in NON_ACTIVATABLE_ROLE_STATUSES

    def test_specialization_type_values(self):
        assert SpecializationType.GENERALIST.value == "generalist"
        assert SpecializationType.CODING_SPECIFIC.value == "coding_specific"
        assert len(SpecializationType) == 7

    def test_autonomy_level_values(self):
        assert AutonomyLevel.ADVISORY_ONLY.value == "advisory_only"
        assert AutonomyLevel.SUPERVISORY.value == "supervisory"
        assert len(AutonomyLevel) == 4

    def test_supervisory_autonomy_constant(self):
        assert SUPERVISORY_AUTONOMY_LEVEL == AutonomyLevel.SUPERVISORY

    def test_role_output_type_values(self):
        assert RoleOutputType.PLAN.value == "plan"
        assert RoleOutputType.TOOL_RESULT.value == "tool_result"
        assert len(RoleOutputType) == 8


class TestAgentRoleDefinition:
    def test_valid(self):
        r = make_role_def()
        assert r.role_id == "role-coder-001"
        assert r.role_type == AgentRoleType.CODER

    def test_blank_role_id_raises(self):
        with pytest.raises(ValidationError):
            make_role_def(role_id="  ")

    def test_blank_name_raises(self):
        with pytest.raises(ValidationError):
            make_role_def(name="  ")

    def test_manager_supervisory_valid(self):
        r = make_role_def(role_type=AgentRoleType.MANAGER,
                          autonomy_level=AutonomyLevel.SUPERVISORY)
        assert r.autonomy_level == AutonomyLevel.SUPERVISORY

    def test_non_manager_supervisory_raises(self):
        with pytest.raises(ValidationError, match="supervisory autonomy"):
            make_role_def(role_type=AgentRoleType.CODER,
                          autonomy_level=AutonomyLevel.SUPERVISORY)

    def test_default_status(self):
        r = AgentRoleDefinition(role_id="role-x", role_type=AgentRoleType.PLANNER, name="X")
        assert r.status == RoleStatus.DRAFT

    def test_expected_output_types(self):
        r = make_role_def(expected_output_types=[RoleOutputType.REVIEW, RoleOutputType.VERIFICATION_REPORT])
        assert len(r.expected_output_types) == 2

    def test_strip_whitespace(self):
        r = AgentRoleDefinition(role_id="  role-x  ", role_type=AgentRoleType.RETRIEVER, name="  Retriever  ")
        assert r.role_id == "role-x"
        assert r.name == "Retriever"


class TestRoleSpecializationProfile:
    def test_valid(self):
        s = make_specialization()
        assert s.profile_id == "spec-001"
        assert "python" in s.domain_tags

    def test_blank_profile_id_raises(self):
        with pytest.raises(ValidationError):
            make_specialization(profile_id="  ")

    def test_strengths_and_weaknesses(self):
        s = make_specialization(strengths=["a", "b"], weaknesses=["c"])
        assert len(s.strengths) == 2
        assert len(s.weaknesses) == 1

    def test_task_types_empty_by_default(self):
        s = make_specialization(task_types=[])
        assert s.task_types == []

    def test_risk_notes_optional(self):
        s = make_specialization(risk_notes="May over-engineer")
        assert s.risk_notes == "May over-engineer"


class TestRoleCapabilityProfile:
    def test_valid(self):
        c = make_capability()
        assert c.can_verify is True

    def test_blank_profile_id_raises(self):
        with pytest.raises(ValidationError):
            make_capability(capability_profile_id="  ")

    def test_can_delegate_without_boundaries_raises(self):
        with pytest.raises(ValidationError, match="delegation_boundaries"):
            make_capability(can_delegate=True, delegation_boundaries=None)

    def test_can_delegate_with_boundaries_valid(self):
        c = make_capability(can_delegate=True, delegation_boundaries="only to verifier and retriever")
        assert c.can_delegate is True

    def test_can_modify_artifacts_default_false(self):
        c = make_capability()
        assert c.can_modify_artifacts is False

    def test_max_budget_scope_optional(self):
        c = make_capability(max_budget_scope="run")
        assert c.max_budget_scope == "run"


class TestRoleConstraintProfile:
    def test_valid(self):
        c = make_constraint()
        assert "deploy" in c.forbidden_tools

    def test_blank_profile_id_raises(self):
        with pytest.raises(ValidationError):
            make_constraint(constraint_profile_id="  ")

    def test_forbidden_actions(self):
        c = make_constraint(forbidden_actions=["delete_remote", "modify_secrets"])
        assert "delete_remote" in c.forbidden_actions

    def test_approval_required_actions(self):
        c = make_constraint(approval_required_actions=["deploy", "delete"])
        assert len(c.approval_required_actions) == 2

    def test_must_not_write_without_verification(self):
        c = make_constraint(must_not_write_without_verification=True)
        assert c.must_not_write_without_verification is True

    def test_must_not_delegate_further(self):
        c = make_constraint(must_not_delegate_further=True)
        assert c.must_not_delegate_further is True


class TestRolePromptProfile:
    def test_valid(self):
        p = make_prompt()
        assert p.system_prompt_ref == "prompts/coder_system_v1.md"

    def test_blank_profile_id_raises(self):
        with pytest.raises(ValidationError):
            make_prompt(prompt_profile_id="  ")

    def test_prompt_fragments(self):
        p = make_prompt(prompt_fragments=["fragment_code_style", "fragment_test_gen"])
        assert len(p.prompt_fragments) == 2

    def test_style_notes_optional(self):
        p = make_prompt(style_notes="Write concise, typed Python")
        assert p.style_notes is not None

    def test_handoff_template_ref_optional(self):
        p = make_prompt(handoff_template_ref=None)
        assert p.handoff_template_ref is None


class TestRoleEvaluationProfile:
    def test_valid(self):
        e = make_evaluation()
        assert "code compiles" in e.success_criteria

    def test_blank_profile_id_raises(self):
        with pytest.raises(ValidationError):
            make_evaluation(evaluation_profile_id="  ")

    def test_failure_modes(self):
        e = make_evaluation(failure_modes=["runtime error", "timeout"])
        assert len(e.failure_modes) == 2

    def test_required_evidence_types(self):
        e = make_evaluation(required_evidence_types=["log", "trace"])
        assert "log" in e.required_evidence_types

    def test_quality_metrics(self):
        e = make_evaluation(quality_metrics=["latency", "accuracy"])
        assert "accuracy" in e.quality_metrics


class TestRoleAssignmentRecord:
    def test_valid(self):
        a = make_assignment()
        assert a.agent_id == "agent-003"

    def test_blank_assignment_id_raises(self):
        with pytest.raises(ValidationError):
            make_assignment(assignment_id="  ")

    def test_blank_role_id_raises(self):
        with pytest.raises(ValidationError):
            make_assignment(role_id="  ")

    def test_blank_agent_id_raises(self):
        with pytest.raises(ValidationError):
            make_assignment(agent_id="  ")

    def test_run_id_optional(self):
        a = make_assignment(run_id=None)
        assert a.run_id is None

    def test_session_id_optional(self):
        a = make_assignment(session_id="session-xyz")
        assert a.session_id == "session-xyz"

    def test_active_until_optional(self):
        a = make_assignment(active_until=NOW)
        assert a.active_until is not None


class TestAgentRoleEnvelope:
    def test_valid(self):
        e = make_envelope()
        assert e.envelope_id == "env-001"
        assert e.role_definition.role_type == AgentRoleType.CODER

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="  ")

    def test_empty_role_is_not_active_so_no_capability_needed(self):
        rd = make_role_def(status=RoleStatus.DRAFT)
        e = AgentRoleEnvelope(envelope_id="env-x", role_definition=rd)
        assert e.envelope_id == "env-x"

    def test_active_role_requires_capability_profile(self):
        rd = make_role_def(status=RoleStatus.ACTIVE)
        with pytest.raises(ValidationError, match="active roles must have a capability_profile"):
            AgentRoleEnvelope(envelope_id="env-x", role_definition=rd,
                              specialization_profile=make_specialization())

    def test_active_role_requires_constraint_profile(self):
        rd = make_role_def(status=RoleStatus.ACTIVE)
        with pytest.raises(ValidationError, match="active roles must have a constraint_profile"):
            AgentRoleEnvelope(envelope_id="env-x", role_definition=rd,
                              capability_profile=make_capability())

    def test_active_role_with_both_profiles_valid(self):
        rd = make_role_def(status=RoleStatus.ACTIVE)
        e = AgentRoleEnvelope(envelope_id="env-x", role_definition=rd,
                              capability_profile=make_capability(),
                              constraint_profile=make_constraint())
        assert e.role_definition.status == RoleStatus.ACTIVE

    def test_artifact_modifying_role_needs_verification_boundary(self):
        cap = make_capability(can_modify_artifacts=True, can_verify=False)
        con = make_constraint(must_not_write_without_verification=False)
        rd = make_role_def(status=RoleStatus.ACTIVE)
        with pytest.raises(ValidationError, match="can_modify_artifacts"):
            AgentRoleEnvelope(envelope_id="env-x", role_definition=rd,
                              capability_profile=cap, constraint_profile=con)

    def test_artifact_modifying_with_verify_is_valid(self):
        cap = make_capability(can_modify_artifacts=True, can_verify=True)
        rd = make_role_def(status=RoleStatus.ACTIVE)
        e = AgentRoleEnvelope(envelope_id="env-x", role_definition=rd,
                              capability_profile=cap,
                              constraint_profile=make_constraint())
        assert e.capability_profile.can_modify_artifacts is True

    def test_artifact_modifying_with_writes_valid(self):
        cap = make_capability(can_modify_artifacts=True, can_verify=False)
        con = make_constraint(must_not_write_without_verification=True)
        rd = make_role_def(status=RoleStatus.ACTIVE)
        e = AgentRoleEnvelope(envelope_id="env-x", role_definition=rd,
                              capability_profile=cap, constraint_profile=con)
        assert e.capability_profile.can_modify_artifacts is True

    def test_forbidden_tools_not_in_allowed(self):
        cap = make_capability(allowed_tools=["read", "write", "deploy"])
        con = make_constraint(forbidden_tools=["deploy"])
        rd = make_role_def(status=RoleStatus.ACTIVE)
        with pytest.raises(ValidationError, match="forbidden tool"):
            AgentRoleEnvelope(envelope_id="env-x", role_definition=rd,
                              capability_profile=cap, constraint_profile=con)

    def test_assignment_must_reference_active_role(self):
        rd = make_role_def(status=RoleStatus.DISABLED)
        assign = make_assignment()
        with pytest.raises(ValidationError, match="assignment records must reference an active role"):
            AgentRoleEnvelope(envelope_id="env-x", role_definition=rd,
                              capability_profile=make_capability(),
                              constraint_profile=make_constraint(),
                              assignment_record=assign)

    def test_assignment_with_active_role_valid(self):
        rd = make_role_def(status=RoleStatus.ACTIVE)
        assign = make_assignment()
        e = AgentRoleEnvelope(envelope_id="env-x", role_definition=rd,
                              capability_profile=make_capability(),
                              constraint_profile=make_constraint(),
                              assignment_record=assign)
        assert e.assignment_record.agent_id == "agent-003"

    def test_minimal_draft_envelope(self):
        rd = make_role_def(status=RoleStatus.DRAFT, role_type=AgentRoleType.RETRIEVER)
        e = AgentRoleEnvelope(envelope_id="env-min", role_definition=rd)
        assert e.envelope_id == "env-min"

    def test_all_optional_profiles_none(self):
        rd = make_role_def(status=RoleStatus.DRAFT)
        e = AgentRoleEnvelope(envelope_id="env-all-none", role_definition=rd,
                              specialization_profile=None, capability_profile=None,
                              constraint_profile=None, prompt_profile=None,
                              evaluation_profile=None, assignment_record=None)
        assert e.specialization_profile is None


class TestSerialization:
    def test_role_def_to_dict_and_back(self):
        r = make_role_def()
        d = r.model_dump()
        r2 = AgentRoleDefinition(**d)
        assert r2.role_id == r.role_id
        assert r2.role_type == r.role_type

    def test_envelope_to_dict_and_back(self):
        e = make_envelope()
        d = e.model_dump()
        e2 = AgentRoleEnvelope(**d)
        assert e2.envelope_id == e.envelope_id
        assert e2.role_definition.role_type == e.role_definition.role_type
        assert e2.specialization_profile.profile_id == e.specialization_profile.profile_id

    def test_full_envelope_roundtrip(self):
        e = make_envelope(assignment_record=make_assignment())
        d = e.model_dump(mode="json")
        e2 = AgentRoleEnvelope(**d)
        assert e2.assignment_record.agent_id == "agent-003"
        assert e2.evaluation_profile.quality_metrics == ["correctness", "performance"]

    def test_json_serialization(self):
        e = make_envelope()
        j = e.model_dump_json()
        e2 = AgentRoleEnvelope.model_validate_json(j)
        assert e2.role_definition.name == "Coding Specialist"


class TestIntegration:
    def test_manager_role_with_supervisory_autonomy(self):
        rd = AgentRoleDefinition(
            role_id="role-mgr-001", role_type=AgentRoleType.MANAGER,
            name="Team Manager", status=RoleStatus.ACTIVE,
            specialization_type=SpecializationType.COORDINATION_SPECIFIC,
            autonomy_level=AutonomyLevel.SUPERVISORY,
            expected_output_types=[RoleOutputType.PLAN, RoleOutputType.REVIEW],
            version="1.0.0", created_at=NOW, updated_at=NOW,
        )
        cap = RoleCapabilityProfile(
            capability_profile_id="cap-mgr", role_id="role-mgr-001",
            allowed_tools=["read", "write", "delegate"],
            can_delegate=True, delegation_boundaries="only to verified roles",
            can_verify=True, can_modify_artifacts=True,
        )
        con = RoleConstraintProfile(
            constraint_profile_id="con-mgr", role_id="role-mgr-001",
            forbidden_tools=["execute"],
            approval_required_actions=["deploy"],
        )
        e = AgentRoleEnvelope(envelope_id="env-mgr", role_definition=rd,
                              capability_profile=cap, constraint_profile=con)
        assert e.role_definition.autonomy_level == AutonomyLevel.SUPERVISORY

    def test_disabled_role_rejected_for_assignment(self):
        rd = make_role_def(status=RoleStatus.DISABLED)
        assign = make_assignment()
        with pytest.raises(ValidationError, match="assignment records must reference an active role"):
            AgentRoleEnvelope(envelope_id="env-disable", role_definition=rd,
                              capability_profile=make_capability(),
                              constraint_profile=make_constraint(),
                              assignment_record=assign)

    def test_verifier_role_with_strict_evidence(self):
        rd = make_role_def(role_id="role-verifier-001", role_type=AgentRoleType.VERIFIER,
                           name="Quality Verifier",
                           specialization_type=SpecializationType.VERIFICATION_SPECIFIC,
                           expected_output_types=[RoleOutputType.VERIFICATION_REPORT])
        spec = make_specialization(profile_id="spec-ver", role_id="role-verifier-001",
                                   strengths=["thorough checking"], weaknesses=["slow"],
                                   quality_focus="completeness")
        cap = make_capability(capability_profile_id="cap-ver", role_id="role-verifier-001",
                              allowed_tools=["read", "compare"], can_verify=True)
        con = make_constraint(constraint_profile_id="con-ver", role_id="role-verifier-001",
                              forbidden_tools=["write", "execute", "deploy"],
                              must_not_write_without_verification=True)
        eval_p = make_evaluation(evaluation_profile_id="eval-ver", role_id="role-verifier-001",
                                 success_criteria=["all checks pass", "no false negatives"],
                                 failure_modes=["missed defect", "false positive"],
                                 required_evidence_types=["checklist", "trace_log"],
                                 quality_metrics=["precision", "recall"])
        e = AgentRoleEnvelope(envelope_id="env-ver", role_definition=rd,
                              specialization_profile=spec, capability_profile=cap,
                              constraint_profile=con, evaluation_profile=eval_p)
        assert "thorough checking" in e.specialization_profile.strengths
        assert "write" in e.constraint_profile.forbidden_tools

    def test_retriever_role_bounded_capabilities(self):
        rd = make_role_def(role_id="role-ret-001", role_type=AgentRoleType.RETRIEVER,
                           name="Knowledge Retriever",
                           specialization_type=SpecializationType.RETRIEVAL_SPECIFIC,
                           expected_output_types=[RoleOutputType.RETRIEVAL_BUNDLE])
        cap = make_capability(capability_profile_id="cap-ret", role_id="role-ret-001",
                              allowed_tools=["read", "search", "fetch"],
                              allowed_context_types=["docs", "codebase"],
                              can_delegate=False, can_verify=False, can_modify_artifacts=False)
        con = make_constraint(constraint_profile_id="con-ret", role_id="role-ret-001",
                              forbidden_tools=["write", "execute", "deploy", "delete"],
                              must_not_write_without_verification=True,
                              must_not_delegate_further=True)
        e = AgentRoleEnvelope(envelope_id="env-ret", role_definition=rd,
                              capability_profile=cap, constraint_profile=con)
        assert e.capability_profile.can_delegate is False
        assert e.constraint_profile.must_not_delegate_further is True

    def test_planner_role_with_plan_output(self):
        rd = make_role_def(role_id="role-plan-001", role_type=AgentRoleType.PLANNER,
                           name="Task Planner",
                           expected_output_types=[RoleOutputType.PLAN, RoleOutputType.ANALYSIS],
                           specialization_type=SpecializationType.GENERALIST)
        prompt = make_prompt(prompt_profile_id="prompt-plan", role_id="role-plan-001",
                             system_prompt_ref="prompts/planner_system_v1.md",
                             instruction_pack_refs=["packs/planning_framework"])
        e = AgentRoleEnvelope(envelope_id="env-plan", role_definition=rd,
                              capability_profile=make_capability(),
                              constraint_profile=make_constraint(),
                              prompt_profile=prompt)
        assert RoleOutputType.PLAN in e.role_definition.expected_output_types
        assert "prompts/planner_system_v1.md" in e.prompt_profile.system_prompt_ref

    def test_agent_assignment_with_session_id(self):
        rd = make_role_def(status=RoleStatus.ACTIVE)
        assign = make_assignment(assignment_id="assign-session", agent_id="agent-007",
                                 session_id="session-42", run_id="run-99")
        e = make_envelope(role_def=rd, assignment_record=assign)
        assert e.assignment_record.session_id == "session-42"
        assert e.assignment_record.run_id == "run-99"

    def test_disabled_status_not_activatable(self):
        assert RoleStatus.DISABLED in NON_ACTIVATABLE_ROLE_STATUSES
        assert RoleStatus.DISABLED not in ACTIVATABLE_ROLE_STATUSES

    def test_deprecated_status_not_activatable(self):
        assert RoleStatus.DEPRECATED not in ACTIVATABLE_ROLE_STATUSES
