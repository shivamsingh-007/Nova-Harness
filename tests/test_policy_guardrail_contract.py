import pytest
from pydantic import ValidationError
from models.policy_guardrail_contract import (
    EvaluationTargetType,
    PolicyDecisionType,
    FindingSeverity,
    RiskLevel,
    ObligationType,
    PolicyRef,
    EvidenceSignal,
    GuardrailFinding,
    DecisionObligation,
    PolicyEvaluation,
    GuardrailDecisionEnvelope,
)


class TestEnums:
    def test_evaluation_target_type_values(self):
        assert EvaluationTargetType.PROMPT.value == "prompt"
        assert EvaluationTargetType.TOOL_INVOCATION.value == "tool_invocation"
        assert EvaluationTargetType.MEMORY_ACCESS.value == "memory_access"
        assert EvaluationTargetType.MODEL_OUTPUT.value == "model_output"
        assert EvaluationTargetType.WORKFLOW_STEP.value == "workflow_step"

    def test_policy_decision_type_values(self):
        assert PolicyDecisionType.ALLOW.value == "allow"
        assert PolicyDecisionType.DENY.value == "deny"
        assert PolicyDecisionType.MODIFY.value == "modify"
        assert PolicyDecisionType.REVIEW.value == "review"
        assert PolicyDecisionType.QUARANTINE.value == "quarantine"
        assert PolicyDecisionType.DEFER.value == "defer"

    def test_finding_severity_values(self):
        assert FindingSeverity.INFO.value == "info"
        assert FindingSeverity.LOW.value == "low"
        assert FindingSeverity.MODERATE.value == "moderate"
        assert FindingSeverity.HIGH.value == "high"
        assert FindingSeverity.CRITICAL.value == "critical"

    def test_risk_level_values(self):
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MODERATE.value == "moderate"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_obligation_type_values(self):
        assert ObligationType.REQUIRE_APPROVAL.value == "require_approval"
        assert ObligationType.MASK_CONTENT.value == "mask_content"
        assert ObligationType.REDUCE_SCOPE.value == "reduce_scope"
        assert ObligationType.DOWNGRADE_TOOL.value == "downgrade_tool"
        assert ObligationType.RETRY_WITH_CONSTRAINTS.value == "retry_with_constraints"
        assert ObligationType.LOG_ONLY.value == "log_only"


class TestPolicyRef:
    def test_valid(self):
        pr = PolicyRef(policy_id="pol-1", policy_name="data_egress")
        assert pr.policy_id == "pol-1"
        assert pr.policy_name == "data_egress"
        assert pr.policy_version is None

    def test_valid_with_version(self):
        pr = PolicyRef(policy_id="pol-2", policy_name="code_exec", policy_version="1.3.0")
        assert pr.policy_version == "1.3.0"

    def test_empty_policy_id_raises(self):
        with pytest.raises(ValueError):
            PolicyRef(policy_id="", policy_name="data_egress")

    def test_empty_policy_name_raises(self):
        with pytest.raises(ValueError):
            PolicyRef(policy_id="pol-3", policy_name="  ")


class TestEvidenceSignal:
    def test_valid_minimal(self):
        sig = EvidenceSignal(
            signal_id="sig-1", signal_type="regex_match",
            source_ref="guardrail:content_filter", summary="Matched PII pattern",
        )
        assert sig.confidence is None

    def test_valid_with_confidence(self):
        sig = EvidenceSignal(
            signal_id="sig-2", signal_type="classifier",
            source_ref="model:safety-v2", summary="Toxicity score 0.92",
            confidence=0.92,
        )
        assert sig.confidence == 0.92

    def test_empty_signal_id_raises(self):
        with pytest.raises(ValueError):
            EvidenceSignal(
                signal_id="", signal_type="regex", source_ref="g",
                summary="test",
            )

    def test_empty_signal_type_raises(self):
        with pytest.raises(ValueError):
            EvidenceSignal(
                signal_id="sig-3", signal_type="", source_ref="g",
                summary="test",
            )

    def test_empty_source_ref_raises(self):
        with pytest.raises(ValueError):
            EvidenceSignal(
                signal_id="sig-4", signal_type="regex", source_ref="",
                summary="test",
            )

    def test_empty_summary_raises(self):
        with pytest.raises(ValueError):
            EvidenceSignal(
                signal_id="sig-5", signal_type="regex", source_ref="g",
                summary="",
            )

    def test_confidence_above_one_raises(self):
        with pytest.raises(ValueError):
            EvidenceSignal(
                signal_id="sig-6", signal_type="classifier",
                source_ref="model:v1", summary="test",
                confidence=1.5,
            )

    def test_confidence_below_zero_raises(self):
        with pytest.raises(ValueError):
            EvidenceSignal(
                signal_id="sig-7", signal_type="classifier",
                source_ref="model:v1", summary="test",
                confidence=-0.1,
            )

    def test_confidence_at_boundaries(self):
        sig = EvidenceSignal(
            signal_id="sig-8", signal_type="classifier",
            source_ref="model:v1", summary="test",
            confidence=0.0,
        )
        assert sig.confidence == 0.0
        sig = EvidenceSignal(
            signal_id="sig-9", signal_type="classifier",
            source_ref="model:v1", summary="test",
            confidence=1.0,
        )
        assert sig.confidence == 1.0


