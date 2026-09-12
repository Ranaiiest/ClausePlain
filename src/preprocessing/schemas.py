"""Data model for a single chunk of a contract."""
from __future__ import annotations

from pydantic import BaseModel


class Chunk(BaseModel):
    """A contiguous span of a contract's text, ready for embedding.

    Attributes:
        chunk_id: Deterministic, unique ID (derived from contract_id + offsets).
        contract_id: ID of the parent contract.
        text: The chunk's text content.
        start_offset: Character offset where this chunk begins in the
            *cleaned* contract text.
        end_offset: Character offset where this chunk ends (exclusive).
        chunk_index: Sequential position of this chunk within the contract.
    """

    chunk_id: str
    contract_id: str
    text: str
    start_offset: int
    end_offset: int
    chunk_index: int
