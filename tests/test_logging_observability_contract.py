import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from models.logging_observability_contract import (
    LogLevel, TelemetrySignalType, EventKind, EventOutcome,
    CorrelationContext, TelemetryAttribute, TelemetryEventRecord,
    LogRecord, TraceEventRecord, ObservabilityEnvelope,
)


NOW = datetime.now(timezone.utc)


def make_corr(**overrides) -> CorrelationContext:
    defaults = dict(trace_id="trace-001", run_id="run-001", agent_id="agent-a")
    defaults.update(overrides)
    return CorrelationContext(**defaults)


def make_attr(**overrides) -> TelemetryAttribute:
    defaults = dict(key="db_host", value="localhost")
    defaults.update(overrides)
    return TelemetryAttribute(**defaults)


def make_event(**overrides) -> TelemetryEventRecord:
    defaults = dict(
        event_id="evt-001", signal_type=TelemetrySignalType.LOG,
        event_kind=EventKind.STATE_CHANGE, event_name="run.start",
        timestamp=NOW, level=LogLevel.INFO, outcome=EventOutcome.SUCCESS,
        message="Run started", service_name="harness",
        correlation=make_corr(),
    )
    defaults.update(overrides)
    return TelemetryEventRecord(**defaults)


def make_envelope(**overrides) -> ObservabilityEnvelope:
    defaults = dict(envelope_id="env-001", event=make_event())
    defaults.update(overrides)
    return ObservabilityEnvelope(**defaults)


class TestEnums:
    def test_log_level_values(self):
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARN.value == "WARN"
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.CRITICAL.value == "CRITICAL"
        assert len(LogLevel) == 5

    def test_signal_type_values(self):
        assert TelemetrySignalType.LOG.value == "log"
        assert TelemetrySignalType.TRACE_EVENT.value == "trace_event"
        assert TelemetrySignalType.OBS_EVENT.value == "obs_event"
        assert TelemetrySignalType.AUDIT.value == "audit"
        assert len(TelemetrySignalType) == 4

    def test_event_kind_values(self):
        assert EventKind.STATE_CHANGE.value == "state_change"
        assert EventKind.ERROR.value == "error"
        assert EventKind.POLICY_DECISION.value == "policy_decision"
        assert EventKind.TOOL_CALL.value == "tool_call"
        assert EventKind.MODEL_CALL.value == "model_call"
        assert EventKind.RUN_START.value == "run_start"
        assert EventKind.RUN_END.value == "run_end"
        assert EventKind.CHECKPOINT.value == "checkpoint"
        assert EventKind.RECOVERY.value == "recovery"
        assert EventKind.CONFIG.value == "config"
        assert len(EventKind) == 10

    def test_event_outcome_values(self):
        assert EventOutcome.SUCCESS.value == "success"
        assert EventOutcome.FAILURE.value == "failure"
        assert EventOutcome.PARTIAL.value == "partial"
        assert EventOutcome.UNKNOWN.value == "unknown"
        assert len(EventOutcome) == 4


class TestCorrelationContext:
    def test_empty(self):
        c = CorrelationContext()
        assert c.trace_id is None

    def test_full(self):
        c = CorrelationContext(
            trace_id="t-001", span_id="s-001", run_id="r-001",
            task_id="task-001", agent_id="a-001", tool_call_id="tc-001",
            model_call_id="mc-001", checkpoint_id="chk-001",
            failure_id="fail-001", recovery_decision_id="dec-001",
        )
        assert c.trace_id == "t-001"
        assert c.recovery_decision_id == "dec-001"

    def test_partial(self):
        c = CorrelationContext(run_id="r-001", agent_id="a-001")
        assert c.run_id == "r-001"
        assert c.span_id is None


class TestTelemetryAttribute:
    def test_valid(self):
        a = make_attr()
        assert a.key == "db_host"

    def test_blank_key_raises(self):
        with pytest.raises(ValidationError):
            make_attr(key="")

    def test_with_type_hint(self):
        a = make_attr(type_hint="string")
        assert a.type_hint == "string"


