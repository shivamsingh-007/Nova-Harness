import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from models.hook_lifecycle_contract import (
    HookPointType, HookExecutionMode, HookEffectType, HookResultStatus, HookFailurePolicy,
    HookPointSpec, HookHandlerManifest, HookContextEnvelope, HookMutationProposal,
    HookResultRecord, HookChainExecutionRecord, HookRegistrationRecord, HookLifecycleEnvelope,
)


NOW = datetime.now(timezone.utc)


def make_hook_point(**overrides) -> HookPointSpec:
    defaults = dict(hook_point_id="hp-001", hook_point_type=HookPointType.PRE_TOOL_CALL,
                    description="Before tool invocation",
                    allowed_effects=[HookEffectType.OBSERVE, HookEffectType.BLOCK])
    defaults.update(overrides)
    return HookPointSpec(**defaults)


def make_handler(**overrides) -> HookHandlerManifest:
    defaults = dict(handler_id="h-001", name="Policy Checker",
                    version="1.0.0", hook_point_type=HookPointType.PRE_TOOL_CALL,
                    effect_type=HookEffectType.BLOCK, enabled=True,
                    failure_policy=HookFailurePolicy.FAIL_CLOSED)
    defaults.update(overrides)
    return HookHandlerManifest(**defaults)


def make_context(**overrides) -> HookContextEnvelope:
    defaults = dict(context_id="ctx-001", run_id="run-001", step_id="step-001",
                    event_ref="pre_tool_call",
                    input_refs=["specs/api.md"])
    defaults.update(overrides)
    return HookContextEnvelope(**defaults)


def make_proposal(**overrides) -> HookMutationProposal:
    defaults = dict(proposal_id="prop-001", handler_id="h-001",
                    target_field="tool_args.timeout",
                    proposed_value_ref="30000", reason="Increase timeout for DB call")
    defaults.update(overrides)
    return HookMutationProposal(**defaults)


def make_result(**overrides) -> HookResultRecord:
    defaults = dict(result_id="res-001", handler_id="h-001",
                    hook_point_type=HookPointType.PRE_TOOL_CALL,
                    status=HookResultStatus.PASS_THROUGH,
                    effect_type=HookEffectType.OBSERVE,
                    started_at=NOW)
    defaults.update(overrides)
    return HookResultRecord(**defaults)


def make_chain(**overrides) -> HookChainExecutionRecord:
    defaults = dict(chain_id="chain-001", hook_point_type=HookPointType.PRE_TOOL_CALL,
                    registered_handler_ids=["h-001", "h-002"],
                    executed_handler_ids=["h-001", "h-002"],
                    execution_order=["h-001", "h-002"])
    defaults.update(overrides)
    return HookChainExecutionRecord(**defaults)


def make_registration(**overrides) -> HookRegistrationRecord:
    defaults = dict(registration_id="reg-001", handler_id="h-001",
                    hook_point_type=HookPointType.PRE_TOOL_CALL,
                    registered_at=NOW)
    defaults.update(overrides)
    return HookRegistrationRecord(**defaults)


def make_envelope(**overrides) -> HookLifecycleEnvelope:
    defaults = dict(envelope_id="env-hk-001",
                    hook_point=make_hook_point())
    defaults.update(overrides)
    return HookLifecycleEnvelope(**defaults)


class TestEnums:
    def test_hook_point_type(self):
        assert HookPointType.PRE_LOOP.value == "pre_loop"
        assert HookPointType.POST_ARTIFACT_UPDATE.value == "post_artifact_update"
        assert len(HookPointType) == 18

    def test_hook_execution_mode(self):
        assert HookExecutionMode.FIRST_MATCH.value == "first_match"
        assert len(HookExecutionMode) == 5

    def test_hook_effect_type(self):
        assert HookEffectType.REQUEST_ESCALATION.value == "request_escalation"
        assert len(HookEffectType) == 6

    def test_hook_result_status(self):
        assert HookResultStatus.PASS_THROUGH.value == "pass_through"
        assert HookResultStatus.SKIPPED.value == "skipped"
        assert len(HookResultStatus) == 5

    def test_hook_failure_policy(self):
        assert HookFailurePolicy.LOG_AND_CONTINUE.value == "log_and_continue"
        assert len(HookFailurePolicy) == 4


