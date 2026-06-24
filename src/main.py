import asyncio
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from src.api.v1 import api_router
from src.core.config import get_settings
from src.core.logging import configure_logging
from src.dependencies import (
    warmup_embedder,
    warmup_qdrant_client,
)
from src.domain.exceptions import DataLoadError, EmbeddingError, VectorStoreError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()

    # Pre-load embedding model into memory (blocking, done once at startup)
    logger.info(f"Loading embedding model '{settings.EMBEDDING_MODEL}'...")
    embedder = await asyncio.to_thread(warmup_embedder, settings.EMBEDDING_MODEL)
    logger.info(f"Embedding model loaded (dim={embedder.vector_size()})")

    # Ensure the Qdrant collection exists
    client = warmup_qdrant_client(settings.QDRANT_HOST, settings.QDRANT_PORT)
    from src.infrastructure.qdrant.vector_store import QdrantVectorStore

    vector_store = QdrantVectorStore(client, settings.QDRANT_COLLECTION)
    await vector_store.init_collection(embedder.vector_size())
    logger.info(f"Qdrant collection '{settings.QDRANT_COLLECTION}' ready")

    yield

    logger.info("Shutting down")


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title="Semantic Search API",
        description="RAG-based Q&A semantic search powered by Qdrant + sentence-transformers",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix="/api/v1")

    # Expose Prometheus metrics at /metrics
    Instrumentator().instrument(app).expose(app)

    @app.exception_handler(VectorStoreError)
    async def _vector_store_error(
        request: Request, exc: VectorStoreError
    ) -> JSONResponse:
        logger.error(f"VectorStoreError on {request.method} {request.url.path}: {exc}")
        return JSONResponse(
            status_code=503, content={"detail": "Vector store unavailable"}
        )

    @app.exception_handler(EmbeddingError)
    async def _embedding_error(request: Request, exc: EmbeddingError) -> JSONResponse:
        logger.error(f"EmbeddingError on {request.method} {request.url.path}: {exc}")
        return JSONResponse(
            status_code=503, content={"detail": "Embedding service unavailable"}
        )

    @app.exception_handler(DataLoadError)
    async def _data_load_error(request: Request, exc: DataLoadError) -> JSONResponse:
        logger.error(f"DataLoadError on {request.method} {request.url.path}: {exc}")
        return JSONResponse(
            status_code=503, content={"detail": "Data source unavailable"}
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled exception on {request.method} {request.url.path}")
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )

    return app


app = create_app()
