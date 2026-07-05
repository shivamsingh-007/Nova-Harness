import pytest
from pydantic import ValidationError
from models.run_orchestration_contract import (
    RunPhase, RunStatus, ExecutionMode, StepDependencyType,
    RunStepRef, RunBlockerRef, RunProgress,
    ExecutionStateRecord, RunOrchestrationEnvelope,
)


def make_step(**overrides) -> RunStepRef:
    defaults = dict(step_id="step-001", step_type="task_execution",
                    order_index=0, status=RunStatus.RUNNING)
    defaults.update(overrides)
    return RunStepRef(**defaults)


def make_blocker(**overrides) -> RunBlockerRef:
    defaults = dict(blocker_id="blk-001", blocker_type="approval",
                    reason="Waiting for human approval")
    defaults.update(overrides)
    return RunBlockerRef(**defaults)


def make_progress(**overrides) -> RunProgress:
    defaults = dict(total_steps=5)
    defaults.update(overrides)
    return RunProgress(**defaults)


def make_state(**overrides) -> ExecutionStateRecord:
    defaults = dict(run_id="run-001", agent_id="agent-code",
                    phase=RunPhase.EXECUTING, status=RunStatus.RUNNING,
                    mode=ExecutionMode.SEQUENTIAL,
                    progress=make_progress())
    defaults.update(overrides)
    return ExecutionStateRecord(**defaults)


def make_envelope(**overrides) -> RunOrchestrationEnvelope:
    defaults = dict(envelope_id="env-001", run=make_state())
    defaults.update(overrides)
    return RunOrchestrationEnvelope(**defaults)


class TestEnums:
    def test_run_phase_values(self):
        assert RunPhase.INIT.value == "init"
        assert RunPhase.PLANNING.value == "planning"
        assert RunPhase.EXECUTING.value == "executing"
        assert RunPhase.WAITING.value == "waiting"
        assert RunPhase.RECOVERING.value == "recovering"
        assert RunPhase.FINALIZING.value == "finalizing"
        assert RunPhase.TERMINATED.value == "terminated"
        assert len(RunPhase) == 7

    def test_run_status_values(self):
        assert RunStatus.PENDING.value == "pending"
        assert RunStatus.READY.value == "ready"
        assert RunStatus.RUNNING.value == "running"
        assert RunStatus.BLOCKED.value == "blocked"
        assert RunStatus.PAUSED.value == "paused"
        assert RunStatus.FAILED.value == "failed"
        assert RunStatus.COMPLETED.value == "completed"
        assert RunStatus.CANCELLED.value == "cancelled"
        assert len(RunStatus) == 8

    def test_execution_mode_values(self):
        assert ExecutionMode.SEQUENTIAL.value == "sequential"
        assert ExecutionMode.PARALLEL.value == "parallel"
        assert ExecutionMode.HYBRID.value == "hybrid"
        assert len(ExecutionMode) == 3

    def test_step_dependency_type_values(self):
        assert StepDependencyType.STARTS_AFTER.value == "starts_after"
        assert StepDependencyType.WAITS_FOR.value == "waits_for"
        assert StepDependencyType.DEPENDS_ON.value == "depends_on"
        assert StepDependencyType.BLOCKS.value == "blocks"
        assert len(StepDependencyType) == 4


class TestRunStepRef:
    def test_valid(self):
        s = make_step()
        assert s.step_id == "step-001"

    def test_all_statuses(self):
        for st in RunStatus:
            s = make_step(status=st)
            assert s.status == st

    def test_with_task_and_tool_and_model(self):
        s = make_step(task_id="t-001", tool_call_id="tc-001", model_call_id="mc-001")
        assert s.task_id == "t-001"
        assert s.tool_call_id == "tc-001"
        assert s.model_call_id == "mc-001"

    def test_with_description(self):
        s = make_step(description="Execute task t-001")
        assert s.description == "Execute task t-001"

    def test_order_index_zero_valid(self):
        s = make_step(order_index=0)
        assert s.order_index == 0

    def test_order_index_positive_valid(self):
        s = make_step(order_index=5)
        assert s.order_index == 5

    def test_order_index_negative_raises(self):
        with pytest.raises(ValidationError, match="order_index"):
            make_step(order_index=-1)

    def test_blank_step_id_raises(self):
        with pytest.raises(ValidationError):
            make_step(step_id="")

    def test_blank_step_type_raises(self):
        with pytest.raises(ValidationError):
            make_step(step_type="")

    def test_steps_order_preserved(self):
        steps = [make_step(step_id="s-3", order_index=2),
                 make_step(step_id="s-1", order_index=0),
                 make_step(step_id="s-2", order_index=1)]
        assert [s.step_id for s in steps] == ["s-3", "s-1", "s-2"]


