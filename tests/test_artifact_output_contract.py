import pytest
from pydantic import ValidationError
from models.artifact_output_contract import (
    ArtifactType, ArtifactStatus, ArtifactOriginType, ArtifactVisibility,
    ArtifactRef, ArtifactProvenance, ArtifactLifecycle,
    GeneratedOutputRecord, ArtifactEnvelope,
)


def make_artifact(**overrides) -> ArtifactRef:
    defaults = dict(artifact_id="art-001", artifact_type=ArtifactType.MARKDOWN,
                    name="report.md", uri="file://outputs/report.md")
    defaults.update(overrides)
    return ArtifactRef(**defaults)


def make_provenance(**overrides) -> ArtifactProvenance:
    defaults = dict(provenance_id="prov-001", origin_type=ArtifactOriginType.MODEL_GENERATED)
    defaults.update(overrides)
    return ArtifactProvenance(**defaults)


def make_lifecycle(**overrides) -> ArtifactLifecycle:
    defaults = dict(lifecycle_id="lc-001")
    defaults.update(overrides)
    return ArtifactLifecycle(**defaults)


def make_output(**overrides) -> GeneratedOutputRecord:
    defaults = dict(output_id="out-001", artifact=make_artifact(),
                    provenance=make_provenance(), lifecycle=make_lifecycle())
    defaults.update(overrides)
    return GeneratedOutputRecord(**defaults)


def make_envelope(**overrides) -> ArtifactEnvelope:
    defaults = dict(envelope_id="env-001", run_id="run-001")
    defaults.update(overrides)
    return ArtifactEnvelope(**defaults)


class TestEnums:
    def test_artifact_type_values(self):
        assert ArtifactType.FILE.value == "file"
        assert ArtifactType.IMAGE.value == "image"
        assert ArtifactType.JSON.value == "json"
        assert ArtifactType.CSV.value == "csv"
        assert ArtifactType.MARKDOWN.value == "markdown"
        assert ArtifactType.HTML.value == "html"
        assert ArtifactType.PDF.value == "pdf"
        assert ArtifactType.CODE.value == "code"
        assert ArtifactType.LOG.value == "log"
        assert ArtifactType.ARCHIVE.value == "archive"
        assert ArtifactType.OTHER.value == "other"
        assert len(ArtifactType) == 11

    def test_artifact_status_values(self):
        assert ArtifactStatus.CREATED.value == "created"
        assert ArtifactStatus.READY.value == "ready"
        assert ArtifactStatus.MODIFIED.value == "modified"
        assert ArtifactStatus.STALE.value == "stale"
        assert ArtifactStatus.ARCHIVED.value == "archived"
        assert ArtifactStatus.DELETED.value == "deleted"
        assert len(ArtifactStatus) == 6

    def test_artifact_origin_type_values(self):
        assert ArtifactOriginType.USER_INPUT.value == "user_input"
        assert ArtifactOriginType.MODEL_GENERATED.value == "model_generated"
        assert ArtifactOriginType.TOOL_GENERATED.value == "tool_generated"
        assert ArtifactOriginType.DERIVED.value == "derived"
        assert ArtifactOriginType.IMPORTED.value == "imported"
        assert len(ArtifactOriginType) == 5

    def test_artifact_visibility_values(self):
        assert ArtifactVisibility.PRIVATE.value == "private"
        assert ArtifactVisibility.TEAM.value == "team"
        assert ArtifactVisibility.SHARED.value == "shared"
        assert ArtifactVisibility.PUBLIC.value == "public"
        assert len(ArtifactVisibility) == 4


class TestArtifactRef:
    def test_valid(self):
        a = make_artifact()
        assert a.artifact_id == "art-001"

    def test_all_types(self):
        for t in ArtifactType:
            a = make_artifact(artifact_type=t)
            assert a.artifact_type == t

    def test_all_statuses(self):
        for s in ArtifactStatus:
            a = make_artifact(status=s)
            assert a.status == s

    def test_all_visibilities(self):
        for v in ArtifactVisibility:
            a = make_artifact(visibility=v)
            assert a.visibility == v

    def test_with_mime_type(self):
        a = make_artifact(mime_type="text/markdown")
        assert a.mime_type == "text/markdown"

    def test_default_status(self):
        a = make_artifact()
        assert a.status == ArtifactStatus.CREATED

    def test_default_visibility(self):
        a = make_artifact()
        assert a.visibility == ArtifactVisibility.PRIVATE

    def test_blank_artifact_id_raises(self):
        with pytest.raises(ValidationError):
            make_artifact(artifact_id="")

    def test_blank_name_raises(self):
        with pytest.raises(ValidationError):
            make_artifact(name="")

    def test_blank_uri_raises(self):
        with pytest.raises(ValidationError):
            make_artifact(uri="")