class TestGuardrailFinding:
    def test_valid_info(self):
        f = GuardrailFinding(
            finding_id="f-1", severity=FindingSeverity.INFO,
            category="content_policy", summary="No issues detected",
        )
        assert f.severity == FindingSeverity.INFO

    def test_high_requires_signals(self):
        with pytest.raises(ValueError):
            GuardrailFinding(
                finding_id="f-2", severity=FindingSeverity.HIGH,
                category="safety", summary="Toxicity detected",
            )

    def test_critical_requires_signals(self):
        with pytest.raises(ValueError):
            GuardrailFinding(
                finding_id="f-3", severity=FindingSeverity.CRITICAL,
                category="security", summary="Credential leak",
            )

    def test_high_with_signals_ok(self):
        sig = EvidenceSignal(
            signal_id="sig-h", signal_type="classifier",
            source_ref="safety:v2", summary="Toxicity 0.88",
            confidence=0.88,
        )
        f = GuardrailFinding(
            finding_id="f-4", severity=FindingSeverity.HIGH,
            category="safety", summary="Toxicity detected",
            evidence_signals=[sig],
        )
        assert len(f.evidence_signals) == 1

    def test_empty_finding_id_raises(self):
        with pytest.raises(ValueError):
            GuardrailFinding(
                finding_id="", severity=FindingSeverity.LOW,
                category="test", summary="x",
            )

    def test_empty_category_raises(self):
        with pytest.raises(ValueError):
            GuardrailFinding(
                finding_id="f-5", severity=FindingSeverity.LOW,
                category="", summary="x",
            )

    def test_empty_summary_raises(self):
        with pytest.raises(ValueError):
            GuardrailFinding(
                finding_id="f-6", severity=FindingSeverity.LOW,
                category="test", summary="",
            )


class TestDecisionObligation:
    def test_valid_minimal(self):
        ob = DecisionObligation(obligation_type=ObligationType.LOG_ONLY)
        assert ob.parameters == []

    def test_valid_with_parameters(self):
        ob = DecisionObligation(
            obligation_type=ObligationType.MASK_CONTENT,
            parameters=["email", "phone"],
        )
        assert "email" in ob.parameters


class TestPolicyEvaluation:
    def test_valid_minimal(self):
        policy = PolicyRef(policy_id="pol-1", policy_name="content_safety")
        ev = PolicyEvaluation(
            evaluation_id="eval-1", target_type=EvaluationTargetType.PROMPT,
            target_ref="prompt://sess-1/msg-3", policy=policy,
            risk_level=RiskLevel.LOW, rationale="No violations detected",
        )
        assert ev.findings == []
        assert ev.risk_level == RiskLevel.LOW

    def test_valid_with_findings(self):
        sig = EvidenceSignal(
            signal_id="sig-1", signal_type="regex",
            source_ref="guardrail:pii", summary="Matched email pattern",
            confidence=0.95,
        )
        finding = GuardrailFinding(
            finding_id="f-1", severity=FindingSeverity.MODERATE,
            category="pii_detection", summary="Email address found in prompt",
            evidence_signals=[sig],
        )
        policy = PolicyRef(policy_id="pol-2", policy_name="pii_policy", policy_version="2.0")
        ev = PolicyEvaluation(
            evaluation_id="eval-2", target_type=EvaluationTargetType.MEMORY_ACCESS,
            target_ref="memory://mem-042", policy=policy,
            findings=[finding], risk_level=RiskLevel.MODERATE,
            rationale="PII detected in memory access; needs masking",
        )
        assert len(ev.findings) == 1

    def test_empty_evaluation_id_raises(self):
        policy = PolicyRef(policy_id="pol-1", policy_name="test")
        with pytest.raises(ValueError):
            PolicyEvaluation(
                evaluation_id="", target_type=EvaluationTargetType.PROMPT,
                target_ref="t", policy=policy,
                risk_level=RiskLevel.LOW, rationale="x",
            )

    def test_empty_target_ref_raises(self):
        policy = PolicyRef(policy_id="pol-1", policy_name="test")
        with pytest.raises(ValueError):
            PolicyEvaluation(
                evaluation_id="eval-3", target_type=EvaluationTargetType.PROMPT,
                target_ref="", policy=policy,
                risk_level=RiskLevel.LOW, rationale="x",
            )

    def test_empty_rationale_raises(self):
        policy = PolicyRef(policy_id="pol-1", policy_name="test")
        with pytest.raises(ValueError):
            PolicyEvaluation(
                evaluation_id="eval-4", target_type=EvaluationTargetType.PROMPT,
                target_ref="t", policy=policy,
                risk_level=RiskLevel.LOW, rationale="",
            )


