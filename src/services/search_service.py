import asyncio
import logging
from datetime import datetime, timezone
from time import perf_counter

from src.domain.exceptions import StatsError
from src.domain.interfaces.embedder import AbstractEmbedder
from src.domain.interfaces.stats_repository import AbstractStatsRepository
from src.domain.interfaces.vector_store import AbstractVectorStore
from src.schemas.search import SearchResult

logger = logging.getLogger(__name__)


class SearchService:
    """
    Orchestrates semantic search: embeds the query, retrieves top-k results
    from the vector store, and persists request statistics.

    Statistics saving is non-fatal: a StatsError is caught, logged, and the
    search results are returned to the caller regardless.
    """

    def __init__(
        self,
        embedder: AbstractEmbedder,
        vector_store: AbstractVectorStore,
        stats_repo: AbstractStatsRepository,
    ) -> None:
        self._embedder = embedder
        self._vector_store = vector_store
        self._stats_repo = stats_repo

    async def search(self, query: str, top_k: int) -> list[SearchResult]:
        received_at = datetime.now(timezone.utc)
        t0 = perf_counter()

        # sentence-transformers is sync, run in thread pool
        vectors: list[list[float]] = await asyncio.to_thread(
            self._embedder.embed, [query]
        )
        query_vector: list[float] = vectors[0]

        raw_results = await self._vector_store.search(query_vector, top_k)

        search_duration_ms = (perf_counter() - t0) * 1000

        await self._save_stats(query, received_at, search_duration_ms)

        return [
            SearchResult(
                question=r["question"],
                answer=r["answer"],
                score=r["score"],
            )
            for r in raw_results
        ]

    async def _save_stats(
        self,
        query: str,
        received_at: datetime,
        search_duration_ms: float,
    ) -> None:
        """Persist statistics; errors are non-fatal and only logged."""

        try:
            await self._stats_repo.save(query, received_at, search_duration_ms)
        except StatsError:
            logger.exception(
                "Failed to save query statistics — search results unaffected"
            )
