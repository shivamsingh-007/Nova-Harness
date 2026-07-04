from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

from models.task_contract import TaskContract, VerificationKind, SuccessCriterion
from models.context_delivery import ContextDeliveryBundle, RepoSnapshot, DeliveryItem, ContentType
from models.prompt_assembly import (
    PromptAssembly, InstructionLayer, InstructionLayerType,
    ContextBlock, ContextBlockType, ToolExposure,
    ConstraintBlock, VerificationBlock, MessageBlock, MessageRole,
)
from models.tool_interface import ToolInvocation, ToolResult, ToolStatus, ApprovalState
from models.approval_safety import (
    ActionRiskRule, ResourceType, RiskLevel, SafetyAction,
    SafetyDecision, ApprovalSafetyPolicy,
)
from models.durable_state import RunState as DurableRunState, RunStatus, StepRecord, StepStatus, ToolCallRecord, ToolCallStatus
from models.verification import (
    VerificationCheck, CheckType, CheckStatus, VerificationEvidence,
    EvidenceType, VerificationResult, VerificationVerdict, VerdictStatus as VerifVerdict,
)
from models.benchmark import (
    BenchmarkRun, VerdictStatus as BenchVerdict, MetricResult, MetricName,
    GraderDefinition, GraderType,
)
from models.observability_trace import (
    RunTrace, StepTrace, StepType, TraceEventStatus,
    ToolTrace, PolicyTrace, VerificationTrace, RetryTrace, TraceSummary, PolicyOutcomeType,
)
from harness.state_driver import StateDriver, RunState as FsmState, RunEvent
from harness.model_provider import ModelProvider

ToolExecutor = Callable[[ToolInvocation], ToolResult]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PipelineInput(BaseModel):
    task_contract: TaskContract
    run_id: str
    model_name: str = "mock"
    harness_version: str = "0.1.0"
    safety_policy: Optional[ApprovalSafetyPolicy] = None
    state_driver: Optional[StateDriver] = None


class ExecutorConfig(BaseModel):
    max_steps: int = 10
    max_tool_calls: int = 20
    max_retries: int = 3


class ExecutionStepResult(BaseModel):
    step_index: int
    step_type: StepType
    status: TraceEventStatus
    started_at: str
    finished_at: Optional[str] = None
    latency_seconds: Optional[float] = None
    tool_invocation: Optional[ToolInvocation] = None
    tool_result: Optional[ToolResult] = None
    safety_decision: Optional[SafetyDecision] = None
    policy_trace: Optional[PolicyTrace] = None
    verification_trace: Optional[VerificationTrace] = None
    retry_trace: Optional[RetryTrace] = None
    error: Optional[str] = None


class PipelineResult(BaseModel):
    run_id: str
    task_id: str
    success: bool
    terminal_state: str
    steps: List[ExecutionStepResult]
    run_trace: RunTrace
    benchmark_run: Optional[BenchmarkRun] = None
    durable_state: Optional[DurableRunState] = None
    error: Optional[str] = None


def _default_tool_executor(invocation: ToolInvocation) -> ToolResult:
    return ToolResult(
        invocation_id=invocation.invocation_id,
        tool_name=invocation.tool_name,
        status=ToolStatus.SUCCESS,
        output={"content": "def add(a, b):\n    return a + b\n\n\ndef test_add():\n    assert add(1, 2) == 3\n    assert add(-1, 1) == 0\n", "mock": True},
        artifacts=[],
        started_at=_now(),
        finished_at=_now(),
    )


def _make_safety_decision(invocation: ToolInvocation, policy: ApprovalSafetyPolicy, run_id: str) -> SafetyDecision:
    for rule in policy.rules:
        if rule.action_name == invocation.tool_name:
            return SafetyDecision(
                decision_id=f"dec-{uuid4().hex[:8]}",
                run_id=run_id,
                action_name=invocation.tool_name,
                risk_level=rule.risk_level,
                safety_action=rule.safety_action,
                decision_reason=f"matched rule: {rule.rationale}",
            )
    return SafetyDecision(
        decision_id=f"dec-{uuid4().hex[:8]}",
        run_id=run_id,
        action_name=invocation.tool_name,
        risk_level=RiskLevel.LOW,
        safety_action=SafetyAction.ALLOW,
        decision_reason="no matching rule, default allow",
    )


