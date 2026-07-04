from typing import List, Set
from .candidates import CandidateFile, CandidateFailure, CandidateDoc


def score_file(
    candidate: CandidateFile,
    task_relevant_files: Set[str],
    task_title: str,
    task_keyword_set: Set[str],
) -> int:
    score = 0
    path_lower = candidate.path.lower()

    if candidate.path in task_relevant_files:
        score += 100

    if any(part in path_lower for part in ("test",)):
        score += 40

    if any(part in path_lower for part in ("src", "lib", "app")):
        score += 15

    for kw in task_keyword_set:
        if kw in path_lower:
            score += 10
            break

    for kw in task_keyword_set:
        if kw in task_title.lower():
            score += 5
            break

    return score


def score_failure(
    candidate: CandidateFailure,
    task_relevant_files: Set[str],
    task_keyword_set: Set[str],
) -> int:
    score = 0

    if candidate.file_path and candidate.file_path in task_relevant_files:
        score += 90

    if candidate.file_path:
        path_lower = candidate.file_path.lower()
        for kw in task_keyword_set:
            if kw in path_lower:
                score += 20
                break

    return score


def score_doc(
    candidate: CandidateDoc,
    task_keyword_set: Set[str],
) -> int:
    score = 0
    title_lower = candidate.title.lower()

    for kw in task_keyword_set:
        if kw in title_lower:
            score += 30
            break

    source_lower = candidate.source.lower()
    for kw in task_keyword_set:
        if kw in source_lower:
            score += 15
            break

    return score


def score_file_import_proximity(
    candidate: CandidateFile,
    directly_imported_by: Set[str],
) -> int:
    if candidate.path in directly_imported_by:
        return 40
    return 0


def score_file_same_directory(
    candidate: CandidateFile,
    selected_dir: str,
) -> int:
    candidate_dir = "/".join(candidate.path.replace("\\", "/").split("/")[:-1])
    if candidate_dir == selected_dir:
        return 20
    return 0
