import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from models.running_loop_contract import (
    LoopTriggerType, LoopGoalType, LoopPhase, LoopStatus, LoopStopReason,
    LoopIterationRecord, LoopMemorySnapshot, LoopExecutionPlan,
    LoopRuleSet, RunningLoopContractEnvelope,
)


NOW = datetime.now(timezone.utc)


def make_cycle(**overrides) -> LoopIterationRecord:
    defaults = dict(iteration=1, started_at=NOW, result_summary="Cycle 1 done")
    defaults.update(overrides)
    return LoopIterationRecord(**defaults)


def make_memory(**overrides) -> LoopMemorySnapshot:
    defaults = dict(current_objective="Build feature X", next_action="Implement module A")
    defaults.update(overrides)
    return LoopMemorySnapshot(**defaults)


def make_plan(**overrides) -> LoopExecutionPlan:
    defaults = dict(loop_id="loop-001")
    defaults.update(overrides)
    return LoopExecutionPlan(**defaults)


def make_envelope(**overrides) -> RunningLoopContractEnvelope:
    defaults = dict(
        envelope_id="env-loop-001", goal=LoopGoalType.BUILD,
        trigger=LoopTriggerType.MANUAL, objective="Build feature X",
        plan=make_plan(), memory=make_memory(),
        created_at=NOW, updated_at=NOW,
    )
    defaults.update(overrides)
    return RunningLoopContractEnvelope(**defaults)


class TestEnums:
    def test_loop_trigger_type_values(self):
        assert LoopTriggerType.MANUAL.value == "manual"
        assert LoopTriggerType.SCHEDULED.value == "scheduled"
        assert LoopTriggerType.EVENT.value == "event"
        assert LoopTriggerType.RECOVERY_RESUME.value == "recovery_resume"
        assert len(LoopTriggerType) == 4

    def test_loop_goal_type_values(self):
        assert LoopGoalType.BUILD.value == "build"
        assert LoopGoalType.REPAIR.value == "repair"
        assert LoopGoalType.VERIFY.value == "verify"
        assert LoopGoalType.REFACTOR.value == "refactor"
        assert LoopGoalType.RESEARCH.value == "research"
        assert LoopGoalType.MAINTAIN.value == "maintain"
        assert len(LoopGoalType) == 6

    def test_loop_phase_values(self):
        assert LoopPhase.INTAKE.value == "intake"
        assert LoopPhase.PLAN.value == "plan"
        assert LoopPhase.EXECUTE.value == "execute"
        assert LoopPhase.VERIFY.value == "verify"
        assert LoopPhase.UPDATE_STATE.value == "update_state"
        assert LoopPhase.STOP_CHECK.value == "stop_check"
        assert LoopPhase.HANDOFF.value == "handoff"
        assert len(LoopPhase) == 7

    def test_loop_status_values(self):
        assert LoopStatus.READY.value == "ready"
        assert LoopStatus.RUNNING.value == "running"
        assert LoopStatus.PAUSED.value == "paused"
        assert LoopStatus.BLOCKED.value == "blocked"
        assert LoopStatus.COMPLETED.value == "completed"
        assert LoopStatus.EXHAUSTED.value == "exhausted"
        assert LoopStatus.FAILED.value == "failed"
        assert len(LoopStatus) == 7

    def test_loop_stop_reason_values(self):
        assert LoopStopReason.SUCCESS.value == "success"
        assert LoopStopReason.NO_WORK.value == "no_work"
        assert LoopStopReason.BLOCKED_EXTERNAL.value == "blocked_external"
        assert LoopStopReason.MAX_ITERATIONS.value == "max_iterations"
        assert LoopStopReason.BUDGET_EXCEEDED.value == "budget_exceeded"
        assert LoopStopReason.REPEATED_NO_PROGRESS.value == "repeated_no_progress"
        assert LoopStopReason.APPROVAL_REQUIRED.value == "approval_required"
        assert LoopStopReason.VERIFICATION_FAILED.value == "verification_failed"
        assert len(LoopStopReason) == 8


