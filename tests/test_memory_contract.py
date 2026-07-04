import pytest
from pydantic import ValidationError
from models.memory_contract import (
    MemoryType,
    MemoryScopeType,
    SensitivityLevel,
    RetentionClass,
    MemoryLifecycleStatus,
    MemoryPurpose,
    ExecutionContext,
    MemoryScope,
    RetentionPolicy,
    MemoryRecord,
    MemoryAccessDecision,
)


def make_session_record(**overrides) -> MemoryRecord:
    kwargs = dict(
        memory_id="mem-001", memory_type=MemoryType.SESSION,
        purpose=MemoryPurpose.TASK_CONTINUITY,
        scope=MemoryScope(scope_type=MemoryScopeType.SESSION, scope_id="sess-001"),
        sensitivity=SensitivityLevel.LOW,
        lifecycle_status=MemoryLifecycleStatus.ACTIVE,
        content_ref="memory-store://sess-001/step-3.json",
        retention_policy=RetentionPolicy(
            retention_class=RetentionClass.EPHEMERAL, ttl_seconds=3600),
    )
    kwargs.update(overrides)
    return MemoryRecord(**kwargs)


class TestEnums:
    def test_memory_type_values(self):
        assert MemoryType.SESSION.value == "session"
        assert MemoryType.LONG_TERM.value == "long_term"

    def test_scope_type_values(self):
        assert MemoryScopeType.USER.value == "user"
        assert MemoryScopeType.TENANT.value == "tenant"

    def test_sensitivity_values(self):
        assert SensitivityLevel.LOW.value == "low"
        assert SensitivityLevel.RESTRICTED.value == "restricted"

    def test_retention_class_values(self):
        assert RetentionClass.EPHEMERAL.value == "ephemeral"
        assert RetentionClass.LEGAL_HOLD.value == "legal_hold"

    def test_lifecycle_status_values(self):
        assert MemoryLifecycleStatus.ACTIVE.value == "active"
        assert MemoryLifecycleStatus.QUARANTINED.value == "quarantined"

    def test_purpose_values(self):
        assert MemoryPurpose.USER_PREFERENCE.value == "user_preference"
        assert MemoryPurpose.SAFETY_SIGNAL.value == "safety_signal"


class TestExecutionContext:
    def test_empty(self):
        ctx = ExecutionContext()
        assert ctx.run_id is None

    def test_with_fields(self):
        ctx = ExecutionContext(run_id="run-001", session_id="sess-001",
                               user_id="user-shiva", actor_role="developer")
        assert ctx.actor_role == "developer"


class TestMemoryScope:
    def test_valid(self):
        scope = MemoryScope(scope_type=MemoryScopeType.PROJECT,
                            scope_id="proj-harness")
        assert scope.scope_type == MemoryScopeType.PROJECT

    def test_empty_scope_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            MemoryScope(scope_type=MemoryScopeType.RUN, scope_id="  ")
        assert "must not be empty" in str(exc.value)


class TestRetentionPolicy:
    def test_ephemeral(self):
        policy = RetentionPolicy(retention_class=RetentionClass.EPHEMERAL,
                                 ttl_seconds=3600)
        assert policy.allow_user_delete is True

    def test_legal_hold(self):
        policy = RetentionPolicy(retention_class=RetentionClass.LEGAL_HOLD,
                                 allow_user_delete=False)
        assert policy.allow_user_delete is False

    def test_negative_ttl_raises(self):
        with pytest.raises(ValidationError) as exc:
            RetentionPolicy(retention_class=RetentionClass.EPHEMERAL,
                            ttl_seconds=-1)
        assert "ttl_seconds must be positive if provided" in str(exc.value)

    def test_zero_ttl_raises(self):
        with pytest.raises(ValidationError) as exc:
            RetentionPolicy(retention_class=RetentionClass.SHORT_LIVED,
                            ttl_seconds=0)
        assert "ttl_seconds must be positive if provided" in str(exc.value)


