from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class QAPair:
    """A question-answer pair loaded from the source dataset."""

    question: str
    answer: str


@dataclass(frozen=True)
class PointMeta:
    """Metadata stored alongside each vector point in the vector store."""

    content_hash: str
    created_at: datetime


@dataclass
class VectorPoint:
    """A point to be stored in the vector database."""

    id: str
    vector: list[float]
    question: str
    answer: str
    content_hash: str
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)
