import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from models.multi_agent_session_graph_contract import (
    SessionNodeType, SessionEdgeType, NodeStatus, EdgeStatus, GraphStatus,
    SessionGraphNode, SessionGraphEdge, BranchStateRecord, JoinStateRecord,
    GraphCheckpointRecord, SessionGraphMetadata, MultiAgentSessionGraph,
    SessionGraphEnvelope,
)

NOW = datetime.now(timezone.utc)


def make_node(node_id="node-entry", **overrides) -> SessionGraphNode:
    defaults = dict(node_id=node_id, node_type=SessionNodeType.PARENT_RUN,
                    label="Root run", run_id="run-001",
                    status=NodeStatus.PENDING, created_at=NOW, updated_at=NOW)
    defaults.update(overrides)
    return SessionGraphNode(**defaults)


def make_edge(edge_id="edge-001", **overrides) -> SessionGraphEdge:
    defaults = dict(edge_id=edge_id, edge_type=SessionEdgeType.CONTROL_FLOW,
                    from_node_id="node-entry", to_node_id="node-child",
                    status=EdgeStatus.ACTIVE, created_at=NOW)
    defaults.update(overrides)
    return SessionGraphEdge(**defaults)


def make_branch(**overrides) -> BranchStateRecord:
    defaults = dict(branch_id="branch-001", entry_node_id="node-entry",
                    branch_node_ids=["node-child-a", "node-child-b"],
                    branch_reason="Parallel verification")
    defaults.update(overrides)
    return BranchStateRecord(**defaults)


def make_join(**overrides) -> JoinStateRecord:
    defaults = dict(join_id="join-001", join_node_id="node-join",
                    incoming_node_ids=["node-a", "node-b"],
                    required_completion_count=2,
                    join_policy="all")
    defaults.update(overrides)
    return JoinStateRecord(**defaults)


def make_checkpoint(**overrides) -> GraphCheckpointRecord:
    defaults = dict(checkpoint_id="cp-001", graph_id="graph-001",
                    graph_status=GraphStatus.ACTIVE,
                    active_node_ids=["node-entry"],
                    created_at=NOW)
    defaults.update(overrides)
    return GraphCheckpointRecord(**defaults)


def make_metadata(**overrides) -> SessionGraphMetadata:
    defaults = dict(graph_id="graph-001", session_id="session-001",
                    root_run_id="run-001",
                    supervisor_agent_id="agent-mgr-01",
                    graph_status=GraphStatus.ACTIVE,
                    entry_node_id="node-entry",
                    terminal_node_ids=["node-terminal"],
                    created_at=NOW, updated_at=NOW)
    defaults.update(overrides)
    return SessionGraphMetadata(**defaults)


def make_graph(meta=None, nodes=None, edges=None, **overrides) -> MultiAgentSessionGraph:
    m = meta or make_metadata()
    ns = nodes or [
        make_node("node-entry", node_type=SessionNodeType.PARENT_RUN),
        make_node("node-child", node_type=SessionNodeType.CHILD_RUN),
        make_node("node-terminal", node_type=SessionNodeType.TERMINAL_NODE),
    ]
    es = edges or [
        make_edge("edge-001", from_node_id="node-entry", to_node_id="node-child"),
        make_edge("edge-002", from_node_id="node-child", to_node_id="node-terminal"),
    ]
    data = dict(metadata=m, nodes=ns, edges=es)
    data.update(overrides)
    return MultiAgentSessionGraph(**data)


def make_envelope(**overrides) -> SessionGraphEnvelope:
    defaults = dict(envelope_id="env-graph-001", graph=make_graph())
    defaults.update(overrides)
    return SessionGraphEnvelope(**defaults)


