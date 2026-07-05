import pytest
from pydantic import ValidationError
from models.memory_context_contract import (
    MemoryScope, MemoryStatus, RetrievalSourceType, ContextTrustLevel,
    MemoryItemRef, RetrievalHitRef, ContextSnapshotBlock,
    MemoryRetentionPolicy, RetrievalSnapshot, ContextStateEnvelope,
)


def make_memory_ref(**overrides) -> MemoryItemRef:
    defaults = dict(
        memory_id="mem-001", scope=MemoryScope.TASK, status=MemoryStatus.ACTIVE,
        source_type=RetrievalSourceType.TOOL_OUTPUT, source_ref="tool://read-001",
        summary="Config file content", trust_level=ContextTrustLevel.TRUSTED,
    )
    defaults.update(overrides)
    return MemoryItemRef(**defaults)


def make_hit(**overrides) -> RetrievalHitRef:
    defaults = dict(hit_id="hit-001", memory_id="mem-001", rank=1)
    defaults.update(overrides)
    return RetrievalHitRef(**defaults)


def make_block(**overrides) -> ContextSnapshotBlock:
    defaults = dict(
        block_id="blk-001", block_type="memory", content_ref="ref://mem-001",
        trust_level=ContextTrustLevel.TRUSTED,
    )
    defaults.update(overrides)
    return ContextSnapshotBlock(**defaults)


def make_policy(**overrides) -> MemoryRetentionPolicy:
    defaults = dict(retention_policy_id="rp-001")
    defaults.update(overrides)
    return MemoryRetentionPolicy(**defaults)


def make_snapshot(**overrides) -> RetrievalSnapshot:
    defaults = dict(snapshot_id="snap-001", run_id="run-001", query="find config files")
    defaults.update(overrides)
    return RetrievalSnapshot(**defaults)


def make_envelope(**overrides) -> ContextStateEnvelope:
    defaults = dict(envelope_id="env-001", session_id="s-001", agent_id="agent-code",
                    snapshot=make_snapshot())
    defaults.update(overrides)
    return ContextStateEnvelope(**defaults)


class TestEnums:
    def test_memory_scope_values(self):
        assert MemoryScope.SESSION.value == "session"
        assert MemoryScope.TASK.value == "task"
        assert MemoryScope.PROJECT.value == "project"
        assert MemoryScope.USER.value == "user"
        assert MemoryScope.SYSTEM.value == "system"
        assert len(MemoryScope) == 5

    def test_memory_status_values(self):
        assert MemoryStatus.ACTIVE.value == "active"
        assert MemoryStatus.STALE.value == "stale"
        assert MemoryStatus.ARCHIVED.value == "archived"
        assert MemoryStatus.DELETED.value == "deleted"
        assert len(MemoryStatus) == 4

    def test_retrieval_source_type_values(self):
        assert RetrievalSourceType.VECTOR_SEARCH.value == "vector_search"
        assert RetrievalSourceType.KEYWORD_SEARCH.value == "keyword_search"
        assert RetrievalSourceType.MANUAL_IMPORT.value == "manual_import"
        assert RetrievalSourceType.TOOL_OUTPUT.value == "tool_output"
        assert RetrievalSourceType.USER_PROVIDED.value == "user_provided"
        assert len(RetrievalSourceType) == 5

    def test_context_trust_level_values(self):
        assert ContextTrustLevel.TRUSTED.value == "trusted"
        assert ContextTrustLevel.INTERNAL_UNVERIFIED.value == "internal_unverified"
        assert ContextTrustLevel.EXTERNAL_UNTRUSTED.value == "external_untrusted"
        assert len(ContextTrustLevel) == 3


