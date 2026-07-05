import pytest
from datetime import datetime, timedelta
from models.execution_budget_resource_contract import (
    BudgetScopeType, ResourceType, BudgetStatus, LimitSeverity,
    OverrunDisposition,
    ExecutionBudgetEnvelope, ResourceBudgetLine,
    ResourceReservationRecord, ResourceUsageRecord,
    BudgetThresholdPolicy, BudgetAlertRecord, BudgetDecisionRecord,
    BudgetResourceEnvelope,
)


# ── Helpers ──────────────────────────────────────────────────────────────

def make_budget(**kw):
    return ExecutionBudgetEnvelope(
        budget_id=kw.get("bid", "budget-001"),
        scope_type=kw.get("scope", BudgetScopeType.task),
        scope_ref=kw.get("ref", "task-001"),
        parent_budget_id=kw.get("parent"),
        budget_status=kw.get("status", BudgetStatus.active),
    )


def make_budget_line(allocated=1000.0, reserved=0.0, consumed=0.0, **kw):
    remaining = allocated - reserved - consumed
    return ResourceBudgetLine(
        budget_line_id=kw.get("blid", "bl-001"),
        budget_id=kw.get("bid", "budget-001"),
        resource_type=kw.get("rtype", ResourceType.tokens),
        allocated_amount=allocated,
        reserved_amount=reserved,
        consumed_amount=consumed,
        remaining_amount=remaining,
        unit=kw.get("unit", "tokens"),
    )


def make_reservation(**kw):
    return ResourceReservationRecord(
        reservation_id=kw.get("rid", "res-001"),
        budget_line_id=kw.get("blid", "bl-001"),
        reserved_amount=kw.get("amount", 200.0),
        reservation_reason=kw.get("reason", "Pre-execution reservation"),
    )


def make_usage(**kw):
    return ResourceUsageRecord(
        usage_id=kw.get("uid", "usage-001"),
        budget_line_id=kw.get("blid", "bl-001"),
        resource_type=kw.get("rtype", ResourceType.tokens),
        consumed_amount=kw.get("amount", 150.0),
    )


def make_threshold(**kw):
    return BudgetThresholdPolicy(
        threshold_policy_id=kw.get("tpid", "tp-001"),
        budget_line_id=kw.get("blid", "bl-001"),
        limit_severity=kw.get("severity", LimitSeverity.soft),
        threshold_value=kw.get("value", 800.0),
        threshold_percent=kw.get("pct"),
        action_on_cross=kw.get("action", "log_warning"),
    )


def make_alert(**kw):
    return BudgetAlertRecord(
        alert_id=kw.get("aid", "alert-001"),
        budget_line_id=kw.get("blid", "bl-001"),
        limit_severity=kw.get("severity", LimitSeverity.soft),
        trigger_value=kw.get("trigger", 850.0),
        remaining_amount=kw.get("remaining", 150.0),
        recommended_action=kw.get("action", "reduce token usage"),
    )


def make_decision(**kw):
    return BudgetDecisionRecord(
        decision_id=kw.get("did", "dec-001"),
        budget_id=kw.get("bid", "budget-001"),
        overrun_disposition=kw.get("disp", OverrunDisposition.continue_with_warning),
        decision_reason=kw.get("reason", "Minor overrun acceptable"),
        approved_by=kw.get("approver"),
        reallocated_from_budget_id=kw.get("source"),
        additional_amount=kw.get("additional"),
    )


def make_envelope(**kw):
    budget = kw.get("budget") or make_budget()
    bl = kw.get("budget_lines") or [make_budget_line(bid=budget.budget_id)]
    reservations = kw.get("reservations", [])
    usage = kw.get("usage", [])
    thresholds = kw.get("thresholds", [])
    alerts = kw.get("alerts", [])
    decisions = kw.get("decisions", [])
    return BudgetResourceEnvelope(
        envelope_id=kw.get("eid", "env-budget-001"),
        budget=budget,
        budget_lines=bl,
        reservations=reservations,
        usage_records=usage,
        threshold_policies=thresholds,
        alerts=alerts,
        decisions=decisions,
    )


# ── Tests ────────────────────────────────────────────────────────────────

