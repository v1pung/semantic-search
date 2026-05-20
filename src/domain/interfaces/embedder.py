from abc import ABC, abstractmethod


class AbstractEmbedder(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    def vector_size(self) -> int: ...
