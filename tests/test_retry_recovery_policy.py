import pytest
from pydantic import ValidationError
from models.retry_recovery import (
    FailureClass,
    RecoveryAction,
    BackoffStrategy,
    RetryRule,
    RecoveryDecision,
    RetryRecoveryPolicy,
    v1_default_policy,
)


def make_rule(**overrides) -> RetryRule:
    kwargs = dict(failure_class=FailureClass.TRANSIENT_INFRA, max_attempts=3,
                  backoff_strategy=BackoffStrategy.EXPONENTIAL_WITH_JITTER,
                  base_delay_seconds=1.0, max_delay_seconds=30.0,
                  allowed_actions=[RecoveryAction.RETRY])
    kwargs.update(overrides)
    return RetryRule(**kwargs)


def make_decision(**overrides) -> RecoveryDecision:
    kwargs = dict(failure_class=FailureClass.TRANSIENT_INFRA,
                  chosen_action=RecoveryAction.RETRY, reason="Transient infrastructure failure")
    kwargs.update(overrides)
    return RecoveryDecision(**kwargs)


def make_policy(**overrides) -> RetryRecoveryPolicy:
    unknown_rule = make_rule(failure_class=FailureClass.UNKNOWN, max_attempts=1,
                             allowed_actions=[RecoveryAction.RETRY, RecoveryAction.ESCALATE_TO_HUMAN])
    kwargs = dict(policy_id="pol-test",
                  rules=[make_rule()],
                  default_unknown_rule=unknown_rule)
    kwargs.update(overrides)
    return RetryRecoveryPolicy(**kwargs)


class TestFailureClass:
    def test_all_values_present(self):
        assert len(FailureClass) == 9
        assert FailureClass.TRANSIENT_INFRA.value == "transient_infra"
        assert FailureClass.UNKNOWN.value == "unknown"


class TestRecoveryAction:
    def test_all_values_present(self):
        assert len(RecoveryAction) == 5
        assert RecoveryAction.FAIL_TERMINAL.value == "fail_terminal"


class TestBackoffStrategy:
    def test_all_values_present(self):
        assert len(BackoffStrategy) == 4
        assert BackoffStrategy.EXPONENTIAL_WITH_JITTER.value == "exponential_with_jitter"


class TestRetryRule:
    def test_minimal_rule(self):
        rule = RetryRule(failure_class=FailureClass.RATE_LIMIT, max_attempts=2)
        assert rule.failure_class == FailureClass.RATE_LIMIT
        assert rule.max_attempts == 2
        assert rule.backoff_strategy == BackoffStrategy.NONE

    def test_full_rule(self):
        rule = make_rule()
        assert rule.max_attempts == 3
        assert rule.base_delay_seconds == 1.0
        assert rule.max_delay_seconds == 30.0

    def test_non_idempotent_rule_can_include_retry(self):
        rule = RetryRule(failure_class=FailureClass.TOOL_EXECUTION_FAILED, max_attempts=2,
                         requires_idempotency=False,
                         allowed_actions=[RecoveryAction.RETRY])
        assert RecoveryAction.RETRY in rule.allowed_actions

    def test_all_failure_classes_accepted(self):
        for fc in FailureClass:
            rule = RetryRule(failure_class=fc, max_attempts=1)
            assert rule.failure_class == fc

    def test_all_backoff_strategies_accepted(self):
        for bs in BackoffStrategy:
            rule = make_rule(backoff_strategy=bs)
            assert rule.backoff_strategy == bs

    def test_negative_max_attempts_invalid(self):
        with pytest.raises(ValidationError):
            make_rule(max_attempts=-1)

    def test_negative_base_delay_invalid(self):
        with pytest.raises(ValidationError):
            make_rule(base_delay_seconds=-0.5)

    def test_negative_max_delay_invalid(self):
        with pytest.raises(ValidationError):
            make_rule(max_delay_seconds=-1.0)

    def test_max_delay_less_than_base_delay_invalid(self):
        with pytest.raises(ValidationError):
            make_rule(base_delay_seconds=5.0, max_delay_seconds=2.0)

    def test_equal_base_and_max_delay_valid(self):
        rule = make_rule(base_delay_seconds=3.0, max_delay_seconds=3.0)
        assert rule.base_delay_seconds == 3.0

    def test_zero_delays_valid(self):
        rule = RetryRule(failure_class=FailureClass.UNKNOWN, max_attempts=1)
        assert rule.base_delay_seconds == 0.0
        assert rule.max_delay_seconds == 0.0

    def test_respect_retry_after_default_false(self):
        rule = RetryRule(failure_class=FailureClass.RATE_LIMIT, max_attempts=2)
        assert rule.respect_retry_after is False

    def test_requires_idempotency_default_false(self):
        rule = RetryRule(failure_class=FailureClass.TOOL_EXECUTION_FAILED, max_attempts=2)
        assert rule.requires_idempotency is False


