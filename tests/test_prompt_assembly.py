import pytest
from pydantic import ValidationError
from models.prompt_assembly import (
    PromptAssembly,
    InstructionLayer,
    ContextBlock,
    ToolExposure,
    ConstraintBlock,
    VerificationBlock,
    MessageBlock,
    InstructionLayerType,
    ContextBlockType,
    MessageRole,
)


def make_instruction(**overrides) -> InstructionLayer:
    kwargs = dict(
        layer_id="sys-001",
        layer_type=InstructionLayerType.SYSTEM,
        title="System identity",
        content="You are an expert software engineer.",
        priority=0,
    )
    kwargs.update(overrides)
    return InstructionLayer(**kwargs)


def make_context_block(**overrides) -> ContextBlock:
    kwargs = dict(
        block_id="ctx-001",
        block_type=ContextBlockType.FILE,
        title="src/main.py",
        content="def main():\n    print('hello')",
        source_ref="src/main.py",
        priority=0,
    )
    kwargs.update(overrides)
    return ContextBlock(**kwargs)


def make_tool(**overrides) -> ToolExposure:
    kwargs = dict(
        tool_name="bash",
        description="Execute shell commands",
        input_schema_summary="command: string",
        requires_approval=False,
    )
    kwargs.update(overrides)
    return ToolExposure(**kwargs)


def make_constraint(**overrides) -> ConstraintBlock:
    kwargs = dict(
        title="Security rules",
        rules=["Do not modify secrets", "Do not access .env files"],
    )
    kwargs.update(overrides)
    return ConstraintBlock(**kwargs)


def make_verification(**overrides) -> VerificationBlock:
    kwargs = dict(
        summary="Run these checks before finishing",
        required_checks=["pytest tests/ -v"],
        done_definition=["All tests pass", "No lint errors"],
    )
    kwargs.update(overrides)
    return VerificationBlock(**kwargs)


def make_message(**overrides) -> MessageBlock:
    kwargs = dict(
        role=MessageRole.USER,
        content="Add error handling to the main function.",
    )
    kwargs.update(overrides)
    return MessageBlock(**kwargs)


def make_assembly(**overrides) -> PromptAssembly:
    kwargs = dict(
        assembly_id="as-001",
        run_id="run-001",
        instruction_layers=[make_instruction()],
        context_blocks=[make_context_block()],
        tool_exposures=[make_tool()],
        constraints=[make_constraint()],
        verification=make_verification(),
        messages=[make_message()],
    )
    kwargs.update(overrides)
    return PromptAssembly(**kwargs)


class TestInstructionLayer:
    def test_valid_instruction(self):
        inst = make_instruction()
        assert inst.layer_id == "sys-001"

    def test_empty_layer_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_instruction(layer_id="")
        assert "layer_id must not be empty" in str(exc.value)

    def test_empty_title_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_instruction(title="")
        assert "title must not be empty" in str(exc.value)

    def test_empty_content_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_instruction(content="")
        assert "content must not be empty" in str(exc.value)

    def test_all_layer_types(self):
        for lt in InstructionLayerType:
            inst = make_instruction(layer_type=lt)
            assert inst.layer_type == lt

    def test_default_priority_zero(self):
        inst = make_instruction()
        assert inst.priority == 0


class TestContextBlock:
    def test_valid_block(self):
        cb = make_context_block()
        assert cb.block_id == "ctx-001"

    def test_empty_block_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_context_block(block_id="")
        assert "block_id must not be empty" in str(exc.value)

    def test_empty_title_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_context_block(title="")
        assert "title must not be empty" in str(exc.value)

    def test_empty_content_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_context_block(content="")
        assert "content must not be empty" in str(exc.value)

    def test_all_block_types(self):
        for bt in ContextBlockType:
            cb = make_context_block(block_type=bt)
            assert cb.block_type == bt

    def test_source_ref_optional(self):
        cb = make_context_block(source_ref=None)
        assert cb.source_ref is None

    def test_default_priority_zero(self):
        cb = make_context_block()
        assert cb.priority == 0


class TestToolExposure:
    def test_valid_tool(self):
        t = make_tool()
        assert t.tool_name == "bash"

    def test_empty_tool_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_tool(tool_name="")
        assert "tool_name must not be empty" in str(exc.value)

    def test_default_no_approval(self):
        t = make_tool()
        assert t.requires_approval is False

    def test_with_approval(self):
        t = make_tool(requires_approval=True)
        assert t.requires_approval is True


