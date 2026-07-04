import pytest
from pydantic import ValidationError
from models.failure_taxonomy import (
    FailureCategory,
    FailureSeverity,
    RecoveryDisposition,
    ErrorContext,
    ErrorChainLink,
    ErrorEnvelope,
    PublicErrorView,
    FailureClassification,
)


def make_envelope(**overrides) -> ErrorEnvelope:
    defaults = dict(
        error_id="err-001",
        code="PROVIDER_TIMEOUT",
        message="Provider request timed out after 30s",
        category=FailureCategory.PROVIDER,
        severity=FailureSeverity.ERROR,
        retryable=True,
        user_safe=True,
        recovery_disposition=RecoveryDisposition.RETRYABLE,
        context=ErrorContext(
            run_id="run-001",
            trace_id="trace-abc",
            step_id="step-3",
            operation="generate",
            component="openrouter",
        ),
        details=["timeout_seconds=30", "model=gemini-2.0-flash"],
    )
    defaults.update(overrides)
    return ErrorEnvelope(**defaults)


class TestEnums:
    def test_failure_category_values(self):
        assert FailureCategory.TASK_INPUT.value == "task_input"
        assert FailureCategory.BUDGET_LIMIT.value == "budget_limit"
        assert FailureCategory.UNKNOWN.value == "unknown"

    def test_all_categories_present(self):
        expected = {
            "TASK_INPUT", "CONTEXT_SELECTION", "PROMPT_ASSEMBLY",
            "PROVIDER", "TOOL_INVOCATION", "SAFETY_POLICY",
            "APPROVAL", "VERIFICATION", "PERSISTENCE",
            "ORCHESTRATION", "BUDGET_LIMIT", "UNKNOWN",
        }
        assert set(FailureCategory.__members__) == expected

    def test_failure_severity_values(self):
        assert FailureSeverity.INFO.value == "info"
        assert FailureSeverity.CRITICAL.value == "critical"

    def test_recovery_disposition_values(self):
        assert RecoveryDisposition.RETRYABLE.value == "retryable"
        assert RecoveryDisposition.BLOCK_AND_AUDIT.value == "block_and_audit"


class TestErrorContext:
    def test_valid(self):
        ctx = ErrorContext(run_id="run-001", operation="generate", component="provider")
        assert ctx.run_id == "run-001"
        assert ctx.trace_id is None

    def test_with_trace_and_step(self):
        ctx = ErrorContext(run_id="run-001", trace_id="t1", step_id="s1", operation="verify", component="verifier")
        assert ctx.trace_id == "t1"
        assert ctx.step_id == "s1"

    def test_empty_run_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            ErrorContext(run_id="  ", operation="gen", component="c")
        assert "must not be empty" in str(exc.value)

    def test_empty_operation_raises(self):
        with pytest.raises(ValidationError) as exc:
            ErrorContext(run_id="r", operation="  ", component="c")
        assert "must not be empty" in str(exc.value)

    def test_empty_component_raises(self):
        with pytest.raises(ValidationError) as exc:
            ErrorContext(run_id="r", operation="gen", component="  ")
        assert "must not be empty" in str(exc.value)


class TestErrorChainLink:
    def test_valid(self):
        link = ErrorChainLink(code="TIMEOUT", message="connection timed out", category=FailureCategory.PROVIDER)
        assert link.code == "TIMEOUT"
        assert link.category == FailureCategory.PROVIDER

    def test_empty_code_raises(self):
        with pytest.raises(ValidationError) as exc:
            ErrorChainLink(code="  ", message="msg", category=FailureCategory.PROVIDER)
        assert "must not be empty" in str(exc.value)

    def test_empty_message_raises(self):
        with pytest.raises(ValidationError) as exc:
            ErrorChainLink(code="C", message="  ", category=FailureCategory.PROVIDER)
        assert "must not be empty" in str(exc.value)