class TestArtifactProvenance:
    def test_valid(self):
        p = make_provenance()
        assert p.provenance_id == "prov-001"

    def test_all_origin_types(self):
        for t in ArtifactOriginType:
            p = make_provenance(origin_type=t)
            assert p.origin_type == t

    def test_with_source_ref(self):
        p = make_provenance(source_ref="user://upload-42")
        assert p.source_ref == "user://upload-42"

    def test_with_creation_links(self):
        p = make_provenance(created_by_run_id="run-001", created_by_task_id="t-001",
                            created_by_tool_call_id="tc-001", created_by_model_call_id="mc-001")
        assert p.created_by_run_id == "run-001"
        assert p.created_by_task_id == "t-001"
        assert p.created_by_tool_call_id == "tc-001"
        assert p.created_by_model_call_id == "mc-001"

    def test_with_content_hash(self):
        p = make_provenance(content_hash="sha256:abc123")
        assert p.content_hash == "sha256:abc123"

    def test_with_parent_ids(self):
        p = make_provenance(parent_artifact_ids=["art-001", "art-002"])
        assert p.parent_artifact_ids == ["art-001", "art-002"]

    def test_blank_provenance_id_raises(self):
        with pytest.raises(ValidationError):
            make_provenance(provenance_id="")

    def test_empty_content_hash_raises(self):
        with pytest.raises(ValidationError, match="content_hash"):
            make_provenance(content_hash="")

    def test_blank_content_hash_raises(self):
        with pytest.raises(ValidationError, match="content_hash"):
            make_provenance(content_hash="   ")

    def test_blank_parent_id_raises(self):
        with pytest.raises(ValidationError, match="parent_artifact_ids"):
            make_provenance(parent_artifact_ids=["art-001", ""])

    def test_parent_ids_order_preserved(self):
        p = make_provenance(parent_artifact_ids=["z-art", "a-art", "m-art"])
        assert p.parent_artifact_ids == ["z-art", "a-art", "m-art"]


class TestArtifactLifecycle:
    def test_valid(self):
        lc = make_lifecycle()
        assert lc.lifecycle_id == "lc-001"

    def test_with_dates(self):
        lc = make_lifecycle(retain_until="2027-01-01T00:00:00Z",
                            archived_at="2026-07-04T12:00:00Z",
                            deleted_at="2026-07-05T12:00:00Z")
        assert lc.retain_until == "2027-01-01T00:00:00Z"
        assert lc.archived_at == "2026-07-04T12:00:00Z"
        assert lc.deleted_at == "2026-07-05T12:00:00Z"

    def test_retained_default_true(self):
        lc = make_lifecycle()
        assert lc.retained is True

    def test_retained_false(self):
        lc = make_lifecycle(retained=False)
        assert lc.retained is False

    def test_blank_lifecycle_id_raises(self):
        with pytest.raises(ValidationError):
            make_lifecycle(lifecycle_id="")


class TestGeneratedOutputRecord:
    def test_valid(self):
        o = make_output()
        assert o.output_id == "out-001"

    def test_with_summary(self):
        o = make_output(summary="Generated markdown report")
        assert o.summary == "Generated markdown report"

    def test_is_exportable_default_true(self):
        o = make_output()
        assert o.is_exportable is True

    def test_is_exportable_false(self):
        o = make_output(is_exportable=False)
        assert o.is_exportable is False

    def test_is_reproducible_default_false(self):
        o = make_output()
        assert o.is_reproducible is False

    def test_is_reproducible_true(self):
        o = make_output(is_reproducible=True)
        assert o.is_reproducible is True

    def test_blank_output_id_raises(self):
        with pytest.raises(ValidationError):
            make_output(output_id="")

    def test_archived_status_requires_archived_at(self):
        with pytest.raises(ValidationError, match="ARCHIVED"):
            make_output(
                artifact=make_artifact(status=ArtifactStatus.ARCHIVED),
                lifecycle=make_lifecycle(archived_at=None),
            )

    def test_archived_status_with_archived_at_valid(self):
        o = make_output(
            artifact=make_artifact(status=ArtifactStatus.ARCHIVED),
            lifecycle=make_lifecycle(archived_at="2026-07-04T12:00:00Z"),
        )
        assert o.artifact.status == ArtifactStatus.ARCHIVED
        assert o.lifecycle.archived_at == "2026-07-04T12:00:00Z"

    def test_deleted_status_requires_deleted_at(self):
        with pytest.raises(ValidationError, match="DELETED"):
            make_output(
                artifact=make_artifact(status=ArtifactStatus.DELETED),
                lifecycle=make_lifecycle(deleted_at=None),
            )

    def test_deleted_status_with_deleted_at_valid(self):
        o = make_output(
            artifact=make_artifact(status=ArtifactStatus.DELETED),
            lifecycle=make_lifecycle(deleted_at="2026-07-05T12:00:00Z"),
        )
        assert o.artifact.status == ArtifactStatus.DELETED
        assert o.lifecycle.deleted_at == "2026-07-05T12:00:00Z"

    def test_status_created_no_dates_required(self):
        o = make_output(artifact=make_artifact(status=ArtifactStatus.CREATED))
        assert o.artifact.status == ArtifactStatus.CREATED

    def test_status_ready_no_dates_required(self):
        o = make_output(artifact=make_artifact(status=ArtifactStatus.READY))
        assert o.artifact.status == ArtifactStatus.READY

    def test_status_modified_no_dates_required(self):
        o = make_output(artifact=make_artifact(status=ArtifactStatus.MODIFIED))
        assert o.artifact.status == ArtifactStatus.MODIFIED

    def test_status_stale_no_dates_required(self):
        o = make_output(artifact=make_artifact(status=ArtifactStatus.STALE))
        assert o.artifact.status == ArtifactStatus.STALE


