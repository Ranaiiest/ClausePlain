"""Prompt templates for document analysis and grounded Q&A."""

ANALYSIS_SYSTEM = (
    "You are a careful legal explainer, not a lawyer giving advice. "
    "Use only the provided excerpts. Never invent parties, dates, amounts, or clauses. "
    "Reply with a single JSON object and no markdown fences."
)

ANALYSIS_USER = """Decide if the excerpts are an actual legal instrument (contract, offer letter, NDA, lease, court filing, terms of service, employment agreement, policy the reader must follow). News, recipes, essays, invoices-only, resumes, and marketing decks are NOT legal documents.

Document filename: {title}

--- EXCERPTS ---
{context}
--- END EXCERPTS ---

Return ONLY this JSON object:
{{
  "is_legal_document": true or false,
  "rejection_reason": "if false, one sentence: Not a legal document. ... otherwise empty string",
  "document_type": "short type",
  "title": "document title if stated, else filename",
  "parties": ["names"],
  "key_dates": ["date — what it controls"],
  "overview": "4-7 sentences covering who, what, when, money, and how it ends",
  "governing_law": "jurisdiction if stated, else empty",
  "dispute_resolution": "court / arbitration / other if stated, else empty",
  "clauses": [
    {{
      "title": "short name",
      "category": "obligation or condition or right or restriction or money or termination or confidentiality or ip or other",
      "excerpt": "verbatim quote",
      "explanation": "plain English with the actual number, deadline, or party name",
      "why_it_matters": "what the reader should watch for",
      "who_it_affects": "which party",
      "numbers": ["any amounts, %, days, or caps in this clause"]
    }}
  ],
  "obligations": [
    {{
      "party": "who",
      "must_do": "plain English duty",
      "when_or_how": "deadline, frequency, or process if stated",
      "if_they_dont": "consequence if stated, else empty",
      "excerpt": "quote"
    }}
  ],
  "conditions": [
    {{
      "title": "condition name",
      "explanation": "plain English",
      "trigger": "what must happen first",
      "consequence": "what follows",
      "excerpt": "quote"
    }}
  ],
  "money_and_numbers": [
    {{
      "label": "salary / fee / cap / deposit / equity / interest / penalty",
      "amount": "the figure with currency or %",
      "explanation": "when it is paid or how it is calculated",
      "excerpt": "quote"
    }}
  ],
  "timelines": [
    {{
      "label": "start / end / notice / probation / renewal / response deadline",
      "when": "the date or period",
      "explanation": "what happens then",
      "excerpt": "quote"
    }}
  ],
  "rights_and_restrictions": [
    {{
      "kind": "right or restriction",
      "party": "who",
      "detail": "plain English including duration and geography if stated",
      "excerpt": "quote"
    }}
  ],
  "legal_terms": [
    {{
      "term": "jargon from the document",
      "plain_english": "everyday meaning",
      "why_it_matters": "how it changes the reader's position"
    }}
  ],
  "watch_outs": ["specific, numbered facts a careful reader should not miss"]
}}

Rules:
- If this is not a legal instrument, set is_legal_document to false, fill rejection_reason, and leave other lists empty.
- Prefer nuance: extract every material number, %, cap, notice period, auto-renewal, termination trigger, non-compete duration, IP owner, at-will vs for-cause, and who pays whom.
- Do not invent. If a detail is missing, omit it.
- excerpts must be copied from the text.
"""

CHAT_SYSTEM = (
    "You explain legal documents in clear English. Answer only from the excerpts. "
    "When the user asks about money, dates, notice, termination, or restrictions, "
    "quote the exact figure or period. If the excerpts do not contain the answer, say so. "
    "You are not a lawyer; do not give legal advice."
)

CHAT_USER = """Document: {title}

Excerpts:
{context}

Conversation so far:
{history}

User question: {question}

Answer in plain English. Include numbers and deadlines when they appear in the excerpts."""

RETRIEVAL_QUERIES = (
    "parties names title effective date commencement execution",
    "payment compensation salary fees consideration bonus equity stock options",
    "notice period termination for cause convenience auto renewal",
    "probation start date end date term length duration days months",
    "confidentiality non-disclosure intellectual property ownership assignment",
    "liability indemnity limitation of damages cap insurance",
    "non-compete non-solicit restrictive covenant geography duration",
    "governing law jurisdiction dispute arbitration venue court",
    "conditions precedent background check representations warranties",
    "leave benefits vacation sick hours working time",
    "penalty liquidated damages interest late fee deposit",
    "definitions shall mean hereinafter",
)
