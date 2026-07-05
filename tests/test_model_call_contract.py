import pytest
from pydantic import ValidationError
from models.model_call_contract import (
    ContextBlockType, ContextTrustLevel, PromptRole,
    ModelProviderType, FinishReason,
    ModelRef, ContextProvenance, PromptContextBlock,
    GenerationConfig, ModelResponseSummary, ModelCallEnvelope,
)


def make_model_ref(**overrides) -> ModelRef:
    defaults = dict(model_ref_id="mr-001", provider=ModelProviderType.ANTHROPIC, model_name="claude-sonnet-4")
    defaults.update(overrides)
    return ModelRef(**defaults)


def make_provenance(**overrides) -> ContextProvenance:
    defaults = dict(provenance_id="prv-001", source_type="file", source_ref="docs/requirements.md")
    defaults.update(overrides)
    return ContextProvenance(**defaults)


def make_block(**overrides) -> PromptContextBlock:
    defaults = dict(
        block_id="blk-001", block_type=ContextBlockType.SYSTEM_INSTRUCTION,
        role=PromptRole.SYSTEM, content_ref="prompts/system/v1.md",
        trust_level=ContextTrustLevel.TRUSTED,
    )
    defaults.update(overrides)
    return PromptContextBlock(**defaults)


def make_config(**overrides) -> GenerationConfig:
    defaults = dict()
    defaults.update(overrides)
    return GenerationConfig(**defaults)


def make_response(**overrides) -> ModelResponseSummary:
    defaults = dict(response_ref="resp-001", finish_reason=FinishReason.STOP)
    defaults.update(overrides)
    return ModelResponseSummary(**defaults)


def make_envelope(**overrides) -> ModelCallEnvelope:
    defaults = dict(
        call_id="call-001", run_id="run-001", agent_id="agent-code",
        model=make_model_ref(),
        generation_config=make_config(),
        response=make_response(),
    )
    defaults.update(overrides)
    return ModelCallEnvelope(**defaults)


class TestEnums:
    def test_context_block_type_values(self):
        assert ContextBlockType.SYSTEM_INSTRUCTION.value == "system_instruction"
        assert ContextBlockType.USER_INPUT.value == "user_input"
        assert ContextBlockType.MEMORY.value == "memory"
        assert ContextBlockType.RETRIEVAL.value == "retrieval"
        assert ContextBlockType.TOOL_OUTPUT.value == "tool_output"
        assert ContextBlockType.POLICY_NOTE.value == "policy_note"
        assert ContextBlockType.SUMMARY.value == "summary"
        assert len(ContextBlockType) == 7

    def test_context_trust_level_values(self):
        assert ContextTrustLevel.TRUSTED.value == "trusted"
        assert ContextTrustLevel.INTERNAL_UNVERIFIED.value == "internal_unverified"
        assert ContextTrustLevel.EXTERNAL_UNTRUSTED.value == "external_untrusted"
        assert len(ContextTrustLevel) == 3

    def test_prompt_role_values(self):
        assert PromptRole.SYSTEM.value == "system"
        assert PromptRole.USER.value == "user"
        assert PromptRole.ASSISTANT.value == "assistant"
        assert PromptRole.TOOL.value == "tool"
        assert len(PromptRole) == 4

    def test_model_provider_type_values(self):
        assert ModelProviderType.OPENAI.value == "openai"
        assert ModelProviderType.ANTHROPIC.value == "anthropic"
        assert ModelProviderType.DEEPSEEK.value == "deepseek"
        assert ModelProviderType.GOOGLE.value == "google"
        assert ModelProviderType.OTHER.value == "other"
        assert len(ModelProviderType) == 5

    def test_finish_reason_values(self):
        assert FinishReason.STOP.value == "stop"
        assert FinishReason.LENGTH.value == "length"
        assert FinishReason.TOOL_CALL.value == "tool_call"
        assert FinishReason.CONTENT_FILTER.value == "content_filter"
        assert FinishReason.ERROR.value == "error"
        assert len(FinishReason) == 5


class TestModelRef:
    def test_valid(self):
        r = make_model_ref()
        assert r.model_ref_id == "mr-001"
        assert r.provider == ModelProviderType.ANTHROPIC

    def test_with_version(self):
        r = make_model_ref(model_version="2026-01-01")
        assert r.model_version == "2026-01-01"

    def test_blank_id_raises(self):
        with pytest.raises(ValidationError):
            make_model_ref(model_ref_id="")

    def test_blank_name_raises(self):
        with pytest.raises(ValidationError):
            make_model_ref(model_name="")

    def test_all_providers_accepted(self):
        for p in ModelProviderType:
            r = make_model_ref(provider=p)
            assert r.provider == p


