import pytest
from pydantic import ValidationError
from models.unit_of_work import (
    TaskStatus, TaskPriority, TaskKind, TaskFailureMode, ConstraintSeverity,
    TaskInputRef, TaskOutputSpec, TaskConstraint, AcceptanceCriterion,
    TaskSpec, TaskEnvelope,
)


def make_input_ref(**overrides) -> TaskInputRef:
    defaults = dict(input_id="in-repo", input_type="git_repository", source_ref="main")
    defaults.update(overrides)
    return TaskInputRef(**defaults)


def make_output_spec(**overrides) -> TaskOutputSpec:
    defaults = dict(output_id="out-code", output_type="source_code", description="Implementation of feature X")
    defaults.update(overrides)
    return TaskOutputSpec(**defaults)


def make_constraint(**overrides) -> TaskConstraint:
    defaults = dict(constraint_id="c-001", category="time", description="30 min limit", severity=ConstraintSeverity.HARD)
    defaults.update(overrides)
    return TaskConstraint(**defaults)


def make_criterion(**overrides) -> AcceptanceCriterion:
    defaults = dict(criterion_id="ac-001", description="All tests pass")
    defaults.update(overrides)
    return AcceptanceCriterion(**defaults)


def make_spec(**overrides) -> TaskSpec:
    defaults = dict(
        task_id="t-001",
        title="Implement null-safe file iterator",
        task_kind=TaskKind.IMPLEMENTATION,
        objective="Add null-safe recursive file iterator.",
        in_scope=["src/file_utils.py"],
        out_of_scope=["network access"],
        inputs=[make_input_ref()],
        expected_outputs=[make_output_spec()],
        constraints=[make_constraint()],
        acceptance_criteria=[make_criterion()],
        failure_mode=TaskFailureMode.RETRY,
        priority=TaskPriority.HIGH,
    )
    defaults.update(overrides)
    return TaskSpec(**defaults)


def make_envelope(**overrides) -> TaskEnvelope:
    defaults = dict(
        envelope_id="uow-001",
        run_id="run-001",
        task=make_spec(),
        status=TaskStatus.READY,
        assigned_agent_id="agent-01",
        parent_task_id=None,
    )
    defaults.update(overrides)
    return TaskEnvelope(**defaults)


