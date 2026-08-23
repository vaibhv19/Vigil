import pytest
from vigil.eval.metrics import PercentileCalculator, RunSummaryMetrics


class TestPercentileCalculator:
    def test_empty_list_returns_zero(self):
        assert PercentileCalculator.percentile([], 50) == 0.0
        assert PercentileCalculator.percentile([], 90) == 0.0

    def test_single_element(self):
        assert PercentileCalculator.percentile([42.0], 50) == 42.0
        assert PercentileCalculator.percentile([42.0], 90) == 42.0

    def test_p50_known_list(self):
        values = list(range(1, 101))  # 1 to 100
        p50 = PercentileCalculator.percentile(values, 50)
        assert p50 == 50.5

    def test_p90_known_list(self):
        values = list(range(1, 101))  # 1 to 100
        p90 = PercentileCalculator.percentile(values, 90)
        assert p90 == pytest.approx(90.1, abs=0.01)

    def test_p50_small_list(self):
        values = [10, 20, 30, 40, 50]
        p50 = PercentileCalculator.percentile(values, 50)
        assert p50 == 30.0

    def test_p90_small_list(self):
        values = [10, 20, 30, 40, 50]
        p90 = PercentileCalculator.percentile(values, 90)
        assert p90 == pytest.approx(46.0, abs=0.1)

    def test_unsorted_input(self):
        values = [50, 10, 40, 20, 30]
        p50 = PercentileCalculator.percentile(values, 50)
        assert p50 == 30.0

    def test_p0_returns_min(self):
        values = [5, 10, 15, 20]
        assert PercentileCalculator.percentile(values, 0) == 5.0

    def test_p100_returns_max(self):
        values = [5, 10, 15, 20]
        assert PercentileCalculator.percentile(values, 100) == 20.0


class TestRunSummaryMetrics:
    def test_model_validation(self):
        metrics = RunSummaryMetrics(
            run_id="test-run-id",
            suite_name="Test Suite",
            agent_version="v1.0.0",
            status="COMPLETED",
            pass_rate=75.0,
            total_tasks=4,
            passed_tasks=3,
            failed_tasks=1,
            error_tasks=0,
            p50_latency_ms=120.5,
            p90_latency_ms=350.2,
            total_duration_ms=5000,
            total_tool_calls=12,
            total_anomalies=0,
            total_cost=0.0,
        )
        assert metrics.pass_rate == 75.0
        assert metrics.total_tasks == 4
        assert metrics.p50_latency_ms == 120.5
        assert metrics.p90_latency_ms == 350.2

    def test_model_serialization(self):
        metrics = RunSummaryMetrics(
            run_id="r1",
            suite_name="S1",
            agent_version="v1",
            status="COMPLETED",
            pass_rate=100.0,
            total_tasks=1,
            passed_tasks=1,
            failed_tasks=0,
            error_tasks=0,
            p50_latency_ms=50.0,
            p90_latency_ms=90.0,
            total_duration_ms=1000,
            total_tool_calls=5,
            total_anomalies=0,
            total_cost=0.0,
        )
        data = metrics.model_dump()
        assert "run_id" in data
        assert "pass_rate" in data
        assert data["passed_tasks"] == 1
