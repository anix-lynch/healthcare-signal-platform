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
import unicodedata
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
    """Normalize to NFKC, strip ASCII control chars, trim whitespace."""
    text = unicodedata.normalize("NFKC", text)
    # strip ASCII control chars (0x00-0x1F except tab \t=0x09 and newline \n=0x0A) + DEL 0x7F
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text.strip()


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
_INJECTION_RE = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def strip_prompt_injection(text: str) -> str:
    """Detect + neutralize known prompt-injection patterns. Logs hits.

    Conservative: false positive (over-strip) > false negative (let it through).
    """
    hits = []
    for pat in _INJECTION_RE:
        if pat.search(text):
            hits.append(pat.pattern)
    if hits:
        print(f"[INPUT_GUARDRAIL] injection blocked: {hits}")
        for pat in _INJECTION_RE:
            text = pat.sub("[INJECTION_BLOCKED]", text)
    return text


# ────────────────────────────────────────────────────────────────────────────
# PHI / PII redaction (HIPAA Safe Harbor — 18 identifiers)
# ────────────────────────────────────────────────────────────────────────────
def redact_pii(text: str, provider=None, use_ner: bool = True) -> tuple[str, dict]:
    """Redact PII per HIPAA Safe Harbor 18 identifiers.

    Two-pass redaction:
      1. Regex over PII_PATTERNS (SSN, DOB, MRN, phone, email, etc.)
      2. spaCy NER for names + locations (PERSON, GPE, LOC, ORG)

    Returns: (masked_text, hit_counts)
    """
    if provider is not None:
        try:
            return provider.deidentify(text), {"provider_used": provider.name}
        except Exception:
            pass  # fall through to local pipeline

    # Pass 1: regex
    hits: dict = {}
    for label, pat in PII_PATTERNS.items():
        matches = pat.findall(text)
        if matches:
            hits[label] = len(matches)
            text = pat.sub(f"[REDACTED_{label}]", text)

    # Pass 2: spaCy NER (optional)
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
    """Truncate if input exceeds context-window budget."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(text)
        if len(tokens) > max_tokens:
            text = enc.decode(tokens[:max_tokens]) + "\n[TRUNCATED: token limit]"
    except ImportError:
        char_limit = max_tokens * 4
        if len(text) > char_limit:
            text = text[:char_limit] + "\n[TRUNCATED: token limit]"
    return text


def block_weird_chars(text: str) -> str:
    """Strip zero-width, RTL overrides, and other prompt-smuggling unicode."""
    text = re.sub(r"[​-‏]", "", text)   # zero-width chars
    text = re.sub(r"[ - ]", " ", text)  # line/paragraph separators
    text = re.sub(r"[‪-‮]", "", text)   # bidirectional overrides
    text = re.sub(r"[‎‏؜]", "", text)  # directional marks
    return text


# ────────────────────────────────────────────────────────────────────────────
# Schema validation
# ────────────────────────────────────────────────────────────────────────────
def validate_schema(payload: dict, schema_cls: type[BaseModel]) -> BaseModel:
    """Pydantic-validate the incoming request. Raise on bad shape."""
    try:
        return schema_cls.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Schema validation failed: {exc}") from exc


# ────────────────────────────────────────────────────────────────────────────
# Pipeline entry point
# ────────────────────────────────────────────────────────────────────────────
def run_input_guardrails(text: str, provider=None) -> str:
    """Sequence: sanitize → strip injection → redact PII → enforce token limit
    → block weird chars. Returns cleaned text ready for the LLM."""
    text = sanitize_note(text)
    text = strip_prompt_injection(text)
    text, _hits = redact_pii(text, provider=provider)
    text = enforce_token_limit(text)
    text = block_weird_chars(text)
    return text
