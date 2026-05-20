class DomainError(Exception):
    """Base class for all domain-level errors."""

    pass


class DataLoadError(DomainError):
    """Raised when source data cannot be loaded (file missing, invalid format, etc.)."""

    pass


class EmbeddingError(DomainError):
    """Raised when the embedding model fails to encode text."""

    pass


class VectorStoreError(DomainError):
    """Raised when a vector store operation fails (connection error, query error, etc.)."""

    pass


class StatsError(DomainError):
    """Raised when persisting query statistics fails. Non-fatal — should be caught and logged."""

    pass
