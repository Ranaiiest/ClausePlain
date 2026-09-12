"""Upload size limits and user-facing rejection errors."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.utils.config import UploadConfig


class UploadRejectedError(ValueError):
    """User-facing rejection (size, length, or not a legal document)."""


class FileTooLargeError(UploadRejectedError):
    pass


class DocumentTooLongError(UploadRejectedError):
    pass


class NotLegalDocumentError(UploadRejectedError):
    def __init__(self, message: str, reason: str = ""):
        super().__init__(message)
        self.reason = reason or message


@dataclass(frozen=True)
class SizeCheck:
    bytes: int
    max_bytes: int
    pages: int | None = None


def max_file_bytes(config: UploadConfig) -> int:
    return int(config.max_file_mb * 1024 * 1024)


def validate_file_size(path: str | Path, config: UploadConfig, size_bytes: int | None = None) -> int:
    file_path = Path(path)
    nbytes = int(size_bytes if size_bytes is not None else file_path.stat().st_size)
    limit = max_file_bytes(config)
    if nbytes > limit:
        raise FileTooLargeError(
            f"This file is {nbytes / (1024 * 1024):.1f} MB. "
            f"The limit is {config.max_file_mb:g} MB. Please upload a shorter document."
        )
    return nbytes


def validate_page_count(page_count: int, config: UploadConfig) -> None:
    if page_count > config.max_pages:
        raise DocumentTooLongError(
            f"This PDF has {page_count} pages. The limit is {config.max_pages} pages."
        )


def validate_word_count(word_count: int, config: UploadConfig) -> None:
    if word_count > config.max_words:
        raise DocumentTooLongError(
            f"This document has {word_count:,} words. The limit is {config.max_words:,} words."
        )