class TestTelemetryEventRecord:
    def test_valid(self):
        e = make_event()
        assert e.event_id == "evt-001"

    def test_blank_event_id_raises(self):
        with pytest.raises(ValidationError):
            make_event(event_id="")

    def test_blank_event_name_raises(self):
        with pytest.raises(ValidationError):
            make_event(event_name="")

    def test_default_outcome(self):
        e = TelemetryEventRecord(
            event_id="evt-def", signal_type=TelemetrySignalType.LOG,
            event_kind=EventKind.STATE_CHANGE, event_name="test",
            timestamp=NOW, level=LogLevel.DEBUG,
        )
        assert e.outcome == EventOutcome.UNKNOWN

    def test_default_attributes_empty(self):
        e = make_event()
        assert e.attributes == []

    def test_all_signal_types(self):
        for st in TelemetrySignalType:
            e = make_event(signal_type=st)
            assert e.signal_type == st

    def test_all_event_kinds(self):
        for ek in EventKind:
            if ek == EventKind.ERROR:
                corr = make_corr(failure_id="fail-001")
                e = make_event(event_kind=ek, level=LogLevel.ERROR, outcome=EventOutcome.FAILURE, correlation=corr)
            else:
                e = make_event(event_kind=ek)
            assert e.event_kind == ek

    def test_all_outcomes(self):
        for o in EventOutcome:
            kwargs = dict(outcome=o)
            if o == EventOutcome.FAILURE:
                kwargs["level"] = LogLevel.WARN
            e = make_event(**kwargs)
            assert e.outcome == o

    def test_error_level_without_failure_outcome_raises(self):
        with pytest.raises(ValidationError, match="outcome=failure"):
            make_event(level=LogLevel.ERROR, outcome=EventOutcome.SUCCESS)

    def test_critical_level_without_failure_outcome_raises(self):
        with pytest.raises(ValidationError, match="outcome=failure"):
            make_event(level=LogLevel.CRITICAL, outcome=EventOutcome.PARTIAL)

    def test_info_level_with_failure_outcome_raises(self):
        with pytest.raises(ValidationError, match="INFO level must not"):
            make_event(level=LogLevel.INFO, outcome=EventOutcome.FAILURE)

    def test_warn_level_with_failure_outcome_valid(self):
        e = make_event(level=LogLevel.WARN, outcome=EventOutcome.FAILURE)
        assert e.outcome == EventOutcome.FAILURE

    def test_debug_level_with_failure_outcome_valid(self):
        e = make_event(level=LogLevel.DEBUG, outcome=EventOutcome.FAILURE)
        assert e.outcome == EventOutcome.FAILURE

    def test_error_kind_without_failure_id_raises(self):
        corr = make_corr(failure_id=None)
        with pytest.raises(ValidationError, match="failure_id"):
            make_event(event_kind=EventKind.ERROR, correlation=corr, level=LogLevel.ERROR, outcome=EventOutcome.FAILURE)

    def test_error_kind_with_correlation_failure_id_valid(self):
        corr = make_corr(failure_id="fail-001")
        e = make_event(event_kind=EventKind.ERROR, correlation=corr, level=LogLevel.ERROR, outcome=EventOutcome.FAILURE)
        assert e.correlation.failure_id == "fail-001"

    def test_error_kind_with_attribute_failure_id_valid(self):
        e = make_event(
            event_kind=EventKind.ERROR, level=LogLevel.ERROR, outcome=EventOutcome.FAILURE,
            attributes=[TelemetryAttribute(key="failure_id", value="fail-001")],
            correlation=make_corr(failure_id=None),
        )
        assert e.event_kind == EventKind.ERROR

    def test_sensitive_with_exposed_key_raises(self):
        with pytest.raises(ValidationError, match="sensitive event must not expose"):
            make_event(
                sensitive=True,
                attributes=[TelemetryAttribute(key="password", value="s3cret")],
            )

    def test_sensitive_with_token_key_raises(self):
        with pytest.raises(ValidationError, match="sensitive event must not expose"):
            make_event(
                sensitive=True,
                attributes=[TelemetryAttribute(key="api_token", value="tok-123")],
            )

    def test_sensitive_with_safe_attrs_valid(self):
        e = make_event(sensitive=True, attributes=[TelemetryAttribute(key="request_id", value="req-001")])
        assert e.sensitive is True

    def test_sensitive_without_attrs_valid(self):
        e = make_event(sensitive=True)
        assert e.sensitive is True

    def test_with_correlation(self):
        corr = make_corr(trace_id="t-001", span_id="s-001")
        e = make_event(correlation=corr)
        assert e.correlation.span_id == "s-001"


class TestLogRecord:
    def test_valid(self):
        e = make_event(signal_type=TelemetrySignalType.LOG, level=LogLevel.INFO)
        rec = LogRecord(event=e)
        assert rec.event.event_id == "evt-001"

    def test_wrong_signal_type_raises(self):
        e = make_event(signal_type=TelemetrySignalType.TRACE_EVENT, level=LogLevel.INFO)
        with pytest.raises(ValidationError, match="signal_type=LOG"):
            LogRecord(event=e)

    def test_missing_level_raises(self):
        e = make_event(signal_type=TelemetrySignalType.LOG, level=None)
        with pytest.raises(ValidationError, match="must have a level"):
            LogRecord(event=e)

    def test_warn_level_valid(self):
        e = make_event(signal_type=TelemetrySignalType.LOG, level=LogLevel.WARN)
        rec = LogRecord(event=e)
        assert rec.event.level == LogLevel.WARN

    def test_debug_level_valid(self):
        e = make_event(signal_type=TelemetrySignalType.LOG, level=LogLevel.DEBUG)
        rec = LogRecord(event=e)
        assert rec.event.level == LogLevel.DEBUG


