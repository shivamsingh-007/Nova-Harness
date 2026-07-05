import pytest
from pydantic import ValidationError
from datetime import datetime, timezone

from models.parallel_work_join_contract import (
    ParallelizationMode,
    BranchStatus,
    JoinPolicy,
    JoinStatus,
    MergeOutcome,
    ParallelWorkRequest,
    BranchAssignmentRecord,
    BranchOutputRecord,
    BranchConflictRecord,
    JoinRequirementRecord,
    JoinExecutionRecord,
    MergeResultRecord,
    ParallelJoinEnvelope,
)


def make_request(overrides: dict = None) -> ParallelWorkRequest:
    base = {
        "parallel_request_id": "pr-001",
        "parallelization_mode": ParallelizationMode.fan_out_all,
        "objective": "Implement login and registration endpoints in parallel",
        "join_policy": JoinPolicy.wait_for_all,
    }
    if overrides:
        base.update(overrides)
    return ParallelWorkRequest(**base)


def make_branch(branch_id: str = "branch-001", overrides: dict = None) -> BranchAssignmentRecord:
    base = {
        "branch_id": branch_id,
        "parallel_request_id": "pr-001",
        "scope_summary": "Implement login endpoint",
        "input_refs": ["specs/login.md"],
        "expected_output_types": ["implementation", "tests"],
    }
    if overrides:
        base.update(overrides)
    return BranchAssignmentRecord(**base)


def make_output(branch_id: str = "branch-001", overrides: dict = None) -> BranchOutputRecord:
    base = {
        "branch_output_id": "bo-001",
        "branch_id": branch_id,
        "status": BranchStatus.completed,
        "result_summary": "Login endpoint implemented",
        "output_refs": ["src/auth/login.py"],
        "confidence": 0.9,
    }
    if overrides:
        base.update(overrides)
    return BranchOutputRecord(**base)


def make_conflict(branch_ids: list = None, overrides: dict = None) -> BranchConflictRecord:
    base = {
        "conflict_id": "conf-001",
        "branch_ids": branch_ids or ["branch-001", "branch-002"],
        "conflict_summary": "Both branches modified auth middleware",
    }
    if overrides:
        base.update(overrides)
    return BranchConflictRecord(**base)


def make_join_requirement(overrides: dict = None) -> JoinRequirementRecord:
    base = {
        "join_requirement_id": "jr-001",
        "parallel_request_id": "pr-001",
        "required_branch_ids": ["branch-001", "branch-002"],
        "required_completion_count": 2,
        "accept_partial_failures": False,
    }
    if overrides:
        base.update(overrides)
    return JoinRequirementRecord(**base)


def make_join_exec(overrides: dict = None) -> JoinExecutionRecord:
    base = {
        "join_id": "join-001",
        "parallel_request_id": "pr-001",
        "join_policy": JoinPolicy.wait_for_all,
        "join_status": JoinStatus.merged,
        "completed_branch_ids": ["branch-001", "branch-002"],
        "selected_output_refs": ["bo-001", "bo-002"],
        "executed_at": datetime.now(timezone.utc),
    }
    if overrides:
        base.update(overrides)
    return JoinExecutionRecord(**base)


def make_merge_result(overrides: dict = None) -> MergeResultRecord:
    base = {
        "merge_id": "merge-001",
        "join_id": "join-001",
        "merge_outcome": MergeOutcome.success,
        "merged_output_refs": ["bo-001", "bo-002"],
        "final_summary": "Both endpoints implemented successfully",
        "next_action": "proceed_to_integration_test",
        "merged_at": datetime.now(timezone.utc),
    }
    if overrides:
        base.update(overrides)
    return MergeResultRecord(**base)


def make_envelope(overrides: dict = None) -> ParallelJoinEnvelope:
    base = {
        "envelope_id": "env-par-001",
        "parallel_request": make_request(),
        "branch_assignments": [make_branch("branch-001"), make_branch("branch-002")],
        "join_requirements": make_join_requirement(),
    }
    if overrides:
        base.update(overrides)
    return ParallelJoinEnvelope(**base)


