"""
PHASE 2 · LLM-as-classifier for ESI tier 1-5.

See mj/docs/02_traffic_light.md for the pattern.
See mj/docs/autotagging_llm_as_classifier_intake_automation.md for the recipe.

Output schema (Pydantic):
    {
      esi_tier: int (1-5),
      confidence: float (0-1),
      reasoning: str,           ← regulator-friendly audit trail
      red_flags: list[str],
      resources_expected: int
    }

Workflow:
  1. classify(case) → raw LLM verdict
  2. SafetyAgent.review(verdict) → may override (never down-triage red flags)
  3. final tier returned to caller (engine.py in ER2)

TODO:
  - implement classify() using anthropic + instructor
  - implement holdout eval in tests/test_smoke_esi.py
"""

from __future__ import annotations


def classify(case: dict) -> dict:
    """Classify a single ER case into ESI tier 1-5."""
    raise NotImplementedError(
        "Implement per docs/01_phase2_autotag.md. "
        "Use anthropic + instructor for structured output. "
        "Always pair with SafetyAgent.review() before returning."
    )


if __name__ == "__main__":
    classify({})
