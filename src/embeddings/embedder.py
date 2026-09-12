"""
Embedding generation using Sentence Transformers.

Wraps `BAAI/bge-small-en-v1.5` (or any Sentence-Transformers-compatible
model) behind a small interface so the embedding backend can be swapped
(e.g. for a larger BGE variant, or an API-based embedder) without
touching retrieval or vector-store code.
"""
from __future__ import annotations

import numpy as np

from src.utils.ssl_certs import configure_ssl_for_corporate_proxy

configure_ssl_for_corporate_proxy()

from sentence_transformers import SentenceTransformer

from src.utils.config import EmbeddingConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Embedder:
    """Generates dense vector embeddings for text using Sentence Transformers."""

    def __init__(self, config: EmbeddingConfig):
        """
        Args:
            config: Embedding configuration (model name, device, batch size).
        """
        self.config = config
        logger.info(
            "Loading embedding model '{}' on device '{}'",
            config.model_name,
            config.device,
        )
        self._model = SentenceTransformer(config.model_name, device=config.device)

    @property
    def dimension(self) -> int:
        """Return the output embedding vector dimension for this model."""
        return self._model.get_sentence_embedding_dimension()

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of texts.

        Args:
            texts: List of raw text strings.

        Returns:
            A numpy array of shape (len(texts), embedding_dim).
        """
        if not texts:
            return np.empty((0, self.dimension))

        embeddings = self._model.encode(
            texts,
            batch_size=self.config.batch_size,
            normalize_embeddings=self.config.normalize_embeddings,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return embeddings

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query string (e.g. a clause description used for retrieval).

        BGE models recommend prefixing retrieval *queries* (not documents)
        with an instruction string for best performance; this is applied here.

        Args:
            query: The query text.

        Returns:
            A 1D numpy array of shape (embedding_dim,).
        """
        prefixed = self._apply_query_instruction(query)
        return self.embed_texts([prefixed])[0]

    def _apply_query_instruction(self, query: str) -> str:
        """Apply BGE's recommended query instruction prefix, if applicable."""
        if "bge" in self.config.model_name.lower():
            return f"Represent this sentence for searching relevant passages: {query}"
        return query


_SHARED_EMBEDDER_CACHE: dict[str, Embedder] = {}


def get_shared_embedder(config: EmbeddingConfig) -> Embedder:
    """Return a process-wide cached `Embedder` instance for the given model.

    Loading a Sentence Transformers model is expensive; this avoids
    reloading it across every pipeline stage within the same process.
    Keyed by model_name+device so switching models via config still works.

    Args:
        config: Embedding configuration.

    Returns:
        A shared `Embedder` instance.
    """
    key = f"{config.model_name}::{config.device}"
    if key not in _SHARED_EMBEDDER_CACHE:
        _SHARED_EMBEDDER_CACHE[key] = Embedder(config)
    return _SHARED_EMBEDDER_CACHE[key]
