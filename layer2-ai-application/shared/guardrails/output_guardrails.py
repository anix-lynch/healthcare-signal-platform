"""Output guardrails — "don't let Claude go insane"

Runs AFTER every LLM response. The post-flight check that catches
hallucinations, missing citations, forbidden actions, schema breaks.

The flow (matches the canonical guardrail diagram):

    Claude says
    ─ "✨ patient aura stable ✨"
    ─ "maybe discharge?"
         │
         ▼
    OUTPUT GUARDRAILS  ← THIS MODULE
    ├── hallucination_check       "bro made up a disease"
    ├── citation_validation       "show me the guideline"
    ├── forbidden_actions         "AI you are NOT a neurosurgeon"
    ├── illegal_advice_filter     "DO NOT prescribe cocaine"
    ├── confidence_check          "why are you 99% confident dumbass"
    ├── schema_validation         "WHERE IS THE URGENCY FIELD"
    └── human_escalation          "this above your salary grade"
         │
         ▼
    Official ER Output
    (slightly less medically cursed)

🛡️ COMPLIANCE + 🎯 ACCURACY pillar evidence (output layer).
"""

import re
from pydantic import BaseModel, ValidationError


# ────────────────────────────────────────────────────────────────────────────
# Hallucination & citation
# ────────────────────────────────────────────────────────────────────────────
def hallucination_check(generation: str, retrieved_sources: list[dict]) -> bool:
    """Coverage-based hallucination check (deterministic — no LLM judge required).

    Strategy: build a 4+-char token set from all retrieved source text, then
    measure the overlap fraction against the generation's tokens.
    Coverage >= 0.70 → grounded. Below → likely hallucinated.

    A production upgrade would run a per-claim LLM judge; this path is fast,
    auditable, and API-key-free.

    Returns True if grounded, False if likely hallucinated.
    """
    if not retrieved_sources:
        return False  # no sources → can't ground anything

    source_text = " ".join(
        str(src.get("text", src.get("content", src.get("summary", ""))))
        for src in retrieved_sources
    ).lower()
    source_tokens = set(re.findall(r"\b\w{4,}\b", source_text))

    gen_tokens = set(re.findall(r"\b\w{4,}\b", generation.lower()))
    if not gen_tokens:
        return True  # empty generation is vacuously grounded

    coverage = len(gen_tokens & source_tokens) / len(gen_tokens)
    return coverage >= 0.70


def citation_validation(generation: str, retrieved_ids: set[str]) -> bool:
    """Every cited case_id in the output must exist in the retrieved set.
    Returns True if all citations are valid (or if none are present)."""
    cited = set(re.findall(r"\bL\d+-\d{6}\b", generation))  # e.g. L1-000001
    if not cited:
        return True  # no citations → vacuously valid
    return cited.issubset(retrieved_ids)


# ────────────────────────────────────────────────────────────────────────────
# Action / advice gates
# ────────────────────────────────────────────────────────────────────────────
FORBIDDEN_ACTIONS = {
    "diagnose_definitively",
    "prescribe_medication",
    "perform_surgery",
    "discharge_decision_alone",
    "override_clinician",
}

_ILLEGAL_ADVICE_RE = [
    re.compile(r"\bprescribe\b", re.IGNORECASE),
    re.compile(r"\badminister\b.{0,30}\b(mg|dose|units?|injection)\b", re.IGNORECASE),
    re.compile(r"\b(cocaine|oxycodone|fentanyl|heroin)\b", re.IGNORECASE),
    re.compile(r"\bdo not call 911\b", re.IGNORECASE),
    re.compile(r"\bdischarge (the )?patient (immediately|now|today)\b", re.IGNORECASE),
]


def forbidden_actions(generation_intent: dict) -> bool:
    """Block if any intent maps to a clinically forbidden action.
    Returns True if safe, False if forbidden."""
    intents = set(generation_intent.get("intents", []))
    action = generation_intent.get("action", "")
    if action:
        intents.add(action)
    return not bool(intents & FORBIDDEN_ACTIONS)


