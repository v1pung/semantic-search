"""
Task status endpoint.

GET /tasks/{task_id}  — poll the state of a Celery background task.

Returns PENDING when the task ID is unknown or not yet picked up by a worker,
SUCCESS/FAILURE once the task finishes, and STARTED/RETRY while it runs.
Task results are kept in Redis for CELERY_RESULT_EXPIRES seconds (default 3600).
"""

import logging

from fastapi import APIRouter, HTTPException

from src.schemas.tasks import TaskStatusResponse
from src.tasks.celery_app import celery_app

router = APIRouter(prefix="/tasks", tags=["tasks"])
logger = logging.getLogger(__name__)


@router.get(
    "/{task_id}",
    response_model=TaskStatusResponse,
    summary="Get background task status",
    description=(
        "Returns the current state of a Celery task by its ID. "
        "The task ID is returned by POST /ingest in the `task_id` field. "
        "Possible states: PENDING (unknown / queued), STARTED (running), "
        "SUCCESS (finished), FAILURE (crashed), RETRY (being retried), REVOKED (cancelled). "
        "Results are available for CELERY_RESULT_EXPIRES seconds after completion."
    ),
)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    result = celery_app.AsyncResult(task_id)

    try:
        status = result.status  # never raises
    except Exception as exc:
        logger.error("Failed to fetch task status for %s: %s", task_id, exc)
        raise HTTPException(status_code=502, detail="Could not reach task backend") from exc

    task_result = None
    error: str | None = None

    if status == "SUCCESS":
        task_result = result.result
    elif status == "FAILURE":
        exc = result.result  # the exception instance stored by Celery
        error = str(exc) if exc is not None else "Task failed with unknown error"
        logger.warning("Task %s failed: %s", task_id, error)

    return TaskStatusResponse(
        task_id=task_id,
        status=status,
        result=task_result,
        error=error,
    )
