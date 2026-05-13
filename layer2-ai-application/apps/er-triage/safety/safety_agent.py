"""
LEVEL-2 SAFETY AGENT.

Hard-rule overlay on top of the classifier. Cannot raise the urgency below
ESI 2 for any safety-critical presentation, regardless of what the classifier
returned. Never down-triages.

Hard rules:
  - chest pain
  - stroke signs (FAST positive, facial droop, hemiparesis)
  - altered mental status / GCS < 8
  - anaphylaxis / severe allergic reaction
  - active major bleeding
  - sepsis concern
"""

from __future__ import annotations
import re

# Same red-flag categories as the router, but enforced as a HARD floor.
HARD_FLOOR_RULES: list[tuple[re.Pattern, int, str]] = [
    (re.compile(r"chest pain|substernal", re.I),                       2, "chest_pain"),
    (re.compile(r"stroke|fast positive|facial droop|hemipares", re.I), 2, "stroke_signs"),
    (re.compile(r"altered mental|ams\b|gcs ?[0-7]\b", re.I),            2, "altered_mental_status"),
    (re.compile(r"anaphyla|severe allergic|airway swelling", re.I),    2, "anaphylaxis"),
    (re.compile(r"active bleeding|gi bleed|hematemesis|exsanguinat", re.I), 2, "active_bleeding"),
    (re.compile(r"sepsis|septic shock", re.I),                          2, "sepsis_concern"),
    (re.compile(r"cardiac arrest|no pulse|pulseless", re.I),           1, "cardiac_arrest"),
    (re.compile(r"unresponsive|not breathing|apneic", re.I),           1, "unresponsive"),
]


def review(case: dict, verdict: dict) -> dict:
    """
    Review the classifier verdict. Override the tier *downward* (more urgent)
    if any hard rule matches. Never override upward.

    Args:
        case: original case (cc, vitals, hpi, arrival)
        verdict: dict from router.classify() — must have 'esi_tier' key.

    Returns:
        dict with the same shape as verdict, plus:
          - 'safety_override': bool
          - 'override_reason': list[str] of triggered rule labels
          - 'pre_override_tier': int (only present if override fired)
    """
    text = f"{case.get('cc', '')} {case.get('hpi', '')}"
    triggered: list[str] = []
    new_floor = 5

    for pattern, floor, label in HARD_FLOOR_RULES:
        if pattern.search(text):
            triggered.append(label)
            if floor < new_floor:
                new_floor = floor

    out = dict(verdict)
    original_tier = verdict.get("esi_tier", 5)

    if triggered and new_floor < original_tier:
        out["safety_override"] = True
        out["pre_override_tier"] = original_tier
        out["override_reason"] = triggered
        out["esi_tier"] = new_floor
        out["bucket"] = "NOW" if new_floor <= 2 else ("SOON" if new_floor == 3 else "WAIT")
        # Override → confidence is high (hard rule)
        out["confidence"] = max(out.get("confidence", 0.5), 0.95)
        out["reasoning"] = f"[SAFETY OVERRIDE: {triggered}] " + out.get("reasoning", "")
    else:
        out["safety_override"] = False
        out["override_reason"] = []

    return out


if __name__ == "__main__":
    import json, sys
    case = json.loads(sys.stdin.read())
    print(json.dumps(review(case["case"], case["verdict"]), indent=2))
