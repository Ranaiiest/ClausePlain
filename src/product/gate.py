"""Fast heuristic: is this text a legal instrument the user uploaded to understand?"""
from __future__ import annotations

from dataclasses import dataclass

LEGAL_CUES = (
    "agreement",
    "hereby",
    "whereas",
    "hereinafter",
    "notwithstanding",
    "the parties",
    "this contract",
    "this agreement",
    "terms and conditions",
    "governing law",
    "indemnif",
    "confidential",
    "non-disclosure",
    "non disclosure",
    "nda",
    "jurisdiction",
    "arbitration",
    "force majeure",
    "in witness",
    "executed as of",
    "effective date",
    "consideration",
    "liability",
    "warranty",
    "covenant",
    "severability",
    "assignment",
    "termination",
    "intellectual property",
    "non-compete",
    "noncompete",
    "at-will",
    "at will employment",
    "offer letter",
    "offer of employment",
    "employer",
    "employee",
    "lessor",
    "lessee",
    "landlord",
    "tenant",
    "plaintiff",
    "defendant",
    "petitioner",
    "respondent",
    "court order",
    "affidavit",
    "hereinafter referred",
    "shall mean",
    "subject to the terms",
    "in consideration of",
    "notice period",
    "probation",
    "compensation",
    "salary",
    "equity grant",
    "stock option",
    "data protection",
    "privacy policy",
    "master services",
    "statement of work",
    "licensee",
    "licensor",
)


@dataclass(frozen=True)
class LegalGateResult:
    is_legal: bool
    confidence: float
    reason: str
    matched_cues: tuple[str, ...]


def classify_legal_text(text: str, *, min_words: int = 40) -> LegalGateResult:
    """Return whether the text looks like a legal document, without calling an LLM."""
    cleaned = (text or "").strip()
    words = cleaned.split()
    if len(words) < min_words:
        return LegalGateResult(
            is_legal=False,
            confidence=0.9,
            reason="This file is too short to be a usable legal document.",
            matched_cues=(),
        )

    lowered = cleaned.lower()
    hits = tuple(cue for cue in LEGAL_CUES if cue in lowered)
    score = len(hits)

    if score == 0:
        return LegalGateResult(
            is_legal=False,
            confidence=0.92,
            reason="Not a legal document. Upload a contract, offer letter, NDA, court paper, or similar legal file.",
            matched_cues=(),
        )

    # A long article that mentions "court" once is not an instrument.
    if score == 1 and len(words) > 350:
        return LegalGateResult(
            is_legal=False,
            confidence=0.75,
            reason="Not a legal document. The text only mentions legal language in passing.",
            matched_cues=hits,
        )

    confidence = min(0.55 + 0.06 * score, 0.97)
    return LegalGateResult(
        is_legal=True,
        confidence=confidence,
        reason="",
        matched_cues=hits,
    )
