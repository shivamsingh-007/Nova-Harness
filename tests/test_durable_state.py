import pytest
from pydantic import ValidationError
from models.durable_state import (
    RunState,
    CheckpointRecord,
    StepRecord,
    ToolCallRecord,
    ArtifactRecord,
    RetryState,
    ResumePointer,
    RunStatus,
    StepStatus,
    ToolCallStatus,
    ArtifactType,
)


def make_artifact(**overrides) -> ArtifactRecord:
    kwargs = dict(
        artifact_id="art-001",
        artifact_type=ArtifactType.FILE,
        path="/workspace/output.txt",
        description="Generated output",
    )
    kwargs.update(overrides)
    return ArtifactRecord(**kwargs)


def make_tool_call(**overrides) -> ToolCallRecord:
    kwargs = dict(
        tool_call_id="tc-001",
        tool_name="bash",
        status=ToolCallStatus.SUCCESS,
        arguments={"command": "pytest tests/"},
        output={"stdout": "all passed", "exit_code": 0},
        started_at="2025-01-01T00:00:00Z",
        finished_at="2025-01-01T00:01:00Z",
    )
    kwargs.update(overrides)
    return ToolCallRecord(**kwargs)


def make_step(**overrides) -> StepRecord:
    kwargs = dict(
        step_id="step-001",
        name="Run tests",
        status=StepStatus.SUCCESS,
        tool_calls=[make_tool_call()],
        artifacts=[make_artifact()],
        retry=RetryState(),
        started_at="2025-01-01T00:00:00Z",
        finished_at="2025-01-01T00:01:30Z",
    )
    kwargs.update(overrides)
    return StepRecord(**kwargs)


def make_checkpoint(**overrides) -> CheckpointRecord:
    kwargs = dict(
        checkpoint_id="cp-001",
        run_id="run-001",
        step_id="step-001",
        summary="Completed test step",
        created_at="2025-01-01T00:01:30Z",
    )
    kwargs.update(overrides)
    return CheckpointRecord(**kwargs)


def make_run(**overrides) -> RunState:
    kwargs = dict(
        run_id="run-001",
        task_id="task-001",
        status=RunStatus.RUNNING,
        steps=[make_step()],
        checkpoints=[make_checkpoint()],
        resume=ResumePointer(),
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:01:30Z",
    )
    kwargs.update(overrides)
    return RunState(**kwargs)


class TestRunState:
    def test_valid_run(self):
        run = make_run()
        assert run.run_id == "run-001"
        assert run.status == RunStatus.RUNNING

    def test_empty_run_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_run(run_id="")
        assert "run_id must not be empty" in str(exc.value)

    def test_empty_task_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_run(task_id="")
        assert "task_id must not be empty" in str(exc.value)

    def test_empty_created_at_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_run(created_at="")
        assert "created_at must not be empty" in str(exc.value)

    def test_empty_updated_at_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_run(updated_at="")
        assert "updated_at must not be empty" in str(exc.value)

    def test_completed_status(self):
        run = make_run(status=RunStatus.COMPLETED)
        assert run.status == RunStatus.COMPLETED

    def test_failed_status(self):
        run = make_run(status=RunStatus.FAILED)
        assert run.status == RunStatus.FAILED

    def test_paused_status(self):
        run = make_run(status=RunStatus.PAUSED)
        assert run.status == RunStatus.PAUSED

    def test_cancelled_status(self):
        run = make_run(status=RunStatus.CANCELLED)
        assert run.status == RunStatus.CANCELLED


class TestCheckpointRecord:
    def test_valid_checkpoint(self):
        cp = make_checkpoint()
        assert cp.checkpoint_id == "cp-001"

    def test_empty_checkpoint_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_checkpoint(checkpoint_id="")
        assert "checkpoint_id must not be empty" in str(exc.value)

    def test_empty_run_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_checkpoint(run_id="")
        assert "run_id must not be empty" in str(exc.value)

    def test_empty_created_at_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_checkpoint(created_at="")
        assert "created_at must not be empty" in str(exc.value)

    def test_default_state_version(self):
        cp = make_checkpoint()
        assert cp.state_version == 1


