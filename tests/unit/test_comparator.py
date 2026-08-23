import pytest
from vigil.eval.comparator import TaskComparison, RunComparison


class TestTaskComparison:
    def test_no_change(self):
        tc = TaskComparison(
            task_slug="task-1",
            status_a="PASS",
            status_b="PASS",
            status_change="NO_CHANGE",
            latency_delta_ms=0,
            steps_delta=0,
            anomaly_delta=0,
        )
        assert tc.status_change == "NO_CHANGE"
        assert tc.latency_delta_ms == 0

    def test_regression_detected(self):
        tc = TaskComparison(
            task_slug="task-2",
            status_a="PASS",
            status_b="FAIL",
            status_change="PASS -> FAIL",
            latency_delta_ms=150,
            steps_delta=2,
            anomaly_delta=1,
        )
        assert tc.status_change == "PASS -> FAIL"
        assert tc.latency_delta_ms == 150
        assert tc.anomaly_delta == 1

    def test_improvement_detected(self):
        tc = TaskComparison(
            task_slug="task-3",
            status_a="FAIL",
            status_b="PASS",
            status_change="FAIL -> PASS",
            latency_delta_ms=-50,
            steps_delta=-1,
            anomaly_delta=0,
        )
        assert tc.status_change == "FAIL -> PASS"
        assert tc.latency_delta_ms == -50


class TestRunComparison:
    def test_model_validation(self):
        comparison = RunComparison(
            run_id_a="run-a",
            run_id_b="run-b",
            agent_version_a="v1.0",
            agent_version_b="v2.0",
            pass_rate_a=80.0,
            pass_rate_b=90.0,
            pass_rate_delta=10.0,
            p50_latency_delta_ms=-20.0,
            p90_latency_delta_ms=-50.0,
            total_tasks_a=5,
            total_tasks_b=5,
            task_changes=[
                TaskComparison(
                    task_slug="task-1",
                    status_a="PASS",
                    status_b="PASS",
                    status_change="NO_CHANGE",
                    latency_delta_ms=-10,
                    steps_delta=0,
                    anomaly_delta=0,
                ),
                TaskComparison(
                    task_slug="task-2",
                    status_a="FAIL",
                    status_b="PASS",
                    status_change="FAIL -> PASS",
                    latency_delta_ms=-30,
                    steps_delta=-1,
                    anomaly_delta=0,
                ),
            ],
        )
        assert comparison.pass_rate_delta == 10.0
        assert len(comparison.task_changes) == 2
        assert comparison.task_changes[1].status_change == "FAIL -> PASS"

    def test_serialization(self):
        comparison = RunComparison(
            run_id_a="a",
            run_id_b="b",
            agent_version_a="v1",
            agent_version_b="v2",
            pass_rate_a=50.0,
            pass_rate_b=75.0,
            pass_rate_delta=25.0,
            p50_latency_delta_ms=0.0,
            p90_latency_delta_ms=0.0,
            total_tasks_a=2,
            total_tasks_b=2,
            task_changes=[],
        )
        data = comparison.model_dump()
        assert data["pass_rate_delta"] == 25.0
        assert isinstance(data["task_changes"], list)
