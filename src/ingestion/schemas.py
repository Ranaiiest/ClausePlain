"""Canonical uploaded document model."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class Contract(BaseModel):
    contract_id: str
    title: str
    raw_text: str
    source_format: str
    source_path: Optional[str] = None
    page_count: int = 0

    @property
    def word_count(self) -> int:
        return len(self.raw_text.split())

    @property
    def char_count(self) -> int:
        return len(self.raw_text)
