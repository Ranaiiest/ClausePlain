"""
Adaptive chunking strategy for contract text.

Rationale (from dataset analysis):
    - Average contract: ~8,000 words; largest: ~47,000 words.
    - Sending a full contract into a local 7B LLM's context window is
      not feasible, so retrieval over chunks is mandatory.
    - Small contracts (e.g. one-page joint-filing agreements) don't
      benefit from chunking overhead and can be treated as a single chunk.

Strategy:
    - If word count <= `small_doc_word_threshold`: emit one chunk = whole doc.
    - Otherwise: recursively split on a priority list of separators
      (paragraph breaks -> line breaks -> sentence breaks -> words),
      targeting `chunk_size_tokens` with `chunk_overlap_tokens` overlap,
      approximating tokens via whitespace-word counts (adequate for
      chunk-size purposes; exact tokenization happens inside the LLM/embedder).
"""
from __future__ import annotations

from src.ingestion.schemas import Contract
from src.preprocessing.schemas import Chunk
from src.utils.config import ChunkingConfig
from src.utils.helpers import stable_hash
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AdaptiveChunker:
    """Splits contract text into retrieval-ready chunks, adapting to document size."""

    def __init__(self, config: ChunkingConfig):
        """
        Args:
            config: Chunking configuration (thresholds, sizes, separators).
        """
        self.config = config

    def chunk_contract(self, contract: Contract) -> list[Chunk]:
        """Chunk a single contract's cleaned text.

        Args:
            contract: A `Contract` whose `raw_text` has already been cleaned.

        Returns:
            List of `Chunk` objects covering the full document in order.
        """
        text = contract.raw_text
        word_count = len(text.split())

        if word_count <= self.config.small_doc_word_threshold:
            logger.debug(
                "'{}' has {} words (<= threshold {}); using single chunk.",
                contract.contract_id,
                word_count,
                self.config.small_doc_word_threshold,
            )
            return [self._build_chunk(contract.contract_id, text, 0, len(text), 0)]

        logger.debug(
            "'{}' has {} words; applying recursive chunking (size={}, overlap={}).",
            contract.contract_id,
            word_count,
            self.config.chunk_size_tokens,
            self.config.chunk_overlap_tokens,
        )
        raw_spans = self._recursive_split(text, self.config.separators)
        merged_spans = self._merge_with_overlap(text, raw_spans)

        chunks = [
            self._build_chunk(contract.contract_id, span_text, start, end, idx)
            for idx, (span_text, start, end) in enumerate(merged_spans)
        ]
        logger.info("'{}' chunked into {} chunks.", contract.contract_id, len(chunks))
        return chunks

    # ------------------------------------------------------------------
    # Internal splitting logic
    # ------------------------------------------------------------------

    def _recursive_split(self, text: str, separators: list[str]) -> list[tuple[str, int, int]]:
        """Recursively split text on the first separator that yields small-enough pieces.

        Returns:
            List of (span_text, start_offset, end_offset) covering the input text.
        """
        target_words = self.config.chunk_size_tokens

        def word_len(s: str) -> int:
            return len(s.split())

        def split_on(text_piece: str, base_offset: int, seps: list[str]) -> list[tuple[str, int, int]]:
            if word_len(text_piece) <= target_words or not seps:
                if not text_piece:
                    return []
                return [(text_piece, base_offset, base_offset + len(text_piece))]

            sep = seps[0]
            remaining_seps = seps[1:]

            if sep == "":
                # Last resort: hard split by words.
                return self._hard_split_by_words(text_piece, base_offset, target_words)

            parts = text_piece.split(sep)
            spans: list[tuple[str, int, int]] = []
            cursor = base_offset
            for i, part in enumerate(parts):
                part_with_sep = part + (sep if i < len(parts) - 1 else "")
                if word_len(part_with_sep) > target_words:
                    spans.extend(split_on(part_with_sep, cursor, remaining_seps))
                elif part_with_sep:
                    spans.append((part_with_sep, cursor, cursor + len(part_with_sep)))
                cursor += len(part_with_sep)
            return spans

        return split_on(text, 0, separators)

    def _hard_split_by_words(
        self, text_piece: str, base_offset: int, target_words: int
    ) -> list[tuple[str, int, int]]:
        """Fallback: split a long run-on piece by raw word count."""
        words = text_piece.split(" ")
        spans = []
        cursor = base_offset
        buf: list[str] = []
        for w in words:
            buf.append(w)
            if len(buf) >= target_words:
                span_text = " ".join(buf)
                spans.append((span_text, cursor, cursor + len(span_text)))
                cursor += len(span_text) + 1
                buf = []
        if buf:
            span_text = " ".join(buf)
            spans.append((span_text, cursor, cursor + len(span_text)))
        return spans

    def _merge_with_overlap(
        self, full_text: str, spans: list[tuple[str, int, int]]
    ) -> list[tuple[str, int, int]]:
        """Merge small adjacent spans up to target size, then apply overlap.

        The recursive splitter can over-fragment text (e.g. many short
        clauses). This pass greedily merges consecutive spans until the
        target chunk size is reached, then prepends the tail of the
        previous chunk to create the configured overlap.
        """
        target_words = self.config.chunk_size_tokens
        overlap_words = self.config.chunk_overlap_tokens

        merged: list[tuple[str, int, int]] = []
        buf_text = ""
        buf_start = None

        for span_text, start, end in spans:
            if buf_start is None:
                buf_start = start
            candidate = (buf_text + span_text) if buf_text else span_text
            if len(candidate.split()) > target_words and buf_text:
                merged.append((buf_text, buf_start, buf_start + len(buf_text)))
                buf_text = span_text
                buf_start = start
            else:
                buf_text = candidate

        if buf_text:
            merged.append((buf_text, buf_start, buf_start + len(buf_text)))

        if overlap_words <= 0 or len(merged) <= 1:
            return merged

        overlapped: list[tuple[str, int, int]] = [merged[0]]
        for i in range(1, len(merged)):
            prev_text, _, _ = overlapped[-1]
            curr_text, curr_start, curr_end = merged[i]
            prev_tail_words = prev_text.split()[-overlap_words:]
            prefix = " ".join(prev_tail_words) + " "
            new_start = max(curr_start - len(prefix), 0)
            overlapped.append((prefix + curr_text, new_start, curr_end))

        return overlapped

    def _build_chunk(
        self, contract_id: str, text: str, start: int, end: int, index: int
    ) -> Chunk:
        chunk_id = f"{contract_id}__chunk_{index}__{stable_hash(text)}"
        return Chunk(
            chunk_id=chunk_id,
            contract_id=contract_id,
            text=text.strip(),
            start_offset=start,
            end_offset=end,
            chunk_index=index,
        )
