from typing import List, Optional, Set
from dataclasses import dataclass, field


EXCLUDED_DIRS: Set[str] = {
    "node_modules", "__pycache__", ".git", ".venv", "venv",
    "dist", "build", ".next", ".nox", ".tox", ".eggs",
    "site-packages", ".pytest_cache", "coverage", ".coverage",
}

EXCLUDED_FILES: Set[str] = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", "Gemfile.lock",
}

EXCLUDED_EXTENSIONS: Set[str] = {
    ".pyc", ".pyo", ".so", ".dll", ".dylib",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".ttf", ".woff", ".woff2", ".eot",
    ".zip", ".tar", ".gz", ".bz2",
}


def is_excluded(path: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    if any(p in EXCLUDED_DIRS for p in parts):
        return True
    if any(p in EXCLUDED_FILES for p in parts):
        return True
    if any(path.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
        return True
    return False


@dataclass
class CandidateFile:
    path: str
    reason: str  # why this file is a candidate


@dataclass
class CandidateFailure:
    test_name: str
    file_path: Optional[str]
    reason: str


@dataclass
class CandidateDoc:
    title: str
    source: str
    reason: str


def gather_file_candidates(
    relevant_files: List[str],
    repo_top_paths: List[str],
) -> List[CandidateFile]:
    seen: Set[str] = set()
    candidates: List[CandidateFile] = []

    for path in relevant_files:
        if path in seen:
            continue
        if is_excluded(path):
            continue
        seen.add(path)
        candidates.append(CandidateFile(
            path=path,
            reason=f"explicitly referenced in task inputs",
        ))

    for path in repo_top_paths:
        if path in seen:
            continue
        if is_excluded(path):
            continue
        seen.add(path)
        candidates.append(CandidateFile(
            path=path,
            reason=f"top-level repo entry",
        ))

    return candidates


def gather_failure_candidates(
    failing_tests: List[str],
    error_logs: List[str],
) -> List[CandidateFailure]:
    candidates: List[CandidateFailure] = []

    for test_ref in failing_tests:
        parts = test_ref.split("::")
        file_path = parts[0] if len(parts) > 1 else None
        candidates.append(CandidateFailure(
            test_name=test_ref,
            file_path=file_path,
            reason=f"failing test explicitly listed in task inputs",
        ))

    seen_errors: Set[str] = set()
    for log in error_logs:
        if log in seen_errors:
            continue
        seen_errors.add(log)
        if "Traceback" in log or "Error" in log or "Exception" in log:
            candidates.append(CandidateFailure(
                test_name="runtime error",
                file_path=None,
                reason=f"error log with traceback or exception",
            ))

    return candidates


def gather_doc_candidates(
    task_keywords: List[str],
) -> List[CandidateDoc]:
    candidates: List[CandidateDoc] = []
    seen: Set[str] = set()

    for kw in task_keywords:
        kw_lower = kw.lower().strip()
        if not kw_lower or kw_lower in seen:
            continue
        seen.add(kw_lower)

    return candidates