class TestBudgetScopeType:
    def test_all_values(self):
        assert len(BudgetScopeType) == 8
        assert BudgetScopeType.session.value == "session"
        assert BudgetScopeType.run.value == "run"
        assert BudgetScopeType.task.value == "task"
        assert BudgetScopeType.agent.value == "agent"
        assert BudgetScopeType.role.value == "role"
        assert BudgetScopeType.branch.value == "branch"
        assert BudgetScopeType.tool_call.value == "tool_call"
        assert BudgetScopeType.model_call.value == "model_call"


class TestResourceType:
    def test_all_values(self):
        assert len(ResourceType) == 8
        assert ResourceType.tokens.value == "tokens"
        assert ResourceType.compute_time_ms.value == "compute_time_ms"
        assert ResourceType.wall_clock_ms.value == "wall_clock_ms"
        assert ResourceType.currency_cost.value == "currency_cost"
        assert ResourceType.tool_invocations.value == "tool_invocations"
        assert ResourceType.network_calls.value == "network_calls"
        assert ResourceType.parallel_slots.value == "parallel_slots"
        assert ResourceType.memory_mb.value == "memory_mb"


class TestBudgetStatus:
    def test_all_values(self):
        assert len(BudgetStatus) == 7
        assert BudgetStatus.planned.value == "planned"
        assert BudgetStatus.active.value == "active"
        assert BudgetStatus.warning.value == "warning"
        assert BudgetStatus.exhausted.value == "exhausted"
        assert BudgetStatus.overrun.value == "overrun"
        assert BudgetStatus.closed.value == "closed"
        assert BudgetStatus.cancelled.value == "cancelled"


class TestLimitSeverity:
    def test_all_values(self):
        assert len(LimitSeverity) == 2
        assert LimitSeverity.soft.value == "soft"
        assert LimitSeverity.hard.value == "hard"


class TestOverrunDisposition:
    def test_all_values(self):
        assert len(OverrunDisposition) == 5
        assert OverrunDisposition.continue_with_warning.value == "continue_with_warning"
        assert OverrunDisposition.throttle.value == "throttle"
        assert OverrunDisposition.require_approval.value == "require_approval"
        assert OverrunDisposition.reallocate.value == "reallocate"
        assert OverrunDisposition.stop_execution.value == "stop_execution"


class TestExecutionBudgetEnvelope:
    def test_valid_budget(self):
        b = make_budget()
        assert b.budget_id == "budget-001"
        assert b.budget_status == BudgetStatus.active

    def test_blank_budget_id_raises(self):
        with pytest.raises(ValueError):
            make_budget(bid="  ")

    def test_blank_scope_ref_raises(self):
        with pytest.raises(ValueError):
            make_budget(ref="  ")

    def test_default_status_planned(self):
        b = ExecutionBudgetEnvelope(
            budget_id="budget-002",
            scope_type=BudgetScopeType.task,
            scope_ref="task-002",
        )
        assert b.budget_status == BudgetStatus.planned

    def test_all_scope_types(self):
        for st in BudgetScopeType:
            b = make_budget(scope=st)
            assert b.scope_type == st

    def test_parent_budget_optional(self):
        b = make_budget(parent="budget-000")
        assert b.parent_budget_id == "budget-000"

    def test_planning_execution_refs_optional(self):
        b = make_budget()
        assert b.planning_budget_ref is None
        assert b.execution_budget_ref is None


class TestResourceBudgetLine:
    def test_valid_line(self):
        bl = make_budget_line()
        assert bl.budget_line_id == "bl-001"

    def test_blank_line_id_raises(self):
        with pytest.raises(ValueError):
            make_budget_line(blid="  ")

    def test_blank_budget_id_raises(self):
        with pytest.raises(ValueError):
            make_budget_line(bid="  ")

    def test_blank_unit_raises(self):
        with pytest.raises(ValueError):
            make_budget_line(unit="  ")

    def test_negative_allocated_raises(self):
        with pytest.raises(ValueError):
            make_budget_line(allocated=-1.0)

    def test_negative_reserved_raises(self):
        with pytest.raises(ValueError):
            make_budget_line(reserved=-1.0)

    def test_negative_consumed_raises(self):
        with pytest.raises(ValueError):
            make_budget_line(consumed=-1.0)

    def test_remaining_consistency_raises(self):
        with pytest.raises(ValueError):
            ResourceBudgetLine(
                budget_line_id="bl-002",
                budget_id="budget-001",
                resource_type=ResourceType.tokens,
                allocated_amount=1000.0,
                reserved_amount=200.0,
                consumed_amount=300.0,
                remaining_amount=999.0,
                unit="tokens",
            )

    def test_remaining_auto_matches(self):
        bl = make_budget_line(allocated=1000.0, reserved=200.0, consumed=300.0)
        assert bl.remaining_amount == 500.0

    def test_all_resource_types(self):
        for rt in ResourceType:
            bl = make_budget_line(rtype=rt)
            assert bl.resource_type == rt

    def test_nan_amount_raises(self):
        with pytest.raises(ValueError):
            make_budget_line(allocated=float("nan"))

    def test_inf_amount_raises(self):
        with pytest.raises(ValueError):
            make_budget_line(allocated=float("inf"))


