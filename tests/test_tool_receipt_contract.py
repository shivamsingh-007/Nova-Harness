import pytest
from pydantic import ValidationError
from models.tool_receipt_contract import (
    InvocationStatus, SideEffectType, IntegrityMode,
    ToolInvocationRef, ExecutionTiming, ResultReference,
    SideEffectSummary, IntegrityMetadata, ToolExecutionResult,
    ToolInvocationReceipt, ReceiptEnvelope,
)


def make_invocation_ref(**overrides) -> ToolInvocationRef:
    defaults = dict(request_id="req-001", run_id="run-001", agent_id="agent-code", tool_id="search_code", action="search")
    defaults.update(overrides)
    return ToolInvocationRef(**defaults)


def make_timing(**overrides) -> ExecutionTiming:
    defaults = dict(requested_at="2026-07-04T10:00:00Z")
    defaults.update(overrides)
    return ExecutionTiming(**defaults)


def make_result_ref(**overrides) -> ResultReference:
    defaults = dict(result_ref_id="rr-001", result_type="search_results", content_ref="results/run-001/search.json")
    defaults.update(overrides)
    return ResultReference(**defaults)


def make_side_effect(**overrides) -> SideEffectSummary:
    defaults = dict(side_effect_type=SideEffectType.READ_ONLY, summary="Searched codebase for pattern")
    defaults.update(overrides)
    return SideEffectSummary(**defaults)


def make_integrity(**overrides) -> IntegrityMetadata:
    defaults = dict(integrity_mode=IntegrityMode.NONE)
    defaults.update(overrides)
    return IntegrityMetadata(**defaults)


def make_execution_result(**overrides) -> ToolExecutionResult:
    defaults = dict(status=InvocationStatus.EXECUTED, outcome_summary="Found 3 matches")
    defaults.update(overrides)
    return ToolExecutionResult(**defaults)


def make_receipt(**overrides) -> ToolInvocationReceipt:
    defaults = dict(
        receipt_id="rcpt-001",
        invocation=make_invocation_ref(),
        timing=make_timing(),
        execution_result=make_execution_result(),
    )
    defaults.update(overrides)
    return ToolInvocationReceipt(**defaults)


def make_envelope(**overrides) -> ReceiptEnvelope:
    defaults = dict(envelope_id="env-001", receipt=make_receipt())
    defaults.update(overrides)
    return ReceiptEnvelope(**defaults)


class TestEnums:
    def test_invocation_status_values(self):
        assert InvocationStatus.REQUESTED.value == "requested"
        assert InvocationStatus.EXECUTED.value == "executed"
        assert InvocationStatus.FAILED.value == "failed"
        assert InvocationStatus.TIMED_OUT.value == "timed_out"
        assert InvocationStatus.BLOCKED.value == "blocked"
        assert InvocationStatus.CANCELLED.value == "cancelled"
        assert len(InvocationStatus) == 6

    def test_side_effect_type_values(self):
        assert SideEffectType.NONE.value == "none"
        assert SideEffectType.READ_ONLY.value == "read_only"
        assert SideEffectType.STATE_MUTATION.value == "state_mutation"
        assert SideEffectType.EXTERNAL_SEND.value == "external_send"
        assert SideEffectType.FILE_WRITE.value == "file_write"
        assert SideEffectType.DATA_EXPORT.value == "data_export"
        assert len(SideEffectType) == 6

    def test_integrity_mode_values(self):
        assert IntegrityMode.NONE.value == "none"
        assert IntegrityMode.HASH_ONLY.value == "hash_only"
        assert IntegrityMode.SIGNED.value == "signed"
        assert IntegrityMode.CHAINED.value == "chained"
        assert len(IntegrityMode) == 4


class TestToolInvocationRef:
    def test_valid(self):
        ref = make_invocation_ref()
        assert ref.request_id == "req-001"
        assert ref.agent_id == "agent-code"

    def test_with_optional_fields(self):
        ref = make_invocation_ref(task_id="t-001", trace_id="trace-001")
        assert ref.task_id == "t-001"
        assert ref.trace_id == "trace-001"

    def test_blank_request_id_raises(self):
        with pytest.raises(ValidationError):
            make_invocation_ref(request_id="")

    def test_blank_run_id_raises(self):
        with pytest.raises(ValidationError):
            make_invocation_ref(run_id="")

    def test_blank_agent_id_raises(self):
        with pytest.raises(ValidationError):
            make_invocation_ref(agent_id="   ")

    def test_blank_tool_id_raises(self):
        with pytest.raises(ValidationError):
            make_invocation_ref(tool_id="")

    def test_blank_action_raises(self):
        with pytest.raises(ValidationError):
            make_invocation_ref(action="")


