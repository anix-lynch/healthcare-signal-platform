"""
Pattern 5 — Smoke Detector · Honest baseline orchestrator.

Wraps the existing `anomaly_flagger.flag()` (rule + cohort-stats) into the
SmokeDetectorOutput contract. The engine computes vitals z-scores against
condition-specific cohorts; we map its dict into a typed output and decide
the anomaly threshold + clinical-review gate.

Engine output (already shipped):
    {
        "is_outlier": bool,
        "anomaly_score": float,
        "reasons": [str, ...],
        "cohort_size": int,
        ...
    }

Threshold rule:
    score >= 2.5  → is_anomaly + requires_clinical_review
    score >= 1.5  → soft warning, no escalation
    otherwise     → normal

A real production model would calibrate the threshold against the holdout.
For now we publish the threshold in the output so eval can sweep it.
"""
from __future__ import annotations

from .anomaly_flagger import flag as _engine_flag
from .schema import SmokeDetectorOutput


DEFAULT_THRESHOLD = 2.5


def detect_smoke(
    case: dict,
    *,
    case_id: str | None = None,
    triage: dict | None = None,
    los_prediction: dict | None = None,
    threshold: float = DEFAULT_THRESHOLD,
) -> SmokeDetectorOutput:
    """
    Run anomaly flagger on a case + emit structured verdict.

    Args:
        case: ER case dict.
        case_id: encounter identifier.
        triage: optional Traffic Light output for context.
        los_prediction: optional Crystal Ball LoS output (rare LoS = signal).
        threshold: anomaly score floor for is_anomaly.

    Returns:
        SmokeDetectorOutput.
    """
    raw = _engine_flag(case, triage=triage, los_prediction=los_prediction)
    score = float(raw.get("anomaly_score", 0.0))
    reasons = list(raw.get("reasons") or [])
    cohort_size = raw.get("cohort_size", 0)

    warnings: list[str] = []
    if cohort_size and cohort_size < 30:
        warnings.append(f"cohort size {cohort_size} < 30 — wide CI on threshold")

    is_anom = score >= threshold
    requires_review = is_anom or score >= 1.5

    return SmokeDetectorOutput(
        case_id=case_id or "unknown",
        is_anomaly=is_anom,
        anomaly_score=round(score, 3),
        distance_from_centroid=raw.get("distance"),
        outlier_reasons=reasons,
        requires_clinical_review=requires_review,
        method="ensemble" if reasons and raw.get("distance") is not None else "rule_based",
        threshold=threshold,
        warnings=warnings,
    )
