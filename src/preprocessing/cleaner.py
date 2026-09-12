"""Text normalization for raw contract text.

Legal PDFs commonly contain extra whitespace, page numbers, and
non-standard unicode. Cleaning here does not try to preserve layout.
"""
from __future__ import annotations

import re
import unicodedata

from src.utils.logger import get_logger

logger = get_logger(__name__)


class TextCleaner:
    """Applies a configurable sequence of normalization steps to raw text."""

    _MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
    _MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
    _PAGE_NUMBER_RE = re.compile(r"^\s*(page\s+)?\d+\s*(of\s*\d+)?\s*$", re.IGNORECASE)
    _CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

    def __init__(self, strip_page_numbers: bool = True):
        """
        Args:
            strip_page_numbers: If True, drop lines that look like
                standalone page numbers (e.g. "Page 3 of 12").
        """
        self.strip_page_numbers = strip_page_numbers

    def clean(self, text: str) -> str:
        """Run the full normalization pipeline on a block of text.

        Steps applied in order:
            1. Unicode normalization (NFKC) to fold odd glyph variants.
            2. Strip control characters.
            3. Optionally drop standalone page-number lines.
            4. Collapse repeated spaces/tabs and excessive blank lines.
            5. Trim trailing whitespace per line and overall.

        Args:
            text: Raw contract text.

        Returns:
            Normalized text.
        """
        if not text:
            return ""

        text = unicodedata.normalize("NFKC", text)
        text = self._CONTROL_CHARS_RE.sub("", text)

        lines = text.split("\n")
        if self.strip_page_numbers:
            lines = [ln for ln in lines if not self._PAGE_NUMBER_RE.match(ln.strip())]
        text = "\n".join(lines)

        text = self._MULTI_SPACE_RE.sub(" ", text)
        text = self._MULTI_NEWLINE_RE.sub("\n\n", text)
        text = "\n".join(line.rstrip() for line in text.split("\n"))

        return text.strip()

    def clean_contract_text(self, contract_id: str, text: str) -> str:
        """Clean text with contract-level logging for observability.

        Args:
            contract_id: Identifier used for log correlation.
            text: Raw contract text.

        Returns:
            Normalized text.
        """
        before_len = len(text)
        cleaned = self.clean(text)
        after_len = len(cleaned)
        logger.debug(
            "Cleaned '{}' | {} -> {} chars ({:+d})",
            contract_id,
            before_len,
            after_len,
            after_len - before_len,
        )
        return cleaned