class TestMemoryItemRef:
    def test_valid(self):
        m = make_memory_ref()
        assert m.memory_id == "mem-001"

    def test_all_scopes(self):
        for s in MemoryScope:
            m = make_memory_ref(scope=s)
            assert m.scope == s

    def test_all_statuses(self):
        for s in MemoryStatus:
            m = make_memory_ref(status=s)
            assert m.status == s

    def test_all_source_types(self):
        for t in RetrievalSourceType:
            m = make_memory_ref(source_type=t)
            assert m.source_type == t

    def test_all_trust_levels(self):
        for t in ContextTrustLevel:
            m = make_memory_ref(trust_level=t)
            assert m.trust_level == t

    def test_with_confidence(self):
        m = make_memory_ref(confidence=0.85)
        assert m.confidence == 0.85

    def test_confidence_low_boundary(self):
        m = make_memory_ref(confidence=0.0)
        assert m.confidence == 0.0

    def test_confidence_high_boundary(self):
        m = make_memory_ref(confidence=1.0)
        assert m.confidence == 1.0

    def test_confidence_below_zero_raises(self):
        with pytest.raises(ValidationError, match="confidence"):
            make_memory_ref(confidence=-0.01)

    def test_confidence_above_one_raises(self):
        with pytest.raises(ValidationError, match="confidence"):
            make_memory_ref(confidence=1.01)

    def test_blank_memory_id_raises(self):
        with pytest.raises(ValidationError):
            make_memory_ref(memory_id="")

    def test_blank_source_ref_raises(self):
        with pytest.raises(ValidationError):
            make_memory_ref(source_ref="")

    def test_blank_summary_raises(self):
        with pytest.raises(ValidationError):
            make_memory_ref(summary="")


class TestRetrievalHitRef:
    def test_valid(self):
        h = make_hit()
        assert h.hit_id == "hit-001"

    def test_with_score_and_query(self):
        h = make_hit(score=0.92, matched_query="find config")
        assert h.score == 0.92
        assert h.matched_query == "find config"

    def test_rank_one_valid(self):
        h = make_hit(rank=1)
        assert h.rank == 1

    def test_rank_zero_raises(self):
        with pytest.raises(ValidationError, match="rank"):
            make_hit(rank=0)

    def test_rank_negative_raises(self):
        with pytest.raises(ValidationError, match="rank"):
            make_hit(rank=-1)

    def test_score_at_zero(self):
        h = make_hit(score=0.0)
        assert h.score == 0.0

    def test_score_at_one(self):
        h = make_hit(score=1.0)
        assert h.score == 1.0

    def test_score_below_zero_raises(self):
        with pytest.raises(ValidationError, match="score"):
            make_hit(score=-0.1)

    def test_score_above_one_raises(self):
        with pytest.raises(ValidationError, match="score"):
            make_hit(score=1.1)

    def test_blank_hit_id_raises(self):
        with pytest.raises(ValidationError):
            make_hit(hit_id="")

    def test_blank_memory_id_raises(self):
        with pytest.raises(ValidationError):
            make_hit(memory_id="")

    def test_hits_order_preserved(self):
        hits = [make_hit(hit_id="h-1", rank=3), make_hit(hit_id="h-2", rank=1), make_hit(hit_id="h-3", rank=2)]
        assert [h.hit_id for h in hits] == ["h-1", "h-2", "h-3"]


class TestContextSnapshotBlock:
    def test_valid(self):
        b = make_block()
        assert b.block_id == "blk-001"

    def test_with_origin_ref(self):
        b = make_block(origin_ref="task://t-001")
        assert b.origin_ref == "task://t-001"

    def test_all_trust_levels(self):
        for t in ContextTrustLevel:
            b = make_block(trust_level=t)
            assert b.trust_level == t

    def test_blank_block_id_raises(self):
        with pytest.raises(ValidationError):
            make_block(block_id="")

    def test_blank_block_type_raises(self):
        with pytest.raises(ValidationError):
            make_block(block_type="")

    def test_blank_content_ref_raises(self):
        with pytest.raises(ValidationError):
            make_block(content_ref="")


class TestMemoryRetentionPolicy:
    def test_valid(self):
        p = make_policy()
        assert p.retention_policy_id == "rp-001"

    def test_with_keep_until(self):
        p = make_policy(keep_until="2026-12-31T23:59:59Z")
        assert p.keep_until == "2026-12-31T23:59:59Z"

    def test_with_expire_days(self):
        p = make_policy(expire_after_days=90)
        assert p.expire_after_days == 90

    def test_expire_zero_valid(self):
        p = make_policy(expire_after_days=0)
        assert p.expire_after_days == 0

    def test_expire_negative_raises(self):
        with pytest.raises(ValidationError, match="expire"):
            make_policy(expire_after_days=-1)

    def test_promote_true(self):
        p = make_policy(promote_to_project_memory=True)
        assert p.promote_to_project_memory is True

    def test_summarize_false(self):
        p = make_policy(summarize_before_store=False)
        assert p.summarize_before_store is False

    def test_blank_policy_id_raises(self):
        with pytest.raises(ValidationError):
            make_policy(retention_policy_id="")