class TestParallelizationMode:
    def test_values(self):
        assert len(ParallelizationMode) == 5
        assert ParallelizationMode.fan_out_all.value == "fan_out_all"
        assert ParallelizationMode.fan_out_selected.value == "fan_out_selected"
        assert ParallelizationMode.conditional_parallel.value == "conditional_parallel"
        assert ParallelizationMode.verification_parallel.value == "verification_parallel"
        assert ParallelizationMode.speculative_parallel.value == "speculative_parallel"


class TestBranchStatus:
    def test_values(self):
        assert len(BranchStatus) == 8
        assert BranchStatus.planned.value == "planned"
        assert BranchStatus.completed.value == "completed"
        assert BranchStatus.blocked.value == "blocked"


class TestJoinPolicy:
    def test_values(self):
        assert len(JoinPolicy) == 5
        assert JoinPolicy.wait_for_all.value == "wait_for_all"
        assert JoinPolicy.wait_for_quorum.value == "wait_for_quorum"
        assert JoinPolicy.manual_join.value == "manual_join"


class TestJoinStatus:
    def test_values(self):
        assert len(JoinStatus) == 7
        assert JoinStatus.ready_to_merge.value == "ready_to_merge"
        assert JoinStatus.partial_merge.value == "partial_merge"


class TestMergeOutcome:
    def test_values(self):
        assert len(MergeOutcome) == 5
        assert MergeOutcome.needs_review.value == "needs_review"


class TestParallelWorkRequest:
    def test_valid_request(self):
        req = make_request()
        assert req.parallel_request_id == "pr-001"
        assert req.parallelization_mode == ParallelizationMode.fan_out_all
        assert req.join_policy == JoinPolicy.wait_for_all

    def test_blank_request_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_request({"parallel_request_id": "   "})

    def test_blank_objective_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_request({"objective": "   "})

    def test_empty_request_id_raises(self):
        with pytest.raises(ValidationError):
            make_request({"parallel_request_id": ""})

    def test_empty_objective_raises(self):
        with pytest.raises(ValidationError):
            make_request({"objective": ""})

    def test_default_created_at(self):
        req = make_request()
        assert req.created_at is not None

    def test_with_all_optionals(self):
        req = make_request({
            "parent_run_id": "run-042",
            "parent_step_id": "step-03",
            "parent_graph_node_id": "node-par-001",
            "branching_reason": "Independent scopes, no shared state",
            "requested_branch_count": 2,
        })
        assert req.parent_run_id == "run-042"


class TestBranchAssignmentRecord:
    def test_valid_branch(self):
        b = make_branch()
        assert b.branch_id == "branch-001"
        assert b.status == BranchStatus.planned

    def test_blank_branch_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_branch(branch_id="   ")

    def test_blank_scope_summary_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_branch(overrides={"scope_summary": "   "})

    def test_deadline_can_be_set(self):
        dt = datetime.now(timezone.utc)
        b = make_branch(overrides={"deadline_at": dt})
        assert b.deadline_at == dt

    def test_status_defaults_to_planned(self):
        b = make_branch()
        assert b.status == BranchStatus.planned

    def test_with_agent_and_role(self):
        b = make_branch(overrides={"assigned_agent_id": "agent-01", "assigned_role_id": "coder"})
        assert b.assigned_agent_id == "agent-01"
        assert b.assigned_role_id == "coder"


class TestBranchOutputRecord:
    def test_valid_output(self):
        o = make_output()
        assert o.branch_output_id == "bo-001"
        assert o.confidence == 0.9

    def test_confidence_above_one_raises(self):
        with pytest.raises(ValidationError):
            make_output(overrides={"confidence": 1.5})

    def test_confidence_below_zero_raises(self):
        with pytest.raises(ValidationError):
            make_output(overrides={"confidence": -0.1})

    def test_confidence_at_boundaries(self):
        o1 = make_output(overrides={"confidence": 0.0})
        assert o1.confidence == 0.0
        o2 = make_output(overrides={"confidence": 1.0})
        assert o2.confidence == 1.0

    def test_blank_output_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_output(overrides={"branch_output_id": "   "})

    def test_blank_branch_id_in_output_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_output(branch_id="   ")

    def test_with_evidence_and_changed_artifacts(self):
        o = make_output(overrides={
            "evidence_refs": ["test_output/login_test.py"],
            "changed_artifact_refs": ["src/auth/login.py", "tests/test_login.py"],
        })
        assert len(o.evidence_refs) == 1
        assert len(o.changed_artifact_refs) == 2