class TestExecutionTiming:
    def test_valid(self):
        t = make_timing()
        assert t.requested_at == "2026-07-04T10:00:00Z"

    def test_with_optional_fields(self):
        t = make_timing(started_at="2026-07-04T10:00:01Z", completed_at="2026-07-04T10:00:05Z", duration_ms=4000)
        assert t.duration_ms == 4000

    def test_blank_requested_at_raises(self):
        with pytest.raises(ValidationError):
            make_timing(requested_at="")

    def test_negative_duration_raises(self):
        with pytest.raises(ValidationError, match="non-negative"):
            make_timing(duration_ms=-1)

    def test_zero_duration_valid(self):
        t = make_timing(duration_ms=0)
        assert t.duration_ms == 0

    def test_none_duration_valid(self):
        t = make_timing(duration_ms=None)
        assert t.duration_ms is None


class TestResultReference:
    def test_valid(self):
        r = make_result_ref()
        assert r.result_ref_id == "rr-001"
        assert r.result_type == "search_results"

    def test_with_optional_fields(self):
        r = make_result_ref(content_hash="abc123", item_count=10)
        assert r.content_hash == "abc123"
        assert r.item_count == 10

    def test_blank_result_ref_id_raises(self):
        with pytest.raises(ValidationError):
            make_result_ref(result_ref_id="")

    def test_blank_result_type_raises(self):
        with pytest.raises(ValidationError):
            make_result_ref(result_type="")

    def test_negative_item_count_raises(self):
        with pytest.raises(ValidationError, match="non-negative"):
            make_result_ref(item_count=-1)

    def test_zero_item_count_valid(self):
        r = make_result_ref(item_count=0)
        assert r.item_count == 0


class TestSideEffectSummary:
    def test_valid(self):
        s = make_side_effect()
        assert s.side_effect_type == SideEffectType.READ_ONLY

    def test_with_target_refs(self):
        s = make_side_effect(target_refs=["file_a.py", "file_b.py"])
        assert len(s.target_refs) == 2

    def test_blank_summary_raises(self):
        with pytest.raises(ValidationError):
            make_side_effect(summary="")

    def test_blank_target_ref_raises(self):
        with pytest.raises(ValidationError, match="blank"):
            make_side_effect(target_refs=["valid", ""])

    def test_all_side_effect_types_accepted(self):
        for t in SideEffectType:
            s = make_side_effect(side_effect_type=t)
            assert s.side_effect_type == t


class TestIntegrityMetadata:
    def test_none_mode_valid(self):
        im = make_integrity()
        assert im.integrity_mode == IntegrityMode.NONE

    def test_hash_only_valid(self):
        im = make_integrity(integrity_mode=IntegrityMode.HASH_ONLY, canonical_hash="sha256-abc")
        assert im.canonical_hash == "sha256-abc"

    def test_hash_only_without_hash_raises(self):
        with pytest.raises(ValidationError, match="canonical_hash"):
            make_integrity(integrity_mode=IntegrityMode.HASH_ONLY)

    def test_signed_valid(self):
        im = make_integrity(integrity_mode=IntegrityMode.SIGNED, signature_ref="sig-001")
        assert im.signature_ref == "sig-001"

    def test_signed_without_signature_raises(self):
        with pytest.raises(ValidationError, match="signature_ref"):
            make_integrity(integrity_mode=IntegrityMode.SIGNED)

    def test_chained_valid(self):
        im = make_integrity(integrity_mode=IntegrityMode.CHAINED, previous_receipt_hash="sha256-prev")
        assert im.previous_receipt_hash == "sha256-prev"

    def test_chained_without_previous_hash_raises(self):
        with pytest.raises(ValidationError, match="previous_receipt_hash"):
            make_integrity(integrity_mode=IntegrityMode.CHAINED)


