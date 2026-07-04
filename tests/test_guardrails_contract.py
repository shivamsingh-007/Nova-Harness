import pytest
from pydantic import ValidationError
from models.guardrails_contract import (
    GuardrailDirection,
    GuardrailAction,
    ContentSourceType,
    RiskCategory,
    GuardrailRule,
    InputPayload,
    OutputPayload,
    GuardrailEvidence,
    GuardrailEvaluation,
    SanitizedOutput,
    GuardrailDecision,
    GuardrailPolicy,
)


class TestEnums:
    def test_guardrail_direction_values(self):
        assert GuardrailDirection.INPUT.value == "input"
        assert GuardrailDirection.OUTPUT.value == "output"

    def test_guardrail_action_values(self):
        assert GuardrailAction.ALLOW.value == "allow"
        assert GuardrailAction.REQUIRE_CONFIRMATION.value == "require_confirmation"

    def test_content_source_type_values(self):
        assert ContentSourceType.USER.value == "user"
        assert ContentSourceType.SYSTEM_PROMPT.value == "system_prompt"

    def test_risk_categories_present(self):
        expected = {
            "PROMPT_INJECTION", "JAILBREAK", "DATA_EXFILTRATION",
            "PII", "POLICY_VIOLATION", "UNSAFE_CODE",
            "UNTRUSTED_INSTRUCTION", "SCHEMA_VIOLATION", "UNKNOWN",
        }
        assert set(RiskCategory.__members__) == expected


class TestGuardrailRule:
    def test_valid(self):
        rule = GuardrailRule(
            rule_id="rule-inject-01", direction=GuardrailDirection.INPUT,
            risk_category=RiskCategory.PROMPT_INJECTION, action=GuardrailAction.REJECT,
        )
        assert rule.enabled is True

    def test_with_description(self):
        rule = GuardrailRule(
            rule_id="r1", direction=GuardrailDirection.OUTPUT,
            risk_category=RiskCategory.PII, action=GuardrailAction.SANITIZE,
            description="Redact PII from model output",
        )
        assert rule.description == "Redact PII from model output"

    def test_empty_rule_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            GuardrailRule(rule_id="  ", direction=GuardrailDirection.INPUT,
                          risk_category=RiskCategory.UNKNOWN, action=GuardrailAction.ALLOW)
        assert "rule_id must not be empty" in str(exc.value)

    def test_disabled_rule(self):
        rule = GuardrailRule(
            rule_id="r2", direction=GuardrailDirection.INPUT,
            risk_category=RiskCategory.JAILBREAK, action=GuardrailAction.REJECT,
            enabled=False,
        )
        assert rule.enabled is False


class TestInputPayload:
    def test_valid(self):
        payload = InputPayload(payload_id="p1", source_type=ContentSourceType.USER, content="write code")
        assert payload.source_label is None

    def test_with_source_label(self):
        payload = InputPayload(payload_id="p2", source_type=ContentSourceType.RETRIEVED_CONTEXT,
                               content="doc content", source_label="docs/api.md")
        assert payload.source_label == "docs/api.md"

    def test_empty_payload_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            InputPayload(payload_id="  ", source_type=ContentSourceType.USER, content="hello")
        assert "payload_id must not be empty" in str(exc.value)

    def test_empty_content_raises(self):
        with pytest.raises(ValidationError) as exc:
            InputPayload(payload_id="p1", source_type=ContentSourceType.USER, content="  ")
        assert "content must not be empty" in str(exc.value)


class TestOutputPayload:
    def test_valid_for_user(self):
        payload = OutputPayload(payload_id="o1", content="response text")
        assert payload.intended_for_user is True
        assert payload.intended_for_tool is False

    def test_for_tool(self):
        payload = OutputPayload(payload_id="o2", content="edit_file(...)", intended_for_user=False, intended_for_tool=True)
        assert payload.intended_for_tool is True

    def test_for_both(self):
        payload = OutputPayload(payload_id="o3", content="summary", intended_for_user=True, intended_for_tool=True)
        assert payload.intended_for_user is True
        assert payload.intended_for_tool is True

    def test_neither_raises(self):
        with pytest.raises(ValidationError) as exc:
            OutputPayload(payload_id="o4", content="x", intended_for_user=False, intended_for_tool=False)
        assert "at least one of intended_for_user or intended_for_tool must be True" in str(exc.value)

    def test_empty_payload_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            OutputPayload(payload_id="  ", content="hello")
        assert "payload_id must not be empty" in str(exc.value)

    def test_empty_content_raises(self):
        with pytest.raises(ValidationError) as exc:
            OutputPayload(payload_id="o1", content="  ")
        assert "content must not be empty" in str(exc.value)