class TestBranchConflictRecord:
    def test_valid_conflict(self):
        c = make_conflict()
        assert c.conflict_id == "conf-001"

    def test_blank_conflict_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_conflict(overrides={"conflict_id": "   "})

    def test_blank_conflict_summary_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_conflict(overrides={"conflict_summary": "   "})

    def test_duplicate_branch_ids_raises(self):
        with pytest.raises(ValidationError, match="must be unique"):
            make_conflict(branch_ids=["branch-001", "branch-001"])

    def test_less_than_two_branch_ids_raises(self):
        with pytest.raises(ValidationError):
            make_conflict(branch_ids=["branch-001"])

    def test_requires_review_default_false(self):
        c = make_conflict()
        assert c.requires_review is False

    def test_with_resolution_and_review(self):
        c = make_conflict(overrides={
            "conflict_type": "merge",
            "proposed_resolution": "Keep login.py from branch-001, override middleware from branch-002",
            "requires_review": True,
        })
        assert c.requires_review is True


class TestJoinRequirementRecord:
    def test_valid_requirement(self):
        jr = make_join_requirement()
        assert jr.join_requirement_id == "jr-001"

    def test_blank_join_requirement_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_join_requirement({"join_requirement_id": "   "})

    def test_blank_parallel_request_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_join_requirement({"parallel_request_id": "   "})

    def test_required_completion_count_cannot_be_zero(self):
        with pytest.raises(ValidationError, match="must be at least 1"):
            make_envelope({
                "join_requirements": make_join_requirement({"required_completion_count": 0})
            })

    def test_required_completion_count_exceeds_required_branches(self):
        with pytest.raises(ValidationError, match="cannot exceed total required branch count"):
            make_envelope({
                "join_requirements": make_join_requirement({
                    "required_branch_ids": ["branch-001", "branch-002"],
                    "required_completion_count": 3,
                })
            })

    def test_wait_for_first_success_with_missing_completion_count_raises(self):
        with pytest.raises(ValidationError, match="must not require all branches"):
            make_envelope({
                "parallel_request": make_request({"join_policy": JoinPolicy.wait_for_first_success}),
                "join_requirements": make_join_requirement({
                    "required_branch_ids": ["branch-001", "branch-002"],
                    "required_completion_count": None,
                }),
            })

    def test_wait_for_first_success_with_completion_count_1_ok(self):
        env = make_envelope({
            "parallel_request": make_request({"join_policy": JoinPolicy.wait_for_first_success}),
            "join_requirements": make_join_requirement({
                "required_branch_ids": ["branch-001", "branch-002"],
                "required_completion_count": 1,
            }),
        })
        assert env.parallel_request.join_policy == JoinPolicy.wait_for_first_success

    def test_accept_partial_failures_default_false(self):
        jr = make_join_requirement()
        assert jr.accept_partial_failures is False


class TestJoinExecutionRecord:
    def test_valid_join_exec(self):
        je = make_join_exec()
        assert je.join_id == "join-001"
        assert je.join_status == JoinStatus.merged

    def test_blank_join_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_join_exec({"join_id": "   "})

    def test_blank_parallel_request_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_join_exec({"parallel_request_id": "   "})

    def test_with_failed_and_late_branches(self):
        je = make_join_exec({
            "join_status": JoinStatus.partial_merge,
            "failed_branch_ids": ["branch-003"],
            "late_branch_ids": ["branch-004"],
            "join_notes": "Branch-003 failed, branch-004 still running",
        })
        assert len(je.failed_branch_ids) == 1
        assert je.join_status == JoinStatus.partial_merge


