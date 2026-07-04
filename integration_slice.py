from datetime import datetime, timezone
from uuid import uuid4

from models.task_contract import (
    TaskContract, TaskType as ContractTaskType, TaskScope, TaskInputs,
    TaskConstraints, ToolName, SuccessCriterion, VerificationKind,
    ApprovalTrigger,
)
from models.prompt_assembly import (
    PromptAssembly, InstructionLayer, InstructionLayerType,
    ContextBlock, ContextBlockType, ToolExposure,
    ConstraintBlock, VerificationBlock, MessageBlock, MessageRole,
)
from models.context_delivery import (
    ContextDeliveryBundle, RepoSnapshot, DeliveryItem, ContentType,
)
from models.tool_interface import (
    ToolInvocation, ApprovalState, ToolResult, ToolStatus,
)
from models.approval_safety import (
    ActionRiskRule, ResourceType, RiskLevel, SafetyAction,
    SafetyDecision, ApprovalRequirement,
)
from models.durable_state import (
    RunState as DurableRunState, RunStatus, StepRecord, StepStatus,
    ToolCallRecord, ToolCallStatus,
)
from models.verification import (
    VerificationCheck, CheckType, CheckStatus, VerificationEvidence,
    EvidenceType, VerificationResult, VerificationVerdict, VerdictStatus as VerifVerdict,
)
from models.benchmark import (
    BenchmarkRun, VerdictStatus as BenchVerdict, MetricResult, MetricName,
    GraderDefinition, GraderType,
)


def make_safety_rule() -> ActionRiskRule:
    return ActionRiskRule(
        rule_id="write-solution-py",
        action_name="write_file",
        resource_type=ResourceType.FILESYSTEM,
        risk_level=RiskLevel.LOW,
        safety_action=SafetyAction.ALLOW,
        rationale="Writing a solution file to workspace is safe.",
        allowed_path_prefixes=["/workspace/solution.py"],
    )