class TestContextProvenance:
    def test_valid(self):
        p = make_provenance()
        assert p.provenance_id == "prv-001"
        assert p.source_type == "file"

    def test_with_optional_fields(self):
        p = make_provenance(timestamp="2026-07-04T10:00:00Z", confidence=0.95)
        assert p.confidence == 0.95

    def test_blank_provenance_id_raises(self):
        with pytest.raises(ValidationError):
            make_provenance(provenance_id="")

    def test_blank_source_type_raises(self):
        with pytest.raises(ValidationError):
            make_provenance(source_type="")

    def test_blank_source_ref_raises(self):
        with pytest.raises(ValidationError):
            make_provenance(source_ref="")

    def test_confidence_too_low_raises(self):
        with pytest.raises(ValidationError, match="confidence"):
            make_provenance(confidence=-0.1)

    def test_confidence_too_high_raises(self):
        with pytest.raises(ValidationError, match="confidence"):
            make_provenance(confidence=1.5)

    def test_confidence_zero_valid(self):
        p = make_provenance(confidence=0.0)
        assert p.confidence == 0.0

    def test_confidence_one_valid(self):
        p = make_provenance(confidence=1.0)
        assert p.confidence == 1.0

    def test_confidence_none_valid(self):
        p = make_provenance(confidence=None)
        assert p.confidence is None


class TestPromptContextBlock:
    def test_valid(self):
        b = make_block()
        assert b.block_id == "blk-001"
        assert b.block_type == ContextBlockType.SYSTEM_INSTRUCTION

    def test_with_provenance(self):
        b = make_block(provenance=make_provenance())
        assert b.provenance is not None

    def test_blank_block_id_raises(self):
        with pytest.raises(ValidationError):
            make_block(block_id="")

    def test_blank_content_ref_raises(self):
        with pytest.raises(ValidationError):
            make_block(content_ref="")

    def test_all_block_types_accepted(self):
        for t in ContextBlockType:
            b = make_block(block_type=t)
            assert b.block_type == t

    def test_all_trust_levels_accepted(self):
        for t in ContextTrustLevel:
            b = make_block(trust_level=t)
            assert b.trust_level == t

    def test_all_roles_accepted(self):
        for r in PromptRole:
            b = make_block(role=r)
            assert b.role == r


class TestGenerationConfig:
    def test_empty_config_valid(self):
        c = make_config()
        assert c.temperature is None
        assert c.max_output_tokens is None
        assert c.stop_sequences == []

    def test_with_values(self):
        c = make_config(temperature=0.7, max_output_tokens=4096, top_p=0.9, stop_sequences=["\n\n"])
        assert c.temperature == 0.7
        assert c.max_output_tokens == 4096

    def test_temperature_too_low_raises(self):
        with pytest.raises(ValidationError, match="temperature"):
            make_config(temperature=-0.1)

    def test_temperature_too_high_raises(self):
        with pytest.raises(ValidationError, match="temperature"):
            make_config(temperature=2.5)

    def test_temperature_zero_valid(self):
        c = make_config(temperature=0.0)
        assert c.temperature == 0.0

    def test_temperature_two_valid(self):
        c = make_config(temperature=2.0)
        assert c.temperature == 2.0

    def test_top_p_too_low_raises(self):
        with pytest.raises(ValidationError, match="top_p"):
            make_config(top_p=-0.1)

    def test_top_p_too_high_raises(self):
        with pytest.raises(ValidationError, match="top_p"):
            make_config(top_p=1.5)

    def test_max_output_tokens_zero_raises(self):
        with pytest.raises(ValidationError, match="max_output_tokens"):
            make_config(max_output_tokens=0)


class TestModelResponseSummary:
    def test_valid(self):
        r = make_response()
        assert r.response_ref == "resp-001"
        assert r.finish_reason == FinishReason.STOP

    def test_with_usage(self):
        r = make_response(prompt_tokens=150, output_tokens=42, latency_ms=1200)
        assert r.prompt_tokens == 150
        assert r.latency_ms == 1200

    def test_blank_response_ref_raises(self):
        with pytest.raises(ValidationError):
            make_response(response_ref="")

    def test_negative_prompt_tokens_raises(self):
        with pytest.raises(ValidationError, match="non-negative"):
            make_response(prompt_tokens=-1)

    def test_negative_output_tokens_raises(self):
        with pytest.raises(ValidationError, match="non-negative"):
            make_response(output_tokens=-1)

    def test_negative_latency_raises(self):
        with pytest.raises(ValidationError, match="non-negative"):
            make_response(latency_ms=-1)

    def test_zero_tokens_valid(self):
        r = make_response(prompt_tokens=0, output_tokens=0)
        assert r.prompt_tokens == 0

    def test_all_finish_reasons_accepted(self):
        for fr in FinishReason:
            r = make_response(finish_reason=fr)
            assert r.finish_reason == fr


