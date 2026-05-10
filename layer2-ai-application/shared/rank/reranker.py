"""Pattern 7 — Police Lineup (Rank) | seven-lens

ER context: "Given a chief complaint, rank ALL past cases by clinical
relevance — top-20 surface to the clinician."
GenAI lens: 3-stage rerank stack — BM25 (cheap broad recall) →
cross-encoder (semantic precision) → LLM judge (final ordering with
explanation).

The funnel pattern is the production trick: cheap stage filters before
expensive stage runs. Same shape as Traffic Light gating Mad Lib.

Eval metrics live in app/evaluation/rank_eval.py:
    NDCG · MRR · win-rate vs single-stage baseline
"""


def rerank(query: str, candidates: list[dict], top_k: int = 20) -> list[dict]:
    """Rerank candidates through the 3-stage funnel.

    Stage 1: BM25 keyword match → keep top 200
    Stage 2: cross-encoder (e.g. ms-marco-MiniLM) → keep top 50
    Stage 3: LLM judge with structured output → final top_k with reasons
    """
    raise NotImplementedError("TODO: BM25 + cross-encoder + LLM-judge funnel")
