import pytest
from pydantic import ValidationError
from models.checkpoint_recovery_contract import (
    CheckpointStatus, CheckpointBoundaryType, RecoveryDisposition, SnapshotConsistencyLevel,
    CheckpointProgress, StateSnapshotRef, RecoveryPolicy, RestoreAttempt,
    CheckpointRecord, SessionRecoveryEnvelope,
)


def make_progress(**overrides) -> CheckpointProgress:
    defaults = dict(completed_units=3, next_unit_ref="unit-004")
    defaults.update(overrides)
    return CheckpointProgress(**defaults)


def make_snapshot(**overrides) -> StateSnapshotRef:
    defaults = dict(snapshot_ref_id="ss-001", snapshot_uri="s3://checkpoints/run-001/cp-001.json", serialization_format="json")
    defaults.update(overrides)
    return StateSnapshotRef(**defaults)


def make_policy(**overrides) -> RecoveryPolicy:
    defaults = dict(disposition=RecoveryDisposition.RESUME, resume_from_unit_ref="unit-004")
    defaults.update(overrides)
    return RecoveryPolicy(**defaults)


def make_attempt(**overrides) -> RestoreAttempt:
    defaults = dict(attempt_id="att-001", attempted_at="2026-07-04T10:00:00Z", outcome="success")
    defaults.update(overrides)
    return RestoreAttempt(**defaults)


def make_checkpoint(**overrides) -> CheckpointRecord:
    defaults = dict(
        checkpoint_id="cp-001", session_id="sess-001", run_id="run-001", agent_id="agent-code",
        status=CheckpointStatus.RESUMABLE, boundary_type=CheckpointBoundaryType.TASK_UNIT_COMPLETED,
        consistency_level=SnapshotConsistencyLevel.CONSISTENT,
        progress=make_progress(), snapshot=make_snapshot(), recovery_policy=make_policy(),
    )
    defaults.update(overrides)
    return CheckpointRecord(**defaults)


def make_envelope(**overrides) -> SessionRecoveryEnvelope:
    defaults = dict(envelope_id="env-001", checkpoint=make_checkpoint())
    defaults.update(overrides)
    return SessionRecoveryEnvelope(**defaults)


class TestEnums:
    def test_checkpoint_status_values(self):
        assert CheckpointStatus.CREATED.value == "created"
        assert CheckpointStatus.RESUMABLE.value == "resumable"
        assert CheckpointStatus.RESTORED.value == "restored"
        assert CheckpointStatus.STALE.value == "stale"
        assert CheckpointStatus.INVALID.value == "invalid"
        assert CheckpointStatus.SUPERSEDED.value == "superseded"
        assert len(CheckpointStatus) == 6

    def test_boundary_type_values(self):
        assert CheckpointBoundaryType.TASK_UNIT_COMPLETED.value == "task_unit_completed"
        assert CheckpointBoundaryType.TOOL_PHASE_COMPLETED.value == "tool_phase_completed"
        assert CheckpointBoundaryType.MODEL_PHASE_COMPLETED.value == "model_phase_completed"
        assert CheckpointBoundaryType.APPROVAL_WAIT.value == "approval_wait"
        assert CheckpointBoundaryType.USER_INPUT_WAIT.value == "user_input_wait"
        assert CheckpointBoundaryType.MANUAL_PAUSE.value == "manual_pause"
        assert len(CheckpointBoundaryType) == 6

    def test_recovery_disposition_values(self):
        assert RecoveryDisposition.RESUME.value == "resume"
        assert RecoveryDisposition.RESTART_UNIT.value == "restart_unit"
        assert RecoveryDisposition.ESCALATE.value == "escalate"
        assert RecoveryDisposition.ABORT.value == "abort"
        assert len(RecoveryDisposition) == 4

    def test_snapshot_consistency_level_values(self):
        assert SnapshotConsistencyLevel.PARTIAL.value == "partial"
        assert SnapshotConsistencyLevel.CONSISTENT.value == "consistent"
        assert SnapshotConsistencyLevel.VERIFIED.value == "verified"
        assert len(SnapshotConsistencyLevel) == 3