class TestConstraintBlock:
    def test_valid_constraint(self):
        c = make_constraint()
        assert c.title == "Security rules"

    def test_empty_title_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_constraint(title="")
        assert "title must not be empty" in str(exc.value)

    def test_empty_rules_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_constraint(rules=[])
        assert "constraint block must have at least one rule" in str(exc.value)


class TestVerificationBlock:
    def test_valid_with_checks(self):
        vb = make_verification(required_checks=["pytest"], done_definition=[])
        assert "pytest" in vb.required_checks

    def test_valid_with_definition(self):
        vb = make_verification(required_checks=[], done_definition=["All tests pass"])
        assert "All tests pass" in vb.done_definition

    def test_empty_checks_and_definition_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_verification(required_checks=[], done_definition=[])
        assert "verification block must have at least one required_check or done_definition item" in str(exc.value)


class TestMessageBlock:
    def test_valid_message(self):
        m = make_message()
        assert m.role == MessageRole.USER

    def test_all_roles(self):
        for r in MessageRole:
            m = make_message(role=r)
            assert m.role == r

    def test_empty_content_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_message(content="")
        assert "message content must not be empty" in str(exc.value)

    def test_system_message(self):
        m = make_message(role=MessageRole.SYSTEM, content="You are an agent.")
        assert m.role == MessageRole.SYSTEM

    def test_assistant_message(self):
        m = make_message(role=MessageRole.ASSISTANT, content="I will fix the bug.")
        assert m.role == MessageRole.ASSISTANT


class TestPromptAssembly:
    def test_valid_assembly(self):
        a = make_assembly()
        assert a.assembly_id == "as-001"
        assert len(a.instruction_layers) == 1
        assert len(a.tool_exposures) == 1

    def test_empty_assembly_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_assembly(assembly_id="")
        assert "assembly_id must not be empty" in str(exc.value)

    def test_empty_run_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_assembly(run_id="")
        assert "run_id must not be empty" in str(exc.value)

    def test_no_instruction_layers_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_assembly(instruction_layers=[])
        assert "prompt assembly must have at least one instruction layer" in str(exc.value)

    def test_no_message_blocks_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_assembly(messages=[])
        assert "prompt assembly must have at least one message block" in str(exc.value)

    def test_duplicate_tool_names_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_assembly(tool_exposures=[make_tool(), make_tool()])
        assert "duplicate tool_name" in str(exc.value)

    def test_unique_tool_names_is_valid(self):
        a = make_assembly(tool_exposures=[
            make_tool(tool_name="bash"),
            make_tool(tool_name="read"),
        ])
        assert len(a.tool_exposures) == 2

    def test_no_tools_is_valid(self):
        a = make_assembly(tool_exposures=[])
        assert a.tool_exposures == []

    def test_no_context_blocks_is_valid(self):
        a = make_assembly(context_blocks=[])
        assert a.context_blocks == []

    def test_no_constraints_is_valid(self):
        a = make_assembly(constraints=[])
        assert a.constraints == []

    def test_verification_optional(self):
        a = make_assembly(verification=None)
        assert a.verification is None

    def test_multiple_instruction_layers(self):
        a = make_assembly(instruction_layers=[
            make_instruction(layer_id="sys-001", layer_type=InstructionLayerType.SYSTEM, title="System", content="Be helpful."),
            make_instruction(layer_id="repo-001", layer_type=InstructionLayerType.REPOSITORY, title="Repo", content="Use ruff."),
        ])
        assert len(a.instruction_layers) == 2

    def test_multiple_messages(self):
        a = make_assembly(messages=[
            make_message(role=MessageRole.SYSTEM, content="You are an agent."),
            make_message(role=MessageRole.USER, content="Do the task."),
        ])
        assert len(a.messages) == 2


class TestSerialization:
    def test_assembly_serialize(self):
        a = make_assembly()
        data = a.model_dump()
        assert data["assembly_id"] == "as-001"
        assert len(data["instruction_layers"]) == 1
        assert data["verification"]["summary"] == "Run these checks before finishing"

    def test_instruction_serialize(self):
        inst = make_instruction()
        data = inst.model_dump()
        assert data["layer_id"] == "sys-001"
        assert data["layer_type"] == "system"

    def test_context_block_serialize(self):
        cb = make_context_block()
        data = cb.model_dump()
        assert data["block_id"] == "ctx-001"
        assert data["block_type"] == "file"

    def test_tool_exposure_serialize(self):
        t = make_tool()
        data = t.model_dump()
        assert data["tool_name"] == "bash"
        assert data["requires_approval"] is False

    def test_message_block_serialize(self):
        m = make_message()
        data = m.model_dump()
        assert data["role"] == "user"
