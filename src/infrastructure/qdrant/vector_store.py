import hashlib
from uuid import NAMESPACE_URL, UUID, uuid5

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    PointIdsList,
    PointStruct,
    VectorParams,
)

from src.domain.entities import VectorPoint
from src.domain.exceptions import VectorStoreError
from src.domain.interfaces.vector_store import AbstractVectorStore


class QdrantVectorStore(AbstractVectorStore):
    """Qdrant-backed implementation of AbstractVectorStore."""

    def __init__(self, client: AsyncQdrantClient, collection_name: str) -> None:
        self._client = client
        self._collection_name = collection_name

    # ── Static helpers ──────────────────────────────────────────────────────

    @staticmethod
    def get_point_id(question: str) -> str:
        """Stable UUID5 derived from the question text — guarantees uniqueness."""
        return str(uuid5(NAMESPACE_URL, question))

    @staticmethod
    def get_content_hash(question: str, answer: str) -> str:
        """SHA-256 of the full Q&A pair — detects any content change."""
        payload = f"{question}\n{answer}".encode()
        return hashlib.sha256(payload).hexdigest()

    # ── Collection management ───────────────────────────────────────────────

    async def init_collection(self, vector_size: int) -> None:
        """Create the collection if it does not exist (idempotent)."""
        try:
            existing = {
                c.name for c in (await self._client.get_collections()).collections
            }
            if self._collection_name not in existing:
                await self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=VectorParams(
                        size=vector_size, distance=Distance.COSINE
                    ),
                )
        except Exception as exc:
            raise VectorStoreError("Failed to initialise Qdrant collection") from exc

    # ── Write operations ────────────────────────────────────────────────────

    async def upsert(self, points: list[VectorPoint]) -> None:
        if not points:
            return
        try:
            qdrant_points = [
                PointStruct(
                    id=p.id,
                    vector=p.vector,
                    payload={
                        "question": p.question,
                        "answer": p.answer,
                        "content_hash": p.content_hash,
                    },
                )
                for p in points
            ]
            await self._client.upsert(
                collection_name=self._collection_name,
                points=qdrant_points,
                wait=True,
            )
        except Exception as exc:
            raise VectorStoreError("Failed to upsert points into Qdrant") from exc

    async def delete(self, point_ids: list[str]) -> None:
        if not point_ids:
            return
        try:
            await self._client.delete(
                collection_name=self._collection_name,
                points_selector=PointIdsList(points=point_ids),
            )
        except Exception as exc:
            raise VectorStoreError("Failed to delete points from Qdrant") from exc

    # ── Read operations ─────────────────────────────────────────────────────

    async def get_all_with_hash(self) -> dict[str, str]:
        """Scroll through the entire collection and return {point_id: content_hash}."""
        result: dict[str, str] = {}
        next_offset: str | UUID | None = None

        try:
            while True:
                records, next_offset = await self._client.scroll(
                    collection_name=self._collection_name,
                    with_payload=["content_hash"],
                    with_vectors=False,
                    limit=100,
                    offset=next_offset,
                )
                for record in records:
                    if record.payload and "content_hash" in record.payload:
                        result[str(record.id)] = record.payload["content_hash"]

                if next_offset is None:
                    break
        except Exception as exc:
            raise VectorStoreError("Failed to scroll Qdrant collection") from exc

        return result

    async def search(self, query_vector: list[float], top_k: int = 5) -> list[dict]:
        """Return top-k most similar Q&A pairs with their similarity scores."""
        try:
            result = await self._client.query_points(
                collection_name=self._collection_name,
                query=query_vector,
                limit=top_k,
                with_payload=True,
            )
            return [
                {
                    "question": hit.payload.get("question", ""),
                    "answer": hit.payload.get("answer", ""),
                    "score": hit.score,
                }
                for hit in result.points
            ]
        except Exception as exc:
            raise VectorStoreError("Failed to search Qdrant collection") from exc