class TestGuardrailDecisionEnvelope:
    def test_allow(self):
        policy = PolicyRef(policy_id="pol-1", policy_name="data_egress")
        ev = PolicyEvaluation(
            evaluation_id="eval-1", target_type=EvaluationTargetType.TOOL_INVOCATION,
            target_ref="tool://td-search/read", policy=policy,
            risk_level=RiskLevel.LOW, rationale="Safe tool call",
        )
        env = GuardrailDecisionEnvelope(
            decision_id="dec-1", evaluation=ev,
            decision=PolicyDecisionType.ALLOW, execution_allowed=True,
            decided_by="guardrail:runtime-v1",
        )
        assert env.execution_allowed is True
        assert env.decision == PolicyDecisionType.ALLOW

    def test_deny_sets_execution_allowed_false(self):
        policy = PolicyRef(policy_id="pol-2", policy_name="safety")
        ev = PolicyEvaluation(
            evaluation_id="eval-2", target_type=EvaluationTargetType.TOOL_INVOCATION,
            target_ref="tool://td-storage/delete", policy=policy,
            risk_level=RiskLevel.HIGH, rationale="High-risk delete blocked",
        )
        env = GuardrailDecisionEnvelope(
            decision_id="dec-2", evaluation=ev,
            decision=PolicyDecisionType.DENY, execution_allowed=False,
            decided_by="guardrail:runtime-v1",
        )
        assert env.execution_allowed is False

    def test_deny_with_execution_allowed_true_raises(self):
        policy = PolicyRef(policy_id="pol-1", policy_name="test")
        ev = PolicyEvaluation(
            evaluation_id="eval-3", target_type=EvaluationTargetType.MODEL_OUTPUT,
            target_ref="output://run-1", policy=policy,
            risk_level=RiskLevel.LOW, rationale="test",
        )
        with pytest.raises(ValueError):
            GuardrailDecisionEnvelope(
                decision_id="dec-3", evaluation=ev,
                decision=PolicyDecisionType.DENY, execution_allowed=True,
                decided_by="guardrail:v1",
            )

    def test_quarantine_with_execution_allowed_true_raises(self):
        policy = PolicyRef(policy_id="pol-1", policy_name="test")
        ev = PolicyEvaluation(
            evaluation_id="eval-4", target_type=EvaluationTargetType.MEMORY_ACCESS,
            target_ref="memory://mem-1", policy=policy,
            risk_level=RiskLevel.LOW, rationale="test",
        )
        with pytest.raises(ValueError):
            GuardrailDecisionEnvelope(
                decision_id="dec-4", evaluation=ev,
                decision=PolicyDecisionType.QUARANTINE, execution_allowed=True,
                decided_by="guardrail:v1",
            )

    def test_review_allows_true(self):
        policy = PolicyRef(policy_id="pol-1", policy_name="test")
        ev = PolicyEvaluation(
            evaluation_id="eval-5", target_type=EvaluationTargetType.WORKFLOW_STEP,
            target_ref="step://build", policy=policy,
            risk_level=RiskLevel.LOW, rationale="Needs human review",
        )
        env = GuardrailDecisionEnvelope(
            decision_id="dec-5", evaluation=ev,
            decision=PolicyDecisionType.REVIEW, execution_allowed=True,
            decided_by="guardrail:v1",
        )
        assert env.execution_allowed is True

    def test_modify_allows_true(self):
        policy = PolicyRef(policy_id="pol-1", policy_name="test")
        ev = PolicyEvaluation(
            evaluation_id="eval-6", target_type=EvaluationTargetType.MODEL_OUTPUT,
            target_ref="output://run-2", policy=policy,
            risk_level=RiskLevel.LOW, rationale="Content needs masking",
        )
        env = GuardrailDecisionEnvelope(
            decision_id="dec-6", evaluation=ev,
            decision=PolicyDecisionType.MODIFY, execution_allowed=True,
            obligations=[DecisionObligation(
                obligation_type=ObligationType.MASK_CONTENT,
                parameters=["email"],
            )],
            decided_by="guardrail:v1",
        )
        assert env.execution_allowed is True

    def test_defer_allows_false(self):
        policy = PolicyRef(policy_id="pol-1", policy_name="test")
        ev = PolicyEvaluation(
            evaluation_id="eval-7", target_type=EvaluationTargetType.MEMORY_ACCESS,
            target_ref="memory://mem-2", policy=policy,
            risk_level=RiskLevel.LOW, rationale="Deferring decision",
        )
        env = GuardrailDecisionEnvelope(
            decision_id="dec-7", evaluation=ev,
            decision=PolicyDecisionType.DEFER, execution_allowed=False,
            decided_by="guardrail:v1",
        )
        assert env.execution_allowed is False

    def test_empty_decision_id_raises(self):
        policy = PolicyRef(policy_id="pol-1", policy_name="test")
        ev = PolicyEvaluation(
            evaluation_id="eval-8", target_type=EvaluationTargetType.PROMPT,
            target_ref="t", policy=policy,
            risk_level=RiskLevel.LOW, rationale="x",
        )
        with pytest.raises(ValueError):
            GuardrailDecisionEnvelope(
                decision_id="", evaluation=ev,
                decision=PolicyDecisionType.ALLOW, execution_allowed=True,
                decided_by="guardrail:v1",
            )

    def test_empty_decided_by_raises(self):
        policy = PolicyRef(policy_id="pol-1", policy_name="test")
        ev = PolicyEvaluation(
            evaluation_id="eval-9", target_type=EvaluationTargetType.PROMPT,
            target_ref="t", policy=policy,
            risk_level=RiskLevel.LOW, rationale="x",
        )
        with pytest.raises(ValueError):
            GuardrailDecisionEnvelope(
                decision_id="dec-9", evaluation=ev,
                decision=PolicyDecisionType.ALLOW, execution_allowed=True,
                decided_by="",
            )


