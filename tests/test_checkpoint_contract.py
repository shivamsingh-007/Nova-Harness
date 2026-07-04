import pytest
from pydantic import ValidationError
from models.checkpoint_contract import (
    SessionStatus,
    CheckpointType,
    ResumeDisposition,
    StepReplaySafety,
    StateSnapshotRef,
    SideEffectMarker,
    CheckpointedStep,
    WorkingSessionState,
    CheckpointRecord,
    ResumeRequest,
    RecoveryDecision,
)


class TestEnums:
    def test_session_status_values(self):
        assert SessionStatus.ACTIVE.value == "active"
        assert SessionStatus.CANCELLED.value == "cancelled"

    def test_checkpoint_type_values(self):
        assert CheckpointType.STEP_BOUNDARY.value == "step_boundary"
        assert CheckpointType.FAILURE_RECOVERY.value == "failure_recovery"

    def test_resume_disposition_values(self):
        assert ResumeDisposition.RESUME_FROM_CHECKPOINT.value == "resume_from_checkpoint"
        assert ResumeDisposition.ABORT_RESUME.value == "abort_resume"

    def test_step_replay_safety_values(self):
        assert StepReplaySafety.REPLAY_SAFE.value == "replay_safe"
        assert StepReplaySafety.NOT_REPLAYABLE.value == "not_replayable"


class TestStateSnapshotRef:
    def test_valid(self):
        ref = StateSnapshotRef(snapshot_id="snap-001", storage_uri="s3://harness/sessions/snap-001.json")
        assert ref.checksum is None

    def test_with_checksum(self):
        ref = StateSnapshotRef(snapshot_id="snap-002", storage_uri="/tmp/snap-002.json",
                               checksum="sha256-abc123")
        assert ref.checksum == "sha256-abc123"

    def test_empty_snapshot_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            StateSnapshotRef(snapshot_id="  ", storage_uri="s3://bucket/key")
        assert "must not be empty" in str(exc.value)

    def test_empty_storage_uri_raises(self):
        with pytest.raises(ValidationError) as exc:
            StateSnapshotRef(snapshot_id="s1", storage_uri="  ")
        assert "must not be empty" in str(exc.value)


class TestSideEffectMarker:
    def test_not_committed_no_key(self):
        marker = SideEffectMarker(marker_id="m1", step_id="step-3",
                                  operation_name="edit_file", side_effect_committed=False)
        assert marker.idempotency_key is None

    def test_committed_with_key(self):
        marker = SideEffectMarker(marker_id="m2", step_id="step-4",
                                  operation_name="send_email", side_effect_committed=True,
                                  idempotency_key="idem-email-042")
        assert marker.idempotency_key == "idem-email-042"

    def test_committed_no_key_raises(self):
        with pytest.raises(ValidationError) as exc:
            SideEffectMarker(marker_id="m3", step_id="step-5",
                             operation_name="delete_file", side_effect_committed=True,
                             idempotency_key=None)
        assert "committed side effects must have an idempotency_key" in str(exc.value)

    def test_empty_marker_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            SideEffectMarker(marker_id="  ", step_id="s", operation_name="op")
        assert "must not be empty" in str(exc.value)


class TestCheckpointedStep:
    def test_replay_safe(self):
        step = CheckpointedStep(step_id="step-1", step_name="parse_input",
                                replay_safety=StepReplaySafety.REPLAY_SAFE, status="completed")
        assert step.replay_safety == StepReplaySafety.REPLAY_SAFE

    def test_requires_idempotency_with_marker(self):
        step = CheckpointedStep(
            step_id="step-2", step_name="send_notification",
            replay_safety=StepReplaySafety.REQUIRES_IDEMPOTENCY_KEY, status="completed",
            side_effect_markers=[
                SideEffectMarker(marker_id="m1", step_id="step-2",
                                 operation_name="send_email", side_effect_committed=True,
                                 idempotency_key="idem-042"),
            ],
        )
        assert len(step.side_effect_markers) == 1

    def test_requires_idempotency_missing_key_raises(self):
        with pytest.raises(ValidationError) as exc:
            CheckpointedStep(
                step_id="step-3", step_name="bad",
                replay_safety=StepReplaySafety.REQUIRES_IDEMPOTENCY_KEY, status="completed",
                side_effect_markers=[
                    SideEffectMarker(marker_id="m1", step_id="step-3",
                                     operation_name="send", side_effect_committed=False,
                                     idempotency_key=None),
                ],
            )
        assert "REQUIRES_IDEMPOTENCY_KEY must have idempotency_key" in str(exc.value)

    def test_not_replayable(self):
        step = CheckpointedStep(step_id="step-99", step_name="irreversible_op",
                                replay_safety=StepReplaySafety.NOT_REPLAYABLE, status="failed")
        assert step.status == "failed"

    def test_empty_step_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            CheckpointedStep(step_id="  ", step_name="n", replay_safety=StepReplaySafety.REPLAY_SAFE, status="ok")
        assert "must not be empty" in str(exc.value)


