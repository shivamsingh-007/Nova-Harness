# Session Graph Protocol

## Purpose
Topology of a multi-agent session as a graph of nodes and edges — parent-child runs, handoffs, delegation paths, branches, joins, and checkpoints for recovery.

## Node Types (11)
| Type | Purpose |
|------|---------|
| `parent_run` | Root orchestration run |
| `child_run` | Sub-run delegated to an agent |
| `agent_role` | Role-based agent node |
| `step` | Atomic execution step |
| `handoff` | Handoff transfer point |
| `delegation` | Delegation boundary |
| `routing_decision` | Conditional routing |
| `approval_gate` | Human/approval checkpoint |
| `verification_step` | Verification execution |
| `join_node` | Fan-in merge point |
| `terminal_node` | Graph completion point |

## Edge Types (8)
| Type | Purpose |
|------|---------|
| `control_flow` | Sequential execution |
| `delegates_to` | Work delegation |
| `returns_to` | Return from delegation |
| `handoff_to` | Handoff transfer |
| `depends_on` | Dependency ordering |
| `conditional_branch` | Conditional routing |
| `joins_into` | Fan-in to join node |
| `blocked_by` | Blocked on dependency |

## Graph Rules
- One entry node, one or more terminal nodes
- Every node and edge has a stable unique ID
- Parent-child relationships explicit through `parent_node_id`
- Join nodes define `required_completion_count` for fan-in
- Checkpoints capture active/waiting/blocked nodes for recovery
- Branches track subgraph state during conditional or parallel execution

## Integration
P52 connects to P44/P45 (loop atoms as nodes), P46 (delegation edges), P47 (routing edges), P48 (skill-attached nodes), P49 (hook points around graph movement), P50 (role-attached nodes), and P51 (handoff/return payloads on edges).
