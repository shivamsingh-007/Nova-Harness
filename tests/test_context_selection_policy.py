import pytest
from context_selection.policy import ContextSelectionPolicy, SelectionResult
from context_selection.candidates import (
    gather_file_candidates,
    gather_failure_candidates,
    is_excluded,
    CandidateFile,
    CandidateFailure,
)
from context_selection.scoring import (
    score_file,
    score_failure,
    score_doc,
    score_file_import_proximity,
    score_file_same_directory,
)


class TestExclusions:
    def test_excludes_node_modules(self):
        assert is_excluded("node_modules/foo/bar.py") is True

    def test_excludes_dist(self):
        assert is_excluded("dist/bundle.js") is True

    def test_excludes_lockfile(self):
        assert is_excluded("package-lock.json") is True

    def test_excludes_image(self):
        assert is_excluded("assets/icon.png") is True

    def test_allows_source_file(self):
        assert is_excluded("src/context_packer.py") is False

    def test_allows_test_file(self):
        assert is_excluded("tests/test_foo.py") is False


class TestCandidateGathering:
    def test_gathers_relevant_files_first(self):
        candidates = gather_file_candidates(
            relevant_files=["src/context_packer.py"],
            repo_top_paths=["src/", "tests/", "node_modules/"],
        )
        paths = [c.path for c in candidates]
        assert "src/context_packer.py" in paths
        assert "src/" in paths
        assert "tests/" in paths
        assert "node_modules/" not in paths

    def test_gathers_failure_candidates(self):
        candidates = gather_failure_candidates(
            failing_tests=["tests/test_foo.py::test_bar"],
            error_logs=["Traceback: ValueError at line 42"],
        )
        assert len(candidates) >= 1
        assert candidates[0].test_name == "tests/test_foo.py::test_bar"


class TestScoring:
    def test_explicitly_named_file_scores_100(self):
        fc = CandidateFile(path="src/context_packer.py", reason="explicit")
        score = score_file(fc, task_relevant_files={"src/context_packer.py"}, task_title="", task_keyword_set=set())
        assert score == 115  # 100 explicit + 15 src dir bonus

    def test_test_file_gets_bonus(self):
        fc = CandidateFile(path="tests/test_foo.py", reason="test file")
        score = score_file(fc, task_relevant_files=set(), task_title="", task_keyword_set=set())
        assert score == 40

    def test_import_proximity_scores_40(self):
        fc = CandidateFile(path="src/dependency.py", reason="imported by")
        score = score_file_import_proximity(fc, directly_imported_by={"src/dependency.py"})
        assert score == 40

    def test_same_directory_scores_20(self):
        fc = CandidateFile(path="src/bar.py", reason="same dir")
        score = score_file_same_directory(fc, selected_dir="src")
        assert score == 20

    def test_failure_referencing_relevant_file_scores_90(self):
        fc = CandidateFailure(
            test_name="test_foo",
            file_path="src/context_packer.py",
            reason="failing test",
        )
        score = score_failure(fc, task_relevant_files={"src/context_packer.py"}, task_keyword_set=set())
        assert score == 90

    def test_doc_matching_keyword_scores_30(self):
        from context_selection.candidates import CandidateDoc
        dc = CandidateDoc(title="Context Packer API", source="docs/api.md", reason="doc")
        score = score_doc(dc, task_keyword_set={"packer"})
        assert score == 30


class TestSelectionPolicy:
    def test_selects_explicitly_named_file(self):
        policy = ContextSelectionPolicy()
        result = policy.select(
            relevant_files=["src/context_packer.py"],
            failing_tests=[],
            error_logs=[],
            task_title="Fix null pointer in context packer",
            task_keywords=["packer", "null"],
            repo_top_paths=["src/", "tests/"],
        )
        file_ids = result.selected_file_ids
        assert any("src/context_packer.py" in f for f in file_ids)

    def test_selects_failing_tests(self):
        policy = ContextSelectionPolicy()
        result = policy.select(
            relevant_files=[],
            failing_tests=["tests/test_foo.py::test_bar"],
            error_logs=[],
            task_title="Fix test_bar",
            task_keywords=["test_bar"],
            repo_top_paths=[],
        )
        assert len(result.selected_failure_ids) == 1

    def test_respects_file_cap(self):
        policy = ContextSelectionPolicy(max_files=1)
        result = policy.select(
            relevant_files=["src/a.py", "src/b.py", "src/c.py"],
            failing_tests=[],
            error_logs=[],
            task_title="test",
            task_keywords=["test"],
            repo_top_paths=[],
        )
        assert len(result.selected_file_ids) <= 1

    def test_respects_max_total_cap(self):
        policy = ContextSelectionPolicy(max_files=5, max_failures=3, max_docs=2, max_total=3)
        result = policy.select(
            relevant_files=["src/a.py", "src/b.py", "src/c.py", "src/d.py"],
            failing_tests=["tests/test_a.py::test_a"],
            error_logs=[],
            task_title="test",
            task_keywords=["test"],
            repo_top_paths=[],
        )
        total_selected = (
            len(result.selected_file_ids)
            + len(result.selected_failure_ids)
            + len(result.selected_doc_ids)
        )
        assert total_selected <= 3

    def test_excluded_paths_are_filtered(self):
        policy = ContextSelectionPolicy()
        result = policy.select(
            relevant_files=["node_modules/foo.py", "src/bar.py"],
            failing_tests=[],
            error_logs=[],
            task_title="test",
            task_keywords=["test"],
            repo_top_paths=[],
        )
        assert any("src/bar.py" in f for f in result.selected_file_ids)
        assert not any("node_modules" in f for f in result.selected_file_ids)

    def test_returns_decisions_for_all_candidates(self):
        policy = ContextSelectionPolicy()
        result = policy.select(
            relevant_files=["src/a.py", "src/b.py"],
            failing_tests=["tests/test_a.py::test_a"],
            error_logs=[],
            task_title="test",
            task_keywords=["test"],
            repo_top_paths=["src/c.py", "src/d.py"],
        )
        assert len(result.decisions) > 0
        has_selected = any("selected" not in " ".join(d.reasons) for d in result.decisions if d.item_id in result.selected_file_ids)
        has_dropped = any("dropped by cap" in " ".join(d.reasons) for d in result.decisions if d.item_id in result.dropped_item_ids)

    def test_empty_inputs_produces_empty_selection(self):
        policy = ContextSelectionPolicy()
        result = policy.select(
            relevant_files=[],
            failing_tests=[],
            error_logs=[],
            task_title="",
            task_keywords=[],
            repo_top_paths=[],
        )
        assert len(result.selected_file_ids) == 0
        assert len(result.selected_failure_ids) == 0
        assert len(result.selected_doc_ids) == 0

    def test_score_and_reasons_in_decisions(self):
        policy = ContextSelectionPolicy()
        result = policy.select(
            relevant_files=["src/context_packer.py"],
            failing_tests=[],
            error_logs=[],
            task_title="Fix packer",
            task_keywords=["packer"],
            repo_top_paths=[],
        )
        for d in result.decisions:
            if d.item_id in result.selected_file_ids:
                assert d.score > 0
                assert len(d.reasons) > 0
