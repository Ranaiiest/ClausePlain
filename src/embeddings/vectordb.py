"""
Vector database abstraction backed by ChromaDB.

Isolating Chroma behind `VectorStore` means retrieval and pipeline code
depend on a small, stable interface (`add_chunks`, `query`) rather than
the Chroma client API directly — swapping to another vector DB (FAISS,
Qdrant, pgvector) later only requires a new implementation of this class.
"""
from __future__ import annotations

from dataclasses import dataclass

import chromadb
from chromadb.config import Settings

from src.preprocessing.schemas import Chunk
from src.utils.config import VectorDBConfig
from src.utils.helpers import ensure_dir
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    """A chunk returned from a similarity search, with its relevance score."""

    chunk_id: str
    contract_id: str
    text: str
    score: float
    chunk_index: int


class VectorStore:
    """Thin wrapper around a persistent ChromaDB collection."""

    def __init__(self, config: VectorDBConfig):
        """
        Args:
            config: Vector DB configuration (collection name, persist dir, metric).
        """
        self.config = config
        ensure_dir(config.persist_directory)

        self._client = chromadb.PersistentClient(
            path=config.persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=config.collection_name,
            metadata={"hnsw:space": config.distance_metric},
        )
        logger.info(
            "Connected to ChromaDB collection '{}' at '{}' ({} existing items).",
            config.collection_name,
            config.persist_directory,
            self._collection.count(),
        )

    def add_chunks(self, chunks: list[Chunk], embeddings) -> None:
        """Insert or update chunks and their embeddings in the vector store.

        Uses `upsert` semantics so re-running ingestion on the same
        contract is idempotent.

        Args:
            chunks: List of `Chunk` objects.
            embeddings: Array-like of shape (len(chunks), embedding_dim),
                aligned positionally with `chunks`.
        """
        if not chunks:
            return

        self._collection.upsert(
            ids=[c.chunk_id for c in chunks],
            embeddings=[e.tolist() for e in embeddings],
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "contract_id": c.contract_id,
                    "chunk_index": c.chunk_index,
                    "start_offset": c.start_offset,
                    "end_offset": c.end_offset,
                }
                for c in chunks
            ],
        )
        logger.debug("Upserted {} chunks into vector store.", len(chunks))

    def query(
        self,
        query_embedding,
        top_k: int,
        contract_id: str | None = None,
    ) -> list[RetrievedChunk]:
        """Run a similarity search against the vector store.

        Args:
            query_embedding: 1D array-like embedding of the query text.
            top_k: Number of nearest neighbors to return.
            contract_id: If provided, restrict the search to chunks
                belonging to this contract only (clause extraction always
                operates within a single contract's chunk space).

        Returns:
            List of `RetrievedChunk`, ordered by descending relevance.
        """
        where_filter = {"contract_id": contract_id} if contract_id else None

        results = self._collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=where_filter,
        )

        retrieved: list[RetrievedChunk] = []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for chunk_id, doc, meta, dist in zip(ids, documents, metadatas, distances):
            # Chroma returns distance; convert to a similarity-like score
            # (1 - cosine_distance) so downstream thresholds read intuitively.
            score = 1.0 - dist
            retrieved.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    contract_id=meta.get("contract_id", ""),
                    text=doc,
                    score=score,
                    chunk_index=meta.get("chunk_index", -1),
                )
            )
        return retrieved

    def contract_has_chunks(self, contract_id: str) -> bool:
        """Check whether any chunks for a contract already exist in the store.

        Used to skip re-embedding on repeated pipeline runs.

        Args:
            contract_id: The contract to check.

        Returns:
            True if at least one chunk exists for this contract.
        """
        result = self._collection.get(where={"contract_id": contract_id}, limit=1)
        return len(result.get("ids", [])) > 0

    def delete_contract(self, contract_id: str) -> None:
        """Remove all chunks belonging to a contract (useful for re-ingestion).

        Args:
            contract_id: The contract whose chunks should be deleted.
        """
        self._collection.delete(where={"contract_id": contract_id})
        logger.debug("Deleted existing chunks for contract '{}'.", contract_id)
