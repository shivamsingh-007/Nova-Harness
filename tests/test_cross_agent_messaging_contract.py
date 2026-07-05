import pytest
from datetime import datetime, timedelta, timezone
from pydantic import ValidationError
from models.cross_agent_messaging_contract import (
    MessageIntentType, MessageTransportMode, MessageDeliveryStatus,
    MessagePriority, AudienceType,
    AgentMessageHeader, MessageAudience, MessagePayload,
    MessageDeliveryPolicy, MessageAcknowledgement, MessageFailureRecord,
    CrossAgentMessage, CrossAgentMessageEnvelope,
)

NOW = datetime.now(timezone.utc)
LATER = NOW + timedelta(hours=1)


def make_header(**overrides) -> AgentMessageHeader:
    defaults = dict(message_id="msg-001", schema_version="1.0",
                    intent_type=MessageIntentType.REQUEST_ACTION,
                    sender_agent_id="agent-mgr-01",
                    transport_mode=MessageTransportMode.ASYNCHRONOUS,
                    created_at=NOW)
    defaults.update(overrides)
    return AgentMessageHeader(**defaults)


def make_audience(**overrides) -> MessageAudience:
    defaults = dict(audience_id="aud-001",
                    audience_type=AudienceType.SINGLE_AGENT,
                    target_agent_ids=["agent-coder-01"])
    defaults.update(overrides)
    return MessageAudience(**defaults)


def make_payload(**overrides) -> MessagePayload:
    defaults = dict(payload_id="pl-001",
                    summary="Generate auth module",
                    data_refs=["specs/auth.md"],
                    requested_actions=["implement auth", "write tests"])
    defaults.update(overrides)
    return MessagePayload(**defaults)


def make_delivery_policy(**overrides) -> MessageDeliveryPolicy:
    defaults = dict(delivery_policy_id="dp-001",
                    requires_ack=True, timeout_ms=30000,
                    max_retries=3, idempotency_key="idem-001")
    defaults.update(overrides)
    return MessageDeliveryPolicy(**defaults)


def make_ack(**overrides) -> MessageAcknowledgement:
    defaults = dict(ack_id="ack-001", message_id="msg-001",
                    receiver_agent_id="agent-coder-01",
                    delivery_status=MessageDeliveryStatus.ACKNOWLEDGED,
                    received_at=NOW)
    defaults.update(overrides)
    return MessageAcknowledgement(**defaults)


def make_failure(**overrides) -> MessageFailureRecord:
    defaults = dict(failure_id="fail-001", message_id="msg-001",
                    failure_stage="delivery", failure_reason="audience_mismatch",
                    retryable=False, rejected_by="agent-coder-01",
                    failed_at=NOW)
    defaults.update(overrides)
    return MessageFailureRecord(**defaults)


def make_message(header=None, audience=None, payload=None,
                 delivery_policy=None, **overrides) -> CrossAgentMessage:
    h = header or make_header()
    a = audience or make_audience()
    p = payload or make_payload()
    dp = delivery_policy or make_delivery_policy()
    data = dict(header=h, audience=a, payload=p, delivery_policy=dp)
    data.update(overrides)
    return CrossAgentMessage(**data)


def make_envelope(**overrides) -> CrossAgentMessageEnvelope:
    defaults = dict(envelope_id="env-msg-001", message=make_message())
    defaults.update(overrides)
    return CrossAgentMessageEnvelope(**defaults)


class TestEnums:
    def test_message_intent_type_values(self):
        assert MessageIntentType.REQUEST_ACTION.value == "request_action"
        assert MessageIntentType.CANCEL.value == "cancel"
        assert len(MessageIntentType) == 10

    def test_transport_mode_values(self):
        assert MessageTransportMode.SYNCHRONOUS.value == "synchronous"
        assert MessageTransportMode.FIRE_AND_FORGET.value == "fire_and_forget"
        assert len(MessageTransportMode) == 3

    def test_delivery_status_values(self):
        assert MessageDeliveryStatus.DRAFT.value == "draft"
        assert MessageDeliveryStatus.REJECTED.value == "rejected"
        assert len(MessageDeliveryStatus) == 9

    def test_priority_values(self):
        assert MessagePriority.LOW.value == "low"
        assert MessagePriority.CRITICAL.value == "critical"
        assert len(MessagePriority) == 4

    def test_audience_type_values(self):
        assert AudienceType.SINGLE_AGENT.value == "single_agent"
        assert AudienceType.BROADCAST_LIMITED.value == "broadcast_limited"
        assert len(AudienceType) == 5