class TestSerialization:
    def test_evaluation_to_json(self):
        policy = PolicyRef(policy_id="pol-1", policy_name="test")
        ev = PolicyEvaluation(
            evaluation_id="eval-s", target_type=EvaluationTargetType.PROMPT,
            target_ref="prompt://1", policy=policy,
            risk_level=RiskLevel.LOW, rationale="test",
        )
        data = ev.model_dump()
        assert data["evaluation_id"] == "eval-s"
        assert data["target_type"] == "prompt"

    def test_envelope_roundtrip(self):
        policy = PolicyRef(policy_id="pol-1", policy_name="test")
        ev = PolicyEvaluation(
            evaluation_id="eval-r", target_type=EvaluationTargetType.TOOL_INVOCATION,
            target_ref="tool://1", policy=policy,
            risk_level=RiskLevel.MODERATE, rationale="Roundtrip",
        )
        env = GuardrailDecisionEnvelope(
            decision_id="dec-r", evaluation=ev,
            decision=PolicyDecisionType.ALLOW, execution_allowed=True,
            obligations=[DecisionObligation(obligation_type=ObligationType.LOG_ONLY)],
            decided_by="guardrail:test",
        )
        raw = env.model_dump()
        restored = GuardrailDecisionEnvelope(**raw)
        assert restored.decision_id == env.decision_id
        assert restored.evaluation.evaluation_id == ev.evaluation_id
        assert len(restored.obligations) == 1

    def test_finding_roundtrip(self):
        sig = EvidenceSignal(
            signal_id="sig-r", signal_type="classifier",
            source_ref="model:v1", summary="test",
            confidence=0.75,
        )
        f = GuardrailFinding(
            finding_id="f-r", severity=FindingSeverity.HIGH,
            category="safety", summary="Test finding",
            evidence_signals=[sig],
        )
        raw = f.model_dump()
        restored = GuardrailFinding(**raw)
        assert restored.severity == FindingSeverity.HIGH
        assert restored.evidence_signals[0].confidence == 0.75


