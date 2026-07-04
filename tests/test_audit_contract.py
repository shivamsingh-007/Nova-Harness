import pytest
from pydantic import ValidationError
from models.audit_contract import (
    AuditEventType,
    ActorType,
    ResourceType,
    TraceContext,
    ActorRef,
    ResourceRef,
    EvidenceRef,
    ProvenanceLink,
    DecisionLineage,
    AuditEvent,
    AuditEnvelope,
)


class TestEnums:
    def test_audit_event_type_values(self):
        assert AuditEventType.RUN_STARTED.value == "run_started"
        assert AuditEventType.CHECKPOINT_CREATED.value == "checkpoint_created"

    def test_audit_event_type_count(self):
        assert len(AuditEventType) == 13

    def test_actor_type_values(self):
        assert ActorType.USER.value == "user"
        assert ActorType.SERVICE.value == "service"

    def test_resource_type_values(self):
        assert ResourceType.RUN.value == "run"
        assert ResourceType.DATA_OBJECT.value == "data_object"


class TestTraceContext:
    def test_valid_minimal(self):
        ctx = TraceContext(trace_id="trace-001", run_id="run-abc",
                           environment="production")
        assert ctx.session_id is None
        assert ctx.step_id is None

    def test_with_all_fields(self):
        ctx = TraceContext(trace_id="trace-002", run_id="run-def",
                           session_id="sess-001", step_id="step-3",
                           parent_event_id="ev-001", environment="staging")
        assert ctx.parent_event_id == "ev-001"

    def test_empty_trace_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            TraceContext(trace_id="  ", run_id="r", environment="dev")
        assert "must not be empty" in str(exc.value)

    def test_empty_run_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            TraceContext(trace_id="t", run_id="  ", environment="dev")
        assert "must not be empty" in str(exc.value)

    def test_empty_environment_raises(self):
        with pytest.raises(ValidationError) as exc:
            TraceContext(trace_id="t", run_id="r", environment="  ")
        assert "must not be empty" in str(exc.value)

    def test_parent_event_not_self(self):
        with pytest.raises(ValidationError) as exc:
            TraceContext(trace_id="t-1", run_id="r-1",
                         environment="dev", parent_event_id="t-1")
        assert "parent_event_id must not equal trace_id" in str(exc.value)


class TestActorRef:
    def test_valid(self):
        actor = ActorRef(actor_id="agent-codex", actor_type=ActorType.AGENT)
        assert actor.role is None

    def test_with_role(self):
        actor = ActorRef(actor_id="user-shiva", actor_type=ActorType.USER,
                         role="admin")
        assert actor.role == "admin"

    def test_empty_actor_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            ActorRef(actor_id="  ", actor_type=ActorType.SYSTEM)
        assert "must not be empty" in str(exc.value)


class TestResourceRef:
    def test_valid(self):
        ref = ResourceRef(resource_id="run-abc", resource_type=ResourceType.RUN)
        assert ref.label is None

    def test_with_label(self):
        ref = ResourceRef(resource_id="tool-write",
                          resource_type=ResourceType.TOOL,
                          label="Write file tool")
        assert ref.label == "Write file tool"

    def test_empty_resource_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            ResourceRef(resource_id="  ", resource_type=ResourceType.POLICY)
        assert "must not be empty" in str(exc.value)


class TestEvidenceRef:
    def test_valid(self):
        ref = EvidenceRef(evidence_id="ev-001", source_type="verification",
                          source_ref="check-output-exists")
        assert ref.digest is None

    def test_with_digest(self):
        ref = EvidenceRef(evidence_id="ev-002", source_type="guardrail",
                          source_ref="eval-toxicity",
                          digest="sha256-abc123")
        assert ref.digest == "sha256-abc123"

    def test_empty_evidence_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            EvidenceRef(evidence_id="  ", source_type="t", source_ref="r")
        assert "must not be empty" in str(exc.value)

    def test_empty_source_type_raises(self):
        with pytest.raises(ValidationError) as exc:
            EvidenceRef(evidence_id="e1", source_type="  ", source_ref="r")
        assert "must not be empty" in str(exc.value)

    def test_empty_source_ref_raises(self):
        with pytest.raises(ValidationError) as exc:
            EvidenceRef(evidence_id="e1", source_type="t", source_ref="  ")
        assert "must not be empty" in str(exc.value)

    def test_empty_digest_raises(self):
        with pytest.raises(ValidationError) as exc:
            EvidenceRef(evidence_id="e1", source_type="t",
                        source_ref="r", digest="  ")
        assert "digest must be non-empty if provided" in str(exc.value)