class TestToolExecutionResult:
    def test_valid_executed(self):
        r = make_execution_result()
        assert r.status == InvocationStatus.EXECUTED

    def test_with_result_refs(self):
        r = make_execution_result(result_references=[make_result_ref()])
        assert len(r.result_references) == 1

    def test_with_side_effects(self):
        r = make_execution_result(side_effects=[make_side_effect()])
        assert len(r.side_effects) == 1

    def test_blank_outcome_summary_raises(self):
        with pytest.raises(ValidationError):
            make_execution_result(outcome_summary="")

    def test_all_status_accepted(self):
        for s in InvocationStatus:
            kwargs = dict(status=s)
            if s in (InvocationStatus.FAILED, InvocationStatus.TIMED_OUT, InvocationStatus.BLOCKED):
                kwargs["error_summary"] = "something went wrong"
            kwargs["outcome_summary"] = "done"
            r = ToolExecutionResult(**kwargs)
            assert r.status == s

    def test_failed_needs_error_summary(self):
        with pytest.raises(ValidationError, match="error_summary"):
            make_execution_result(status=InvocationStatus.FAILED)

    def test_timed_out_needs_error_summary(self):
        with pytest.raises(ValidationError, match="error_summary"):
            make_execution_result(status=InvocationStatus.TIMED_OUT)

    def test_blocked_needs_error_summary(self):
        with pytest.raises(ValidationError, match="error_summary"):
            make_execution_result(status=InvocationStatus.BLOCKED)

    def test_executed_no_error_summary_valid(self):
        r = make_execution_result(status=InvocationStatus.EXECUTED)
        assert r.error_summary is None

    def test_cancelled_no_error_summary_valid(self):
        r = make_execution_result(status=InvocationStatus.CANCELLED, outcome_summary="Cancelled by operator")
        assert r.error_summary is None

    def test_requested_no_error_summary_valid(self):
        r = make_execution_result(status=InvocationStatus.REQUESTED, outcome_summary="Request submitted")
        assert r.error_summary is None

    def test_failed_with_error_code(self):
        r = make_execution_result(status=InvocationStatus.FAILED, error_summary="timeout", error_code="ERR_TIMEOUT")
        assert r.error_code == "ERR_TIMEOUT"


class TestToolInvocationReceipt:
    def test_valid_receipt(self):
        r = make_receipt()
        assert r.receipt_id == "rcpt-001"
        assert r.policy_decision_ref is None

    def test_with_policy_and_approval_refs(self):
        r = make_receipt(policy_decision_ref="pd-001", approval_ref="app-001")
        assert r.policy_decision_ref == "pd-001"
        assert r.approval_ref == "app-001"

    def test_with_integrity(self):
        r = make_receipt(integrity=IntegrityMetadata(integrity_mode=IntegrityMode.HASH_ONLY, canonical_hash="abc"))
        assert r.integrity.canonical_hash == "abc"

    def test_blank_receipt_id_raises(self):
        with pytest.raises(ValidationError):
            make_receipt(receipt_id="")

    def test_completed_before_started_raises(self):
        with pytest.raises(ValidationError, match="completed_at must not be earlier than started_at"):
            make_receipt(
                timing=make_timing(started_at="2026-07-04T10:00:10Z", completed_at="2026-07-04T10:00:05Z")
            )

    def test_completed_after_started_valid(self):
        r = make_receipt(timing=make_timing(started_at="2026-07-04T10:00:01Z", completed_at="2026-07-04T10:00:05Z"))
        assert r.timing.completed_at == "2026-07-04T10:00:05Z"

    def test_no_timing_optional_fields_valid(self):
        r = make_receipt(timing=make_timing())
        assert r.timing.started_at is None


class TestReceiptEnvelope:
    def test_valid_envelope(self):
        e = make_envelope()
        assert e.envelope_id == "env-001"
        assert e.receipt.receipt_id == "rcpt-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="")


class TestSerialization:
    def test_receipt_to_dict_and_back(self):
        r = make_receipt()
        data = r.model_dump()
        assert data["receipt_id"] == "rcpt-001"
        assert data["execution_result"]["status"] == "executed"
        restored = ToolInvocationReceipt(**data)
        assert restored.receipt_id == r.receipt_id

    def test_envelope_to_dict_and_back(self):
        e = make_envelope()
        data = e.model_dump()
        assert data["envelope_id"] == "env-001"
        restored = ReceiptEnvelope(**data)
        assert restored.envelope_id == e.envelope_id


