import asyncio
import logging

from src.domain.entities import VectorPoint
from src.domain.interfaces.data_loader import AbstractDataLoader
from src.domain.interfaces.embedder import AbstractEmbedder
from src.domain.interfaces.vector_store import AbstractVectorStore
from src.infrastructure.qdrant.vector_store import QdrantVectorStore

logger = logging.getLogger(__name__)


class IngestService:
    """
    Orchestrates incremental synchronisation of the Q&A source data into
    the vector store.

    Algorithm (two-level check):
      - UUID5(question)           → identity   (is this record known?)
      - sha256(question + answer) → integrity  (has the content changed?)

    Only new or modified records are re-embedded; deleted records are removed.
    Unchanged records are skipped — zero wasted compute.
    """

    def __init__(
        self,
        loader: AbstractDataLoader,
        embedder: AbstractEmbedder,
        vector_store: AbstractVectorStore,
    ) -> None:
        self._loader = loader
        self._embedder = embedder
        self._vector_store = vector_store

    async def run(self) -> dict:
        # Load source data
        pairs = self._loader.load()
        logger.info(f"Loaded {len(pairs)} Q&A pairs from source")

        # Build {point_id: {pair, content_hash}} index from the source
        csv_index: dict[str, dict] = {
            QdrantVectorStore.get_point_id(pair.question): {
                "pair": pair,
                "content_hash": QdrantVectorStore.get_content_hash(
                    pair.question, pair.answer
                ),
            }
            for pair in pairs
        }

        # Ensure collection exists
        await self._vector_store.init_collection(self._embedder.vector_size())

        # Fetch existing points with their stored content hashes
        existing: dict[str, str] = await self._vector_store.get_all_with_hash()

        # Determine which points need (re)embedding: new or changed
        to_upsert_ids = [
            pid
            for pid, data in csv_index.items()
            if pid not in existing or existing[pid] != data["content_hash"]
        ]

        upserted = 0
        if to_upsert_ids:
            questions = [csv_index[pid]["pair"].question for pid in to_upsert_ids]
            # sentence-transformers is sync, run in thread pool
            vectors = await asyncio.to_thread(self._embedder.embed, questions)

            points = [
                VectorPoint(
                    id=pid,
                    vector=vector,
                    question=csv_index[pid]["pair"].question,
                    answer=csv_index[pid]["pair"].answer,
                    content_hash=csv_index[pid]["content_hash"],
                )
                for pid, vector in zip(to_upsert_ids, vectors)
            ]
            await self._vector_store.upsert(points)
            upserted = len(points)
            logger.info(f"Upserted {upserted} points")
        else:
            logger.info("No changes detected — embedding step skipped")

        # Delete stale points (present in store but no longer in source)
        stale_ids = [pid for pid in existing if pid not in csv_index]
        if stale_ids:
            await self._vector_store.delete(stale_ids)
            logger.info(f"Deleted {len(stale_ids)} stale points")

        return {
            "total": len(pairs),
            "upserted": upserted,
            "deleted": len(stale_ids),
            "skipped": len(pairs) - upserted,
        }
