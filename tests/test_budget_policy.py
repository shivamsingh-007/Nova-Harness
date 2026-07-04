import pytest
from pydantic import ValidationError
from models.budget_policy import (
    BudgetScope,
    LimitAction,
    RateWindow,
    TokenBudget,
    CostBudget,
    RuntimeBudget,
    ToolCallBudget,
    RateLimitRule,
    BudgetPolicy,
    BudgetUsageSnapshot,
    BudgetDecision,
    BudgetViolation,
)


def make_policy(**overrides) -> BudgetPolicy:
    defaults = dict(
        policy_id="policy-run-001",
        token_budget=TokenBudget(max_input_tokens=32000, max_output_tokens=16000, max_total_tokens=48000),
        cost_budget=CostBudget(max_cost_usd=1.0, warn_cost_usd=0.8),
        runtime_budget=RuntimeBudget(max_runtime_seconds=120, max_steps=12, max_retries=2),
        tool_call_budget=ToolCallBudget(max_total_tool_calls=20, max_tool_calls_per_tool=8),
    )
    defaults.update(overrides)
    return BudgetPolicy(**defaults)


class TestEnums:
    def test_budget_scope_values(self):
        assert BudgetScope.RUN.value == "run"
        assert BudgetScope.USER.value == "user"
        assert BudgetScope.TENANT.value == "tenant"
        assert BudgetScope.MODEL.value == "model"
        assert BudgetScope.TOOL.value == "tool"
        assert BudgetScope.ENVIRONMENT.value == "environment"

    def test_limit_action_values(self):
        assert LimitAction.ALLOW.value == "allow"
        assert LimitAction.WARN.value == "warn"
        assert LimitAction.THROTTLE.value == "throttle"
        assert LimitAction.BLOCK.value == "block"

    def test_rate_window_values(self):
        assert RateWindow.PER_MINUTE.value == "per_minute"
        assert RateWindow.PER_HOUR.value == "per_hour"
        assert RateWindow.PER_DAY.value == "per_day"
        assert RateWindow.PER_RUN.value == "per_run"


class TestTokenBudget:
    def test_valid(self):
        tb = TokenBudget(max_input_tokens=32000, max_output_tokens=16000, max_total_tokens=48000)
        assert tb.max_input_tokens == 32000
        assert tb.max_output_tokens == 16000
        assert tb.max_total_tokens == 48000

    def test_zero_input_raises(self):
        with pytest.raises(ValidationError) as exc:
            TokenBudget(max_input_tokens=0, max_output_tokens=16000, max_total_tokens=48000)
        assert "must be at least 1" in str(exc.value)

    def test_zero_output_raises(self):
        with pytest.raises(ValidationError) as exc:
            TokenBudget(max_input_tokens=32000, max_output_tokens=0, max_total_tokens=48000)
        assert "must be at least 1" in str(exc.value)

    def test_zero_total_raises(self):
        with pytest.raises(ValidationError) as exc:
            TokenBudget(max_input_tokens=32000, max_output_tokens=16000, max_total_tokens=0)
        assert "must be at least 1" in str(exc.value)

    def test_total_less_than_input_raises(self):
        with pytest.raises(ValidationError) as exc:
            TokenBudget(max_input_tokens=32000, max_output_tokens=16000, max_total_tokens=16000)
        assert "max_total_tokens must be >= max_input_tokens" in str(exc.value)

    def test_total_less_than_output_raises(self):
        with pytest.raises(ValidationError) as exc:
            TokenBudget(max_input_tokens=1000, max_output_tokens=16000, max_total_tokens=8000)
        assert "max_total_tokens must be >= max_output_tokens" in str(exc.value)