class TestProvenanceLink:
    def test_valid(self):
        link = ProvenanceLink(link_id="pl-001", from_event_id="ev-001",
                              to_event_id="ev-002",
                              relationship_type="caused")
        assert link.relationship_type == "caused"

    def test_empty_link_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            ProvenanceLink(link_id="  ", from_event_id="a",
                           to_event_id="b", relationship_type="r")
        assert "must not be empty" in str(exc.value)

    def test_empty_from_raises(self):
        with pytest.raises(ValidationError) as exc:
            ProvenanceLink(link_id="l1", from_event_id="  ",
                           to_event_id="b", relationship_type="r")
        assert "must not be empty" in str(exc.value)

    def test_empty_to_raises(self):
        with pytest.raises(ValidationError) as exc:
            ProvenanceLink(link_id="l1", from_event_id="a",
                           to_event_id="  ", relationship_type="r")
        assert "must not be empty" in str(exc.value)

    def test_empty_relationship_raises(self):
        with pytest.raises(ValidationError) as exc:
            ProvenanceLink(link_id="l1", from_event_id="a",
                           to_event_id="b", relationship_type="  ")
        assert "must not be empty" in str(exc.value)

    def test_self_link_raises(self):
        with pytest.raises(ValidationError) as exc:
            ProvenanceLink(link_id="l1", from_event_id="ev-001",
                           to_event_id="ev-001",
                           relationship_type="self")
        assert "from_event_id must not equal to_event_id" in str(exc.value)


class TestDecisionLineage:
    def test_with_inputs(self):
        lineage = DecisionLineage(lineage_id="dl-001",
                                  input_refs=[
                                      ResourceRef(resource_id="file-solution",
                                                   resource_type=ResourceType.DATA_OBJECT),
                                  ])
        assert len(lineage.input_refs) == 1

    def test_with_all_refs(self):
        lineage = DecisionLineage(lineage_id="dl-002",
                                  input_refs=[
                                      ResourceRef(resource_id="prompt-1",
                                                   resource_type=ResourceType.DATA_OBJECT),
                                  ],
                                  evidence_refs=[
                                      EvidenceRef(evidence_id="ev-1",
                                                   source_type="verification",
                                                   source_ref="check-output"),
                                  ],
                                  policy_refs=[
                                      ResourceRef(resource_id="policy-output-v1",
                                                   resource_type=ResourceType.POLICY),
                                  ],
                                  output_refs=[
                                      ResourceRef(resource_id="output-gen-001",
                                                   resource_type=ResourceType.OUTPUT),
                                  ])
        assert len(lineage.output_refs) == 1

    def test_empty_lineage_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            DecisionLineage(lineage_id="  ")
        assert "must not be empty" in str(exc.value)

    def test_no_refs_raises(self):
        with pytest.raises(ValidationError) as exc:
            DecisionLineage(lineage_id="dl-003")
        assert "decision lineage must have at least one reference" in str(exc.value)