class TestHookPointSpec:
    def test_valid(self):
        p = make_hook_point()
        assert p.hook_point_id == "hp-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValidationError):
            make_hook_point(hook_point_id="")

    def test_pre_step(self):
        p = make_hook_point(hook_point_type=HookPointType.PRE_STEP)
        assert p.hook_point_type == HookPointType.PRE_STEP

    def test_on_failure(self):
        p = make_hook_point(hook_point_type=HookPointType.ON_FAILURE)
        assert p.hook_point_type == HookPointType.ON_FAILURE

    def test_execution_mode(self):
        p = make_hook_point(execution_mode=HookExecutionMode.ORDERED_CHAIN)
        assert p.execution_mode == HookExecutionMode.ORDERED_CHAIN


class TestHookHandlerManifest:
    def test_valid(self):
        h = make_handler()
        assert h.handler_id == "h-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValidationError):
            make_handler(handler_id="")

    def test_observe_effect(self):
        h = make_handler(effect_type=HookEffectType.OBSERVE)
        assert h.effect_type == HookEffectType.OBSERVE

    def test_disabled(self):
        h = make_handler(enabled=False)
        assert h.enabled is False

    def test_tags(self):
        h = make_handler(tags=["policy", "security"])
        assert len(h.tags) == 2


class TestHookContextEnvelope:
    def test_valid(self):
        c = make_context()
        assert c.context_id == "ctx-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValidationError):
            make_context(context_id="")

    def test_sensitive_context(self):
        c = make_context(sensitive=True, read_only_fields=["config.secret"])
        assert c.sensitive is True

    def test_sensitive_no_restrictions_valid(self):
        c = make_context(sensitive=True)
        assert c.sensitive is True

    def test_with_artifact_refs(self):
        c = make_context(artifact_refs=["src/main.py"])
        assert len(c.artifact_refs) == 1


class TestHookMutationProposal:
    def test_valid(self):
        p = make_proposal()
        assert p.proposal_id == "prop-001"

    def test_blank_proposal_id_raises(self):
        with pytest.raises(ValidationError):
            make_proposal(proposal_id="")

    def test_blank_handler_id_raises(self):
        with pytest.raises(ValidationError):
            make_proposal(handler_id="")

    def test_blank_target_field_raises(self):
        with pytest.raises(ValidationError):
            make_proposal(target_field="")

    def test_requires_approval(self):
        p = make_proposal(requires_approval=True)
        assert p.requires_approval is True

    def test_not_safe(self):
        p = make_proposal(safe_to_apply=False)
        assert p.safe_to_apply is False


class TestHookResultRecord:
    def test_valid(self):
        r = make_result()
        assert r.result_id == "res-001"

    def test_blank_result_id_raises(self):
        with pytest.raises(ValidationError):
            make_result(result_id="")

    def test_blank_handler_id_raises(self):
        with pytest.raises(ValidationError):
            make_result(handler_id="")

    def test_modify_effect_needs_proposals(self):
        with pytest.raises(ValidationError, match="MODIFY effect requires at least one mutation proposal"):
            make_result(effect_type=HookEffectType.MODIFY)

    def test_modify_with_proposals_valid(self):
        r = make_result(effect_type=HookEffectType.MODIFY,
                        status=HookResultStatus.MODIFIED,
                        mutation_proposals=[make_proposal()])
        assert len(r.mutation_proposals) == 1

    def test_blocked_status_needs_reason(self):
        with pytest.raises(ValidationError, match="BLOCKED status requires block_reason"):
            make_result(status=HookResultStatus.BLOCKED,
                        effect_type=HookEffectType.BLOCK, block_reason="")

    def test_blocked_with_reason_valid(self):
        r = make_result(status=HookResultStatus.BLOCKED,
                        effect_type=HookEffectType.BLOCK,
                        block_reason="Tool not allowed by policy")
        assert r.block_reason == "Tool not allowed by policy"

    def test_escalation_requested(self):
        r = make_result(escalation_requested=True)
        assert r.escalation_requested is True

    def test_with_emitted_events(self):
        r = make_result(emitted_event_refs=["evt-policy-block-001"])
        assert r.emitted_event_refs[0] == "evt-policy-block-001"

    def test_ended_at(self):
        r = make_result(started_at=NOW, ended_at=NOW)
        assert r.ended_at is not None


