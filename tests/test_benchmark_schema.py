import pytest
from pydantic import ValidationError
from models.benchmark import (
    TaskType, GraderType, MetricName, VerdictStatus,
    TaskReference, BenchmarkTask, GraderDefinition,
    MetricResult, BenchmarkRun, BenchmarkSummary, BenchmarkSuite,
)


def make_reference(**overrides) -> TaskReference:
    kwargs = dict(reference_id="ref-001", description="Expected: add function with tests")
    kwargs.update(overrides)
    return TaskReference(**kwargs)


def make_task(**overrides) -> BenchmarkTask:
    kwargs = dict(task_id="task-001", name="Add two numbers",
                  task_type=TaskType.CODING, prompt="Write a function that adds two numbers.")
    kwargs.update(overrides)
    return BenchmarkTask(**kwargs)


def make_grader(**overrides) -> GraderDefinition:
    kwargs = dict(grader_id="grd-001", name="Output matches expected",
                  grader_type=GraderType.DETERMINISTIC, pass_condition="output == expected")
    kwargs.update(overrides)
    return GraderDefinition(**kwargs)


def make_metric(**overrides) -> MetricResult:
    kwargs = dict(metric_name=MetricName.TASK_SUCCESS, value=1.0)
    kwargs.update(overrides)
    return MetricResult(**kwargs)


def make_run(**overrides) -> BenchmarkRun:
    kwargs = dict(run_id="run-001", suite_id="suite-code", task_id="task-001",
                  harness_version="1.0.0", model_name="gpt-4",
                  graders=[make_grader()], metrics=[make_metric()],
                  verdict=VerdictStatus.PASS, finished_at="2025-04-01T12:00:00Z")
    kwargs.update(overrides)
    return BenchmarkRun(**kwargs)


def make_summary(**overrides) -> BenchmarkSummary:
    kwargs = dict(suite_id="suite-code", total_runs=10, pass_rate=0.8)
    kwargs.update(overrides)
    return BenchmarkSummary(**kwargs)


def make_suite(**overrides) -> BenchmarkSuite:
    kwargs = dict(suite_id="suite-code", name="Coding Benchmarks",
                  tasks=[make_task()])
    kwargs.update(overrides)
    return BenchmarkSuite(**kwargs)


class TestTaskType:
    def test_all_values_present(self):
        assert len(TaskType) == 4
        assert TaskType.REFACTOR.value == "refactor"


class TestGraderType:
    def test_all_values_present(self):
        assert len(GraderType) == 3
        assert GraderType.LLM_JUDGE.value == "llm_judge"


class TestMetricName:
    def test_all_values_present(self):
        assert len(MetricName) == 7
        assert MetricName.SAFETY_VIOLATIONS.value == "safety_violations"


class TestVerdictStatus:
    def test_all_values_present(self):
        assert len(VerdictStatus) == 3
        assert VerdictStatus.PARTIAL.value == "partial"


class TestTaskReference:
    def test_minimal(self):
        ref = make_reference()
        assert ref.reference_id == "ref-001"

    def test_empty_id_raises(self):
        with pytest.raises(ValidationError):
            make_reference(reference_id="  ")

    def test_empty_description_raises(self):
        with pytest.raises(ValidationError):
            make_reference(description="  ")

    def test_with_expected_artifacts(self):
        ref = make_reference(expected_artifacts=["main.py", "test_main.py"])
        assert len(ref.expected_artifacts) == 2

    def test_with_reference_notes(self):
        ref = make_reference(reference_notes="Uses standard library only")
        assert ref.reference_notes == "Uses standard library only"


class TestBenchmarkTask:
    def test_minimal(self):
        t = make_task()
        assert t.task_id == "task-001"
        assert t.task_type == TaskType.CODING

    def test_empty_task_id_raises(self):
        with pytest.raises(ValidationError):
            make_task(task_id="  ")

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError):
            make_task(name="  ")

    def test_empty_prompt_raises(self):
        with pytest.raises(ValidationError):
            make_task(prompt="  ")

    def test_with_reference(self):
        t = make_task(reference=make_reference())
        assert t.reference.reference_id == "ref-001"

    def test_with_inputs(self):
        t = make_task(inputs={"a": 2, "b": 3})
        assert t.inputs["a"] == 2

    def test_with_tags(self):
        t = make_task(tags=["regression", "math"])
        assert "math" in t.tags

    def test_all_task_types_accepted(self):
        for tt in TaskType:
            t = make_task(task_id=f"task-{tt.value}", task_type=tt)
            assert t.task_type == tt

    def test_inputs_default_empty(self):
        t = make_task()
        assert t.inputs == {}

    def test_tags_default_empty(self):
        t = make_task()
        assert t.tags == []


