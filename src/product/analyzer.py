"""RAG context builder + one structured LLM call for a user document."""
from __future__ import annotations

from src.embeddings.embedder import Embedder
from src.embeddings.vectordb import RetrievedChunk, VectorStore
from src.llm.engine import LLMEngine
from src.product.parser import parse_document_analysis
from src.product.prompts import ANALYSIS_SYSTEM, ANALYSIS_USER, RETRIEVAL_QUERIES
from src.product.schemas import DocumentAnalysis
from src.utils.config import RetrievalConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)

_MAX_CONTEXT_CHARS = 18000
_MAX_CHUNKS = 24


class DocumentAnalyzer:
    """Retrieve diverse passages, then extract clauses/terms in a single LLM call."""

    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        llm: LLMEngine,
        retrieval: RetrievalConfig,
        analysis_max_tokens: int = 4096,
    ):
        self.embedder = embedder
        self.vector_store = vector_store
        self.llm = llm
        self.retrieval = retrieval
        self.analysis_max_tokens = analysis_max_tokens

    def gather_context(self, contract_id: str) -> str:
        seen: set[str] = set()
        chunks: list[RetrievedChunk] = []
        per_query = max(self.retrieval.top_k, 3)

        for query in RETRIEVAL_QUERIES:
            embedding = self.embedder.embed_query(query)
            hits = self.vector_store.query(
                query_embedding=embedding,
                top_k=per_query,
                contract_id=contract_id,
            )
            for hit in hits:
                if hit.chunk_id in seen:
                    continue
                seen.add(hit.chunk_id)
                chunks.append(hit)
            if len(chunks) >= _MAX_CHUNKS:
                break

        chunks.sort(key=lambda c: c.chunk_index)
        parts: list[str] = []
        used = 0
        for chunk in chunks[:_MAX_CHUNKS]:
            block = f"[Passage {chunk.chunk_index}]\n{chunk.text.strip()}"
            if used + len(block) > _MAX_CONTEXT_CHARS:
                break
            parts.append(block)
            used += len(block)
        return "\n\n---\n\n".join(parts)

    def analyze(self, contract_id: str, title: str) -> tuple[DocumentAnalysis, float, str]:
        context = self.gather_context(contract_id)
        if not context.strip():
            return (
                DocumentAnalysis(
                    title=title,
                    overview="No searchable text was indexed for this file.",
                ),
                0.0,
                "",
            )

        prompt = ANALYSIS_USER.format(title=title, context=context)
        # Prefix system instructions into the user prompt so json_mode can add its own system.
        full_prompt = f"{ANALYSIS_SYSTEM}\n\n{prompt}"
        response = self.llm.generate(
            full_prompt,
            json_mode=True,
            max_tokens=self.analysis_max_tokens,
        )
        analysis = parse_document_analysis(response.text, fallback_title=title)
        logger.info(
            "Analyzed '{}' in {:.2f}s with model '{}'",
            contract_id,
            response.latency_seconds,
            response.model_name,
        )
        return analysis, response.latency_seconds, response.model_name