class TestArtifactEnvelope:
    def test_valid_empty(self):
        e = make_envelope()
        assert e.outputs == []

    def test_with_outputs(self):
        e = make_envelope(outputs=[make_output()])
        assert len(e.outputs) == 1

    def test_with_task_and_trace(self):
        e = make_envelope(task_id="t-001", trace_id="trace-001")
        assert e.task_id == "t-001"
        assert e.trace_id == "trace-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="")

    def test_blank_run_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(run_id="")

    def test_duplicate_output_ids_raises(self):
        with pytest.raises(ValidationError, match="output_ids"):
            make_envelope(outputs=[
                make_output(output_id="out-001"),
                make_output(output_id="out-001", artifact=make_artifact(artifact_id="art-999")),
            ])

    def test_unique_output_ids_valid(self):
        e = make_envelope(outputs=[
            make_output(output_id="out-001"),
            make_output(output_id="out-002"),
        ])
        assert len(e.outputs) == 2

    def test_outputs_order_preserved(self):
        e = make_envelope(outputs=[
            make_output(output_id="out-b"),
            make_output(output_id="out-a"),
        ])
        assert [o.output_id for o in e.outputs] == ["out-b", "out-a"]


class TestSerialization:
    def test_output_to_dict_and_back(self):
        o = make_output()
        data = o.model_dump()
        assert data["output_id"] == "out-001"
        assert data["artifact"]["name"] == "report.md"
        restored = GeneratedOutputRecord(**data)
        assert restored.output_id == o.output_id

    def test_envelope_to_dict_and_back(self):
        e = make_envelope(outputs=[make_output()])
        data = e.model_dump()
        assert data["envelope_id"] == "env-001"
        restored = ArtifactEnvelope(**data)
        assert len(restored.outputs) == 1