def run_mock_harness() -> dict:
    run_id = f"run-{uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()

    # 1. Load one task contract
    contract = TaskContract(
        task_id="task-add",
        title="Add two numbers",
        task_type=ContractTaskType.FEATURE,
        goal="Write a Python function that adds two integers and returns the sum.",
        scope=TaskScope(
            repo_path="/workspace",
            allowed_paths=["solution.py"],
        ),
        inputs=TaskInputs(
            user_request="Write a Python function add(a, b) that returns a + b.",
            relevant_files=["solution.py"],
        ),
        constraints=TaskConstraints(max_files_changed=1, max_retries=1),
        tools_allowed=[ToolName.READ_FILE, ToolName.EDIT_FILE, ToolName.RUN_TESTS],
        success_criteria=[
            SuccessCriterion(kind=VerificationKind.TEST, target="pytest tests/"),
        ],
        approval_gates=[ApprovalTrigger.DEPENDENCY_CHANGE],
    )

    # 2. Assemble prompt layers
    assembly = PromptAssembly(
        assembly_id=f"asm-{uuid4().hex[:8]}",
        run_id=run_id,
        instruction_layers=[
            InstructionLayer(
                layer_id="sys-behave",
                layer_type=InstructionLayerType.SYSTEM,
                title="System behavior",
                content="You are a coding assistant. Write correct, tested Python code.",
            ),
            InstructionLayer(
                layer_id="task-goal",
                layer_type=InstructionLayerType.TASK,
                title="Task goal",
                content=contract.goal,
            ),
        ],
        context_blocks=[
            ContextBlock(
                block_id="ctx-input",
                block_type=ContextBlockType.SUMMARY,
                title="User request",
                content=contract.inputs.user_request,
            ),
        ],
        tool_exposures=[
            ToolExposure(
                tool_name="write_file",
                description="Write content to a file in the workspace.",
                input_schema_summary="path, content",
            ),
        ],
        constraints=[
            ConstraintBlock(
                title="Scope",
                rules=["Only edit files under /workspace.", "Max 1 file changed."],
            ),
        ],
        verification=VerificationBlock(
            summary="Verify the output file exists and contains valid Python.",
            required_checks=["File exists", "Syntax is valid Python"],
        ),
        messages=[
            MessageBlock(role=MessageRole.SYSTEM, content="You are a coding assistant."),
            MessageBlock(
                role=MessageRole.USER,
                content=(
                    f"Write a Python function in solution.py that adds two integers.\n"
                    f"Scope: only edit solution.py."
                ),
            ),
        ],
    )

    # 3. Select / deliver bounded context
    bundle = ContextDeliveryBundle(
        task_id=contract.task_id,
        task_brief=contract.goal,
        repo_snapshot=RepoSnapshot(
            repo_root="/workspace",
            top_level_paths=["solution.py"],
            primary_language="python",
        ),
        selected_files=[
            DeliveryItem(
                item_id="file:solution.py",
                content_type=ContentType.FILE_SNIPPET,
                title="solution.py",
                reason="Target file for the task",
                content="# solution.py\n# Write your function here",
            ),
        ],
    )

    # 4. Create one tool invocation
    invocation = ToolInvocation(
        invocation_id=f"inv-{uuid4().hex[:8]}",
        tool_name="write_file",
        arguments={"path": "/workspace/solution.py",
                   "content": "def add(a, b):\n    return a + b\n"},
        requested_by_task_id=contract.task_id,
        requested_by_agent="mock-agent",
        approval_state=ApprovalState.NOT_REQUIRED,
    )

    # 5. Run approval / safety evaluation
    safety_rule = make_safety_rule()
    decision = SafetyDecision(
        decision_id=f"dec-{uuid4().hex[:8]}",
        run_id=run_id,
        action_name=invocation.tool_name,
        risk_level=safety_rule.risk_level,
        safety_action=safety_rule.safety_action,
        decision_reason=f"Auto-allowed: {safety_rule.rationale}",
    )

    # 6. Simulate tool execution
    output_path = "/workspace/solution.py"
    tool_result = ToolResult(
        invocation_id=invocation.invocation_id,
        tool_name=invocation.tool_name,
        status=ToolStatus.SUCCESS,
        output={"path": output_path, "size": 44},
        artifacts=[output_path],
        started_at=now,
        finished_at=now,
    )

    # 7. Persist durable state
    run_state = DurableRunState(
        run_id=run_id,
        task_id=contract.task_id,
        status=RunStatus.COMPLETED,
        steps=[
            StepRecord(
                step_id=f"step-{uuid4().hex[:8]}",
                name="Write solution",
                status=StepStatus.SUCCESS,
                tool_calls=[
                    ToolCallRecord(
                        tool_call_id=invocation.invocation_id,
                        tool_name=invocation.tool_name,
                        status=ToolCallStatus.SUCCESS,
                        arguments=invocation.arguments,
                        output={"path": output_path},
                        started_at=now,
                        finished_at=now,
                    ),
                ],
                started_at=now,
                finished_at=now,
            ),
        ],
        created_at=now,
        updated_at=now,
    )

    # 8. Run one deterministic verification check
    verif_check = VerificationCheck(
        check_id="chk-file-exists",
        name="Solution file exists",
        check_type=CheckType.ARTIFACT,
        command=f"test -f {output_path}",
        status=CheckStatus.PASSED,
        evidence=[
            VerificationEvidence(
                evidence_id="ev-file",
                evidence_type=EvidenceType.FILE,
                path=output_path,
                summary="File written successfully",
            ),
        ],
    )
    verif_result = VerificationResult(
        plan_id="plan-add",
        run_id=run_id,
        checks=[verif_check],
        verdict=VerificationVerdict(
            status=VerifVerdict.PASS,
            summary="Solution file exists and passes basic checks.",
        ),
        started_at=now,
        finished_at=now,
    )

    # 9. Emit one benchmark-ready run result
    bench_result = BenchmarkRun(
        run_id=run_id,
        suite_id="suite-integration",
        task_id=contract.task_id,
        harness_version="0.1.0",
        model_name="mock-simulator",
        graders=[
            GraderDefinition(
                grader_id="grd-output",
                name="Output file exists",
                grader_type=GraderType.DETERMINISTIC,
                pass_condition="output_path is not None",
            ),
        ],
        metrics=[
            MetricResult(metric_name=MetricName.TASK_SUCCESS, value=1.0,
                         unit="bool", passed=True),
            MetricResult(metric_name=MetricName.VERIFICATION_PASS, value=1.0,
                         unit="bool", passed=True),
            MetricResult(metric_name=MetricName.LATENCY_SECONDS, value=0.5,
                         unit="s", threshold=30.0, passed=True),
            MetricResult(metric_name=MetricName.RETRY_COUNT, value=0.0,
                         unit="count"),
            MetricResult(metric_name=MetricName.SAFETY_VIOLATIONS, value=0.0,
                         unit="count"),
        ],
        verdict=BenchVerdict.PASS,
        notes="Integration slice: all stages completed successfully.",
        started_at=now,
        finished_at=now,
    )

    return {
        "run_id": run_id,
        "task_contract": contract,
        "prompt_assembly": assembly,
        "context_delivery": bundle,
        "tool_invocation": invocation,
        "safety_decision": decision,
        "tool_result": tool_result,
        "run_state": run_state,
        "verification_result": verif_result,
        "benchmark_result": bench_result,
    }
