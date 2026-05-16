"""
Pattern 1 — Rachel · Honest baseline orchestrator.

What this is:
    Wraps BM25 and (now) dense embedding retrievers into the structured
    RachelOutput contract that services/rag-api and Mad Lib consume.

    method="bm25"   token-overlap floor. Free, deterministic, fast.
    method="dense"  sentence-transformers MiniLM cosine. Semantic match on
                    synonyms / paraphrase. Falls back to BM25 with
                    fallback_used=True if the encoder is missing or fails.

What this is NOT (yet):
    - hybrid BM25 + dense + RRF (queued)
    - cross-encoder rerank (queued)

This file is the FLOOR. If a fancier retriever doesn't beat BM25 + guards
on Recall@10 AND clinical_recall@10, the fancier retriever is broken —
not impressive.
"""
from __future__ import annotations
import time
import re
from typing import Literal

from .retriever import (
    search as _bm25_search,
    _ensure_index,
)
from . import dense as _dense
from .schema import RachelOutput, Hit
from .guardrails import apply_all_guards
from .identity import patient_of as _patient_of, identity_available as _identity_available


Method = Literal["bm25", "dense"]


# Heuristic relevance reason — replace with cross-encoder when V2 lands.
def _why_relevant(query: str, snippet: str, *, method: str) -> str:
    q_tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
    s_tokens = set(re.findall(r"[a-z0-9]+", snippet.lower()))
    shared = sorted(q_tokens & s_tokens, key=len, reverse=True)[:4]
    if shared:
        return "shared tokens: " + ", ".join(shared)
    if method == "dense":
        return "ranked by semantic similarity; no literal token overlap"
    return "ranked by BM25 score; no token overlap with query"


def _bm25_score_to_similarity(score: float, *, scale: float = 12.0) -> float:
    """Squash unbounded BM25 score into 0-1. scale tuned to typical max ~12."""
    return round(min(1.0, score / scale), 4)


def _dense_score_to_similarity(score: float) -> float:
    """MiniLM cosine after normalize_embeddings ∈ [-1, 1]; clamp to [0, 1]."""
    return round(max(0.0, min(1.0, score)), 4)


# ── Public API ─────────────────────────────────────────────────────────────
def retrieve(
    query: str,
    *,
    query_case_id: str = "unknown",
    k: int = 10,
    patient_id: str | None = None,
    min_score: float = 0.0,
    method: Method = "bm25",
) -> RachelOutput:
    """
    Run retrieval, wrap into RachelOutput, apply guards.

    Args:
        query: free-text query (CC + HPI rendered, or just CC).
        query_case_id: identifier echoed back in output.
        k: how many hits to attempt to retrieve.
        patient_id: when set, same-patient hits are filtered out.
        min_score: relevance floor (0-1 similarity space).
        method: "bm25" (default) or "dense". Dense path falls back to BM25
                with fallback_used=True if sentence-transformers is missing
                or model load fails.

    Returns:
        RachelOutput — pydantic-validated, JSON-serializable.
    """
    t0 = time.time()
    warnings: list[str] = []
    fallback_used = False
    chosen = method

    if method == "dense":
        try:
            raw_hits = _dense.search(query, k=k)
            score_to_sim = _dense_score_to_similarity
        except RuntimeError as e:
            warnings.append(
                f"dense path failed ({type(e).__name__}: {e}); BM25 fallback"
            )
            raw_hits = _bm25_search(query, k=k)
            score_to_sim = _bm25_score_to_similarity
            chosen = "bm25_fallback"
            fallback_used = True
    else:
        raw_hits = _bm25_search(query, k=k)
        score_to_sim = _bm25_score_to_similarity

    hits = [
        Hit(
            source_id=h["case_id"],
            type="past_case",
            similarity=score_to_sim(h["score"]),
            summary=h["snippet"][:300],
            why_relevant=_why_relevant(query, h["snippet"], method=chosen),
        )
        for h in raw_hits
    ]

    index = _ensure_index()
    valid_ids = {d["case_id"] for d in index.docs}

    def _source_exists(sid: str) -> bool:
        return sid in valid_ids

    out = RachelOutput(
        pattern="rachel_retrieval",
        query_case_id=query_case_id,
        retrieved=hits,
        retrieval_method=chosen,
        fallback_used=fallback_used,
        latency_ms=int((time.time() - t0) * 1000),
        warnings=warnings,
    )

    # hit_patient_of: wired to Layer 1's patient_identity_map.json when available.
    # When the map is missing AND the caller passed a query patient_id, we
    # cannot enforce the cross-patient guard — surface that as a single
    # warning so downstream knows the protection is degraded, not silent.
    if _identity_available():
        hit_patient_of = _patient_of
    else:
        hit_patient_of = None
        if patient_id:
            out.warnings.append(
                "patient identity map unavailable — cross-patient leak guard "
                "is a no-op for this query (run scripts/patient_identity.py "
                "in layer1-data-backbone to enable)"
            )

    return apply_all_guards(
        out,
        source_exists=_source_exists,
        query_patient_id=patient_id,
        hit_patient_of=hit_patient_of,
        min_score=min_score,
    )


def retrieve_for_case(
    case: dict,
    *,
    query_case_id: str = "unknown",
    k: int = 5,
    patient_id: str | None = None,
    method: Method = "bm25",
) -> RachelOutput:
    """Convenience: build a Rachel query from an ER triage case payload."""
    cc = case.get("cc", "") or ""
    hpi = case.get("hpi", "") or ""
    query = f"{cc} {hpi}".strip()
    return retrieve(
        query,
        query_case_id=query_case_id,
        k=k,
        patient_id=patient_id,
        method=method,
    )


if __name__ == "__main__":
    import sys, json
    case_text = sys.stdin.read().strip() if not sys.stdin.isatty() else "62yo male chest pain hypertension"
    out = retrieve(case_text, query_case_id="DEMO-001", k=5)
    print(out.model_dump_json(indent=2))
