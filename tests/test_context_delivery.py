import pytest
from pydantic import ValidationError
from models.context_delivery import (
    ContextDeliveryBundle,
    DeliveryItem,
    RepoSnapshot,
    VerificationHints,
    ContentType,
)


def make_valid_bundle(**overrides) -> ContextDeliveryBundle:
    defaults = dict(
        task_id="ctx-001",
        task_brief="Fix null pointer in context packer when file list is empty.",
        repo_snapshot=RepoSnapshot(
            repo_root="/repo",
            top_level_paths=["src/", "tests/", "README.md"],
            primary_language="python",
            build_system="pytest",
            test_command="pytest tests/",
            lint_command="ruff check .",
        ),
        selected_files=[
            DeliveryItem(
                item_id="f1",
                content_type=ContentType.FILE_SNIPPET,
                source_path="src/context_packer.py",
                title="context_packer.py",
                reason="Contains the null pointer bug in the scan_files method.",
                content="def scan_files(paths):\n    if not paths:\n        return None",
                priority=1,
            ),
        ],
        selected_failures=[
            DeliveryItem(
                item_id="err1",
                content_type=ContentType.TEST_FAILURE,
                source_path="tests/test_context_packer.py",
                title="test_empty_file_list failure",
                reason="This test exposes the null pointer bug.",
                content="FAILED test_empty_file_list - TypeError: 'NoneType' object is not iterable",
                priority=1,
            ),
        ],
        selected_docs=[
            DeliveryItem(
                item_id="d1",
                content_type=ContentType.DOC_SNIPPET,
                title="Context Packer API",
                reason="Documents the expected return type of scan_files.",
                content="scan_files(paths: list[str]) -> list[FileEntry]",
                priority=2,
            ),
        ],
        verification_hints=VerificationHints(
            recommended_commands=["pytest tests/test_context_packer.py::test_empty_file_list -v"],
            success_signals=["test passes with exit code 0", "no TypeError raised"],
        ),
    )
    defaults.update(overrides)
    return ContextDeliveryBundle(**defaults)


class TestValidBundles:
    def test_valid_bug_fix_bundle(self):
        bundle = make_valid_bundle()
        assert bundle.task_id == "ctx-001"
        assert len(bundle.selected_files) == 1
        assert len(bundle.selected_failures) == 1
        assert len(bundle.selected_docs) == 1

    def test_valid_feature_bundle(self):
        bundle = make_valid_bundle(
            task_id="ctx-002",
            task_brief="Add file watcher that triggers context repack on file change.",
            repo_snapshot=RepoSnapshot(
                repo_root="/repo",
                top_level_paths=["src/", "tests/", "docs/"],
                primary_language="python",
                test_command="pytest tests/",
            ),
            selected_files=[
                DeliveryItem(
                    item_id="f1", content_type=ContentType.FILE_SNIPPET,
                    source_path="src/context_packer.py", title="context_packer.py",
                    reason="Existing context packer that needs watcher integration.",
                    content="class ContextPacker:\n    def pack(self): ...",
                    priority=1,
                ),
                DeliveryItem(
                    item_id="f2", content_type=ContentType.FILE_SNIPPET,
                    source_path="src/watcher.py", title="watcher.py",
                    reason="New file to create with file watcher logic.",
                    content="# TODO: implement file watcher",
                    priority=1,
                ),
            ],
            selected_failures=[],
            selected_docs=[
                DeliveryItem(
                    item_id="d1", content_type=ContentType.DOC_SNIPPET,
                    title="watchdog library docs",
                    reason="Reference for filesystem event API.",
                    content="Observer().schedule(EventHandler(), path, recursive=True)",
                    priority=3,
                ),
            ],
        )
        assert bundle.task_id == "ctx-002"
        assert len(bundle.selected_files) == 2
        assert len(bundle.selected_docs) == 1
        assert len(bundle.selected_failures) == 0

    def test_empty_bundle_fields_default(self):
        bundle = make_valid_bundle(
            selected_files=[], selected_failures=[], selected_docs=[]
        )
        assert bundle.selected_files == []
        assert bundle.selected_failures == []
        assert bundle.selected_docs == []

    def test_verification_hints_defaults(self):
        bundle = make_valid_bundle(
            verification_hints=VerificationHints()
        )
        assert bundle.verification_hints.recommended_commands == []
        assert bundle.verification_hints.success_signals == []


class TestFieldValidators:
    def test_empty_task_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_bundle(task_id="")
        assert "must not be empty" in str(exc.value)

    def test_empty_task_brief_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_bundle(task_brief="   ")
        assert "must not be empty" in str(exc.value)

    def test_empty_delivery_item_title_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_bundle(
                selected_files=[
                    DeliveryItem(
                        item_id="bad", content_type=ContentType.FILE_SNIPPET,
                        title="", reason="test", content="test",
                    )
                ]
            )
        assert "must not be empty" in str(exc.value)

    def test_empty_delivery_item_reason_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_bundle(
                selected_files=[
                    DeliveryItem(
                        item_id="bad", content_type=ContentType.FILE_SNIPPET,
                        title="test", reason="", content="test",
                    )
                ]
            )
        assert "must not be empty" in str(exc.value)

    def test_empty_delivery_item_content_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_bundle(
                selected_files=[
                    DeliveryItem(
                        item_id="bad", content_type=ContentType.FILE_SNIPPET,
                        title="test", reason="test", content="",
                    )
                ]
            )
        assert "must not be empty" in str(exc.value)

    def test_priority_too_low_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_bundle(
                selected_files=[
                    DeliveryItem(
                        item_id="bad", content_type=ContentType.FILE_SNIPPET,
                        title="test", reason="test", content="test",
                        priority=0,
                    )
                ]
            )
        assert "priority must be between 1 and 5" in str(exc.value)

    def test_priority_too_high_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_bundle(
                selected_files=[
                    DeliveryItem(
                        item_id="bad", content_type=ContentType.FILE_SNIPPET,
                        title="test", reason="test", content="test",
                        priority=6,
                    )
                ]
            )
        assert "priority must be between 1 and 5" in str(exc.value)

    def test_empty_repo_root_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_bundle(
                repo_snapshot=RepoSnapshot(repo_root="")
            )
        assert "repo_root must not be empty" in str(exc.value)


class TestContentType:
    def test_all_content_types_present(self):
        expected = ["file_snippet", "error_log", "test_failure", "doc_snippet", "repo_map", "command_hint"]
        actual = [e.value for e in ContentType]
        assert sorted(actual) == sorted(expected)


class TestDefaultsAndSerialization:
    def test_default_priority(self):
        item = DeliveryItem(
            item_id="t1", content_type=ContentType.COMMAND_HINT,
            title="Run tests", reason="Verify fix.", content="pytest",
        )
        assert item.priority == 1

    def test_serialize_to_dict(self):
        bundle = make_valid_bundle()
        data = bundle.model_dump()
        assert data["task_id"] == "ctx-001"
        assert data["repo_snapshot"]["primary_language"] == "python"
        assert len(data["selected_files"]) == 1
        assert data["selected_files"][0]["content_type"] == "file_snippet"