def illegal_advice_filter(generation: str) -> bool:
    """Block illegal medication recommendations and dangerous directives.
    Returns True if clean, False if illegal advice detected."""
    for pat in _ILLEGAL_ADVICE_RE:
        if pat.search(generation):
            return False
    return True


# ────────────────────────────────────────────────────────────────────────────
# Confidence calibration
# ────────────────────────────────────────────────────────────────────────────
CONFIDENCE_FLOOR = 0.60


def confidence_check(stated_confidence: float, evidence_strength: float = 1.0) -> bool:
    """Pass if confidence is above the floor AND not wildly exceeding evidence.
    Returns True when it is safe to act on the model's output."""
    if stated_confidence < CONFIDENCE_FLOOR:
        return False
    if stated_confidence - evidence_strength > 0.25:
        return False
    return True


# ────────────────────────────────────────────────────────────────────────────
# Schema enforcement
# ────────────────────────────────────────────────────────────────────────────
def schema_validation(output: dict, schema_cls: type[BaseModel]) -> BaseModel:
    """Validate the LLM output against the declared Pydantic schema.
    Raises GuardrailViolation if any required field is missing or wrong type."""
    try:
        return schema_cls.model_validate(output)
    except ValidationError as exc:
        raise GuardrailViolation(f"Output schema invalid: {exc}") from exc


# ────────────────────────────────────────────────────────────────────────────
# Human-escalation
# ────────────────────────────────────────────────────────────────────────────
def needs_human_escalation(case: dict, generation: dict) -> bool:
    """Always escalate for ESI 1, safety_override, low confidence, psych emergency."""
    tier = generation.get("esi_tier", 5)
    confidence = generation.get("confidence", 0.0)

    if tier == 1:
        return True
    if generation.get("safety_override"):
        return True
    if not confidence_check(confidence):
        return True

    text = f"{case.get('cc', '')} {case.get('hpi', '')}".lower()
    if any(k in text for k in ["suicidal", "homicidal", "self harm", "suicide"]):
        return True

    return False


# ────────────────────────────────────────────────────────────────────────────
# Pipeline entry point
# ────────────────────────────────────────────────────────────────────────────
def run_output_guardrails(generation: dict, retrieved_sources: list[dict],
                          schema_cls: type[BaseModel] | None = None) -> dict:
    """Sequence: hallucination → citation → forbidden → illegal → confidence
    → schema → escalation. Returns vetted output with audit log attached.
    Raises GuardrailViolation on hard fail."""
    gen_text = str(generation)
    retrieved_ids = {str(s.get("case_id", s.get("id", ""))) for s in retrieved_sources}

    audit: dict = {}

    audit["hallucination"] = hallucination_check(gen_text, retrieved_sources)
    if not audit["hallucination"]:
        raise GuardrailViolation("Hallucination check failed — generation not grounded in sources")

    audit["citation"] = citation_validation(gen_text, retrieved_ids)
    if not audit["citation"]:
        raise GuardrailViolation("Citation validation failed — fabricated case_id in output")

    intent = generation if isinstance(generation, dict) else {}
    audit["forbidden_actions"] = forbidden_actions(intent)
    if not audit["forbidden_actions"]:
        raise GuardrailViolation("Forbidden action detected in generation intent")

    audit["illegal_advice"] = illegal_advice_filter(gen_text)
    if not audit["illegal_advice"]:
        raise GuardrailViolation("Illegal medical advice detected in generation")

    confidence = generation.get("confidence", 1.0) if isinstance(generation, dict) else 1.0
    audit["confidence"] = confidence_check(confidence)

    if schema_cls is not None:
        schema_validation(generation if isinstance(generation, dict) else {}, schema_cls)
        audit["schema"] = True

    audit["needs_human"] = needs_human_escalation({}, generation if isinstance(generation, dict) else {})

    if isinstance(generation, dict):
        generation["_guardrail_audit"] = audit
    return generation


class GuardrailViolation(Exception):
    """Raised when an output fails a hard guardrail. Caller must refuse,
    escalate, or downgrade to a safe default."""
    pass
