from uuid import uuid4
import pytest
from pydantic import ValidationError

from models.task_contract import (
    TaskContract, TaskType, TaskScope, TaskInputs, TaskConstraints,
    ToolName, SuccessCriterion, VerificationKind,
)
from models.tool_interface import ToolInvocation, ToolResult, ToolStatus
from models.approval_safety import (
    ApprovalSafetyPolicy, ApprovalRequirement, ActionRiskRule, ResourceType, RiskLevel, SafetyAction,
)
from models.observability_trace import TraceEventStatus, PolicyOutcomeType, StepType
from harness.pipeline import PipelineExecutor, PipelineInput, ExecutorConfig, PipelineResult
from harness.state_driver import StateDriver, RunState as FsmState


def minimal_contract(**overrides) -> TaskContract:
    kwargs = dict(
        task_id="test-task",
        title="Test task",
        task_type=TaskType.FEATURE,
        goal="Write a Python function.",
        scope=TaskScope(repo_path="/workspace", allowed_paths=["solution.py"]),
        inputs=TaskInputs(user_request="Write add(a,b) function.", relevant_files=["solution.py"]),
            constraints=TaskConstraints(max_files_changed=1, max_retries=1, allow_dependency_changes=True),
            tools_allowed=[ToolName.EDIT_FILE],
        success_criteria=[SuccessCriterion(kind=VerificationKind.TEST, target="pytest")],
    )
    kwargs.update(overrides)
    return TaskContract(**kwargs)


def executor(**kw) -> PipelineExecutor:
    return PipelineExecutor(config=ExecutorConfig(**kw))


class TestSuccessPath:
    def test_basic_success(self):
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-test-1")
        result = executor().run(inp)
        assert result.success is True
        assert result.terminal_state == FsmState.SUCCEEDED.value
        assert result.error is None

    def test_four_steps_produced(self):
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-test-2")
        result = executor().run(inp)
        assert len(result.steps) == 4
        types = [s.step_type for s in result.steps]
        assert types == [
            StepType.PROMPT_ASSEMBLY,
            StepType.POLICY_CHECK,
            StepType.TOOL_EXECUTION,
            StepType.VERIFICATION,
        ]

    def test_all_steps_success_or_skipped(self):
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-test-3")
        result = executor().run(inp)
        for step in result.steps:
            assert step.status in (TraceEventStatus.SUCCESS, TraceEventStatus.SKIPPED), f"step {step.step_index} had status {step.status}"

    def test_run_trace_produced(self):
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-test-4")
        result = executor().run(inp)
        rt = result.run_trace
        assert rt.run_id == "run-test-4"
        assert rt.task_id == "test-task"
        assert len(rt.steps) == 4
        assert rt.terminal_status == TraceEventStatus.SUCCESS
        assert rt.summary is not None
        assert rt.summary.total_steps == 4

    def test_benchmark_run_produced(self):
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-test-5")
        result = executor().run(inp)
        bm = result.benchmark_run
        assert bm is not None
        assert bm.task_id == "test-task"
        assert bm.verdict.value == "pass"

    def test_driver_tracks_history(self):
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-test-6")
        result = executor().run(inp)
        assert len(result.run_trace.steps) > 0

    def test_all_terminal_fields_set(self):
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-test-7")
        result = executor().run(inp)
        assert result.run_trace.finished_at is not None
        assert result.run_trace.started_at is not None
        for s in result.run_trace.steps:
            assert s.finished_at is not None
            assert s.latency_seconds is not None


class TestBlockedByPolicy:
    def test_blocking_policy_returns_failure(self):
        policy = ApprovalSafetyPolicy(
            policy_id="block-all",
            rules=[ActionRiskRule(
                rule_id="block-mock", action_name="mock_tool",
                resource_type=ResourceType.FILESYSTEM,
                risk_level=RiskLevel.CRITICAL, safety_action=SafetyAction.BLOCK,
                rationale="testing block",
            )],
        )
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-block-1", safety_policy=policy)
        result = executor().run(inp)
        assert result.success is False
        assert result.error is None

    def test_blocked_step_status(self):
        policy = ApprovalSafetyPolicy(
            policy_id="block-all",
            rules=[ActionRiskRule(
                rule_id="block-mock", action_name="mock_tool",
                resource_type=ResourceType.FILESYSTEM,
                risk_level=RiskLevel.CRITICAL, safety_action=SafetyAction.BLOCK,
                rationale="testing block",
            )],
        )
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-block-2", safety_policy=policy)
        result = executor().run(inp)
        blocked_steps = [s for s in result.steps if s.status == TraceEventStatus.BLOCKED]
        assert len(blocked_steps) == 1
        assert blocked_steps[0].step_type == StepType.POLICY_CHECK

    def test_blocked_trace_terminal_status(self):
        policy = ApprovalSafetyPolicy(
            policy_id="block-all",
            rules=[ActionRiskRule(
                rule_id="block-mock", action_name="mock_tool",
                resource_type=ResourceType.FILESYSTEM,
                risk_level=RiskLevel.CRITICAL, safety_action=SafetyAction.BLOCK,
                rationale="testing block",
            )],
        )
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-block-3", safety_policy=policy)
        result = executor().run(inp)
        assert result.run_trace.terminal_status == TraceEventStatus.BLOCKED
        assert result.run_trace.summary.policy_blocks == 1

    def test_blocked_stops_after_two_steps(self):
        policy = ApprovalSafetyPolicy(
            policy_id="block-all",
            rules=[ActionRiskRule(
                rule_id="block-mock", action_name="mock_tool",
                resource_type=ResourceType.FILESYSTEM,
                risk_level=RiskLevel.CRITICAL, safety_action=SafetyAction.BLOCK,
                rationale="testing block",
            )],
        )
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-block-4", safety_policy=policy)
        result = executor().run(inp)
        assert len(result.steps) == 2  # prompt + policy, no tool or verif