class TestAgentMessageHeader:
    def test_valid(self):
        h = make_header()
        assert h.message_id == "msg-001"

    def test_blank_message_id_raises(self):
        with pytest.raises(ValidationError):
            make_header(message_id="  ")

    def test_blank_schema_version_raises(self):
        with pytest.raises(ValidationError):
            make_header(schema_version="  ")

    def test_blank_sender_agent_id_raises(self):
        with pytest.raises(ValidationError):
            make_header(sender_agent_id="  ")

    def test_expires_at_must_be_later(self):
        with pytest.raises(ValidationError, match="expires_at must be later"):
            make_header(expires_at=NOW - timedelta(hours=1))

    def test_expires_at_valid(self):
        h = make_header(expires_at=LATER)
        assert h.expires_at > h.created_at

    def test_trace_id(self):
        h = make_header(trace_id="trace-abc", run_id="run-001")
        assert h.trace_id == "trace-abc"

    def test_sender_role_id(self):
        h = make_header(sender_role_id="manager")
        assert h.sender_role_id == "manager"


class TestMessageAudience:
    def test_valid_single_agent(self):
        a = make_audience()
        assert a.audience_type == AudienceType.SINGLE_AGENT

    def test_blank_audience_id_raises(self):
        with pytest.raises(ValidationError):
            make_audience(audience_id="  ")

    def test_no_targets_raises(self):
        with pytest.raises(ValidationError, match="audience must specify"):
            make_audience(target_agent_ids=[], target_role_ids=[], target_node_ids=[])

    def test_target_by_role(self):
        a = make_audience(audience_type=AudienceType.ROLE_GROUP,
                          target_agent_ids=[],
                          target_role_ids=["coder", "verifier"])
        assert "coder" in a.target_role_ids

    def test_target_by_node(self):
        a = make_audience(audience_type=AudienceType.GRAPH_NODE,
                          target_agent_ids=[],
                          target_node_ids=["node-join"])
        assert len(a.target_node_ids) == 1

    def test_supervisor_only(self):
        a = make_audience(audience_type=AudienceType.SUPERVISOR_ONLY,
                          target_agent_ids=["agent-sup-01"])
        assert a.audience_type == AudienceType.SUPERVISOR_ONLY

    def test_broadcast_limited_with_no_targets_raises(self):
        with pytest.raises(ValidationError, match="audience must specify"):
            make_audience(audience_type=AudienceType.BROADCAST_LIMITED,
                          target_agent_ids=[], target_role_ids=[], target_node_ids=[])

    def test_broadcast_limited_with_targets_valid(self):
        a = make_audience(audience_type=AudienceType.BROADCAST_LIMITED,
                          target_agent_ids=["agent-a", "agent-b"])
        assert len(a.target_agent_ids) == 2


class TestMessagePayload:
    def test_valid(self):
        p = make_payload()
        assert p.payload_id == "pl-001"

    def test_blank_payload_id_raises(self):
        with pytest.raises(ValidationError):
            make_payload(payload_id="  ")

    def test_artifact_refs(self):
        p = make_payload(artifact_refs=["src/auth.py"])
        assert "src/auth.py" in p.artifact_refs

    def test_question_list(self):
        p = make_payload(question_list=["Which DB?", "Auth strategy?"])
        assert len(p.question_list) == 2

    def test_expected_response_type(self):
        p = make_payload(expected_response_type="verification_report")
        assert p.expected_response_type is not None


class TestMessageDeliveryPolicy:
    def test_valid(self):
        dp = make_delivery_policy()
        assert dp.delivery_policy_id == "dp-001"

    def test_blank_policy_id_raises(self):
        with pytest.raises(ValidationError):
            make_delivery_policy(delivery_policy_id="  ")

    def test_max_retries_non_negative(self):
        dp = make_delivery_policy(max_retries=0)
        assert dp.max_retries == 0

    def test_max_retries_negative_raises(self):
        with pytest.raises(ValidationError):
            make_delivery_policy(max_retries=-1)

    def test_timeout_ms_negative_raises(self):
        with pytest.raises(ValidationError):
            make_delivery_policy(timeout_ms=-1)

    def test_idempotency_key(self):
        dp = make_delivery_policy(idempotency_key="idem-xyz")
        assert dp.idempotency_key == "idem-xyz"


class TestMessageAcknowledgement:
    def test_valid(self):
        a = make_ack()
        assert a.ack_id == "ack-001"

    def test_blank_ack_id_raises(self):
        with pytest.raises(ValidationError):
            make_ack(ack_id="  ")

    def test_blank_message_id_raises(self):
        with pytest.raises(ValidationError):
            make_ack(message_id="  ")

    def test_blank_receiver_id_raises(self):
        with pytest.raises(ValidationError):
            make_ack(receiver_agent_id="  ")

    def test_processing_note(self):
        a = make_ack(processing_note="Will process after current task")
        assert a.processing_note is not None


