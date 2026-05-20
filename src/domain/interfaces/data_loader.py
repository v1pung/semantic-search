from abc import ABC, abstractmethod

from src.domain.entities import QAPair


class AbstractDataLoader(ABC):
    @abstractmethod
    def load(self) -> list[QAPair]: ...
