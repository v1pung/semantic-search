from datetime import datetime

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
    ) -> None:
        try:
            self._session.add(
                QueryStat(
                    user_query=user_query,
                    received_at=received_at,
                    search_duration_ms=search_duration_ms,
                )
            )
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise StatsError("Failed to persist query statistics") from exc
