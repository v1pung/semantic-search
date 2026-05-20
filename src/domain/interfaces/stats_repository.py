from abc import ABC, abstractmethod
from datetime import datetime


class AbstractStatsRepository(ABC):
    @abstractmethod
    async def save(
        self,
        user_query: str,
        received_at: datetime,
        search_duration_ms: float,
    ) -> None: ...
