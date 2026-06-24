from abc import ABC, abstractmethod

from src.domain.entities import PointMeta, VectorPoint


class AbstractVectorStore(ABC):
    @abstractmethod
    async def init_collection(self, vector_size: int) -> None: ...

    @abstractmethod
    async def upsert(self, points: list[VectorPoint]) -> None: ...

    @abstractmethod
    async def delete(self, point_ids: list[str]) -> None: ...

    @abstractmethod
    async def get_all_with_hash(self) -> dict[str, str]: ...

    @abstractmethod
    async def get_metadata(self) -> dict[str, PointMeta]: ...

    @abstractmethod
    async def search(self, query_vector: list[float], top_k: int) -> list[dict]: ...