class TestHookChainExecutionRecord:
    def test_valid(self):
        c = make_chain()
        assert c.chain_id == "chain-001"

    def test_blank_chain_id_raises(self):
        with pytest.raises(ValidationError):
            make_chain(chain_id="")

    def test_stopped_by_handler(self):
        c = make_chain(stopped_by_handler_id="h-001",
                       chain_status="stopped")
        assert c.stopped_by_handler_id == "h-001"

    def test_final_effect(self):
        c = make_chain(final_effect=HookEffectType.BLOCK)
        assert c.final_effect == HookEffectType.BLOCK


class TestHookRegistrationRecord:
    def test_valid(self):
        r = make_registration()
        assert r.registration_id == "reg-001"

    def test_blank_registration_id_raises(self):
        with pytest.raises(ValidationError):
            make_registration(registration_id="")

    def test_blank_handler_id_raises(self):
        with pytest.raises(ValidationError):
            make_registration(handler_id="")

    def test_scope(self):
        r = make_registration(registration_scope="global")
        assert r.registration_scope == "global"


class TestHookLifecycleEnvelope:
    def test_valid(self):
        e = make_envelope()
        assert e.envelope_id == "env-hk-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="")

    def test_with_handler(self):
        e = make_envelope(handler_manifest=make_handler())
        assert e.handler_manifest.handler_id == "h-001"

    def test_with_context_and_result(self):
        e = make_envelope(context=make_context(),
                          result=make_result())
        assert e.context.context_id == "ctx-001"
        assert e.result.result_id == "res-001"

    def test_with_chain(self):
        e = make_envelope(chain_execution=make_chain())
        assert e.chain_execution.chain_id == "chain-001"

    def test_with_registration(self):
        e = make_envelope(registration=make_registration())
        assert e.registration.registration_id == "reg-001"


class TestSerialization:
    def test_hook_point_to_dict_and_back(self):
        p = make_hook_point()
        data = p.model_dump()
        restored = HookPointSpec(**data)
        assert restored.hook_point_id == p.hook_point_id

    def test_envelope_to_dict_and_back(self):
        e = make_envelope()
        data = e.model_dump()
        restored = HookLifecycleEnvelope(**data)
        assert restored.envelope_id == e.envelope_id

    def test_full_envelope_roundtrip(self):
        e = make_envelope(
            handler_manifest=make_handler(),
            context=make_context(),
            result=make_result(),
            chain_execution=make_chain(),
            registration=make_registration(),
        )
        data = e.model_dump()
        restored = HookLifecycleEnvelope(**data)
        assert restored.handler_manifest.handler_id == "h-001"
        assert restored.chain_execution.chain_id == "chain-001"
        assert restored.registration.registration_id == "reg-001"


