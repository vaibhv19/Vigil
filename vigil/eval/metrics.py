import uuid
import math
from pydantic import BaseModel
from sqlalchemy import select, func


from vigil.db.models import EvalRun, EvalSuite, TaskResult, ToolCall, Anomaly
from vigil.db.connection import get_session


class RunSummaryMetrics(BaseModel):
    """Structured metrics summary for a single evaluation run."""
    run_id: str
    suite_name: str
    agent_version: str
    status: str
    pass_rate: float
    total_tasks: int
    passed_tasks: int
    failed_tasks: int
    error_tasks: int
    p50_latency_ms: float
    p90_latency_ms: float
    total_duration_ms: int
    total_tool_calls: int
    total_anomalies: int
    total_cost: float


class PercentileCalculator:
    """Fast math implementations for percentile extraction from duration lists."""

    @staticmethod
    def percentile(values: list[float], p: float) -> float:
        """
        Calculate the p-th percentile of a list of values.
        Uses linear interpolation between closest ranks.
        Returns 0.0 for empty lists.
        """
        if not values:
            return 0.0

        sorted_vals = sorted(values)
        n = len(sorted_vals)

        if n == 1:
            return sorted_vals[0]

        # Calculate rank using the C=1 variant (Excel PERCENTILE.INC)
        rank = (p / 100.0) * (n - 1)
        lower = int(math.floor(rank))
        upper = int(math.ceil(rank))
        fraction = rank - lower

        if lower == upper:
            return sorted_vals[lower]

        return sorted_vals[lower] + fraction * (sorted_vals[upper] - sorted_vals[lower])


class MetricsEngine:
    """
    Queries PostgreSQL to aggregate and compute statistical metrics
    for evaluation runs including pass rates, latency percentiles,
    tool call counts, and anomaly tallies.
    """

    @staticmethod
    def get_run_metrics(run_id: uuid.UUID) -> RunSummaryMetrics:
        """
        Computes aggregated metrics for a given evaluation run.
        """
        with get_session() as session:
            # Fetch the run record
            run = session.scalar(select(EvalRun).where(EvalRun.id == run_id))
            if not run:
                raise ValueError(f"EvalRun not found: {run_id}")

            # Fetch suite metadata
            suite = session.scalar(select(EvalSuite).where(EvalSuite.id == run.suite_id))
            suite_name = suite.name if suite else "Unknown"
            agent_version = suite.agent_version if suite else "Unknown"

            # Fetch all task results for this run
            results = session.scalars(
                select(TaskResult).where(TaskResult.run_id == run_id)
            ).all()

            total_tasks = len(results)
            passed = sum(1 for r in results if r.status == "PASS")
            failed = sum(1 for r in results if r.status == "FAIL")
            errors = sum(1 for r in results if r.status == "ERROR")
            pass_rate = (passed / total_tasks * 100.0) if total_tasks > 0 else 0.0

            # Collect durations for percentile calculations
            result_ids = [r.id for r in results]

            # Get all tool calls for this run's results
            tool_call_count = 0
            durations = []
            if result_ids:
                calls = session.scalars(
                    select(ToolCall).where(ToolCall.task_result_id.in_(result_ids))
                ).all()
                tool_call_count = len(calls)
                durations = [c.duration_ms for c in calls if c.duration_ms is not None]

            # Get anomaly count
            anomaly_count = 0
            if result_ids:
                anomaly_count = session.scalar(
                    select(func.count(Anomaly.id)).where(Anomaly.task_result_id.in_(result_ids))
                ) or 0

            p50 = PercentileCalculator.percentile(durations, 50)
            p90 = PercentileCalculator.percentile(durations, 90)

            return RunSummaryMetrics(
                run_id=str(run_id),
                suite_name=suite_name,
                agent_version=agent_version,
                status=run.status,
                pass_rate=round(pass_rate, 2),
                total_tasks=total_tasks,
                passed_tasks=passed,
                failed_tasks=failed,
                error_tasks=errors,
                p50_latency_ms=round(p50, 2),
                p90_latency_ms=round(p90, 2),
                total_duration_ms=run.total_duration_ms or 0,
                total_tool_calls=tool_call_count,
                total_anomalies=anomaly_count,
                total_cost=run.total_cost or 0.0,
            )
