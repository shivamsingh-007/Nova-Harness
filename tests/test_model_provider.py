import os
from unittest.mock import patch, MagicMock
import pytest

from harness.model_provider import ModelProvider, ModelResponse
from harness.pipeline import PipelineExecutor, PipelineInput
from models.task_contract import TaskContract, TaskType, TaskScope, TaskInputs, TaskConstraints, ToolName, SuccessCriterion, VerificationKind


def minimal_contract(**overrides) -> TaskContract:
    kwargs = dict(
        task_id="test-task", title="Test task", task_type=TaskType.FEATURE,
        goal="Write a Python function.",
        scope=TaskScope(repo_path="/workspace", allowed_paths=["solution.py"]),
        inputs=TaskInputs(user_request="Write add(a,b) function.", relevant_files=["solution.py"]),
        constraints=TaskConstraints(max_files_changed=1, max_retries=1, allow_dependency_changes=True),
        tools_allowed=[ToolName.EDIT_FILE],
        success_criteria=[SuccessCriterion(kind=VerificationKind.TEST, target="pytest")],
    )
    kwargs.update(overrides)
    return TaskContract(**kwargs)


class MockProvider:
    def __init__(self, responses=None):
        self._responses = list(responses) if responses else ["mock response"]

    def generate(self, messages, **kwargs):
        content = self._responses.pop(0) if self._responses else ""
        return ModelResponse(content=content, finish_reason="stop", model_used="mock-model", usage={"total_tokens": 10})


class TestModelProviderConfig:
    def test_default_model(self):
        p = ModelProvider()
        assert p.model == "google/gemini-2.0-flash-001"

    def test_custom_model(self):
        p = ModelProvider(model="anthropic/claude-3.5-sonnet")
        assert p.model == "anthropic/claude-3.5-sonnet"

    def test_missing_api_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            p = ModelProvider()
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
                p._headers()


class TestModelProviderGenerate:
    def test_successful_response(self):
        mock_data = {
            "choices": [{"message": {"content": "Hello!"}, "finish_reason": "stop"}],
            "model": "test-model",
            "usage": {"total_tokens": 5},
        }
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-test-key"}, clear=True):
            with patch("httpx.Client") as MockClient:
                mock_instance = MagicMock()
                mock_instance.post.return_value = MagicMock(status_code=200, json=lambda: mock_data)
                MockClient.return_value.__enter__.return_value = mock_instance

                p = ModelProvider(model="test-model")
                resp = p.generate([{"role": "user", "content": "Hi"}])

        assert resp.content == "Hello!"
        assert resp.finish_reason == "stop"
        assert resp.model_used == "test-model"
        assert resp.usage["total_tokens"] == 5

    def test_passes_messages_to_api(self):
        mock_data = {
            "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
            "model": "m", "usage": {},
        }
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-test"}, clear=True):
            with patch("httpx.Client") as MockClient:
                mock_instance = MagicMock()
                mock_instance.post.return_value = MagicMock(status_code=200, json=lambda: mock_data)
                MockClient.return_value.__enter__.return_value = mock_instance

                p = ModelProvider(model="m")
                msgs = [{"role": "user", "content": "test"}]
                p.generate(msgs)

                call_kwargs = mock_instance.post.call_args[1]
                assert call_kwargs["json"]["messages"] == msgs
                assert call_kwargs["json"]["model"] == "m"

    def test_api_error_raises(self):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-test"}, clear=True):
            with patch("httpx.Client") as MockClient:
                mock_instance = MagicMock()
                mock_instance.post.side_effect = Exception("API error")
                MockClient.return_value.__enter__.return_value = mock_instance

                p = ModelProvider()
                with pytest.raises(Exception, match="API error"):
                    p.generate([{"role": "user", "content": "Hi"}])


class TestWiredExecutor:
    def test_model_provider_wired_success(self):
        provider = MockProvider(responses=["```python\ndef add(a, b): return a + b\n\n\ndef test_add():\n    assert add(1, 2) == 3\n```"])
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-mp-1")
        result = PipelineExecutor(model_provider=provider).run(inp)
        assert result.success is True
        assert result.terminal_state == "succeeded"

    def test_model_provider_response_in_result(self):
        provider = MockProvider(responses=["hello world"])
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-mp-2")
        result = PipelineExecutor(model_provider=provider).run(inp)
        tool_step = result.steps[2]
        assert tool_step.tool_result is not None
        assert tool_step.tool_result.status.value == "success"
        assert "hello world" in str(tool_step.tool_result.output.get("content", ""))

    def test_model_provider_failure_propagates(self):
        class FailingProvider:
            def generate(self, messages, **kwargs):
                raise RuntimeError("model failure")

        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-mp-3")
        result = PipelineExecutor(model_provider=FailingProvider()).run(inp)
        assert result.success is False
        assert "model failure" in (result.error or "")

    def test_model_provider_uses_correct_tool_name(self):
        provider = MockProvider(responses=["ok"])
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-mp-4")
        result = PipelineExecutor(model_provider=provider).run(inp)
        assert result.steps[1].tool_invocation is not None
        assert result.steps[1].tool_invocation.tool_name == "model_generate"

    def test_mock_fallback_still_works(self):
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-mp-5")
        result = PipelineExecutor().run(inp)
        assert result.success is True
        assert result.steps[1].tool_invocation.tool_name == "mock_tool"

    def test_mock_provider_four_steps(self):
        provider = MockProvider(responses=["output"])
        inp = PipelineInput(task_contract=minimal_contract(), run_id="run-mp-6")
        result = PipelineExecutor(model_provider=provider).run(inp)
        assert len(result.steps) == 4