class TestCostBudget:
    def test_valid(self):
        cb = CostBudget(max_cost_usd=1.0, warn_cost_usd=0.8)
        assert cb.max_cost_usd == 1.0
        assert cb.warn_cost_usd == 0.8

    def test_no_warn(self):
        cb = CostBudget(max_cost_usd=1.0)
        assert cb.warn_cost_usd is None

    def test_zero_cost(self):
        cb = CostBudget(max_cost_usd=0.0)
        assert cb.max_cost_usd == 0.0

    def test_max_cost_negative_raises(self):
        with pytest.raises(ValidationError) as exc:
            CostBudget(max_cost_usd=-1.0)
        assert "max_cost_usd must be non-negative" in str(exc.value)

    def test_warn_negative_raises(self):
        with pytest.raises(ValidationError) as exc:
            CostBudget(max_cost_usd=1.0, warn_cost_usd=-0.5)
        assert "warn_cost_usd must be non-negative" in str(exc.value)

    def test_warn_greater_than_max_raises(self):
        with pytest.raises(ValidationError) as exc:
            CostBudget(max_cost_usd=1.0, warn_cost_usd=1.5)
        assert "warn_cost_usd must be <= max_cost_usd" in str(exc.value)

    def test_warn_equal_to_max_is_valid(self):
        cb = CostBudget(max_cost_usd=1.0, warn_cost_usd=1.0)
        assert cb.warn_cost_usd == 1.0


class TestRuntimeBudget:
    def test_valid(self):
        rb = RuntimeBudget(max_runtime_seconds=120, max_steps=12, max_retries=2)
        assert rb.max_runtime_seconds == 120
        assert rb.max_steps == 12
        assert rb.max_retries == 2

    def test_zero_runtime_raises(self):
        with pytest.raises(ValidationError) as exc:
            RuntimeBudget(max_runtime_seconds=0, max_steps=12, max_retries=2)
        assert "must be at least 1" in str(exc.value)

    def test_zero_steps_raises(self):
        with pytest.raises(ValidationError) as exc:
            RuntimeBudget(max_runtime_seconds=120, max_steps=0, max_retries=2)
        assert "must be at least 1" in str(exc.value)

    def test_retries_negative_raises(self):
        with pytest.raises(ValidationError) as exc:
            RuntimeBudget(max_runtime_seconds=120, max_steps=12, max_retries=-1)
        assert "max_retries must be non-negative" in str(exc.value)

    def test_retries_zero_is_valid(self):
        rb = RuntimeBudget(max_runtime_seconds=120, max_steps=12, max_retries=0)
        assert rb.max_retries == 0


class TestToolCallBudget:
    def test_valid(self):
        tcb = ToolCallBudget(max_total_tool_calls=20, max_tool_calls_per_tool=8)
        assert tcb.max_total_tool_calls == 20
        assert tcb.max_tool_calls_per_tool == 8

    def test_with_restricted_tools(self):
        tcb = ToolCallBudget(
            max_total_tool_calls=20,
            max_tool_calls_per_tool=8,
            restricted_tools=["edit_file", "delete_file"],
        )
        assert "edit_file" in tcb.restricted_tools

    def test_zero_total_raises(self):
        with pytest.raises(ValidationError) as exc:
            ToolCallBudget(max_total_tool_calls=0, max_tool_calls_per_tool=8)
        assert "must be at least 1" in str(exc.value)

    def test_zero_per_tool_raises(self):
        with pytest.raises(ValidationError) as exc:
            ToolCallBudget(max_total_tool_calls=20, max_tool_calls_per_tool=0)
        assert "must be at least 1" in str(exc.value)


class TestRateLimitRule:
    def test_valid(self):
        rule = RateLimitRule(
            scope=BudgetScope.USER,
            window=RateWindow.PER_HOUR,
            identifier_key="user-abc",
            max_requests=100,
            action_on_exceed=LimitAction.BLOCK,
        )
        assert rule.scope == BudgetScope.USER
        assert rule.max_requests == 100

    def test_with_token_limit(self):
        rule = RateLimitRule(
            scope=BudgetScope.TENANT,
            window=RateWindow.PER_DAY,
            identifier_key="tenant-xyz",
            max_tokens=500000,
            action_on_exceed=LimitAction.THROTTLE,
        )
        assert rule.max_tokens == 500000

    def test_empty_identifier_raises(self):
        with pytest.raises(ValidationError) as exc:
            RateLimitRule(
                scope=BudgetScope.RUN,
                window=RateWindow.PER_RUN,
                identifier_key="  ",
                action_on_exceed=LimitAction.BLOCK,
            )
        assert "identifier_key must not be empty" in str(exc.value)

    def test_max_requests_zero_raises(self):
        with pytest.raises(ValidationError) as exc:
            RateLimitRule(
                scope=BudgetScope.RUN,
                window=RateWindow.PER_RUN,
                identifier_key="test",
                max_requests=0,
                action_on_exceed=LimitAction.BLOCK,
            )
        assert "must be at least 1 if provided" in str(exc.value)

    def test_max_tokens_zero_raises(self):
        with pytest.raises(ValidationError) as exc:
            RateLimitRule(
                scope=BudgetScope.RUN,
                window=RateWindow.PER_RUN,
                identifier_key="test",
                max_tokens=0,
                action_on_exceed=LimitAction.BLOCK,
            )
        assert "must be at least 1 if provided" in str(exc.value)

    def test_negative_cost_raises(self):
        with pytest.raises(ValidationError) as exc:
            RateLimitRule(
                scope=BudgetScope.RUN,
                window=RateWindow.PER_RUN,
                identifier_key="test",
                max_cost_usd=-0.5,
                action_on_exceed=LimitAction.BLOCK,
            )
        assert "max_cost_usd must be non-negative" in str(exc.value)


