"""
Pattern 7 — ranking · Output schema.

    "which evidence should appear first 😭"

Reranks retrieval's top-K hits using clinical severity / age proximity /
condition match. Produces a smaller, sharper lineup for generation grounding.
"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


RerankMethod = Literal["heuristic_severity", "cross_encoder", "ensemble"]


class RankedHit(BaseModel):
    source_id: str
    rerank_score: float = Field(..., ge=0)
    severity_signals: list[str] = Field(default_factory=list, description=(
        "snake_case reasons for ranking. e.g. 'matched_age_band', 'severe_los'"
    ))
    summary: str
    original_rachel_rank: int | None = Field(None, ge=0)


class PoliceLineupOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pattern: Literal["police_lineup_rank"] = "police_lineup_rank"
    case_id: str
    ranked: list[RankedHit] = Field(default_factory=list)
    method: RerankMethod
    k_input: int = Field(..., description="how many retrieval hits we reranked from")
    k_output: int = Field(..., description="how many we returned")
    ndcg_lift_vs_rachel: float | None = Field(None, description=(
        "offline-computed lift. None at inference time, populated by eval."
    ))
    warnings: list[str] = Field(default_factory=list)
