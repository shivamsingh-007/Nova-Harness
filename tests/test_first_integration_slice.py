from integration_slice import run_mock_harness
from models.task_contract import TaskContract
from models.prompt_assembly import PromptAssembly
from models.context_delivery import ContextDeliveryBundle
from models.tool_interface import ToolInvocation, ToolResult, ToolStatus
from models.approval_safety import SafetyDecision, SafetyAction
from models.durable_state import RunState, RunStatus
from models.verification import VerificationResult, VerdictStatus as VerifVerdict
from models.benchmark import BenchmarkRun, VerdictStatus as BenchVerdict


class TestFirstIntegrationSlice:
    def test_all_stages_returned(self):
        result = run_mock_harness()
        expected_keys = {
            "run_id", "task_contract", "prompt_assembly", "context_delivery",
            "tool_invocation", "safety_decision", "tool_result", "run_state",
            "verification_result", "benchmark_result",
        }
        assert set(result.keys()) == expected_keys

    def test_run_id_is_nonempty_string(self):
        result = run_mock_harness()
        assert isinstance(result["run_id"], str)
        assert len(result["run_id"]) > 0

    def test_task_contract_is_valid(self):
        result = run_mock_harness()
        c = result["task_contract"]
        assert isinstance(c, TaskContract)
        assert c.task_id == "task-add"
        assert len(c.tools_allowed) >= 1
        assert len(c.success_criteria) >= 1

    def test_prompt_assembly_has_layers_and_messages(self):
        result = run_mock_harness()
        a = result["prompt_assembly"]
        assert isinstance(a, PromptAssembly)
        assert len(a.instruction_layers) >= 1
        assert len(a.messages) >= 1
        assert len(a.tool_exposures) >= 1

    def test_context_delivery_has_bundle(self):
        result = run_mock_harness()
        b = result["context_delivery"]
        assert isinstance(b, ContextDeliveryBundle)
        assert b.task_id == "task-add"
        assert len(b.selected_files) >= 1

    def test_tool_invocation_created(self):
        result = run_mock_harness()
        inv = result["tool_invocation"]
        assert isinstance(inv, ToolInvocation)
        assert inv.tool_name == "write_file"
        assert "path" in inv.arguments

    def test_safety_decision_allows_action(self):
        result = run_mock_harness()
        d = result["safety_decision"]
        assert isinstance(d, SafetyDecision)
        assert d.safety_action == SafetyAction.ALLOW
        assert d.approved is None
        assert len(d.decision_reason) > 0

    def test_tool_result_is_success(self):
        result = run_mock_harness()
        tr = result["tool_result"]
        assert isinstance(tr, ToolResult)
        assert tr.status == ToolStatus.SUCCESS
        assert len(tr.artifacts) >= 1

    def test_run_state_is_completed(self):
        result = run_mock_harness()
        rs = result["run_state"]
        assert isinstance(rs, RunState)
        assert rs.status == RunStatus.COMPLETED
        assert len(rs.steps) >= 1
        assert len(rs.steps[0].tool_calls) >= 1

    def test_verification_result_is_pass(self):
        result = run_mock_harness()
        vr = result["verification_result"]
        assert isinstance(vr, VerificationResult)
        assert vr.verdict.status == VerifVerdict.PASS
        assert len(vr.checks) >= 1
        assert vr.checks[0].status.value == "passed"

    def test_benchmark_result_is_pass_with_metrics(self):
        result = run_mock_harness()
        br = result["benchmark_result"]
        assert isinstance(br, BenchmarkRun)
        assert br.verdict == BenchVerdict.PASS
        assert len(br.graders) >= 1
        assert len(br.metrics) >= 1
        assert br.harness_version == "0.1.0"

    def test_benchmark_has_safety_and_retry_metrics(self):
        result = run_mock_harness()
        br = result["benchmark_result"]
        metric_names = {m.metric_name.value for m in br.metrics}
        assert "safety_violations" in metric_names
        assert "retry_count" in metric_names

    def test_all_ids_are_unique(self):
        result = run_mock_harness()
        ids = [
            result["run_id"],
            result["prompt_assembly"].assembly_id,
            result["tool_invocation"].invocation_id,
            result["safety_decision"].decision_id,
            result["run_state"].steps[0].step_id,
        ]
        assert len(set(ids)) == len(ids)

    def test_entire_flow_deterministic_fields(self):
        r1 = run_mock_harness()
        r2 = run_mock_harness()
        assert r1["run_id"] != r2["run_id"]
        assert r1["task_contract"].task_id == r2["task_contract"].task_id
        assert r1["benchmark_result"].harness_version == r2["benchmark_result"].harness_version