class TestEnums:
    def test_task_status_values(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.READY.value == "ready"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.BLOCKED.value == "blocked"
        assert TaskStatus.NEEDS_INPUT.value == "needs_input"
        assert TaskStatus.NEEDS_APPROVAL.value == "needs_approval"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.CANCELLED.value == "cancelled"
        assert len(TaskStatus) == 9

    def test_task_priority_values(self):
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.NORMAL.value == "normal"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.CRITICAL.value == "critical"
        assert len(TaskPriority) == 4

    def test_task_kind_values(self):
        assert TaskKind.ANALYSIS.value == "analysis"
        assert TaskKind.IMPLEMENTATION.value == "implementation"
        assert TaskKind.REVIEW.value == "review"
        assert TaskKind.RESEARCH.value == "research"
        assert TaskKind.TRANSFORMATION.value == "transformation"
        assert len(TaskKind) == 5

    def test_task_failure_mode_values(self):
        assert TaskFailureMode.STOP.value == "stop"
        assert TaskFailureMode.RETRY.value == "retry"
        assert TaskFailureMode.ESCALATE.value == "escalate"
        assert TaskFailureMode.REQUEST_INPUT.value == "request_input"
        assert len(TaskFailureMode) == 4

    def test_constraint_severity_values(self):
        assert ConstraintSeverity.SOFT.value == "soft"
        assert ConstraintSeverity.HARD.value == "hard"
        assert len(ConstraintSeverity) == 2


class TestTaskInputRef:
    def test_valid_input_ref(self):
        ref = make_input_ref()
        assert ref.input_id == "in-repo"
        assert ref.required is True

    def test_non_required(self):
        ref = make_input_ref(required=False)
        assert ref.required is False

    def test_blank_input_id_raises(self):
        with pytest.raises(ValidationError):
            make_input_ref(input_id="")

    def test_blank_input_type_raises(self):
        with pytest.raises(ValidationError):
            make_input_ref(input_type="   ")

    def test_blank_source_ref_raises(self):
        with pytest.raises(ValidationError):
            make_input_ref(source_ref="")


class TestTaskOutputSpec:
    def test_valid_output_spec(self):
        spec = make_output_spec()
        assert spec.output_id == "out-code"
        assert spec.required is True

    def test_non_required(self):
        spec = make_output_spec(required=False)
        assert spec.required is False

    def test_blank_output_id_raises(self):
        with pytest.raises(ValidationError):
            make_output_spec(output_id="")

    def test_blank_output_type_raises(self):
        with pytest.raises(ValidationError):
            make_output_spec(output_type="")

    def test_blank_description_raises(self):
        with pytest.raises(ValidationError):
            make_output_spec(description="")


class TestTaskConstraint:
    def test_valid_constraint(self):
        c = make_constraint()
        assert c.constraint_id == "c-001"
        assert c.severity == ConstraintSeverity.HARD

    def test_soft_constraint(self):
        c = make_constraint(severity=ConstraintSeverity.SOFT)
        assert c.severity == ConstraintSeverity.SOFT

    def test_blank_id_raises(self):
        with pytest.raises(ValidationError):
            make_constraint(constraint_id="")

    def test_blank_category_raises(self):
        with pytest.raises(ValidationError):
            make_constraint(category="")

    def test_blank_description_raises(self):
        with pytest.raises(ValidationError):
            make_constraint(description="")


class TestAcceptanceCriterion:
    def test_valid_criterion(self):
        ac = make_criterion()
        assert ac.criterion_id == "ac-001"
        assert ac.required is True

    def test_non_required(self):
        ac = make_criterion(required=False)
        assert ac.required is False

    def test_blank_id_raises(self):
        with pytest.raises(ValidationError):
            make_criterion(criterion_id="")

    def test_blank_description_raises(self):
        with pytest.raises(ValidationError):
            make_criterion(description="")


class TestTaskSpec:
    def test_valid_spec(self):
        spec = make_spec()
        assert spec.task_id == "t-001"
        assert spec.task_kind == TaskKind.IMPLEMENTATION
        assert spec.failure_mode == TaskFailureMode.RETRY
        assert spec.priority == TaskPriority.HIGH
        assert len(spec.inputs) == 1
        assert len(spec.expected_outputs) == 1
        assert len(spec.constraints) == 1
        assert len(spec.acceptance_criteria) == 1

    def test_default_values(self):
        spec = TaskSpec(
            task_id="t-002",
            title="Do the thing",
            task_kind=TaskKind.ANALYSIS,
            objective="Analyze the system.",
        )
        assert spec.failure_mode == TaskFailureMode.STOP
        assert spec.priority == TaskPriority.NORMAL
        assert spec.in_scope == []
        assert spec.out_of_scope == []
        assert spec.inputs == []
        assert spec.expected_outputs == []
        assert spec.constraints == []
        assert spec.acceptance_criteria == []

    def test_blank_task_id_raises(self):
        with pytest.raises(ValidationError):
            make_spec(task_id="")

    def test_blank_title_raises(self):
        with pytest.raises(ValidationError):
            make_spec(title="   ")

    def test_blank_objective_raises(self):
        with pytest.raises(ValidationError):
            make_spec(objective="")

    def test_placeholder_title_raises(self):
        for val in ["untitled", "TBD", "TODO", "Task", "new task"]:
            with pytest.raises(ValidationError, match="placeholder"):
                make_spec(title=val)

    def test_placeholder_objective_raises(self):
        for val in ["TBD", "TODO", "Objective", "goal"]:
            with pytest.raises(ValidationError, match="placeholder"):
                make_spec(objective=val)

    def test_valid_short_title(self):
        spec = make_spec(title="Fix bug")
        assert spec.title == "Fix bug"

    def test_blank_in_scope_item_raises(self):
        with pytest.raises(ValidationError, match="blank"):
            make_spec(in_scope=["src/", ""])

    def test_blank_out_of_scope_item_raises(self):
        with pytest.raises(ValidationError, match="blank"):
            make_spec(out_of_scope=["network", "   "])

    def test_scope_contradiction_raises(self):
        with pytest.raises(ValidationError, match="overlap"):
            make_spec(in_scope=["src/", "db/"], out_of_scope=["db/"])

    def test_no_scope_contradiction_is_valid(self):
        spec = make_spec(in_scope=["src/"], out_of_scope=["network"])
        assert "src/" in spec.in_scope

    def test_output_with_blank_description_raises(self):
        with pytest.raises(ValidationError, match="must not be blank"):
            make_output_spec(description="")

    def test_all_task_kinds_accepted(self):
        for kind in TaskKind:
            spec = make_spec(task_kind=kind)
            assert spec.task_kind == kind

    def test_all_failure_modes_accepted(self):
        for mode in TaskFailureMode:
            spec = make_spec(failure_mode=mode)
            assert spec.failure_mode == mode

    def test_all_priorities_accepted(self):
        for priority in TaskPriority:
            spec = make_spec(priority=priority)
            assert spec.priority == priority


class TestTaskEnvelope:
    def test_valid_envelope(self):
        env = make_envelope()
        assert env.envelope_id == "uow-001"
        assert env.status == TaskStatus.READY
        assert env.assigned_agent_id == "agent-01"
        assert env.parent_task_id is None

    def test_with_parent_task(self):
        env = make_envelope(parent_task_id="t-000")
        assert env.parent_task_id == "t-000"

    def test_no_agent_assigned(self):
        env = make_envelope(assigned_agent_id=None)
        assert env.assigned_agent_id is None

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="")

    def test_blank_run_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(run_id="")

    def test_all_status_values_accepted(self):
        for status in TaskStatus:
            if status in (TaskStatus.READY, TaskStatus.RUNNING, TaskStatus.COMPLETED):
                env = make_envelope(status=status, task=make_spec(acceptance_criteria=[make_criterion()]))
            else:
                env = make_envelope(status=status, task=make_spec(acceptance_criteria=[make_criterion()]))
            assert env.status == status