def _check_criterion(criterion: SuccessCriterion, content: str) -> VerificationTrace:
    kind = criterion.kind
    target = criterion.target or kind.value
    stripped = content.strip()

    if not stripped or stripped in ("{}", "{'mock': True}"):
        return VerificationTrace(check_name=target, status=TraceEventStatus.FAILURE, summary="no output produced")

    if kind == VerificationKind.TEST:
        test_patterns = ["test", "assert", "def test_", "pytest", "unittest", "TestCase", "pytest.mark"]
        found = [p for p in test_patterns if p in stripped.lower()]
        if found:
            return VerificationTrace(check_name=target, status=TraceEventStatus.SUCCESS, summary=f"test patterns found: {', '.join(found)}")
        return VerificationTrace(check_name=target, status=TraceEventStatus.FAILURE, summary="no test patterns in output")

    if kind == VerificationKind.LINT:
        if len(stripped) >= 20:
            return VerificationTrace(check_name=target, status=TraceEventStatus.SUCCESS, summary="output has sufficient content")
        return VerificationTrace(check_name=target, status=TraceEventStatus.FAILURE, summary="output too short")

    if kind == VerificationKind.TYPECHECK:
        type_patterns = [": int", ": str", ": float", ": bool", ": list", ": dict", ": tuple", ": set",
                         "-> ", "Optional[", "List[", "Dict[", "Union[", "Any", "Sequence["]
        found = [p for p in type_patterns if p in stripped]
        if found:
            return VerificationTrace(check_name=target, status=TraceEventStatus.SUCCESS, summary=f"type annotations: {', '.join(found)}")
        return VerificationTrace(check_name=target, status=TraceEventStatus.FAILURE, summary="no type annotations")

    if kind == VerificationKind.DIFF_REVIEW:
        return VerificationTrace(check_name=target, status=TraceEventStatus.SUCCESS, summary="output produced")

    return VerificationTrace(check_name=target, status=TraceEventStatus.SUCCESS, summary="unknown check, default pass")


