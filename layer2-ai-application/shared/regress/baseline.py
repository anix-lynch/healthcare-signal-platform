"""
Pattern 3 — Crystal Ball · Honest baselines.

What this is:
    The minimal cohort-stat + rule combo that produces a structured
    CrystalBallOutput from a Layer-1-style case payload.

What this is NOT:
    - a trained tabular model (see train_lightgbm.py — optional, scaffold)
    - a clinical predictor (current data is billing registry, not EHR)
    - a defensible production model (see warnings in every output)

This is the floor that everything else must beat. If LightGBM doesn't
beat cohort-median LOS, the LightGBM is broken — not impressive.

Reads from:
    shared/regress/los_predictor.py  ← existing hierarchical cohort model

Readmission proxy:
    Layer 1 has `previous_admission_count` and `is_readmission` (the latter
    is leakage at predict time). The honest pre-discharge proxy is:
        risk = sigmoid(prior_visits / 5)
    Calibration is rough. Mark confidence accordingly.

Mortality heuristic:
    No vitals, no labs, no ICU telemetry in current data. We use a rule:
        - Cancer + Age ≥ 70 + Emergency admission     → med
        - Sepsis-like keywords in CC + low BP         → high   (needs enrich v2)
        - All else                                     → low / unknown
    This is a STAND-IN for when real clinical telemetry lands. Document it
    so the next engineer doesn't think we shipped a real mortality model.
"""
from __future__ import annotations
import math
import re
from typing import Any

from .los_predictor import predict_los, LoSPrediction, _age_band
from .schema import (
    CrystalBallOutput,
    LoSBlock,
    ReadmissionBlock,
    MortalityBlock,
)
from .leakage_checks import check_features


# ── Readmission proxy ──────────────────────────────────────────────────────
def _readmission_proxy(prior_visits: int | None) -> ReadmissionBlock:
    """
    Crude proxy: more prior visits → more likely back.

    This is a placeholder. A real model would use comorbidities, social
    determinants, discharge disposition, follow-up scheduling. None of
    that is in the current Layer 1 dataset.
    """
    n = max(0, int(prior_visits or 0))
    # sigmoid-ish saturating curve, max ~0.6 because we have no real signal
    risk = round(1 / (1 + math.exp(-(n - 2) / 1.5)) * 0.6, 3)
    band = "high" if risk >= 0.5 else "med" if risk >= 0.3 else "low"
    return ReadmissionBlock(
        risk_30d=risk,
        risk_band=band,
        method="proxy_prior_admission_count",
    )


# ── Mortality heuristic ────────────────────────────────────────────────────
_HIGH_RISK_KEYWORDS = (
    "sepsis", "septic", "stroke", "stemi", "cardiac arrest",
    "respiratory failure", "anaphyla", "altered mental status",
)


def _mortality_rule(case: dict, condition: str, age: int) -> MortalityBlock:
    cc = (case.get("cc") or "").lower()
    hpi = (case.get("hpi") or "").lower()
    txt = f"{cc} {hpi}"

    if any(k in txt for k in _HIGH_RISK_KEYWORDS):
        return MortalityBlock(
            indicator="high",
            rule_fired="acuity_keyword_in_chief_complaint",
            requires_clinical_review=True,
        )
    if condition.lower() == "cancer" and age >= 70:
        return MortalityBlock(
            indicator="med",
            rule_fired="cancer_age_geq_70",
            requires_clinical_review=True,
        )
    if condition.lower() == "cancer":
        return MortalityBlock(
            indicator="med",
            rule_fired="cancer_any_age_placeholder",
            requires_clinical_review=True,
        )
    return MortalityBlock(
        indicator="low",
        rule_fired=None,
        requires_clinical_review=False,
    )


# ── Confidence + warnings synthesis ────────────────────────────────────────
def _synth_confidence(los: LoSPrediction, has_clinical_telemetry: bool) -> tuple[str, list[str]]:
    warnings: list[str] = []
    if not has_clinical_telemetry:
        warnings.append("limited clinical telemetry — no real vitals or labs in current data")
    if los.cohort_n < 20:
        warnings.append(f"LOS cohort size n={los.cohort_n} < 20 — wide confidence interval")
    if los.cohort_std > los.predicted_days:
        warnings.append("LOS stddev exceeds mean — high variance cohort")
    warnings.append("readmission risk is a proxy from prior_visits, not a trained model")
    warnings.append("mortality indicator is rule-based heuristic, not a clinical predictor")

    if los.cohort_n < 20 or not has_clinical_telemetry:
        tier = "low"
    elif los.cohort_n < 100:
        tier = "med"
    else:
        tier = "med"  # cap at med until we have real EHR
    return tier, warnings


# ── Public API ─────────────────────────────────────────────────────────────
def predict_prognosis(
    case: dict,
    *,
    case_id: str | None = None,
    triage: dict | None = None,
    prior_visits: int | None = None,
    allow_mid_stay: bool = False,
) -> CrystalBallOutput:
    """
    Run the full Crystal Ball stack on one case.

    Args:
        case: dict with at least 'cc'; ideally 'hpi', 'arrival'.
        case_id: encounter identifier (echoed back in output).
        triage: optional Traffic Light output ({bucket: NOW|SOON|WAIT}).
        prior_visits: pre-admission visit count (NOT is_readmission).
        allow_mid_stay: pass True only for legitimate post-triage updates.

    Returns:
        CrystalBallOutput — pydantic-validated, JSON-serializable.

    Raises:
        LeakageError if `case` contains discharge-time fields.
    """
    # Guard: nothing post-discharge should be in the input.
    check_features(case, allow_mid_stay=allow_mid_stay)

    los_pred = predict_los(case, triage=triage)
    los_block = LoSBlock(
        predicted_days=los_pred.predicted_days,
        bin=los_pred.bin,
        cohort_n=los_pred.cohort_n,
        cohort_std=los_pred.cohort_std,
        source_level=los_pred.source_level,
    )

    readm_block = _readmission_proxy(prior_visits)

    # Mortality needs condition + age, which we infer from case text.
    condition = _infer_condition(case)
    age = _infer_age(case)
    mort_block = _mortality_rule(case, condition, age)

    has_telemetry = bool(case.get("vitals") or case.get("lab_panel_json"))
    confidence_tier, warnings = _synth_confidence(los_pred, has_telemetry)

    data_source = "registry_v2_enriched" if has_telemetry else "registry_v1"

    return CrystalBallOutput(
        case_id=case_id or "unknown",
        los=los_block,
        readmission=readm_block,
        mortality=mort_block,
        confidence=confidence_tier,
        warnings=warnings,
        data_source=data_source,
    )


# ── tiny helpers (avoid circular import of los_predictor internals) ────────
def _infer_condition(case: dict) -> str:
    from .los_predictor import _infer_condition as _delegate
    return _delegate(case)


def _infer_age(case: dict) -> int:
    from .los_predictor import _infer_age as _delegate
    return _delegate(case)


if __name__ == "__main__":
    import json, sys
    case = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {
        "cc": "chest pain", "hpi": "62yo M, substernal pressure 30 min", "arrival": "ambulance",
    }
    out = predict_prognosis(case, case_id="DEMO-001", prior_visits=2)
    print(out.model_dump_json(indent=2))