class TestResourceReservationRecord:
    def test_valid_reservation(self):
        r = make_reservation()
        assert r.reservation_id == "res-001"

    def test_blank_reservation_id_raises(self):
        with pytest.raises(ValueError):
            make_reservation(rid="  ")

    def test_blank_budget_line_id_raises(self):
        with pytest.raises(ValueError):
            make_reservation(blid="  ")

    def test_negative_reserved_amount_raises(self):
        with pytest.raises(ValueError):
            make_reservation(amount=-1.0)

    def test_nan_reserved_amount_raises(self):
        with pytest.raises(ValueError):
            make_reservation(amount=float("nan"))

    def test_expires_at_optional(self):
        r = make_reservation()
        assert r.expires_at is None

    def test_request_ref_optional(self):
        r = make_reservation()
        assert r.request_ref is None


class TestResourceUsageRecord:
    def test_valid_usage(self):
        u = make_usage()
        assert u.usage_id == "usage-001"

    def test_blank_usage_id_raises(self):
        with pytest.raises(ValueError):
            make_usage(uid="  ")

    def test_blank_budget_line_id_raises(self):
        with pytest.raises(ValueError):
            make_usage(blid="  ")

    def test_negative_consumed_raises(self):
        with pytest.raises(ValueError):
            make_usage(amount=-1.0)

    def test_nan_consumed_raises(self):
        with pytest.raises(ValueError):
            make_usage(amount=float("nan"))

    def test_context_refs_optional(self):
        u = make_usage()
        assert u.usage_context_ref is None
        assert u.actor_ref is None
        assert u.source_event_ref is None


class TestBudgetThresholdPolicy:
    def test_valid_threshold(self):
        tp = make_threshold()
        assert tp.threshold_policy_id == "tp-001"

    def test_blank_policy_id_raises(self):
        with pytest.raises(ValueError):
            make_threshold(tpid="  ")

    def test_blank_budget_line_id_raises(self):
        with pytest.raises(ValueError):
            make_threshold(blid="  ")

    def test_blank_action_raises(self):
        with pytest.raises(ValueError):
            make_threshold(action="  ")

    def test_hard_threshold_requires_action(self):
        with pytest.raises(ValueError):
            BudgetThresholdPolicy(
                threshold_policy_id="tp-002",
                budget_line_id="bl-001",
                limit_severity=LimitSeverity.hard,
                threshold_value=1000.0,
                action_on_cross="  ",
            )

    def test_must_have_value_or_percent(self):
        with pytest.raises(ValueError):
            BudgetThresholdPolicy(
                threshold_policy_id="tp-003",
                budget_line_id="bl-001",
                limit_severity=LimitSeverity.soft,
                action_on_cross="log",
            )

    def test_threshold_by_value(self):
        tp = make_threshold(value=800.0, pct=None)
        assert tp.threshold_value == 800.0

    def test_threshold_by_percent(self):
        tp = make_threshold(value=None, pct=80.0)
        assert tp.threshold_percent == 80.0

    def test_negative_threshold_value_raises(self):
        with pytest.raises(ValueError):
            make_threshold(value=-1.0)

    def test_percent_out_of_range_raises(self):
        with pytest.raises(ValueError):
            make_threshold(value=None, pct=101.0)

    def test_notification_targets_default_empty(self):
        tp = make_threshold()
        assert tp.notification_targets == []


class TestBudgetAlertRecord:
    def test_valid_alert(self):
        a = make_alert()
        assert a.alert_id == "alert-001"

    def test_blank_alert_id_raises(self):
        with pytest.raises(ValueError):
            make_alert(aid="  ")

    def test_blank_budget_line_id_raises(self):
        with pytest.raises(ValueError):
            make_alert(blid="  ")

    def test_negative_trigger_raises(self):
        with pytest.raises(ValueError):
            make_alert(trigger=-1.0)

    def test_negative_remaining_allowed_for_overrun(self):
        a = make_alert(remaining=-1.0)
        assert a.remaining_amount == -1.0


