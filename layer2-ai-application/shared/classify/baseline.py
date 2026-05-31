"""
Pattern 2 — classifier · Honest baseline orchestrator.

What this is:
    Wraps the existing rule-based `router.classify()` engine into the
    structured TrafficLightOutput contract, applies leakage guard, returns.

What this is NOT:
    - the LLM-as-classifier (that lives in apps/er-triage/classify/esi_classifier.py)
    - a trained tabular classifier (queued for enriched data)
    - the 3-tier cost router (that's in cost_router.py — different concern,
      it picks WHICH model to call, not what the ESI tier is)

This file is the floor. If an LLM classifier doesn't beat rules + guards
on F1, the LLM classifier is broken — not impressive.
"""
from __future__ import annotations
import time

from .router import classify as _rules_classify
from .schema import TrafficLightOutput
from .leakage_checks import check_features


# ── Helpers ────────────────────────────────────────────────────────────────
def _tier_to_bucket(esi_tier: int) -> str:
    if esi_tier <= 2: return "NOW"
    if esi_tier == 3: return "SOON"
    return "WAIT"


# ── Public API ─────────────────────────────────────────────────────────────
def triage(
    case: dict,
    *,
    case_id: str | None = None,
    allow_post_triage: bool = False,
) -> TrafficLightOutput:
    """
    Run the rule-based classifier baseline on one case.

    Args:
        case: dict with at least 'cc'; ideally also 'hpi', 'vitals', 'arrival'.
        case_id: encounter identifier (echoed back).
        allow_post_triage: True only when re-classifying with labs back.

    Returns:
        TrafficLightOutput — pydantic-validated, JSON-serializable.

    Raises:
        ClassifyLeakError if `case` contains label/future fields.
    """
    check_features(case, allow_post_triage=allow_post_triage)

    decision = _rules_classify(case)
    confidence = decision.confidence

    return TrafficLightOutput(
        case_id=case_id or case.get("case_id") or "unknown",
        tier=decision.bucket,
        esi_tier=decision.esi_tier,
        confidence=round(confidence, 3),
        reason=decision.reasoning or "rule-based ESI assessment",
        red_flags=list(decision.red_flags or []),
        escalate=decision.esi_tier <= 2 or bool(decision.red_flags),
        human_review_required=(confidence < 0.85) or decision.esi_tier == 1,
        method="rules_fallback",
        fallback_used=False,
        model_tier_used="rules",
        cost_usd=0.0,
        warnings=([] if decision.red_flags else ["no red flags fired — confidence uses default prior"]),
    )


def triage_dict(case: dict, **kwargs) -> dict:
    return triage(case, **kwargs).model_dump()


if __name__ == "__main__":
    import json, sys
    case = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {
        "cc": "chest pain",
        "hpi": "62yo M with substernal pressure 30 min, diaphoresis, radiates to jaw",
        "arrival": "ambulance",
        "vitals": {"bp_sys": 95, "hr": 122, "rr": 24, "spo2": 92, "temp_f": 99.1},
    }
    out = triage(case, case_id="CASE-104")
    print(out.model_dump_json(indent=2))
