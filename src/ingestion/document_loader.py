"""Load user-uploaded legal files (PDF or plain text) into a Contract."""
from __future__ import annotations

from pathlib import Path

from src.ingestion.limits import validate_file_size, validate_word_count
from src.ingestion.pdf_loader import PDFLoader
from src.ingestion.schemas import Contract
from src.utils.config import UploadConfig
from src.utils.helpers import slugify, stable_hash


def load_legal_document(
    path: str | Path,
    contract_id: str | None = None,
    upload_config: UploadConfig | None = None,
    size_bytes: int | None = None,
) -> Contract:
    """Dispatch by file extension after enforcing size limits."""
    config = upload_config or UploadConfig()
    file_path = Path(path)
    validate_file_size(file_path, config, size_bytes=size_bytes)

    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        contract = PDFLoader(upload_config=config).load(str(file_path), contract_id=contract_id)
    elif suffix in {".txt", ".md"}:
        text = file_path.read_text(encoding="utf-8", errors="replace").strip()
        if not text:
            raise ValueError(f"No text found in '{file_path}'.")
        title = file_path.stem
        cid = contract_id or f"{slugify(title)}_{stable_hash(text[:2000], 8)}"
        contract = Contract(
            contract_id=cid,
            title=title,
            raw_text=text,
            source_format="text",
            source_path=str(file_path),
            page_count=1,
        )
    else:
        raise ValueError(
            f"Unsupported file type '{suffix}'. Upload a PDF or a .txt legal document."
        )

    validate_word_count(contract.word_count, config)
    return contract
