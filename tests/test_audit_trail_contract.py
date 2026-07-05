import pytest
from pydantic import ValidationError
from models.audit_trail_contract import (
    AuditEventType, AuditSeverity, EventDirection, EventActorType, EventLinkType,
    AuditEventRef, EventEvidenceRef, AuditMetadata, AuditEventRecord, AuditTrailEnvelope,
)


def make_ref(**overrides) -> AuditEventRef:
    defaults = dict(ref_id="ref-001", ref_type="task")
    defaults.update(overrides)
    return AuditEventRef(**defaults)


def make_evidence(**overrides) -> EventEvidenceRef:
    defaults = dict(evidence_id="ev-001", evidence_type="tool_receipt")
    defaults.update(overrides)
    return EventEvidenceRef(**defaults)


def make_metadata(**overrides) -> AuditMetadata:
    defaults = dict(event_id="evt-001", run_id="run-001", timestamp="2026-07-04T10:00:00Z")
    defaults.update(overrides)
    return AuditMetadata(**defaults)


def make_record(**overrides) -> AuditEventRecord:
    defaults = dict(
        audit_type=AuditEventType.TASK_CREATED,
        metadata=make_metadata(),
        summary="Task created",
    )
    defaults.update(overrides)
    return AuditEventRecord(**defaults)


def make_envelope(**overrides) -> AuditTrailEnvelope:
    defaults = dict(envelope_id="env-001")
    defaults.update(overrides)
    return AuditTrailEnvelope(**defaults)


class TestEnums:
    def test_audit_event_type_values(self):
        assert AuditEventType.TASK_CREATED.value == "task_created"
        assert AuditEventType.TASK_UPDATED.value == "task_updated"
        assert AuditEventType.TASK_COMPLETED.value == "task_completed"
        assert AuditEventType.TOOL_REQUESTED.value == "tool_requested"
        assert AuditEventType.TOOL_COMPLETED.value == "tool_completed"
        assert AuditEventType.MODEL_CALLED.value == "model_called"
        assert AuditEventType.CHECKPOINT_CREATED.value == "checkpoint_created"
        assert AuditEventType.CHECKPOINT_RESTORED.value == "checkpoint_restored"
        assert AuditEventType.POLICY_DECIDED.value == "policy_decided"
        assert AuditEventType.APPROVAL_GRANTED.value == "approval_granted"
        assert AuditEventType.APPROVAL_DENIED.value == "approval_denied"
        assert AuditEventType.FAILURE_RECORDED.value == "failure_recorded"
        assert AuditEventType.SESSION_RESUMED.value == "session_resumed"
        assert AuditEventType.SESSION_TERMINATED.value == "session_terminated"
        assert len(AuditEventType) == 14

    def test_audit_severity_values(self):
        assert AuditSeverity.INFO.value == "info"
        assert AuditSeverity.LOW.value == "low"
        assert AuditSeverity.MEDIUM.value == "medium"
        assert AuditSeverity.HIGH.value == "high"
        assert AuditSeverity.CRITICAL.value == "critical"
        assert len(AuditSeverity) == 5

    def test_event_direction_values(self):
        assert EventDirection.INBOUND.value == "inbound"
        assert EventDirection.INTERNAL.value == "internal"
        assert EventDirection.OUTBOUND.value == "outbound"
        assert len(EventDirection) == 3

    def test_event_actor_type_values(self):
        assert EventActorType.AGENT.value == "agent"
        assert EventActorType.HUMAN.value == "human"
        assert EventActorType.SYSTEM.value == "system"
        assert EventActorType.TOOL.value == "tool"
        assert EventActorType.POLICY_ENGINE.value == "policy_engine"
        assert len(EventActorType) == 5

    def test_event_link_type_values(self):
        assert EventLinkType.CAUSES.value == "causes"
        assert EventLinkType.FOLLOWS.value == "follows"
        assert EventLinkType.RESOLVES.value == "resolves"
        assert EventLinkType.REPLACES.value == "replaces"
        assert EventLinkType.REFERENCES.value == "references"
        assert len(EventLinkType) == 5


