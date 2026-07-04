from typing import List, Optional, Set
from pydantic import BaseModel
from dataclasses import dataclass

from .candidates import (
    CandidateFile, CandidateFailure, CandidateDoc,
    gather_file_candidates, gather_failure_candidates, gather_doc_candidates,
    is_excluded,
)
from .scoring import (
    score_file, score_failure, score_doc,
    score_file_import_proximity, score_file_same_directory,
)


class SelectionDecision(BaseModel):
    item_id: str
    item_type: str
    score: int
    reasons: List[str]


class SelectionResult(BaseModel):
    selected_file_ids: List[str]
    selected_failure_ids: List[str]
    selected_doc_ids: List[str]
    dropped_item_ids: List[str]
    decisions: List[SelectionDecision]


CAP_MAX_FILES = 5
CAP_MAX_FAILURES = 3
CAP_MAX_DOCS = 2
CAP_MAX_TOTAL = 10


class ContextSelectionPolicy:
    def __init__(
        self,
        max_files: int = CAP_MAX_FILES,
        max_failures: int = CAP_MAX_FAILURES,
        max_docs: int = CAP_MAX_DOCS,
        max_total: int = CAP_MAX_TOTAL,
    ):
        self.max_files = max_files
        self.max_failures = max_failures
        self.max_docs = max_docs
        self.max_total = max_total

    def select(
        self,
        *,
        relevant_files: List[str],
        failing_tests: List[str],
        error_logs: List[str],
        task_title: str = "",
        task_keywords: List[str],
        repo_top_paths: List[str],
        imported_by: Optional[Set[str]] = None,
        selected_dir: Optional[str] = None,
    ) -> SelectionResult:
        keyword_set = set(k.lower() for k in task_keywords if k.strip())
        relevant_set = set(relevant_files)

        file_candidates = gather_file_candidates(relevant_files, repo_top_paths)
        failure_candidates = gather_failure_candidates(failing_tests, error_logs)
        doc_candidates = gather_doc_candidates(task_keywords)

        scored_files = []
        for fc in file_candidates:
            s = score_file(fc, relevant_set, task_title, keyword_set)
            if imported_by:
                s += score_file_import_proximity(fc, imported_by)
            if selected_dir:
                s += score_file_same_directory(fc, selected_dir)
            scored_files.append((s, fc))

        scored_failures = []
        for fc in failure_candidates:
            s = score_failure(fc, relevant_set, keyword_set)
            scored_failures.append((s, fc))

        scored_docs = []
        for dc in doc_candidates:
            s = score_doc(dc, keyword_set)
            scored_docs.append((s, dc))

        scored_files.sort(key=lambda x: -x[0])
        scored_failures.sort(key=lambda x: -x[0])
        scored_docs.sort(key=lambda x: -x[0])

        decisions: List[SelectionDecision] = []
        selected_file_ids: List[str] = []
        selected_failure_ids: List[str] = []
        selected_doc_ids: List[str] = []
        dropped_item_ids: List[str] = []
        total_selected = 0

        for score, fc in scored_files:
            item_id = f"file:{fc.path}"
            if (
                len(selected_file_ids) < self.max_files
                and total_selected < self.max_total
            ):
                selected_file_ids.append(item_id)
                total_selected += 1
                decisions.append(SelectionDecision(
                    item_id=item_id, item_type="file", score=score,
                    reasons=[fc.reason],
                ))
            else:
                dropped_item_ids.append(item_id)
                decisions.append(SelectionDecision(
                    item_id=item_id, item_type="file", score=score,
                    reasons=[fc.reason, "dropped by cap"],
                ))

        for score, fc in scored_failures:
            item_id = f"failure:{fc.test_name}"
            if (
                len(selected_failure_ids) < self.max_failures
                and total_selected < self.max_total
            ):
                selected_failure_ids.append(item_id)
                total_selected += 1
                decisions.append(SelectionDecision(
                    item_id=item_id, item_type="failure", score=score,
                    reasons=[fc.reason],
                ))
            else:
                dropped_item_ids.append(item_id)
                decisions.append(SelectionDecision(
                    item_id=item_id, item_type="failure", score=score,
                    reasons=[fc.reason, "dropped by cap"],
                ))

        for score, dc in scored_docs:
            item_id = f"doc:{dc.title}"
            if (
                len(selected_doc_ids) < self.max_docs
                and total_selected < self.max_total
            ):
                selected_doc_ids.append(item_id)
                total_selected += 1
                decisions.append(SelectionDecision(
                    item_id=item_id, item_type="doc", score=score,
                    reasons=[dc.reason],
                ))
            else:
                dropped_item_ids.append(item_id)
                decisions.append(SelectionDecision(
                    item_id=item_id, item_type="doc", score=score,
                    reasons=[dc.reason, "dropped by cap"],
                ))

        return SelectionResult(
            selected_file_ids=selected_file_ids,
            selected_failure_ids=selected_failure_ids,
            selected_doc_ids=selected_doc_ids,
            dropped_item_ids=dropped_item_ids,
            decisions=decisions,
        )