class TestRunBlockerRef:
    def test_valid(self):
        b = make_blocker()
        assert b.blocker_id == "blk-001"

    def test_with_related_ref(self):
        b = make_blocker(related_ref="approval://gate-001")
        assert b.related_ref == "approval://gate-001"

    def test_blank_blocker_id_raises(self):
        with pytest.raises(ValidationError):
            make_blocker(blocker_id="")

    def test_blank_blocker_type_raises(self):
        with pytest.raises(ValidationError):
            make_blocker(blocker_type="")

    def test_blank_reason_raises(self):
        with pytest.raises(ValidationError):
            make_blocker(reason="")


class TestRunProgress:
    def test_valid(self):
        p = make_progress()
        assert p.total_steps == 5

    def test_with_active_step(self):
        p = make_progress(active_step_id="step-002")
        assert p.active_step_id == "step-002"

    def test_completed_not_exceed_total(self):
        p = make_progress(total_steps=5, completed_steps=3)
        assert p.completed_steps == 3

    def test_completed_equal_total_valid(self):
        p = make_progress(total_steps=3, completed_steps=3)
        assert p.completed_steps == 3

    def test_completed_exceeds_total_raises(self):
        with pytest.raises(ValidationError, match="completed_steps"):
            make_progress(total_steps=3, completed_steps=4)

    def test_zero_total_valid(self):
        p = make_progress(total_steps=0)
        assert p.total_steps == 0

    def test_negative_total_raises(self):
        with pytest.raises(ValidationError, match="non-negative"):
            make_progress(total_steps=-1)

    def test_negative_completed_raises(self):
        with pytest.raises(ValidationError, match="non-negative"):
            make_progress(completed_steps=-1)

    def test_negative_blocked_raises(self):
        with pytest.raises(ValidationError, match="non-negative"):
            make_progress(blocked_steps=-1)

    def test_negative_failed_raises(self):
        with pytest.raises(ValidationError, match="non-negative"):
            make_progress(failed_steps=-1)

    def test_defaults_zero(self):
        p = make_progress(total_steps=5)
        assert p.completed_steps == 0
        assert p.blocked_steps == 0
        assert p.failed_steps == 0
        assert p.active_step_id is None


class TestExecutionStateRecord:
    def test_valid(self):
        s = make_state()
        assert s.run_id == "run-001"

    def test_all_phases(self):
        for ph in RunPhase:
            s = make_state(phase=ph)
            assert s.phase == ph

    def test_all_statuses(self):
        for st in RunStatus:
            s = make_state(status=st, blockers=[make_blocker()] if st == RunStatus.BLOCKED else [])
            assert s.status == st

    def test_all_modes(self):
        for m in ExecutionMode:
            s = make_state(mode=m)
            assert s.mode == m

    def test_with_session_and_task_and_trace(self):
        s = make_state(session_id="s-001", task_id="t-001", trace_id="trace-001")
        assert s.session_id == "s-001"
        assert s.task_id == "t-001"
        assert s.trace_id == "trace-001"

    def test_with_checkpoint_and_policy(self):
        s = make_state(checkpoint_id="chk-001", policy_decision_id="pd-001")
        assert s.checkpoint_id == "chk-001"
        assert s.policy_decision_id == "pd-001"

    def test_with_steps(self):
        s = make_state(steps=[make_step()])
        assert len(s.steps) == 1

    def test_with_blockers(self):
        s = make_state(steps=[make_step()], blockers=[make_blocker()])
        assert len(s.blockers) == 1

    def test_blank_run_id_raises(self):
        with pytest.raises(ValidationError):
            make_state(run_id="")

    def test_blank_agent_id_raises(self):
        with pytest.raises(ValidationError):
            make_state(agent_id="")

    def test_blocked_without_blockers_raises(self):
        with pytest.raises(ValidationError, match="BLOCKED"):
            make_state(status=RunStatus.BLOCKED, blockers=[])

    def test_blocked_with_blockers_valid(self):
        s = make_state(status=RunStatus.BLOCKED, blockers=[make_blocker()])
        assert s.status == RunStatus.BLOCKED
        assert len(s.blockers) == 1

    def test_not_blocked_no_blockers_valid(self):
        s = make_state(status=RunStatus.RUNNING)
        assert s.blockers == []

    def test_active_step_exists_in_steps(self):
        s = make_state(
            steps=[make_step(step_id="step-001")],
            progress=make_progress(total_steps=1, active_step_id="step-001"),
        )
        assert s.progress.active_step_id == "step-001"

    def test_active_step_not_found_raises(self):
        with pytest.raises(ValidationError, match="active_step_id"):
            make_state(
                steps=[make_step(step_id="step-001")],
                progress=make_progress(total_steps=1, active_step_id="step-999"),
            )

    def test_active_step_none_with_no_steps_valid(self):
        s = make_state(steps=[], progress=make_progress(total_steps=0))
        assert s.progress.active_step_id is None

    def test_steps_order_preserved(self):
        s = make_state(steps=[
            make_step(step_id="s-b", order_index=1),
            make_step(step_id="s-a", order_index=0),
        ])
        assert [st.step_id for st in s.steps] == ["s-b", "s-a"]