class TestMemoryRecord:
    def test_session_ephemeral(self):
        record = make_session_record()
        assert record.memory_type == MemoryType.SESSION

    def test_long_term_standard(self):
        record = MemoryRecord(
            memory_id="mem-010", memory_type=MemoryType.LONG_TERM,
            purpose=MemoryPurpose.USER_PREFERENCE,
            scope=MemoryScope(scope_type=MemoryScopeType.USER,
                              scope_id="user-shiva"),
            sensitivity=SensitivityLevel.LOW,
            lifecycle_status=MemoryLifecycleStatus.ACTIVE,
            content_ref="memory-store://users/user-shiva/prefs.json",
            retention_policy=RetentionPolicy(
                retention_class=RetentionClass.STANDARD, ttl_seconds=864000),
        )
        assert record.purpose == MemoryPurpose.USER_PREFERENCE

    def test_project_scoped(self):
        record = MemoryRecord(
            memory_id="mem-020", memory_type=MemoryType.LONG_TERM,
            purpose=MemoryPurpose.PROJECT_CONTEXT,
            scope=MemoryScope(scope_type=MemoryScopeType.PROJECT,
                              scope_id="proj-harness"),
            sensitivity=SensitivityLevel.MODERATE,
            lifecycle_status=MemoryLifecycleStatus.ACTIVE,
            content_ref="memory-store://projects/proj-harness/context.json",
            provenance_ref="audit://ev-context-save-001",
            retention_policy=RetentionPolicy(
                retention_class=RetentionClass.STANDARD, ttl_seconds=2592000),
        )
        assert record.provenance_ref == "audit://ev-context-save-001"

    def test_session_with_extended_retention_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_session_record(
                retention_policy=RetentionPolicy(
                    retention_class=RetentionClass.EXTENDED),
            )
        assert "SESSION or WORKING memory must not use EXTENDED or LEGAL_HOLD retention" in str(exc.value)

    def test_session_with_legal_hold_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_session_record(
                retention_policy=RetentionPolicy(
                    retention_class=RetentionClass.LEGAL_HOLD),
            )
        assert "SESSION or WORKING memory must not use EXTENDED or LEGAL_HOLD retention" in str(exc.value)

    def test_working_with_extended_raises(self):
        with pytest.raises(ValidationError) as exc:
            MemoryRecord(
                memory_id="mem-w", memory_type=MemoryType.WORKING,
                purpose=MemoryPurpose.TASK_CONTINUITY,
                scope=MemoryScope(scope_type=MemoryScopeType.RUN,
                                  scope_id="run-001"),
                sensitivity=SensitivityLevel.LOW,
                lifecycle_status=MemoryLifecycleStatus.ACTIVE,
                content_ref="mem://run-001/work",
                retention_policy=RetentionPolicy(
                    retention_class=RetentionClass.EXTENDED),
            )
        assert "SESSION or WORKING memory must not use EXTENDED or LEGAL_HOLD retention" in str(exc.value)

    def test_long_term_ephemeral_raises(self):
        with pytest.raises(ValidationError) as exc:
            MemoryRecord(
                memory_id="mem-lt", memory_type=MemoryType.LONG_TERM,
                purpose=MemoryPurpose.USER_PREFERENCE,
                scope=MemoryScope(scope_type=MemoryScopeType.USER,
                                  scope_id="user-a"),
                sensitivity=SensitivityLevel.LOW,
                lifecycle_status=MemoryLifecycleStatus.ACTIVE,
                content_ref="mem://lt/prefs",
                retention_policy=RetentionPolicy(
                    retention_class=RetentionClass.EPHEMERAL),
            )
        assert "LONG_TERM memory must not use EPHEMERAL or SHORT_LIVED retention" in str(exc.value)

    def test_long_term_short_lived_raises(self):
        with pytest.raises(ValidationError) as exc:
            MemoryRecord(
                memory_id="mem-lt2", memory_type=MemoryType.LONG_TERM,
                purpose=MemoryPurpose.PROJECT_CONTEXT,
                scope=MemoryScope(scope_type=MemoryScopeType.PROJECT,
                                  scope_id="proj-a"),
                sensitivity=SensitivityLevel.MODERATE,
                lifecycle_status=MemoryLifecycleStatus.ACTIVE,
                content_ref="mem://lt/ctx",
                retention_policy=RetentionPolicy(
                    retention_class=RetentionClass.SHORT_LIVED),
            )
        assert "LONG_TERM memory must not use EPHEMERAL or SHORT_LIVED retention" in str(exc.value)

    def test_suppressed_created(self):
        record = make_session_record(
            lifecycle_status=MemoryLifecycleStatus.SUPPRESSED,
        )
        assert record.lifecycle_status == MemoryLifecycleStatus.SUPPRESSED

    def test_quarantined_created(self):
        record = make_session_record(
            lifecycle_status=MemoryLifecycleStatus.QUARANTINED,
        )
        assert record.lifecycle_status == MemoryLifecycleStatus.QUARANTINED

    def test_empty_memory_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_session_record(memory_id="  ")
        assert "must not be empty" in str(exc.value)

    def test_empty_content_ref_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_session_record(content_ref="  ")
        assert "must not be empty" in str(exc.value)

    def test_all_lifecycle_states_accepted(self):
        for status in MemoryLifecycleStatus:
            record = make_session_record(lifecycle_status=status)
            assert record.lifecycle_status == status

    def test_all_memory_types_accepted(self):
        for mem_type in MemoryType:
            if mem_type == MemoryType.LONG_TERM:
                record = MemoryRecord(
                    memory_id=f"mem-{mem_type.value}",
                    memory_type=mem_type,
                    purpose=MemoryPurpose.PROJECT_CONTEXT,
                    scope=MemoryScope(scope_type=MemoryScopeType.PROJECT,
                                      scope_id="proj-a"),
                    sensitivity=SensitivityLevel.LOW,
                    lifecycle_status=MemoryLifecycleStatus.ACTIVE,
                    content_ref="mem://lt/ctx",
                    retention_policy=RetentionPolicy(
                        retention_class=RetentionClass.STANDARD),
                )
            else:
                record = make_session_record(
                    memory_id=f"mem-{mem_type.value}",
                    memory_type=mem_type,
                )
            assert record.memory_type == mem_type