class TestGraderDefinition:
    def test_minimal(self):
        g = make_grader()
        assert g.grader_id == "grd-001"

    def test_empty_grader_id_raises(self):
        with pytest.raises(ValidationError):
            make_grader(grader_id="  ")

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError):
            make_grader(name="  ")

    def test_empty_pass_condition_raises(self):
        with pytest.raises(ValidationError):
            make_grader(pass_condition="  ")

    def test_with_rubric(self):
        g = make_grader(rubric="Output must match expected exactly")
        assert g.rubric == "Output must match expected exactly"

    def test_all_grader_types_accepted(self):
        for gt in GraderType:
            g = make_grader(grader_id=f"grd-{gt.value}", grader_type=gt)
            assert g.grader_type == gt

    def test_llm_judge(self):
        g = make_grader(grader_type=GraderType.LLM_JUDGE,
                        rubric="Is the solution correct? 1-5",
                        pass_condition="score >= 4")
        assert g.grader_type == GraderType.LLM_JUDGE

    def test_human_grader(self):
        g = make_grader(grader_type=GraderType.HUMAN,
                        rubric="Code review checklist",
                        pass_condition="all items checked")
        assert g.grader_type == GraderType.HUMAN


class TestMetricResult:
    def test_minimal(self):
        m = make_metric()
        assert m.metric_name == MetricName.TASK_SUCCESS
        assert m.value == 1.0

    def test_with_unit(self):
        m = make_metric(metric_name=MetricName.LATENCY_SECONDS, value=12.5,
                        unit="s")
        assert m.unit == "s"

    def test_with_threshold_and_passed(self):
        m = make_metric(metric_name=MetricName.LATENCY_SECONDS, value=12.5,
                        threshold=30.0, passed=True)
        assert m.passed is True

    def test_negative_latency_raises(self):
        with pytest.raises(ValidationError):
            make_metric(metric_name=MetricName.LATENCY_SECONDS, value=-1.0)

    def test_negative_cost_raises(self):
        with pytest.raises(ValidationError):
            make_metric(metric_name=MetricName.COST_USD, value=-0.5)

    def test_negative_retries_raises(self):
        with pytest.raises(ValidationError):
            make_metric(metric_name=MetricName.RETRY_COUNT, value=-1)

    def test_negative_safety_violations_raises(self):
        with pytest.raises(ValidationError):
            make_metric(metric_name=MetricName.SAFETY_VIOLATIONS, value=-1)

    def test_non_negative_latency_valid(self):
        m = make_metric(metric_name=MetricName.LATENCY_SECONDS, value=0.0)
        assert m.value == 0.0

    def test_task_success_can_be_negative(self):
        m = make_metric(metric_name=MetricName.TASK_SUCCESS, value=-1.0)
        assert m.value == -1.0

    def test_all_metric_names_accepted(self):
        for mn in MetricName:
            val = 0.0 if mn in {MetricName.LATENCY_SECONDS, MetricName.COST_USD,
                                MetricName.RETRY_COUNT, MetricName.SAFETY_VIOLATIONS} else 1.0
            m = make_metric(metric_name=mn, value=val)
            assert m.metric_name == mn


