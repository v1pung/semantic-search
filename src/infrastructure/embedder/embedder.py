from sentence_transformers import SentenceTransformer

from src.domain.exceptions import EmbeddingError
from src.domain.interfaces.embedder import AbstractEmbedder


class SentenceTransformerEmbedder(AbstractEmbedder):
    """Sentence-transformers implementation of AbstractEmbedder.

    Instantiate once per process and reuse - model loading is expensive.
    """

    def __init__(self, model_name: str) -> None:
        try:
            self._model: SentenceTransformer = SentenceTransformer(model_name)
        except Exception as exc:
            raise EmbeddingError(
                f"Failed to load embedding model '{model_name}'"
            ) from exc

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts into L2-normalised vectors (cosine ≡ dot product)."""
        
        try:
            embeddings = self._model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return embeddings.tolist()
        except Exception as exc:
            raise EmbeddingError("Failed to embed texts") from exc

    def vector_size(self) -> int:
        return self._model.get_embedding_dimension()
