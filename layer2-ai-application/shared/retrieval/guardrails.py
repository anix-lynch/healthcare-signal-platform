"""
Pattern 1 — Rachel · Retrieval guardrails.

Three things that get the hospital sued if Rachel hallucinates them:

    1. CITATION HALLUCINATION  → returned a source_id that doesn't exist
    2. CROSS-PATIENT LEAKAGE   → returned another patient's row when query
                                  was filtered by patient_id
    3. IRRELEVANT JUNK         → all hits below score floor; pretending
                                  these are matches inflates faithfulness

This is the "Llama Guard for retrieval" — runs after the index call,
before Mad Lib touches the hits.
"""
from __future__ import annotations
from typing import Callable, Iterable

from .schema import Hit, RachelOutput


class RetrievalGuardError(ValueError):
    """Raised when retrieval output violates a guard."""


# ── Citation hallucination ─────────────────────────────────────────────────
def validate_citations(
    hits: Iterable[Hit],
    source_exists: Callable[[str], bool],
) -> tuple[list[Hit], list[str]]:
    """
    Drop any hit whose source_id doesn't resolve in the store.

    Returns (kept_hits, dropped_ids). `dropped_ids` empty = all real.
    """
    kept: list[Hit] = []
    dropped: list[str] = []
    for h in hits:
        if source_exists(h.source_id):
            kept.append(h)
        else:
            dropped.append(h.source_id)
    return kept, dropped


# ── Cross-patient leakage ──────────────────────────────────────────────────
def filter_cross_patient(
    hits: Iterable[Hit],
    *,
    query_patient_id: str | None,
    hit_patient_of: Callable[[str], str | None],
) -> tuple[list[Hit], int]:
    """
    Drop any past-case hit whose patient_id matches the query patient.

    Why: "find me similar PAST cases" should mean OTHER patients, not the
    same patient's earlier visits (that's the readmission_history feature,
    not retrieval). Same-patient hits inflate similarity + leak PHI patterns.

    Returns (kept_hits, n_dropped).
    """
    if not query_patient_id:
        return list(hits), 0
    kept: list[Hit] = []
    dropped = 0
    for h in hits:
        if h.type != "past_case":
            kept.append(h)
            continue
        hit_pid = hit_patient_of(h.source_id)
        if hit_pid and hit_pid == query_patient_id:
            dropped += 1
            continue
        kept.append(h)
    return kept, dropped


# ── Relevance floor ────────────────────────────────────────────────────────
def enforce_score_floor(hits: Iterable[Hit], *, min_score: float = 0.3) -> list[Hit]:
    """Drop hits below the floor. Returning empty is BETTER than returning junk."""
    return [h for h in hits if h.similarity >= min_score]


# ── Compose into one call ──────────────────────────────────────────────────
def apply_all_guards(
    output: RachelOutput,
    *,
    source_exists: Callable[[str], bool],
    query_patient_id: str | None = None,
    hit_patient_of: Callable[[str], str | None] | None = None,
    min_score: float = 0.3,
) -> RachelOutput:
    """
    Run citation validation + cross-patient filter + score floor on a
    RachelOutput. Mutates `warnings` to record what was dropped.
    """
    hits = output.retrieved
    warnings = list(output.warnings)

    # 1. citation hallucinations
    hits, missing = validate_citations(hits, source_exists)
    if missing:
        warnings.append(
            f"dropped {len(missing)} hits with unresolved source_ids — "
            f"first: {missing[:3]}"
        )

    # 2. cross-patient leak
    if hit_patient_of is not None and query_patient_id:
        hits, n = filter_cross_patient(
            hits,
            query_patient_id=query_patient_id,
            hit_patient_of=hit_patient_of,
        )
        if n:
            warnings.append(f"suppressed {n} same-patient hits to prevent leakage")

    # 3. relevance floor
    pre = len(hits)
    hits = enforce_score_floor(hits, min_score=min_score)
    if pre and not hits:
        warnings.append(
            f"all hits below score floor {min_score} — returning empty rather than junk"
        )

    return output.model_copy(update={"retrieved": hits, "warnings": warnings})