class TestAuditEventRef:
    def test_valid(self):
        r = make_ref()
        assert r.ref_id == "ref-001"

    def test_with_uri(self):
        r = make_ref(ref_uri="task://t-001")
        assert r.ref_uri == "task://t-001"

    def test_blank_ref_id_raises(self):
        with pytest.raises(ValidationError):
            make_ref(ref_id="")

    def test_blank_ref_type_raises(self):
        with pytest.raises(ValidationError):
            make_ref(ref_type="")


class TestEventEvidenceRef:
    def test_valid(self):
        e = make_evidence()
        assert e.evidence_id == "ev-001"

    def test_with_uri_and_hash(self):
        e = make_evidence(evidence_uri="receipt://r-001", evidence_hash="abc123")
        assert e.evidence_hash == "abc123"

    def test_blank_evidence_id_raises(self):
        with pytest.raises(ValidationError):
            make_evidence(evidence_id="")

    def test_blank_evidence_type_raises(self):
        with pytest.raises(ValidationError):
            make_evidence(evidence_type="")


class TestAuditMetadata:
    def test_valid(self):
        m = make_metadata()
        assert m.event_id == "evt-001"

    def test_with_all_fields(self):
        m = make_metadata(
            task_id="t-001", trace_id="trace-001", session_id="s-001",
            agent_id="agent-code",
            severity=AuditSeverity.HIGH,
            direction=EventDirection.OUTBOUND,
            actor_type=EventActorType.AGENT,
            actor_ref=make_ref(ref_id="agent-001", ref_type="agent"),
            parent_event_id="evt-000",
        )
        assert m.task_id == "t-001"
        assert m.trace_id == "trace-001"
        assert m.severity == AuditSeverity.HIGH
        assert m.direction == EventDirection.OUTBOUND
        assert m.actor_type == EventActorType.AGENT
        assert m.actor_ref.ref_id == "agent-001"
        assert m.parent_event_id == "evt-000"

    def test_blank_event_id_raises(self):
        with pytest.raises(ValidationError):
            make_metadata(event_id="")

    def test_blank_run_id_raises(self):
        with pytest.raises(ValidationError):
            make_metadata(run_id="")

    def test_blank_timestamp_raises(self):
        with pytest.raises(ValidationError):
            make_metadata(timestamp="")

    def test_parent_event_id_not_self_raises(self):
        with pytest.raises(ValidationError, match="parent_event_id"):
            make_metadata(event_id="evt-001", parent_event_id="evt-001")

    def test_parent_event_id_different_valid(self):
        m = make_metadata(event_id="evt-002", parent_event_id="evt-001")
        assert m.parent_event_id == "evt-001"

    def test_defaults(self):
        m = make_metadata()
        assert m.severity == AuditSeverity.INFO
        assert m.direction == EventDirection.INTERNAL
        assert m.actor_type == EventActorType.SYSTEM
        assert m.parent_event_id is None

    def test_all_severities(self):
        for s in AuditSeverity:
            m = make_metadata(severity=s)
            assert m.severity == s

    def test_all_directions(self):
        for d in EventDirection:
            m = make_metadata(direction=d)
            assert m.direction == d

    def test_all_actor_types(self):
        for a in EventActorType:
            m = make_metadata(actor_type=a)
            assert m.actor_type == a


