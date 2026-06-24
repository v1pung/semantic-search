from typing import Any

from pydantic import BaseModel, Field


class TaskStatusResponse(BaseModel):
    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(
        ...,
        description=(
            "Celery task state: PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED"
        ),
    )
    result: Any = Field(
        default=None,
        description="Task return value on SUCCESS, error info on FAILURE, None otherwise",
    )
    error: str | None = Field(
        default=None,
        description="Human-readable error message when status is FAILURE",
    )