class TestAuditEvent:
    def test_minimal(self):
        event = AuditEvent(
            event_id="ev-001",
            event_type=AuditEventType.RUN_STARTED,
            occurred_at="2026-07-04T12:00:00Z",
            trace_context=TraceContext(trace_id="trace-001", run_id="run-abc",
                                       environment="production"),
            actor=ActorRef(actor_id="user-shiva", actor_type=ActorType.USER),
            target_resource=ResourceRef(resource_id="run-abc",
                                        resource_type=ResourceType.RUN),
            action_summary="Run started for task-add-42",
            outcome="success",
        )
        assert event.decision_lineage is None

    def test_with_decision_lineage(self):
        event = AuditEvent(
            event_id="ev-002",
            event_type=AuditEventType.TOOL_EXECUTED,
            occurred_at="2026-07-04T12:01:00Z",
            trace_context=TraceContext(trace_id="trace-001", run_id="run-abc",
                                       step_id="step-2", environment="production"),
            actor=ActorRef(actor_id="agent-codex", actor_type=ActorType.AGENT),
            target_resource=ResourceRef(resource_id="tool-write",
                                        resource_type=ResourceType.TOOL,
                                        label="write_file"),
            action_summary="Executed write_file on solution.py",
            outcome="success",
            decision_lineage=DecisionLineage(
                lineage_id="dl-001",
                input_refs=[
                    ResourceRef(resource_id="file-solution",
                                resource_type=ResourceType.DATA_OBJECT),
                ],
                policy_refs=[
                    ResourceRef(resource_id="policy-write-v1",
                                resource_type=ResourceType.POLICY),
                ],
                output_refs=[
                    ResourceRef(resource_id="output-solution-py",
                                resource_type=ResourceType.OUTPUT),
                ],
            ),
        )
        assert event.decision_lineage is not None

    def test_empty_event_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            AuditEvent(event_id="  ", event_type=AuditEventType.RUN_STARTED,
                       occurred_at="now", trace_context=TraceContext(
                           trace_id="t", run_id="r", environment="d"),
                       actor=ActorRef(actor_id="a", actor_type=ActorType.SYSTEM),
                       target_resource=ResourceRef(resource_id="r",
                                                   resource_type=ResourceType.RUN),
                       action_summary="x", outcome="ok")
        assert "must not be empty" in str(exc.value)

    def test_empty_occurred_at_raises(self):
        with pytest.raises(ValidationError) as exc:
            AuditEvent(event_id="e1", event_type=AuditEventType.RUN_STARTED,
                       occurred_at="  ", trace_context=TraceContext(
                           trace_id="t", run_id="r", environment="d"),
                       actor=ActorRef(actor_id="a", actor_type=ActorType.SYSTEM),
                       target_resource=ResourceRef(resource_id="r",
                                                   resource_type=ResourceType.RUN),
                       action_summary="x", outcome="ok")
        assert "must not be empty" in str(exc.value)

    def test_empty_action_summary_raises(self):
        with pytest.raises(ValidationError) as exc:
            AuditEvent(event_id="e1", event_type=AuditEventType.RUN_STARTED,
                       occurred_at="now", trace_context=TraceContext(
                           trace_id="t", run_id="r", environment="d"),
                       actor=ActorRef(actor_id="a", actor_type=ActorType.SYSTEM),
                       target_resource=ResourceRef(resource_id="r",
                                                   resource_type=ResourceType.RUN),
                       action_summary="  ", outcome="ok")
        assert "must not be empty" in str(exc.value)

    def test_empty_outcome_raises(self):
        with pytest.raises(ValidationError) as exc:
            AuditEvent(event_id="e1", event_type=AuditEventType.RUN_STARTED,
                       occurred_at="now", trace_context=TraceContext(
                           trace_id="t", run_id="r", environment="d"),
                       actor=ActorRef(actor_id="a", actor_type=ActorType.SYSTEM),
                       target_resource=ResourceRef(resource_id="r",
                                                   resource_type=ResourceType.RUN),
                       action_summary="x", outcome="  ")
        assert "must not be empty" in str(exc.value)

    def test_all_event_types_accepted(self):
        for event_type in AuditEventType:
            event = AuditEvent(
                event_id=f"ev-{event_type.value}",
                event_type=event_type,
                occurred_at="now",
                trace_context=TraceContext(trace_id="t", run_id="r",
                                           environment="d"),
                actor=ActorRef(actor_id="a", actor_type=ActorType.SYSTEM),
                target_resource=ResourceRef(resource_id="r",
                                            resource_type=ResourceType.RUN),
                action_summary=f"Event {event_type.value}",
                outcome="success",
            )
            assert event.event_type == event_type