class TestAuditEventRecord:
    def test_valid(self):
        r = make_record()
        assert r.audit_type == AuditEventType.TASK_CREATED

    def test_with_refs_and_evidence(self):
        r = make_record(
            event_refs=[make_ref()],
            evidence_refs=[make_evidence()],
            link_type=EventLinkType.CAUSES,
        )
        assert len(r.event_refs) == 1
        assert len(r.evidence_refs) == 1
        assert r.link_type == EventLinkType.CAUSES

    def test_all_event_types(self):
        for t in AuditEventType:
            r = make_record(audit_type=t)
            assert r.audit_type == t

    def test_all_link_types(self):
        for lt in EventLinkType:
            r = make_record(link_type=lt)
            assert r.link_type == lt

    def test_blank_summary_raises(self):
        with pytest.raises(ValidationError, match="summary"):
            make_record(summary="")

    def test_superseded_by_not_self_raises(self):
        with pytest.raises(ValidationError, match="superseded_by"):
            make_record(
                metadata=make_metadata(event_id="evt-001"),
                superseded_by="evt-001",
            )

    def test_superseded_by_different_ok(self):
        r = make_record(
            metadata=make_metadata(event_id="evt-001"),
            superseded_by="evt-002",
        )
        assert r.superseded_by == "evt-002"

    def test_redacted_preserves_traceability(self):
        r = make_record(
            metadata=make_metadata(event_id="evt-001", run_id="run-001", timestamp="2026-07-04T10:00:00Z"),
            summary="Sensitive action redacted",
            redacted=True,
        )
        assert r.redacted is True
        assert r.metadata.event_id == "evt-001"
        assert r.metadata.run_id == "run-001"
        assert r.metadata.timestamp is not None

    def test_redacted_preserves_all_traceability_fields(self):
        r = make_record(
            metadata=make_metadata(event_id="evt-r", run_id="run-r", timestamp="now"),
            summary="redacted event",
            redacted=True,
        )
        assert r.redacted is True
        assert r.metadata.event_id == "evt-r"
        assert r.metadata.run_id == "run-r"
        assert r.metadata.timestamp == "now"

    def test_not_redacted_valid(self):
        r = make_record(redacted=False)
        assert r.redacted is False

    def test_evidence_refs_ordered(self):
        refs = [
            make_evidence(evidence_id="e-1"),
            make_evidence(evidence_id="e-2"),
            make_evidence(evidence_id="e-3"),
        ]
        r = make_record(evidence_refs=refs)
        assert [e.evidence_id for e in r.evidence_refs] == ["e-1", "e-2", "e-3"]

    def test_event_refs_ordered(self):
        refs = [
            make_ref(ref_id="r-1"),
            make_ref(ref_id="r-2"),
        ]
        r = make_record(event_refs=refs)
        assert [e.ref_id for e in r.event_refs] == ["r-1", "r-2"]


class TestAuditTrailEnvelope:
    def test_valid_empty_events(self):
        e = make_envelope()
        assert e.events == []

    def test_valid_with_events(self):
        e = make_envelope(events=[make_record(), make_record(metadata=make_metadata(event_id="evt-002"))])
        assert len(e.events) == 2

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="")

    def test_duplicate_event_ids_raises(self):
        with pytest.raises(ValidationError, match="unique"):
            make_envelope(events=[
                make_record(metadata=make_metadata(event_id="evt-001")),
                make_record(metadata=make_metadata(event_id="evt-001")),
            ])

    def test_unique_event_ids_valid(self):
        e = make_envelope(events=[
            make_record(metadata=make_metadata(event_id="evt-001")),
            make_record(metadata=make_metadata(event_id="evt-002")),
        ])
        assert len(e.events) == 2

    def test_event_order_preserved(self):
        e = make_envelope(events=[
            make_record(metadata=make_metadata(event_id="evt-001", timestamp="2026-07-04T10:00:00Z")),
            make_record(metadata=make_metadata(event_id="evt-002", timestamp="2026-07-04T10:01:00Z")),
            make_record(metadata=make_metadata(event_id="evt-003", timestamp="2026-07-04T10:02:00Z")),
        ])
        assert [ev.metadata.event_id for ev in e.events] == ["evt-001", "evt-002", "evt-003"]


class TestSerialization:
    def test_record_to_dict_and_back(self):
        r = make_record()
        data = r.model_dump()
        assert data["audit_type"] == "task_created"
        assert data["summary"] == "Task created"
        restored = AuditEventRecord(**data)
        assert restored.audit_type == r.audit_type

    def test_envelope_to_dict_and_back(self):
        e = make_envelope(events=[make_record()])
        data = e.model_dump()
        assert data["envelope_id"] == "env-001"
        restored = AuditTrailEnvelope(**data)
        assert len(restored.events) == 1