class TestEnums:
    def test_session_node_type_values(self):
        assert SessionNodeType.PARENT_RUN.value == "parent_run"
        assert SessionNodeType.TERMINAL_NODE.value == "terminal_node"
        assert len(SessionNodeType) == 11

    def test_session_edge_type_values(self):
        assert SessionEdgeType.DELEGATES_TO.value == "delegates_to"
        assert SessionEdgeType.BLOCKED_BY.value == "blocked_by"
        assert len(SessionEdgeType) == 8

    def test_node_status_values(self):
        assert NodeStatus.PENDING.value == "pending"
        assert NodeStatus.CANCELLED.value == "cancelled"
        assert len(NodeStatus) == 8

    def test_edge_status_values(self):
        assert EdgeStatus.ACTIVE.value == "active"
        assert EdgeStatus.CANCELLED.value == "cancelled"
        assert len(EdgeStatus) == 5

    def test_graph_status_values(self):
        assert GraphStatus.DRAFT.value == "draft"
        assert GraphStatus.CANCELLED.value == "cancelled"
        assert len(GraphStatus) == 7


class TestSessionGraphNode:
    def test_valid(self):
        n = make_node()
        assert n.node_id == "node-entry"

    def test_blank_node_id_raises(self):
        with pytest.raises(ValidationError):
            make_node(node_id="  ")

    def test_parent_run_type(self):
        n = make_node(node_type=SessionNodeType.PARENT_RUN, run_id="run-001")
        assert n.node_type == SessionNodeType.PARENT_RUN

    def test_child_run_node(self):
        n = make_node(node_id="node-child", node_type=SessionNodeType.CHILD_RUN,
                      parent_node_id="node-parent")
        assert n.parent_node_id == "node-parent"

    def test_handoff_node(self):
        n = make_node(node_id="node-hf", node_type=SessionNodeType.HANDOFF,
                      handoff_id="hf-001")
        assert n.handoff_id == "hf-001"

    def test_delegation_node(self):
        n = make_node(node_id="node-del", node_type=SessionNodeType.DELEGATION,
                      delegation_id="del-001")
        assert n.delegation_id == "del-001"

    def test_approval_gate_node(self):
        n = make_node(node_id="node-approve", node_type=SessionNodeType.APPROVAL_GATE)
        assert n.node_type == SessionNodeType.APPROVAL_GATE

    def test_input_output_refs(self):
        n = make_node(input_refs=["spec.md"], output_refs=["result.json"])
        assert "spec.md" in n.input_refs
        assert "result.json" in n.output_refs


class TestSessionGraphEdge:
    def test_valid(self):
        e = make_edge()
        assert e.edge_id == "edge-001"

    def test_blank_edge_id_raises(self):
        with pytest.raises(ValidationError):
            make_edge(edge_id="  ")

    def test_delegates_to_type(self):
        e = make_edge(edge_type=SessionEdgeType.DELEGATES_TO)
        assert e.edge_type == SessionEdgeType.DELEGATES_TO

    def test_conditional_branch_with_ref(self):
        e = make_edge(edge_type=SessionEdgeType.CONDITIONAL_BRANCH,
                      condition_ref="condition:result=ok")
        assert e.condition_ref == "condition:result=ok"

    def test_blocked_by(self):
        e = make_edge(edge_type=SessionEdgeType.BLOCKED_BY)
        assert e.edge_type == SessionEdgeType.BLOCKED_BY

    def test_traversed_at(self):
        e = make_edge(traversed_at=NOW)
        assert e.traversed_at is not None


class TestBranchStateRecord:
    def test_valid(self):
        b = make_branch()
        assert b.branch_id == "branch-001"

    def test_blank_branch_id_raises(self):
        with pytest.raises(ValidationError):
            make_branch(branch_id="  ")

    def test_completed_node_ids(self):
        b = make_branch(completed_node_ids=["node-child-a"])
        assert "node-child-a" in b.completed_node_ids

    def test_failed_node_ids(self):
        b = make_branch(failed_node_ids=["node-child-b"])
        assert len(b.failed_node_ids) == 1