class TestCustomToolExecutor:
    def test_custom_tool_result(self):
        def custom_exec(inv: ToolInvocation) -> ToolResult:
            return ToolResult(
                invocation_id=inv.invocation_id, tool_name=inv.tool_name,
                status=ToolStatus.SUCCESS, output={"content": "def test_foo():\n    assert True\n", "custom": True},
                artifacts=[], started_at="2024-01-01T00:00:00", finished_at="2024-01-01T00:00:01",
            )
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-custom-1")
        result = PipelineExecutor(tool_executor=custom_exec).run(inp)
        assert result.success is True
        tool_step = result.steps[2]
        assert tool_step.tool_result is not None
        assert tool_step.tool_result.output.get("custom") is True

    def test_tool_failure_propagates(self):
        def failing_exec(inv: ToolInvocation) -> ToolResult:
            return ToolResult(
                invocation_id=inv.invocation_id, tool_name=inv.tool_name,
                status=ToolStatus.ERROR, output={}, artifacts=[],
                error="mock failure",
                started_at="2024-01-01T00:00:00", finished_at="2024-01-01T00:00:01",
            )
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-fail-1")
        result = PipelineExecutor(tool_executor=failing_exec).run(inp)
        assert result.success is False
        assert "mock failure" in (result.error or "")


class TestApprovalRequired:
    def test_approval_required_path(self):
        policy = ApprovalSafetyPolicy(
            policy_id="approve-all",
            rules=[ActionRiskRule(
                rule_id="req-approval", action_name="mock_tool",
                resource_type=ResourceType.FILESYSTEM,
                risk_level=RiskLevel.HIGH, safety_action=SafetyAction.REQUIRE_APPROVAL,
                rationale="testing approval gate",
                approval_requirement=ApprovalRequirement(),
            )],
        )
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-approve-1", safety_policy=policy)
        result = executor().run(inp)
        assert result.success is True
        approval_steps = [s for s in result.steps if s.step_type == StepType.APPROVAL]
        assert len(approval_steps) == 1
        assert approval_steps[0].status == TraceEventStatus.SUCCESS

    def test_approval_trace_outcome(self):
        policy = ApprovalSafetyPolicy(
            policy_id="approve-all",
            rules=[ActionRiskRule(
                rule_id="req-approval", action_name="mock_tool",
                resource_type=ResourceType.FILESYSTEM,
                risk_level=RiskLevel.HIGH, safety_action=SafetyAction.REQUIRE_APPROVAL,
                rationale="testing",
                approval_requirement=ApprovalRequirement(),
            )],
        )
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-approve-2", safety_policy=policy)
        result = executor().run(inp)
        pt = result.steps[1].policy_trace
        assert pt is not None
        assert pt.outcome == PolicyOutcomeType.REQUIRED_APPROVAL


class TestConfig:
    def test_default_config(self):
        e = PipelineExecutor()
        assert e.config.max_steps == 10
        assert e.config.max_tool_calls == 20
        assert e.config.max_retries == 3

    def test_custom_config(self):
        e = PipelineExecutor(config=ExecutorConfig(max_steps=5, max_tool_calls=10, max_retries=1))
        assert e.config.max_steps == 5
        assert e.config.max_tool_calls == 10
        assert e.config.max_retries == 1


class TestTerminalState:
    def test_succeeded_state(self):
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-term-1")
        result = executor().run(inp)
        assert result.terminal_state == "succeeded"


class TestBenchmarkEmission:
    def test_success_benchmark_verdict_pass(self):
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-bm-1")
        result = executor().run(inp)
        assert result.benchmark_run.verdict.value == "pass"
        for m in result.benchmark_run.metrics:
            if m.metric_name.value == "task_success":
                assert m.value == 1.0
                assert m.passed is True

    def test_failure_benchmark_verdict_fail(self):
        def failing_exec(inv: ToolInvocation) -> ToolResult:
            return ToolResult(
                invocation_id=inv.invocation_id, tool_name=inv.tool_name,
                status=ToolStatus.ERROR, output={}, artifacts=[],
                error="mock failure",
                started_at="2024-01-01T00:00:00", finished_at="2024-01-01T00:00:01",
            )
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-bm-2")
        result = PipelineExecutor(tool_executor=failing_exec).run(inp)
        assert result.benchmark_run.verdict.value == "fail"


