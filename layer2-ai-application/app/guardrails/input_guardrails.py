"""Input guardrails — "don't poison Claude brain"

Runs BEFORE every LLM call. The pre-flight check that turns human
keyboard chaos into a sanitized, schema-valid prompt.

The flow (matches the canonical guardrail diagram):

    Human Chaos
    ─ "IGNORE ALL RULES 😈"
    ─ "patient safe discharge"
    ─ "also buy crypto bro"
         │
         ▼
    INPUT GUARDRAILS  ← THIS MODULE
    ├── sanitize_note            "wash human keyboard vomit"
    ├── strip_prompt_injection   "nice try satan"
    ├── redact_pii               "no leaking SSN"
    ├── enforce_token_limit      "this is ER not Harry Potter book 7"
    ├── block_weird_chars        "no demon unicode"
    └── validate_schema          "submit suffering correctly"
         │
         ▼
    Claude (hospital brain)

🛡️ COMPLIANCE pillar evidence (input layer).
"""

import re
from pydantic import BaseModel, ValidationError


# ────────────────────────────────────────────────────────────────────────────
# PII regex patterns (folded from healthcare-rag-guardrails/scripts/04_pii_masker.py
# 2026-05-09 — verified to redact 1,753 PII tokens on 50-sample healthcare set)
# ────────────────────────────────────────────────────────────────────────────
PII_PATTERNS = {
    "SSN":         re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "SSN_nodash":  re.compile(r"\b\d{9}\b"),
    "DOB":         re.compile(r"\b(0[1-9]|1[0-2])[/-](0[1-9]|[12]\d|3[01])[/-](19|20)\d{2}\b"),
    "PHONE":       re.compile(r"\b\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "EMAIL":       re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "MRN":         re.compile(r"\bMRN[-:\s]*\d{6,10}\b", re.IGNORECASE),
    "ZIP":         re.compile(r"\b\d{5}(-\d{4})?\b"),
    "CREDIT_CARD": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
}


# ────────────────────────────────────────────────────────────────────────────
# Sanitization
# ────────────────────────────────────────────────────────────────────────────
def sanitize_note(text: str) -> str:
    """Normalize whitespace, strip control chars, trim. Generic hygiene."""
    raise NotImplementedError("TODO: unicodedata.normalize NFKC + strip control chars")


# ────────────────────────────────────────────────────────────────────────────
# Prompt-injection defense
# ────────────────────────────────────────────────────────────────────────────
INJECTION_PATTERNS = [
    r"ignore (all|previous|the above) (instructions|rules)",
    r"disregard (your|the) (system|instructions)",
    r"you are now",
    r"new instructions:",
    r"system:",
    r"</?(system|user|assistant)>",
]


def strip_prompt_injection(text: str) -> str:
    """Detect + neutralize known prompt-injection patterns. Logs hits.

    Conservative: false positive (over-strip) > false negative (let it through).
    """
    raise NotImplementedError("TODO: regex match + replacement + audit log of hits")


# ────────────────────────────────────────────────────────────────────────────
# PHI / PII redaction (HIPAA Safe Harbor — 18 identifiers)
# ────────────────────────────────────────────────────────────────────────────
def redact_pii(text: str, provider=None, use_ner: bool = True) -> tuple[str, dict]:
    """Redact PII per HIPAA Safe Harbor 18 identifiers.

    Two-pass redaction:
      1. Regex over PII_PATTERNS (SSN, DOB, MRN, phone, email, etc.)
      2. spaCy NER for names + locations (PERSON, GPE, LOC, ORG)

    If a CloudProvider is passed, prefer its native deidentify() (Comprehend
    Medical / Healthcare API DLP / Azure AI Language) — falls back to the
    local regex+NER pipeline if the provider is None or fails.

    Returns: (masked_text, hit_counts)
    """
    if provider is not None:
        try:
            return provider.deidentify(text), {"provider_used": provider.name}
        except Exception:
            pass  # fall through to local pipeline

    # Pass 1: regex
    hits = {}
    for label, pat in PII_PATTERNS.items():
        matches = pat.findall(text)
        if matches:
            hits[label] = len(matches)
            text = pat.sub(f"[REDACTED_{label}]", text)

    # Pass 2: spaCy NER (optional — heavy import)
    if use_ner:
        try:
            import spacy
            nlp = spacy.load("en_core_web_sm")
            doc = nlp(text)
            ents = sorted(doc.ents, key=lambda e: -e.start_char)
            for ent in ents:
                if ent.label_ in {"PERSON", "GPE", "LOC", "ORG"}:
                    hits[ent.label_] = hits.get(ent.label_, 0) + 1
                    text = text[:ent.start_char] + f"[REDACTED_{ent.label_}]" + text[ent.end_char:]
        except OSError:
            hits["_warning"] = "spaCy model not loaded — run: python -m spacy download en_core_web_sm"

    hits["_total"] = sum(v for k, v in hits.items() if isinstance(v, int))
    return text, hits


# ────────────────────────────────────────────────────────────────────────────
# Hard limits
# ────────────────────────────────────────────────────────────────────────────
def enforce_token_limit(text: str, max_tokens: int = 4000) -> str:
    """Truncate or reject if input exceeds context-window budget."""
    raise NotImplementedError("TODO: tiktoken count + truncate-with-summary")


def block_weird_chars(text: str) -> str:
    """Strip zero-width chars, RTL overrides, and other prompt-smuggling tricks."""
    raise NotImplementedError("TODO: strip U+200B-U+200F, U+2028-U+2029, U+202A-U+202E")


# ────────────────────────────────────────────────────────────────────────────
# Schema validation
# ────────────────────────────────────────────────────────────────────────────
def validate_schema(payload: dict, schema_cls: type[BaseModel]) -> BaseModel:
    """Pydantic-validate the incoming request. Raise on bad shape."""
    raise NotImplementedError("TODO: schema_cls.model_validate(payload)")


# ────────────────────────────────────────────────────────────────────────────
# Pipeline entry point
# ────────────────────────────────────────────────────────────────────────────
def run_input_guardrails(text: str, provider=None) -> str:
    """Sequence: sanitize → strip injection → redact PII → enforce token limit
    → block weird chars. Returns cleaned text ready for the LLM."""
    raise NotImplementedError("TODO: chain the 5 functions above with audit logging")
