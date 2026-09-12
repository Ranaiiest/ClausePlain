from pathlib import Path

import pytest

from src.ingestion.document_loader import load_legal_document
from src.ingestion.limits import FileTooLargeError, DocumentTooLongError, validate_file_size
from src.utils.config import UploadConfig


def test_load_text_document(tmp_path: Path):
    path = tmp_path / "offer.txt"
    path.write_text(
        "This Offer Letter is between Acme and Jordan.\nSalary is 90,000 per year.",
        encoding="utf-8",
    )
    contract = load_legal_document(path)
    assert contract.source_format == "text"
    assert "Acme" in contract.raw_text
    assert contract.word_count > 5


def test_rejects_unknown_type(tmp_path: Path):
    path = tmp_path / "scan.png"
    path.write_bytes(b"x")
    with pytest.raises(ValueError, match="Unsupported"):
        load_legal_document(path)


def test_file_size_limit(tmp_path: Path):
    path = tmp_path / "big.txt"
    path.write_bytes(b"a" * 5000)
    config = UploadConfig(max_file_mb=0.001)  # ~1 KB
    with pytest.raises(FileTooLargeError, match="limit"):
        validate_file_size(path, config)


def test_word_count_limit(tmp_path: Path):
    path = tmp_path / "long.txt"
    path.write_text(" ".join(["word"] * 200), encoding="utf-8")
    config = UploadConfig(max_file_mb=10, max_words=50)
    with pytest.raises(DocumentTooLongError, match="words"):
        load_legal_document(path, upload_config=config)
