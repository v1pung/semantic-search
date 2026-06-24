from datetime import datetime, timezone

from fastapi import APIRouter, Request

from src.core.rate_limit import limiter
from src.core.config import get_settings
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
        "are (re)embedded, and deleted ones are removed from the collection.\n\n"
        "Rate-limited per IP — default 5 requests/minute "
        "(configurable via RATE_LIMIT_INGEST env var). "
        "Returns 429 with Retry-After header when the limit is exceeded."
    ),
)
@limiter.limit(get_settings().RATE_LIMIT_INGEST)
async def trigger_ingest(request: Request) -> IngestResponse:
    started_at = datetime.now(timezone.utc)
    task = ingest_data.delay()
    return IngestResponse(task_id=task.id, status="queued", started_at=started_at)
