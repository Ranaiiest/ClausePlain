"""PDF text extraction into the shared Contract schema."""
from __future__ import annotations

from pathlib import Path

from src.ingestion.limits import DocumentTooLongError, validate_page_count
from src.ingestion.schemas import Contract
from src.utils.config import UploadConfig
from src.utils.helpers import slugify, stable_hash
from src.utils.logger import get_logger

logger = get_logger(__name__)

try:
    import fitz  # PyMuPDF
    _PYMUPDF_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    _PYMUPDF_AVAILABLE = False


class PDFLoader:
    """Extracts plain text from PDF contracts using PyMuPDF."""

    def __init__(self, min_chars: int = 20, upload_config: UploadConfig | None = None):
        self.min_chars = min_chars
        self.upload_config = upload_config or UploadConfig()

    def load(self, pdf_path: str, contract_id: str | None = None) -> Contract:
        """Extract text from a PDF file and wrap it as a `Contract`."""
        if not _PYMUPDF_AVAILABLE:
            raise ImportError(
                "PyMuPDF is not installed. Run `pip install pymupdf` to enable PDF ingestion."
            )

        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found at: {pdf_path}")

        logger.info("Extracting text from PDF: {}", path)
        doc = fitz.open(str(path))
        page_count = doc.page_count
        try:
            validate_page_count(page_count, self.upload_config)
        except DocumentTooLongError:
            doc.close()
            raise

        pages_text = []
        low_yield_pages = 0

        for page in doc:
            text = page.get_text("text")
            if len(text.strip()) < self.min_chars:
                low_yield_pages += 1
            pages_text.append(text)
        doc.close()

        full_text = "\n".join(pages_text).strip()

        if not full_text:
            raise ValueError(
                f"No extractable text found in '{pdf_path}'. "
                "This may be a scanned/image-only PDF requiring OCR (not yet supported)."
            )

        if low_yield_pages:
            logger.warning(
                "{} of {} pages had very little extractable text — possible scan artifacts.",
                low_yield_pages,
                page_count,
            )

        title = path.stem
        cid = contract_id or f"{slugify(title)}_{stable_hash(full_text[:2000], 8)}"
        return Contract(
            contract_id=cid,
            title=title,
            raw_text=full_text,
            source_format="pdf",
            source_path=str(path),
            page_count=page_count,
        )