class TestGuardrailEvidence:
    def test_valid(self):
        ev = GuardrailEvidence(evidence_type="regex_match", detail="matched email pattern", matched_text="user@example.com")
        assert ev.evidence_type == "regex_match"
        assert ev.matched_text == "user@example.com"

    def test_no_matched_text(self):
        ev = GuardrailEvidence(evidence_type="length_check", detail="exceeded max 4000 chars")
        assert ev.matched_text is None

    def test_empty_type_raises(self):
        with pytest.raises(ValidationError) as exc:
            GuardrailEvidence(evidence_type="  ", detail="x")
        assert "must not be empty" in str(exc.value)

    def test_empty_detail_raises(self):
        with pytest.raises(ValidationError) as exc:
            GuardrailEvidence(evidence_type="type", detail="  ")
        assert "must not be empty" in str(exc.value)


class TestGuardrailEvaluation:
    def test_allowed(self):
        eval_ = GuardrailEvaluation(
            evaluation_id="e1", payload_id="p1", direction=GuardrailDirection.INPUT,
            action=GuardrailAction.ALLOW, blocked=False,
        )
        assert eval_.blocked is False

    def test_blocked_with_rules(self):
        eval_ = GuardrailEvaluation(
            evaluation_id="e2", payload_id="p2", direction=GuardrailDirection.INPUT,
            action=GuardrailAction.REJECT, blocked=True,
            triggered_rules=["rule-inject-01"],
            detected_risks=[RiskCategory.PROMPT_INJECTION],
        )
        assert eval_.blocked is True
        assert RiskCategory.PROMPT_INJECTION in eval_.detected_risks

    def test_blocked_no_rules_raises(self):
        with pytest.raises(ValidationError) as exc:
            GuardrailEvaluation(
                evaluation_id="e3", payload_id="p3", direction=GuardrailDirection.INPUT,
                action=GuardrailAction.REJECT, blocked=True,
            )
        assert "blocked=True requires at least one triggered_rules entry" in str(exc.value)

    def test_reject_no_rules_raises(self):
        with pytest.raises(ValidationError) as exc:
            GuardrailEvaluation(
                evaluation_id="e4", payload_id="p4", direction=GuardrailDirection.OUTPUT,
                action=GuardrailAction.REJECT, blocked=True,
            )
        assert "blocked=True requires at least one triggered_rules entry" in str(exc.value)

    def test_reject_no_rules_even_if_not_blocked(self):
        with pytest.raises(ValidationError) as exc:
            GuardrailEvaluation(
                evaluation_id="e5", payload_id="p5", direction=GuardrailDirection.OUTPUT,
                action=GuardrailAction.REJECT, blocked=False,
            )
        assert "REJECT action requires at least one triggered_rules entry" in str(exc.value)

    def test_sanitize_not_blocked(self):
        eval_ = GuardrailEvaluation(
            evaluation_id="e6", payload_id="p6", direction=GuardrailDirection.OUTPUT,
            action=GuardrailAction.SANITIZE, blocked=False,
            triggered_rules=["rule-pii-01"],
        )
        assert eval_.action == GuardrailAction.SANITIZE

    def test_with_evidence(self):
        eval_ = GuardrailEvaluation(
            evaluation_id="e7", payload_id="p7", direction=GuardrailDirection.INPUT,
            action=GuardrailAction.REJECT, blocked=True,
            triggered_rules=["r1"],
            evidence=[GuardrailEvidence(evidence_type="pattern", detail="injection pattern detected")],
        )
        assert len(eval_.evidence) == 1

    def test_empty_evaluation_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            GuardrailEvaluation(evaluation_id="  ", payload_id="p1", direction=GuardrailDirection.INPUT,
                                action=GuardrailAction.ALLOW, blocked=False)
        assert "must not be empty" in str(exc.value)

    def test_empty_payload_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            GuardrailEvaluation(evaluation_id="e1", payload_id="  ", direction=GuardrailDirection.INPUT,
                                action=GuardrailAction.ALLOW, blocked=False)
        assert "must not be empty" in str(exc.value)


class TestSanitizedOutput:
    def test_valid(self):
        sanitized = SanitizedOutput(output_id="s1", sanitized_content="Hello [REDACTED]")
        assert sanitized.schema_valid is True

    def test_with_redactions(self):
        sanitized = SanitizedOutput(
            output_id="s2", sanitized_content="Your email is [REDACTED]",
            redactions_applied=["email", "phone"],
        )
        assert len(sanitized.redactions_applied) == 2

    def test_schema_invalid(self):
        sanitized = SanitizedOutput(output_id="s3", sanitized_content="{}", schema_valid=False)
        assert sanitized.schema_valid is False

    def test_empty_output_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            SanitizedOutput(output_id="  ", sanitized_content="hello")
        assert "output_id must not be empty" in str(exc.value)

    def test_empty_content_raises(self):
        with pytest.raises(ValidationError) as exc:
            SanitizedOutput(output_id="s1", sanitized_content="  ")
        assert "sanitized_content must not be empty" in str(exc.value)