class TestMessageFailureRecord:
    def test_valid(self):
        f = make_failure()
        assert f.failure_id == "fail-001"

    def test_blank_failure_id_raises(self):
        with pytest.raises(ValidationError):
            make_failure(failure_id="  ")

    def test_blank_message_id_raises(self):
        with pytest.raises(ValidationError):
            make_failure(message_id="  ")

    def test_blank_failure_stage_raises(self):
        with pytest.raises(ValidationError):
            make_failure(failure_stage="  ")

    def test_blank_failure_reason_raises(self):
        with pytest.raises(ValidationError):
            make_failure(failure_reason="  ")

    def test_diagnostic_refs(self):
        f = make_failure(diagnostic_refs=["logs/msg-001-trace.json"])
        assert len(f.diagnostic_refs) == 1


class TestCrossAgentMessage:
    def test_valid(self):
        m = make_message()
        assert m.header.message_id == "msg-001"

    def test_fire_and_forget_with_ack_raises(self):
        dp = make_delivery_policy(requires_ack=True)
        h = make_header(transport_mode=MessageTransportMode.FIRE_AND_FORGET)
        with pytest.raises(ValidationError, match="fire_and_forget must not require acknowledgement"):
            make_message(header=h, delivery_policy=dp)

    def test_fire_and_forget_no_ack_valid(self):
        dp = make_delivery_policy(requires_ack=False)
        h = make_header(transport_mode=MessageTransportMode.FIRE_AND_FORGET)
        m = make_message(header=h, delivery_policy=dp)
        assert m.header.transport_mode == MessageTransportMode.FIRE_AND_FORGET

    def test_with_acknowledgement(self):
        ack = make_ack()
        m = make_message(acknowledgement=ack)
        assert m.acknowledgement.ack_id == "ack-001"

    def test_with_failure_record(self):
        fr = make_failure()
        m = make_message(failure_record=fr)
        assert m.failure_record.failure_reason == "audience_mismatch"

    def test_no_default_delivery_policy(self):
        m = make_message()
        assert m.delivery_policy.delivery_policy_id == "dp-001"

    def test_empty_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="  ")


class TestSerialization:
    def test_header_to_dict_and_back(self):
        h = make_header()
        d = h.model_dump()
        h2 = AgentMessageHeader(**d)
        assert h2.message_id == h.message_id

    def test_message_to_dict_and_back(self):
        m = make_message(acknowledgement=make_ack())
        d = m.model_dump()
        m2 = CrossAgentMessage(**d)
        assert m2.header.intent_type == m.header.intent_type
        assert m2.acknowledgement.ack_id == m.acknowledgement.ack_id

    def test_full_envelope_roundtrip(self):
        e = make_envelope()
        d = e.model_dump(mode="json")
        e2 = CrossAgentMessageEnvelope(**d)
        assert e2.envelope_id == e.envelope_id
        assert e2.message.header.sender_agent_id == "agent-mgr-01"

    def test_json_serialization(self):
        e = make_envelope()
        j = e.model_dump_json()
        e2 = CrossAgentMessageEnvelope.model_validate_json(j)
        assert e2.message.audience.target_agent_ids == ["agent-coder-01"]


