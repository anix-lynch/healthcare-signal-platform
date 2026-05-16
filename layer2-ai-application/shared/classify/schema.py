"""
Pattern 2 — Traffic Light · Output schema.

The thing apps/er-triage hands to a charge nurse:

    "how urgently should we panic 😭"

Output is structured so the UI can render a colour + a banner + an
escalation page without parsing prose. Every field is renderable in <50ms.
"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


TierBucket = Literal["NOW", "SOON", "WAIT"]
ESITier = Literal[1, 2, 3, 4, 5]
ClassifyMethod = Literal["llm_primary", "rules_fallback", "llm_with_rules_override"]


class TrafficLightOutput(BaseModel):
    """Top-level triage verdict for a single case."""
    model_config = ConfigDict(extra="forbid")

    pattern: Literal["traffic_light_classification"] = "traffic_light_classification"
    case_id: str
    tier: TierBucket
    esi_tier: ESITier = Field(..., description="1=resuscitation, 5=non-urgent")
    confidence: float = Field(..., ge=0, le=1)
    reason: str = Field(..., description="one-sentence rationale clinician can read")
    red_flags: list[str] = Field(default_factory=list, description=(
        "snake_case acuity triggers. Examples: "
        "'chest_pain', 'diaphoresis', 'hypotension', 'altered_mental_status'."
    ))
    escalate: bool = Field(..., description=(
        "true if attending should be paged immediately (ESI 1 or rule trigger)"
    ))
    human_review_required: bool = Field(..., description=(
        "true when confidence < threshold OR escalate=true OR rules override"
    ))
    method: ClassifyMethod
    fallback_used: bool = False
    model_tier_used: Literal["haiku", "flash", "sonnet", "rules"] | None = None
    cost_usd: float | None = Field(None, ge=0)
    warnings: list[str] = Field(default_factory=list)
