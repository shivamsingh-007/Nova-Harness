# P53 — Cross-Agent Messaging Contract

## Purpose
Typed, versioned, auditable messages for agent-to-agent communication with explicit intent, audience, structured payload, delivery policy, acknowledgement, and failure recording.

## Core Types

### MessageHeader
- **message_id** (str): Unique message identifier
- **schema_version** (str): Schema version for evolution
- **intent_type** (IntentType): Purpose of the message
- **transport_mode** (TransportMode): Synchronous or asynchronous
- **priority** (Priority, optional): Normal, high, critical
- **sender_agent_id** (str): Originating agent
- **sender_role_id** (str, optional): Agent's role at time of sending
- **trace_id, run_id, step_id** (str, optional): Orchestration context
- **handoff_id, delegation_id** (str, optional): Cross-reference to handoff/delegation records
- **graph_id** (str, optional): Session graph reference
- **created_at, expires_at** (datetime): Temporal bounds

### Audience
- **audience_type** (AudienceType): `single_agent`, `broadcast_all`, `broadcast_role_cohort`, `broadcast_limited`, `supervisor_only`
- **target_agent_ids, target_role_ids, target_node_ids** (list[str]): Audience specification
- **explicit_audience_note** (str, optional): Human/agent rationale for audience choice

### Payload
- **payload_id** (str): Unique payload identifier
- **summary** (str): Human-readable summary of the message content
- **data_refs, artifact_refs, instruction_refs** (list[str]): References to supporting materials
- **question_list** (list[str], optional): Explicit questions for the receiver
- **requested_actions** (list[str], optional): Requested actions for intent_request messages
- **constraints** (list[str]): Execution constraints and decorations

### DeliveryPolicy
- **requires_ack** (bool): Whether acknowledgement is required
- **timeout_ms** (int): Maximum delivery wait time
- **max_retries** (int): Retry count on delivery failure
- **retry_backoff_policy** (str, optional): `exponential` or `linear`
- **idempotency_key** (str, optional): Deduplication key

### Acknowledgement
- **ack_id** (str): Unique ACK identifier
- **message_id** (str): Reference to the acknowledged message
- **receiver_agent_id** (str): Who received
- **delivery_status** (DeliveryStatus): `acknowledged`, `delivered`, `read`, `rejected`, `deferred`, `failed`
- **received_at** (datetime): When received
- **processing_note** (str, optional): Receiver's processing note

### FailureRecord
- **failure_id** (str): Unique failure identifier
- **message_id** (str): Reference to the failed message
- **failure_stage** (str): Where the failure occurred (e.g., `validation`, `delivery`, `processing`)
- **failure_reason** (str): Machine-readable and human-readable failure reason
- **retryable** (bool): Whether the failure is transient
- **rejected_by** (str, optional): Which component rejected the message
- **diagnostic_refs** (list[str]): References to diagnostic logs/artifacts

### IntentType Enum
- `signal_blocker`, `request_action`, `request_info`, `handoff`, `cancel`, `status_update`, `error_report`, `ack`, `custom`

### AudienceType Enum
- `single_agent`, `broadcast_all`, `broadcast_role_cohort`, `broadcast_limited`, `supervisor_only`

### TransportMode Enum
- `synchronous`, `asynchronous`

### Priority Enum
- `normal`, `high`, `critical`

### DeliveryStatus Enum
- `acknowledged`, `delivered`, `read`, `rejected`, `deferred`, `failed`

## Cross-Field Validation Rules
1. **audience must specify at least one target** — at least one of `target_agent_ids`, `target_role_ids`, `target_node_ids` must be non-empty
2. **broadcast_all should have no resolved targets** — must not supply target lists (they should be empty or defaults)
3. **supervisor_only must exclude unrelated** — must not supply `target_role_ids` or `target_node_ids`
4. **delivery policy cannot have zero max_retries with requires_ack true** — contradictory: requiring ACK but never retrying
5. **expires_at must be after created_at** — temporal consistency

## State Machine
```
Pending → Acknowledged → Delivered → Read → Processing → Complete
                                  ↘ Failed
                                     ↘ Retry → Re-deliver
```