class TestLoopIterationRecord:
    def test_valid(self):
        c = make_cycle()
        assert c.iteration == 1

    def test_iteration_zero_raises(self):
        with pytest.raises(ValidationError, match="iteration must be >= 1"):
            make_cycle(iteration=0)

    def test_iteration_negative_raises(self):
        with pytest.raises(ValidationError, match="iteration must be >= 1"):
            make_cycle(iteration=-1)

    def test_with_ended_at(self):
        c = make_cycle(ended_at=NOW)
        assert c.ended_at is not None

    def test_with_phase_transitions(self):
        c = make_cycle(phase_transitions=[LoopPhase.INTAKE, LoopPhase.PLAN])
        assert len(c.phase_transitions) == 2

    def test_with_actions(self):
        c = make_cycle(actions_performed=["Scanned todos", "Selected task"])
        assert c.actions_performed[0] == "Scanned todos"

    def test_with_artifacts(self):
        c = make_cycle(artifacts_touched=["todo.json", "state.md"])
        assert len(c.artifacts_touched) == 2

    def test_with_lessons(self):
        c = make_cycle(lessons_extracted=["Always verify first"])
        assert c.lessons_extracted[0] == "Always verify first"

    def test_with_verification_result(self):
        c = make_cycle(verification_result="PASS")
        assert c.verification_result == "PASS"

    def test_with_next_suggested_step(self):
        c = make_cycle(next_suggested_step="Implement module B")
        assert c.next_suggested_step == "Implement module B"


class TestLoopMemorySnapshot:
    def test_valid(self):
        m = make_memory()
        assert m.current_objective == "Build feature X"

    def test_blank_objective_raises(self):
        with pytest.raises(ValidationError):
            make_memory(current_objective="")

    def test_empty_next_action_valid(self):
        m = make_memory(next_action="")
        assert m.next_action == ""

    def test_with_active_task(self):
        m = make_memory(active_task_id="task-001")
        assert m.active_task_id == "task-001"

    def test_with_blockers(self):
        m = make_memory(unresolved_blockers=["Missing API key"])
        assert len(m.unresolved_blockers) == 1

    def test_with_failures(self):
        m = make_memory(known_failures=["Install failed"])
        assert m.known_failures[0] == "Install failed"

    def test_with_lessons(self):
        m = make_memory(recent_lessons=["Pin dependencies"])
        assert m.recent_lessons[0] == "Pin dependencies"

    def test_with_evidence(self):
        m = make_memory(recent_evidence=["Tested and passed"])
        assert m.recent_evidence[0] == "Tested and passed"


class TestLoopExecutionPlan:
    def test_valid(self):
        p = make_plan()
        assert p.loop_id == "loop-001"

    def test_blank_loop_id_raises(self):
        with pytest.raises(ValidationError):
            make_plan(loop_id="")

    def test_max_iterations_default(self):
        p = make_plan()
        assert p.max_iterations == 50

    def test_max_iterations_zero_raises(self):
        with pytest.raises(ValidationError, match="max_iterations must be > 0"):
            make_plan(max_iterations=0)

    def test_max_iterations_negative_raises(self):
        with pytest.raises(ValidationError, match="max_iterations must be > 0"):
            make_plan(max_iterations=-1)

    def test_max_no_progress_default(self):
        p = make_plan()
        assert p.max_no_progress_iterations == 5

    def test_max_no_progress_zero_valid(self):
        p = make_plan(max_no_progress_iterations=0)
        assert p.max_no_progress_iterations == 0

    def test_max_no_progress_negative_raises(self):
        with pytest.raises(ValidationError, match="max_no_progress_iterations must be >= 0"):
            make_plan(max_no_progress_iterations=-1)

    def test_verification_required_default_true(self):
        p = make_plan()
        assert p.verification_required is True

    def test_with_run_id(self):
        p = make_plan(run_id="run-001", session_id="sess-001")
        assert p.run_id == "run-001"
        assert p.session_id == "sess-001"


class TestLoopRuleSet:
    def test_empty_valid(self):
        r = LoopRuleSet()
        assert r.update_per_iteration == []

    def test_with_rules(self):
        r = LoopRuleSet(
            update_per_iteration=["loop_execution.md", "loop_memory.md"],
            stop_conditions=["max_iterations exceeded"],
            retry_conditions=["transient error"],
            escalate_conditions=["approval needed"],
            commit_conditions=["verified progress"],
            feature_done_conditions=["all acceptance criteria met"],
            lesson_promotion_rules=["3 occurrences promotes to rule"],
        )
        assert len(r.update_per_iteration) == 2
        assert r.stop_conditions[0] == "max_iterations exceeded"