class TestMemoryAccessDecision:
    def test_allowed(self):
        decision = MemoryAccessDecision(
            decision_id="mad-001", memory_id="mem-001", allowed=True,
            reason="Execution context scope matches memory scope",
            execution_context=ExecutionContext(session_id="sess-001"),
        )
        assert decision.allowed is True

    def test_denied(self):
        decision = MemoryAccessDecision(
            decision_id="mad-002", memory_id="mem-002", allowed=False,
            reason="Memory is SUPPRESSED, not retrievable",
            execution_context=ExecutionContext(),
        )
        assert decision.allowed is False

    def test_empty_decision_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            MemoryAccessDecision(decision_id="  ", memory_id="m",
                                 allowed=True, reason="ok",
                                 execution_context=ExecutionContext())
        assert "must not be empty" in str(exc.value)

    def test_empty_memory_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            MemoryAccessDecision(decision_id="d", memory_id="  ",
                                 allowed=True, reason="ok",
                                 execution_context=ExecutionContext())
        assert "must not be empty" in str(exc.value)

    def test_empty_reason_raises(self):
        with pytest.raises(ValidationError) as exc:
            MemoryAccessDecision(decision_id="d", memory_id="m",
                                 allowed=True, reason="  ",
                                 execution_context=ExecutionContext())
        assert "must not be empty" in str(exc.value)


class TestSerialization:
    def test_memory_to_json(self):
        record = make_session_record()
        json_str = record.model_dump_json()
        assert "mem-001" in json_str
        assert "session" in json_str

    def test_decision_roundtrip(self):
        decision = MemoryAccessDecision(
            decision_id="mad-001", memory_id="mem-001", allowed=True,
            reason="Scope match",
            execution_context=ExecutionContext(run_id="run-001"),
        )
        dumped = decision.model_dump()
        assert dumped["allowed"] is True
        assert dumped["execution_context"]["run_id"] == "run-001"

    def test_record_all_fields(self):
        record = MemoryRecord(
            memory_id="mem-full", memory_type=MemoryType.LONG_TERM,
            purpose=MemoryPurpose.SAFETY_SIGNAL,
            scope=MemoryScope(scope_type=MemoryScopeType.SYSTEM,
                              scope_id="system-global"),
            sensitivity=SensitivityLevel.RESTRICTED,
            lifecycle_status=MemoryLifecycleStatus.QUARANTINED,
            content_ref="memory-store://system/safety-signal-001.json",
            provenance_ref="audit://ev-safety-001",
            retention_policy=RetentionPolicy(
                retention_class=RetentionClass.LEGAL_HOLD,
                allow_user_delete=False),
        )
        dumped = record.model_dump()
        assert dumped["sensitivity"] == "restricted"
        assert dumped["provenance_ref"] == "audit://ev-safety-001"
