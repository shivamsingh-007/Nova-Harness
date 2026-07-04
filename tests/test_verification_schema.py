import pytest
from pydantic import ValidationError
from models.verification import (
    VerificationPlan,
    VerificationCheck,
    VerificationEvidence,
    VerificationResult,
    VerificationVerdict,
    CheckType,
    CheckStatus,
    EvidenceType,
    VerdictStatus,
)


def make_evidence(**overrides) -> VerificationEvidence:
    kwargs = dict(
        evidence_id="ev-001",
        evidence_type=EvidenceType.LOG,
        path="/workspace/test-output.log",
        summary="Tests passed: 162/162",
    )
    kwargs.update(overrides)
    return VerificationEvidence(**kwargs)


def make_check(**overrides) -> VerificationCheck:
    kwargs = dict(
        check_id="chk-001",
        name="Run tests",
        check_type=CheckType.TEST,
        blocking=True,
        command="pytest tests/",
        status=CheckStatus.PASSED,
        evidence=[make_evidence()],
    )
    kwargs.update(overrides)
    return VerificationCheck(**kwargs)


def make_plan(**overrides) -> VerificationPlan:
    kwargs = dict(
        plan_id="plan-001",
        task_id="task-001",
        checks=[make_check()],
    )
    kwargs.update(overrides)
    return VerificationPlan(**kwargs)


def make_verdict(**overrides) -> VerificationVerdict:
    kwargs = dict(
        status=VerdictStatus.PASS,
        blocking_failures=[],
        non_blocking_failures=[],
        summary="All checks passed",
    )
    kwargs.update(overrides)
    return VerificationVerdict(**kwargs)


def make_result(**overrides) -> VerificationResult:
    kwargs = dict(
        plan_id="plan-001",
        run_id="run-001",
        checks=[make_check()],
        verdict=make_verdict(),
        started_at="2025-01-01T00:00:00Z",
        finished_at="2025-01-01T00:01:30Z",
    )
    kwargs.update(overrides)
    return VerificationResult(**kwargs)


class TestVerificationEvidence:
    def test_valid_evidence(self):
        ev = make_evidence()
        assert ev.evidence_id == "ev-001"

    def test_empty_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_evidence(evidence_id="")
        assert "evidence_id must not be empty" in str(exc.value)

    def test_metric_without_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_evidence(
                evidence_type=EvidenceType.METRIC,
                metric_name=None,
                metric_value=85.0,
            )
        assert "metric_name is required for METRIC evidence" in str(exc.value)

    def test_metric_without_value_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_evidence(
                evidence_type=EvidenceType.METRIC,
                metric_name="coverage",
                metric_value=None,
            )
        assert "metric_value is required for METRIC evidence" in str(exc.value)

    def test_metric_with_name_and_value_is_valid(self):
        ev = make_evidence(
            evidence_type=EvidenceType.METRIC,
            metric_name="coverage",
            metric_value=92.5,
        )
        assert ev.metric_name == "coverage"
        assert ev.metric_value == 92.5

    def test_log_evidence_without_metric_is_valid(self):
        ev = make_evidence(evidence_type=EvidenceType.LOG, summary="All good")
        assert ev.evidence_type == EvidenceType.LOG


class TestVerificationCheck:
    def test_valid_check(self):
        chk = make_check()
        assert chk.check_id == "chk-001"
        assert chk.status == CheckStatus.PASSED

    def test_empty_check_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_check(check_id="")
        assert "must not be empty" in str(exc.value)

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_check(name="")
        assert "must not be empty" in str(exc.value)

    def test_no_command_or_acceptance_rule_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_check(command=None, acceptance_rule=None)
        assert "each check must have either command or acceptance_rule" in str(exc.value)

    def test_acceptance_rule_without_command_is_valid(self):
        chk = make_check(command=None, acceptance_rule="Table contains 8 competitors")
        assert chk.acceptance_rule == "Table contains 8 competitors"
        assert chk.command is None

    def test_failure_reason_when_failed_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_check(status=CheckStatus.FAILED, failure_reason=None)
        assert "failure_reason is required when status is FAILED" in str(exc.value)

    def test_failure_reason_when_failed_is_valid(self):
        chk = make_check(
            status=CheckStatus.FAILED,
            failure_reason="3 tests failed",
        )
        assert chk.failure_reason == "3 tests failed"

    def test_passed_check_without_failure_reason_is_valid(self):
        chk = make_check(status=CheckStatus.PASSED, failure_reason=None)
        assert chk.status == CheckStatus.PASSED

    def test_blocking_default_true(self):
        chk = make_check()
        assert chk.blocking is True

    def test_non_blocking_check(self):
        chk = make_check(blocking=False)
        assert chk.blocking is False

    def test_all_check_types(self):
        for ct in CheckType:
            chk = make_check(check_type=ct)
            assert chk.check_type == ct


