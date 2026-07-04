from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class TaskType(str, Enum):
    BUG_FIX = "bug_fix"
    FEATURE = "feature"
    REFACTOR = "refactor"
    TEST_ONLY = "test_only"


class ToolName(str, Enum):
    READ_FILE = "read_file"
    SEARCH_CODE = "search_code"
    EDIT_FILE = "edit_file"
    RUN_TESTS = "run_tests"
    RUN_LINT = "run_lint"
    RUN_TYPECHECK = "run_typecheck"
    GIT_DIFF = "git_diff"


class ApprovalTrigger(str, Enum):
    DEPENDENCY_CHANGE = "dependency_change"
    DELETE_FILE = "delete_file"
    TOUCH_BLOCKED_PATH = "touch_blocked_path"
    LARGE_DIFF = "large_diff"


class VerificationKind(str, Enum):
    TEST = "test"
    LINT = "lint"
    TYPECHECK = "typecheck"
    DIFF_REVIEW = "diff_review"


class TaskScope(BaseModel):
    repo_path: str
    allowed_paths: List[str] = Field(default_factory=list)
    blocked_paths: List[str] = Field(default_factory=list)

    @field_validator("repo_path")
    @classmethod
    def validate_repo_path(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("repo_path must not be empty")
        return value

    @field_validator("allowed_paths", "blocked_paths")
    @classmethod
    def validate_subpaths(cls, value: List[str]) -> List[str]:
        cleaned: List[str] = []
        seen: set = set()
        for item in value:
            item = item.strip()
            if not item:
                raise ValueError("path entries must not be empty")
            if item.startswith("/") or ".." in item:
                raise ValueError(f"invalid relative path: {item}")
            if item in seen:
                continue
            seen.add(item)
            cleaned.append(item)
        return cleaned

    @model_validator(mode="after")
    def validate_no_path_overlap(self):
        overlap = set(self.allowed_paths) & set(self.blocked_paths)
        if overlap:
            raise ValueError(f"allowed_paths and blocked_paths overlap: {sorted(overlap)}")
        return self


class TaskInputs(BaseModel):
    user_request: str
    relevant_files: List[str] = Field(default_factory=list)
    failing_tests: List[str] = Field(default_factory=list)
    error_logs: List[str] = Field(default_factory=list)


class TaskConstraints(BaseModel):
    max_files_changed: int = 5
    max_retries: int = 2
    allow_network: bool = False
    allow_dependency_changes: bool = False

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, value: int) -> int:
        if value < 0 or value > 5:
            raise ValueError("max_retries must be between 0 and 5")
        return value

    @field_validator("max_files_changed")
    @classmethod
    def validate_max_files_changed(cls, value: int) -> int:
        if value < 1 or value > 50:
            raise ValueError("max_files_changed must be between 1 and 50")
        return value


class SuccessCriterion(BaseModel):
    kind: VerificationKind
    target: str


class OutputRequirements(BaseModel):
    include_summary: bool = True
    include_changed_files: bool = True
    include_verification_receipts: bool = True


class TaskContract(BaseModel):
    task_id: str
    title: str
    task_type: TaskType
    goal: str
    scope: TaskScope
    inputs: TaskInputs
    constraints: TaskConstraints
    tools_allowed: List[ToolName]
    success_criteria: List[SuccessCriterion]
    approval_gates: List[ApprovalTrigger] = Field(default_factory=list)
    output_requirements: OutputRequirements = Field(default_factory=OutputRequirements)

    @field_validator("title", "goal")
    @classmethod
    def validate_non_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("tools_allowed")
    @classmethod
    def tools_must_not_be_empty(cls, value):
        if not value:
            raise ValueError("tools_allowed must not be empty")
        return value

    @field_validator("success_criteria")
    @classmethod
    def success_criteria_must_not_be_empty(cls, value):
        if not value:
            raise ValueError("success_criteria must not be empty")
        return value

    @model_validator(mode="after")
    def validate_tool_criterion_alignment(self):
        tool_set = set(self.tools_allowed)
        if ToolName.RUN_TESTS in tool_set:
            has_test_criterion = any(c.kind == VerificationKind.TEST for c in self.success_criteria)
            if not has_test_criterion:
                raise ValueError("RUN_TESTS requires at least one TEST success criterion")
        return self

    @model_validator(mode="after")
    def validate_dependency_policy(self):
        if not self.constraints.allow_dependency_changes:
            if ApprovalTrigger.DEPENDENCY_CHANGE not in self.approval_gates:
                raise ValueError(
                    "DEPENDENCY_CHANGE approval gate required when allow_dependency_changes=False"
                )
        return self