class TestRetrievalSnapshot:
    def test_valid(self):
        s = make_snapshot()
        assert s.snapshot_id == "snap-001"

    def test_with_hits_and_memory_items(self):
        s = make_snapshot(hits=[make_hit()], memory_items=[make_memory_ref()])
        assert len(s.hits) == 1
        assert len(s.memory_items) == 1

    def test_with_task_and_trace(self):
        s = make_snapshot(task_id="t-001", trace_id="trace-001")
        assert s.task_id == "t-001"
        assert s.trace_id == "trace-001"

    def test_blank_snapshot_id_raises(self):
        with pytest.raises(ValidationError):
            make_snapshot(snapshot_id="")

    def test_blank_run_id_raises(self):
        with pytest.raises(ValidationError):
            make_snapshot(run_id="")

    def test_blank_query_raises(self):
        with pytest.raises(ValidationError):
            make_snapshot(query="")

    def test_duplicate_hit_ids_raises(self):
        with pytest.raises(ValidationError, match="hit_ids"):
            make_snapshot(hits=[make_hit(hit_id="hit-001"), make_hit(hit_id="hit-001", memory_id="mem-002")])

    def test_unique_hit_ids_valid(self):
        s = make_snapshot(hits=[make_hit(hit_id="hit-001"), make_hit(hit_id="hit-002", memory_id="mem-002")])
        assert len(s.hits) == 2

    def test_duplicate_memory_ids_raises(self):
        with pytest.raises(ValidationError, match="memory_ids"):
            make_snapshot(memory_items=[
                make_memory_ref(memory_id="mem-001"),
                make_memory_ref(memory_id="mem-001", summary="duplicate"),
            ])

    def test_unique_memory_ids_valid(self):
        s = make_snapshot(memory_items=[
            make_memory_ref(memory_id="mem-001"),
            make_memory_ref(memory_id="mem-002"),
        ])
        assert len(s.memory_items) == 2

    def test_hits_order_preserved(self):
        s = make_snapshot(hits=[make_hit(hit_id="h-3", rank=3), make_hit(hit_id="h-1", rank=1)])
        assert [h.hit_id for h in s.hits] == ["h-3", "h-1"]

    def test_memory_items_order_preserved(self):
        s = make_snapshot(memory_items=[
            make_memory_ref(memory_id="mem-b"),
            make_memory_ref(memory_id="mem-a"),
        ])
        assert [m.memory_id for m in s.memory_items] == ["mem-b", "mem-a"]


class TestContextStateEnvelope:
    def test_valid(self):
        e = make_envelope()
        assert e.envelope_id == "env-001"

    def test_with_context_blocks_and_policy(self):
        e = make_envelope(
            context_blocks=[make_block()],
            retention_policy=make_policy(),
        )
        assert len(e.context_blocks) == 1
        assert e.retention_policy.retention_policy_id == "rp-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="")

    def test_blank_session_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(session_id="")

    def test_blank_agent_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(agent_id="")

    def test_duplicate_block_ids_raises(self):
        with pytest.raises(ValidationError, match="block_ids"):
            make_envelope(context_blocks=[
                make_block(block_id="blk-001"),
                make_block(block_id="blk-001", block_type="retrieval"),
            ])

    def test_unique_block_ids_valid(self):
        e = make_envelope(context_blocks=[
            make_block(block_id="blk-001"),
            make_block(block_id="blk-002"),
        ])
        assert len(e.context_blocks) == 2

    def test_context_blocks_order_preserved(self):
        e = make_envelope(context_blocks=[
            make_block(block_id="blk-b"),
            make_block(block_id="blk-a"),
        ])
        assert [b.block_id for b in e.context_blocks] == ["blk-b", "blk-a"]

    def test_no_context_blocks_valid(self):
        e = make_envelope(context_blocks=[])
        assert e.context_blocks == []

    def test_no_retention_policy_valid(self):
        e = make_envelope(retention_policy=None)
        assert e.retention_policy is None


