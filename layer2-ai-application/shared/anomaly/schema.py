"""
Pattern 5 — anomaly detector · Output schema.

    "this case smells WRONG 😭"

Per-case anomaly flagging + corpus-level drift detection. Output is the
per-case verdict; drift snapshots live in shared/evaluation/.
"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


AnomalyMethod = Literal["centroid_distance", "vital_stats", "rule_based", "ensemble"]


class SmokeDetectorOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pattern: Literal["smoke_detector_anomaly"] = "smoke_detector_anomaly"
    case_id: str
    is_anomaly: bool
    anomaly_score: float = Field(..., ge=0, description="0=typical, higher=weirder")
    distance_from_centroid: float | None = Field(None, ge=0, description=(
        "cosine or z-score distance — method-specific"
    ))
    outlier_reasons: list[str] = Field(default_factory=list, description=(
        "snake_case explanations. e.g. 'bp_severe_low', 'hr_extreme', 'cc_unusual_for_age'"
    ))
    requires_clinical_review: bool
    method: AnomalyMethod
    threshold: float = Field(..., description="score threshold used for is_anomaly")
    warnings: list[str] = Field(default_factory=list)
