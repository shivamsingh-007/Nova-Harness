from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum


class ParallelizationMode(str, Enum):
    fan_out_all = "fan_out_all"
    fan_out_selected = "fan_out_selected"
    conditional_parallel = "conditional_parallel"
    verification_parallel = "verification_parallel"
    speculative_parallel = "speculative_parallel"


class BranchStatus(str, Enum):
    planned = "planned"
    ready = "ready"
    running = "running"
    waiting = "waiting"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
    blocked = "blocked"


class JoinPolicy(str, Enum):
    wait_for_all = "wait_for_all"
    wait_for_quorum = "wait_for_quorum"
    wait_for_first_success = "wait_for_first_success"
    wait_for_required_set = "wait_for_required_set"
    manual_join = "manual_join"


class JoinStatus(str, Enum):
    pending = "pending"
    waiting = "waiting"
    ready_to_merge = "ready_to_merge"
    merged = "merged"
    partial_merge = "partial_merge"
    failed = "failed"
    cancelled = "cancelled"


class MergeOutcome(str, Enum):
    success = "success"
    partial = "partial"
    conflict = "conflict"
    rejected = "rejected"
    needs_review = "needs_review"


class ParallelWorkRequest(BaseModel):
    parallel_request_id: str = Field(min_length=1)
    parent_run_id: Optional[str] = None
    parent_step_id: Optional[str] = None
    parent_graph_node_id: Optional[str] = None
    parallelization_mode: ParallelizationMode
    objective: str = Field(min_length=1)
    branching_reason: Optional[str] = None
    requested_branch_count: Optional[int] = None
    join_policy: JoinPolicy
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator("parallel_request_id")
    @classmethod
    def parallel_request_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("parallel_request_id must not be blank")
        return v.strip()

    @field_validator("objective")
    @classmethod
    def objective_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("objective must not be blank")
        return v.strip()


class BranchAssignmentRecord(BaseModel):
    branch_id: str = Field(min_length=1)
    parallel_request_id: str = Field(min_length=1)
    assigned_agent_id: Optional[str] = None
    assigned_role_id: Optional[str] = None
    scope_summary: str = Field(min_length=1)
    input_refs: List[str] = Field(default_factory=list)
    expected_output_types: List[str] = Field(default_factory=list)
    dependency_refs: List[str] = Field(default_factory=list)
    conflict_risk: Optional[str] = None
    status: BranchStatus = BranchStatus.planned
    started_at: Optional[datetime] = None
    deadline_at: Optional[datetime] = None

    @field_validator("branch_id")
    @classmethod
    def branch_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("branch_id must not be blank")
        return v.strip()

    @field_validator("parallel_request_id")
    @classmethod
    def branch_parallel_request_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("parallel_request_id must not be blank")
        return v.strip()

    @field_validator("scope_summary")
    @classmethod
    def scope_summary_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("scope_summary must not be blank")
        return v.strip()


class BranchOutputRecord(BaseModel):
    branch_output_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    status: BranchStatus
    result_summary: Optional[str] = None
    output_refs: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    changed_artifact_refs: List[str] = Field(default_factory=list)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    submitted_at: Optional[datetime] = None

    @field_validator("branch_output_id")
    @classmethod
    def branch_output_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("branch_output_id must not be blank")
        return v.strip()

    @field_validator("branch_id")
    @classmethod
    def output_branch_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("branch_id must not be blank")
        return v.strip()


class BranchConflictRecord(BaseModel):
    conflict_id: str = Field(min_length=1)
    branch_ids: List[str] = Field(min_length=2)
    conflict_type: Optional[str] = None
    conflict_summary: str = Field(min_length=1)
    artifact_refs: List[str] = Field(default_factory=list)
    proposed_resolution: Optional[str] = None
    requires_review: bool = False

    @field_validator("conflict_id")
    @classmethod
    def conflict_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("conflict_id must not be blank")
        return v.strip()

    @field_validator("branch_ids")
    @classmethod
    def conflict_branch_ids_must_be_unique(cls, v: List[str]) -> List[str]:
        if len(v) != len(set(v)):
            raise ValueError("branch_ids in conflict must be unique")
        return v

    @field_validator("conflict_summary")
    @classmethod
    def conflict_summary_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("conflict_summary must not be blank")
        return v.strip()


class JoinRequirementRecord(BaseModel):
    join_requirement_id: str = Field(min_length=1)
    parallel_request_id: str = Field(min_length=1)
    required_branch_ids: List[str] = Field(default_factory=list)
    optional_branch_ids: List[str] = Field(default_factory=list)
    required_completion_count: Optional[int] = None
    accept_partial_failures: bool = False
    deadline_policy: Optional[str] = None

    @field_validator("join_requirement_id")
    @classmethod
    def join_requirement_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("join_requirement_id must not be blank")
        return v.strip()

    @field_validator("parallel_request_id")
    @classmethod
    def req_parallel_request_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("parallel_request_id must not be blank")
        return v.strip()


class JoinExecutionRecord(BaseModel):
    join_id: str = Field(min_length=1)
    parallel_request_id: str = Field(min_length=1)
    join_policy: JoinPolicy
    join_status: JoinStatus
    completed_branch_ids: List[str] = Field(default_factory=list)
    failed_branch_ids: List[str] = Field(default_factory=list)
    late_branch_ids: List[str] = Field(default_factory=list)
    selected_output_refs: List[str] = Field(default_factory=list)
    join_notes: Optional[str] = None
    executed_at: Optional[datetime] = None

    @field_validator("join_id")
    @classmethod
    def join_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("join_id must not be blank")
        return v.strip()

    @field_validator("parallel_request_id")
    @classmethod
    def exec_parallel_request_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("parallel_request_id must not be blank")
        return v.strip()


