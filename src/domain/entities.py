from dataclasses import dataclass


@dataclass(frozen=True)
class QAPair:
    """A question-answer pair loaded from the source dataset."""

    question: str
    answer: str


@dataclass
class VectorPoint:
    """A point to be stored in the vector database."""

    id: str
    vector: list[float]
    question: str
    answer: str
    content_hash: str
