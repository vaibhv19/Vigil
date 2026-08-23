import uuid
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from vigil.db.connection import get_session
from vigil.db.models import EvalRun, EvalSuite, TaskResult, ToolCall, Anomaly

router = APIRouter()


@router.get("/runs")
def list_runs():
    """Returns a list of all historical eval_runs with suite metadata."""
    with get_session() as session:
        runs = session.scalars(select(EvalRun).order_by(EvalRun.started_at.desc())).all()
        results = []
        for run in runs:
            suite = session.scalar(select(EvalSuite).where(EvalSuite.id == run.suite_id))
            results.append({
                "id": str(run.id),
                "suite_name": suite.name if suite else "Unknown",
                "agent_version": suite.agent_version if suite else "Unknown",
                "status": run.status,
                "total_duration_ms": run.total_duration_ms,
                "total_cost": run.total_cost,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            })
        return results


@router.get("/runs/{run_id}")
def get_run_detail(run_id: str):
    """Returns detailed information for a specific run including task results."""
    try:
        rid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format.")

    with get_session() as session:
        run = session.scalar(select(EvalRun).where(EvalRun.id == rid))
        if not run:
            # Build response data as None to signal not found outside session
            run_data = None
        else:
            suite = session.scalar(select(EvalSuite).where(EvalSuite.id == run.suite_id))
            task_results = session.scalars(
                select(TaskResult).where(TaskResult.run_id == rid)
            ).all()

            tasks = []
            for tr in task_results:
                tasks.append({
                    "id": str(tr.id),
                    "task_id": str(tr.task_id),
                    "status": tr.status,
                    "steps_taken": tr.steps_taken,
                    "failure_reason": tr.failure_reason,
                    "final_output": tr.final_output,
                    "finished_at": tr.finished_at.isoformat() if tr.finished_at else None,
                })

            run_data = {
                "id": str(run.id),
                "suite_name": suite.name if suite else "Unknown",
                "agent_version": suite.agent_version if suite else "Unknown",
                "status": run.status,
                "total_duration_ms": run.total_duration_ms,
                "total_cost": run.total_cost,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "finished_at": run.finished_at.isoformat() if run.finished_at else None,
                "task_results": tasks,
            }

    if run_data is None:
        raise HTTPException(status_code=404, detail="Run not found.")

    return run_data


@router.get("/runs/{run_id}/tasks/{task_result_id}/tools")
def get_tool_calls(run_id: str, task_result_id: str):
    """Returns tool call sequence for a specific task result."""
    try:
        trid = uuid.UUID(task_result_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task result ID format.")

    with get_session() as session:
        calls = session.scalars(
            select(ToolCall).where(ToolCall.task_result_id == trid).order_by(ToolCall.sequence_number)
        ).all()

        return [
            {
                "id": str(c.id),
                "sequence_number": c.sequence_number,
                "tool_name": c.tool_name,
                "input_args": c.input_args,
                "stdout_capture": c.stdout_capture,
                "exit_code": c.exit_code,
                "duration_ms": c.duration_ms,
            }
            for c in calls
        ]


@router.get("/runs/{run_id}/anomalies")
def get_run_anomalies(run_id: str):
    """Returns anomalies flagged during the run."""
    try:
        rid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format.")

    with get_session() as session:
        # Get all task results for this run
        result_ids = [
            r.id for r in session.scalars(
                select(TaskResult).where(TaskResult.run_id == rid)
            ).all()
        ]

        if not result_ids:
            return []

        anomalies = session.scalars(
            select(Anomaly).where(Anomaly.task_result_id.in_(result_ids))
        ).all()

        return [
            {
                "id": str(a.id),
                "task_result_id": str(a.task_result_id),
                "pattern_type": a.pattern_type,
                "severity": a.severity,
                "incident_data": a.incident_data,
                "detected_at": a.detected_at.isoformat() if a.detected_at else None,
            }
            for a in anomalies
        ]
