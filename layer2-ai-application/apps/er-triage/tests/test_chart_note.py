"""
CHART-NOTE GENERATOR (Pattern 4 — Mad Lib) tests.

Verifies:
  - 5 views always emitted, all non-empty
  - chart_note has every required section
  - No hallucinated numeric values (faithful by construction)
  - Bucket tone reflects NOW / SOON / WAIT
  - Safety-override is mentioned in chart_note when it fires
  - Patient explanation never leaks ESI tier numbers (lay-friendly)
"""

from __future__ import annotations
import sys
import pathlib

ER_TRIAGE = pathlib.Path(__file__).resolve().parents[1]
LAYER2_ROOT = ER_TRIAGE.parent.parent
sys.path.insert(0, str(LAYER2_ROOT))
sys.path.insert(0, str(ER_TRIAGE))

from shared.classify.router import classify as router_classify
from safety.safety_agent import review as safety_review
from shared.guardrails.output_guardrails import needs_human_escalation
from shared.generate.chart_note import generate as gen_views


def _pipeline(case: dict) -> dict:
    v = router_classify(case).to_dict()
    r = safety_review(case, v)
    r["needs_human_escalation"] = needs_human_escalation(case, r)
    return r


CHEST_PAIN = {
    "cc": "chest pain",
    "vitals": {"hr": 105, "rr": 22, "bp": "150/95", "spo2": 96},
    "hpi": "62yo M, substernal pressure 30 min, radiating to left arm",
    "arrival": "walk-in",
}

ANKLE_SPRAIN = {
    "cc": "ankle sprain",
    "vitals": {"hr": 76, "rr": 14, "bp": "120/76", "spo2": 99},
    "hpi": "24yo F, twisted ankle running",
    "arrival": "walk-in",
}


def test_five_views_present():
    triage = _pipeline(CHEST_PAIN)
    views = gen_views(CHEST_PAIN, triage)
    for v in ["chart_note", "nurse_handoff", "patient_explanation",
              "clinician_summary", "executive_summary"]:
        assert v in views, f"missing view {v}"
        assert views[v].strip(), f"view {v} is empty"


def test_chart_note_has_required_sections():
    triage = _pipeline(CHEST_PAIN)
    note = gen_views(CHEST_PAIN, triage)["chart_note"]
    for sec in ["CHIEF COMPLAINT", "ARRIVAL", "HISTORY OF PRESENT ILLNESS",
                "Vitals:", "ASSESSMENT:", "PLAN / DISPOSITION:", "AUDIT:"]:
        assert sec in note, f"chart_note missing {sec}"


def test_no_hallucinated_numbers_chest_pain():
    """No number in any view that wasn't in the inputs (numeric compare)."""
    import re, json
    triage = _pipeline(CHEST_PAIN)
    views = gen_views(CHEST_PAIN, triage)
    src = (
        f"{CHEST_PAIN['cc']} {CHEST_PAIN['hpi']} {json.dumps(CHEST_PAIN['vitals'])} "
        f"{triage['esi_tier']} {triage['confidence']} {triage['resources_expected']} "
        f"{triage.get('reasoning', '')}"
    )
    allowed = {float(n) for n in re.findall(r"\d+(?:\.\d+)?", src)}
    for view_name, content in views.items():
        if view_name.startswith("_"):
            continue
        for num in re.findall(r"\d+(?:\.\d+)?", content):
            assert float(num) in allowed, f"hallucinated number {num} in {view_name}"


def test_bucket_tone_now():
    triage = _pipeline(CHEST_PAIN)
    assert triage["bucket"] == "NOW"
    views = gen_views(CHEST_PAIN, triage)
    text = (views["chart_note"] + " " + views["patient_explanation"]).lower()
    assert any(w in text for w in ["immediate", "right now", "resuscitation", "right away"])


def test_bucket_tone_wait():
    triage = _pipeline(ANKLE_SPRAIN)
    assert triage["bucket"] == "WAIT"
    views = gen_views(ANKLE_SPRAIN, triage)
    text = (views["chart_note"] + " " + views["patient_explanation"]).lower()
    assert any(w in text for w in ["non-urgent", "fast track", "wait", "patience"])


def test_patient_explanation_no_jargon():
    """Lay-language: must NOT contain 'ESI' tier label."""
    for case in [CHEST_PAIN, ANKLE_SPRAIN]:
        triage = _pipeline(case)
        explanation = gen_views(case, triage)["patient_explanation"]
        assert "ESI" not in explanation, f"patient explanation leaks 'ESI' jargon: {explanation}"


def test_safety_override_surfaces_in_note():
    """When override fires, the chart_note must say so explicitly."""
    case = {"cc": "chest pain", "hpi": "atypical", "vitals": {}}
    # Force the safety overlay to fire by handing it a wrong verdict
    wrong_verdict = {
        "esi_tier": 4, "bucket": "WAIT", "confidence": 0.5,
        "reasoning": "(test under-triage)", "red_flags": [],
        "resources_expected": 1,
    }
    reviewed = safety_review(case, wrong_verdict)
    reviewed["needs_human_escalation"] = needs_human_escalation(case, reviewed)
    assert reviewed["safety_override"] is True
    note = gen_views(case, reviewed)["chart_note"]
    assert "SAFETY OVERRIDE" in note
    assert "chest_pain" in note  # the override reason


def test_executive_summary_is_one_line():
    triage = _pipeline(CHEST_PAIN)
    summary = gen_views(CHEST_PAIN, triage)["executive_summary"]
    assert "\n" not in summary
    assert len(summary) < 120