class TestIntegration:
    def test_task_created_and_completed_chain(self):
        created = AuditEventRecord(
            audit_type=AuditEventType.TASK_CREATED,
            metadata=AuditMetadata(event_id="evt-001", run_id="run-001", timestamp="2026-07-04T10:00:00Z",
                                    task_id="t-001", agent_id="agent-code", actor_type=EventActorType.AGENT),
            summary="Task t-001 created for code review",
        )
        completed = AuditEventRecord(
            audit_type=AuditEventType.TASK_COMPLETED,
            metadata=AuditMetadata(event_id="evt-002", run_id="run-001", timestamp="2026-07-04T10:30:00Z",
                                    task_id="t-001", agent_id="agent-code",
                                    actor_type=EventActorType.AGENT, parent_event_id="evt-001"),
            summary="Task t-001 completed successfully",
            link_type=EventLinkType.FOLLOWS,
            event_refs=[AuditEventRef(ref_id="evt-001", ref_type="audit_event")],
        )
        env = AuditTrailEnvelope(envelope_id="env-task", events=[created, completed])
        assert len(env.events) == 2
        assert env.events[0].audit_type == AuditEventType.TASK_CREATED
        assert env.events[1].audit_type == AuditEventType.TASK_COMPLETED
        assert env.events[1].metadata.parent_event_id == "evt-001"

    def test_tool_requested_and_completed_chain(self):
        requested = AuditEventRecord(
            audit_type=AuditEventType.TOOL_REQUESTED,
            metadata=AuditMetadata(event_id="evt-010", run_id="run-001", timestamp="2026-07-04T10:05:00Z",
                                    task_id="t-001", agent_id="agent-code",
                                    actor_type=EventActorType.AGENT),
            summary="Tool read_file requested",
            event_refs=[AuditEventRef(ref_id="t-001", ref_type="task")],
        )
        completed = AuditEventRecord(
            audit_type=AuditEventType.TOOL_COMPLETED,
            metadata=AuditMetadata(event_id="evt-011", run_id="run-001", timestamp="2026-07-04T10:05:03Z",
                                    task_id="t-001", agent_id="agent-code",
                                    actor_type=EventActorType.TOOL, parent_event_id="evt-010"),
            summary="Tool read_file completed with 1 file read",
            evidence_refs=[EventEvidenceRef(evidence_id="receipt-001", evidence_type="tool_receipt",
                                             evidence_uri="receipt://r-001")],
            link_type=EventLinkType.FOLLOWS,
        )
        env = AuditTrailEnvelope(envelope_id="env-tool", events=[requested, completed])
        assert env.events[0].audit_type == AuditEventType.TOOL_REQUESTED
        assert env.events[1].audit_type == AuditEventType.TOOL_COMPLETED
        assert len(env.events[1].evidence_refs) == 1

    def test_policy_decided_with_approval_follow_up(self):
        decided = AuditEventRecord(
            audit_type=AuditEventType.POLICY_DECIDED,
            metadata=AuditMetadata(event_id="evt-020", run_id="run-001", timestamp="2026-07-04T10:10:00Z",
                                    task_id="t-001", agent_id="agent-code",
                                    severity=AuditSeverity.MEDIUM, actor_type=EventActorType.POLICY_ENGINE),
            summary="Policy decision: require_approval for delete_endpoint",
            event_refs=[AuditEventRef(ref_id="pd-001", ref_type="policy_decision")],
        )
        denied = AuditEventRecord(
            audit_type=AuditEventType.APPROVAL_DENIED,
            metadata=AuditMetadata(event_id="evt-021", run_id="run-001", timestamp="2026-07-04T10:15:00Z",
                                    task_id="t-001", agent_id="agent-code",
                                    severity=AuditSeverity.HIGH, actor_type=EventActorType.HUMAN,
                                    parent_event_id="evt-020"),
            summary="Approval denied by API team lead",
            link_type=EventLinkType.RESOLVES,
            event_refs=[AuditEventRef(ref_id="gate-001", ref_type="approval_gate")],
        )
        env = AuditTrailEnvelope(envelope_id="env-policy", events=[decided, denied])
        assert env.events[0].audit_type == AuditEventType.POLICY_DECIDED
        assert env.events[1].audit_type == AuditEventType.APPROVAL_DENIED
        assert env.events[1].metadata.parent_event_id == "evt-020"

    def test_checkpoint_created_and_restored_chain(self):
        created = AuditEventRecord(
            audit_type=AuditEventType.CHECKPOINT_CREATED,
            metadata=AuditMetadata(event_id="evt-030", run_id="run-001", timestamp="2026-07-04T10:20:00Z",
                                    task_id="t-001", agent_id="agent-code",
                                    actor_type=EventActorType.SYSTEM),
            summary="Checkpoint at boundary safe_unit_after_tool",
            event_refs=[AuditEventRef(ref_id="chk-001", ref_type="checkpoint")],
        )
        restored = AuditEventRecord(
            audit_type=AuditEventType.CHECKPOINT_RESTORED,
            metadata=AuditMetadata(event_id="evt-031", run_id="run-001", timestamp="2026-07-04T10:25:00Z",
                                    task_id="t-001", agent_id="agent-code",
                                    severity=AuditSeverity.LOW, actor_type=EventActorType.SYSTEM,
                                    parent_event_id="evt-030"),
            summary="Recovery: restored checkpoint chk-001 after tool failure",
            link_type=EventLinkType.RESOLVES,
            evidence_refs=[EventEvidenceRef(evidence_id="recovery-log", evidence_type="recovery_record",
                                             evidence_uri="recovery://chk-001")],
        )
        env = AuditTrailEnvelope(envelope_id="env-chk", events=[created, restored])
        assert env.events[0].audit_type == AuditEventType.CHECKPOINT_CREATED
        assert env.events[1].audit_type == AuditEventType.CHECKPOINT_RESTORED
        assert env.events[1].metadata.parent_event_id == "evt-030"

    def test_redacted_critical_event_with_evidence_refs(self):
        critical = AuditEventRecord(
            audit_type=AuditEventType.FAILURE_RECORDED,
            metadata=AuditMetadata(
                event_id="evt-040", run_id="run-001", timestamp="2026-07-04T10:30:00Z",
                task_id="t-001", agent_id="agent-code",
                severity=AuditSeverity.CRITICAL, actor_type=EventActorType.SYSTEM,
            ),
            summary="CRITICAL: secret leaked in tool output — payload redacted",
            redacted=True,
            evidence_refs=[
                EventEvidenceRef(evidence_id="ev-secret-1", evidence_type="guardrail_finding",
                                 evidence_uri="guardrail://finding-001", evidence_hash="sha256:abc123"),
                EventEvidenceRef(evidence_id="ev-secret-2", evidence_type="policy_decision",
                                 evidence_uri="policy://pd-090"),
            ],
            event_refs=[AuditEventRef(ref_id="pd-090", ref_type="policy_decision")],
        )
        env = AuditTrailEnvelope(envelope_id="env-critical", events=[critical])
        assert env.events[0].redacted is True
        assert env.events[0].metadata.event_id == "evt-040"
        assert env.events[0].metadata.run_id == "run-001"
        assert env.events[0].metadata.severity == AuditSeverity.CRITICAL
        assert len(env.events[0].evidence_refs) == 2
        assert env.events[0].evidence_refs[1].evidence_id == "ev-secret-2"

    def test_session_terminated_with_session_resumed(self):
        terminated = AuditEventRecord(
            audit_type=AuditEventType.SESSION_TERMINATED,
            metadata=AuditMetadata(event_id="evt-050", run_id="run-001", timestamp="2026-07-04T12:00:00Z",
                                    session_id="s-001", agent_id="agent-code",
                                    severity=AuditSeverity.INFO, actor_type=EventActorType.SYSTEM),
            summary="Session s-001 terminated due to inactivity timeout",
        )
        resumed = AuditEventRecord(
            audit_type=AuditEventType.SESSION_RESUMED,
            metadata=AuditMetadata(event_id="evt-051", run_id="run-002", timestamp="2026-07-04T12:05:00Z",
                                    session_id="s-001", agent_id="agent-code",
                                    severity=AuditSeverity.INFO, actor_type=EventActorType.SYSTEM,
                                    parent_event_id="evt-050"),
            summary="Session s-001 resumed from checkpoint",
            link_type=EventLinkType.FOLLOWS,
        )
        env = AuditTrailEnvelope(envelope_id="env-session", events=[terminated, resumed])
        assert env.events[0].audit_type == AuditEventType.SESSION_TERMINATED
        assert env.events[1].audit_type == AuditEventType.SESSION_RESUMED
        assert env.events[1].metadata.parent_event_id == "evt-050"
