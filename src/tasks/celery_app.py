from celery import Celery

from src.core.config import get_settings

_settings = get_settings()

celery_app = Celery(
    "semantic_search",
    broker=_settings.REDIS_BROKER_URL,
    backend=_settings.REDIS_BACKEND_URL,
    include=["src.tasks.ingest_task"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Prevent task result accumulation in Redis
    result_expires=3600,
)