class TestWorkingSessionState:
    def test_active_with_current_step(self):
        session = WorkingSessionState(
            session_id="sess-001", run_id="run-001", status=SessionStatus.ACTIVE,
            current_step_id="step-3",
        )
        assert session.current_step_id == "step-3"

    def test_paused_no_current_step(self):
        session = WorkingSessionState(
            session_id="sess-002", run_id="run-002", status=SessionStatus.PAUSED,
        )
        assert session.current_step_id is None

    def test_completed_with_step_ids(self):
        session = WorkingSessionState(
            session_id="sess-003", run_id="run-003", status=SessionStatus.COMPLETED,
            current_step_id="step-final",
            completed_step_ids=["step-1", "step-2", "step-final"],
        )
        assert len(session.completed_step_ids) == 3

    def test_active_missing_current_step_raises(self):
        with pytest.raises(ValidationError) as exc:
            WorkingSessionState(session_id="sess-004", run_id="run-004", status=SessionStatus.ACTIVE)
        assert "ACTIVE session must have a current_step_id" in str(exc.value)

    def test_empty_session_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            WorkingSessionState(session_id="  ", run_id="r", status=SessionStatus.PAUSED)
        assert "must not be empty" in str(exc.value)

    def test_with_context_refs(self):
        session = WorkingSessionState(
            session_id="sess-005", run_id="run-005", status=SessionStatus.ACTIVE,
            current_step_id="step-2",
            active_context_refs=["ctx-001", "ctx-002"],
            tool_result_refs=["tr-001"],
        )
        assert len(session.active_context_refs) == 2


class TestCheckpointRecord:
    def test_valid_step_boundary(self):
        record = CheckpointRecord(
            checkpoint_id="cp-001", session_id="sess-001", run_id="run-001",
            checkpoint_type=CheckpointType.STEP_BOUNDARY, created_at="2026-07-04T12:00:00Z",
            state_snapshot=StateSnapshotRef(snapshot_id="snap-001", storage_uri="s3://bucket/cp-001.json"),
        )
        assert record.checkpoint_type == CheckpointType.STEP_BOUNDARY

    def test_with_checkpointed_steps(self):
        record = CheckpointRecord(
            checkpoint_id="cp-002", session_id="sess-001", run_id="run-001",
            checkpoint_type=CheckpointType.PRE_SIDEEFFECT, created_at="2026-07-04T12:05:00Z",
            state_snapshot=StateSnapshotRef(snapshot_id="snap-002", storage_uri="/tmp/cp-002.json"),
            checkpointed_steps=[
                CheckpointedStep(step_id="step-3", step_name="send_email",
                                 replay_safety=StepReplaySafety.REQUIRES_IDEMPOTENCY_KEY, status="pending"),
            ],
            notes="Checkpoint before external email send",
        )
        assert len(record.checkpointed_steps) == 1
        assert record.notes == "Checkpoint before external email send"

    def test_empty_checkpoint_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            CheckpointRecord(checkpoint_id="  ", session_id="s", run_id="r",
                             checkpoint_type=CheckpointType.MANUAL, created_at="now",
                             state_snapshot=StateSnapshotRef(snapshot_id="s", storage_uri="u"))
        assert "must not be empty" in str(exc.value)

    def test_empty_created_at_raises(self):
        with pytest.raises(ValidationError) as exc:
            CheckpointRecord(checkpoint_id="c", session_id="s", run_id="r",
                             checkpoint_type=CheckpointType.MANUAL, created_at="  ",
                             state_snapshot=StateSnapshotRef(snapshot_id="s", storage_uri="u"))
        assert "must not be empty" in str(exc.value)