class TestModelCallEnvelope:
    def test_valid(self):
        e = make_envelope()
        assert e.call_id == "call-001"
        assert e.model.provider == ModelProviderType.ANTHROPIC

    def test_with_all_fields(self):
        blocks = [
            make_block(block_id="blk-sys", block_type=ContextBlockType.SYSTEM_INSTRUCTION, role=PromptRole.SYSTEM),
            make_block(block_id="blk-user", block_type=ContextBlockType.USER_INPUT, role=PromptRole.USER),
        ]
        e = make_envelope(
            task_id="t-001", trace_id="trace-001",
            prompt_blocks=blocks,
            policy_ref="pd-001",
            generation_config=GenerationConfig(temperature=0.5),
        )
        assert len(e.prompt_blocks) == 2
        assert e.policy_ref == "pd-001"

    def test_default_generation_config(self):
        e = make_envelope()
        assert e.generation_config.temperature is None
        assert e.generation_config.stop_sequences == []

    def test_blank_call_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(call_id="")

    def test_blank_run_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(run_id="")

    def test_blank_agent_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(agent_id="   ")

    def test_prompt_blocks_order_preserved(self):
        blocks = [
            make_block(block_id="blk-1"),
            make_block(block_id="blk-2"),
            make_block(block_id="blk-3"),
        ]
        e = make_envelope(prompt_blocks=blocks)
        assert [b.block_id for b in e.prompt_blocks] == ["blk-1", "blk-2", "blk-3"]

    def test_empty_prompt_blocks_valid(self):
        e = make_envelope(prompt_blocks=[])
        assert e.prompt_blocks == []


class TestSerialization:
    def test_envelope_to_dict_and_back(self):
        e = make_envelope()
        data = e.model_dump()
        assert data["call_id"] == "call-001"
        assert data["model"]["provider"] == "anthropic"
        restored = ModelCallEnvelope(**data)
        assert restored.call_id == e.call_id