class TestSerialization:
    def test_memory_ref_to_dict_and_back(self):
        m = make_memory_ref()
        data = m.model_dump()
        assert data["memory_id"] == "mem-001"
        assert data["scope"] == "task"
        restored = MemoryItemRef(**data)
        assert restored.memory_id == m.memory_id

    def test_envelope_to_dict_and_back(self):
        e = make_envelope(context_blocks=[make_block()])
        data = e.model_dump()
        assert data["envelope_id"] == "env-001"
        restored = ContextStateEnvelope(**data)
        assert len(restored.context_blocks) == 1
        assert restored.snapshot.run_id == "run-001"


class TestIntegration:
    def test_session_memory_snapshot(self):
        mem = MemoryItemRef(
            memory_id="mem-session-1", scope=MemoryScope.SESSION, status=MemoryStatus.ACTIVE,
            source_type=RetrievalSourceType.TOOL_OUTPUT, source_ref="tool://list-dir",
            summary="Project directory structure", trust_level=ContextTrustLevel.TRUSTED,
        )
        snap = RetrievalSnapshot(
            snapshot_id="snap-session", run_id="run-001", session_id="s-001",
            query="get session context",
            memory_items=[mem],
        )
        env = ContextStateEnvelope(
            envelope_id="env-session", session_id="s-001", agent_id="agent-code",
            snapshot=snap,
        )
        assert env.snapshot.memory_items[0].scope == MemoryScope.SESSION
        assert env.snapshot.memory_items[0].status == MemoryStatus.ACTIVE
        assert env.snapshot.memory_items[0].confidence is None

    def test_task_specific_retrieval_snapshot(self):
        mem = MemoryItemRef(
            memory_id="mem-task-1", scope=MemoryScope.TASK, status=MemoryStatus.ACTIVE,
            source_type=RetrievalSourceType.VECTOR_SEARCH, source_ref="vector://query-abc",
            summary="Relevant code fragment from vector search", trust_level=ContextTrustLevel.TRUSTED,
            confidence=0.94,
        )
        hit = RetrievalHitRef(
            hit_id="hit-task-1", memory_id="mem-task-1", rank=1, score=0.94,
            matched_query="find function validate_input",
        )
        snap = RetrievalSnapshot(
            snapshot_id="snap-task", run_id="run-001", task_id="t-001",
            query="find function validate_input",
            hits=[hit], memory_items=[mem],
        )
        env = ContextStateEnvelope(
            envelope_id="env-task", session_id="s-001", agent_id="agent-code",
            snapshot=snap,
            context_blocks=[ContextSnapshotBlock(
                block_id="blk-task-1", block_type="retrieval",
                content_ref="ref://mem-task-1", trust_level=ContextTrustLevel.TRUSTED,
                origin_ref="task://t-001",
            )],
        )
        assert env.snapshot.query == "find function validate_input"
        assert env.snapshot.hits[0].rank == 1
        assert env.snapshot.hits[0].score == 0.94
        assert env.context_blocks[0].origin_ref == "task://t-001"
        assert env.snapshot.memory_items[0].confidence == 0.94

    def test_project_memory_with_promotion_policy(self):
        mem = MemoryItemRef(
            memory_id="mem-project-1", scope=MemoryScope.PROJECT, status=MemoryStatus.ACTIVE,
            source_type=RetrievalSourceType.MANUAL_IMPORT, source_ref="doc://onboarding.md",
            summary="Project onboarding guide for new agents", trust_level=ContextTrustLevel.TRUSTED,
            confidence=1.0,
        )
        hit = RetrievalHitRef(hit_id="hit-1", memory_id="mem-project-1", rank=1, score=0.88)
        snap = RetrievalSnapshot(
            snapshot_id="snap-project", run_id="run-001", task_id="t-001",
            query="onboarding instructions", hits=[hit], memory_items=[mem],
        )
        policy = MemoryRetentionPolicy(
            retention_policy_id="rp-project", keep_until="2027-01-01T00:00:00Z",
            expire_after_days=180, promote_to_project_memory=True, summarize_before_store=True,
        )
        env = ContextStateEnvelope(
            envelope_id="env-project", session_id="s-001", agent_id="agent-code",
            snapshot=snap, retention_policy=policy,
        )
        assert env.snapshot.memory_items[0].scope == MemoryScope.PROJECT
        assert env.retention_policy.promote_to_project_memory is True
        assert env.retention_policy.expire_after_days == 180
        assert env.retention_policy.keep_until == "2027-01-01T00:00:00Z"

    def test_external_untrusted_retrieval_block(self):
        mem = MemoryItemRef(
            memory_id="mem-ext-1", scope=MemoryScope.SESSION, status=MemoryStatus.ACTIVE,
            source_type=RetrievalSourceType.USER_PROVIDED, source_ref="user://message-42",
            summary="User-provided API documentation snippet",
            trust_level=ContextTrustLevel.EXTERNAL_UNTRUSTED, confidence=0.35,
        )
        hit = RetrievalHitRef(hit_id="hit-ext-1", memory_id="mem-ext-1", rank=1, score=0.35)
        snap = RetrievalSnapshot(
            snapshot_id="snap-ext", run_id="run-001", task_id="t-001",
            query="api docs", hits=[hit], memory_items=[mem],
        )
        block = ContextSnapshotBlock(
            block_id="blk-ext-1", block_type="user_provided",
            content_ref="ref://mem-ext-1",
            trust_level=ContextTrustLevel.EXTERNAL_UNTRUSTED,
            origin_ref="user://message-42",
        )
        env = ContextStateEnvelope(
            envelope_id="env-ext", session_id="s-001", agent_id="agent-code",
            snapshot=snap, context_blocks=[block],
        )
        assert env.snapshot.memory_items[0].trust_level == ContextTrustLevel.EXTERNAL_UNTRUSTED
        assert env.snapshot.memory_items[0].confidence == 0.35
        assert env.context_blocks[0].trust_level == ContextTrustLevel.EXTERNAL_UNTRUSTED

    def test_stale_memory_item_retained_for_audit(self):
        mem = MemoryItemRef(
            memory_id="mem-stale-1", scope=MemoryScope.TASK, status=MemoryStatus.STALE,
            source_type=RetrievalSourceType.TOOL_OUTPUT, source_ref="tool://old-query",
            summary="Deprecated config format (superseded by v2)",
            trust_level=ContextTrustLevel.INTERNAL_UNVERIFIED, confidence=0.2,
        )
        active = MemoryItemRef(
            memory_id="mem-active-1", scope=MemoryScope.TASK, status=MemoryStatus.ACTIVE,
            source_type=RetrievalSourceType.TOOL_OUTPUT, source_ref="tool://new-query",
            summary="Current config format v2",
            trust_level=ContextTrustLevel.TRUSTED, confidence=0.95,
        )
        snap = RetrievalSnapshot(
            snapshot_id="snap-stale", run_id="run-001", task_id="t-001",
            query="config format", memory_items=[mem, active],
        )
        env = ContextStateEnvelope(
            envelope_id="env-stale", session_id="s-001", agent_id="agent-code",
            snapshot=snap,
        )
        stale = env.snapshot.memory_items[0]
        assert stale.status == MemoryStatus.STALE
        assert stale.confidence == 0.2
        assert stale.trust_level == ContextTrustLevel.INTERNAL_UNVERIFIED
        assert env.snapshot.memory_items[1].status == MemoryStatus.ACTIVE

    def test_stale_memory_not_surfaced_as_active(self):
        mem = MemoryItemRef(
            memory_id="mem-s", scope=MemoryScope.TASK, status=MemoryStatus.STALE,
            source_type=RetrievalSourceType.TOOL_OUTPUT, source_ref="tool://x",
            summary="Stale entry", trust_level=ContextTrustLevel.INTERNAL_UNVERIFIED,
        )
        assert mem.status == MemoryStatus.STALE
        assert mem.status != MemoryStatus.ACTIVE

    def test_deleted_memory_identifiable(self):
        mem = MemoryItemRef(
            memory_id="mem-del", scope=MemoryScope.SESSION, status=MemoryStatus.DELETED,
            source_type=RetrievalSourceType.MANUAL_IMPORT, source_ref="doc://removed",
            summary="Previously imported doc (deleted)", trust_level=ContextTrustLevel.INTERNAL_UNVERIFIED,
        )
        assert mem.status == MemoryStatus.DELETED