class TestCheckpointProgress:
    def test_valid(self):
        p = make_progress()
        assert p.completed_units == 3
        assert p.next_unit_ref == "unit-004"

    def test_with_all_fields(self):
        p = make_progress(completed_units=5, remaining_units=2, last_completed_unit_ref="unit-005", progress_note="All tests pass")
        assert p.remaining_units == 2
        assert p.progress_note == "All tests pass"

    def test_default_zero(self):
        p = CheckpointProgress()
        assert p.completed_units == 0
        assert p.next_unit_ref is None

    def test_negative_completed_units_raises(self):
        with pytest.raises(ValidationError, match="non-negative"):
            make_progress(completed_units=-1)

    def test_negative_remaining_units_raises(self):
        with pytest.raises(ValidationError, match="non-negative"):
            make_progress(remaining_units=-1)


class TestStateSnapshotRef:
    def test_valid(self):
        s = make_snapshot()
        assert s.snapshot_ref_id == "ss-001"
        assert s.serialization_format == "json"

    def test_with_hash_and_size(self):
        s = make_snapshot(snapshot_hash="sha256-abc", size_bytes=4096)
        assert s.size_bytes == 4096

    def test_blank_ref_id_raises(self):
        with pytest.raises(ValidationError):
            make_snapshot(snapshot_ref_id="")

    def test_blank_uri_raises(self):
        with pytest.raises(ValidationError):
            make_snapshot(snapshot_uri="")

    def test_blank_format_raises(self):
        with pytest.raises(ValidationError):
            make_snapshot(serialization_format="")

    def test_negative_size_raises(self):
        with pytest.raises(ValidationError, match="non-negative"):
            make_snapshot(size_bytes=-1)

    def test_zero_size_valid(self):
        s = make_snapshot(size_bytes=0)
        assert s.size_bytes == 0


class TestRecoveryPolicy:
    def test_valid_resume(self):
        p = make_policy()
        assert p.disposition == RecoveryDisposition.RESUME
        assert p.max_restore_attempts == 3

    def test_default_max_restore_attempts(self):
        p = RecoveryPolicy(disposition=RecoveryDisposition.ABORT)
        assert p.max_restore_attempts == 3
        assert p.requires_validation_before_resume is True

    def test_all_dispositions_accepted(self):
        for d in RecoveryDisposition:
            kwargs = dict(disposition=d)
            if d in (RecoveryDisposition.RESUME, RecoveryDisposition.RESTART_UNIT):
                kwargs["resume_from_unit_ref"] = "unit-001"
            p = RecoveryPolicy(**kwargs)
            assert p.disposition == d

    def test_resume_needs_unit_ref(self):
        with pytest.raises(ValidationError, match="resume_from_unit_ref"):
            RecoveryPolicy(disposition=RecoveryDisposition.RESUME)

    def test_restart_unit_needs_unit_ref(self):
        with pytest.raises(ValidationError, match="resume_from_unit_ref"):
            RecoveryPolicy(disposition=RecoveryDisposition.RESTART_UNIT)

    def test_escalate_no_unit_ref_valid(self):
        p = RecoveryPolicy(disposition=RecoveryDisposition.ESCALATE)
        assert p.disposition == RecoveryDisposition.ESCALATE

    def test_abort_no_unit_ref_valid(self):
        p = RecoveryPolicy(disposition=RecoveryDisposition.ABORT)
        assert p.disposition == RecoveryDisposition.ABORT

    def test_max_restore_attempts_zero_raises(self):
        with pytest.raises(ValidationError, match="at least 1"):
            RecoveryPolicy(disposition=RecoveryDisposition.ABORT, max_restore_attempts=0)

    def test_max_restore_attempts_one_valid(self):
        p = make_policy(max_restore_attempts=1)
        assert p.max_restore_attempts == 1


class TestRestoreAttempt:
    def test_valid(self):
        a = make_attempt()
        assert a.attempt_id == "att-001"
        assert a.outcome == "success"

    def test_with_note(self):
        a = make_attempt(note="Restored successfully")
        assert a.note == "Restored successfully"

    def test_blank_attempt_id_raises(self):
        with pytest.raises(ValidationError):
            make_attempt(attempt_id="")

    def test_blank_attempted_at_raises(self):
        with pytest.raises(ValidationError):
            make_attempt(attempted_at="")

    def test_blank_outcome_raises(self):
        with pytest.raises(ValidationError):
            make_attempt(outcome="   ")