class TestVerification:
    def test_verification_passes_with_test_content(self):
        def good_exec(inv):
            return ToolResult(invocation_id=inv.invocation_id, tool_name=inv.tool_name, status=ToolStatus.SUCCESS,
                              output={"content": "def test_answer():\n    assert 42 == 42\n"}, artifacts=[],
                              started_at="now", finished_at="now")
        contract = minimal_contract(success_criteria=[SuccessCriterion(kind=VerificationKind.TEST, target="pytest")])
        inp = PipelineInput(task_contract=contract, run_id="run-verify-1")
        result = PipelineExecutor(tool_executor=good_exec).run(inp)
        assert result.success is True
        verif_step = result.steps[3]
        assert verif_step.verification_trace is not None
        assert verif_step.verification_trace.status == TraceEventStatus.SUCCESS

    def test_verification_fails_without_test_content(self):
        def bad_exec(inv):
            return ToolResult(invocation_id=inv.invocation_id, tool_name=inv.tool_name, status=ToolStatus.SUCCESS,
                              output={"content": "just a comment"}, artifacts=[],
                              started_at="now", finished_at="now")
        contract = minimal_contract(success_criteria=[SuccessCriterion(kind=VerificationKind.TEST, target="pytest")])
        inp = PipelineInput(task_contract=contract, run_id="run-verify-2")
        result = PipelineExecutor(tool_executor=bad_exec).run(inp)
        assert result.success is False
        verif_step = result.steps[3]
        assert verif_step.verification_trace is not None
        assert verif_step.verification_trace.status == TraceEventStatus.FAILURE

    def test_different_kinds_pass(self):
        contract = minimal_contract(success_criteria=[
            SuccessCriterion(kind=VerificationKind.LINT, target="pylint"),
            SuccessCriterion(kind=VerificationKind.DIFF_REVIEW, target="diff"),
        ])
        inp = PipelineInput(task_contract=contract, run_id="run-verify-3")
        result = executor().run(inp)
        assert result.success is True

    def test_mixed_pass_fail(self):
        def mixed_exec(inv):
            return ToolResult(invocation_id=inv.invocation_id, tool_name=inv.tool_name, status=ToolStatus.SUCCESS,
                              output={"content": "x = 1"}, artifacts=[],
                              started_at="now", finished_at="now")
        contract = minimal_contract(success_criteria=[
            SuccessCriterion(kind=VerificationKind.TEST, target="pytest"),
            SuccessCriterion(kind=VerificationKind.DIFF_REVIEW, target="diff"),
        ])
        inp = PipelineInput(task_contract=contract, run_id="run-verify-4")
        result = PipelineExecutor(tool_executor=mixed_exec).run(inp)
        assert result.success is False
        assert result.steps[3].verification_trace.status == TraceEventStatus.FAILURE

    def test_typecheck_kind(self):
        def tc_exec(inv):
            return ToolResult(invocation_id=inv.invocation_id, tool_name=inv.tool_name, status=ToolStatus.SUCCESS,
                              output={"content": "def add(a: int, b: int) -> int:\n    return a + b"}, artifacts=[],
                              started_at="now", finished_at="now")
        contract = minimal_contract(success_criteria=[SuccessCriterion(kind=VerificationKind.TYPECHECK, target="pyright")])
        inp = PipelineInput(task_contract=contract, run_id="run-verify-5")
        result = PipelineExecutor(tool_executor=tc_exec).run(inp)
        assert result.success is True

    def test_typecheck_kind_fails_without_types(self):
        def tc_bad_exec(inv):
            return ToolResult(invocation_id=inv.invocation_id, tool_name=inv.tool_name, status=ToolStatus.SUCCESS,
                              output={"content": "def add(a, b):\n    return a + b"}, artifacts=[],
                              started_at="now", finished_at="now")
        contract = minimal_contract(success_criteria=[SuccessCriterion(kind=VerificationKind.TYPECHECK, target="pyright")])
        inp = PipelineInput(task_contract=contract, run_id="run-verify-6")
        result = PipelineExecutor(tool_executor=tc_bad_exec).run(inp)
        assert result.success is False

    def test_verification_trace_in_run_trace(self):
        contract = minimal_contract(success_criteria=[SuccessCriterion(kind=VerificationKind.TEST, target="pytest")])
        inp = PipelineInput(task_contract=contract, run_id="run-verify-7")
        result = executor().run(inp)
        rt = result.run_trace
        verif_step_trace = rt.steps[3]
        assert verif_step_trace.verification is not None
        assert "passed" in (verif_step_trace.verification.summary or "")


class TestInputValidation:
    def test_invalid_task_contract(self):
        with pytest.raises(ValidationError):
            TaskContract(
                task_id="",  # empty
                title="Test",
                task_type=TaskType.FEATURE,
                goal="test",
                scope=TaskScope(repo_path="/workspace", allowed_paths=[]),
                inputs=TaskInputs(user_request="test", relevant_files=[]),
                constraints=TaskConstraints(max_files_changed=1, max_retries=1),
                tools_allowed=[ToolName.EDIT_FILE],
                success_criteria=[],
            )
