"""
SMOKE TEST · ESI auto-tagger.

Must-pass criteria:
  1. Every gold case classifies within ±1 of expected tier
  2. Every safety-critical case (chest pain, stroke, AMS, anaphylaxis)
     classifies ≤ 2 (NEVER higher than ESI 2)
  3. Every output has a non-empty reasoning field

If this test fails in CI → er-triage does not ship.
"""

from __future__ import annotations
import json
import pathlib
import sys
import pytest

ER_TRIAGE = pathlib.Path(__file__).resolve().parents[1]
LAYER2_ROOT = ER_TRIAGE.parent.parent
sys.path.insert(0, str(LAYER2_ROOT))
sys.path.insert(0, str(ER_TRIAGE))

from shared.classify.router import classify as router_classify
from safety.safety_agent import review as safety_review
from shared.guardrails.output_guardrails import needs_human_escalation


GOLDEN_SET = ER_TRIAGE / "inputs" / "golden_esi.json"


def _full_pipeline(case: dict) -> dict:
    verdict = router_classify(case).to_dict()
    reviewed = safety_review(case, verdict)
    reviewed["needs_human_escalation"] = needs_human_escalation(case, reviewed)
    return reviewed


@pytest.fixture
def golden():
    return json.loads(GOLDEN_SET.read_text())


def test_golden_set_loadable(golden):
    assert "cases" in golden
    assert len(golden["cases"]) >= 2


def test_every_case_within_tolerance(golden):
    """Each prediction must be within ±1 tier of expected."""
    failures = []
    for c in golden["cases"]:
        result = _full_pipeline(c["case"])
        if abs(result["esi_tier"] - c["expected_tier"]) > 1:
            failures.append(
                f"{c['id']}: expected ESI {c['expected_tier']}, "
                f"got ESI {result['esi_tier']}"
            )
    assert not failures, "Tier-tolerance failures:\n  " + "\n  ".join(failures)


def test_safety_critical_never_above_tier_2(golden):
    """Chest pain / stroke / AMS / anaphylaxis must never classify ≥ 3."""
    failures = []
    for c in golden["cases"]:
        cap = c.get("must_be_at_most")
        if cap is None:
            continue
        result = _full_pipeline(c["case"])
        if result["esi_tier"] > cap:
            failures.append(
                f"{c['id']}: cap=ESI{cap}, got ESI{result['esi_tier']}"
            )
    assert not failures, "Safety-floor violations:\n  " + "\n  ".join(failures)


def test_reasoning_field_non_empty(golden):
    """Every output must have a non-empty reasoning string."""
    for c in golden["cases"]:
        result = _full_pipeline(c["case"])
        assert isinstance(result.get("reasoning"), str)
        assert len(result["reasoning"]) > 0, f"{c['id']} has empty reasoning"


def test_bucket_consistency_with_tier(golden):
    """ESI 1-2 → NOW, ESI 3 → SOON, ESI 4-5 → WAIT."""
    expected_map = {1: "NOW", 2: "NOW", 3: "SOON", 4: "WAIT", 5: "WAIT"}
    for c in golden["cases"]:
        result = _full_pipeline(c["case"])
        assert result["bucket"] == expected_map[result["esi_tier"]], (
            f"{c['id']}: tier={result['esi_tier']} but bucket={result['bucket']}"
        )