class TestTraceEventRecord:
    def test_valid(self):
        e = make_event(signal_type=TelemetrySignalType.TRACE_EVENT)
        rec = TraceEventRecord(event=e)
        assert rec.event.event_id == "evt-001"

    def test_wrong_signal_type_raises(self):
        e = make_event(signal_type=TelemetrySignalType.LOG)
        with pytest.raises(ValidationError, match="signal_type=TRACE_EVENT"):
            TraceEventRecord(event=e)

    def test_trace_without_level_valid(self):
        e = make_event(signal_type=TelemetrySignalType.TRACE_EVENT, level=None)
        rec = TraceEventRecord(event=e)
        assert rec.event.level is None


class TestObservabilityEnvelope:
    def test_valid(self):
        env = make_envelope()
        assert env.envelope_id == "env-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="")

    def test_round_trip(self):
        env = make_envelope()
        data = env.model_dump()
        restored = ObservabilityEnvelope(**data)
        assert restored.envelope_id == env.envelope_id


class TestSerialization:
    def test_event_to_dict_and_back(self):
        e = make_event()
        data = e.model_dump()
        assert data["event_id"] == "evt-001"
        restored = TelemetryEventRecord(**data)
        assert restored.event_id == e.event_id

    def test_envelope_to_dict_and_back(self):
        env = make_envelope()
        data = env.model_dump()
        restored = ObservabilityEnvelope(**data)
        assert restored.envelope_id == env.envelope_id


class TestIntegration:
    def test_info_run_start_event(self):
        e = TelemetryEventRecord(
            event_id="evt-run-start", signal_type=TelemetrySignalType.LOG,
            event_kind=EventKind.RUN_START, event_name="run.start",
            timestamp=NOW, level=LogLevel.INFO, outcome=EventOutcome.SUCCESS,
            message="Run r-001 started", service_name="harness",
            correlation=CorrelationContext(trace_id="t-001", run_id="r-001", agent_id="a-001"),
        )
        rec = LogRecord(event=e)
        assert rec.event.correlation.run_id == "r-001"

    def test_warn_tool_call_partial(self):
        e = TelemetryEventRecord(
            event_id="evt-tool", signal_type=TelemetrySignalType.LOG,
            event_kind=EventKind.TOOL_CALL, event_name="tool.call.partial",
            timestamp=NOW, level=LogLevel.WARN, outcome=EventOutcome.PARTIAL,
            message="Tool read_file returned partial results",
            service_name="harness",
            correlation=CorrelationContext(trace_id="t-001", run_id="r-001", tool_call_id="tc-001"),
            attributes=[TelemetryAttribute(key="bytes_read", value="512")],
        )
        rec = LogRecord(event=e)
        assert rec.event.outcome == EventOutcome.PARTIAL

    def test_error_failure_event_linked(self):
        e = TelemetryEventRecord(
            event_id="evt-err", signal_type=TelemetrySignalType.LOG,
            event_kind=EventKind.ERROR, event_name="tool.failure",
            timestamp=NOW, level=LogLevel.ERROR, outcome=EventOutcome.FAILURE,
            message="Tool read_file timed out",
            service_name="harness",
            correlation=CorrelationContext(
                trace_id="t-001", run_id="r-001", tool_call_id="tc-001",
                failure_id="fail-001",
            ),
            attributes=[TelemetryAttribute(key="timeout_sec", value="30")],
        )
        rec = LogRecord(event=e)
        assert rec.event.correlation.failure_id == "fail-001"

    def test_checkpoint_event(self):
        e = TelemetryEventRecord(
            event_id="evt-chk", signal_type=TelemetrySignalType.TRACE_EVENT,
            event_kind=EventKind.CHECKPOINT, event_name="checkpoint.taken",
            timestamp=NOW, outcome=EventOutcome.SUCCESS,
            message="Checkpoint chk-001 taken at step 4",
            service_name="harness",
            correlation=CorrelationContext(
                trace_id="t-001", run_id="r-001", checkpoint_id="chk-001",
            ),
        )
        rec = TraceEventRecord(event=e)
        assert rec.event.correlation.checkpoint_id == "chk-001"

    def test_recovery_decision_event(self):
        e = TelemetryEventRecord(
            event_id="evt-rec", signal_type=TelemetrySignalType.TRACE_EVENT,
            event_kind=EventKind.RECOVERY, event_name="recovery.decided",
            timestamp=NOW, outcome=EventOutcome.SUCCESS,
            message="Recovery decision: retry from fail-001",
            service_name="harness",
            correlation=CorrelationContext(
                trace_id="t-001", run_id="r-001",
                failure_id="fail-001", recovery_decision_id="dec-001",
            ),
        )
        rec = TraceEventRecord(event=e)
        assert rec.event.correlation.recovery_decision_id == "dec-001"
