from abc import ABC, abstractmethod
from datetime import datetime


class AbstractStatsRepository(ABC):
    @abstractmethod
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
    ) -> None: ...