class TestRecoveryDecision:
    def test_minimal_decision(self):
        d = make_decision()
        assert d.failure_class == FailureClass.TRANSIENT_INFRA
        assert d.chosen_action == RecoveryAction.RETRY

    def test_with_retry_after(self):
        d = make_decision(retry_after_seconds=2.5)
        assert d.retry_after_seconds == 2.5

    def test_with_checkpoint_id(self):
        d = make_decision(resume_from_checkpoint_id="cp-003")
        assert d.resume_from_checkpoint_id == "cp-003"

    def test_empty_reason_invalid(self):
        with pytest.raises(ValidationError):
            make_decision(reason="  ")

    def test_negative_retry_after_invalid(self):
        with pytest.raises(ValidationError):
            make_decision(retry_after_seconds=-1.0)


class TestRetryRecoveryPolicy:
    def test_minimal_policy(self):
        p = make_policy()
        assert p.policy_id == "pol-test"
        assert len(p.rules) == 1

    def test_multiple_rules(self):
        p = make_policy(rules=[
            make_rule(failure_class=FailureClass.TRANSIENT_INFRA),
            make_rule(failure_class=FailureClass.RATE_LIMIT, max_attempts=3),
        ])
        assert len(p.rules) == 2

    def test_empty_policy_id_invalid(self):
        with pytest.raises(ValidationError):
            make_policy(policy_id="  ")

    def test_duplicate_failure_classes_invalid(self):
        with pytest.raises(ValidationError):
            make_policy(rules=[
                make_rule(failure_class=FailureClass.TRANSIENT_INFRA),
                make_rule(failure_class=FailureClass.TRANSIENT_INFRA),
            ])

    def test_non_duplicate_failure_classes_valid(self):
        p = make_policy(rules=[
            make_rule(failure_class=FailureClass.TRANSIENT_INFRA),
            make_rule(failure_class=FailureClass.RATE_LIMIT),
            make_rule(failure_class=FailureClass.MODEL_OUTPUT_INVALID),
            make_rule(failure_class=FailureClass.VERIFICATION_FAILED),
        ])
        assert len(p.rules) == 4

    def test_default_unknown_rule_required(self):
        with pytest.raises(ValidationError):
            RetryRecoveryPolicy(policy_id="pol-bad")

    def test_default_unknown_must_not_be_in_rules(self):
        unk = make_rule(failure_class=FailureClass.UNKNOWN, max_attempts=1)
        with pytest.raises(ValidationError):
            make_policy(rules=[make_rule(), unk])


class TestV1DefaultPolicy:
    def test_creates_successfully(self):
        p = v1_default_policy()
        assert p.policy_id == "retry-recovery-v1"

    def test_has_all_8_rules_plus_unknown(self):
        p = v1_default_policy()
        assert len(p.rules) == 8

    def test_transient_infra_3_attempts(self):
        p = v1_default_policy()
        r = [x for x in p.rules if x.failure_class == FailureClass.TRANSIENT_INFRA][0]
        assert r.max_attempts == 3
        assert r.backoff_strategy == BackoffStrategy.EXPONENTIAL_WITH_JITTER

    def test_rate_limit_respects_retry_after(self):
        p = v1_default_policy()
        r = [x for x in p.rules if x.failure_class == FailureClass.RATE_LIMIT][0]
        assert r.respect_retry_after is True

    def test_tool_input_invalid_zero_attempts(self):
        p = v1_default_policy()
        r = [x for x in p.rules if x.failure_class == FailureClass.TOOL_INPUT_INVALID][0]
        assert r.max_attempts == 0
        assert RecoveryAction.RETRY not in r.allowed_actions

    def test_tool_execution_failed_requires_idempotency(self):
        p = v1_default_policy()
        r = [x for x in p.rules if x.failure_class == FailureClass.TOOL_EXECUTION_FAILED][0]
        assert r.requires_idempotency is True
        assert RecoveryAction.RETRY not in r.allowed_actions

    def test_verification_failed_1_retry_or_replan(self):
        p = v1_default_policy()
        r = [x for x in p.rules if x.failure_class == FailureClass.VERIFICATION_FAILED][0]
        assert r.max_attempts == 1
        assert RecoveryAction.REPLAN in r.allowed_actions

    def test_approval_rejected_has_escalation_and_fail(self):
        p = v1_default_policy()
        r = [x for x in p.rules if x.failure_class == FailureClass.APPROVAL_REJECTED][0]
        assert RecoveryAction.ESCALATE_TO_HUMAN in r.allowed_actions
        assert RecoveryAction.FAIL_TERMINAL in r.allowed_actions

    def test_non_retryable_policy_fails_terminal(self):
        p = v1_default_policy()
        r = [x for x in p.rules if x.failure_class == FailureClass.NON_RETRYABLE_POLICY][0]
        assert RecoveryAction.FAIL_TERMINAL in r.allowed_actions

    def test_unknown_default_has_escalation_path(self):
        p = v1_default_policy()
        assert p.default_unknown_rule.max_attempts == 1
        assert RecoveryAction.ESCALATE_TO_HUMAN in p.default_unknown_rule.allowed_actions