class TestBudgetDecisionRecord:
    def test_valid_decision(self):
        d = make_decision()
        assert d.decision_id == "dec-001"

    def test_blank_decision_id_raises(self):
        with pytest.raises(ValueError):
            make_decision(did="  ")

    def test_blank_budget_id_raises(self):
        with pytest.raises(ValueError):
            make_decision(bid="  ")

    def test_reallocate_requires_source(self):
        with pytest.raises(ValueError):
            make_decision(
                disp=OverrunDisposition.reallocate,
                source=None,
            )

    def test_reallocate_with_source_ok(self):
        d = make_decision(
            disp=OverrunDisposition.reallocate,
            source="budget-002",
        )
        assert d.reallocated_from_budget_id == "budget-002"

    def test_negative_additional_raises(self):
        with pytest.raises(ValueError):
            make_decision(additional=-1.0)

    def test_effective_until_optional(self):
        d = make_decision()
        assert d.effective_until is None


class TestBudgetResourceEnvelope:
    def test_valid_envelope(self):
        env = make_envelope()
        assert env.envelope_id == "env-budget-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValueError):
            make_envelope(eid="  ")

    def test_budget_line_budget_id_mismatch_raises(self):
        bl = make_budget_line(bid="budget-999")
        with pytest.raises(ValueError):
            make_envelope(budget_lines=[bl])

    def test_reservation_references_unknown_budget_line_raises(self):
        res = make_reservation(blid="bl-999")
        with pytest.raises(ValueError):
            make_envelope(reservations=[res])

    def test_usage_references_unknown_budget_line_raises(self):
        u = make_usage(blid="bl-999")
        with pytest.raises(ValueError):
            make_envelope(usage=[u])

    def test_threshold_references_unknown_budget_line_raises(self):
        tp = make_threshold(blid="bl-999")
        with pytest.raises(ValueError):
            make_envelope(thresholds=[tp])

    def test_alert_references_unknown_budget_line_raises(self):
        a = make_alert(blid="bl-999")
        with pytest.raises(ValueError):
            make_envelope(alerts=[a])

    def test_decision_references_wrong_budget_raises(self):
        d = make_decision(bid="budget-999")
        with pytest.raises(ValueError):
            make_envelope(decisions=[d])

    def test_decision_references_correct_budget_ok(self):
        d = make_decision(bid="budget-001")
        env = make_envelope(decisions=[d])
        assert len(env.decisions) == 1

    def test_reservation_references_valid_budget_line_ok(self):
        bl = make_budget_line()
        res = make_reservation(blid=bl.budget_line_id)
        env = make_envelope(budget_lines=[bl], reservations=[res])
        assert len(env.reservations) == 1

    def test_threshold_references_valid_budget_line_ok(self):
        bl = make_budget_line()
        tp = make_threshold(blid=bl.budget_line_id)
        env = make_envelope(budget_lines=[bl], thresholds=[tp])
        assert len(env.threshold_policies) == 1

    def test_multiple_budget_lines(self):
        bl1 = make_budget_line(blid="bl-001", allocated=1000.0)
        bl2 = make_budget_line(blid="bl-002", allocated=2000.0, rtype=ResourceType.compute_time_ms, unit="ms")
        env = make_envelope(budget_lines=[bl1, bl2])
        assert len(env.budget_lines) == 2