class TestJoinStateRecord:
    def test_valid(self):
        j = make_join()
        assert j.join_id == "join-001"

    def test_blank_join_id_raises(self):
        with pytest.raises(ValidationError):
            make_join(join_id="  ")

    def test_required_count_exceeds_incoming_raises(self):
        with pytest.raises(ValidationError, match="must not exceed"):
            make_join(incoming_node_ids=["node-a"], required_completion_count=3)

    def test_required_count_equal_to_incoming(self):
        j = make_join(incoming_node_ids=["node-a", "node-b"], required_completion_count=2)
        assert j.required_completion_count == 2

    def test_completed_incoming_ids(self):
        j = make_join(completed_incoming_ids=["node-a"])
        assert len(j.completed_incoming_ids) == 1

    def test_merge_notes(self):
        j = make_join(merge_notes="All branches completed successfully")
        assert j.merge_notes is not None


class TestGraphCheckpointRecord:
    def test_valid(self):
        c = make_checkpoint()
        assert c.checkpoint_id == "cp-001"

    def test_blank_checkpoint_id_raises(self):
        with pytest.raises(ValidationError):
            make_checkpoint(checkpoint_id="  ")

    def test_blank_graph_id_raises(self):
        with pytest.raises(ValidationError):
            make_checkpoint(graph_id="  ")

    def test_waiting_and_blocked_nodes(self):
        c = make_checkpoint(waiting_node_ids=["node-wait"],
                            blocked_node_ids=["node-block"])
        assert "node-wait" in c.waiting_node_ids
        assert "node-block" in c.blocked_node_ids

    def test_snapshot_ref(self):
        c = make_checkpoint(snapshot_ref="snapshots/graph-001-cp-001.json")
        assert c.snapshot_ref is not None


class TestSessionGraphMetadata:
    def test_valid(self):
        m = make_metadata()
        assert m.graph_id == "graph-001"

    def test_blank_graph_id_raises(self):
        with pytest.raises(ValidationError):
            make_metadata(graph_id="  ")

    def test_blank_session_id_raises(self):
        with pytest.raises(ValidationError):
            make_metadata(session_id="  ")

    def test_blank_entry_node_id(self):
        with pytest.raises(ValidationError):
            make_metadata(entry_node_id="  ")


class TestMultiAgentSessionGraph:
    def test_valid_graph(self):
        g = make_graph()
        assert g.metadata.graph_id == "graph-001"

    def test_duplicate_node_id_raises(self):
        nodes = [make_node("node-dupe"), make_node("node-dupe")]
        with pytest.raises(ValidationError, match="duplicate node_id"):
            make_graph(nodes=nodes)

    def test_duplicate_edge_id_raises(self):
        edges = [make_edge("edge-dupe"), make_edge("edge-dupe")]
        with pytest.raises(ValidationError, match="duplicate edge_id"):
            make_graph(edges=edges)

    def test_edge_from_node_not_found_raises(self):
        edges = [make_edge("edge-bad", from_node_id="node-nonexistent")]
        with pytest.raises(ValidationError, match="not found in nodes"):
            make_graph(edges=edges)

    def test_edge_to_node_not_found_raises(self):
        edges = [make_edge("edge-bad", to_node_id="node-nonexistent")]
        with pytest.raises(ValidationError, match="not found in nodes"):
            make_graph(edges=edges)

    def test_parent_node_refers_to_existing_node(self):
        meta = make_metadata(entry_node_id="node-parent",
                             terminal_node_ids=["node-term"])
        nodes = [make_node("node-parent"), make_node("node-child",
                 parent_node_id="node-parent"),
                 make_node("node-term", node_type=SessionNodeType.TERMINAL_NODE)]
        edges = [make_edge("e1", from_node_id="node-parent", to_node_id="node-child"),
                 make_edge("e2", from_node_id="node-child", to_node_id="node-term")]
        g = make_graph(meta=meta, nodes=nodes, edges=edges)
        assert len(g.nodes) == 3

    def test_parent_node_refers_to_nonexistent_raises(self):
        nodes = [make_node("node-child", parent_node_id="node-missing"),
                 make_node("node-term", node_type=SessionNodeType.TERMINAL_NODE)]
        edges = [make_edge("e1", from_node_id="node-child", to_node_id="node-term")]
        with pytest.raises(ValidationError, match="parent_node_id"):
            make_graph(nodes=nodes, edges=edges)

    def test_no_terminal_node_raises(self):
        nodes = [make_node("node-a"), make_node("node-b")]
        edges = [make_edge("e1", from_node_id="node-a", to_node_id="node-b")]
        with pytest.raises(ValidationError, match="at least one terminal_node"):
            make_graph(nodes=nodes, edges=edges)

    def test_entry_node_not_found_raises(self):
        meta = make_metadata(entry_node_id="node-nonexistent")
        with pytest.raises(ValidationError, match="entry_node_id"):
            make_graph(meta=meta)

    def test_branch_entry_not_found_raises(self):
        br = make_branch(entry_node_id="node-nonexistent")
        with pytest.raises(ValidationError, match="not found in nodes"):
            make_graph(branches=[br])

    def test_branch_node_not_found_raises(self):
        br = make_branch(branch_node_ids=["node-nonexistent"])
        with pytest.raises(ValidationError, match="not found in nodes"):
            make_graph(branches=[br])

    def test_join_node_not_found_raises(self):
        jn = make_join(join_node_id="node-nonexistent")
        with pytest.raises(ValidationError, match="not found in nodes"):
            make_graph(joins=[jn])

    def test_join_incoming_node_not_found_raises(self):
        jn = make_join(incoming_node_ids=["node-nonexistent"],
                       required_completion_count=1)
        with pytest.raises(ValidationError, match="not found in nodes"):
            make_graph(joins=[jn])

    def test_checkpoint_graph_id_mismatch_raises(self):
        cp = make_checkpoint(graph_id="graph-other")
        with pytest.raises(ValidationError, match="checkpoint"):
            make_graph(checkpoints=[cp])