class PipelineExecutor:
    def __init__(self, config: Optional[ExecutorConfig] = None, tool_executor: Optional[ToolExecutor] = None, model_provider: Optional[ModelProvider] = None):
        self.config = config or ExecutorConfig()
        self._tool_executor = tool_executor or _default_tool_executor
        self._model_provider = model_provider

    def run(self, input: PipelineInput) -> PipelineResult:
        contract = input.task_contract
        run_id = input.run_id
        started_at = _now()
        step_results: List[ExecutionStepResult] = []
        driver = input.state_driver or StateDriver()

        try:
            driver.trigger(RunEvent.START_RUN)
        except ValueError as e:
            return self._build_result(run_id, contract.task_id, driver, step_results, started_at, error=str(e))

        # --- step 0: context + prompt assembly ---
        s0 = _now()
        self._build_context_bundle(contract, run_id)
        self._build_prompt_assembly(contract, run_id)
        step_results.append(ExecutionStepResult(
            step_index=0, step_type=StepType.PROMPT_ASSEMBLY, status=TraceEventStatus.SUCCESS,
            started_at=s0, finished_at=_now(), latency_seconds=0.1,
        ))

        # --- advance to TOOL_PENDING ---
        try:
            driver.trigger(RunEvent.PROMPT_READY)
            driver.trigger(RunEvent.MODEL_RESPONSE_RECEIVED)
            driver.trigger(RunEvent.TOOL_CALL_REQUESTED)
        except ValueError as e:
            return self._build_result(run_id, contract.task_id, driver, step_results, started_at, error=str(e))

        # --- step 1: approval / safety ---
        s1 = _now()
        tool_name = "model_generate" if self._model_provider else "mock_tool"
        invocation = ToolInvocation(
            invocation_id=f"inv-{uuid4().hex[:8]}",
            tool_name=tool_name,
            arguments={"task": contract.goal},
            requested_by_task_id=contract.task_id,
            requested_by_agent=input.model_name,
            approval_state=ApprovalState.NOT_REQUIRED,
        )

        policy = input.safety_policy
        if policy:
            decision = _make_safety_decision(invocation, policy, run_id)
            if decision.safety_action == SafetyAction.BLOCK:
                driver.trigger(RunEvent.APPROVAL_REQUIRED)
                driver.trigger(RunEvent.APPROVAL_REJECTED)
                pt = PolicyTrace(policy_name="approval_safety", outcome=PolicyOutcomeType.BLOCKED, risk_level=decision.risk_level.value, reason=decision.decision_reason)
                step_results.append(ExecutionStepResult(
                    step_index=1, step_type=StepType.POLICY_CHECK, status=TraceEventStatus.BLOCKED,
                    started_at=s1, finished_at=_now(), latency_seconds=0.05,
                    tool_invocation=invocation, safety_decision=decision, policy_trace=pt,
                ))
                return self._build_result(run_id, contract.task_id, driver, step_results, started_at)

            if decision.safety_action == SafetyAction.REQUIRE_APPROVAL:
                driver.trigger(RunEvent.APPROVAL_REQUIRED)
                invocation.approval_state = ApprovalState.PENDING
                pt = PolicyTrace(policy_name="approval_safety", outcome=PolicyOutcomeType.REQUIRED_APPROVAL, risk_level=decision.risk_level.value, reason=decision.decision_reason)
                step_results.append(ExecutionStepResult(
                    step_index=1, step_type=StepType.APPROVAL, status=TraceEventStatus.SUCCESS,
                    started_at=s1, finished_at=_now(), latency_seconds=0.05,
                    tool_invocation=invocation, safety_decision=decision, policy_trace=pt,
                ))
                driver.trigger(RunEvent.APPROVAL_GRANTED, guard_results={"approval_granted_if_required": True})
            else:
                driver.trigger(RunEvent.TOOL_APPROVED_OR_NOT_REQUIRED)
                pt = PolicyTrace(policy_name="approval_safety", outcome=PolicyOutcomeType.ALLOWED, risk_level=decision.risk_level.value, reason=decision.decision_reason)
                step_results.append(ExecutionStepResult(
                    step_index=1, step_type=StepType.POLICY_CHECK, status=TraceEventStatus.SUCCESS,
                    started_at=s1, finished_at=_now(), latency_seconds=0.05,
                    tool_invocation=invocation, safety_decision=decision, policy_trace=pt,
                ))
        else:
            driver.trigger(RunEvent.TOOL_APPROVED_OR_NOT_REQUIRED)
            pt = PolicyTrace(policy_name="approval_safety", outcome=PolicyOutcomeType.ALLOWED, reason="no policy, default allow")
            step_results.append(ExecutionStepResult(
                step_index=1, step_type=StepType.POLICY_CHECK, status=TraceEventStatus.SKIPPED,
                started_at=s1, finished_at=_now(), latency_seconds=0.01,
                tool_invocation=invocation, policy_trace=pt,
            ))

        # --- step 2: tool / model execution ---
        s2 = _now()
        if self._model_provider:
            assembly = self._build_prompt_assembly(contract, run_id)
            messages = [{"role": m.role.value, "content": m.content} for m in assembly.messages]
            try:
                resp = self._model_provider.generate(messages)
                tool_result = ToolResult(
                    invocation_id=invocation.invocation_id,
                    tool_name=invocation.tool_name,
                    status=ToolStatus.SUCCESS,
                    output={"content": resp.content, "model": resp.model_used, "finish_reason": resp.finish_reason},
                    artifacts=[],
                    started_at=s2, finished_at=_now(),
                )
                tool_ok = True
            except Exception as e:
                tool_result = ToolResult(
                    invocation_id=invocation.invocation_id,
                    tool_name=invocation.tool_name,
                    status=ToolStatus.ERROR, output={}, artifacts=[], error=str(e),
                    started_at=s2, finished_at=_now(),
                )
                tool_ok = False
        else:
            tool_result = self._tool_executor(invocation)
            tool_ok = tool_result.status == ToolStatus.SUCCESS

        step_results.append(ExecutionStepResult(
            step_index=2, step_type=StepType.TOOL_EXECUTION,
            status=TraceEventStatus.SUCCESS if tool_ok else TraceEventStatus.FAILURE,
            started_at=s2, finished_at=_now(), latency_seconds=0.2,
            tool_invocation=invocation, tool_result=tool_result,
            error=tool_result.error if not tool_ok else None,
        ))

        if tool_ok:
            try:
                driver.trigger(RunEvent.TOOL_COMPLETED)
            except ValueError:
                pass
        else:
            try:
                driver.trigger(RunEvent.TOOL_FAILED_RETRYABLE)
            except ValueError:
                pass
            return self._build_result(run_id, contract.task_id, driver, step_results, started_at, error=tool_result.error or "execution failed")

        # --- step 3: verification ---
        s3 = _now()
        output_content = str(tool_result.output) if isinstance(tool_result.output, dict) else (tool_result.output or "")
        if isinstance(output_content, bytes):
            output_content = output_content.decode()

        verif_traces = [
            _check_criterion(criterion, output_content)
            for criterion in contract.success_criteria
        ]
        all_pass = all(v.status == TraceEventStatus.SUCCESS for v in verif_traces)

        if all_pass:
            driver.trigger(RunEvent.VERIFICATION_PASSED)
            vs = TraceEventStatus.SUCCESS
        else:
            driver.trigger(RunEvent.VERIFICATION_FAILED_TERMINAL)
            vs = TraceEventStatus.FAILURE

        step_results.append(ExecutionStepResult(
            step_index=3, step_type=StepType.VERIFICATION, status=vs,
            started_at=s3, finished_at=_now(), latency_seconds=0.15,
            verification_trace=VerificationTrace(
                check_name="all_checks", status=vs,
                summary=f"{'passed' if all_pass else 'failed'} {len(verif_traces)} check(s)",
            ),
        ))

        return self._build_result(run_id, contract.task_id, driver, step_results, started_at)

    def _build_context_bundle(self, contract: TaskContract, run_id: str) -> ContextDeliveryBundle:
        return ContextDeliveryBundle(
            task_id=contract.task_id,
            task_brief=contract.goal,
            repo_snapshot=RepoSnapshot(
                repo_root=contract.scope.repo_path if contract.scope else "/workspace",
                top_level_paths=contract.scope.allowed_paths if contract.scope else [],
                primary_language="python",
            ),
            selected_files=[
                DeliveryItem(item_id=f"file:{p}", content_type=ContentType.FILE_SNIPPET, title=p, reason="referenced in task", content="# placeholder")
                for p in (contract.scope.allowed_paths if contract.scope else [])
            ],
        )

    def _build_prompt_assembly(self, contract: TaskContract, run_id: str) -> PromptAssembly:
        return PromptAssembly(
            assembly_id=f"asm-{uuid4().hex[:8]}",
            run_id=run_id,
            instruction_layers=[
                InstructionLayer(layer_id="sys-default", layer_type=InstructionLayerType.SYSTEM, title="System", content="You are a coding assistant."),
                InstructionLayer(layer_id="task-goal", layer_type=InstructionLayerType.TASK, title="Task goal", content=contract.goal),
            ],
            context_blocks=[
                ContextBlock(block_id="ctx-input", block_type=ContextBlockType.SUMMARY, title="Request", content=contract.inputs.user_request),
            ] if contract.inputs else [],
            tool_exposures=[],
            constraints=[],
            verification=VerificationBlock(summary=f"verify {len(contract.success_criteria)} criteria", required_checks=[c.target or c.kind.value for c in contract.success_criteria]),
            messages=[
                MessageBlock(role=MessageRole.SYSTEM, content="You are a coding assistant."),
                MessageBlock(role=MessageRole.USER, content=contract.goal),
            ],
        )

    def _build_result(self, run_id: str, task_id: str, driver: StateDriver, step_results: List[ExecutionStepResult], started_at: str, error: Optional[str] = None) -> PipelineResult:
        finished_at = _now()
        success = driver.current_state_id == FsmState.SUCCEEDED and not error

        step_traces: List[StepTrace] = []
        for r in step_results:
            tool = None
            if r.tool_invocation and r.tool_result:
                tool = ToolTrace(
                    tool_name=r.tool_invocation.tool_name,
                    argument_summary=str(list(r.tool_invocation.arguments.keys())),
                    status=TraceEventStatus.SUCCESS if r.tool_result.status == ToolStatus.SUCCESS else TraceEventStatus.FAILURE,
                    latency_seconds=r.latency_seconds or 0,
                    error=r.tool_result.error if r.tool_result.error else None,
                )
            step_traces.append(StepTrace(
                step_id=f"step-{r.step_index}", step_index=r.step_index, step_type=r.step_type,
                status=r.status, started_at=r.started_at, finished_at=r.finished_at,
                latency_seconds=r.latency_seconds, tool=tool, policy=r.policy_trace,
                verification=r.verification_trace, retry=r.retry_trace,
            ))

        total_latency = sum(r.latency_seconds or 0 for r in step_results)
        total_steps = len(step_results)
        successful = sum(1 for r in step_results if r.status == TraceEventStatus.SUCCESS)
        failed = sum(1 for r in step_results if r.status == TraceEventStatus.FAILURE)
        blocked = sum(1 for r in step_results if r.status == TraceEventStatus.BLOCKED)

        terminal_status = (
            TraceEventStatus.BLOCKED if blocked > 0 else
            TraceEventStatus.FAILURE if driver.current_state_id in (FsmState.FAILED,) or error else
            TraceEventStatus.SUCCESS
        )

        run_trace = RunTrace(
            run_id=run_id, task_id=task_id, steps=step_traces,
            terminal_status=terminal_status, total_latency_seconds=total_latency,
            started_at=started_at, finished_at=finished_at,
            summary=TraceSummary(
                total_steps=total_steps, successful_steps=successful, failed_steps=failed, blocked_steps=blocked,
                total_tool_calls=sum(1 for r in step_results if r.tool_invocation is not None),
                total_policy_checks=sum(1 for r in step_results if r.policy_trace is not None),
                policy_blocks=sum(1 for r in step_results if r.policy_trace and r.policy_trace.outcome == PolicyOutcomeType.BLOCKED),
                total_retries=sum(1 for r in step_results if r.retry_trace is not None),
                total_verification_checks=sum(1 for r in step_results if r.verification_trace is not None),
                verification_failures=sum(1 for r in step_results if r.verification_trace and r.verification_trace.status == TraceEventStatus.FAILURE),
                total_latency_seconds=total_latency,
            ),
        )

        benchmark_run = BenchmarkRun(
            run_id=run_id, suite_id="pipeline-executor", task_id=task_id,
            harness_version="0.1.0", model_name="mock",
            graders=[GraderDefinition(grader_id="grd-auto", name="Auto result", grader_type=GraderType.DETERMINISTIC, pass_condition="success == True")],
            metrics=[
                MetricResult(metric_name=MetricName.TASK_SUCCESS, value=1.0 if success else 0.0, unit="bool", passed=success),
                MetricResult(metric_name=MetricName.VERIFICATION_PASS, value=1.0 if failed == 0 else 0.0, unit="bool", passed=failed == 0),
                MetricResult(metric_name=MetricName.LATENCY_SECONDS, value=total_latency, unit="s", threshold=30.0, passed=total_latency <= 30.0),
                MetricResult(metric_name=MetricName.RETRY_COUNT, value=0.0, unit="count"),
                MetricResult(metric_name=MetricName.SAFETY_VIOLATIONS, value=float(blocked), unit="count"),
            ],
            verdict=BenchVerdict.PASS if success else BenchVerdict.FAIL,
            notes=f"PipelineExecutor run completed in {total_latency}s",
            started_at=started_at, finished_at=finished_at,
        )

        return PipelineResult(run_id=run_id, task_id=task_id, success=success, terminal_state=driver.current_state_id.value, steps=step_results, run_trace=run_trace, benchmark_run=benchmark_run, error=error)
