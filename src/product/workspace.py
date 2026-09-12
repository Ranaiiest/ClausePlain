"""End-to-end workspace: ingest a user PDF/text file, analyze, then chat."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.embeddings.embedder import Embedder, get_shared_embedder
from src.embeddings.vectordb import VectorStore
from src.ingestion.document_loader import load_legal_document
from src.ingestion.limits import NotLegalDocumentError
from src.ingestion.schemas import Contract
from src.llm.engine import build_llm_engine
from src.preprocessing.chunker import AdaptiveChunker
from src.preprocessing.cleaner import TextCleaner
from src.product.analyzer import DocumentAnalyzer
from src.product.chat import DocumentChat
from src.product.gate import classify_legal_text
from src.product.schemas import ChatTurn, DocumentAnalysis
from src.utils.config import AppConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AnalyzeResult:
    contract: Contract | None
    analysis: DocumentAnalysis | None
    latency_seconds: float
    model_name: str
    rejected: bool
    rejection_reason: str = ""


class DocumentWorkspace:
    """Product pipeline without any labeled dataset."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.cleaner = TextCleaner()
        self.chunker = AdaptiveChunker(config.chunking)
        self.embedder: Embedder = get_shared_embedder(config.embedding)
        self.vector_store = VectorStore(config.vectordb)
        self.llm = build_llm_engine(config.llm)
        self.analyzer = DocumentAnalyzer(
            self.embedder,
            self.vector_store,
            self.llm,
            config.retrieval,
            analysis_max_tokens=config.llm.analysis_max_tokens,
        )
        self.chat = DocumentChat(
            self.embedder,
            self.vector_store,
            self.llm,
            config.retrieval,
            chat_max_tokens=config.llm.chat_max_tokens,
        )

    def load_file(self, path: str | Path, size_bytes: int | None = None) -> Contract:
        return load_legal_document(path, upload_config=self.config.upload, size_bytes=size_bytes)

    def ingest(self, contract: Contract, force_reembed: bool = True) -> Contract:
        cleaned = self.cleaner.clean_contract_text(contract.contract_id, contract.raw_text)
        contract = contract.model_copy(update={"raw_text": cleaned})

        if self.vector_store.contract_has_chunks(contract.contract_id) and force_reembed:
            self.vector_store.delete_contract(contract.contract_id)
        elif self.vector_store.contract_has_chunks(contract.contract_id) and not force_reembed:
            return contract

        chunks = self.chunker.chunk_contract(contract)
        embeddings = self.embedder.embed_texts([c.text for c in chunks])
        self.vector_store.add_chunks(chunks, embeddings)
        logger.info("Indexed {} chunks for '{}'.", len(chunks), contract.contract_id)
        return contract

    def analyze_file(self, path: str | Path, size_bytes: int | None = None) -> AnalyzeResult:
        contract = self.load_file(path, size_bytes=size_bytes)
        gate = classify_legal_text(contract.raw_text)
        if not gate.is_legal:
            logger.info("Rejected '{}' as non-legal: {}", contract.title, gate.reason)
            raise NotLegalDocumentError(gate.reason, reason=gate.reason)

        contract = self.ingest(contract)
        analysis, latency, model = self.analyzer.analyze(contract.contract_id, contract.title)
        if analysis.is_legal_document is False:
            reason = analysis.rejection_reason or "Not a legal document."
            logger.info("Model flagged '{}' as non-legal: {}", contract.title, reason)
            return AnalyzeResult(
                contract=contract,
                analysis=analysis,
                latency_seconds=latency,
                model_name=model,
                rejected=True,
                rejection_reason=reason,
            )
        return AnalyzeResult(
            contract=contract,
            analysis=analysis,
            latency_seconds=latency,
            model_name=model,
            rejected=False,
        )

    def ask(
        self,
        contract_id: str,
        title: str,
        question: str,
        history: list[ChatTurn] | None = None,
    ) -> tuple[str, float]:
        return self.chat.answer(contract_id, title, question, history)