class TestResumeRequest:
    def test_valid(self):
        req = ResumeRequest(request_id="rr-001", session_id="sess-001", run_id="run-001",
                            checkpoint_id="cp-001", requested_by="agent-01")
        assert req.reason is None

    def test_with_reason(self):
        req = ResumeRequest(request_id="rr-002", session_id="sess-001", run_id="run-001",
                            checkpoint_id="cp-001", requested_by="human-operator",
                            reason="Infra issue resolved, resume session")
        assert req.reason == "Infra issue resolved, resume session"

    def test_empty_request_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            ResumeRequest(request_id="  ", session_id="s", run_id="r",
                          checkpoint_id="c", requested_by="a")
        assert "must not be empty" in str(exc.value)


class TestRecoveryDecision:
    def test_resume_from_checkpoint(self):
        d = RecoveryDecision(
            decision_id="rd-001", request_id="rr-001",
            disposition=ResumeDisposition.RESUME_FROM_CHECKPOINT,
            target_step_id="step-3",
            rationale="Infra resolved, resuming from last checkpoint",
        )
        assert d.requires_revalidation is False

    def test_abort_resume(self):
        d = RecoveryDecision(
            decision_id="rd-002", request_id="rr-002",
            disposition=ResumeDisposition.ABORT_RESUME,
            rationale="Session expired, cannot resume safely",
        )
        assert d.target_step_id is None

    def test_require_revalidation(self):
        d = RecoveryDecision(
            decision_id="rd-003", request_id="rr-003",
            disposition=ResumeDisposition.REQUIRE_REVALIDATION,
            target_step_id="step-5",
            requires_revalidation=True,
            rationale="Side-effect step needs human review before replay",
        )
        assert d.requires_revalidation is True

    def test_abort_with_target_raises(self):
        with pytest.raises(ValidationError) as exc:
            RecoveryDecision(
                decision_id="rd-004", request_id="rr-004",
                disposition=ResumeDisposition.ABORT_RESUME,
                target_step_id="step-1",
                rationale="should not have target",
            )
        assert "ABORT_RESUME must not include a target_step_id" in str(exc.value)

    def test_resume_without_target_raises(self):
        with pytest.raises(ValidationError) as exc:
            RecoveryDecision(
                decision_id="rd-005", request_id="rr-005",
                disposition=ResumeDisposition.RESUME_FROM_CHECKPOINT,
                rationale="needs target",
            )
        assert "resume_from_checkpoint requires a target_step_id" in str(exc.value)

    def test_restart_without_target_raises(self):
        with pytest.raises(ValidationError) as exc:
            RecoveryDecision(
                decision_id="rd-006", request_id="rr-006",
                disposition=ResumeDisposition.RESTART_STEP,
                rationale="needs target",
            )
        assert "restart_step requires a target_step_id" in str(exc.value)

    def test_empty_decision_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            RecoveryDecision(decision_id="  ", request_id="r",
                             disposition=ResumeDisposition.ABORT_RESUME, rationale="x")
        assert "must not be empty" in str(exc.value)

    def test_empty_rationale_raises(self):
        with pytest.raises(ValidationError) as exc:
            RecoveryDecision(decision_id="d", request_id="r",
                             disposition=ResumeDisposition.ABORT_RESUME, rationale="  ")
        assert "rationale must not be empty" in str(exc.value)


class TestSerialization:
    def test_session_to_json(self):
        session = WorkingSessionState(
            session_id="sess-001", run_id="run-001", status=SessionStatus.ACTIVE,
            current_step_id="step-2", completed_step_ids=["step-1"],
        )
        json_str = session.model_dump_json()
        assert "sess-001" in json_str
        assert "step-2" in json_str

    def test_checkpoint_roundtrip(self):
        record = CheckpointRecord(
            checkpoint_id="cp-001", session_id="s", run_id="r",
            checkpoint_type=CheckpointType.MANUAL, created_at="now",
            state_snapshot=StateSnapshotRef(snapshot_id="s1", storage_uri="u"),
        )
        dumped = record.model_dump()
        assert dumped["checkpoint_type"] == "manual"

    def test_decision_roundtrip(self):
        d = RecoveryDecision(decision_id="d1", request_id="r1",
                             disposition=ResumeDisposition.ABORT_RESUME, rationale="done")
        dumped = d.model_dump()
        assert dumped["disposition"] == "abort_resume"