class TestRunningLoopContractEnvelope:
    def test_valid(self):
        e = make_envelope()
        assert e.envelope_id == "env-loop-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="")

    def test_blank_objective_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(objective="")

    def test_default_status_ready(self):
        e = make_envelope()
        assert e.status == LoopStatus.READY

    def test_default_phase_intake(self):
        e = make_envelope()
        assert e.phase == LoopPhase.INTAKE

    def test_terminal_status_needs_stop_reason(self):
        with pytest.raises(ValidationError, match="terminal status requires a stop_reason"):
            make_envelope(status=LoopStatus.COMPLETED, stop_reason=None)

    def test_terminal_status_with_stop_reason_valid(self):
        e = make_envelope(status=LoopStatus.COMPLETED, stop_reason=LoopStopReason.SUCCESS,
                          cycles=[make_cycle(verification_result="PASS")])
        assert e.stop_reason == LoopStopReason.SUCCESS

    def test_stop_reason_without_terminal_status_raises(self):
        with pytest.raises(ValidationError, match="stop_reason requires terminal status"):
            make_envelope(status=LoopStatus.RUNNING, stop_reason=LoopStopReason.SUCCESS)

    def test_active_loop_needs_next_action(self):
        mem = make_memory(next_action="")
        with pytest.raises(ValidationError, match="active loop.*must have non-empty"):
            make_envelope(status=LoopStatus.RUNNING, memory=mem)

    def test_active_loop_with_next_action_valid(self):
        mem = make_memory(next_action="Implement module A")
        e = make_envelope(status=LoopStatus.RUNNING, memory=mem)
        assert e.memory.next_action == "Implement module A"

    def test_paused_loop_no_next_action_valid(self):
        mem = make_memory(next_action="")
        e = make_envelope(status=LoopStatus.PAUSED, memory=mem)
        assert e.status == LoopStatus.PAUSED

    def test_completed_needs_verification_on_cycles(self):
        with pytest.raises(ValidationError, match="verification_result"):
            make_envelope(
                status=LoopStatus.COMPLETED, stop_reason=LoopStopReason.SUCCESS,
                cycles=[make_cycle(verification_result="")],
            )

    def test_completed_with_verification_valid(self):
        e = make_envelope(
            status=LoopStatus.COMPLETED, stop_reason=LoopStopReason.SUCCESS,
            cycles=[make_cycle(verification_result="PASS")],
        )
        assert e.status == LoopStatus.COMPLETED

    def test_exhausted_needs_verification_on_cycles(self):
        with pytest.raises(ValidationError, match="verification_result"):
            make_envelope(
                status=LoopStatus.EXHAUSTED, stop_reason=LoopStopReason.MAX_ITERATIONS,
                cycles=[make_cycle(verification_result=None)],
            )

    def test_exhausted_with_verification_valid(self):
        e = make_envelope(
            status=LoopStatus.EXHAUSTED, stop_reason=LoopStopReason.MAX_ITERATIONS,
            cycles=[make_cycle(verification_result="PASS")],
            plan=make_plan(verification_required=True),
        )
        assert e.status == LoopStatus.EXHAUSTED

    def test_failed_no_verification_needed(self):
        e = make_envelope(
            status=LoopStatus.FAILED, stop_reason=LoopStopReason.VERIFICATION_FAILED,
            cycles=[make_cycle()],
        )
        assert e.status == LoopStatus.FAILED

    def test_multiple_cycles(self):
        e = make_envelope(
            cycles=[
                make_cycle(iteration=1, verification_result="PASS"),
                make_cycle(iteration=2, verification_result="PASS"),
            ],
        )
        assert len(e.cycles) == 2

    def test_all_goal_types(self):
        for g in LoopGoalType:
            e = make_envelope(goal=g)
            assert e.goal == g

    def test_all_trigger_types(self):
        for t in LoopTriggerType:
            e = make_envelope(trigger=t)
            assert e.trigger == t

    def test_all_phases(self):
        for p in LoopPhase:
            e = make_envelope(phase=p)
            assert e.phase == p

    def test_all_statuses_non_terminal(self):
        for s in LoopStatus:
            kwargs = dict(status=s)
            if s in (LoopStatus.COMPLETED, LoopStatus.EXHAUSTED, LoopStatus.FAILED):
                kwargs["stop_reason"] = LoopStopReason.SUCCESS
                kwargs["cycles"] = [make_cycle(verification_result="PASS")]
            e = make_envelope(**kwargs)
            assert e.status == s

    def test_with_rules(self):
        rules = LoopRuleSet(stop_conditions=["max_iterations"])
        e = make_envelope(rules=rules)
        assert len(e.rules.stop_conditions) == 1


class TestSerialization:
    def test_envelope_to_dict_and_back(self):
        e = make_envelope()
        data = e.model_dump()
        assert data["envelope_id"] == "env-loop-001"
        restored = RunningLoopContractEnvelope(**data)
        assert restored.envelope_id == e.envelope_id
        assert restored.memory.current_objective == "Build feature X"