class TestIntegration:
    def test_read_only_search_receipt(self):
        ref = ToolInvocationRef(request_id="req-search", run_id="run-042", agent_id="agent-code", tool_id="search_code", action="search")
        timing = ExecutionTiming(requested_at="2026-07-04T10:00:00Z", started_at="2026-07-04T10:00:01Z", completed_at="2026-07-04T10:00:03Z", duration_ms=2000)
        result = ToolExecutionResult(
            status=InvocationStatus.EXECUTED,
            outcome_summary="Found 12 matching files",
            result_references=[ResultReference(result_ref_id="rr-srch", result_type="file_list", content_ref="search/run-042/results.json", item_count=12)],
            side_effects=[SideEffectSummary(side_effect_type=SideEffectType.READ_ONLY, summary="Queried search index")],
        )
        receipt = ToolInvocationReceipt(receipt_id="rcpt-srch", invocation=ref, timing=timing, execution_result=result)
        env = ReceiptEnvelope(envelope_id="env-srch", receipt=receipt)
        assert env.receipt.execution_result.status == InvocationStatus.EXECUTED
        assert env.receipt.execution_result.result_references[0].item_count == 12
        assert env.receipt.timing.duration_ms == 2000

    def test_file_write_with_side_effects(self):
        ref = ToolInvocationRef(request_id="req-write", run_id="run-043", agent_id="agent-code", tool_id="edit_file", action="write")
        timing = ExecutionTiming(requested_at="2026-07-04T10:01:00Z", completed_at="2026-07-04T10:01:02Z", duration_ms=2000)
        result = ToolExecutionResult(
            status=InvocationStatus.EXECUTED,
            outcome_summary="Wrote 150 lines to src/handler.py",
            result_references=[ResultReference(result_ref_id="rr-write", result_type="diff", content_ref="diff/run-043/handler.patch")],
            side_effects=[SideEffectSummary(side_effect_type=SideEffectType.FILE_WRITE, target_refs=["src/handler.py"], summary="Updated file with new implementation")],
        )
        receipt = ToolInvocationReceipt(
            receipt_id="rcpt-write", invocation=ref, timing=timing, execution_result=result,
            integrity=IntegrityMetadata(integrity_mode=IntegrityMode.HASH_ONLY, canonical_hash="sha256-xyz"),
        )
        env = ReceiptEnvelope(envelope_id="env-write", receipt=receipt)
        assert env.receipt.integrity.integrity_mode == IntegrityMode.HASH_ONLY
        assert env.receipt.integrity.canonical_hash == "sha256-xyz"

    def test_blocked_by_policy(self):
        ref = ToolInvocationRef(request_id="req-block", run_id="run-044", agent_id="agent-code", tool_id="delete_file", action="delete")
        timing = ExecutionTiming(requested_at="2026-07-04T10:02:00Z")
        result = ToolExecutionResult(
            status=InvocationStatus.BLOCKED,
            outcome_summary="Blocked by deletion policy",
            error_summary="File path matches protected paths list",
            error_code="ERR_PROTECTED_PATH",
        )
        receipt = ToolInvocationReceipt(receipt_id="rcpt-block", invocation=ref, timing=timing, execution_result=result, policy_decision_ref="pd-099")
        env = ReceiptEnvelope(envelope_id="env-block", receipt=receipt)
        assert env.receipt.execution_result.status == InvocationStatus.BLOCKED
        assert env.receipt.policy_decision_ref == "pd-099"
        assert env.receipt.execution_result.error_code == "ERR_PROTECTED_PATH"

    def test_failed_api_call(self):
        ref = ToolInvocationRef(request_id="req-api", run_id="run-045", agent_id="agent-code", tool_id="github_api", action="create_issue")
        timing = ExecutionTiming(requested_at="2026-07-04T10:03:00Z", started_at="2026-07-04T10:03:01Z", completed_at="2026-07-04T10:03:30Z", duration_ms=29000)
        result = ToolExecutionResult(
            status=InvocationStatus.FAILED,
            outcome_summary="GitHub API returned 403",
            error_summary="Rate limit exceeded",
            error_code="HTTP_403",
        )
        receipt = ToolInvocationReceipt(receipt_id="rcpt-fail", invocation=ref, timing=timing, execution_result=result)
        env = ReceiptEnvelope(envelope_id="env-fail", receipt=receipt)
        assert env.receipt.execution_result.status == InvocationStatus.FAILED
        assert env.receipt.execution_result.error_code == "HTTP_403"
        assert env.receipt.timing.duration_ms == 29000

    def test_hash_integrity_receipt(self):
        ref = ToolInvocationRef(request_id="req-hash", run_id="run-046", agent_id="agent-code", tool_id="read_file", action="read")
        timing = ExecutionTiming(requested_at="2026-07-04T10:04:00Z", duration_ms=150)
        result = ToolExecutionResult(
            status=InvocationStatus.EXECUTED,
            outcome_summary="Read 200 lines from config.yaml",
            result_references=[ResultReference(result_ref_id="rr-hash", result_type="file_content", content_ref="files/config.yaml", content_hash="sha256-abc123")],
        )
        receipt = ToolInvocationReceipt(
            receipt_id="rcpt-hash", invocation=ref, timing=timing, execution_result=result,
            integrity=IntegrityMetadata(integrity_mode=IntegrityMode.HASH_ONLY, canonical_hash="sha256-receipt-hash"),
        )
        env = ReceiptEnvelope(envelope_id="env-hash", receipt=receipt)
        assert env.receipt.integrity.canonical_hash == "sha256-receipt-hash"
        assert env.receipt.execution_result.result_references[0].content_hash == "sha256-abc123"
