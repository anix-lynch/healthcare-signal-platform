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

from pydantic import BaseModel, ValidationError


# ────────────────────────────────────────────────────────────────────────────
# Hallucination & citation
# ────────────────────────────────────────────────────────────────────────────
def hallucination_check(generation: str, retrieved_sources: list[dict]) -> bool:
    """LLM-judge: every factual claim in the generation must be supported
    by a retrieved source. Returns True if grounded, False if hallucinated.

    Production gate: if False → trigger refusal or human escalation.
    """
    raise NotImplementedError("TODO: claim extraction + per-claim source-match via judge LLM")


def citation_validation(generation: str, retrieved_ids: set[str]) -> bool:
    """Every cited case_id in the output must exist in the retrieved set.
    No fabricated citations. Returns True if all citations are valid."""
    raise NotImplementedError("TODO: regex extract case_id refs + set membership")


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


def forbidden_actions(generation_intent: dict) -> bool:
    """Block actions the LLM is not authorized to take. Triage system
    suggests, never decides. Returns True if safe, False if forbidden."""
    raise NotImplementedError("TODO: intent classifier + FORBIDDEN_ACTIONS lookup")


def illegal_advice_filter(generation: str) -> bool:
    """Block illegal medication recommendations (controlled substances,
    off-label dangerous combos, etc.). Returns True if clean."""
    raise NotImplementedError("TODO: regex + LLM-judge against an illegal-advice rubric")


# ────────────────────────────────────────────────────────────────────────────
# Confidence calibration
# ────────────────────────────────────────────────────────────────────────────
def confidence_check(stated_confidence: float, evidence_strength: float) -> bool:
    """Warn if model's stated confidence wildly exceeds evidence strength.
    A 99% confident answer with weak evidence = miscalibration → flag."""
    raise NotImplementedError("TODO: |stated - evidence| > threshold → False")


# ────────────────────────────────────────────────────────────────────────────
# Schema enforcement
# ────────────────────────────────────────────────────────────────────────────
def schema_validation(output: dict, schema_cls: type[BaseModel]) -> BaseModel:
    """Validate the LLM output against the declared Pydantic schema.
    Raises if any required field missing / wrong type."""
    raise NotImplementedError("TODO: schema_cls.model_validate(output)")


# ────────────────────────────────────────────────────────────────────────────
# Human-escalation
# ────────────────────────────────────────────────────────────────────────────
def needs_human_escalation(case: dict, generation: dict) -> bool:
    """Hard rules: ESI tier 1, pediatric < 1yo, suicidal ideation, etc.
    → always escalate to a human clinician, regardless of model output.

    Delegates to safety_agent for the medical-domain rule set.
    """
    raise NotImplementedError("TODO: import from app.safety.safety_agent")


# ────────────────────────────────────────────────────────────────────────────
# Pipeline entry point
# ────────────────────────────────────────────────────────────────────────────
def run_output_guardrails(generation: dict, retrieved_sources: list[dict],
                          schema_cls: type[BaseModel] | None = None) -> dict:
    """Sequence: hallucination → citation → forbidden → illegal → confidence
    → schema → escalation. Returns vetted output, raises GuardrailViolation
    on hard fail."""
    raise NotImplementedError("TODO: chain the 7 checks above with audit logging")


class GuardrailViolation(Exception):
    """Raised when an output fails a hard guardrail. Caller must refuse,
    escalate, or downgrade response to a safe default."""
    pass