class TestRunOrchestrationEnvelope:
    def test_valid(self):
        e = make_envelope()
        assert e.envelope_id == "env-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="")

    def test_run_accessible(self):
        e = make_envelope()
        assert e.run.agent_id == "agent-code"
        assert e.run.phase == RunPhase.EXECUTING


class TestSerialization:
    def test_state_to_dict_and_back(self):
        s = make_state()
        data = s.model_dump()
        assert data["run_id"] == "run-001"
        assert data["phase"] == "executing"
        restored = ExecutionStateRecord(**data)
        assert restored.run_id == s.run_id
        assert restored.phase == s.phase

    def test_envelope_to_dict_and_back(self):
        e = make_envelope()
        data = e.model_dump()
        assert data["envelope_id"] == "env-001"
        restored = RunOrchestrationEnvelope(**data)
        assert restored.envelope_id == e.envelope_id
        assert restored.run.run_id == "run-001"


class TestIntegration:
    def test_sequential_run_executing_steps(self):
        steps = [
            RunStepRef(step_id="s-1", step_type="task_execution", order_index=0,
                       status=RunStatus.COMPLETED, task_id="t-001"),
            RunStepRef(step_id="s-2", step_type="task_execution", order_index=1,
                       status=RunStatus.RUNNING, task_id="t-002"),
            RunStepRef(step_id="s-3", step_type="task_execution", order_index=2,
                       status=RunStatus.PENDING, task_id="t-003"),
        ]
        progress = RunProgress(total_steps=3, completed_steps=1, active_step_id="s-2")
        state = ExecutionStateRecord(
            run_id="run-seq", agent_id="agent-code",
            phase=RunPhase.EXECUTING, status=RunStatus.RUNNING,
            mode=ExecutionMode.SEQUENTIAL,
            steps=steps, progress=progress,
        )
        env = RunOrchestrationEnvelope(envelope_id="env-seq", run=state)
        assert env.run.mode == ExecutionMode.SEQUENTIAL
        assert env.run.progress.completed_steps == 1
        assert env.run.progress.active_step_id == "s-2"
        assert len(env.run.steps) == 3

    def test_parallel_run_with_multiple_steps(self):
        steps = [
            RunStepRef(step_id="s-p1", step_type="analysis", order_index=0,
                       status=RunStatus.RUNNING, task_id="t-001"),
            RunStepRef(step_id="s-p2", step_type="retrieval", order_index=1,
                       status=RunStatus.RUNNING, task_id="t-002"),
            RunStepRef(step_id="s-p3", step_type="generation", order_index=2,
                       status=RunStatus.PENDING, task_id="t-003"),
        ]
        progress = RunProgress(total_steps=3, completed_steps=0, active_step_id="s-p1",
                               blocked_steps=0, failed_steps=0)
        state = ExecutionStateRecord(
            run_id="run-par", agent_id="agent-code",
            phase=RunPhase.EXECUTING, status=RunStatus.RUNNING,
            mode=ExecutionMode.PARALLEL,
            steps=steps, progress=progress,
        )
        env = RunOrchestrationEnvelope(envelope_id="env-par", run=state)
        assert env.run.mode == ExecutionMode.PARALLEL
        assert env.run.steps[0].status == RunStatus.RUNNING
        assert env.run.steps[1].status == RunStatus.RUNNING

    def test_blocked_run_waiting_on_approval(self):
        steps = [
            RunStepRef(step_id="s-1", step_type="tool_execution", order_index=0,
                       status=RunStatus.COMPLETED, task_id="t-001", tool_call_id="tc-001"),
            RunStepRef(step_id="s-2", step_type="deletion", order_index=1,
                       status=RunStatus.BLOCKED, task_id="t-002"),
        ]
        blockers = [
            RunBlockerRef(blocker_id="blk-001", blocker_type="approval",
                          reason="Requires human approval to delete API endpoint",
                          related_ref="approval://gate-001"),
        ]
        progress = RunProgress(total_steps=2, completed_steps=1, active_step_id="s-2",
                               blocked_steps=1)
        state = ExecutionStateRecord(
            run_id="run-blocked", agent_id="agent-code",
            phase=RunPhase.WAITING, status=RunStatus.BLOCKED,
            mode=ExecutionMode.SEQUENTIAL,
            steps=steps, blockers=blockers, progress=progress,
            policy_decision_id="pd-001",
        )
        env = RunOrchestrationEnvelope(envelope_id="env-blocked", run=state)
        assert env.run.status == RunStatus.BLOCKED
        assert len(env.run.blockers) == 1
        assert env.run.blockers[0].reason == "Requires human approval to delete API endpoint"
        assert env.run.policy_decision_id == "pd-001"

    def test_recovering_run_with_checkpoint_linkage(self):
        steps = [
            RunStepRef(step_id="s-1", step_type="task_execution", order_index=0,
                       status=RunStatus.COMPLETED, task_id="t-001"),
            RunStepRef(step_id="s-2", step_type="task_execution", order_index=1,
                       status=RunStatus.FAILED, task_id="t-002"),
            RunStepRef(step_id="s-3", step_type="task_execution", order_index=2,
                       status=RunStatus.PENDING, task_id="t-003"),
        ]
        progress = RunProgress(total_steps=3, completed_steps=1, active_step_id="s-2",
                               failed_steps=1)
        state = ExecutionStateRecord(
            run_id="run-recover", agent_id="agent-code",
            phase=RunPhase.RECOVERING, status=RunStatus.FAILED,
            mode=ExecutionMode.SEQUENTIAL,
            steps=steps, progress=progress,
            checkpoint_id="chk-001",
        )
        env = RunOrchestrationEnvelope(envelope_id="env-recover", run=state)
        assert env.run.phase == RunPhase.RECOVERING
        assert env.run.status == RunStatus.FAILED
        assert env.run.checkpoint_id == "chk-001"
        assert env.run.progress.failed_steps == 1

    def test_finalized_run_with_completed_steps(self):
        steps = [
            RunStepRef(step_id="s-1", step_type="planning", order_index=0,
                       status=RunStatus.COMPLETED, task_id="t-001"),
            RunStepRef(step_id="s-2", step_type="execution", order_index=1,
                       status=RunStatus.COMPLETED, task_id="t-002"),
            RunStepRef(step_id="s-3", step_type="verification", order_index=2,
                       status=RunStatus.COMPLETED, task_id="t-003"),
        ]
        progress = RunProgress(total_steps=3, completed_steps=3, active_step_id="s-3")
        state = ExecutionStateRecord(
            run_id="run-final", agent_id="agent-code",
            session_id="s-001", task_id="t-003", trace_id="trace-001",
            phase=RunPhase.TERMINATED, status=RunStatus.COMPLETED,
            mode=ExecutionMode.SEQUENTIAL,
            steps=steps, progress=progress,
        )
        env = RunOrchestrationEnvelope(envelope_id="env-final", run=state)
        assert env.run.phase == RunPhase.TERMINATED
        assert env.run.status == RunStatus.COMPLETED
        assert env.run.progress.completed_steps == 3
        assert env.run.progress.total_steps == 3