class TestIntegration:
    def test_pre_tool_call_policy_hook_blocks_unsafe_call(self):
        hp = HookPointSpec(hook_point_id="hp-int-001",
                           hook_point_type=HookPointType.PRE_TOOL_CALL,
                           allowed_effects=[HookEffectType.OBSERVE, HookEffectType.BLOCK])
        handler = HookHandlerManifest(handler_id="h-int-001", name="Policy Enforcer",
                                      version="1.0.0",
                                      hook_point_type=HookPointType.PRE_TOOL_CALL,
                                      effect_type=HookEffectType.BLOCK,
                                      failure_policy=HookFailurePolicy.FAIL_CLOSED)
        ctx = HookContextEnvelope(context_id="ctx-int-001", run_id="run-080",
                                  step_id="step-050", event_ref="pre_tool_call",
                                  input_refs=["tools/delete_prod.sh"])
        result = HookResultRecord(result_id="res-int-001", handler_id="h-int-001",
                                  hook_point_type=HookPointType.PRE_TOOL_CALL,
                                  status=HookResultStatus.BLOCKED,
                                  effect_type=HookEffectType.BLOCK,
                                  block_reason="Delete tool blocked by policy: production safety",
                                  mutation_proposals=[],
                                  started_at=NOW, ended_at=NOW)
        env = HookLifecycleEnvelope(envelope_id="env-hk-int-001", hook_point=hp,
                                    handler_manifest=handler, context=ctx, result=result)
        assert env.result.status == HookResultStatus.BLOCKED
        assert "production safety" in env.result.block_reason

    def test_post_tool_call_hook_annotates_result(self):
        hp = HookPointSpec(hook_point_id="hp-int-002",
                           hook_point_type=HookPointType.POST_TOOL_CALL,
                           allowed_effects=[HookEffectType.ANNOTATE])
        handler = HookHandlerManifest(handler_id="h-int-002", name="Result Annotator",
                                      version="1.0.0",
                                      hook_point_type=HookPointType.POST_TOOL_CALL,
                                      effect_type=HookEffectType.ANNOTATE)
        ctx = HookContextEnvelope(context_id="ctx-int-002", run_id="run-081",
                                  step_id="step-051", event_ref="post_tool_call")
        result = HookResultRecord(result_id="res-int-002", handler_id="h-int-002",
                                  hook_point_type=HookPointType.POST_TOOL_CALL,
                                  status=HookResultStatus.PASS_THROUGH,
                                  effect_type=HookEffectType.ANNOTATE,
                                  message="Tool completed in 2.3s. Result size: 14KB.",
                                  emitted_event_refs=["evt-timing-001"],
                                  started_at=NOW, ended_at=NOW)
        env = HookLifecycleEnvelope(envelope_id="env-hk-int-002", hook_point=hp,
                                    handler_manifest=handler, context=ctx, result=result)
        assert env.result.effect_type == HookEffectType.ANNOTATE
        assert "2.3s" in env.result.message

    def test_pre_verify_hook_proposes_additional_checks(self):
        hp = HookPointSpec(hook_point_id="hp-int-003",
                           hook_point_type=HookPointType.PRE_VERIFY,
                           allowed_effects=[HookEffectType.MODIFY, HookEffectType.OBSERVE])
        handler = HookHandlerManifest(handler_id="h-int-003", name="Coverage Enforcer",
                                      version="2.0.0",
                                      hook_point_type=HookPointType.PRE_VERIFY,
                                      effect_type=HookEffectType.MODIFY)
        ctx = HookContextEnvelope(context_id="ctx-int-003", run_id="run-082",
                                  step_id="step-052", event_ref="pre_verify",
                                  artifact_refs=["src/main.py"])
        prop = HookMutationProposal(proposal_id="prop-int-001", handler_id="h-int-003",
                                    target_field="verification.additional_checks",
                                    proposed_value_ref="['coverage > 80%', 'lint_score >= 9']",
                                    reason="Ensure code quality before acceptance")
        result = HookResultRecord(result_id="res-int-003", handler_id="h-int-003",
                                  hook_point_type=HookPointType.PRE_VERIFY,
                                  status=HookResultStatus.MODIFIED,
                                  effect_type=HookEffectType.MODIFY,
                                  mutation_proposals=[prop],
                                  started_at=NOW, ended_at=NOW)
        env = HookLifecycleEnvelope(envelope_id="env-hk-int-003", hook_point=hp,
                                    handler_manifest=handler, context=ctx, result=result)
        assert env.result.status == HookResultStatus.MODIFIED
        assert env.result.mutation_proposals[0].target_field == "verification.additional_checks"

    def test_on_failure_hook_emits_recovery_event(self):
        hp = HookPointSpec(hook_point_id="hp-int-004",
                           hook_point_type=HookPointType.ON_FAILURE,
                           allowed_effects=[HookEffectType.EMIT_EVENT, HookEffectType.REQUEST_ESCALATION])
        handler = HookHandlerManifest(handler_id="h-int-004", name="Failure Observer",
                                      version="1.0.0",
                                      hook_point_type=HookPointType.ON_FAILURE,
                                      effect_type=HookEffectType.EMIT_EVENT)
        ctx = HookContextEnvelope(context_id="ctx-int-004", run_id="run-083",
                                  step_id="step-053", event_ref="on_failure",
                                  state_snapshot_refs=["state/failure-083.json"])
        result = HookResultRecord(result_id="res-int-004", handler_id="h-int-004",
                                  hook_point_type=HookPointType.ON_FAILURE,
                                  status=HookResultStatus.PASS_THROUGH,
                                  effect_type=HookEffectType.EMIT_EVENT,
                                  message="Tool call failed: timeout exceeded",
                                  emitted_event_refs=["evt-recovery-001"],
                                  escalation_requested=True,
                                  started_at=NOW, ended_at=NOW)
        env = HookLifecycleEnvelope(envelope_id="env-hk-int-004", hook_point=hp,
                                    handler_manifest=handler, context=ctx, result=result)
        assert env.result.emitted_event_refs[0] == "evt-recovery-001"
        assert env.result.escalation_requested is True

    def test_ordered_chain_with_modify_and_pass_through(self):
        hp = HookPointSpec(hook_point_id="hp-int-005",
                           hook_point_type=HookPointType.PRE_PLAN,
                           allowed_effects=[HookEffectType.MODIFY, HookEffectType.OBSERVE],
                           execution_mode=HookExecutionMode.ORDERED_CHAIN)
        h1 = HookHandlerManifest(handler_id="h-int-005a", name="Context Enricher",
                                 version="1.0.0",
                                 hook_point_type=HookPointType.PRE_PLAN,
                                 effect_type=HookEffectType.MODIFY, priority=10)
        h2 = HookHandlerManifest(handler_id="h-int-005b", name="Audit Logger",
                                 version="1.0.0",
                                 hook_point_type=HookPointType.PRE_PLAN,
                                 effect_type=HookEffectType.OBSERVE, priority=20)
        ctx = HookContextEnvelope(context_id="ctx-int-005", run_id="run-084",
                                  step_id="step-054", event_ref="pre_plan")
        prop = HookMutationProposal(proposal_id="prop-int-002", handler_id="h-int-005a",
                                    target_field="plan.context_refs",
                                    proposed_value_ref="['specs/auth.md', 'docs/api.md']",
                                    reason="Enrich plan context")
        res1 = HookResultRecord(result_id="res-int-005a", handler_id="h-int-005a",
                                hook_point_type=HookPointType.PRE_PLAN,
                                status=HookResultStatus.MODIFIED,
                                effect_type=HookEffectType.MODIFY,
                                mutation_proposals=[prop],
                                started_at=NOW, ended_at=NOW)
        res2 = HookResultRecord(result_id="res-int-005b", handler_id="h-int-005b",
                                hook_point_type=HookPointType.PRE_PLAN,
                                status=HookResultStatus.PASS_THROUGH,
                                effect_type=HookEffectType.OBSERVE,
                                message="Plan context enriched by h-int-005a",
                                started_at=NOW, ended_at=NOW)
        chain = HookChainExecutionRecord(chain_id="chain-int-001",
                                         hook_point_type=HookPointType.PRE_PLAN,
                                         registered_handler_ids=["h-int-005a", "h-int-005b"],
                                         executed_handler_ids=["h-int-005a", "h-int-005b"],
                                         execution_order=["h-int-005a", "h-int-005b"],
                                         chain_status="completed",
                                         final_effect=HookEffectType.MODIFY)
        env1 = HookLifecycleEnvelope(envelope_id="env-hk-int-005a", hook_point=hp,
                                     handler_manifest=h1, context=ctx, result=res1,
                                     chain_execution=chain)
        env2 = HookLifecycleEnvelope(envelope_id="env-hk-int-005b", hook_point=hp,
                                     handler_manifest=h2, context=ctx, result=res2,
                                     chain_execution=chain)
        assert env1.chain_execution.execution_order == ["h-int-005a", "h-int-005b"]
        assert env1.result.status == HookResultStatus.MODIFIED
        assert env2.result.status == HookResultStatus.PASS_THROUGH
