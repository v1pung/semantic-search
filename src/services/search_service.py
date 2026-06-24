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

    Timing is measured at two levels:
      - embed_duration_ms  — sentence-transformers encoding only
      - search_duration_ms — total wall time (embed + vector search)

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
        t_total = perf_counter()

        # sentence-transformers is sync — run in thread pool
        t_embed = perf_counter()
        vectors: list[list[float]] = await asyncio.to_thread(
            self._embedder.embed, [query]
        )
        embed_duration_ms = (perf_counter() - t_embed) * 1000
        query_vector: list[float] = vectors[0]

        raw_results = await self._vector_store.search(query_vector, top_k)
        search_duration_ms = (perf_counter() - t_total) * 1000

        top_score = raw_results[0]["score"] if raw_results else None

        await self._save_stats(
            query=query,
            received_at=received_at,
            search_duration_ms=search_duration_ms,
            embed_duration_ms=embed_duration_ms,
            result_count=len(raw_results),
            top_score=top_score,
        )

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
        embed_duration_ms: float,
        result_count: int,
        top_score: float | None,
        status: str = "ok",
        error_message: str | None = None,
    ) -> None:
        """Persist statistics; errors are non-fatal and only logged."""

        try:
            await self._stats_repo.save(
                query,
                received_at,
                search_duration_ms,
                embed_duration_ms=embed_duration_ms,
                result_count=result_count,
                top_score=top_score,
                status=status,
                error_message=error_message,
            )
        except StatsError:
            logger.exception(
                "Failed to save query statistics — search results unaffected"
            )
