import asyncio
import logging

from celery.signals import worker_process_init, worker_process_shutdown
from qdrant_client import AsyncQdrantClient

from src.core.config import get_settings
from src.infrastructure.csv.data_loader import CsvDataLoader
from src.infrastructure.embedder.embedder import SentenceTransformerEmbedder
from src.infrastructure.qdrant.vector_store import QdrantVectorStore
from src.services.ingest_service import IngestService
from src.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

# Process-level singletons
# Initialised once per worker process in worker_process_init (after fork).
# Using a persistent event loop avoids the "Event loop is closed" error that
# occurs when asyncio.run() destroys the loop after each task, invalidating
# the httpx connection pool inside AsyncQdrantClient.

_loop: asyncio.AbstractEventLoop | None = None
_qdrant_client: AsyncQdrantClient | None = None
_embedder: SentenceTransformerEmbedder | None = None


@worker_process_init.connect
def init_worker_process(**kwargs) -> None:  # type: ignore[type-arg]
    """Create a persistent event loop and Qdrant client once per worker process."""

    global _loop, _qdrant_client
    settings = get_settings()
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    # Client is created after set_event_loop so httpx binds to the right loop.
    _qdrant_client = AsyncQdrantClient(
        host=settings.QDRANT_HOST, port=settings.QDRANT_PORT
    )
    logger.info(
        "Worker process initialised: persistent event loop and Qdrant client ready"
    )


@worker_process_shutdown.connect
def shutdown_worker_process(**kwargs) -> None:  # type: ignore[type-arg]
    """Gracefully close the Qdrant client and event loop on worker exit."""

    global _loop, _qdrant_client
    if _qdrant_client is not None and _loop is not None and not _loop.is_closed():
        _loop.run_until_complete(_qdrant_client.close())
    if _loop is not None and not _loop.is_closed():
        _loop.close()
    logger.info("Worker process shutdown: event loop and Qdrant client closed")


def _get_embedder(model_name: str) -> SentenceTransformerEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformerEmbedder(model_name)
    return _embedder


@celery_app.task(name="ingest_data", bind=True)
def ingest_data(self) -> dict:  # type: ignore[type-arg]
    """Celery wrapper: resolves dependencies and delegates to IngestService."""

    assert _loop is not None and _qdrant_client is not None, (
        "Worker process not initialised — worker_process_init signal not fired"
    )
    settings = get_settings()
    service = IngestService(
        loader=CsvDataLoader(settings.CSV_PATH),
        embedder=_get_embedder(settings.EMBEDDING_MODEL),
        vector_store=QdrantVectorStore(_qdrant_client, settings.QDRANT_COLLECTION),
    )
    # run_until_complete keeps the loop open; the Qdrant client reuses its
    # httpx connection pool across consecutive task invocations.
    return _loop.run_until_complete(service.run())
