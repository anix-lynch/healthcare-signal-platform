"""
Pattern 1 — Rachel · Output schema.

The contract every caller of retrieval gets back. Matches the spec:

    "bro find me another patient who almost died like this 😭"

Output is structured so services/rag-api can wrap it as /v1/search without
reshaping, and Mad Lib can ground every claim on a `source_id` from here.
"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


HitType = Literal["past_case", "guideline", "protocol", "policy", "kb_article"]
RetrievalMethod = Literal["bm25", "dense", "hybrid_bm25_dense", "bm25_fallback"]


class Hit(BaseModel):
    """One retrieved item — past case OR guideline OR protocol."""
    source_id: str = Field(..., description="encounter_id or document_id")
    type: HitType
    similarity: float = Field(..., ge=0, le=1)
    summary: str = Field(..., description="renderable snippet (rendered from row or doc)")
    why_relevant: str = Field(..., description="one-line plain-English match explanation")


class RachelOutput(BaseModel):
    """Top-level Rachel verdict for a single query case."""
    model_config = ConfigDict(extra="forbid")

    pattern: Literal["rachel_retrieval"] = "rachel_retrieval"
    query_case_id: str
    retrieved: list[Hit] = Field(default_factory=list)
    retrieval_method: RetrievalMethod
    fallback_used: bool = False
    latency_ms: int | None = None
    warnings: list[str] = Field(default_factory=list, description=(
        "human-readable hedges. Examples: "
        "'embedding service degraded — BM25-only fallback', "
        "'cross-patient leak suppressed', 'no citations resolved'."
    ))