class TestStepRecord:
    def test_valid_step(self):
        step = make_step()
        assert step.step_id == "step-001"
        assert len(step.tool_calls) == 1
        assert len(step.artifacts) == 1

    def test_empty_step_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_step(step_id="")
        assert "step_id must not be empty" in str(exc.value)

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_step(name="")
        assert "name must not be empty" in str(exc.value)

    def test_success_step_without_finished_at_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_step(finished_at=None)
        assert "finished_at is required for SUCCESS or FAILED steps" in str(exc.value)

    def test_failed_step_without_finished_at_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_step(status=StepStatus.FAILED, finished_at=None)
        assert "finished_at is required for SUCCESS or FAILED steps" in str(exc.value)

    def test_running_step_without_finished_at_is_valid(self):
        step = make_step(status=StepStatus.RUNNING, finished_at=None)
        assert step.status == StepStatus.RUNNING
        assert step.finished_at is None

    def test_pending_step_without_finished_at_is_valid(self):
        step = make_step(status=StepStatus.PENDING, finished_at=None)
        assert step.status == StepStatus.PENDING

    def test_skipped_step_without_finished_at_is_valid(self):
        step = make_step(status=StepStatus.SKIPPED, finished_at=None)
        assert step.status == StepStatus.SKIPPED

    def test_retry_count_exceeds_max_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_step(retry=RetryState(retry_count=3, max_retries=2))
        assert "retry_count must not exceed max_retries" in str(exc.value)

    def test_retry_count_within_max_is_valid(self):
        step = make_step(retry=RetryState(retry_count=2, max_retries=3))
        assert step.retry.retry_count == 2

    def test_retry_count_equal_max_is_valid(self):
        step = make_step(retry=RetryState(retry_count=3, max_retries=3))
        assert step.retry.retry_count == 3


class TestToolCallRecord:
    def test_valid_tool_call(self):
        tc = make_tool_call()
        assert tc.tool_call_id == "tc-001"

    def test_empty_tool_call_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_tool_call(tool_call_id="")
        assert "tool_call_id must not be empty" in str(exc.value)

    def test_empty_tool_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_tool_call(tool_name="")
        assert "tool_name must not be empty" in str(exc.value)

    def test_error_status_without_error_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_tool_call(status=ToolCallStatus.ERROR, error=None)
        assert "error must be set when status is ERROR" in str(exc.value)

    def test_error_status_with_error_is_valid(self):
        tc = make_tool_call(status=ToolCallStatus.ERROR, error="Command failed", output=None)
        assert tc.error == "Command failed"

    def test_success_status_without_error_is_valid(self):
        tc = make_tool_call(status=ToolCallStatus.SUCCESS, error=None)
        assert tc.status == ToolCallStatus.SUCCESS

    def test_requested_status_without_error_is_valid(self):
        tc = make_tool_call(status=ToolCallStatus.REQUESTED, error=None)
        assert tc.status == ToolCallStatus.REQUESTED

    def test_blocked_status_without_error_is_valid(self):
        tc = make_tool_call(status=ToolCallStatus.BLOCKED, error=None)
        assert tc.status == ToolCallStatus.BLOCKED


class TestArtifactRecord:
    def test_valid_artifact(self):
        art = make_artifact()
        assert art.artifact_id == "art-001"

    def test_empty_artifact_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_artifact(artifact_id="")
        assert "artifact_id must not be empty" in str(exc.value)

    def test_empty_path_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_artifact(path="")
        assert "path must not be empty" in str(exc.value)

    def test_all_artifact_types(self):
        for at in ArtifactType:
            art = make_artifact(artifact_type=at)
            assert art.artifact_type == at


class TestResumePointer:
    def test_default_can_resume(self):
        rp = ResumePointer()
        assert rp.can_resume is True
        assert rp.resume_reason is None

    def test_cannot_resume_without_reason_raises(self):
        with pytest.raises(ValidationError) as exc:
            ResumePointer(can_resume=False)
        assert "resume_reason is required when can_resume is False" in str(exc.value)

    def test_cannot_resume_with_reason_is_valid(self):
        rp = ResumePointer(can_resume=False, resume_reason="Missing API key")
        assert rp.can_resume is False
        assert rp.resume_reason == "Missing API key"

    def test_can_resume_with_reason_is_valid(self):
        rp = ResumePointer(can_resume=True, resume_reason="All clear")
        assert rp.can_resume is True


class TestRetryState:
    def test_default_retry_state(self):
        rs = RetryState()
        assert rs.retry_count == 0
        assert rs.max_retries == 0
        assert rs.last_error is None

    def test_retry_state_with_values(self):
        rs = RetryState(retry_count=1, max_retries=3, last_error="Timeout")
        assert rs.retry_count == 1
        assert rs.last_error == "Timeout"


class TestSerialization:
    def test_run_state_serialize(self):
        run = make_run()
        data = run.model_dump()
        assert data["run_id"] == "run-001"
        assert data["status"] == "running"
        assert len(data["steps"]) == 1
        assert len(data["checkpoints"]) == 1

    def test_step_serialize(self):
        step = make_step()
        data = step.model_dump()
        assert data["step_id"] == "step-001"
        assert data["status"] == "success"
        assert data["tool_calls"][0]["tool_name"] == "bash"

    def test_tool_call_serialize(self):
        tc = make_tool_call()
        data = tc.model_dump()
        assert data["tool_call_id"] == "tc-001"
        assert data["arguments"] == {"command": "pytest tests/"}

    def test_checkpoint_serialize(self):
        cp = make_checkpoint()
        data = cp.model_dump()
        assert data["checkpoint_id"] == "cp-001"
        assert data["state_version"] == 1
