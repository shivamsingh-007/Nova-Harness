import pytest
from pydantic import ValidationError
from models.tool_interface import (
    ToolDefinition, ToolInvocation, ToolResult,
    ExecutionMode, ApprovalState, ToolStatus,
)


def make_valid_definition(**overrides) -> ToolDefinition:
    defaults = dict(
        name="read_file",
        description="Read the contents of a file at the given path.",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
        execution_mode=ExecutionMode.READ_ONLY,
    )
    defaults.update(overrides)
    return ToolDefinition(**defaults)


def make_valid_invocation(**overrides) -> ToolInvocation:
    defaults = dict(
        invocation_id="inv-001",
        tool_name="read_file",
        arguments={"path": "src/context_packer.py"},
        requested_by_task_id="task-001",
        requested_by_agent="agent-a",
    )
    defaults.update(overrides)
    return ToolInvocation(**defaults)


def make_valid_result(**overrides) -> ToolResult:
    defaults = dict(
        invocation_id="inv-001",
        tool_name="read_file",
        status=ToolStatus.SUCCESS,
        output={"content": "def scan_files(paths): ..."},
    )
    defaults.update(overrides)
    return ToolResult(**defaults)


class TestToolDefinition:
    def test_valid_read_only(self):
        t = make_valid_definition()
        assert t.name == "read_file"
        assert t.execution_mode == ExecutionMode.READ_ONLY
        assert t.enabled is True

    def test_valid_mutating(self):
        t = make_valid_definition(
            name="edit_file",
            description="Edit a file at the given path.",
            input_schema={"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}},
            execution_mode=ExecutionMode.MUTATING,
            requires_approval=True,
        )
        assert t.requires_approval is True
        assert t.execution_mode == ExecutionMode.MUTATING

    def test_valid_execution(self):
        t = make_valid_definition(
            name="run_tests",
            description="Run tests with pytest.",
            input_schema={"type": "object", "properties": {"target": {"type": "string"}}},
            execution_mode=ExecutionMode.EXECUTION,
            tags=["test", "verify"],
        )
        assert len(t.tags) == 2

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_definition(name="")
        assert "must not be empty" in str(exc.value)

    def test_empty_description_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_definition(description="   ")
        assert "must not be empty" in str(exc.value)

    def test_empty_input_schema_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_definition(input_schema={})
        assert "input_schema must not be empty" in str(exc.value)

    def test_default_enabled(self):
        t = make_valid_definition()
        assert t.enabled is True

    def test_default_no_approval(self):
        t = make_valid_definition()
        assert t.requires_approval is False


class TestToolInvocation:
    def test_valid_invocation(self):
        inv = make_valid_invocation()
        assert inv.approval_state == ApprovalState.NOT_REQUIRED
        assert inv.tool_name == "read_file"

    def test_pending_approval(self):
        inv = make_valid_invocation(approval_state=ApprovalState.PENDING)
        assert inv.approval_state == ApprovalState.PENDING

    def test_cannot_start_approved(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_invocation(approval_state=ApprovalState.APPROVED)
        assert "cannot start as already approved" in str(exc.value)

    def test_empty_invocation_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_invocation(invocation_id="")
        assert "must not be empty" in str(exc.value)

    def test_empty_tool_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_invocation(tool_name="")
        assert "must not be empty" in str(exc.value)

    def test_default_not_required(self):
        inv = make_valid_invocation()
        assert inv.approval_state == ApprovalState.NOT_REQUIRED


class TestToolResult:
    def test_success_with_output(self):
        r = make_valid_result()
        assert r.status == ToolStatus.SUCCESS
        assert r.output is not None
        assert r.error is None

    def test_success_with_artifacts(self):
        r = make_valid_result(output=None, artifacts=["report.html"])
        assert r.status == ToolStatus.SUCCESS
        assert r.artifacts == ["report.html"]

    def test_success_with_no_output_or_artifacts_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_result(output=None, artifacts=[])
        assert "successful result must have output or artifacts" in str(exc.value)

    def test_error_with_message(self):
        r = make_valid_result(
            status=ToolStatus.ERROR,
            output=None,
            error="File not found",
        )
        assert r.status == ToolStatus.ERROR
        assert r.error == "File not found"

    def test_error_without_message_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_result(status=ToolStatus.ERROR, output=None, error="")
        assert "error status must include an error message" in str(exc.value)

    def test_blocked_with_message(self):
        r = make_valid_result(
            status=ToolStatus.BLOCKED,
            output=None,
            error="Approval rejected",
        )
        assert r.status == ToolStatus.BLOCKED

    def test_blocked_without_message_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_result(status=ToolStatus.BLOCKED, output=None, error="")
        assert "blocked status must include an error message" in str(exc.value)


class TestDefaultsAndSerialization:
    def test_definition_serialize(self):
        t = make_valid_definition()
        data = t.model_dump()
        assert data["name"] == "read_file"
        assert data["execution_mode"] == "read_only"
        assert data["enabled"] is True

    def test_invocation_serialize(self):
        inv = make_valid_invocation()
        data = inv.model_dump()
        assert data["invocation_id"] == "inv-001"
        assert data["approval_state"] == "not_required"

    def test_result_serialize(self):
        r = make_valid_result()
        data = r.model_dump()
        assert data["status"] == "success"
        assert "content" in data["output"]
