from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings
from src.core.config import get_settings
from src.domain.interfaces.embedder import AbstractEmbedder
from src.domain.interfaces.stats_repository import AbstractStatsRepository
from src.domain.interfaces.vector_store import AbstractVectorStore
from src.infrastructure.csv.data_loader import CsvDataLoader
from src.infrastructure.embedder.embedder import SentenceTransformerEmbedder
from src.infrastructure.postgres.base import get_db as _get_db
from src.infrastructure.postgres.repositories.stats import StatsRepository
from src.infrastructure.qdrant.vector_store import QdrantVectorStore
from src.services.ingest_service import IngestService
from src.services.search_service import SearchService


# Process-level singletons (expensive to create)


@lru_cache(maxsize=1)
def _qdrant_client_singleton(host: str, port: int) -> AsyncQdrantClient:
    return AsyncQdrantClient(host=host, port=port)


@lru_cache(maxsize=1)
def _embedder_singleton(model_name: str) -> SentenceTransformerEmbedder:
    return SentenceTransformerEmbedder(model_name)


# FastAPI dependency providers


def get_qdrant_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncQdrantClient:
    return _qdrant_client_singleton(settings.QDRANT_HOST, settings.QDRANT_PORT)


def get_vector_store(
    settings: Annotated[Settings, Depends(get_settings)],
    client: Annotated[AsyncQdrantClient, Depends(get_qdrant_client)],
) -> AbstractVectorStore:
    return QdrantVectorStore(client, settings.QDRANT_COLLECTION)


def get_embedder(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AbstractEmbedder:
    return _embedder_singleton(settings.EMBEDDING_MODEL)


async def _db_session(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncGenerator[AsyncSession, None]:
    async for session in _get_db(settings.POSTGRES_URL):
        yield session


async def get_stats_repository(
    session: Annotated[AsyncSession, Depends(_db_session)],
) -> AbstractStatsRepository:
    return StatsRepository(session)


def get_search_service(
    embedder: Annotated[AbstractEmbedder, Depends(get_embedder)],
    vector_store: Annotated[AbstractVectorStore, Depends(get_vector_store)],
    stats_repo: Annotated[AbstractStatsRepository, Depends(get_stats_repository)],
) -> SearchService:
    return SearchService(embedder, vector_store, stats_repo)


def get_ingest_service(
    settings: Annotated[Settings, Depends(get_settings)],
    embedder: Annotated[AbstractEmbedder, Depends(get_embedder)],
    vector_store: Annotated[AbstractVectorStore, Depends(get_vector_store)],
) -> IngestService:
    return IngestService(
        loader=CsvDataLoader(settings.CSV_PATH),
        embedder=embedder,
        vector_store=vector_store,
    )


# Warmup helpers (called from lifespan)


def warmup_embedder(model_name: str) -> SentenceTransformerEmbedder:
    """Pre-load the embedding model into the lru_cache at startup."""
    return _embedder_singleton(model_name)


def warmup_qdrant_client(host: str, port: int) -> AsyncQdrantClient:
    """Pre-create the Qdrant client at startup."""
    return _qdrant_client_singleton(host, port)
