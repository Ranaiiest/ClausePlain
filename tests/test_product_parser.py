from src.product.parser import parse_document_analysis


def test_parse_valid_analysis():
    raw = """
    {
      "is_legal_document": true,
      "rejection_reason": "",
      "document_type": "Offer letter",
      "title": "Offer of Employment",
      "parties": ["Acme Inc", "Jordan Lee"],
      "key_dates": ["Start date: 1 June 2026"],
      "overview": "This is a job offer.",
      "governing_law": "California",
      "dispute_resolution": "",
      "clauses": [{"title": "At-will", "category": "condition", "excerpt": "employment is at-will", "explanation": "Either side can end it.", "why_it_matters": "Little job security.", "who_it_affects": "both", "numbers": []}],
      "obligations": [{"party": "Jordan Lee", "must_do": "Start work on the start date", "when_or_how": "1 June 2026", "if_they_dont": "", "excerpt": "shall commence"}],
      "conditions": [{"title": "Background check", "explanation": "Offer depends on a check.", "trigger": "satisfactory check", "consequence": "offer can be withdrawn", "excerpt": "subject to"}],
      "money_and_numbers": [{"label": "salary", "amount": "$90,000 per year", "explanation": "paid monthly", "excerpt": "annual salary of $90,000"}],
      "timelines": [{"label": "notice", "when": "14 days", "explanation": "either party may resign", "excerpt": "fourteen (14) days"}],
      "rights_and_restrictions": [{"kind": "restriction", "party": "Jordan Lee", "detail": "No competing work for 6 months", "excerpt": "non-compete"}],
      "legal_terms": [{"term": "at-will", "plain_english": "Either of you can end the job at any time, within the law.", "why_it_matters": "You can be let go without a stated reason."}],
      "watch_outs": ["Notice period is 14 days."]
    }
    """
    analysis = parse_document_analysis(raw, fallback_title="file")
    assert analysis.is_legal_document is True
    assert analysis.clauses[0].why_it_matters
    assert analysis.money_and_numbers[0].amount.startswith("$90,000")
    assert analysis.timelines[0].when == "14 days"


def test_parse_flags_non_legal_document():
    raw = '{"is_legal_document": false, "rejection_reason": "Not a legal document. This is a cake recipe."}'
    analysis = parse_document_analysis(raw, fallback_title="recipe")
    assert analysis.is_legal_document is False
    assert "Not a legal document" in analysis.rejection_reason


def test_parse_invalid_falls_back():
    analysis = parse_document_analysis("not json at all", fallback_title="My PDF")
    assert analysis.title == "My PDF"
    assert analysis.watch_outs
