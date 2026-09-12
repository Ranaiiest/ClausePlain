"""Grounded Q&A over the uploaded document using the same vector index."""
from __future__ import annotations

from src.embeddings.embedder import Embedder
from src.embeddings.vectordb import VectorStore
from src.llm.engine import LLMEngine
from src.product.prompts import CHAT_SYSTEM, CHAT_USER
from src.product.schemas import ChatTurn
from src.utils.config import RetrievalConfig


class DocumentChat:
    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        llm: LLMEngine,
        retrieval: RetrievalConfig,
        chat_max_tokens: int = 1024,
    ):
        self.embedder = embedder
        self.vector_store = vector_store
        self.llm = llm
        self.retrieval = retrieval
        self.chat_max_tokens = chat_max_tokens

    def answer(
        self,
        contract_id: str,
        title: str,
        question: str,
        history: list[ChatTurn] | None = None,
    ) -> tuple[str, float]:
        embedding = self.embedder.embed_query(question)
        hits = self.vector_store.query(
            query_embedding=embedding,
            top_k=max(self.retrieval.top_k, 5),
            contract_id=contract_id,
        )
        context = "\n\n---\n\n".join(
            f"[Passage {h.chunk_index}]\n{h.text.strip()}" for h in hits
        ) or "(No matching passages.)"

        history_lines = []
        for turn in (history or [])[-6:]:
            label = "User" if turn.role == "user" else "Assistant"
            history_lines.append(f"{label}: {turn.content}")
        history_text = "\n".join(history_lines) if history_lines else "(none)"

        prompt = f"{CHAT_SYSTEM}\n\n" + CHAT_USER.format(
            title=title,
            context=context,
            history=history_text,
            question=question.strip(),
        )
        response = self.llm.generate(prompt, json_mode=False, max_tokens=self.chat_max_tokens)
        return response.text.strip(), response.latency_seconds
