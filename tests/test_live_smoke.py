"""Optional live smoke test. Skipped when GROQ_API_KEY is missing."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.ingestion.limits import NotLegalDocumentError
from src.utils.config import load_config, resolve_secret

pytestmark = pytest.mark.skipif(
    not resolve_secret("GROQ_API_KEY") and not os.getenv("GROQ_API_KEY"),
    reason="GROQ_API_KEY not set",
)


OFFER = """
OFFER OF EMPLOYMENT
This offer letter is made between Acme Inc., the employer, and Jordan Lee, the employee.
In consideration of the salary of ninety thousand dollars ($90,000) per year, paid monthly,
you shall commence work on 1 June 2026. Employment is at-will. Either party may terminate
this agreement upon fourteen (14) days' written notice. Confidential information must not
be disclosed. This agreement is governed by the laws of California. You agree not to
solicit customers for six (6) months after termination of employment.
"""


def test_live_analyze_offer_and_reject_recipe(tmp_path: Path):
    from src.product.workspace import DocumentWorkspace

    config = load_config("configs/config.yaml", force_reload=True)
    workspace = DocumentWorkspace(config)

    offer = tmp_path / "offer.txt"
    offer.write_text(OFFER, encoding="utf-8")
    result = workspace.analyze_file(offer)
    assert result.rejected is False
    assert result.analysis is not None
    assert result.analysis.is_legal_document is True
    assert result.analysis.parties or result.analysis.overview

    recipe = tmp_path / "cake.txt"
    recipe.write_text(
        "Chocolate cake recipe for a birthday party. Preheat the oven to 350 degrees. "
        "Mix flour, sugar, cocoa powder, eggs, and butter until smooth. Pour into a pan "
        "and bake for thirty minutes. Frost with vanilla icing and serve with ice cream "
        "and berries after you buy groceries at the market this weekend with friends.\n"
        * 2,
        encoding="utf-8",
    )
    with pytest.raises(NotLegalDocumentError, match="Not a legal document"):
        workspace.analyze_file(recipe)
