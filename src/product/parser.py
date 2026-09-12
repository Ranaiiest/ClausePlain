"""Parse LLM JSON into a DocumentAnalysis without crashing on messy output."""
from __future__ import annotations

import json

from pydantic import ValidationError

from src.product.schemas import DocumentAnalysis
from src.utils.helpers import extract_json_block
from src.utils.logger import get_logger

logger = get_logger(__name__)


def parse_document_analysis(raw_llm_text: str, fallback_title: str = "") -> DocumentAnalysis:
    """Validate analysis JSON; return a safe empty analysis on failure."""
    json_block = extract_json_block(raw_llm_text)
    try:
        data = json.loads(json_block)
        if not isinstance(data, dict):
            raise TypeError("Expected a JSON object")
        analysis = DocumentAnalysis(**data)
    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
        logger.warning("Failed to parse document analysis: {}. Raw: {}", exc, raw_llm_text[:400])
        return DocumentAnalysis(
            title=fallback_title,
            overview=(
                "We could not structure this document on the first pass. "
                "Try asking a question in chat — answers still use the uploaded text."
            ),
            watch_outs=["Structured extraction returned incomplete JSON. Chat still works."],
        )

    if not analysis.title:
        analysis.title = fallback_title
    if analysis.is_legal_document is False and not analysis.rejection_reason:
        analysis.rejection_reason = "Not a legal document."
    return analysis
