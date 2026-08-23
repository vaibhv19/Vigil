import pytest
from vigil.db.connection import get_session
from vigil.db.repository import VigilRepository
from vigil.eval.metrics import MetricsEngine
from vigil.eval.comparator import RunComparator


def _create_test_run(session, suite_name, agent_version, tasks_data):
    """
    Helper to create a suite, run, tasks, and tool calls for metrics testing.
    tasks_data: list of dicts with keys: slug, status, tool_durations (list of int ms)
    """
    suite = VigilRepository.get_or_create_suite(session, suite_name, agent_version)
    run = VigilRepository.create_eval_run(session, suite.id, {"test": True})

    from vigil.eval.task_models import TaskDefinition
    for idx, td in enumerate(tasks_data, start=1):
        task_def = TaskDefinition(
            task_id=td["slug"],
            description=f"Metrics test task {td['slug']}",
            input_prompt="test",
            category="metrics",
            expected_output={"assertions": []},
        )
        task = VigilRepository.get_or_create_task(session, task_def)
        VigilRepository.associate_task_with_suite(session, suite.id, task.id, idx)

        result = VigilRepository.create_task_result(
            session=session,
            run_id=run.id,
            task_id=task.id,
            status=td["status"],
            steps_taken=len(td.get("tool_durations", [])),
            final_output="test output",
        )

        for seq, dur in enumerate(td.get("tool_durations", []), start=1):
            VigilRepository.create_tool_call(
                session=session,
                task_result_id=result.id,
                sequence_number=seq,
                tool_name="bash",
                input_args={"cmd": "echo"},
                stdout_capture="ok",
                exit_code=0,
                duration_ms=dur,
            )

    VigilRepository.update_eval_run(session, run.id, "COMPLETED", 5000)
    return run.id


def test_metrics_engine_aggregation():
    """Verify MetricsEngine computes correct pass rates and percentiles from DB data."""
    with get_session() as session:
        run_id = _create_test_run(session, "metrics-suite-agg", "v1.0.0", [
            {"slug": "metrics-t1", "status": "PASS", "tool_durations": [100, 200, 300]},
            {"slug": "metrics-t2", "status": "PASS", "tool_durations": [150, 250]},
            {"slug": "metrics-t3", "status": "FAIL", "tool_durations": [500]},
            {"slug": "metrics-t4", "status": "ERROR", "tool_durations": []},
        ])

    metrics = MetricsEngine.get_run_metrics(run_id)

    assert metrics.total_tasks == 4
    assert metrics.passed_tasks == 2
    assert metrics.failed_tasks == 1
    assert metrics.error_tasks == 1
    assert metrics.pass_rate == 50.0
    assert metrics.total_tool_calls == 6
    assert metrics.p50_latency_ms > 0
    assert metrics.p90_latency_ms >= metrics.p50_latency_ms
    assert metrics.status == "COMPLETED"


def test_comparator_differential():
    """Verify RunComparator correctly identifies task status changes and latency deltas."""
    with get_session() as session:
        run_id_a = _create_test_run(session, "compare-suite", "v1.0.0", [
            {"slug": "compare-t1", "status": "PASS", "tool_durations": [100, 200]},
            {"slug": "compare-t2", "status": "FAIL", "tool_durations": [500]},
        ])
        run_id_b = _create_test_run(session, "compare-suite", "v2.0.0", [
            {"slug": "compare-t1", "status": "PASS", "tool_durations": [80, 120]},
            {"slug": "compare-t2", "status": "PASS", "tool_durations": [200]},
        ])

    comparison = RunComparator.compare_runs(run_id_a, run_id_b)

    assert comparison.pass_rate_a == 50.0
    assert comparison.pass_rate_b == 100.0
    assert comparison.pass_rate_delta == 50.0
    assert len(comparison.task_changes) == 2

    # Find the task that changed status
    t2_change = next(tc for tc in comparison.task_changes if tc.task_slug == "compare-t2")
    assert t2_change.status_change == "FAIL -> PASS"
    assert t2_change.latency_delta_ms < 0  # v2 should be faster

    t1_change = next(tc for tc in comparison.task_changes if tc.task_slug == "compare-t1")
    assert t1_change.status_change == "NO_CHANGE"