class TestCheckpointRecord:
    def test_valid(self):
        c = make_checkpoint()
        assert c.checkpoint_id == "cp-001"
        assert c.status == CheckpointStatus.RESUMABLE
        assert c.boundary_type == CheckpointBoundaryType.TASK_UNIT_COMPLETED

    def test_with_optional_fields(self):
        c = make_checkpoint(task_id="t-001", trace_id="trace-001")
        assert c.task_id == "t-001"

    def test_with_restore_attempts(self):
        c = make_checkpoint(restore_attempts=[make_attempt()])
        assert len(c.restore_attempts) == 1

    def test_default_empty_restore_attempts(self):
        c = make_checkpoint()
        assert c.restore_attempts == []

    def test_blank_checkpoint_id_raises(self):
        with pytest.raises(ValidationError):
            make_checkpoint(checkpoint_id="")

    def test_blank_session_id_raises(self):
        with pytest.raises(ValidationError):
            make_checkpoint(session_id="")

    def test_blank_run_id_raises(self):
        with pytest.raises(ValidationError):
            make_checkpoint(run_id="")

    def test_blank_agent_id_raises(self):
        with pytest.raises(ValidationError):
            make_checkpoint(agent_id="")

    def test_all_status_values_accepted(self):
        for s in CheckpointStatus:
            kwargs = dict(status=s)
            if s in (CheckpointStatus.INVALID, CheckpointStatus.STALE):
                kwargs["recovery_policy"] = RecoveryPolicy(disposition=RecoveryDisposition.ABORT)
            c = make_checkpoint(**kwargs)
            assert c.status == s

    def test_all_boundary_types_accepted(self):
        for b in CheckpointBoundaryType:
            c = make_checkpoint(boundary_type=b)
            assert c.boundary_type == b

    def test_all_consistency_levels_accepted(self):
        for lv in SnapshotConsistencyLevel:
            c = make_checkpoint(consistency_level=lv)
            assert c.consistency_level == lv

    def test_invalid_with_resume_raises(self):
        with pytest.raises(ValidationError, match="RESUME"):
            make_checkpoint(
                status=CheckpointStatus.INVALID,
                recovery_policy=RecoveryPolicy(disposition=RecoveryDisposition.RESUME, resume_from_unit_ref="unit-001"),
            )

    def test_stale_with_resume_raises(self):
        with pytest.raises(ValidationError, match="RESUME"):
            make_checkpoint(
                status=CheckpointStatus.STALE,
                recovery_policy=RecoveryPolicy(disposition=RecoveryDisposition.RESUME, resume_from_unit_ref="unit-001"),
            )

    def test_invalid_with_abort_valid(self):
        c = make_checkpoint(
            status=CheckpointStatus.INVALID,
            recovery_policy=RecoveryPolicy(disposition=RecoveryDisposition.ABORT),
        )
        assert c.status == CheckpointStatus.INVALID

    def test_stale_with_escalate_valid(self):
        c = make_checkpoint(
            status=CheckpointStatus.STALE,
            recovery_policy=RecoveryPolicy(disposition=RecoveryDisposition.ESCALATE),
        )
        assert c.status == CheckpointStatus.STALE


class TestSessionRecoveryEnvelope:
    def test_valid(self):
        e = make_envelope()
        assert e.envelope_id == "env-001"
        assert e.checkpoint.checkpoint_id == "cp-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="")


class TestSerialization:
    def test_checkpoint_to_dict_and_back(self):
        c = make_checkpoint()
        data = c.model_dump()
        assert data["checkpoint_id"] == "cp-001"
        assert data["status"] == "resumable"
        restored = CheckpointRecord(**data)
        assert restored.checkpoint_id == c.checkpoint_id

    def test_envelope_to_dict_and_back(self):
        e = make_envelope()
        data = e.model_dump()
        assert data["envelope_id"] == "env-001"
        restored = SessionRecoveryEnvelope(**data)
        assert restored.envelope_id == e.envelope_id


