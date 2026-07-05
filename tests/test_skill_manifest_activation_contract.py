import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from models.skill_manifest_activation_contract import (
    SkillType, SkillStatus, ActivationMode, ActivationStatus, ActivationOutcome,
    SkillManifest, SkillInputSpec, SkillOutputSpec, SkillPermissionProfile,
    SkillDependencyRecord, SkillActivationRule, SkillActivationRequest,
    SkillActivationDecision, SkillActivationRecord, SkillEnvelope,
)


NOW = datetime.now(timezone.utc)


def make_manifest(**overrides) -> SkillManifest:
    defaults = dict(skill_id="skill-py-001", name="Python Code Generator",
                    version="1.0.0", description="Generates Python code",
                    skill_type=SkillType.INSTRUCTIONAL, status=SkillStatus.ACTIVE,
                    created_at=NOW, updated_at=NOW)
    defaults.update(overrides)
    return SkillManifest(**defaults)


def make_input(**overrides) -> SkillInputSpec:
    defaults = dict(input_id="in-001", name="task_description", type="string")
    defaults.update(overrides)
    return SkillInputSpec(**defaults)


def make_output(**overrides) -> SkillOutputSpec:
    defaults = dict(output_id="out-001", name="generated_code", type="string")
    defaults.update(overrides)
    return SkillOutputSpec(**defaults)


def make_permission(**overrides) -> SkillPermissionProfile:
    defaults = dict(permission_profile_id="perm-001",
                    tool_allowlist=["read", "write"])
    defaults.update(overrides)
    return SkillPermissionProfile(**defaults)


def make_dependency(**overrides) -> SkillDependencyRecord:
    defaults = dict(dependency_id="dep-001", dependency_type="tool",
                    dependency_ref="python3", required=True)
    defaults.update(overrides)
    return SkillDependencyRecord(**defaults)


def make_rule(**overrides) -> SkillActivationRule:
    defaults = dict(rule_id="rule-001", activation_mode=ActivationMode.RULE_BASED,
                    required_task_types=["coding"])
    defaults.update(overrides)
    return SkillActivationRule(**defaults)


def make_activation_request(**overrides) -> SkillActivationRequest:
    defaults = dict(activation_request_id="ar-001", skill_id="skill-py-001",
                    requested_by="router", activation_mode=ActivationMode.RULE_BASED,
                    request_reason="Coding task detected")
    defaults.update(overrides)
    return SkillActivationRequest(**defaults)


def make_activation_decision(**overrides) -> SkillActivationDecision:
    defaults = dict(decision_id="dec-001", activation_request_id="ar-001",
                    approved=True, decision_reason="Skill active and matches task")
    defaults.update(overrides)
    return SkillActivationDecision(**defaults)


def make_activation_record(**overrides) -> SkillActivationRecord:
    defaults = dict(activation_id="act-001", skill_id="skill-py-001",
                    activation_request_id="ar-001",
                    activation_status=ActivationStatus.LOADED,
                    started_at=NOW)
    defaults.update(overrides)
    return SkillActivationRecord(**defaults)


def make_envelope(**overrides) -> SkillEnvelope:
    defaults = dict(envelope_id="env-sk-001",
                    manifest=make_manifest(),
                    inputs=[make_input()],
                    outputs=[make_output()],
                    permission_profile=make_permission())
    defaults.update(overrides)
    return SkillEnvelope(**defaults)


class TestEnums:
    def test_skill_type(self):
        assert SkillType.INSTRUCTIONAL.value == "instructional"
        assert SkillType.INTEGRATION.value == "integration"
        assert len(SkillType) == 7

    def test_skill_status(self):
        assert SkillStatus.DISABLED.value == "disabled"
        assert len(SkillStatus) == 4

    def test_activation_mode(self):
        assert ActivationMode.CONTEXT_MATCH.value == "context_match"
        assert len(ActivationMode) == 5

    def test_activation_status(self):
        assert ActivationStatus.DEFERRED.value == "deferred"
        assert len(ActivationStatus) == 7

    def test_activation_outcome(self):
        assert ActivationOutcome.NOT_APPLICABLE.value == "not_applicable"
        assert len(ActivationOutcome) == 5


