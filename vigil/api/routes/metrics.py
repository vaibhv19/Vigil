import uuid
from fastapi import APIRouter, HTTPException, Query

from vigil.core.exceptions import DatabasePersistenceError
from vigil.eval.metrics import MetricsEngine
from vigil.eval.comparator import RunComparator

router = APIRouter()


@router.get("/runs/{run_id}/summary")
def get_run_metrics(run_id: str):
    """Returns aggregated metrics summary for a specific run."""
    try:
        rid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format.")

    try:
        metrics = MetricsEngine.get_run_metrics(rid)
        return metrics.model_dump()
    except (ValueError, DatabasePersistenceError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/compare")
def compare_runs(
    run_a: str = Query(..., description="Run ID A"),
    run_b: str = Query(..., description="Run ID B"),
):
    """Returns task-by-task differential comparison between two runs."""
    try:
        rid_a = uuid.UUID(run_a)
        rid_b = uuid.UUID(run_b)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format.")

    try:
        comparison = RunComparator.compare_runs(rid_a, rid_b)
        return comparison.model_dump()
    except (ValueError, DatabasePersistenceError) as e:
        raise HTTPException(status_code=404, detail=str(e))

