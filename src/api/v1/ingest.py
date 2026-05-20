from fastapi import APIRouter

from src.schemas.ingest import IngestResponse
from src.tasks.ingest_task import ingest_data

router = APIRouter()


@router.get(
    "/ingest",
    response_model=IngestResponse,
    summary="Trigger incremental data ingestion",
    description=(
        "Enqueues a Celery task that syncs the Q&A CSV file into the vector database. "
        "The task is idempotent: unchanged records are skipped, new/modified ones "
        "are (re)embedded, and deleted ones are removed from the collection."
    ),
)
async def trigger_ingest() -> IngestResponse:
    task = ingest_data.delay()
    return IngestResponse(task_id=task.id, status="queued")