class TestIntegration:
    def test_build_loop_full_lifecycle(self):
        plan = LoopExecutionPlan(loop_id="loop-build", max_iterations=10)
        mem = LoopMemorySnapshot(current_objective="Add login feature",
                                 next_action="Create auth module")
        c1 = LoopIterationRecord(iteration=1, started_at=NOW,
                                 actions_performed=["Created auth model"],
                                 verification_result="PASS",
                                 result_summary="Auth model created")
        env = RunningLoopContractEnvelope(
            envelope_id="env-build", goal=LoopGoalType.BUILD,
            trigger=LoopTriggerType.MANUAL, objective="Add login feature",
            plan=plan, memory=mem, created_at=NOW, updated_at=NOW,
            cycles=[c1], status=LoopStatus.COMPLETED,
            stop_reason=LoopStopReason.SUCCESS,
        )
        assert env.status == LoopStatus.COMPLETED

    def test_repair_loop_with_no_progress(self):
        plan = LoopExecutionPlan(loop_id="loop-repair", max_no_progress_iterations=3)
        mem = LoopMemorySnapshot(current_objective="Fix auth bug",
                                 next_action="Isolate the issue")
        env = RunningLoopContractEnvelope(
            envelope_id="env-repair", goal=LoopGoalType.REPAIR,
            trigger=LoopTriggerType.EVENT, objective="Fix auth bug",
            plan=plan, memory=mem, created_at=NOW, updated_at=NOW,
            status=LoopStatus.EXHAUSTED, stop_reason=LoopStopReason.MAX_ITERATIONS,
            cycles=[make_cycle(verification_result="PASS")],
        )
        assert env.status == LoopStatus.EXHAUSTED

    def test_recovery_resume_loop(self):
        plan = LoopExecutionPlan(loop_id="loop-resume")
        mem = LoopMemorySnapshot(current_objective="Continue feature build",
                                 next_action="Pick up task-003",
                                 unresolved_blockers=["Pending review"])
        env = RunningLoopContractEnvelope(
            envelope_id="env-resume", goal=LoopGoalType.BUILD,
            trigger=LoopTriggerType.RECOVERY_RESUME,
            objective="Complete feature build after crash",
            plan=plan, memory=mem, created_at=NOW, updated_at=NOW,
            status=LoopStatus.RUNNING,
            cycles=[make_cycle(verification_result="PASS")],
        )
        assert env.trigger == LoopTriggerType.RECOVERY_RESUME
        assert env.memory.unresolved_blockers[0] == "Pending review"

    def test_loop_with_rules_and_artifact_policy(self):
        rules = LoopRuleSet(
            update_per_iteration=["todo.json", "state.md", "loop_memory.md"],
            stop_conditions=["max_iterations", "verification_failed"],
            commit_conditions=["verified_progress"],
        )
        plan = LoopExecutionPlan(loop_id="loop-rules", max_iterations=25)
        mem = LoopMemorySnapshot(current_objective="Refactor utils",
                                 next_action="Extract helper functions")
        env = RunningLoopContractEnvelope(
            envelope_id="env-rules", goal=LoopGoalType.REFACTOR,
            trigger=LoopTriggerType.MANUAL, objective="Refactor utils",
            plan=plan, rules=rules, memory=mem,
            created_at=NOW, updated_at=NOW,
        )
        assert len(env.rules.update_per_iteration) == 3
        assert env.rules.stop_conditions[0] == "max_iterations"

    def test_repeated_no_progress_with_maintain_goal(self):
        plan = LoopExecutionPlan(loop_id="loop-mnt", max_no_progress_iterations=3)
        mem = LoopMemorySnapshot(current_objective="Routine dep update",
                                 next_action="Update deps")
        cycles = [make_cycle(iteration=1, progress_delta="no_progress", verification_result="PASS")]
        env = RunningLoopContractEnvelope(
            envelope_id="env-mnt", goal=LoopGoalType.MAINTAIN,
            trigger=LoopTriggerType.MANUAL, objective="Routine dep update",
            plan=plan, memory=mem, created_at=NOW, updated_at=NOW,
            cycles=cycles, status=LoopStatus.EXHAUSTED,
            stop_reason=LoopStopReason.REPEATED_NO_PROGRESS,
        )
        assert env.goal == LoopGoalType.MAINTAIN

    def test_repeated_no_progress_no_cycles_matching(self):
        plan = LoopExecutionPlan(loop_id="loop-rnp", max_no_progress_iterations=3)
        mem = LoopMemorySnapshot(current_objective="Fix flaky test",
                                 next_action="Investigate test-003")
        cycles = [
            make_cycle(iteration=1, progress_delta="added", verification_result="PASS"),
            make_cycle(iteration=2, progress_delta="added", verification_result="PASS"),
        ]
        env = RunningLoopContractEnvelope(
            envelope_id="env-rnp", goal=LoopGoalType.REPAIR,
            trigger=LoopTriggerType.MANUAL, objective="Fix flaky test",
            plan=plan, memory=mem, created_at=NOW, updated_at=NOW,
            cycles=cycles, status=LoopStatus.EXHAUSTED,
            stop_reason=LoopStopReason.REPEATED_NO_PROGRESS,
        )
        assert env.stop_reason == LoopStopReason.REPEATED_NO_PROGRESS