class TestIntegration:
    def test_model_generated_markdown_report(self):
        artifact = ArtifactRef(
            artifact_id="art-report", artifact_type=ArtifactType.MARKDOWN,
            name="analysis.md", uri="file://outputs/analysis.md",
            mime_type="text/markdown", status=ArtifactStatus.READY,
            visibility=ArtifactVisibility.TEAM,
        )
        provenance = ArtifactProvenance(
            provenance_id="prov-report", origin_type=ArtifactOriginType.MODEL_GENERATED,
            created_by_run_id="run-001", created_by_task_id="t-001",
            created_by_model_call_id="mc-001",
            content_hash="sha256:def456",
        )
        lifecycle = ArtifactLifecycle(
            lifecycle_id="lc-report", retained=True, retain_until="2027-01-01T00:00:00Z",
        )
        output = GeneratedOutputRecord(
            output_id="out-report", artifact=artifact, provenance=provenance,
            lifecycle=lifecycle, summary="Model-generated analysis report",
        )
        env = ArtifactEnvelope(envelope_id="env-report", run_id="run-001", outputs=[output])
        assert env.outputs[0].artifact.artifact_type == ArtifactType.MARKDOWN
        assert env.outputs[0].provenance.created_by_model_call_id == "mc-001"
        assert env.outputs[0].provenance.content_hash == "sha256:def456"
        assert env.outputs[0].artifact.visibility == ArtifactVisibility.TEAM

    def test_tool_generated_csv_file(self):
        artifact = ArtifactRef(
            artifact_id="art-csv", artifact_type=ArtifactType.CSV,
            name="metrics.csv", uri="file://outputs/metrics.csv",
            mime_type="text/csv", status=ArtifactStatus.READY,
        )
        provenance = ArtifactProvenance(
            provenance_id="prov-csv", origin_type=ArtifactOriginType.TOOL_GENERATED,
            created_by_run_id="run-001", created_by_task_id="t-001",
            created_by_tool_call_id="tc-001", content_hash="sha256:789ghi",
        )
        output = GeneratedOutputRecord(
            output_id="out-csv", artifact=artifact, provenance=provenance,
            lifecycle=make_lifecycle(lifecycle_id="lc-csv"),
            summary="Exported performance metrics",
            is_exportable=True, is_reproducible=True,
        )
        env = ArtifactEnvelope(envelope_id="env-csv", run_id="run-001", outputs=[output])
        assert env.outputs[0].artifact.artifact_type == ArtifactType.CSV
        assert env.outputs[0].provenance.created_by_tool_call_id == "tc-001"
        assert env.outputs[0].is_reproducible is True
        assert env.outputs[0].is_exportable is True

    def test_derived_html_artifact_with_parent_lineage(self):
        artifact = ArtifactRef(
            artifact_id="art-html", artifact_type=ArtifactType.HTML,
            name="dashboard.html", uri="file://outputs/dashboard.html",
            mime_type="text/html", status=ArtifactStatus.READY,
            visibility=ArtifactVisibility.PUBLIC,
        )
        provenance = ArtifactProvenance(
            provenance_id="prov-html", origin_type=ArtifactOriginType.DERIVED,
            created_by_run_id="run-001", created_by_task_id="t-001",
            created_by_model_call_id="mc-002",
            parent_artifact_ids=["art-report", "art-csv"],
            content_hash="sha256:html999",
        )
        output = GeneratedOutputRecord(
            output_id="out-html", artifact=artifact, provenance=provenance,
            lifecycle=make_lifecycle(lifecycle_id="lc-html"),
            summary="Derived HTML dashboard from report and CSV",
            is_exportable=True,
        )
        env = ArtifactEnvelope(envelope_id="env-html", run_id="run-001", outputs=[output])
        assert env.outputs[0].provenance.origin_type == ArtifactOriginType.DERIVED
        assert env.outputs[0].provenance.parent_artifact_ids == ["art-report", "art-csv"]
        assert env.outputs[0].artifact.visibility == ArtifactVisibility.PUBLIC

    def test_private_archived_artifact_with_retention(self):
        artifact = ArtifactRef(
            artifact_id="art-old", artifact_type=ArtifactType.LOG,
            name="debug.log", uri="file://logs/debug.log",
            mime_type="text/plain", status=ArtifactStatus.ARCHIVED,
            visibility=ArtifactVisibility.PRIVATE,
        )
        provenance = ArtifactProvenance(
            provenance_id="prov-old", origin_type=ArtifactOriginType.TOOL_GENERATED,
            created_by_run_id="run-001",
        )
        lifecycle = ArtifactLifecycle(
            lifecycle_id="lc-old", retained=False,
            retain_until="2026-07-01T00:00:00Z",
            archived_at="2026-07-02T00:00:00Z",
        )
        output = GeneratedOutputRecord(
            output_id="out-old", artifact=artifact, provenance=provenance,
            lifecycle=lifecycle, summary="Archived debug log",
            is_exportable=False,
        )
        env = ArtifactEnvelope(envelope_id="env-old", run_id="run-001", outputs=[output])
        assert env.outputs[0].artifact.status == ArtifactStatus.ARCHIVED
        assert env.outputs[0].lifecycle.archived_at == "2026-07-02T00:00:00Z"
        assert env.outputs[0].lifecycle.retained is False
        assert env.outputs[0].is_exportable is False

    def test_public_exportable_artifact_with_provenance_links(self):
        artifact = ArtifactRef(
            artifact_id="art-public", artifact_type=ArtifactType.JSON,
            name="public_data.json", uri="s3://bucket/public_data.json",
            mime_type="application/json", status=ArtifactStatus.READY,
            visibility=ArtifactVisibility.PUBLIC,
        )
        provenance = ArtifactProvenance(
            provenance_id="prov-public", origin_type=ArtifactOriginType.DERIVED,
            source_ref="pipeline://nightly-build",
            created_by_run_id="run-002", created_by_task_id="t-002",
            created_by_tool_call_id="tc-002",
            parent_artifact_ids=["art-source"],
            content_hash="sha256:pub123",
        )
        lifecycle = ArtifactLifecycle(
            lifecycle_id="lc-public", retained=True, retain_until="2027-06-01T00:00:00Z",
        )
        output = GeneratedOutputRecord(
            output_id="out-public", artifact=artifact, provenance=provenance,
            lifecycle=lifecycle, summary="Public dataset for external sharing",
            is_exportable=True, is_reproducible=True,
        )
        env = ArtifactEnvelope(envelope_id="env-public", run_id="run-002", outputs=[output])
        assert env.outputs[0].artifact.visibility == ArtifactVisibility.PUBLIC
        assert env.outputs[0].provenance.source_ref == "pipeline://nightly-build"
        assert env.outputs[0].is_exportable is True
        assert env.outputs[0].is_reproducible is True
