"""
Pattern 4 — generation · ER chart-note generator.

Takes a case + triage decision (from Pattern 2) and renders five human-facing
views of the same underlying decision:

    1. chart_note         — structured SOAP-style note for the EHR
    2. nurse_handoff      — 1-2 sentence brief for shift change
    3. patient_explanation — lay-language, what to expect now
    4. clinician_summary  — 2-line punchline for the attending
    5. executive_summary  — 1-line for the operations dashboard

Implementation: DETERMINISTIC TEMPLATES.
Why deterministic, not LLM:
    - faithfulness is structurally guaranteed (every fact comes from inputs)
    - no hallucination surface
    - audit-friendly + reproducible (compliance bar)
    - cost: $0 / inference, 0ms latency
    - LLM uplift can be added later via shared.cloud.adapter without rewriting
      this contract — the dict shape stays the same.

If ANTHROPIC_API_KEY is set AND `enhance=True` is passed, the chart_note's
narrative paragraph can optionally be polished via Claude — but only over
the *already-grounded* content, never to add new facts.
"""

from __future__ import annotations
from typing import Any


# ── Bucket-aware tone phrases ──────────────────────────────────────────────
BUCKET_TONE = {
    "NOW":  ("immediate evaluation",     "resuscitation room",      "right now"),
    "SOON": ("prompt evaluation",        "main ED bed",              "shortly"),
    "WAIT": ("non-urgent evaluation",    "fast track / waiting room", "after higher-acuity patients"),
}

ESI_LABEL = {
    1: "ESI 1 — resuscitation",
    2: "ESI 2 — emergent",
    3: "ESI 3 — urgent",
    4: "ESI 4 — less urgent",
    5: "ESI 5 — non-urgent",
}


def _vitals_line(vitals: dict | None) -> str:
    if not vitals:
        return "Vitals: not recorded."
    parts = []
    for k, label in [("hr", "HR"), ("rr", "RR"), ("bp", "BP"), ("spo2", "SpO2")]:
        v = vitals.get(k)
        if v is None:
            continue
        unit = "%" if k == "spo2" else ""
        parts.append(f"{label} {v}{unit}")
    return "Vitals: " + ", ".join(parts) + "." if parts else "Vitals: not recorded."


def _flag_phrase(flags: list[str]) -> str:
    if not flags:
        return "no red flags identified"
    pretty = [f.replace("_", " ") for f in flags]
    return "red flags: " + ", ".join(pretty)


def _disposition(triage: dict) -> str:
    bucket = triage.get("bucket", "WAIT")
    tone, location, when = BUCKET_TONE[bucket]
    if triage.get("needs_human_escalation"):
        return f"Escalate to attending physician for {tone}; place in {location}, see {when}."
    return f"{tone.capitalize()}; place in {location}, see {when}."


def _chart_note(case: dict, triage: dict) -> str:
    cc = case.get("cc", "(not documented)")
    hpi = case.get("hpi", "(no HPI documented)")
    arrival = case.get("arrival", "unknown arrival mode")
    tier = triage.get("esi_tier", 5)

    lines = [
        f"CHIEF COMPLAINT: {cc}",
        f"ARRIVAL: {arrival}",
        f"HISTORY OF PRESENT ILLNESS: {hpi}",
        _vitals_line(case.get("vitals")),
        "",
        "ASSESSMENT:",
        f"  Triage classification: {ESI_LABEL.get(tier, f'ESI {tier}')}.",
        f"  Bucket: {triage.get('bucket', '?')} (resources expected: "
        f"{triage.get('resources_expected', 0)}).",
        f"  Decision basis: {_flag_phrase(triage.get('red_flags') or [])}.",
        f"  Confidence: {triage.get('confidence', 0):.2f}.",
    ]
    if triage.get("safety_override"):
        lines.append(
            f"  ⚠ SAFETY OVERRIDE FIRED — {', '.join(triage.get('override_reason', []))}; "
            f"tier raised from ESI {triage.get('pre_override_tier', '?')} to ESI {tier}."
        )
    lines.append("")
    lines.append(f"PLAN / DISPOSITION: {_disposition(triage)}")
    if triage.get("needs_human_escalation"):
        lines.append("HUMAN ESCALATION: REQUIRED — clinician review before final disposition.")
    lines.append("")
    lines.append(f"AUDIT: {triage.get('reasoning', '')}")
    return "\n".join(lines)


def _nurse_handoff(case: dict, triage: dict) -> str:
    cc = case.get("cc", "complaint")
    bucket = triage.get("bucket", "WAIT")
    tier = triage.get("esi_tier", 5)
    flags = triage.get("red_flags") or []
    flag_str = f", flags: {', '.join(flags[:3])}" if flags else ""
    escalation = " — needs MD review" if triage.get("needs_human_escalation") else ""
    return (
        f"{bucket} / ESI {tier}: {cc}{flag_str}{escalation}. "
        f"{_disposition(triage)}"
    )