class TestEnvelopeExecutableValidation:
    def test_ready_needs_acceptance_criteria(self):
        spec = make_spec(acceptance_criteria=[])
        with pytest.raises(ValidationError, match="acceptance criterion"):
            make_envelope(status=TaskStatus.READY, task=spec)

    def test_running_needs_acceptance_criteria(self):
        spec = make_spec(acceptance_criteria=[])
        with pytest.raises(ValidationError, match="acceptance criterion"):
            make_envelope(status=TaskStatus.RUNNING, task=spec)

    def test_completed_needs_acceptance_criteria(self):
        spec = make_spec(acceptance_criteria=[])
        with pytest.raises(ValidationError, match="acceptance criterion"):
            make_envelope(status=TaskStatus.COMPLETED, task=spec)

    def test_pending_does_not_need_acceptance_criteria(self):
        spec = make_spec(acceptance_criteria=[])
        env = make_envelope(status=TaskStatus.PENDING, task=spec)
        assert env.status == TaskStatus.PENDING

    def test_blocked_does_not_need_acceptance_criteria(self):
        spec = make_spec(acceptance_criteria=[])
        env = make_envelope(status=TaskStatus.BLOCKED, task=spec)
        assert env.status == TaskStatus.BLOCKED

    def test_needs_input_does_not_need_acceptance_criteria(self):
        spec = make_spec(acceptance_criteria=[])
        env = make_envelope(status=TaskStatus.NEEDS_INPUT, task=spec)
        assert env.status == TaskStatus.NEEDS_INPUT

    def test_needs_approval_does_not_need_acceptance_criteria(self):
        spec = make_spec(acceptance_criteria=[])
        env = make_envelope(status=TaskStatus.NEEDS_APPROVAL, task=spec)
        assert env.status == TaskStatus.NEEDS_APPROVAL

    def test_failed_does_not_need_acceptance_criteria(self):
        spec = make_spec(acceptance_criteria=[])
        env = make_envelope(status=TaskStatus.FAILED, task=spec)
        assert env.status == TaskStatus.FAILED

    def test_cancelled_does_not_need_acceptance_criteria(self):
        spec = make_spec(acceptance_criteria=[])
        env = make_envelope(status=TaskStatus.CANCELLED, task=spec)
        assert env.status == TaskStatus.CANCELLED