class TestBenchmarkRun:
    def test_minimal(self):
        r = make_run()
        assert r.run_id == "run-001"
        assert r.verdict == VerdictStatus.PASS

    def test_empty_run_id_raises(self):
        with pytest.raises(ValidationError):
            make_run(run_id="  ")

    def test_empty_suite_id_raises(self):
        with pytest.raises(ValidationError):
            make_run(suite_id="  ")

    def test_empty_task_id_raises(self):
        with pytest.raises(ValidationError):
            make_run(task_id="  ")

    def test_empty_harness_version_raises(self):
        with pytest.raises(ValidationError):
            make_run(harness_version="  ")

    def test_empty_model_name_raises(self):
        with pytest.raises(ValidationError):
            make_run(model_name="  ")

    def test_no_graders_raises(self):
        with pytest.raises(ValidationError):
            make_run(graders=[])

    def test_no_metrics_raises(self):
        with pytest.raises(ValidationError):
            make_run(metrics=[])

    def test_pass_without_finished_at_raises(self):
        with pytest.raises(ValidationError):
            make_run(finished_at=None)

    def test_fail_without_finished_at_raises(self):
        with pytest.raises(ValidationError):
            make_run(verdict=VerdictStatus.FAIL, finished_at=None)

    def test_partial_without_finished_at_valid(self):
        r = make_run(verdict=VerdictStatus.PARTIAL, finished_at=None)
        assert r.verdict == VerdictStatus.PARTIAL
        assert r.finished_at is None

    def test_multiple_graders(self):
        r = make_run(graders=[
            make_grader(grader_id="grd-001"),
            make_grader(grader_id="grd-002", grader_type=GraderType.HUMAN,
                        pass_condition="reviewed"),
        ])
        assert len(r.graders) == 2

    def test_multiple_metrics(self):
        r = make_run(metrics=[
            make_metric(),
            make_metric(metric_name=MetricName.LATENCY_SECONDS, value=15.0),
        ])
        assert len(r.metrics) == 2

    def test_with_notes(self):
        r = make_run(notes="Hallucinated import")
        assert r.notes == "Hallucinated import"

    def test_with_started_at(self):
        r = make_run(started_at="2025-04-01T11:55:00Z")
        assert r.started_at == "2025-04-01T11:55:00Z"

    def test_all_verdicts_accepted(self):
        for vs in VerdictStatus:
            ft = "2025-04-01T12:00:00Z" if vs in (VerdictStatus.PASS, VerdictStatus.FAIL) else None
            r = make_run(verdict=vs, finished_at=ft)
            assert r.verdict == vs


class TestBenchmarkSummary:
    def test_minimal(self):
        s = make_summary()
        assert s.suite_id == "suite-code"
        assert s.pass_rate == 0.8

    def test_empty_suite_id_raises(self):
        with pytest.raises(ValidationError):
            make_summary(suite_id="  ")

    def test_pass_rate_too_low_raises(self):
        with pytest.raises(ValidationError):
            make_summary(pass_rate=-0.1)

    def test_pass_rate_too_high_raises(self):
        with pytest.raises(ValidationError):
            make_summary(pass_rate=1.1)

    def test_pass_rate_zero_valid(self):
        s = make_summary(pass_rate=0.0)
        assert s.pass_rate == 0.0

    def test_pass_rate_one_valid(self):
        s = make_summary(pass_rate=1.0)
        assert s.pass_rate == 1.0

    def test_negative_total_runs_raises(self):
        with pytest.raises(ValidationError):
            make_summary(total_runs=-1)

    def test_zero_total_runs_valid(self):
        s = make_summary(total_runs=0, pass_rate=0.0)
        assert s.total_runs == 0

    def test_negative_violations_raises(self):
        with pytest.raises(ValidationError):
            make_summary(total_safety_violations=-1)

    def test_with_latency_and_cost(self):
        s = make_summary(average_latency_seconds=25.0, average_cost_usd=0.15)
        assert s.average_latency_seconds == 25.0
        assert s.average_cost_usd == 0.15

    def test_total_safety_violations_defaults_zero(self):
        s = make_summary()
        assert s.total_safety_violations == 0


class TestBenchmarkSuite:
    def test_minimal(self):
        s = make_suite()
        assert s.suite_id == "suite-code"
        assert len(s.tasks) == 1

    def test_empty_suite_id_raises(self):
        with pytest.raises(ValidationError):
            make_suite(suite_id="  ")

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError):
            make_suite(name="  ")

    def test_no_tasks_raises(self):
        with pytest.raises(ValidationError):
            make_suite(tasks=[])

    def test_multiple_tasks(self):
        s = make_suite(tasks=[
            make_task(task_id="task-001"),
            make_task(task_id="task-002", name="Debug crash",
                      task_type=TaskType.DEBUGGING,
                      prompt="Fix the null pointer crash"),
            make_task(task_id="task-003", name="Refactor class",
                      task_type=TaskType.REFACTOR,
                      prompt="Refactor this class into smaller ones"),
        ])
        assert len(s.tasks) == 3

    def test_with_summary(self):
        s = make_suite(summary=make_summary())
        assert s.summary.pass_rate == 0.8

    def test_all_task_types_in_suite(self):
        tasks = []
        for tt in TaskType:
            tasks.append(make_task(task_id=f"task-{tt.value}", task_type=tt,
                                   name=f"Task {tt.value}", prompt=f"Do {tt.value}"))
        s = make_suite(tasks=tasks)
        assert len(s.tasks) == 4
