from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class SessionNodeType(str, Enum):
    PARENT_RUN = "parent_run"
    CHILD_RUN = "child_run"
    AGENT_ROLE = "agent_role"
    STEP = "step"
    HANDOFF = "handoff"
    DELEGATION = "delegation"
    ROUTING_DECISION = "routing_decision"
    APPROVAL_GATE = "approval_gate"
    VERIFICATION_STEP = "verification_step"
    JOIN_NODE = "join_node"
    TERMINAL_NODE = "terminal_node"


class SessionEdgeType(str, Enum):
    CONTROL_FLOW = "control_flow"
    DELEGATES_TO = "delegates_to"
    RETURNS_TO = "returns_to"
    HANDOFF_TO = "handoff_to"
    DEPENDS_ON = "depends_on"
    CONDITIONAL_BRANCH = "conditional_branch"
    JOINS_INTO = "joins_into"
    BLOCKED_BY = "blocked_by"


class NodeStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


ACTIONABLE_NODE_STATUSES = {NodeStatus.READY, NodeStatus.RUNNING,
                            NodeStatus.WAITING, NodeStatus.BLOCKED}


class EdgeStatus(str, Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    TRAVERSED = "traversed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class GraphStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


ACTIVE_GRAPH_STATUSES = {GraphStatus.ACTIVE, GraphStatus.RECOVERING}


class SessionGraphNode(BaseModel):
    node_id: str = Field(min_length=1)
    node_type: SessionNodeType
    label: Optional[str] = None
    run_id: Optional[str] = None
    agent_id: Optional[str] = None
    role_id: Optional[str] = None
    step_id: Optional[str] = None
    handoff_id: Optional[str] = None
    delegation_id: Optional[str] = None
    status: NodeStatus = NodeStatus.PENDING
    parent_node_id: Optional[str] = None
    input_refs: List[str] = Field(default_factory=list)
    output_refs: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator("node_id")
    @classmethod
    def node_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("node_id must not be blank")
        return v.strip()


class SessionGraphEdge(BaseModel):
    edge_id: str = Field(min_length=1)
    edge_type: SessionEdgeType
    from_node_id: str = Field(min_length=1)
    to_node_id: str = Field(min_length=1)
    status: EdgeStatus = EdgeStatus.INACTIVE
    condition_ref: Optional[str] = None
    trigger_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    traversed_at: Optional[datetime] = None

    @field_validator("edge_id")
    @classmethod
    def edge_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("edge_id must not be blank")
        return v.strip()


class BranchStateRecord(BaseModel):
    branch_id: str = Field(min_length=1)
    entry_node_id: str = Field(min_length=1)
    branch_node_ids: List[str] = Field(default_factory=list)
    branch_reason: Optional[str] = None
    expected_completion_policy: Optional[str] = None
    active_node_ids: List[str] = Field(default_factory=list)
    completed_node_ids: List[str] = Field(default_factory=list)
    failed_node_ids: List[str] = Field(default_factory=list)
    branch_status: str = "active"

    @field_validator("branch_id")
    @classmethod
    def branch_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("branch_id must not be blank")
        return v.strip()


class JoinStateRecord(BaseModel):
    join_id: str = Field(min_length=1)
    join_node_id: str = Field(min_length=1)
    incoming_node_ids: List[str] = Field(min_length=1)
    required_completion_count: int = Field(default=1, ge=1)
    completed_incoming_ids: List[str] = Field(default_factory=list)
    join_policy: Optional[str] = None
    join_status: str = "waiting"
    merge_notes: Optional[str] = None

    @field_validator("join_id")
    @classmethod
    def join_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("join_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def completion_count_not_exceed_incoming(self) -> "JoinStateRecord":
        if self.required_completion_count > len(self.incoming_node_ids):
            raise ValueError(
                f"required_completion_count ({self.required_completion_count}) "
                f"must not exceed incoming_node_ids count ({len(self.incoming_node_ids)})"
            )
        return self


class GraphCheckpointRecord(BaseModel):
    checkpoint_id: str = Field(min_length=1)
    graph_id: str = Field(min_length=1)
    graph_status: GraphStatus
    active_node_ids: List[str] = Field(default_factory=list)
    waiting_node_ids: List[str] = Field(default_factory=list)
    blocked_node_ids: List[str] = Field(default_factory=list)
    last_traversed_edge_ids: List[str] = Field(default_factory=list)
    snapshot_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator("checkpoint_id")
    @classmethod
    def checkpoint_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("checkpoint_id must not be blank")
        return v.strip()

    @field_validator("graph_id")
    @classmethod
    def graph_id_in_checkpoint_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("graph_id in checkpoint must not be blank")
        return v.strip()


class SessionGraphMetadata(BaseModel):
    graph_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    root_run_id: Optional[str] = None
    supervisor_agent_id: Optional[str] = None
    graph_status: GraphStatus = GraphStatus.DRAFT
    entry_node_id: str = Field(min_length=1)
    terminal_node_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"

    @field_validator("graph_id")
    @classmethod
    def graph_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("graph_id must not be blank")
        return v.strip()

    @field_validator("session_id")
    @classmethod
    def session_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("session_id must not be blank")
        return v.strip()

    @field_validator("entry_node_id")
    @classmethod
    def entry_node_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("entry_node_id must not be blank")
        return v.strip()


def _node_ids(graph) -> set:
    return {n.node_id for n in graph.nodes}


class MultiAgentSessionGraph(BaseModel):
    metadata: SessionGraphMetadata
    nodes: List[SessionGraphNode] = Field(default_factory=list)
    edges: List[SessionGraphEdge] = Field(default_factory=list)
    branches: List[BranchStateRecord] = Field(default_factory=list)
    joins: List[JoinStateRecord] = Field(default_factory=list)
    checkpoints: List[GraphCheckpointRecord] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_ids(self) -> "MultiAgentSessionGraph":
        node_ids = _node_ids(self)
        edge_ids = {e.edge_id for e in self.edges}
        seen_nodes = set()
        seen_edges = set()

        for n in self.nodes:
            if n.node_id in seen_nodes:
                raise ValueError(f"duplicate node_id: {n.node_id}")
            seen_nodes.add(n.node_id)
            if n.parent_node_id and n.parent_node_id not in node_ids:
                raise ValueError(
                    f"parent_node_id '{n.parent_node_id}' on node '{n.node_id}' "
                    f"does not reference an existing node"
                )

        for e in self.edges:
            if e.edge_id in seen_edges:
                raise ValueError(f"duplicate edge_id: {e.edge_id}")
            seen_edges.add(e.edge_id)
            if e.from_node_id not in node_ids:
                raise ValueError(f"edge '{e.edge_id}' from_node_id '{e.from_node_id}' not found in nodes")
            if e.to_node_id not in node_ids:
                raise ValueError(f"edge '{e.edge_id}' to_node_id '{e.to_node_id}' not found in nodes")

        for b in self.branches:
            if b.entry_node_id not in node_ids:
                raise ValueError(f"branch '{b.branch_id}' entry_node_id '{b.entry_node_id}' not found in nodes")
            for nid in b.branch_node_ids:
                if nid not in node_ids:
                    raise ValueError(f"branch '{b.branch_id}' references node '{nid}' not found in nodes")

        for j in self.joins:
            if j.join_node_id not in node_ids:
                raise ValueError(f"join '{j.join_id}' join_node_id '{j.join_node_id}' not found in nodes")
            for nid in j.incoming_node_ids:
                if nid not in node_ids:
                    raise ValueError(f"join '{j.join_id}' incoming_node '{nid}' not found in nodes")

        n_terminal = sum(1 for n in self.nodes if n.node_type == SessionNodeType.TERMINAL_NODE)
        if n_terminal == 0:
            raise ValueError("at least one terminal_node must exist in the graph")

        meta = self.metadata
        if meta.entry_node_id not in node_ids:
            raise ValueError(f"entry_node_id '{meta.entry_node_id}' not found in nodes")

        for cp in self.checkpoints:
            if cp.graph_id != meta.graph_id:
                raise ValueError(
                    f"checkpoint '{cp.checkpoint_id}' references graph_id "
                    f"'{cp.graph_id}' but metadata graph_id is '{meta.graph_id}'"
                )

        return self


class SessionGraphEnvelope(BaseModel):
    envelope_id: str = Field(min_length=1)
    graph: MultiAgentSessionGraph

    @field_validator("envelope_id")
    @classmethod
    def envelope_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("envelope_id must not be blank")
        return v.strip()