class TestBudgetPolicy:
    def test_valid_policy(self):
        policy = make_policy()
        assert policy.policy_id == "policy-run-001"

    def test_empty_policy_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_policy(policy_id="  ")
        assert "policy_id must not be empty" in str(exc.value)

    def test_with_rate_limit_rules(self):
        policy = make_policy(
            rate_limit_rules=[
                RateLimitRule(
                    scope=BudgetScope.USER,
                    window=RateWindow.PER_HOUR,
                    identifier_key="user-1",
                    max_requests=50,
                    action_on_exceed=LimitAction.THROTTLE,
                ),
            ]
        )
        assert len(policy.rate_limit_rules) == 1
        assert policy.rate_limit_rules[0].action_on_exceed == LimitAction.THROTTLE


class TestBudgetUsageSnapshot:
    def test_defaults(self):
        snapshot = BudgetUsageSnapshot(run_id="run-001")
        assert snapshot.run_id == "run-001"
        assert snapshot.input_tokens_used == 0
        assert snapshot.cost_usd_used == 0.0
        assert snapshot.steps_used == 0
        assert snapshot.tool_calls_used == 0

    def test_partial_usage(self):
        snapshot = BudgetUsageSnapshot(
            run_id="run-002",
            input_tokens_used=15000,
            output_tokens_used=5000,
            total_tokens_used=20000,
            cost_usd_used=0.35,
            steps_used=4,
            tool_calls_used=6,
        )
        assert snapshot.input_tokens_used == 15000
        assert snapshot.cost_usd_used == 0.35

    def test_empty_run_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            BudgetUsageSnapshot(run_id="  ")
        assert "run_id must not be empty" in str(exc.value)

    def test_negative_tokens_raises(self):
        with pytest.raises(ValidationError) as exc:
            BudgetUsageSnapshot(run_id="r", input_tokens_used=-1)
        assert "must be non-negative" in str(exc.value)

    def test_negative_cost_raises(self):
        with pytest.raises(ValidationError) as exc:
            BudgetUsageSnapshot(run_id="r", cost_usd_used=-0.1)
        assert "cost_usd_used must be non-negative" in str(exc.value)

    def test_negative_steps_raises(self):
        with pytest.raises(ValidationError) as exc:
            BudgetUsageSnapshot(run_id="r", steps_used=-1)
        assert "must be non-negative" in str(exc.value)

    def test_negative_retries_raises(self):
        with pytest.raises(ValidationError) as exc:
            BudgetUsageSnapshot(run_id="r", retries_used=-1)
        assert "must be non-negative" in str(exc.value)

    def test_negative_tool_calls_raises(self):
        with pytest.raises(ValidationError) as exc:
            BudgetUsageSnapshot(run_id="r", tool_calls_used=-1)
        assert "must be non-negative" in str(exc.value)