class TestErrorEnvelope:
    def test_valid_retryable(self):
        env = make_envelope()
        assert env.error_id == "err-001"
        assert env.retryable is True
        assert env.user_safe is True

    def test_non_retryable(self):
        env = make_envelope(
            error_id="err-002",
            code="VERIFICATION_FAILED",
            message="Output failed test criteria",
            category=FailureCategory.VERIFICATION,
            severity=FailureSeverity.ERROR,
            retryable=False,
            user_safe=True,
            recovery_disposition=RecoveryDisposition.NON_RETRYABLE,
        )
        assert env.retryable is False
        assert env.recovery_disposition == RecoveryDisposition.NON_RETRYABLE

    def test_with_cause_chain(self):
        env = make_envelope(
            cause_chain=[
                ErrorChainLink(code="EMPTY_RESPONSE", message="provider returned empty", category=FailureCategory.PROVIDER),
                ErrorChainLink(code="RETRY_EXHAUSTED", message="all retries used", category=FailureCategory.PROVIDER),
            ]
        )
        assert len(env.cause_chain) == 2

    def test_empty_error_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_envelope(error_id="  ")
        assert "must not be empty" in str(exc.value)

    def test_empty_code_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_envelope(code="  ")
        assert "must not be empty" in str(exc.value)

    def test_empty_message_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_envelope(message="  ")
        assert "must not be empty" in str(exc.value)

    def test_retryable_with_non_retryable_disposition_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_envelope(
                retryable=True,
                recovery_disposition=RecoveryDisposition.NON_RETRYABLE,
            )
        assert "retryable=True is inconsistent with NON_RETRYABLE disposition" in str(exc.value)

    def test_block_and_audit_with_wrong_category_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_envelope(
                category=FailureCategory.PROVIDER,
                recovery_disposition=RecoveryDisposition.BLOCK_AND_AUDIT,
            )
        assert "BLOCK_AND_AUDIT only valid for safety/approval/budget/unknown categories" in str(exc.value)

    def test_block_and_audit_with_safety_valid(self):
        env = make_envelope(
            category=FailureCategory.SAFETY_POLICY,
            severity=FailureSeverity.CRITICAL,
            retryable=False,
            user_safe=False,
            recovery_disposition=RecoveryDisposition.BLOCK_AND_AUDIT,
        )
        assert env.recovery_disposition == RecoveryDisposition.BLOCK_AND_AUDIT

    def test_block_and_audit_with_budget_valid(self):
        env = make_envelope(
            category=FailureCategory.BUDGET_LIMIT,
            severity=FailureSeverity.ERROR,
            retryable=False,
            user_safe=True,
            recovery_disposition=RecoveryDisposition.BLOCK_AND_AUDIT,
        )
        assert env.category == FailureCategory.BUDGET_LIMIT

    def test_critical_with_retryable_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_envelope(
                severity=FailureSeverity.CRITICAL,
                recovery_disposition=RecoveryDisposition.RETRYABLE,
            )
        assert "CRITICAL severity should map to ESCALATE or BLOCK_AND_AUDIT" in str(exc.value)

    def test_critical_with_escalate_valid(self):
        env = make_envelope(
            category=FailureCategory.PROVIDER,
            severity=FailureSeverity.CRITICAL,
            retryable=True,
            user_safe=False,
            recovery_disposition=RecoveryDisposition.ESCALATE,
        )
        assert env.severity == FailureSeverity.CRITICAL


class TestPublicErrorView:
    def test_from_envelope(self):
        env = make_envelope()
        view = PublicErrorView(
            error_id=env.error_id,
            code=env.code,
            message=env.message,
            category=env.category,
            retryable=env.retryable,
        )
        assert view.code == "PROVIDER_TIMEOUT"
        assert view.retryable is True

    def test_sanitized_safe_message(self):
        view = PublicErrorView(
            error_id="err-001",
            code="PROVIDER_TIMEOUT",
            message="The AI provider took too long to respond. Please try again.",
            category=FailureCategory.PROVIDER,
            retryable=True,
        )
        assert "timeout_seconds" not in view.message

    def test_empty_view_fields_raises(self):
        with pytest.raises(ValidationError) as exc:
            PublicErrorView(error_id="", code="C", message="m", category=FailureCategory.UNKNOWN, retryable=False)
        assert "must not be empty" in str(exc.value)


class TestFailureClassification:
    def test_info_no_alert(self):
        fc = FailureClassification(
            error_id="err-001",
            primary_category=FailureCategory.PROVIDER,
            severity=FailureSeverity.INFO,
            recovery_disposition=RecoveryDisposition.RETRYABLE,
            should_trigger_alert=False,
        )
        assert fc.should_trigger_alert is False

    def test_critical_with_alert(self):
        fc = FailureClassification(
            error_id="err-002",
            primary_category=FailureCategory.SAFETY_POLICY,
            severity=FailureSeverity.CRITICAL,
            recovery_disposition=RecoveryDisposition.BLOCK_AND_AUDIT,
            should_trigger_alert=True,
        )
        assert fc.should_trigger_alert is True

    def test_alert_with_warning_raises(self):
        with pytest.raises(ValidationError) as exc:
            FailureClassification(
                error_id="err-003",
                primary_category=FailureCategory.PROVIDER,
                severity=FailureSeverity.WARNING,
                recovery_disposition=RecoveryDisposition.RETRYABLE,
                should_trigger_alert=True,
            )
        assert "alerts should only be triggered for ERROR or CRITICAL severity" in str(exc.value)

    def test_alert_with_info_raises(self):
        with pytest.raises(ValidationError) as exc:
            FailureClassification(
                error_id="err-004",
                primary_category=FailureCategory.PROVIDER,
                severity=FailureSeverity.INFO,
                recovery_disposition=RecoveryDisposition.RETRYABLE,
                should_trigger_alert=True,
            )
        assert "alerts should only be triggered for ERROR or CRITICAL severity" in str(exc.value)

    def test_empty_error_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            FailureClassification(
                error_id="  ",
                primary_category=FailureCategory.UNKNOWN,
                severity=FailureSeverity.ERROR,
                recovery_disposition=RecoveryDisposition.ESCALATE,
            )
        assert "must not be empty" in str(exc.value)


class TestSerialization:
    def test_envelope_to_json(self):
        env = make_envelope()
        json_str = env.model_dump_json()
        assert "err-001" in json_str
        assert "PROVIDER_TIMEOUT" in json_str

    def test_view_roundtrip(self):
        view = PublicErrorView(
            error_id="err-001",
            code="TOOL_FAILURE",
            message="Tool execution failed",
            category=FailureCategory.TOOL_INVOCATION,
            retryable=True,
        )
        dumped = view.model_dump()
        assert dumped["code"] == "TOOL_FAILURE"

    def test_classification_roundtrip(self):
        fc = FailureClassification(
            error_id="err-002",
            primary_category=FailureCategory.SAFETY_POLICY,
            severity=FailureSeverity.CRITICAL,
            recovery_disposition=RecoveryDisposition.BLOCK_AND_AUDIT,
            should_trigger_alert=True,
        )
        dumped = fc.model_dump()
        assert dumped["should_trigger_alert"] is True