class MergeResultRecord(BaseModel):
    merge_id: str = Field(min_length=1)
    join_id: str = Field(min_length=1)
    merge_outcome: MergeOutcome
    merged_output_refs: List[str] = Field(default_factory=list)
    rejected_output_refs: List[str] = Field(default_factory=list)
    conflict_refs: List[str] = Field(default_factory=list)
    review_required: bool = False
    final_summary: Optional[str] = None
    next_action: Optional[str] = None
    merged_at: Optional[datetime] = None

    @field_validator("merge_id")
    @classmethod
    def merge_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("merge_id must not be blank")
        return v.strip()

    @field_validator("join_id")
    @classmethod
    def merge_join_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("join_id must not be blank")
        return v.strip()


class ParallelJoinEnvelope(BaseModel):
    envelope_id: str = Field(min_length=1)
    parallel_request: ParallelWorkRequest
    branch_assignments: List[BranchAssignmentRecord] = Field(min_length=1)
    branch_outputs: List[BranchOutputRecord] = Field(default_factory=list)
    conflicts: List[BranchConflictRecord] = Field(default_factory=list)
    join_requirements: JoinRequirementRecord
    join_execution: Optional[JoinExecutionRecord] = None
    merge_result: Optional[MergeResultRecord] = None

    @field_validator("envelope_id")
    @classmethod
    def envelope_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("envelope_id must not be blank")
        return v.strip()

    @field_validator("branch_assignments")
    @classmethod
    def branch_ids_must_be_unique(cls, v: List[BranchAssignmentRecord]) -> List[BranchAssignmentRecord]:
        ids = [b.branch_id for b in v]
        if len(ids) != len(set(ids)):
            raise ValueError("branch IDs must be unique within a parallel request")
        return v

    @field_validator("branch_assignments")
    @classmethod
    def at_least_one_branch(cls, v: List[BranchAssignmentRecord]) -> List[BranchAssignmentRecord]:
        if len(v) < 1:
            raise ValueError("at least one branch assignment is required")
        return v

    @field_validator("conflicts")
    @classmethod
    def conflict_branch_ids_must_exist_in_assignments(
        cls, v: List[BranchConflictRecord], info
    ) -> List[BranchConflictRecord]:
        if not info.data.get("branch_assignments"):
            return v
        valid_ids = {b.branch_id for b in info.data["branch_assignments"]}
        for conflict in v:
            for bid in conflict.branch_ids:
                if bid not in valid_ids:
                    raise ValueError(f"conflict references unknown branch_id '{bid}'")
        return v

    @field_validator("branch_outputs")
    @classmethod
    def output_branch_ids_must_exist_in_assignments(
        cls, v: List[BranchOutputRecord], info
    ) -> List[BranchOutputRecord]:
        if not info.data.get("branch_assignments"):
            return v
        valid_ids = {b.branch_id for b in info.data["branch_assignments"]}
        for output in v:
            if output.branch_id not in valid_ids:
                raise ValueError(f"output references unknown branch_id '{output.branch_id}'")
        return v

    def validate_join_requirements(self) -> None:
        req = self.join_requirements
        policy = self.parallel_request.join_policy
        total_required = len(req.required_branch_ids)
        if req.required_completion_count is not None:
            if req.required_completion_count < 1:
                raise ValueError("required_completion_count must be at least 1")
            if total_required > 0 and req.required_completion_count > total_required:
                raise ValueError("required_completion_count cannot exceed total required branch count")
        if policy == JoinPolicy.wait_for_all:
            for bid in req.required_branch_ids:
                matching = [o for o in self.branch_outputs if o.branch_id == bid and o.status == BranchStatus.completed]
                if not matching:
                    pass  # validation is caller's responsibility at runtime
        if policy == JoinPolicy.wait_for_first_success:
            if len(req.required_branch_ids) > 1 and req.required_completion_count is None:
                raise ValueError("wait_for_first_success must not require all branches; set required_completion_count=1 or use wait_for_all")

    @field_validator("join_requirements")
    @classmethod
    def validate_join_requirements_field(cls, v: JoinRequirementRecord, info) -> JoinRequirementRecord:
        if not info.data.get("parallel_request"):
            return v
        policy = info.data["parallel_request"].join_policy
        total_required = len(v.required_branch_ids)
        if v.required_completion_count is not None:
            if v.required_completion_count < 1:
                raise ValueError("required_completion_count must be at least 1")
            if total_required > 0 and v.required_completion_count > total_required:
                raise ValueError("required_completion_count cannot exceed total required branch count")
        if policy == JoinPolicy.wait_for_first_success and total_required > 1 and v.required_completion_count is None:
            raise ValueError("wait_for_first_success must not require all branches; set required_completion_count=1 or use wait_for_all")
        return v

    def check_merge_requires_completed_join(self) -> None:
        if self.merge_result is not None and self.join_execution is not None:
            if self.join_execution.join_status not in (JoinStatus.merged, JoinStatus.partial_merge):
                raise ValueError("merge results require completed or partial join state")

    @field_validator("merge_result")
    @classmethod
    def merge_requires_completed_or_partial_join(cls, v: Optional[MergeResultRecord], info) -> Optional[MergeResultRecord]:
        if v is None:
            return v
        join_execution = info.data.get("join_execution")
        if join_execution is not None and join_execution.join_status not in (JoinStatus.merged, JoinStatus.partial_merge):
            raise ValueError("merge results require completed or partial join state")
        return v

    def check_all_envelope_rules(self) -> None:
        self.validate_join_requirements()
        self.check_merge_requires_completed_join()
