from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.exceptions import StatsError
from src.domain.interfaces.stats_repository import AbstractStatsRepository
from src.infrastructure.postgres.models.query_stat import QueryStat


class StatsRepository(AbstractStatsRepository):
    """SQLAlchemy-implementation of AbstractStatsRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(
        self,
        user_query: str,
        received_at: datetime,
        search_duration_ms: float,
        *,
        embed_duration_ms: float = 0.0,
        result_count: int = 0,
        top_score: float | None = None,
        status: str = "ok",
        error_message: str | None = None,
    ) -> None:
        now = datetime.now(timezone.utc)
        try:
            self._session.add(
                QueryStat(
                    user_query=user_query,
                    received_at=received_at,
                    search_duration_ms=search_duration_ms,
                    embed_duration_ms=embed_duration_ms,
                    result_count=result_count,
                    top_score=top_score,
                    status=status,
                    error_message=error_message,
                    created_at=now,
                    updated_at=now,
                )
            )
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise StatsError("Failed to persist query statistics") from exc
