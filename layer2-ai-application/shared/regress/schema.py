"""
Pattern 3 — forecast · Output schema.

The thing services/rag-api and apps/er-triage hand to clinicians.

Three brutal questions, three structured answers:
    "patient camp เตียงกี่วัน?"        → predicted_los_days
    "ปล่อยกลับแล้วโผล่อีกไหม?"        → readmission_30d_risk
    "death aura meter วันนี้?"         → mortality_risk_indicator

Confidence and warnings are NOT decoration. They are how a hospital lawyer
sleeps at night. Every field surfaces the data weakness behind the number.
"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


MortalityTier = Literal["low", "med", "high", "unknown"]
ConfidenceTier = Literal["low", "med", "high"]
LoSBin = Literal["short", "medium", "long"]


class LoSBlock(BaseModel):
    """How long they camp the bed."""
    predicted_days: float = Field(..., ge=0, le=120)
    bin: LoSBin
    cohort_n: int = Field(..., description="rows in matched cohort — drives confidence")
    cohort_std: float = Field(..., ge=0, description="population stddev of LOS in cohort")
    source_level: str = Field(..., description="which hierarchy level provided the estimate")


class ReadmissionBlock(BaseModel):
    """Will they bounce back in 30 days. Proxy-only with current data."""
    risk_30d: float = Field(..., ge=0, le=1, description="probability of 30-day readmission")
    risk_band: Literal["low", "med", "high"]
    method: Literal["proxy_prior_admission_count", "trained_lightgbm", "heuristic_fallback"]


class MortalityBlock(BaseModel):
    """Death aura meter. Heuristic until real ICU telemetry lands."""
    indicator: MortalityTier
    rule_fired: str | None = Field(None, description="which rule produced the tier")
    requires_clinical_review: bool = True


class CrystalBallOutput(BaseModel):
    """Top-level forecast verdict for a single case."""
    model_config = ConfigDict(extra="forbid")

    pattern: Literal["crystal_ball_prognosis"] = "crystal_ball_prognosis"
    case_id: str
    los: LoSBlock
    readmission: ReadmissionBlock
    mortality: MortalityBlock
    confidence: ConfidenceTier
    warnings: list[str] = Field(default_factory=list, description=(
        "human-readable hedges. Examples: "
        "'limited clinical telemetry', 'cohort size < 20', 'proxy readmission only'."
    ))
    data_source: Literal["registry_v1", "registry_v2_enriched", "real_ehr"] = "registry_v1"