class TestGuardrailDecision:
    def test_allowed(self):
        d = GuardrailDecision(decision_id="d1", payload_id="p1", final_action=GuardrailAction.ALLOW,
                              rationale="passed all checks")
        assert d.should_audit is False

    def test_rejected_with_audit(self):
        d = GuardrailDecision(decision_id="d2", payload_id="p2", final_action=GuardrailAction.REJECT,
                              rationale="prompt injection detected", should_audit=True)
        assert d.should_audit is True

    def test_escalate(self):
        d = GuardrailDecision(decision_id="d3", payload_id="p3", final_action=GuardrailAction.ESCALATE,
                              rationale="ambiguous pattern, human review needed")
        assert d.final_action == GuardrailAction.ESCALATE

    def test_empty_decision_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            GuardrailDecision(decision_id="  ", payload_id="p1", final_action=GuardrailAction.ALLOW, rationale="ok")
        assert "must not be empty" in str(exc.value)

    def test_empty_payload_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            GuardrailDecision(decision_id="d1", payload_id="  ", final_action=GuardrailAction.ALLOW, rationale="ok")
        assert "must not be empty" in str(exc.value)

    def test_empty_rationale_raises(self):
        with pytest.raises(ValidationError) as exc:
            GuardrailDecision(decision_id="d1", payload_id="p1", final_action=GuardrailAction.ALLOW, rationale="  ")
        assert "rationale must not be empty" in str(exc.value)


class TestGuardrailPolicy:
    def test_valid(self):
        policy = GuardrailPolicy(policy_id="gp-default", require_schema_validation=False)
        assert policy.policy_id == "gp-default"

    def test_with_rules(self):
        policy = GuardrailPolicy(
            policy_id="gp-strict",
            input_rules=[
                GuardrailRule(rule_id="r1", direction=GuardrailDirection.INPUT,
                              risk_category=RiskCategory.PROMPT_INJECTION, action=GuardrailAction.REJECT),
            ],
            output_rules=[
                GuardrailRule(rule_id="r2", direction=GuardrailDirection.OUTPUT,
                              risk_category=RiskCategory.PII, action=GuardrailAction.SANITIZE),
            ],
            allowed_output_formats=["json", "text"],
            require_schema_validation=True,
        )
        assert len(policy.input_rules) == 1
        assert len(policy.output_rules) == 1
        assert "json" in policy.allowed_output_formats

    def test_empty_policy_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            GuardrailPolicy(policy_id="  ")
        assert "policy_id must not be empty" in str(exc.value)

    def test_schema_validation_without_formats_raises(self):
        with pytest.raises(ValidationError) as exc:
            GuardrailPolicy(
                policy_id="gp-bad",
                require_schema_validation=True,
                allowed_output_formats=[],
            )
        assert "allowed_output_formats must not be empty when require_schema_validation=True" in str(exc.value)

    def test_schema_validation_disabled_no_formats_needed(self):
        policy = GuardrailPolicy(policy_id="gp-loose", require_schema_validation=False)
        assert policy.require_schema_validation is False


class TestSerialization:
    def test_policy_to_json(self):
        policy = GuardrailPolicy(
            policy_id="gp-test",
            output_rules=[
                GuardrailRule(rule_id="r-schema", direction=GuardrailDirection.OUTPUT,
                              risk_category=RiskCategory.SCHEMA_VIOLATION, action=GuardrailAction.REJECT),
            ],
            allowed_output_formats=["json"],
            require_schema_validation=True,
        )
        json_str = policy.model_dump_json()
        assert "gp-test" in json_str
        assert "schema_violation" in json_str

    def test_decision_roundtrip(self):
        d = GuardrailDecision(decision_id="d1", payload_id="p1", final_action=GuardrailAction.REJECT,
                              rationale="blocked by policy")
        dumped = d.model_dump()
        assert dumped["final_action"] == "reject"

    def test_evaluation_roundtrip(self):
        eval_ = GuardrailEvaluation(
            evaluation_id="e1", payload_id="p1", direction=GuardrailDirection.INPUT,
            action=GuardrailAction.REJECT, blocked=True, triggered_rules=["r1"],
        )
        dumped = eval_.model_dump()
        assert dumped["blocked"] is True
