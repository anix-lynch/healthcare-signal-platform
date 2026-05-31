"""
Pattern 7 — ranking · Honest baseline orchestrator.

Wraps the existing `reranker.rerank()` (heuristic severity + age/condition
proximity) into the PoliceLineupOutput contract.

The engine takes retrieval candidates + query context, scores each on:
    - age proximity to query
    - condition match
    - LoS quartile signal (severe ⇒ higher rerank)
    - acuity keywords

Returns top-K reranked. We add original_rachel_rank for eval lift math.

This is the FLOOR. A cross-encoder rerank (ms-marco-MiniLM) goes here
when we ship V2 retrieval. Eval must show NDCG lift vs retrieval raw.
"""
from __future__ import annotations
from typing import Iterable

from .reranker import rerank as _engine_rerank
from .schema import PoliceLineupOutput, RankedHit


def lineup(
    query: str,
    candidates: Iterable[dict],
    *,
    case_id: str | None = None,
    top_k: int = 5,
) -> PoliceLineupOutput:
    """
    Rerank retrieval candidates → top-K reranked list.

    Args:
        query: free-text query (or rendered case CC+HPI).
        candidates: iterable of retrieval hit dicts ({source_id/case_id, snippet, score, ...}).
        case_id: encounter identifier.
        top_k: how many to return after rerank.

    Returns:
        PoliceLineupOutput.
    """
    cand_list = list(candidates)
    rachel_rank = {c.get("source_id") or c.get("case_id"): i for i, c in enumerate(cand_list)}

    # The engine expects {"case_id", "snippet", "score"} keys. retrieval's Hit
    # uses "source_id" + "similarity". Normalize before calling.
    engine_input = [
        {
            "case_id": c.get("source_id") or c.get("case_id") or "",
            "snippet": c.get("summary") or c.get("snippet") or "",
            "score": float(c.get("similarity") or c.get("score") or 0.0),
        }
        for c in cand_list
    ]
    reranked = _engine_rerank(query, engine_input, top_k=top_k)

    ranked_hits: list[RankedHit] = []
    for r in reranked:
        sid = r.get("source_id") or r.get("case_id") or "unknown"
        ranked_hits.append(RankedHit(
            source_id=sid,
            rerank_score=float(r.get("rerank_score", r.get("score", 0.0))),
            severity_signals=list(r.get("severity_signals") or r.get("reasons") or []),
            summary=r.get("snippet", "")[:300],
            original_rachel_rank=rachel_rank.get(sid),
        ))

    return PoliceLineupOutput(
        case_id=case_id or "unknown",
        ranked=ranked_hits,
        method="heuristic_severity",
        k_input=len(cand_list),
        k_output=len(ranked_hits),
        ndcg_lift_vs_rachel=None,  # offline eval fills this
    )
