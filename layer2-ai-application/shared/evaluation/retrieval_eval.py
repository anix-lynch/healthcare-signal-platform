"""Pattern 1 (Rachel) eval — retrieval metrics.

🎯 ACCURACY pillar evidence.
"""


def precision_at_k(retrieved_ids: list[str], gold_ids: set[str], k: int) -> float:
    """How many of the top-k were correct."""
    raise NotImplementedError("TODO")


def ndcg_at_k(retrieved_ids: list[str], gold_relevance: dict[str, float], k: int) -> float:
    """Normalized discounted cumulative gain — rewards higher rank for more relevant."""
    raise NotImplementedError("TODO")


def recall_at_k(retrieved_ids: list[str], gold_ids: set[str], k: int) -> float:
    """How many of the gold set we surfaced in top-k."""
    raise NotImplementedError("TODO")
