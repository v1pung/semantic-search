from datetime import datetime

from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    task_id: str
    status: str
    started_at: datetime = Field(..., description="UTC timestamp when the task was enqueued")