class TestSerialization:
    def test_node_to_dict_and_back(self):
        n = make_node()
        d = n.model_dump()
        n2 = SessionGraphNode(**d)
        assert n2.node_id == n.node_id

    def test_graph_to_dict_and_back(self):
        g = make_graph()
        d = g.model_dump()
        g2 = MultiAgentSessionGraph(**d)
        assert g2.metadata.graph_id == g.metadata.graph_id
        assert len(g2.nodes) == len(g.nodes)

    def test_full_envelope_roundtrip(self):
        e = make_envelope()
        d = e.model_dump(mode="json")
        e2 = SessionGraphEnvelope(**d)
        assert e2.envelope_id == e.envelope_id
        assert e2.graph.metadata.session_id == e.graph.metadata.session_id

    def test_json_serialization(self):
        e = make_envelope()
        j = e.model_dump_json()
        e2 = SessionGraphEnvelope.model_validate_json(j)
        assert e2.graph.metadata.entry_node_id == "node-entry"


class TestIntegration:
    def test_simple_parent_child_delegation(self):
        meta = SessionGraphMetadata(graph_id="graph-simple", session_id="session-simple",
                                    entry_node_id="node-parent",
                                    terminal_node_ids=["node-terminal"],
                                    graph_status=GraphStatus.ACTIVE)
        nodes = [
            SessionGraphNode(node_id="node-parent", node_type=SessionNodeType.PARENT_RUN,
                             label="Manager", status=NodeStatus.RUNNING),
            SessionGraphNode(node_id="node-child", node_type=SessionNodeType.CHILD_RUN,
                             label="Coder", status=NodeStatus.READY,
                             parent_node_id="node-parent"),
            SessionGraphNode(node_id="node-terminal", node_type=SessionNodeType.TERMINAL_NODE,
                             label="Done", status=NodeStatus.PENDING),
        ]
        edges = [
            SessionGraphEdge(edge_id="e-delegate", edge_type=SessionEdgeType.DELEGATES_TO,
                             from_node_id="node-parent", to_node_id="node-child",
                             status=EdgeStatus.TRAVERSED),
            SessionGraphEdge(edge_id="e-return", edge_type=SessionEdgeType.RETURNS_TO,
                             from_node_id="node-child", to_node_id="node-terminal",
                             status=EdgeStatus.ACTIVE),
        ]
        g = MultiAgentSessionGraph(metadata=meta, nodes=nodes, edges=edges)
        assert g.metadata.graph_status == GraphStatus.ACTIVE
        assert len(g.edges) == 2

    def test_verification_branch_returning_to_supervisor(self):
        meta = SessionGraphMetadata(graph_id="graph-verify", session_id="session-verify",
                                    entry_node_id="node-supervisor",
                                    terminal_node_ids=["node-terminal"])
        nodes = [
            SessionGraphNode(node_id="node-supervisor", node_type=SessionNodeType.PARENT_RUN,
                             label="Supervisor", status=NodeStatus.RUNNING),
            SessionGraphNode(node_id="node-verify", node_type=SessionNodeType.VERIFICATION_STEP,
                             label="Verifier", status=NodeStatus.READY),
            SessionGraphNode(node_id="node-join", node_type=SessionNodeType.JOIN_NODE,
                             label="Join", status=NodeStatus.WAITING),
            SessionGraphNode(node_id="node-terminal", node_type=SessionNodeType.TERMINAL_NODE,
                             label="Done", status=NodeStatus.PENDING),
        ]
        edges = [
            SessionGraphEdge(edge_id="e-to-verify", edge_type=SessionEdgeType.DELEGATES_TO,
                             from_node_id="node-supervisor", to_node_id="node-verify"),
            SessionGraphEdge(edge_id="e-verify-return", edge_type=SessionEdgeType.RETURNS_TO,
                             from_node_id="node-verify", to_node_id="node-join"),
            SessionGraphEdge(edge_id="e-join-terminal", edge_type=SessionEdgeType.CONTROL_FLOW,
                             from_node_id="node-join", to_node_id="node-terminal"),
        ]
        g = MultiAgentSessionGraph(metadata=meta, nodes=nodes, edges=edges)
        assert g.metadata.graph_id == "graph-verify"

    def test_blocked_node_and_recovery_checkpoint(self):
        meta = SessionGraphMetadata(graph_id="graph-blocked", session_id="session-blocked",
                                    entry_node_id="node-entry",
                                    terminal_node_ids=["node-terminal"],
                                    graph_status=GraphStatus.RECOVERING)
        nodes = [
            SessionGraphNode(node_id="node-entry", node_type=SessionNodeType.PARENT_RUN,
                             status=NodeStatus.COMPLETED),
            SessionGraphNode(node_id="node-blocked", node_type=SessionNodeType.STEP,
                             label="Blocked step", status=NodeStatus.BLOCKED),
            SessionGraphNode(node_id="node-terminal", node_type=SessionNodeType.TERMINAL_NODE,
                             status=NodeStatus.PENDING),
        ]
        edges = [
            SessionGraphEdge(edge_id="e-to-blocked", edge_type=SessionEdgeType.CONTROL_FLOW,
                             from_node_id="node-entry", to_node_id="node-blocked",
                             status=EdgeStatus.TRAVERSED),
            SessionGraphEdge(edge_id="e-blocked", edge_type=SessionEdgeType.BLOCKED_BY,
                             from_node_id="node-blocked", to_node_id="node-terminal",
                             status=EdgeStatus.BLOCKED),
        ]
        cp = GraphCheckpointRecord(checkpoint_id="cp-blocked", graph_id="graph-blocked",
                                   graph_status=GraphStatus.RECOVERING,
                                   active_node_ids=["node-entry"],
                                   blocked_node_ids=["node-blocked"],
                                   snapshot_ref="snapshots/blocked-state.json")
        g = MultiAgentSessionGraph(metadata=meta, nodes=nodes, edges=edges,
                                   checkpoints=[cp])
        assert "node-blocked" in g.checkpoints[0].blocked_node_ids
        assert g.metadata.graph_status == GraphStatus.RECOVERING

    def test_conditional_branch_graph(self):
        meta = SessionGraphMetadata(graph_id="graph-cond", session_id="session-cond",
                                    entry_node_id="node-router",
                                    terminal_node_ids=["node-terminal"])
        nodes = [
            SessionGraphNode(node_id="node-router", node_type=SessionNodeType.ROUTING_DECISION,
                             label="Router", status=NodeStatus.RUNNING),
            SessionGraphNode(node_id="node-branch-a", node_type=SessionNodeType.CHILD_RUN,
                             label="Branch A", status=NodeStatus.READY),
            SessionGraphNode(node_id="node-branch-b", node_type=SessionNodeType.CHILD_RUN,
                             label="Branch B", status=NodeStatus.READY),
            SessionGraphNode(node_id="node-terminal", node_type=SessionNodeType.TERMINAL_NODE,
                             label="Done", status=NodeStatus.PENDING),
        ]
        edges = [
            SessionGraphEdge(edge_id="e-branch-a", edge_type=SessionEdgeType.CONDITIONAL_BRANCH,
                             from_node_id="node-router", to_node_id="node-branch-a",
                             condition_ref="route=a", status=EdgeStatus.ACTIVE),
            SessionGraphEdge(edge_id="e-branch-b", edge_type=SessionEdgeType.CONDITIONAL_BRANCH,
                             from_node_id="node-router", to_node_id="node-branch-b",
                             condition_ref="route=b", status=EdgeStatus.INACTIVE),
        ]
        br = BranchStateRecord(branch_id="branch-a", entry_node_id="node-branch-a",
                               branch_node_ids=["node-branch-a"],
                               branch_reason="Route A selected")
        g = MultiAgentSessionGraph(metadata=meta, nodes=nodes, edges=edges, branches=[br])
        assert len(g.edges) == 2
        assert g.branches[0].branch_reason == "Route A selected"

    def test_join_node_waiting_on_multiple_child_returns(self):
        meta = SessionGraphMetadata(graph_id="graph-join", session_id="session-join",
                                    entry_node_id="node-parent",
                                    terminal_node_ids=["node-terminal"])
        nodes = [
            SessionGraphNode(node_id="node-parent", node_type=SessionNodeType.PARENT_RUN,
                             label="Parent", status=NodeStatus.RUNNING),
            SessionGraphNode(node_id="node-child-a", node_type=SessionNodeType.CHILD_RUN,
                             label="Child A", status=NodeStatus.COMPLETED),
            SessionGraphNode(node_id="node-child-b", node_type=SessionNodeType.CHILD_RUN,
                             label="Child B", status=NodeStatus.RUNNING),
            SessionGraphNode(node_id="node-join", node_type=SessionNodeType.JOIN_NODE,
                             label="Join", status=NodeStatus.WAITING),
            SessionGraphNode(node_id="node-terminal", node_type=SessionNodeType.TERMINAL_NODE,
                             label="Done", status=NodeStatus.PENDING),
        ]
        edges = [
            SessionGraphEdge(edge_id="e-to-a", edge_type=SessionEdgeType.DELEGATES_TO,
                             from_node_id="node-parent", to_node_id="node-child-a"),
            SessionGraphEdge(edge_id="e-to-b", edge_type=SessionEdgeType.DELEGATES_TO,
                             from_node_id="node-parent", to_node_id="node-child-b"),
            SessionGraphEdge(edge_id="e-a-join", edge_type=SessionEdgeType.JOINS_INTO,
                             from_node_id="node-child-a", to_node_id="node-join"),
            SessionGraphEdge(edge_id="e-b-join", edge_type=SessionEdgeType.JOINS_INTO,
                             from_node_id="node-child-b", to_node_id="node-join"),
            SessionGraphEdge(edge_id="e-join-term", edge_type=SessionEdgeType.CONTROL_FLOW,
                             from_node_id="node-join", to_node_id="node-terminal"),
        ]
        jn = JoinStateRecord(join_id="join-main", join_node_id="node-join",
                             incoming_node_ids=["node-child-a", "node-child-b"],
                             required_completion_count=2,
                             completed_incoming_ids=["node-child-a"],
                             join_policy="all")
        g = MultiAgentSessionGraph(metadata=meta, nodes=nodes, edges=edges, joins=[jn])
        assert len(g.joins) == 1
        assert g.joins[0].required_completion_count == 2
        assert len(g.joins[0].completed_incoming_ids) == 1
