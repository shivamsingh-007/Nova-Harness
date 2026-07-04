from typing import Set

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