class TestAuditEnvelope:
    def test_valid_without_links(self):
        envelope = AuditEnvelope(
            envelope_id="env-001",
            event=AuditEvent(
                event_id="ev-001",
                event_type=AuditEventType.RUN_STARTED,
                occurred_at="2026-07-04T12:00:00Z",
                trace_context=TraceContext(trace_id="trace-001",
                                           run_id="run-abc",
                                           environment="production"),
                actor=ActorRef(actor_id="user-shiva",
                               actor_type=ActorType.USER),
                target_resource=ResourceRef(resource_id="run-abc",
                                            resource_type=ResourceType.RUN),
                action_summary="Run started",
                outcome="success",
            ),
        )
        assert len(envelope.provenance_links) == 0
        assert envelope.integrity_hash is None

    def test_with_provenance_links(self):
        envelope = AuditEnvelope(
            envelope_id="env-002",
            event=AuditEvent(
                event_id="ev-002",
                event_type=AuditEventType.TOOL_EXECUTED,
                occurred_at="now",
                trace_context=TraceContext(trace_id="t", run_id="r",
                                           environment="d"),
                actor=ActorRef(actor_id="a", actor_type=ActorType.AGENT),
                target_resource=ResourceRef(resource_id="r",
                                            resource_type=ResourceType.TOOL),
                action_summary="Tool executed",
                outcome="success",
            ),
            provenance_links=[
                ProvenanceLink(link_id="pl-001", from_event_id="ev-001",
                               to_event_id="ev-002",
                               relationship_type="caused"),
            ],
            integrity_hash="sha256-def456",
        )
        assert len(envelope.provenance_links) == 1
        assert envelope.integrity_hash == "sha256-def456"

    def test_empty_envelope_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            AuditEnvelope(envelope_id="  ",
                          event=AuditEvent(event_id="e1",
                                           event_type=AuditEventType.RUN_STARTED,
                                           occurred_at="now",
                                           trace_context=TraceContext(
                                               trace_id="t", run_id="r",
                                               environment="d"),
                                           actor=ActorRef(actor_id="a",
                                                          actor_type=ActorType.SYSTEM),
                                           target_resource=ResourceRef(
                                               resource_id="r",
                                               resource_type=ResourceType.RUN),
                                           action_summary="x",
                                           outcome="ok"))
        assert "must not be empty" in str(exc.value)

    def test_empty_integrity_hash_raises(self):
        with pytest.raises(ValidationError) as exc:
            AuditEnvelope(envelope_id="env-001",
                          event=AuditEvent(event_id="e1",
                                           event_type=AuditEventType.RUN_STARTED,
                                           occurred_at="now",
                                           trace_context=TraceContext(
                                               trace_id="t", run_id="r",
                                               environment="d"),
                                           actor=ActorRef(actor_id="a",
                                                          actor_type=ActorType.SYSTEM),
                                           target_resource=ResourceRef(
                                               resource_id="r",
                                               resource_type=ResourceType.RUN),
                                           action_summary="x",
                                           outcome="ok"),
                          integrity_hash="  ")
        assert "integrity_hash must be non-empty if provided" in str(exc.value)


class TestSerialization:
    def test_audit_event_to_json(self):
        event = AuditEvent(
            event_id="ev-001", event_type=AuditEventType.RUN_STARTED,
            occurred_at="2026-07-04T12:00:00Z",
            trace_context=TraceContext(trace_id="t", run_id="r",
                                       environment="dev"),
            actor=ActorRef(actor_id="agent-a", actor_type=ActorType.AGENT),
            target_resource=ResourceRef(resource_id="r",
                                        resource_type=ResourceType.RUN),
            action_summary="Run started", outcome="success",
        )
        json_str = event.model_dump_json()
        assert "ev-001" in json_str
        assert "run_started" in json_str

    def test_envelope_roundtrip(self):
        envelope = AuditEnvelope(
            envelope_id="env-001",
            event=AuditEvent(
                event_id="ev-001", event_type=AuditEventType.RUN_COMPLETED,
                occurred_at="now",
                trace_context=TraceContext(trace_id="t", run_id="r",
                                           environment="d"),
                actor=ActorRef(actor_id="a", actor_type=ActorType.SYSTEM),
                target_resource=ResourceRef(resource_id="r",
                                            resource_type=ResourceType.RUN),
                action_summary="Run done", outcome="success",
            ),
            integrity_hash="sha256-hash",
        )
        dumped = envelope.model_dump()
        assert dumped["integrity_hash"] == "sha256-hash"
        assert dumped["event"]["event_type"] == "run_completed"

    def test_lineage_roundtrip(self):
        lineage = DecisionLineage(
            lineage_id="dl-001",
            input_refs=[
                ResourceRef(resource_id="input-1",
                            resource_type=ResourceType.DATA_OBJECT),
            ],
        )
        dumped = lineage.model_dump()
        assert dumped["lineage_id"] == "dl-001"
        assert dumped["input_refs"][0]["resource_type"] == "data_object"