class TestSkillManifest:
    def test_valid(self):
        m = make_manifest()
        assert m.skill_id == "skill-py-001"

    def test_blank_skill_id_raises(self):
        with pytest.raises(ValidationError):
            make_manifest(skill_id="")

    def test_blank_name_raises(self):
        with pytest.raises(ValidationError):
            make_manifest(name="")

    def test_blank_version_raises(self):
        with pytest.raises(ValidationError):
            make_manifest(version="")

    def test_draft_status(self):
        m = make_manifest(status=SkillStatus.DRAFT)
        assert m.status == SkillStatus.DRAFT

    def test_tags(self):
        m = make_manifest(tags=["python", "codegen"])
        assert len(m.tags) == 2


class TestSkillInputSpec:
    def test_valid(self):
        i = make_input()
        assert i.input_id == "in-001"

    def test_blank_input_id_raises(self):
        with pytest.raises(ValidationError):
            make_input(input_id="")

    def test_blank_name_raises(self):
        with pytest.raises(ValidationError):
            make_input(name="")

    def test_blank_type_raises(self):
        with pytest.raises(ValidationError):
            make_input(type="")

    def test_not_required(self):
        i = make_input(required=False)
        assert i.required is False

    def test_with_default(self):
        i = make_input(default_value="hello world")
        assert i.default_value == "hello world"


class TestSkillOutputSpec:
    def test_valid(self):
        o = make_output()
        assert o.output_id == "out-001"

    def test_blank_output_id_raises(self):
        with pytest.raises(ValidationError):
            make_output(output_id="")

    def test_blank_name_raises(self):
        with pytest.raises(ValidationError):
            make_output(name="")

    def test_evidence_required(self):
        o = make_output(evidence_required=True)
        assert o.evidence_required is True

    def test_with_schema_ref(self):
        o = make_output(schema_ref="schemas/code_output.json")
        assert o.schema_ref == "schemas/code_output.json"


class TestSkillPermissionProfile:
    def test_valid(self):
        p = make_permission()
        assert p.permission_profile_id == "perm-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValidationError):
            make_permission(permission_profile_id="")

    def test_sensitive_access_requires_allowlist(self):
        with pytest.raises(ValidationError, match="permission profile must not grant unrestricted access"):
            make_permission(tool_allowlist=[], file_write_access=True)

    def test_network_with_allowlist_valid(self):
        p = make_permission(tool_allowlist=["http"], network_access=True)
        assert p.network_access is True

    def test_sensitive_data_access_requires_allowlist(self):
        with pytest.raises(ValidationError, match="permission profile must not grant unrestricted access"):
            make_permission(tool_allowlist=[], sensitive_data_access=True)

    def test_empty_allowlist_no_sensitive_valid(self):
        p = make_permission(tool_allowlist=[], network_access=False,
                            file_write_access=False, sensitive_data_access=False)
        assert p.file_write_access is False


class TestSkillDependencyRecord:
    def test_valid(self):
        d = make_dependency()
        assert d.dependency_id == "dep-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValidationError):
            make_dependency(dependency_id="")

    def test_blank_ref_raises(self):
        with pytest.raises(ValidationError):
            make_dependency(dependency_ref="")

    def test_invalid_type_raises(self):
        with pytest.raises(ValidationError, match="dependency_type must be one of"):
            make_dependency(dependency_type="unknown")

    def test_skill_dependency_type(self):
        d = make_dependency(dependency_type="skill", dependency_ref="skill-verifier-001")
        assert d.dependency_type == "skill"

    def test_provider_dependency_type(self):
        d = make_dependency(dependency_type="provider", dependency_ref="openai")
        assert d.dependency_type == "provider"

    def test_runtime_feature_type(self):
        d = make_dependency(dependency_type="runtime_feature", dependency_ref="file_io")
        assert d.dependency_type == "runtime_feature"

    def test_version_constraint(self):
        d = make_dependency(version_constraint=">=1.0.0")
        assert d.version_constraint == ">=1.0.0"


class TestSkillActivationRule:
    def test_valid(self):
        r = make_rule()
        assert r.rule_id == "rule-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValidationError):
            make_rule(rule_id="")

    def test_with_conditions(self):
        r = make_rule(match_conditions=["task_type == coding", "risk_level == low"])
        assert len(r.match_conditions) == 2

    def test_priority(self):
        r = make_rule(priority=10)
        assert r.priority == 10