class TestMergeResultRecord:
    def test_valid_merge(self):
        mr = make_merge_result()
        assert mr.merge_outcome == MergeOutcome.success

    def test_blank_merge_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_merge_result({"merge_id": "   "})

    def test_blank_join_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_merge_result({"join_id": "   "})

    def test_with_conflicts_and_review(self):
        mr = make_merge_result({
            "merge_outcome": MergeOutcome.conflict,
            "conflict_refs": ["conf-001"],
            "rejected_output_refs": ["bo-002"],
            "review_required": True,
        })
        assert mr.review_required is True
        assert mr.merge_outcome == MergeOutcome.conflict


class TestParallelJoinEnvelope:
    def test_valid_envelope(self):
        env = make_envelope()
        assert env.envelope_id == "env-par-001"
        assert len(env.branch_assignments) == 2

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_envelope({"envelope_id": "   "})

    def test_zero_branches_raises(self):
        with pytest.raises(ValidationError, match="at least 1 item"):
            make_envelope({"branch_assignments": []})

    def test_duplicate_branch_ids_raises(self):
        with pytest.raises(ValidationError, match="branch IDs must be unique"):
            make_envelope({
                "branch_assignments": [
                    make_branch("branch-001"),
                    make_branch("branch-001"),
                ]
            })

    def test_conflict_with_unknown_branch_id_raises(self):
        with pytest.raises(ValidationError, match="unknown branch_id"):
            make_envelope({
                "conflicts": [make_conflict(branch_ids=["branch-001", "branch-999"])],
            })

    def test_output_with_unknown_branch_id_raises(self):
        with pytest.raises(ValidationError, match="unknown branch_id"):
            make_envelope({
                "branch_outputs": [make_output(branch_id="branch-999")],
            })

    def test_merge_result_without_join_execution_ok(self):
        env = make_envelope({
            "merge_result": make_merge_result(),
        })
        assert env.merge_result is not None

    def test_merge_result_with_pending_join_raises(self):
        with pytest.raises(ValidationError, match="require completed or partial join"):
            make_envelope({
                "join_execution": make_join_exec({"join_status": JoinStatus.pending}),
                "merge_result": make_merge_result(),
            })

    def test_merge_result_with_merged_join_ok(self):
        env = make_envelope({
            "join_execution": make_join_exec({"join_status": JoinStatus.merged}),
            "merge_result": make_merge_result(),
        })
        assert env.merge_result is not None

    def test_merge_result_with_partial_merge_join_ok(self):
        env = make_envelope({
            "join_execution": make_join_exec({"join_status": JoinStatus.partial_merge}),
            "merge_result": make_merge_result(),
        })
        assert env.merge_result is not None

    def test_fan_out_all_with_outputs_and_conflicts(self):
        env = make_envelope({
            "branch_outputs": [
                make_output("branch-001"),
                make_output("branch-002", {"branch_output_id": "bo-002", "result_summary": "Registration endpoint implemented"}),
            ],
            "conflicts": [make_conflict()],
            "join_execution": make_join_exec(),
            "merge_result": make_merge_result(),
        })
        assert len(env.branch_outputs) == 2
        assert len(env.conflicts) == 1

    def test_wait_for_first_success_single_branch_ok(self):
        env = make_envelope({
            "parallel_request": make_request({"join_policy": JoinPolicy.wait_for_first_success, "parallelization_mode": ParallelizationMode.speculative_parallel}),
            "branch_assignments": [make_branch("branch-001")],
            "join_requirements": make_join_requirement({
                "required_branch_ids": ["branch-001"],
                "required_completion_count": 1,
            }),
        })
        assert env.parallel_request.parallelization_mode == ParallelizationMode.speculative_parallel