def _patient_explanation(case: dict, triage: dict) -> str:
    bucket = triage.get("bucket", "WAIT")
    cc = case.get("cc", "your symptoms")
    if bucket == "NOW":
        return (
            f"Based on {cc}, we're going to see you immediately. "
            f"A clinician will be with you right away. "
            f"You may be moved to a treatment room before completing registration."
        )
    if bucket == "SOON":
        return (
            f"Based on {cc}, you'll be seen as soon as a bed is available. "
            f"This usually means within the hour. "
            f"You may need lab tests or imaging — please stay nearby."
        )
    return (
        f"Based on {cc}, your case is non-urgent. "
        f"You'll be seen after patients with more time-sensitive needs. "
        f"Wait times can vary; thank you for your patience."
    )


def _clinician_summary(case: dict, triage: dict) -> str:
    cc = case.get("cc", "?")
    tier = triage.get("esi_tier", 5)
    flags = triage.get("red_flags") or []
    flag_str = f"; flags: {', '.join(flags[:5])}" if flags else ""
    override = " [OVERRIDE]" if triage.get("safety_override") else ""
    return f"ESI {tier} / {triage.get('bucket', '?')}{override}: {cc}{flag_str}."


def _executive_summary(case: dict, triage: dict) -> str:
    return (
        f"{triage.get('bucket', 'WAIT')} | ESI {triage.get('esi_tier', 5)} | "
        f"conf {triage.get('confidence', 0):.2f} | "
        f"{'esc' if triage.get('needs_human_escalation') else 'auto'}"
    )


# ── Public API ─────────────────────────────────────────────────────────────
def generate(case: dict, triage: dict, enhance: bool = False) -> dict:
    """
    Render five human-facing views of one triage decision.

    Args:
        case: original case dict (cc, vitals, hpi, arrival)
        triage: dict from apps/er-triage/classify/esi_classifier.classify()
        enhance: if True AND ANTHROPIC_API_KEY is set, polish the narrative
                 via Claude WITHOUT adding new facts. Default False (deterministic).

    Returns:
        dict with five string fields — all derivable from inputs (faithful by
        construction). JSON-serializable.
    """
    if not isinstance(case, dict) or not case.get("cc"):
        raise ValueError("case must be a dict with at least a 'cc' field")
    if not isinstance(triage, dict) or "esi_tier" not in triage:
        raise ValueError("triage must include esi_tier")

    out = {
        "chart_note":          _chart_note(case, triage),
        "nurse_handoff":       _nurse_handoff(case, triage),
        "patient_explanation": _patient_explanation(case, triage),
        "clinician_summary":   _clinician_summary(case, triage),
        "executive_summary":   _executive_summary(case, triage),
        "_generation_mode":    "deterministic_template",
    }

    if enhance:
        polished = _maybe_enhance(out["chart_note"], case, triage)
        if polished:
            out["chart_note"] = polished
            out["_generation_mode"] = "deterministic_template+llm_polish"

    return out


def _maybe_enhance(chart_note: str, case: dict, triage: dict) -> str | None:
    """
    Optional LLM polish. Returns None if no API key or call fails — the
    deterministic note is always preserved. Never adds new facts; only
    rewrites the narrative paragraphs for tone/grammar.
    """
    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
        client = anthropic.Anthropic()
        prompt = (
            "You are polishing an ER chart note for a clinician. "
            "Rewrite the prose for tone and grammar ONLY. Do NOT add, remove, "
            "or reword any clinical fact, vital sign, ESI tier, red flag, or "
            "disposition. Preserve all numeric values exactly. Keep the same "
            "section headers. Return only the rewritten note.\n\n"
            f"---\n{chart_note}\n---"
        )
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()
    except Exception:
        return None  # keep deterministic note on any failure


# Legacy entry-point kept for backwards-compat with the old stub signature.
def draft_chart_note(case: dict, retrieved_cases: list[dict] | None = None):
    """Legacy alias — use generate(case, triage) instead.

    The old signature took retrieved_cases (Pattern 1 RAG output). For the
    current vertical slice, the triage decision itself is the source of truth.
    """
    raise NotImplementedError(
        "Use shared.generate.chart_note.generate(case, triage) instead. "
        "The retrieval-grounded variant is wired in once Pattern 1 ships."
    )


if __name__ == "__main__":
    import json, sys
    payload = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {
        "case": {
            "cc": "chest pain",
            "vitals": {"hr": 105, "rr": 22, "bp": "150/95", "spo2": 96},
            "hpi": "62yo M, substernal pressure 30 min, radiating to left arm",
            "arrival": "walk-in",
        },
        "triage": {
            "esi_tier": 2, "bucket": "NOW", "confidence": 0.92,
            "reasoning": "red_flags=['chest_pain']", "red_flags": ["chest_pain"],
            "resources_expected": 4, "safety_override": False, "override_reason": [],
            "needs_human_escalation": False,
        },
    }
    print(json.dumps(generate(payload["case"], payload["triage"]), indent=2))