class TestEnvelopeCompletedValidity:
    def test_completed_with_outputs_and_criteria_valid(self):
        env = make_envelope(status=TaskStatus.COMPLETED)
        assert env.status == TaskStatus.COMPLETED

    def test_completed_without_acceptance_criteria_raises(self):
        spec = make_spec(acceptance_criteria=[])
        with pytest.raises(ValidationError, match="acceptance criterion"):
            make_envelope(status=TaskStatus.COMPLETED, task=spec)


class TestSerialization:
    def test_spec_to_dict_and_back(self):
        spec = make_spec()
        data = spec.model_dump()
        assert data["task_id"] == "t-001"
        assert data["task_kind"] == "implementation"
        restored = TaskSpec(**data)
        assert restored.task_id == spec.task_id

    def test_envelope_to_dict_and_back(self):
        env = make_envelope()
        data = env.model_dump()
        assert data["envelope_id"] == "uow-001"
        assert data["status"] == "ready"
        restored = TaskEnvelope(**data)
        assert restored.envelope_id == env.envelope_id


class TestIntegration:
    def test_full_research_workflow(self):
        spec = TaskSpec(
            task_id="t-res-01",
            title="Evaluate Python async frameworks",
            task_kind=TaskKind.RESEARCH,
            objective="Compare FastAPI, Sanic, and Quart for a high-throughput API service.",
            in_scope=["latency benchmarks", "ecosystem maturity"],
            out_of_scope=["deployment strategies", "database integration"],
            inputs=[TaskInputRef(input_id="in-reqs", input_type="document", source_ref="docs/requirements.md")],
            expected_outputs=[TaskOutputSpec(output_id="out-report", output_type="doc", description="Comparison report with recommendation")],
            acceptance_criteria=[AcceptanceCriterion(criterion_id="ac-001", description="Scorecard with 5 metrics per framework")],
            failure_mode=TaskFailureMode.ESCALATE,
            priority=TaskPriority.NORMAL,
        )
        env = TaskEnvelope(
            envelope_id="uow-res-01",
            run_id="run-res-001",
            task=spec,
            status=TaskStatus.READY,
            assigned_agent_id="agent-research",
        )
        assert env.task.task_kind == TaskKind.RESEARCH
        assert env.status == TaskStatus.READY

    def test_completed_implementation_workflow(self):
        spec = TaskSpec(
            task_id="t-impl-01",
            title="Add input validation to user registration endpoint",
            task_kind=TaskKind.IMPLEMENTATION,
            objective="Add Pydantic-based input validation to POST /api/v2/users.",
            in_scope=["src/api/v2/users.py", "tests/api/v2/"],
            out_of_scope=["email verification flow"],
            expected_outputs=[TaskOutputSpec(output_id="out-code", output_type="source", description="Validated registration handler")],
            acceptance_criteria=[AcceptanceCriterion(criterion_id="ac-001", description="All user API tests pass")],
            failure_mode=TaskFailureMode.STOP,
        )
        env = TaskEnvelope(
            envelope_id="uow-impl-01",
            run_id="run-impl-001",
            task=spec,
            status=TaskStatus.COMPLETED,
            assigned_agent_id="agent-impl",
        )
        assert env.status == TaskStatus.COMPLETED
        assert env.task.failure_mode == TaskFailureMode.STOP
        assert len(env.task.acceptance_criteria) == 1

    def test_missing_required_input_source_ref(self):
        with pytest.raises(ValidationError):
            TaskInputRef(input_id="in-data", input_type="csv", source_ref="")

    def test_task_with_all_defaults_valid(self):
        spec = TaskSpec(
            task_id="t-simple",
            title="Simple task",
            task_kind=TaskKind.ANALYSIS,
            objective="Analyze something quickly.",
        )
        env = TaskEnvelope(
            envelope_id="uow-simple",
            run_id="run-simple",
            task=spec,
            status=TaskStatus.PENDING,
        )
        assert env.status == TaskStatus.PENDING
        assert env.assigned_agent_id is None
        assert env.parent_task_id is None

    def test_scope_list_with_whitespace_values_stripped(self):
        spec = make_spec(in_scope=["  src/  ", "  tests/  "])
        assert spec.in_scope == ["src/", "tests/"]