class TestIntegration:
    def test_request_action_manager_to_specialist(self):
        h = AgentMessageHeader(message_id="msg-req-001", schema_version="1.0",
                               intent_type=MessageIntentType.REQUEST_ACTION,
                               sender_agent_id="agent-mgr-01",
                               trace_id="trace-req", run_id="run-042")
        aud = MessageAudience(audience_id="aud-req", audience_type=AudienceType.SINGLE_AGENT,
                              target_agent_ids=["agent-spec-01"])
        pl = MessagePayload(payload_id="pl-req", summary="Implement API endpoint",
                            data_refs=["specs/api.md"],
                            requested_actions=["write endpoint", "write tests"],
                            expected_response_type="implementation")
        dp = MessageDeliveryPolicy(delivery_policy_id="dp-req", requires_ack=True,
                                   timeout_ms=60000, max_retries=2,
                                   idempotency_key="idem-req-001")
        m = CrossAgentMessage(header=h, audience=aud, payload=pl, delivery_policy=dp)
        assert m.header.intent_type == MessageIntentType.REQUEST_ACTION
        assert m.delivery_policy.max_retries == 2

    def test_handoff_message_with_structured_payload_refs(self):
        h = AgentMessageHeader(message_id="msg-hf-001", schema_version="1.0",
                               intent_type=MessageIntentType.HANDOFF,
                               sender_agent_id="agent-mgr-01",
                               handoff_id="hf-001", delegation_id="del-001")
        aud = MessageAudience(audience_id="aud-hf", audience_type=AudienceType.SINGLE_AGENT,
                              target_agent_ids=["agent-coder-01"])
        pl = MessagePayload(payload_id="pl-hf", summary="Handoff rate limiter task",
                            artifact_refs=["specs/rate_limit.md"],
                            instruction_refs=["packs/coding_standards_v2"],
                            constraints=["must_not_delegate_further"])
        m = CrossAgentMessage(header=h, audience=aud, payload=pl)
        assert m.header.handoff_id == "hf-001"
        assert "must_not_delegate_further" in pl.constraints

    def test_async_blocker_signal_requiring_ack(self):
        h = AgentMessageHeader(message_id="msg-block-001", schema_version="1.0",
                               intent_type=MessageIntentType.SIGNAL_BLOCKER,
                               sender_agent_id="agent-coder-01",
                               transport_mode=MessageTransportMode.ASYNCHRONOUS)
        aud = MessageAudience(audience_id="aud-block", audience_type=AudienceType.SUPERVISOR_ONLY,
                              target_agent_ids=["agent-mgr-01"])
        pl = MessagePayload(payload_id="pl-block", summary="Blocked on API key provisioning",
                            question_list=["Please provision Stripe sandbox key"],
                            constraints=["blocker:stripe_key_missing"])
        dp = MessageDeliveryPolicy(delivery_policy_id="dp-block", requires_ack=True,
                                   timeout_ms=120000, max_retries=3,
                                   idempotency_key="idem-block-001")
        ack = MessageAcknowledgement(ack_id="ack-block", message_id="msg-block-001",
                                     receiver_agent_id="agent-mgr-01",
                                     delivery_status=MessageDeliveryStatus.ACKNOWLEDGED)
        m = CrossAgentMessage(header=h, audience=aud, payload=pl,
                              delivery_policy=dp, acknowledgement=ack)
        assert m.acknowledgement.delivery_status == MessageDeliveryStatus.ACKNOWLEDGED

    def test_failed_message_due_to_audience_validation(self):
        h = make_header(message_id="msg-fail-001")
        aud = make_audience(audience_id="aud-fail",
                            target_agent_ids=["agent-unknown"])
        pl = make_payload(payload_id="pl-fail")
        fr = MessageFailureRecord(failure_id="fail-msg-001", message_id="msg-fail-001",
                                  failure_stage="validation",
                                  failure_reason="target_agent_not_found",
                                  retryable=False, rejected_by="router")
        m = CrossAgentMessage(header=h, audience=aud, payload=pl,
                              failure_record=fr)
        assert m.failure_record.failure_reason == "target_agent_not_found"
        assert m.failure_record.retryable is False

    def test_cancel_message_for_expired_task(self):
        h = AgentMessageHeader(message_id="msg-cancel-001", schema_version="1.0",
                               intent_type=MessageIntentType.CANCEL,
                               sender_agent_id="agent-mgr-01",
                               delegation_id="del-001",
                               created_at=NOW, expires_at=LATER)
        aud = MessageAudience(audience_id="aud-cancel", audience_type=AudienceType.SINGLE_AGENT,
                              target_agent_ids=["agent-coder-01"])
        pl = MessagePayload(payload_id="pl-cancel", summary="Cancel delegated task del-001",
                            data_refs=["delegations/del-001.md"])
        dp = MessageDeliveryPolicy(delivery_policy_id="dp-cancel", requires_ack=True,
                                   timeout_ms=10000, max_retries=1,
                                   idempotency_key="idem-cancel-001")
        m = CrossAgentMessage(header=h, audience=aud, payload=pl, delivery_policy=dp)
        assert m.header.intent_type == MessageIntentType.CANCEL
        assert m.header.delegation_id == "del-001"

    def test_inform_message_broadcast_limited(self):
        h = make_header(message_id="msg-info-001",
                        intent_type=MessageIntentType.INFORM,
                        transport_mode=MessageTransportMode.FIRE_AND_FORGET)
        aud = make_audience(audience_id="aud-info",
                            audience_type=AudienceType.BROADCAST_LIMITED,
                            target_role_ids=["coder", "verifier"],
                            target_agent_ids=[])
        pl = make_payload(payload_id="pl-info",
                          summary="Schema v2 migration schedule updated")
        dp = make_delivery_policy(delivery_policy_id="dp-info", requires_ack=False)
        m = CrossAgentMessage(header=h, audience=aud, payload=pl, delivery_policy=dp)
        assert m.header.transport_mode == MessageTransportMode.FIRE_AND_FORGET
        assert m.delivery_policy.requires_ack is False

    def test_message_with_graph_and_step_lineage(self):
        h = make_header(message_id="msg-graph-001", trace_id="trace-graph",
                        run_id="run-100", step_id="step-05", graph_id="graph-001")
        m = make_message(header=h)
        assert m.header.graph_id == "graph-001"
        assert m.header.step_id == "step-05"
