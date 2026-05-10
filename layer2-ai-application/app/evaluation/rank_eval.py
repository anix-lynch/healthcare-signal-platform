"""Pattern 7 (Police Lineup) eval — rank metrics.

⚡ SPEED + 🎯 ACCURACY pillar evidence (funnel = speed; rank quality = accuracy).
"""


def ndcg(predicted_ranking: list[str], gold_relevance: dict[str, float]) -> float:
    """NDCG over the full predicted ranking against graded relevance."""
    raise NotImplementedError("TODO")


def mrr(predicted_rankings: list[list[str]], gold_first_relevant: list[str]) -> float:
    """Mean reciprocal rank — how high does the first relevant result land
    on average? Critical for triage UX."""
    raise NotImplementedError("TODO")


def win_rate_vs_baseline(reranked_results, baseline_results, judge_fn) -> float:
    """A/B win-rate of the 3-stage rerank stack vs single-stage BM25 baseline.
    Judge function compares (a) and (b) outputs — production gate >= 0.6."""
    raise NotImplementedError("TODO")