class TestBudgetDecision:
    def test_allowed_decision(self):
        decision = BudgetDecision(
            decision_id="dec-001",
            run_id="run-001",
            allowed=True,
            action=LimitAction.ALLOW,
            reason="within all budgets",
        )
        assert decision.allowed is True

    def test_blocked_decision(self):
        decision = BudgetDecision(
            decision_id="dec-002",
            run_id="run-001",
            allowed=False,
            action=LimitAction.BLOCK,
            reason="exceeded max_cost_usd",
            violated_rules=["cost_budget.max_cost_usd"],
        )
        assert decision.allowed is False
        assert len(decision.violated_rules) == 1

    def test_warn_decision(self):
        decision = BudgetDecision(
            decision_id="dec-003",
            run_id="run-002",
            allowed=True,
            action=LimitAction.WARN,
            reason="approaching max_cost_usd",
            violated_rules=["cost_budget.warn_cost_usd"],
        )
        assert decision.action == LimitAction.WARN

    def test_empty_decision_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            BudgetDecision(
                decision_id="  ",
                run_id="run-001",
                allowed=True,
                action=LimitAction.ALLOW,
                reason="ok",
            )
        assert "must not be empty" in str(exc.value)

    def test_empty_run_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            BudgetDecision(
                decision_id="dec-001",
                run_id="  ",
                allowed=True,
                action=LimitAction.ALLOW,
                reason="ok",
            )
        assert "must not be empty" in str(exc.value)

    def test_allowed_false_with_action_allow_raises(self):
        with pytest.raises(ValidationError) as exc:
            BudgetDecision(
                decision_id="dec-004",
                run_id="run-001",
                allowed=False,
                action=LimitAction.ALLOW,
                reason="inconsistent",
            )
        assert "allowed=False and action=ALLOW are inconsistent" in str(exc.value)


class TestBudgetViolation:
    def test_valid_violation(self):
        violation = BudgetViolation(
            rule_id="cost_budget.max_cost_usd",
            run_id="run-001",
            scope=BudgetScope.RUN,
            observed_value=1.5,
            allowed_value=1.0,
            action_taken=LimitAction.BLOCK,
        )
        assert violation.rule_id == "cost_budget.max_cost_usd"
        assert violation.observed_value == 1.5
        assert violation.allowed_value == 1.0

    def test_throttle_violation(self):
        violation = BudgetViolation(
            rule_id="rate_limit.max_requests",
            run_id="run-002",
            scope=BudgetScope.USER,
            observed_value=55.0,
            allowed_value=50.0,
            action_taken=LimitAction.THROTTLE,
        )
        assert violation.action_taken == LimitAction.THROTTLE

    def test_empty_rule_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            BudgetViolation(
                rule_id="  ",
                run_id="run-001",
                scope=BudgetScope.RUN,
                observed_value=1.5,
                allowed_value=1.0,
                action_taken=LimitAction.BLOCK,
            )
        assert "must not be empty" in str(exc.value)

    def test_negative_observed_value_raises(self):
        with pytest.raises(ValidationError) as exc:
            BudgetViolation(
                rule_id="cost",
                run_id="run-001",
                scope=BudgetScope.RUN,
                observed_value=-1.0,
                allowed_value=1.0,
                action_taken=LimitAction.BLOCK,
            )
        assert "must be non-negative" in str(exc.value)

    def test_negative_allowed_value_raises(self):
        with pytest.raises(ValidationError) as exc:
            BudgetViolation(
                rule_id="cost",
                run_id="run-001",
                scope=BudgetScope.RUN,
                observed_value=1.0,
                allowed_value=-1.0,
                action_taken=LimitAction.BLOCK,
            )
        assert "must be non-negative" in str(exc.value)


class TestSerialization:
    def test_policy_to_json(self):
        policy = make_policy()
        json_str = policy.model_dump_json()
        assert "policy-run-001" in json_str
        assert "32000" in json_str

    def test_decision_roundtrip(self):
        decision = BudgetDecision(
            decision_id="dec-001",
            run_id="run-001",
            allowed=True,
            action=LimitAction.ALLOW,
            reason="within limits",
        )
        dumped = decision.model_dump()
        assert dumped["action"] == "allow"
        assert dumped["allowed"] is True

    def test_violation_roundtrip(self):
        violation = BudgetViolation(
            rule_id="steps",
            run_id="run-001",
            scope=BudgetScope.RUN,
            observed_value=15.0,
            allowed_value=12.0,
            action_taken=LimitAction.WARN,
        )
        dumped = violation.model_dump()
        assert dumped["observed_value"] == 15.0