class TestIntegrationExamples:
    def test_fan_out_two_specialists_wait_for_all(self):
        env = make_envelope()
        assert env.parallel_request.join_policy == JoinPolicy.wait_for_all
        assert len(env.branch_assignments) == 2

    def test_verification_parallel_quorum_join(self):
        env = make_envelope({
            "envelope_id": "env-par-002",
            "parallel_request": make_request({
                "parallel_request_id": "pr-002",
                "parallelization_mode": ParallelizationMode.verification_parallel,
                "objective": "Verify login module implementation",
                "join_policy": JoinPolicy.wait_for_quorum,
            }),
            "branch_assignments": [
                make_branch("branch-001", {"scope_summary": "Security review of login"}),
                make_branch("branch-002", {"scope_summary": "Performance review of login"}),
            ],
            "join_requirements": make_join_requirement({
                "join_requirement_id": "jr-002",
                "required_branch_ids": ["branch-001", "branch-002"],
                "required_completion_count": 2,
            }),
        })
        assert env.parallel_request.parallelization_mode == ParallelizationMode.verification_parallel
        assert env.parallel_request.join_policy == JoinPolicy.wait_for_quorum

    def test_merge_conflict_between_two_branches(self):
        env = make_envelope({
            "envelope_id": "env-par-003",
            "parallel_request": make_request({
                "parallel_request_id": "pr-003",
                "parallelization_mode": ParallelizationMode.fan_out_selected,
                "objective": "Refactor auth module",
            }),
            "branch_assignments": [
                make_branch("branch-001", {"scope_summary": "Refactor login handler"}),
                make_branch("branch-002", {"scope_summary": "Refactor registration handler"}),
            ],
            "branch_outputs": [
                make_output("branch-001", {"branch_output_id": "bo-003"}),
                make_output("branch-002", {"branch_output_id": "bo-004"}),
            ],
            "conflicts": [make_conflict()],
            "join_execution": make_join_exec({"join_id": "join-003", "join_status": JoinStatus.merged}),
            "merge_result": make_merge_result({
                "merge_id": "merge-003",
                "merge_outcome": MergeOutcome.conflict,
                "conflict_refs": ["conf-001"],
                "rejected_output_refs": ["bo-004"],
                "review_required": True,
            }),
        })
        assert env.merge_result.merge_outcome == MergeOutcome.conflict
        assert env.merge_result.review_required is True

    def test_blocked_branch_partial_join_needs_review(self):
        env = make_envelope({
            "envelope_id": "env-par-004",
            "parallel_request": make_request({
                "parallel_request_id": "pr-004",
                "objective": "Implement payment integration",
            }),
            "branch_assignments": [
                make_branch("branch-001", {"scope_summary": "Stripe integration"}),
                make_branch("branch-002", {"scope_summary": "PayPal integration"}),
                make_branch("branch-003", {"scope_summary": "Receipt generation"}),
            ],
            "branch_outputs": [
                make_output("branch-001", {"branch_output_id": "bo-005"}),
                make_output("branch-002", {"branch_output_id": "bo-006"}),
            ],
            "join_execution": make_join_exec({
                "join_id": "join-004",
                "join_status": JoinStatus.partial_merge,
                "completed_branch_ids": ["branch-001", "branch-002"],
                "failed_branch_ids": ["branch-003"],
                "join_notes": "Branch-003 blocked on Stripe sandbox key provisioning",
            }),
            "merge_result": make_merge_result({
                "merge_id": "merge-004",
                "merge_outcome": MergeOutcome.needs_review,
                "rejected_output_refs": ["bo-006"],
                "review_required": True,
                "final_summary": "Stripe done, PayPal rejected, receipt blocked",
                "next_action": "review_paypal_output_and_unblock_receipt",
            }),
        })
        assert env.merge_result.merge_outcome == MergeOutcome.needs_review
        assert env.merge_result.review_required is True
        assert "review_paypal_output" in env.merge_result.next_action


class TestEdgeCases:
    def test_confidence_none_allowed(self):
        o = make_output(overrides={"confidence": None})
        assert o.confidence is None

    def test_empty_output_refs_allowed(self):
        o = make_output(overrides={"output_refs": []})
        assert o.output_refs == []

    def test_required_completion_count_equals_total_ok(self):
        env = make_envelope()
        assert env.join_requirements.required_completion_count == 2

    def test_no_optional_branches(self):
        jr = make_join_requirement()
        assert jr.optional_branch_ids == []

    def test_late_branches_recorded(self):
        je = make_join_exec({
            "late_branch_ids": ["branch-003"],
        })
        assert "branch-003" in je.late_branch_ids