class TestExampleScenarios:
    def test_task_level_token_and_cost_budget(self):
        budget = ExecutionBudgetEnvelope(
            budget_id="budget-task-001",
            scope_type=BudgetScopeType.task,
            scope_ref="task-042",
            budget_status=BudgetStatus.active,
        )
        bl_tokens = ResourceBudgetLine(
            budget_line_id="bl-tokens",
            budget_id="budget-task-001",
            resource_type=ResourceType.tokens,
            allocated_amount=50000.0,
            reserved_amount=10000.0,
            consumed_amount=25000.0,
            remaining_amount=15000.0,
            unit="tokens",
        )
        bl_cost = ResourceBudgetLine(
            budget_line_id="bl-cost",
            budget_id="budget-task-001",
            resource_type=ResourceType.currency_cost,
            allocated_amount=0.50,
            reserved_amount=0.10,
            consumed_amount=0.25,
            remaining_amount=0.15,
            unit="usd",
        )
        env = make_envelope(budget=budget, budget_lines=[bl_tokens, bl_cost])
        assert env.budget.budget_id == "budget-task-001"
        assert len(env.budget_lines) == 2

    def test_branch_level_reallocation_from_parent(self):
        parent = ExecutionBudgetEnvelope(
            budget_id="budget-parent",
            scope_type=BudgetScopeType.run,
            scope_ref="run-001",
            budget_status=BudgetStatus.active,
        )
        branch_budget = ExecutionBudgetEnvelope(
            budget_id="budget-branch",
            scope_type=BudgetScopeType.branch,
            scope_ref="branch-003",
            parent_budget_id="budget-parent",
            budget_status=BudgetStatus.active,
        )
        bl_branch = ResourceBudgetLine(
            budget_line_id="bl-branch-tokens",
            budget_id="budget-branch",
            resource_type=ResourceType.tokens,
            allocated_amount=20000.0,
            reserved_amount=5000.0,
            consumed_amount=18000.0,
            remaining_amount=-3000.0,
            unit="tokens",
        )
        decision = BudgetDecisionRecord(
            decision_id="dec-realloc",
            budget_id="budget-branch",
            overrun_disposition=OverrunDisposition.reallocate,
            decision_reason="Branch exceeded token budget, reallocating from parent",
            approved_by="manager-alpha",
            reallocated_from_budget_id="budget-parent",
            additional_amount=5000.0,
        )
        env = BudgetResourceEnvelope(
            envelope_id="env-branch-realloc",
            budget=branch_budget,
            budget_lines=[bl_branch],
            decisions=[decision],
        )
        assert env.decisions[0].overrun_disposition == OverrunDisposition.reallocate
        assert env.decisions[0].reallocated_from_budget_id == "budget-parent"

    def test_hard_threshold_stop_execution(self):
        budget = make_budget(bid="budget-hardstop")
        bl = make_budget_line(bid="budget-hardstop", blid="bl-hard", allocated=1000.0)
        tp = BudgetThresholdPolicy(
            threshold_policy_id="tp-hard",
            budget_line_id="bl-hard",
            limit_severity=LimitSeverity.hard,
            threshold_value=1000.0,
            action_on_cross="stop_execution",
        )
        alert = BudgetAlertRecord(
            alert_id="alert-hard",
            budget_line_id="bl-hard",
            limit_severity=LimitSeverity.hard,
            trigger_value=1000.0,
            remaining_amount=0.0,
            recommended_action="stop_execution",
        )
        env = make_envelope(
            budget=budget,
            budget_lines=[bl],
            thresholds=[tp],
            alerts=[alert],
        )
        assert env.threshold_policies[0].action_on_cross == "stop_execution"
        assert env.alerts[0].remaining_amount == 0.0

    def test_planning_budget_separate_from_execution(self):
        budget = ExecutionBudgetEnvelope(
            budget_id="budget-plan-exec",
            scope_type=BudgetScopeType.task,
            scope_ref="task-099",
            budget_status=BudgetStatus.active,
            planning_budget_ref="plan-budget-001",
            execution_budget_ref="exec-budget-001",
        )
        assert budget.planning_budget_ref == "plan-budget-001"
        assert budget.execution_budget_ref == "exec-budget-001"

    def test_warning_alert_followed_by_approved_increase(self):
        budget = make_budget(bid="budget-warn")
        bl = make_budget_line(bid="budget-warn", blid="bl-warn", allocated=1000.0)
        alert = BudgetAlertRecord(
            alert_id="alert-warn",
            budget_line_id="bl-warn",
            limit_severity=LimitSeverity.soft,
            trigger_value=900.0,
            remaining_amount=100.0,
            recommended_action="request_budget_increase",
        )
        decision = BudgetDecisionRecord(
            decision_id="dec-increase",
            budget_id="budget-warn",
            overrun_disposition=OverrunDisposition.require_approval,
            decision_reason="Approved budget increase after warning alert",
            approved_by="manager-alpha",
            additional_amount=500.0,
        )
        env = make_envelope(
            budget=budget,
            budget_lines=[bl],
            alerts=[alert],
            decisions=[decision],
        )
        assert env.alerts[0].remaining_amount == 100.0
        assert env.decisions[0].approved_by == "manager-alpha"
        assert env.decisions[0].additional_amount == 500.0
