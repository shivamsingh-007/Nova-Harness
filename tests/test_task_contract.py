import pytest
from pydantic import ValidationError
from models.task_contract import (
    TaskContract,
    TaskType,
    ToolName,
    ApprovalTrigger,
    VerificationKind,
    TaskScope,
    TaskInputs,
    TaskConstraints,
    SuccessCriterion,
    OutputRequirements,
)


def make_valid_contract(**overrides) -> TaskContract:
    defaults = dict(
        task_id="task-test",
        title="Fix null pointer in context packer",
        task_type=TaskType.BUG_FIX,
        goal="Fix the null pointer exception when context_packer receives an empty file list.",
        scope=TaskScope(
            repo_path="/repo",
            allowed_paths=["src/context_packer.py"],
            blocked_paths=["src/deployment/", "secrets/"],
        ),
        inputs=TaskInputs(
            user_request="Fix null pointer",
            relevant_files=["src/context_packer.py"],
            failing_tests=["tests/test_context_packer.py::test_empty_file_list"],
            error_logs=["TypeError: 'NoneType' object is not iterable"],
        ),
        constraints=TaskConstraints(max_files_changed=2, max_retries=2),
        tools_allowed=[ToolName.READ_FILE, ToolName.SEARCH_CODE, ToolName.EDIT_FILE, ToolName.RUN_TESTS],
        success_criteria=[
            SuccessCriterion(kind=VerificationKind.TEST, target="tests/test_context_packer.py::test_empty_file_list"),
            SuccessCriterion(kind=VerificationKind.LINT, target="src/"),
        ],
        approval_gates=[ApprovalTrigger.LARGE_DIFF, ApprovalTrigger.DEPENDENCY_CHANGE],
    )
    defaults.update(overrides)
    return TaskContract(**defaults)


class TestValidContracts:
    def test_valid_bug_fix(self):
        contract = make_valid_contract()
        assert contract.task_id == "task-test"
        assert contract.task_type == TaskType.BUG_FIX

    def test_valid_feature(self):
        contract = make_valid_contract(
            task_id="task-002",
            title="Add file watcher to context packer",
            task_type=TaskType.FEATURE,
            goal="Add a file watcher that triggers context repack on file change.",
            scope=TaskScope(repo_path="/repo", allowed_paths=["src/", "tests/"]),
            inputs=TaskInputs(user_request="Add file watcher"),
            constraints=TaskConstraints(max_files_changed=5),
            tools_allowed=[ToolName.READ_FILE, ToolName.SEARCH_CODE, ToolName.EDIT_FILE, ToolName.RUN_TESTS],
            success_criteria=[
                SuccessCriterion(kind=VerificationKind.TEST, target="tests/test_watcher.py"),
                SuccessCriterion(kind=VerificationKind.TYPECHECK, target="src/"),
            ],
            approval_gates=[ApprovalTrigger.DEPENDENCY_CHANGE],
        )
        assert contract.task_type == TaskType.FEATURE

    def test_valid_refactor(self):
        contract = make_valid_contract(
            task_id="task-003",
            title="Extract file scanning from context packer",
            task_type=TaskType.REFACTOR,
            goal="Extract file scanning logic into a separate module without changing behavior.",
            scope=TaskScope(repo_path="/repo", allowed_paths=["src/"]),
            inputs=TaskInputs(user_request="Extract file scanning", relevant_files=["src/context_packer.py"]),
            constraints=TaskConstraints(max_files_changed=4),
            tools_allowed=[ToolName.READ_FILE, ToolName.SEARCH_CODE, ToolName.EDIT_FILE, ToolName.RUN_TESTS, ToolName.GIT_DIFF],
            success_criteria=[
                SuccessCriterion(kind=VerificationKind.TEST, target="tests/"),
                SuccessCriterion(kind=VerificationKind.DIFF_REVIEW, target="all"),
            ],
            approval_gates=[ApprovalTrigger.DEPENDENCY_CHANGE],
        )
        assert ToolName.GIT_DIFF in contract.tools_allowed

    def test_task_with_network_allowed(self):
        contract = make_valid_contract(
            task_id="task-net",
            title="Network task",
            task_type=TaskType.FEATURE,
            goal="A task that needs network.",
            constraints=TaskConstraints(allow_network=True),
            approval_gates=[ApprovalTrigger.DEPENDENCY_CHANGE],
        )
        assert contract.constraints.allow_network is True

    def test_test_only_no_edit_tools(self):
        contract = make_valid_contract(
            task_id="task-test-only",
            title="Run tests only",
            task_type=TaskType.TEST_ONLY,
            goal="Just run the test suite.",
            tools_allowed=[ToolName.RUN_TESTS, ToolName.RUN_LINT],
            success_criteria=[SuccessCriterion(kind=VerificationKind.TEST, target="tests/")],
            approval_gates=[ApprovalTrigger.DEPENDENCY_CHANGE],
        )
        assert contract.task_type == TaskType.TEST_ONLY