class TestIntegration:
    def test_simple_prompt_with_system_instruction(self):
        blocks = [
            PromptContextBlock(block_id="blk-sys", block_type=ContextBlockType.SYSTEM_INSTRUCTION, role=PromptRole.SYSTEM, content_ref="prompts/system/v2.md", trust_level=ContextTrustLevel.TRUSTED),
            PromptContextBlock(block_id="blk-user", block_type=ContextBlockType.USER_INPUT, role=PromptRole.USER, content_ref="inputs/run-001/request.txt", trust_level=ContextTrustLevel.TRUSTED),
        ]
        env = ModelCallEnvelope(
            call_id="call-simple", run_id="run-001", agent_id="agent-code",
            model=ModelRef(model_ref_id="mr-001", provider=ModelProviderType.ANTHROPIC, model_name="claude-sonnet-4"),
            prompt_blocks=blocks,
            generation_config=GenerationConfig(temperature=0.3),
            response=ModelResponseSummary(response_ref="resp-simple", finish_reason=FinishReason.STOP, prompt_tokens=250, output_tokens=80, latency_ms=3400),
        )
        assert len(env.prompt_blocks) == 2
        assert env.response.prompt_tokens == 250
        assert env.generation_config.temperature == 0.3

    def test_model_call_with_retrieval_provenance(self):
        provenance = ContextProvenance(provenance_id="prv-ret", source_type="vector_db", source_ref="collection=docs,query=semantic-search", timestamp="2026-07-04T10:00:00Z", confidence=0.87)
        blocks = [
            PromptContextBlock(block_id="blk-sys", block_type=ContextBlockType.SYSTEM_INSTRUCTION, role=PromptRole.SYSTEM, content_ref="prompts/system/v1.md", trust_level=ContextTrustLevel.TRUSTED),
            PromptContextBlock(block_id="blk-ret", block_type=ContextBlockType.RETRIEVAL, role=PromptRole.USER, content_ref="retrieval/run-001/results.md", trust_level=ContextTrustLevel.INTERNAL_UNVERIFIED, provenance=provenance),
        ]
        env = ModelCallEnvelope(
            call_id="call-ret", run_id="run-001", task_id="t-001", agent_id="agent-code",
            model=ModelRef(model_ref_id="mr-002", provider=ModelProviderType.OPENAI, model_name="gpt-4o"),
            prompt_blocks=blocks,
            generation_config=GenerationConfig(),
            response=ModelResponseSummary(response_ref="resp-ret", finish_reason=FinishReason.STOP),
        )
        assert env.task_id == "t-001"
        assert env.prompt_blocks[1].provenance.confidence == 0.87
        assert env.prompt_blocks[1].provenance.source_type == "vector_db"

    def test_tool_output_enriched_prompt_with_trust_labels(self):
        blocks = [
            PromptContextBlock(block_id="blk-sys", block_type=ContextBlockType.SYSTEM_INSTRUCTION, role=PromptRole.SYSTEM, content_ref="prompts/system/v1.md", trust_level=ContextTrustLevel.TRUSTED),
            PromptContextBlock(block_id="blk-user", block_type=ContextBlockType.USER_INPUT, role=PromptRole.USER, content_ref="inputs/run-002/query.txt", trust_level=ContextTrustLevel.TRUSTED),
            PromptContextBlock(block_id="blk-tool", block_type=ContextBlockType.TOOL_OUTPUT, role=PromptRole.TOOL, content_ref="tools/search_code/output.json", trust_level=ContextTrustLevel.INTERNAL_UNVERIFIED),
        ]
        env = ModelCallEnvelope(
            call_id="call-tool", run_id="run-002", agent_id="agent-code",
            model=ModelRef(model_ref_id="mr-001", provider=ModelProviderType.ANTHROPIC, model_name="claude-sonnet-4"),
            prompt_blocks=blocks,
            generation_config=GenerationConfig(temperature=0.5, max_output_tokens=2000),
            response=ModelResponseSummary(response_ref="resp-tool", finish_reason=FinishReason.STOP, output_tokens=512),
        )
        assert len(env.prompt_blocks) == 3
        assert env.prompt_blocks[2].block_type == ContextBlockType.TOOL_OUTPUT
        assert env.prompt_blocks[2].trust_level == ContextTrustLevel.INTERNAL_UNVERIFIED

    def test_external_untrusted_web_content_block(self):
        provenance = ContextProvenance(provenance_id="prv-web", source_type="web", source_ref="https://example.com/article", timestamp="2026-07-04T09:00:00Z")
        blocks = [
            PromptContextBlock(block_id="blk-sys", block_type=ContextBlockType.SYSTEM_INSTRUCTION, role=PromptRole.SYSTEM, content_ref="prompts/system/v1.md", trust_level=ContextTrustLevel.TRUSTED),
            PromptContextBlock(block_id="blk-ext", block_type=ContextBlockType.RETRIEVAL, role=PromptRole.USER, content_ref="web/example-com/article.md", trust_level=ContextTrustLevel.EXTERNAL_UNTRUSTED, provenance=provenance),
        ]
        env = ModelCallEnvelope(
            call_id="call-ext", run_id="run-003", agent_id="agent-code",
            model=ModelRef(model_ref_id="mr-001", provider=ModelProviderType.ANTHROPIC, model_name="claude-sonnet-4"),
            prompt_blocks=blocks,
            generation_config=GenerationConfig(temperature=0.2),
            response=ModelResponseSummary(response_ref="resp-ext", finish_reason=FinishReason.STOP),
            policy_ref="pd-ext-content",
        )
        assert env.prompt_blocks[1].trust_level == ContextTrustLevel.EXTERNAL_UNTRUSTED
        assert env.policy_ref == "pd-ext-content"
        assert env.prompt_blocks[1].provenance.source_type == "web"

    def test_response_summary_with_token_and_latency_metadata(self):
        env = ModelCallEnvelope(
            call_id="call-meta", run_id="run-004", agent_id="agent-code",
            model=ModelRef(model_ref_id="mr-003", provider=ModelProviderType.DEEPSEEK, model_name="deepseek-v4"),
            generation_config=GenerationConfig(temperature=0.0, max_output_tokens=1024),
            response=ModelResponseSummary(response_ref="resp-meta", finish_reason=FinishReason.LENGTH, prompt_tokens=500, output_tokens=1024, latency_ms=5200),
        )
        assert env.response.finish_reason == FinishReason.LENGTH
        assert env.response.output_tokens == 1024
        assert env.response.latency_ms == 5200
        assert env.model.provider == ModelProviderType.DEEPSEEK
