"""Structured analysis models for a user-uploaded legal document."""
from __future__ import annotations

from pydantic import BaseModel, Field


class LegalTerm(BaseModel):
    term: str
    plain_english: str
    why_it_matters: str = ""


class ClauseCard(BaseModel):
    title: str
    category: str = "other"
    excerpt: str = ""
    explanation: str = ""
    why_it_matters: str = ""
    who_it_affects: str = ""
    numbers: list[str] = Field(default_factory=list)


class Obligation(BaseModel):
    party: str
    must_do: str
    when_or_how: str = ""
    if_they_dont: str = ""
    excerpt: str = ""


class Condition(BaseModel):
    title: str
    explanation: str
    trigger: str = ""
    consequence: str = ""
    excerpt: str = ""


class MoneyTerm(BaseModel):
    label: str
    amount: str
    explanation: str = ""
    excerpt: str = ""


class TimelineItem(BaseModel):
    label: str
    when: str
    explanation: str = ""
    excerpt: str = ""


class RightOrRestriction(BaseModel):
    kind: str = "restriction"
    party: str = ""
    detail: str
    excerpt: str = ""


class DocumentAnalysis(BaseModel):
    is_legal_document: bool = True
    rejection_reason: str = ""
    document_type: str = "Legal document"
    title: str = ""
    parties: list[str] = Field(default_factory=list)
    key_dates: list[str] = Field(default_factory=list)
    overview: str = ""
    governing_law: str = ""
    dispute_resolution: str = ""
    clauses: list[ClauseCard] = Field(default_factory=list)
    obligations: list[Obligation] = Field(default_factory=list)
    conditions: list[Condition] = Field(default_factory=list)
    money_and_numbers: list[MoneyTerm] = Field(default_factory=list)
    timelines: list[TimelineItem] = Field(default_factory=list)
    rights_and_restrictions: list[RightOrRestriction] = Field(default_factory=list)
    legal_terms: list[LegalTerm] = Field(default_factory=list)
    watch_outs: list[str] = Field(default_factory=list)


class ChatTurn(BaseModel):
    role: str
    content: str