class TestFieldValidators:
    def test_empty_title_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_contract(title="   ")
        assert "must not be blank" in str(exc.value)

    def test_empty_goal_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_contract(goal="")
        assert "must not be blank" in str(exc.value)

    def test_empty_tools_allowed_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_contract(tools_allowed=[])
        assert "tools_allowed must not be empty" in str(exc.value)

    def test_empty_success_criteria_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_contract(success_criteria=[])
        assert "success_criteria must not be empty" in str(exc.value)

    def test_retries_negative_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_contract(constraints=TaskConstraints(max_retries=-1))
        assert "max_retries must be between 0 and 5" in str(exc.value)

    def test_retries_too_high_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_contract(constraints=TaskConstraints(max_retries=6))
        assert "max_retries must be between 0 and 5" in str(exc.value)

    def test_retries_zero_is_valid(self):
        contract = make_valid_contract(constraints=TaskConstraints(max_retries=0))
        assert contract.constraints.max_retries == 0

    def test_max_files_changed_zero_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_contract(constraints=TaskConstraints(max_files_changed=0))
        assert "max_files_changed must be between 1 and 50" in str(exc.value)

    def test_max_files_changed_too_high_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_contract(constraints=TaskConstraints(max_files_changed=51))
        assert "max_files_changed must be between 1 and 50" in str(exc.value)

    def test_empty_repo_path_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_contract(scope=TaskScope(repo_path=""))
        assert "repo_path must not be empty" in str(exc.value)

    def test_empty_path_entry_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_contract(scope=TaskScope(repo_path="/repo", allowed_paths=[""]))
        assert "path entries must not be empty" in str(exc.value)

    def test_absolute_subpath_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_contract(scope=TaskScope(repo_path="/repo", blocked_paths=["/etc"]))
        assert "invalid relative path" in str(exc.value)

    def test_parent_traversal_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_contract(scope=TaskScope(repo_path="/repo", allowed_paths=["../src"]))
        assert "invalid relative path" in str(exc.value)

    def test_duplicate_paths_deduplicated(self):
        scope = TaskScope(repo_path="/repo", allowed_paths=["src/", "src/", "lib/"])
        assert scope.allowed_paths == ["src/", "lib/"]


class TestModelValidators:
    def test_overlapping_allowed_and_blocked_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_contract(
                scope=TaskScope(repo_path="/repo", allowed_paths=["src/", "tests/"], blocked_paths=["src/"])
            )
        assert "allowed_paths and blocked_paths overlap" in str(exc.value)

    def test_run_tests_without_test_criterion_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_contract(
                tools_allowed=[ToolName.READ_FILE, ToolName.RUN_TESTS],
                success_criteria=[SuccessCriterion(kind=VerificationKind.LINT, target="src/")],
            )
        assert "RUN_TESTS requires at least one TEST success criterion" in str(exc.value)

    def test_dependency_change_disallowed_without_gate_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_contract(
                constraints=TaskConstraints(allow_dependency_changes=False),
                approval_gates=[ApprovalTrigger.LARGE_DIFF],
            )
        assert "DEPENDENCY_CHANGE approval gate required" in str(exc.value)

    def test_dependency_change_allowed_does_not_require_gate(self):
        contract = make_valid_contract(
            constraints=TaskConstraints(allow_dependency_changes=True),
            approval_gates=[ApprovalTrigger.LARGE_DIFF],
        )
        assert contract.constraints.allow_dependency_changes is True

    def test_run_lint_without_test_criterion_is_valid(self):
        contract = make_valid_contract(
            tools_allowed=[ToolName.READ_FILE, ToolName.RUN_LINT],
            success_criteria=[SuccessCriterion(kind=VerificationKind.LINT, target="src/")],
        )
        assert ToolName.RUN_LINT in contract.tools_allowed


class TestDefaultsAndSerialization:
    def test_default_values(self):
        contract = make_valid_contract()
        assert contract.constraints.max_files_changed == 2
        assert contract.constraints.max_retries == 2
        assert contract.output_requirements.include_verification_receipts is True

    def test_serialize_to_dict(self):
        contract = make_valid_contract()
        data = contract.model_dump()
        assert data["task_id"] == "task-test"
        assert data["task_type"] == "bug_fix"
        assert isinstance(data["tools_allowed"], list)
        assert "read_file" in data["tools_allowed"]