class TestSkillActivationRequest:
    def test_valid(self):
        r = make_activation_request()
        assert r.activation_request_id == "ar-001"

    def test_blank_request_id_raises(self):
        with pytest.raises(ValidationError):
            make_activation_request(activation_request_id="")

    def test_blank_skill_id_raises(self):
        with pytest.raises(ValidationError):
            make_activation_request(skill_id="")

    def test_blank_requested_by_raises(self):
        with pytest.raises(ValidationError):
            make_activation_request(requested_by="")

    def test_router_selected(self):
        r = make_activation_request(activation_mode=ActivationMode.ROUTER_SELECTED)
        assert r.activation_mode == ActivationMode.ROUTER_SELECTED


class TestSkillActivationDecision:
    def test_valid(self):
        d = make_activation_decision()
        assert d.decision_id == "dec-001"

    def test_blank_decision_id_raises(self):
        with pytest.raises(ValidationError):
            make_activation_decision(decision_id="")

    def test_blank_request_id_raises(self):
        with pytest.raises(ValidationError):
            make_activation_decision(activation_request_id="")

    def test_blank_reason_raises(self):
        with pytest.raises(ValidationError):
            make_activation_decision(decision_reason="")

    def test_rejected(self):
        d = make_activation_decision(approved=False,
                                     decision_reason="Skill disabled for this runtime")
        assert d.approved is False

    def test_with_policy_checks(self):
        d = make_activation_decision(policy_checks=["permission_profile_valid", "budget_ok"])
        assert len(d.policy_checks) == 2


class TestSkillActivationRecord:
    def test_valid(self):
        r = make_activation_record()
        assert r.activation_id == "act-001"

    def test_blank_activation_id_raises(self):
        with pytest.raises(ValidationError):
            make_activation_record(activation_id="")

    def test_blank_skill_id_raises(self):
        with pytest.raises(ValidationError):
            make_activation_record(skill_id="")

    def test_failed_status_needs_reason(self):
        with pytest.raises(ValidationError, match="FAILED status requires failure_reason"):
            make_activation_record(activation_status=ActivationStatus.FAILED,
                                   failure_reason="")

    def test_failed_with_reason_valid(self):
        r = make_activation_record(activation_status=ActivationStatus.FAILED,
                                   failure_reason="Missing dependency: python3")
        assert r.failure_reason == "Missing dependency: python3"

    def test_executed_with_outputs(self):
        r = make_activation_record(activation_status=ActivationStatus.EXECUTED,
                                   outcome=ActivationOutcome.SUCCESS,
                                   output_refs=["src/generated.py"],
                                   evidence_refs=["test_output/test.log"],
                                   ended_at=NOW)
        assert r.outcome == ActivationOutcome.SUCCESS


class TestSkillEnvelope:
    def test_valid(self):
        e = make_envelope()
        assert e.envelope_id == "env-sk-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="")

    def test_active_skill_without_inputs_outputs_valid(self):
        e = make_envelope(inputs=[], outputs=[])
        assert len(e.inputs) == 0

    def test_executed_without_decision_raises(self):
        with pytest.raises(ValidationError, match="LOADED/EXECUTED status requires a prior approved activation decision"):
            make_envelope(
                activation_request=make_activation_request(),
                activation_record=make_activation_record(
                    activation_status=ActivationStatus.EXECUTED,
                    outcome=ActivationOutcome.SUCCESS,
                ),
            )

    def test_executed_with_approved_decision_valid(self):
        e = make_envelope(
            activation_request=make_activation_request(),
            activation_decision=make_activation_decision(),
            activation_record=make_activation_record(
                activation_status=ActivationStatus.EXECUTED,
                outcome=ActivationOutcome.SUCCESS,
                output_refs=["src/generated.py"],
                ended_at=NOW,
            ),
        )
        assert e.activation_record.activation_status == ActivationStatus.EXECUTED

    def test_decision_mismatch_raises(self):
        with pytest.raises(ValidationError, match="activation_decision.activation_request_id must match"):
            make_envelope(
                activation_request=make_activation_request(activation_request_id="ar-001"),
                activation_decision=make_activation_decision(activation_request_id="ar-999"),
            )

    def test_record_mismatch_raises(self):
        with pytest.raises(ValidationError, match="activation_record.activation_request_id must match"):
            make_envelope(
                activation_request=make_activation_request(activation_request_id="ar-001"),
                activation_decision=make_activation_decision(),
                activation_record=make_activation_record(activation_request_id="ar-999"),
            )

    def test_full_activation_flow(self):
        req = make_activation_request(activation_request_id="ar-flow-001",
                                      request_reason="Match rule: coding task")
        dec = make_activation_decision(activation_request_id="ar-flow-001",
                                       approved=True,
                                       decision_reason="Skill active, permissions ok")
        rec = make_activation_record(activation_request_id="ar-flow-001",
                                     activation_status=ActivationStatus.EXECUTED,
                                     outcome=ActivationOutcome.SUCCESS,
                                     output_refs=["output.py"],
                                     evidence_refs=["test.log"],
                                     started_at=NOW, ended_at=NOW)
        e = make_envelope(activation_request=req, activation_decision=dec,
                          activation_record=rec)
        assert e.activation_decision.approved is True
        assert e.activation_record.outcome == ActivationOutcome.SUCCESS


