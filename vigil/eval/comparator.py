import uuid
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from vigil.db.models import EvalRun, EvalSuite, TaskResult, Task, ToolCall, Anomaly
from vigil.db.connection import get_session
from vigil.eval.metrics import MetricsEngine, RunSummaryMetrics


class TaskComparison(BaseModel):
    """Side-by-side differential for a single task across two runs."""
    task_slug: str
    status_a: str
    status_b: str
    status_change: str  # e.g. "PASS -> FAIL", "NO_CHANGE"
    latency_delta_ms: int
    steps_delta: int
    anomaly_delta: int


class RunComparison(BaseModel):
    """Aggregate differential comparison between two evaluation runs."""
    run_id_a: str
    run_id_b: str
    agent_version_a: str
    agent_version_b: str
    pass_rate_a: float
    pass_rate_b: float
    pass_rate_delta: float
    p50_latency_delta_ms: float
    p90_latency_delta_ms: float
    total_tasks_a: int
    total_tasks_b: int
    task_changes: list[TaskComparison]


class RunComparator:
    """
    Compares two evaluation runs side-by-side, computing task-level
    status changes, latency deltas, step count differences, and anomaly diffs.
    """

    @staticmethod
    def compare_runs(run_id_a: uuid.UUID, run_id_b: uuid.UUID) -> RunComparison:
        """
        Computes a differential comparison between Run A and Run B.
        """
        metrics_a = MetricsEngine.get_run_metrics(run_id_a)
        metrics_b = MetricsEngine.get_run_metrics(run_id_b)

        # Fetch task-level results for both runs
        with get_session() as session:
            results_a = session.scalars(
                select(TaskResult).where(TaskResult.run_id == run_id_a)
            ).all()
            results_b = session.scalars(
                select(TaskResult).where(TaskResult.run_id == run_id_b)
            ).all()

            # Build lookup maps by task_id
            def build_task_map(results, session):
                task_map = {}
                for r in results:
                    task = session.scalar(select(Task).where(Task.id == r.task_id))
                    if task:
                        # Get tool call count for this result
                        tool_count = session.scalar(
                            select(func.count(ToolCall.id)).where(ToolCall.task_result_id == r.id)
                        ) or 0
                        # Get anomaly count for this result
                        anomaly_count = session.scalar(
                            select(func.count(Anomaly.id)).where(Anomaly.task_result_id == r.id)
                        ) or 0
                        # Get total tool duration
                        total_duration = session.scalar(
                            select(func.coalesce(func.sum(ToolCall.duration_ms), 0)).where(
                                ToolCall.task_result_id == r.id
                            )
                        ) or 0
                        task_map[task.slug] = {
                            "status": r.status,
                            "steps": r.steps_taken,
                            "latency_ms": total_duration,
                            "anomalies": anomaly_count,
                        }
                return task_map

            map_a = build_task_map(results_a, session)
            map_b = build_task_map(results_b, session)

        # Compute task-level diffs
        all_slugs = sorted(set(list(map_a.keys()) + list(map_b.keys())))
        task_changes = []

        for slug in all_slugs:
            a = map_a.get(slug, {"status": "MISSING", "steps": 0, "latency_ms": 0, "anomalies": 0})
            b = map_b.get(slug, {"status": "MISSING", "steps": 0, "latency_ms": 0, "anomalies": 0})

            status_change = "NO_CHANGE" if a["status"] == b["status"] else f"{a['status']} -> {b['status']}"

            task_changes.append(TaskComparison(
                task_slug=slug,
                status_a=a["status"],
                status_b=b["status"],
                status_change=status_change,
                latency_delta_ms=b["latency_ms"] - a["latency_ms"],
                steps_delta=b["steps"] - a["steps"],
                anomaly_delta=b["anomalies"] - a["anomalies"],
            ))

        return RunComparison(
            run_id_a=str(run_id_a),
            run_id_b=str(run_id_b),
            agent_version_a=metrics_a.agent_version,
            agent_version_b=metrics_b.agent_version,
            pass_rate_a=metrics_a.pass_rate,
            pass_rate_b=metrics_b.pass_rate,
            pass_rate_delta=round(metrics_b.pass_rate - metrics_a.pass_rate, 2),
            p50_latency_delta_ms=round(metrics_b.p50_latency_ms - metrics_a.p50_latency_ms, 2),
            p90_latency_delta_ms=round(metrics_b.p90_latency_ms - metrics_a.p90_latency_ms, 2),
            total_tasks_a=metrics_a.total_tasks,
            total_tasks_b=metrics_b.total_tasks,
            task_changes=task_changes,
        )