class TestIntegration:
    def test_safe_tool_call_allowed(self):
        policy = PolicyRef(policy_id="pol-search", policy_name="search_policy", policy_version="1.0")
        ev = PolicyEvaluation(
            evaluation_id="eval-safe", target_type=EvaluationTargetType.TOOL_INVOCATION,
            target_ref="tool://td-search/read", policy=policy,
            risk_level=RiskLevel.LOW,
            rationale="Search tool read actions are allowlisted for agent-reader",
        )
        env = GuardrailDecisionEnvelope(
            decision_id="dec-safe", evaluation=ev,
            decision=PolicyDecisionType.ALLOW, execution_allowed=True,
            decided_by="guardrail:runtime-v1",
        )
        assert env.execution_allowed is True
        assert env.decision == PolicyDecisionType.ALLOW

    def test_high_risk_delete_action_denied(self):
        sig = EvidenceSignal(
            signal_id="sig-del", signal_type="risk_classifier",
            source_ref="policy:data_governance", summary="DELETE on production storage",
            confidence=0.98,
        )
        finding = GuardrailFinding(
            finding_id="f-del", severity=FindingSeverity.CRITICAL,
            category="data_loss_prevention",
            summary="DELETE action on production blob storage is prohibited",
            evidence_signals=[sig],
        )
        policy = PolicyRef(policy_id="pol-dlp", policy_name="data_loss_prevention", policy_version="2.1")
        ev = PolicyEvaluation(
            evaluation_id="eval-del", target_type=EvaluationTargetType.TOOL_INVOCATION,
            target_ref="tool://td-storage/delete", policy=policy,
            findings=[finding], risk_level=RiskLevel.CRITICAL,
            rationale="DELETE on production storage violates data loss prevention policy",
        )
        env = GuardrailDecisionEnvelope(
            decision_id="dec-del", evaluation=ev,
            decision=PolicyDecisionType.DENY, execution_allowed=False,
            decided_by="guardrail:runtime-v1",
        )
        assert env.execution_allowed is False
        assert env.decision == PolicyDecisionType.DENY

    def test_model_output_modified_with_masking(self):
        sig = EvidenceSignal(
            signal_id="sig-pii", signal_type="regex",
            source_ref="guardrail:pii_detector", summary="Email pattern detected",
            confidence=0.95,
        )
        finding = GuardrailFinding(
            finding_id="f-pii", severity=FindingSeverity.MODERATE,
            category="pii_detection", summary="PII found in model output",
            evidence_signals=[sig],
        )
        policy = PolicyRef(policy_id="pol-pii", policy_name="pii_redaction", policy_version="3.0")
        ev = PolicyEvaluation(
            evaluation_id="eval-pii", target_type=EvaluationTargetType.MODEL_OUTPUT,
            target_ref="output://run-42/msg-7", policy=policy,
            findings=[finding], risk_level=RiskLevel.MODERATE,
            rationale="Model output contains PII; masking required before delivery",
        )
        env = GuardrailDecisionEnvelope(
            decision_id="dec-pii", evaluation=ev,
            decision=PolicyDecisionType.MODIFY, execution_allowed=True,
            obligations=[DecisionObligation(
                obligation_type=ObligationType.MASK_CONTENT,
                parameters=["email", "phone"],
            )],
            decided_by="guardrail:runtime-v1",
        )
        assert env.decision == PolicyDecisionType.MODIFY
        assert env.execution_allowed is True
        assert env.obligations[0].obligation_type == ObligationType.MASK_CONTENT

    def test_memory_access_deferred_for_review(self):
        sig = EvidenceSignal(
            signal_id="sig-mem", signal_type="scope_check",
            source_ref="policy:memory_boundary", summary="Cross-tenant memory access",
            confidence=0.85,
        )
        finding = GuardrailFinding(
            finding_id="f-mem", severity=FindingSeverity.HIGH,
            category="tenant_isolation",
            summary="Memory access crosses tenant boundary",
            evidence_signals=[sig],
        )
        policy = PolicyRef(policy_id="pol-mem", policy_name="memory_isolation", policy_version="1.2")
        ev = PolicyEvaluation(
            evaluation_id="eval-mem", target_type=EvaluationTargetType.MEMORY_ACCESS,
            target_ref="memory://mem-042", policy=policy,
            findings=[finding], risk_level=RiskLevel.HIGH,
            rationale="Cross-tenant memory access flagged for human review",
        )
        env = GuardrailDecisionEnvelope(
            decision_id="dec-mem", evaluation=ev,
            decision=PolicyDecisionType.REVIEW, execution_allowed=True,
            obligations=[DecisionObligation(
                obligation_type=ObligationType.REQUIRE_APPROVAL,
                parameters=["security_team"],
            )],
            decided_by="guardrail:runtime-v1",
        )
        assert env.decision == PolicyDecisionType.REVIEW
        assert env.execution_allowed is True

    def test_workflow_step_quarantined_due_to_critical_findings(self):
        sig1 = EvidenceSignal(
            signal_id="sig-wf-1", signal_type="static_analysis",
            source_ref="analyzer:codeql", summary="Command injection vulnerability",
            confidence=0.92,
        )
        sig2 = EvidenceSignal(
            signal_id="sig-wf-2", signal_type="secret_scan",
            source_ref="scanner:secrets", summary="Hardcoded API key in step",
            confidence=0.99,
        )
        f1 = GuardrailFinding(
            finding_id="f-wf-1", severity=FindingSeverity.CRITICAL,
            category="security", summary="Code injection risk",
            evidence_signals=[sig1],
        )
        f2 = GuardrailFinding(
            finding_id="f-wf-2", severity=FindingSeverity.CRITICAL,
            category="secrets_leak", summary="Hardcoded credential",
            evidence_signals=[sig2],
        )
        policy = PolicyRef(policy_id="pol-wf", policy_name="workflow_safety", policy_version="1.0")
        ev = PolicyEvaluation(
            evaluation_id="eval-wf", target_type=EvaluationTargetType.WORKFLOW_STEP,
            target_ref="step://build/deploy", policy=policy,
            findings=[f1, f2], risk_level=RiskLevel.CRITICAL,
            rationale="Two critical findings: command injection and secret leak",
        )
        env = GuardrailDecisionEnvelope(
            decision_id="dec-wf", evaluation=ev,
            decision=PolicyDecisionType.QUARANTINE, execution_allowed=False,
            obligations=[DecisionObligation(
                obligation_type=ObligationType.REQUIRE_APPROVAL,
                parameters=["security_team", "lead_engineer"],
            )],
            decided_by="guardrail:runtime-v1",
        )
        assert env.decision == PolicyDecisionType.QUARANTINE
        assert env.execution_allowed is False
        assert len(env.evaluation.findings) == 2

    def test_all_target_types_accepted(self):
        policy = PolicyRef(policy_id="pol-1", policy_name="test")
        for ttype in EvaluationTargetType:
            ev = PolicyEvaluation(
                evaluation_id=f"eval-{ttype.value}", target_type=ttype,
                target_ref=f"ref://{ttype.value}", policy=policy,
                risk_level=RiskLevel.LOW, rationale="test",
            )
            assert ev.target_type == ttype

    def test_all_decision_types_accepted(self):
        policy = PolicyRef(policy_id="pol-1", policy_name="test")
        ev = PolicyEvaluation(
            evaluation_id="eval-d", target_type=EvaluationTargetType.PROMPT,
            target_ref="ref://1", policy=policy,
            risk_level=RiskLevel.LOW, rationale="test",
        )
        for dtype in PolicyDecisionType:
            allowed = dtype not in (PolicyDecisionType.DENY, PolicyDecisionType.QUARANTINE)
            env = GuardrailDecisionEnvelope(
                decision_id=f"dec-{dtype.value}", evaluation=ev,
                decision=dtype, execution_allowed=allowed,
                decided_by="guardrail:v1",
            )
            assert env.decision == dtype

    def test_all_severity_levels_accepted(self):
        policy = PolicyRef(policy_id="pol-1", policy_name="test")
        for sev in FindingSeverity:
            sigs = []
            if sev in (FindingSeverity.HIGH, FindingSeverity.CRITICAL):
                sigs.append(EvidenceSignal(
                    signal_id="sig", signal_type="test",
                    source_ref="src", summary="req",
                ))
            f = GuardrailFinding(
                finding_id=f"f-{sev.value}", severity=sev,
                category="test", summary="test",
                evidence_signals=sigs,
            )
            assert f.severity == sev

    def test_all_obligation_types_accepted(self):
        for ob_type in ObligationType:
            ob = DecisionObligation(obligation_type=ob_type)
            assert ob.obligation_type == ob_type