class TestVerificationPlan:
    def test_valid_plan(self):
        plan = make_plan()
        assert plan.plan_id == "plan-001"
        assert len(plan.checks) == 1

    def test_empty_plan_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_plan(plan_id="")
        assert "plan_id must not be empty" in str(exc.value)

    def test_empty_task_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_plan(task_id="")
        assert "task_id must not be empty" in str(exc.value)

    def test_no_checks_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_plan(checks=[])
        assert "verification plan must contain at least one check" in str(exc.value)

    def test_multiple_checks(self):
        plan = make_plan(checks=[make_check(), make_check(check_id="chk-002", name="Lint", check_type=CheckType.LINT)])
        assert len(plan.checks) == 2


class TestVerificationVerdict:
    def test_valid_pass(self):
        v = make_verdict()
        assert v.status == VerdictStatus.PASS

    def test_valid_fail_with_blocking(self):
        v = make_verdict(
            status=VerdictStatus.FAIL,
            blocking_failures=["chk-001"],
        )
        assert v.status == VerdictStatus.FAIL

    def test_valid_partial(self):
        v = make_verdict(
            status=VerdictStatus.PARTIAL,
            non_blocking_failures=["chk-002"],
        )
        assert v.status == VerdictStatus.PARTIAL

    def test_valid_blocked(self):
        v = make_verdict(status=VerdictStatus.BLOCKED)
        assert v.status == VerdictStatus.BLOCKED

    def test_pass_with_blocking_failures_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_verdict(status=VerdictStatus.PASS, blocking_failures=["chk-001"])
        assert "verdict cannot be PASS when blocking failures exist" in str(exc.value)

    def test_fail_with_blocking_failures_is_valid(self):
        v = make_verdict(status=VerdictStatus.FAIL, blocking_failures=["chk-001"])
        assert v.status == VerdictStatus.FAIL


class TestVerificationResult:
    def test_valid_result(self):
        r = make_result()
        assert r.plan_id == "plan-001"
        assert r.verdict.status == VerdictStatus.PASS

    def test_empty_plan_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_result(plan_id="")
        assert "plan_id must not be empty" in str(exc.value)

    def test_empty_run_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_result(run_id="")
        assert "run_id must not be empty" in str(exc.value)

    def test_pass_verdict_without_finished_at_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_result(finished_at=None)
        assert "finished_at is required when verdict is PASS or FAIL" in str(exc.value)

    def test_fail_verdict_without_finished_at_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_result(
                verdict=make_verdict(status=VerdictStatus.FAIL, blocking_failures=["chk-001"]),
                finished_at=None,
            )
        assert "finished_at is required when verdict is PASS or FAIL" in str(exc.value)

    def test_partial_verdict_without_finished_at_is_valid(self):
        r = make_result(
            verdict=make_verdict(status=VerdictStatus.PARTIAL, non_blocking_failures=["chk-002"]),
            finished_at=None,
        )
        assert r.verdict.status == VerdictStatus.PARTIAL
        assert r.finished_at is None

    def test_blocked_verdict_without_finished_at_is_valid(self):
        r = make_result(
            verdict=make_verdict(status=VerdictStatus.BLOCKED),
            finished_at=None,
        )
        assert r.verdict.status == VerdictStatus.BLOCKED

    def test_checks_can_differ_from_plan(self):
        r = make_result(checks=[make_check(check_id="chk-002", name="Lint", check_type=CheckType.LINT)])
        assert len(r.checks) == 1
        assert r.checks[0].check_type == CheckType.LINT


class TestSerialization:
    def test_plan_serialize(self):
        plan = make_plan()
        data = plan.model_dump()
        assert data["plan_id"] == "plan-001"
        assert len(data["checks"]) == 1

    def test_check_serialize(self):
        chk = make_check()
        data = chk.model_dump()
        assert data["check_id"] == "chk-001"
        assert data["status"] == "passed"

    def test_evidence_serialize(self):
        ev = make_evidence()
        data = ev.model_dump()
        assert data["evidence_id"] == "ev-001"
        assert data["evidence_type"] == "log"

    def test_verdict_serialize(self):
        v = make_verdict()
        data = v.model_dump()
        assert data["status"] == "pass"
        assert data["summary"] == "All checks passed"

    def test_result_serialize(self):
        r = make_result()
        data = r.model_dump()
        assert data["verdict"]["status"] == "pass"
        assert data["finished_at"] == "2025-01-01T00:01:30Z"
