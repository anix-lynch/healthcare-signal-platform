"""
SAFETY AGENT REGRESSION TEST.

Verifies the hard-rule overlay forces tier ≤ 2 even when the (hypothetical)
upstream classifier returns a higher tier. The router itself catches most
red flags — but the safety agent is the SECOND defense, so we test it
in isolation by feeding it a deliberately-wrong verdict.
"""

from __future__ import annotations
import sys
import pathlib

ER_TRIAGE = pathlib.Path(__file__).resolve().parents[1]
LAYER2_ROOT = ER_TRIAGE.parent.parent
sys.path.insert(0, str(LAYER2_ROOT))
sys.path.insert(0, str(ER_TRIAGE))

from safety.safety_agent import review


def _wrong_verdict(tier: int = 4) -> dict:
    """Simulates a classifier under-triage. Safety agent must push back to ≤ 2."""
    return {
        "esi_tier": tier,
        "bucket": "WAIT",
        "confidence": 0.5,
        "reasoning": "(simulated under-triage)",
        "red_flags": [],
        "resources_expected": 1,
    }


def test_chest_pain_override():
    case = {"cc": "chest pain", "hpi": "55yo M, substernal 30 min", "vitals": {}}
    out = review(case, _wrong_verdict(4))
    assert out["esi_tier"] <= 2
    assert out["safety_override"] is True
    assert "chest_pain" in out["override_reason"]


def test_stroke_override():
    case = {"cc": "facial droop", "hpi": "71yo F, FAST positive 1hr ago", "vitals": {}}
    out = review(case, _wrong_verdict(4))
    assert out["esi_tier"] <= 2
    assert out["safety_override"] is True
    assert "stroke_signs" in out["override_reason"]


def test_ams_override():
    case = {"cc": "altered mental status", "hpi": "78yo F, GCS 12", "vitals": {}}
    out = review(case, _wrong_verdict(5))
    assert out["esi_tier"] <= 2
    assert out["safety_override"] is True
    assert "altered_mental_status" in out["override_reason"]


def test_anaphylaxis_override():
    case = {"cc": "anaphylaxis", "hpi": "peanut exposure, lip swelling, wheeze", "vitals": {}}
    out = review(case, _wrong_verdict(3))
    assert out["esi_tier"] <= 2
    assert out["safety_override"] is True
    assert "anaphylaxis" in out["override_reason"]


def test_cardiac_arrest_floor_is_one():
    """Cardiac arrest must floor to ESI 1, not 2."""
    case = {"cc": "cardiac arrest, no pulse", "hpi": "witnessed collapse", "vitals": {}}
    out = review(case, _wrong_verdict(3))
    assert out["esi_tier"] == 1
    assert out["safety_override"] is True


def test_no_override_for_benign_case():
    """Benign case → no override fires."""
    case = {"cc": "ankle sprain", "hpi": "twisted running", "vitals": {}}
    out = review(case, _wrong_verdict(4))
    assert out["safety_override"] is False
    assert out["esi_tier"] == 4  # unchanged


def test_never_overrides_upward():
    """Even if hard rule fires, never raise tier number (= less urgent)."""
    case = {"cc": "chest pain", "hpi": "atypical", "vitals": {}}
    # Classifier already said tier 1 — safety agent must NOT push to tier 2.
    out = review(case, _wrong_verdict(1))
    assert out["esi_tier"] == 1
    assert out["safety_override"] is False  # tier 1 already ≤ floor