class TestSerialization:
    def test_manifest_to_dict_and_back(self):
        m = make_manifest()
        data = m.model_dump()
        restored = SkillManifest(**data)
        assert restored.skill_id == m.skill_id

    def test_envelope_to_dict_and_back(self):
        e = make_envelope()
        data = e.model_dump()
        restored = SkillEnvelope(**data)
        assert restored.envelope_id == e.envelope_id

    def test_full_flow_roundtrip(self):
        e = make_envelope(
            activation_request=make_activation_request(),
            activation_decision=make_activation_decision(),
            activation_record=make_activation_record(
                activation_status=ActivationStatus.EXECUTED,
                outcome=ActivationOutcome.SUCCESS,
                output_refs=["src/gen.py"],
                ended_at=NOW,
            ),
        )
        data = e.model_dump()
        restored = SkillEnvelope(**data)
        assert restored.activation_decision.approved is True
        assert restored.activation_record.activation_status == ActivationStatus.EXECUTED


class TestIntegration:
    def test_coding_skill_activated_by_rule(self):
        manifest = SkillManifest(skill_id="skill-code-001", name="Python Coding",
                                 version="2.1.0", skill_type=SkillType.INSTRUCTIONAL,
                                 status=SkillStatus.ACTIVE,
                                 compatible_agent_roles=["coder", "specialist"],
                                 tags=["python", "codegen"],
                                 created_at=NOW, updated_at=NOW)
        inp = SkillInputSpec(input_id="in-code-001", name="specification",
                             type="string", description="Coding task specification")
        out = SkillOutputSpec(output_id="out-code-001", name="source_code",
                              type="string", evidence_required=True)
        perm = SkillPermissionProfile(permission_profile_id="perm-code-001",
                                      tool_allowlist=["read", "write", "execute"])
        rule = SkillActivationRule(rule_id="rule-code-001",
                                   activation_mode=ActivationMode.RULE_BASED,
                                   required_task_types=["coding"],
                                   priority=10)
        req = SkillActivationRequest(activation_request_id="ar-code-001",
                                     skill_id="skill-code-001",
                                     run_id="run-060", step_id="step-030",
                                     task_id="task-gen-001",
                                     requested_by="router",
                                     activation_mode=ActivationMode.RULE_BASED,
                                     request_reason="Rule match: coding task")
        dec = SkillActivationDecision(decision_id="dec-code-001",
                                      activation_request_id="ar-code-001",
                                      approved=True,
                                      decision_reason="Skill active, permissions verified",
                                      applied_rule_ids=["rule-code-001"],
                                      policy_checks=["profile_valid", "budget_ok"])
        rec = SkillActivationRecord(activation_id="act-code-001",
                                    skill_id="skill-code-001",
                                    activation_request_id="ar-code-001",
                                    activation_status=ActivationStatus.EXECUTED,
                                    outcome=ActivationOutcome.SUCCESS,
                                    loaded_instruction_refs=["skills/coding/SKILL.md"],
                                    execution_summary="Generated auth middleware",
                                    output_refs=["src/middleware/auth.py"],
                                    evidence_refs=["test_output/auth_test.log"],
                                    started_at=NOW, ended_at=NOW)
        env = SkillEnvelope(envelope_id="env-sk-int-001", manifest=manifest,
                            inputs=[inp], outputs=[out], permission_profile=perm,
                            activation_rules=[rule],
                            activation_request=req, activation_decision=dec,
                            activation_record=rec)
        assert env.manifest.status == SkillStatus.ACTIVE
        assert env.activation_decision.approved is True
        assert env.activation_record.outcome == ActivationOutcome.SUCCESS

    def test_verification_skill_activated_by_router(self):
        manifest = SkillManifest(skill_id="skill-verifier-001",
                                 name="Security Verifier", version="1.0.0",
                                 skill_type=SkillType.VERIFICATION,
                                 status=SkillStatus.ACTIVE,
                                 tags=["security", "audit"],
                                 created_at=NOW, updated_at=NOW)
        inp = SkillInputSpec(input_id="in-ver-001", name="code_path", type="string")
        out = SkillOutputSpec(output_id="out-ver-001", name="audit_report",
                              type="string", evidence_required=True)
        perm = SkillPermissionProfile(permission_profile_id="perm-ver-001",
                                      tool_allowlist=["read", "static_analysis"],
                                      file_write_access=False)
        rule = SkillActivationRule(rule_id="rule-ver-001",
                                   activation_mode=ActivationMode.ROUTER_SELECTED,
                                   required_context_signals=["high_risk"],
                                   risk_constraints="high")
        req = SkillActivationRequest(activation_request_id="ar-ver-001",
                                     skill_id="skill-verifier-001",
                                     run_id="run-061", step_id="step-031",
                                     requested_by="router",
                                     activation_mode=ActivationMode.ROUTER_SELECTED,
                                     request_reason="Router selected verifier for high-risk task")
        dec = SkillActivationDecision(decision_id="dec-ver-001",
                                      activation_request_id="ar-ver-001",
                                      approved=True,
                                      decision_reason="High-risk task requires verification skill")
        rec = SkillActivationRecord(activation_id="act-ver-001",
                                    skill_id="skill-verifier-001",
                                    activation_request_id="ar-ver-001",
                                    activation_status=ActivationStatus.EXECUTED,
                                    outcome=ActivationOutcome.SUCCESS,
                                    loaded_instruction_refs=["skills/verifier/SKILL.md"],
                                    execution_summary="Security audit complete, no critical issues",
                                    output_refs=["audit/report.md"],
                                    evidence_refs=["scan/semgrep.json", "scan/secrets.txt"],
                                    started_at=NOW, ended_at=NOW)
        env = SkillEnvelope(envelope_id="env-sk-int-002", manifest=manifest,
                            inputs=[inp], outputs=[out], permission_profile=perm,
                            activation_rules=[rule],
                            activation_request=req, activation_decision=dec,
                            activation_record=rec)
        assert env.manifest.skill_type == SkillType.VERIFICATION
        assert env.activation_decision.decision_reason == "High-risk task requires verification skill"

    def test_disabled_skill_rejected_at_activation(self):
        manifest = make_manifest(skill_id="skill-dep-001", status=SkillStatus.DISABLED)
        perm = make_permission(permission_profile_id="perm-dep-001")
        req = SkillActivationRequest(activation_request_id="ar-dep-001",
                                     skill_id="skill-dep-001",
                                     requested_by="router",
                                     activation_mode=ActivationMode.RULE_BASED,
                                     request_reason="Task matched but skill is disabled")
        dec = SkillActivationDecision(decision_id="dec-dep-001",
                                      activation_request_id="ar-dep-001",
                                      approved=False,
                                      decision_reason="Skill is disabled, cannot activate")
        env = SkillEnvelope(envelope_id="env-sk-int-003", manifest=manifest,
                            inputs=[make_input()], outputs=[make_output()],
                            permission_profile=perm,
                            activation_request=req, activation_decision=dec)
        assert env.manifest.status == SkillStatus.DISABLED
        assert env.activation_decision.approved is False

    def test_skill_with_dependency_and_permission_constraints(self):
        manifest = make_manifest(skill_id="skill-data-001", name="Data Transformer",
                                 version="0.5.0", skill_type=SkillType.TRANSFORMATION,
                                 status=SkillStatus.ACTIVE, tags=["data", "etl"])
        inp = make_input(input_id="in-data-001", name="input_data", type="json")
        out = make_output(output_id="out-data-001", name="transformed_data",
                          type="json", evidence_required=True)
        perm = SkillPermissionProfile(permission_profile_id="perm-data-001",
                                      tool_allowlist=["read", "write", "execute"],
                                      network_access=True,
                                      file_write_access=True,
                                      max_budget=10.0)
        dep1 = SkillDependencyRecord(dependency_id="dep-data-001",
                                     dependency_type="tool",
                                     dependency_ref="pandas",
                                     version_constraint=">=2.0.0")
        dep2 = SkillDependencyRecord(dependency_id="dep-data-002",
                                     dependency_type="runtime_feature",
                                     dependency_ref="network_io")
        req = SkillActivationRequest(activation_request_id="ar-data-001",
                                     skill_id="skill-data-001",
                                     requested_by="router",
                                     activation_mode=ActivationMode.RULE_BASED,
                                     request_reason="Data transformation task")
        dec = SkillActivationDecision(decision_id="dec-data-001",
                                      activation_request_id="ar-data-001",
                                      approved=True,
                                      decision_reason="Dependencies satisfied, permission budget within limits",
                                      permission_profile_id="perm-data-001")
        rec = SkillActivationRecord(activation_id="act-data-001",
                                    skill_id="skill-data-001",
                                    activation_request_id="ar-data-001",
                                    activation_status=ActivationStatus.LOADED,
                                    loaded_instruction_refs=["skills/transformer/SKILL.md"],
                                    started_at=NOW)
        env = SkillEnvelope(envelope_id="env-sk-int-004", manifest=manifest,
                            inputs=[inp], outputs=[out], permission_profile=perm,
                            dependencies=[dep1, dep2],
                            activation_request=req, activation_decision=dec,
                            activation_record=rec)
        assert len(env.dependencies) == 2
        assert env.permission_profile.max_budget == 10.0
        assert env.activation_record.activation_status == ActivationStatus.LOADED

    def test_successful_activation_with_outputs_and_evidence(self):
        manifest = make_manifest(skill_id="skill-test-001", name="Test Runner",
                                 version="3.0.0", skill_type=SkillType.TOOLING,
                                 status=SkillStatus.ACTIVE)
        inp = make_input(input_id="in-test-001", name="test_path", type="string")
        out = make_output(output_id="out-test-001", name="test_results",
                          type="json", evidence_required=True)
        perm = make_permission(permission_profile_id="perm-test-001",
                               tool_allowlist=["read", "execute"])
        req = SkillActivationRequest(activation_request_id="ar-test-001",
                                     skill_id="skill-test-001",
                                     run_id="run-062", step_id="step-032",
                                     requested_by="step_lifecycle",
                                     activation_mode=ActivationMode.RULE_BASED,
                                     request_reason="Post-coding verification step")
        dec = SkillActivationDecision(decision_id="dec-test-001",
                                      activation_request_id="ar-test-001",
                                      approved=True,
                                      decision_reason="Rule match: verification after coding",
                                      applied_rule_ids=["rule-verify-after-code"],
                                      policy_checks=["no_network_required", "budget_ok"])
        rec = SkillActivationRecord(activation_id="act-test-001",
                                    skill_id="skill-test-001",
                                    activation_request_id="ar-test-001",
                                    activation_status=ActivationStatus.EXECUTED,
                                    outcome=ActivationOutcome.SUCCESS,
                                    loaded_instruction_refs=["skills/tester/SKILL.md"],
                                    execution_summary="Ran 142 tests, all passing",
                                    output_refs=["test_output/results.json"],
                                    evidence_refs=["test_output/coverage.xml",
                                                   "test_output/pytest.log"],
                                    started_at=NOW, ended_at=NOW)
        env = SkillEnvelope(envelope_id="env-sk-int-005", manifest=manifest,
                            inputs=[inp], outputs=[out], permission_profile=perm,
                            activation_request=req, activation_decision=dec,
                            activation_record=rec)
        assert env.activation_record.outcome == ActivationOutcome.SUCCESS
        assert len(env.activation_record.evidence_refs) == 2
        assert env.activation_decision.approved is True
