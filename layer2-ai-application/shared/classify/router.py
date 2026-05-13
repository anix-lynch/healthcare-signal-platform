"""
ER triage classifier — produces NOW / SOON / WAIT from a patient case.

Deterministic, rule-based, no API calls. Composite score from:
  - chief-complaint red-flag keyword match
  - vital-sign abnormality (HR, RR, SpO2, SBP)
  - age modifier (extremes of age push toward NOW)

Returns a structured TriageDecision with confidence and reasoning, so the
result is auditable and the guardrails layer can inspect it.

Mapping ESI ↔ bucket:
  ESI 1, 2 → NOW   (immediate, can't wait)
  ESI 3    → SOON  (multi-resource, stable)
  ESI 4, 5 → WAIT  (low-acuity)

Cost-routing classifier was moved to shared/classify/cost_router.py.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, asdict, field


# ── Red-flag keyword rules ──────────────────────────────────────────────────
# Each rule: (regex, esi_cap, label). esi_cap is the WORST tier we allow.
# Order matters — first match for a given category wins, but we accumulate flags.
RED_FLAGS = [
    # ESI 1 — life-threatening
    (re.compile(r"cardiac arrest|no pulse|asystole|pulseless", re.I), 1, "cardiac_arrest"),
    (re.compile(r"unresponsive|gcs ?[0-7]\b", re.I),                  1, "unresponsive"),
    (re.compile(r"agonal|apneic|not breathing", re.I),                1, "respiratory_arrest"),
    (re.compile(r"massive (hemorr|bleed)|exsanguinat", re.I),         1, "massive_bleeding"),
    (re.compile(r"intubat|airway compromise", re.I),                  1, "airway_compromise"),

    # ESI 2 — high-risk, can't wait
    (re.compile(r"chest pain|substernal|cardiac sounding", re.I),     2, "chest_pain"),
    (re.compile(r"stroke|fast positive|facial droop|hemipares", re.I),2, "stroke_signs"),
    (re.compile(r"altered mental|ams\b|confused|lethargic", re.I),    2, "altered_mental_status"),
    (re.compile(r"anaphyla|severe allergic|airway swelling", re.I),   2, "anaphylaxis"),
    (re.compile(r"active bleeding|gi bleed|hematemesis", re.I),       2, "active_bleeding"),
    (re.compile(r"respiratory distress|severe asthma|status asth", re.I), 2, "respiratory_distress"),
    (re.compile(r"suicidal|homicidal|sui ideation", re.I),            2, "psych_emergency"),
    (re.compile(r"sepsis|septic shock|qSOFA", re.I),                  2, "sepsis_concern"),
]

# ── Moderate-acuity keywords (floor at ESI 3, multi-resource expected) ─────
# Per ESI Annex: cases that typically need ≥2 resources (labs, imaging, IV
# fluids, specialist consult). Even with stable vitals, these aren't ESI 4-5.
MODERATE_ACUITY = [
    (re.compile(r"abdominal pain|abd pain|rlq|ruq|llq|luq", re.I),    "abd_pain_workup"),
    (re.compile(r"flank pain|kidney stone|renal colic|hematuria", re.I), "renal_workup"),
    (re.compile(r"fracture|deformed|dislocat", re.I),                  "ortho_workup"),
    (re.compile(r"dehydration|severe vomiting|severe diarrhea", re.I), "fluid_workup"),
    (re.compile(r"fall(?!en asleep)|head strike|head injury", re.I),   "fall_workup"),
    (re.compile(r"pregnan|first trimester bleeding", re.I),            "obgyn_workup"),
    (re.compile(r"new onset|acute onset", re.I),                       "acute_workup"),
]

# ── Vital-sign abnormality scoring ─────────────────────────────────────────
def _vital_score(vitals: dict) -> tuple[int, list[str]]:
    """Return (severity_points, flag_list). Severity 0=normal, 3=critical."""
    flags: list[str] = []
    score = 0
    if not vitals:
        return 0, []

    hr = vitals.get("hr")
    rr = vitals.get("rr")
    spo2 = vitals.get("spo2")
    bp = vitals.get("bp")

    if hr is not None:
        if hr == 0 or hr >= 150:
            score += 3; flags.append(f"hr_critical_{hr}")
        elif hr >= 130 or hr <= 40:
            score += 2; flags.append(f"hr_severe_{hr}")
        elif hr >= 110 or hr <= 50:
            score += 1; flags.append(f"hr_abnormal_{hr}")

    if rr is not None:
        if rr == 0 or rr >= 30:
            score += 3; flags.append(f"rr_critical_{rr}")
        elif rr >= 24 or rr <= 8:
            score += 2; flags.append(f"rr_severe_{rr}")
        elif rr >= 20 or rr <= 10:
            score += 1; flags.append(f"rr_abnormal_{rr}")

    if spo2 is not None:
        if spo2 < 88:
            score += 3; flags.append(f"spo2_critical_{spo2}")
        elif spo2 < 92:
            score += 2; flags.append(f"spo2_severe_{spo2}")
        elif spo2 < 95:
            score += 1; flags.append(f"spo2_abnormal_{spo2}")

    if isinstance(bp, str) and "/" in bp:
        try:
            sbp = int(bp.split("/")[0])
            if sbp == 0 or sbp >= 220:
                score += 3; flags.append(f"sbp_critical_{sbp}")
            elif sbp <= 90 or sbp >= 200:
                score += 2; flags.append(f"sbp_severe_{sbp}")
            elif sbp <= 100 or sbp >= 180:
                score += 1; flags.append(f"sbp_abnormal_{sbp}")
        except ValueError:
            pass

    return score, flags


# ── Age modifier ──────────────────────────────────────────────────────────
def _age_modifier(hpi: str) -> int:
    """Pediatric < 1yo or geriatric > 75yo → +1 vital severity."""
    m = re.search(r"\b(\d{1,3})\s*(yo|y/o|year)", hpi or "", re.I)
    m_mo = re.search(r"\b(\d+)\s*(mo|month)", hpi or "", re.I)
    if m_mo:
        return 1
    if m:
        age = int(m.group(1))
        if age < 1 or age > 75:
            return 1
    return 0


# ── Output schema ─────────────────────────────────────────────────────────
@dataclass
class TriageDecision:
    esi_tier: int                # 1-5
    bucket: str                  # NOW / SOON / WAIT
    confidence: float            # 0-1
    reasoning: str               # human-readable trace
    red_flags: list[str] = field(default_factory=list)
    resources_expected: int = 0  # ESI Annex resource count

    def to_dict(self) -> dict:
        return asdict(self)


def _tier_to_bucket(tier: int) -> str:
    if tier <= 2: return "NOW"
    if tier == 3: return "SOON"
    return "WAIT"


def _tier_resources(tier: int) -> int:
    return {1: 5, 2: 4, 3: 2, 4: 1, 5: 0}.get(tier, 0)


# ── Main classifier ────────────────────────────────────────────────────────
def classify(case: dict) -> TriageDecision:
    """
    Classify an ER case into ESI 1-5 + NOW/SOON/WAIT bucket.

    Args:
        case: dict with keys cc (str), vitals (dict), hpi (str), arrival (str)

    Returns:
        TriageDecision (deterministic, JSON-serializable via .to_dict()).
    """
    cc = case.get("cc", "") or ""
    hpi = case.get("hpi", "") or ""
    text = f"{cc} {hpi}".strip()
    vitals = case.get("vitals") or {}

    # 1) red-flag scan
    matched_flags: list[str] = []
    keyword_cap = 5  # default = no urgency forced
    for pattern, cap, label in RED_FLAGS:
        if pattern.search(text):
            matched_flags.append(label)
            if cap < keyword_cap:
                keyword_cap = cap

    # 1b) moderate-acuity scan — floor at ESI 3 if multi-resource workup needed
    moderate_match = False
    for pattern, label in MODERATE_ACUITY:
        if pattern.search(text):
            matched_flags.append(label)
            moderate_match = True

    # 2) vital-sign score
    vital_pts, vital_flags = _vital_score(vitals)
    age_mod = _age_modifier(hpi)
    vital_pts += age_mod
    if age_mod:
        vital_flags.append("extremes_of_age")

    # 3) composite tier — worst of red-flag cap and vital-derived tier
    if vital_pts >= 6:
        vital_tier = 1
    elif vital_pts >= 4:
        vital_tier = 2
    elif vital_pts >= 2:
        vital_tier = 3
    elif vital_pts >= 1:
        vital_tier = 4
    else:
        vital_tier = 5

    final_tier = min(keyword_cap, vital_tier)
    # Moderate-acuity keywords floor the tier at 3 (multi-resource workup)
    if moderate_match and final_tier > 3:
        final_tier = 3

    # 4) confidence — high when keyword AND vitals agree, lower when they diverge
    keyword_signal = keyword_cap < 5
    vital_signal = vital_pts > 0

    if keyword_signal and vital_signal:
        confidence = 0.92
    elif keyword_signal and not vital_signal:
        confidence = 0.78  # keyword alone — we trust the rule but vitals reassuring
    elif vital_signal and not keyword_signal:
        confidence = 0.70  # vitals alone — no narrative context
    elif moderate_match:
        confidence = 0.68  # moderate-acuity keyword caught it
    else:
        confidence = 0.55  # nothing alarming — could be ESI 4/5 or under-documented

    # 5) reasoning trace
    parts = []
    if matched_flags:
        parts.append(f"red_flags={matched_flags}")
    if vital_flags:
        parts.append(f"vital_abnormalities={vital_flags} (severity_pts={vital_pts})")
    if not parts:
        parts.append("no red flags, vitals within normal limits")
    parts.append(f"→ ESI {final_tier}")
    reasoning = " · ".join(parts)

    return TriageDecision(
        esi_tier=final_tier,
        bucket=_tier_to_bucket(final_tier),
        confidence=round(confidence, 3),
        reasoning=reasoning,
        red_flags=matched_flags + vital_flags,
        resources_expected=_tier_resources(final_tier),
    )


def classify_dict(case: dict) -> dict:
    """Same as classify() but returns plain dict (for JSON serialization)."""
    return classify(case).to_dict()


if __name__ == "__main__":
    import json, sys
    sample = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {
        "cc": "chest pain",
        "vitals": {"hr": 105, "rr": 22, "bp": "150/95", "spo2": 96},
        "hpi": "62yo M, substernal pressure 30 min, radiating to left arm",
        "arrival": "walk-in",
    }
    print(json.dumps(classify_dict(sample), indent=2))