class TestIntegration:
    def test_resumable_checkpoint_after_completed_task_unit(self):
        cp = CheckpointRecord(
            checkpoint_id="cp-resume", session_id="sess-001", run_id="run-001", agent_id="agent-code",
            status=CheckpointStatus.RESUMABLE,
            boundary_type=CheckpointBoundaryType.TASK_UNIT_COMPLETED,
            consistency_level=SnapshotConsistencyLevel.CONSISTENT,
            progress=CheckpointProgress(completed_units=3, remaining_units=2, last_completed_unit_ref="unit-003", next_unit_ref="unit-004"),
            snapshot=StateSnapshotRef(snapshot_ref_id="ss-res", snapshot_uri="s3://cp/run-001/cp-resume.json", serialization_format="json", size_bytes=8192),
            recovery_policy=RecoveryPolicy(disposition=RecoveryDisposition.RESUME, resume_from_unit_ref="unit-004", max_restore_attempts=3),
        )
        env = SessionRecoveryEnvelope(envelope_id="env-resume", checkpoint=cp)
        assert env.checkpoint.progress.completed_units == 3
        assert env.checkpoint.recovery_policy.resume_from_unit_ref == "unit-004"
        assert env.checkpoint.snapshot.size_bytes == 8192

    def test_manual_pause_checkpoint(self):
        cp = CheckpointRecord(
            checkpoint_id="cp-pause", session_id="sess-002", run_id="run-002", agent_id="agent-code",
            status=CheckpointStatus.CREATED,
            boundary_type=CheckpointBoundaryType.MANUAL_PAUSE,
            consistency_level=SnapshotConsistencyLevel.CONSISTENT,
            progress=CheckpointProgress(completed_units=2, next_unit_ref="unit-003"),
            snapshot=StateSnapshotRef(snapshot_ref_id="ss-pause", snapshot_uri="s3://cp/run-002/cp-pause.json", serialization_format="json"),
            recovery_policy=RecoveryPolicy(disposition=RecoveryDisposition.RESUME, resume_from_unit_ref="unit-003"),
        )
        assert cp.status == CheckpointStatus.CREATED
        assert cp.boundary_type == CheckpointBoundaryType.MANUAL_PAUSE

    def test_approval_wait_checkpoint(self):
        cp = CheckpointRecord(
            checkpoint_id="cp-approval", session_id="sess-003", run_id="run-003", task_id="t-001", agent_id="agent-code",
            status=CheckpointStatus.RESUMABLE,
            boundary_type=CheckpointBoundaryType.APPROVAL_WAIT,
            consistency_level=SnapshotConsistencyLevel.PARTIAL,
            progress=CheckpointProgress(completed_units=1, next_unit_ref="unit-002"),
            snapshot=StateSnapshotRef(snapshot_ref_id="ss-app", snapshot_uri="s3://cp/run-003/cp-approval.json", serialization_format="json"),
            recovery_policy=RecoveryPolicy(disposition=RecoveryDisposition.RESUME, resume_from_unit_ref="unit-002"),
        )
        assert cp.task_id == "t-001"
        assert cp.consistency_level == SnapshotConsistencyLevel.PARTIAL

    def test_invalid_checkpoint_after_failed_restore(self):
        cp = CheckpointRecord(
            checkpoint_id="cp-invalid", session_id="sess-004", run_id="run-004", agent_id="agent-code",
            status=CheckpointStatus.INVALID,
            boundary_type=CheckpointBoundaryType.TASK_UNIT_COMPLETED,
            consistency_level=SnapshotConsistencyLevel.CONSISTENT,
            progress=CheckpointProgress(completed_units=3),
            snapshot=StateSnapshotRef(snapshot_ref_id="ss-inv", snapshot_uri="s3://cp/run-004/cp-invalid.json", serialization_format="json"),
            recovery_policy=RecoveryPolicy(disposition=RecoveryDisposition.ABORT),
            restore_attempts=[
                RestoreAttempt(attempt_id="att-fail", attempted_at="2026-07-04T10:05:00Z", outcome="failed", note="Snapshot hash mismatch"),
            ],
        )
        assert cp.status == CheckpointStatus.INVALID
        assert cp.recovery_policy.disposition == RecoveryDisposition.ABORT
        assert len(cp.restore_attempts) == 1
        assert cp.restore_attempts[0].outcome == "failed"

    def test_superseded_checkpoint_replaced_by_newer(self):
        cp = CheckpointRecord(
            checkpoint_id="cp-super", session_id="sess-005", run_id="run-005", agent_id="agent-code",
            status=CheckpointStatus.SUPERSEDED,
            boundary_type=CheckpointBoundaryType.TASK_UNIT_COMPLETED,
            consistency_level=SnapshotConsistencyLevel.CONSISTENT,
            progress=CheckpointProgress(completed_units=2, last_completed_unit_ref="unit-002", next_unit_ref="unit-003"),
            snapshot=StateSnapshotRef(snapshot_ref_id="ss-super", snapshot_uri="s3://cp/run-005/cp-super.json", serialization_format="json"),
            recovery_policy=RecoveryPolicy(disposition=RecoveryDisposition.ESCALATE),
        )
        assert cp.status == CheckpointStatus.SUPERSEDED
        assert cp.recovery_policy.disposition == RecoveryDisposition.ESCALATE
