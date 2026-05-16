"""
Pattern 4 — Mad Lib · Honest baseline orchestrator.

Wraps the existing template-based `chart_note.generate()` engine into the
structured MadLibOutput contract. The engine produces a chart note + nurse
handoff + patient explanation; we validate citations against Rachel's
returned source_ids before emitting.

Citation rule:
    Every cited source_id must be present in the Rachel hits we received.
    Uncited claims are accepted (the chart note has structured fields and
    can describe vitals directly), but cited source_ids that DON'T resolve
    = hallucination → drop the citation and warn.

This is the FLOOR. An LLM-enhanced path (enhance=True in the engine) can
beat it on prose quality but must not regress on citations_validated.
"""
from __future__ import annotations
from typing import Iterable

from .chart_note import generate as _engine_generate
from .schema import MadLibOutput


def _extract_citations(text: str, valid_ids: set[str]) -> tuple[list[str], list[str]]:
    """
    Naive citation extraction — looks for tokens that match the source_id
    pattern (L1-XXXXXX or P-XXXXXXXXXX) in the text and validates them.
    Returns (kept, dropped).
    """
    import re
    candidates = set(re.findall(r"\b(L1-\d{6}|P-[a-f0-9]{10}|GUIDE-[A-Z0-9-]+)\b", text))
    kept = sorted(c for c in candidates if c in valid_ids)
    dropped = sorted(c for c in candidates if c not in valid_ids)
    return kept, dropped


def generate_note(
    case: dict,
    triage: dict,
    *,
    case_id: str | None = None,
    rachel_hits: Iterable[dict] | None = None,
    enhance: bool = False,
) -> MadLibOutput:
    """
    Generate chart note + handoffs grounded in Rachel hits.

    Args:
        case: ER case dict (cc, hpi, vitals, ...).
        triage: Traffic Light output dict (tier, esi_tier, red_flags, ...).
        case_id: encounter identifier echoed back.
        rachel_hits: iterable of Hit-shaped dicts from Rachel. Source_ids
                     here are the only valid citations.
        enhance: pass-through to engine for optional LLM enhancement.

    Returns:
        MadLibOutput — pydantic-validated.
    """
    rachel_hits = list(rachel_hits or [])
    valid_ids = {h.get("source_id") for h in rachel_hits if h.get("source_id")}

    raw = _engine_generate(case, triage, enhance=enhance)

    chart_note = raw.get("chart_note", "")
    nurse_handoff = raw.get("nurse_handoff", "")
    patient_explanation = raw.get("patient_explanation", "")

    # Validate any citations present in the chart_note body
    kept, dropped = _extract_citations(chart_note, valid_ids)
    warnings: list[str] = []
    if dropped:
        warnings.append(f"dropped {len(dropped)} unresolved citations: {dropped[:3]}")

    method = "llm_enhanced" if (enhance and raw.get("enhanced")) else "template"
    fallback = bool(enhance and not raw.get("enhanced"))
    if fallback:
        warnings.append("LLM enhancement requested but not available — template fallback")

    return MadLibOutput(
        case_id=case_id or "unknown",
        chart_note=chart_note,
        nurse_handoff=nurse_handoff,
        patient_explanation=patient_explanation,
        citations=kept,
        citations_validated=(not dropped),
        faithfulness_score=None,  # offline Ragas run sets this
        generation_method=method,
        fallback_used=fallback,
        warnings=warnings,
    )
