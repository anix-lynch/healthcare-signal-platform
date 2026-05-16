"""
Pattern 1 — Rachel · Retrieval eval harness.

Five metrics, five reasons:

    Recall@K           "of relevant cases in corpus, how many in our top-K?"
                        Cares about coverage. Crucial for safety-net retrieval.
                        Floor metric — token overlap is enough to pass.

    Precision@K        "of K returned, how many are actually relevant?"
                        Cares about noise. Critical when downstream is Mad Lib
                        grounding — noisy hits = hallucinated chart notes.

    MRR                "how high did the FIRST relevant result rank?"
                        Cares about ordering. Best UX signal.

    NDCG@K             "full-list ordering with graded relevance"
                        Catches subtle reranking wins/losses. The eval you
                        ship in a regression gate.

    ClinicalRecall@K   "of top-K returned, how many share the query's
                        clinical bucket (diagnosis / condition family)?"
                        Ceiling metric — token-overlap retrievers will look
                        good on Recall@K but bleed here when the query says
                        "elephant sitting on chest" and the right answer is
                        a cardiac-event case that never used the word "chest".
                        This is the V1 (BM25) → V2 (dense + rerank) gap.

Golden set shape (one row per query):
    {
        "query_id": "Q-001",
        "query_text": "62yo M chest pain hypertension diaphoresis",
        "relevant_ids": ["L1-002150", "L1-040201", "GUIDE-CHEST-PAIN-ED"],
        "graded_relevance": {"L1-002150": 3, "L1-040201": 2, "GUIDE-CHEST-PAIN-ED": 3},
        "query_bucket": "cardiac_event"   # optional — enables ClinicalRecall@K
    }
"""
from __future__ import annotations
import math
from typing import Iterable, Callable, Optional


# ── Per-query metrics ──────────────────────────────────────────────────────
def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    if not relevant_ids: return float("nan")
    return len(set(retrieved_ids[:k]) & relevant_ids) / len(relevant_ids)


def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    if not retrieved_ids[:k]: return 0.0
    return len(set(retrieved_ids[:k]) & relevant_ids) / k


def reciprocal_rank(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    for i, rid in enumerate(retrieved_ids, 1):
        if rid in relevant_ids:
            return 1.0 / i
    return 0.0


def dcg_at_k(retrieved_ids: list[str], graded: dict[str, int], k: int) -> float:
    """DCG = Σ rel_i / log2(i+1) for i=1..k. Graded relevance integer ≥0."""
    score = 0.0
    for i, rid in enumerate(retrieved_ids[:k], 1):
        rel = graded.get(rid, 0)
        if rel:
            score += rel / math.log2(i + 1)
    return score


def ndcg_at_k(retrieved_ids: list[str], graded: dict[str, int], k: int) -> float:
    ideal_order = sorted(graded.values(), reverse=True)[:k]
    idcg = sum(rel / math.log2(i + 1) for i, rel in enumerate(ideal_order, 1) if rel)
    if idcg == 0: return float("nan")
    return dcg_at_k(retrieved_ids, graded, k) / idcg


def clinical_recall_at_k(
    retrieved_ids: list[str],
    query_bucket: str,
    bucket_of: Callable[[str], Optional[str]],
    k: int,
) -> float:
    """
    Fraction of top-K retrieved hits that share the query's clinical bucket.

    This is the V1→V2 gap metric. A token-overlap retriever (BM25) can score
    well on recall_at_k via shared words while bringing back the wrong
    clinical bucket. A semantic retriever (dense + rerank) should beat BM25
    here even when it loses on raw token recall.

    Unknown buckets (bucket_of returns None) are excluded from numerator and
    denominator — they neither help nor hurt.
    """
    top = retrieved_ids[:k]
    if not top: return float("nan")
    matched = 0
    counted = 0
    for rid in top:
        b = bucket_of(rid)
        if b is None: continue
        counted += 1
        if b == query_bucket:
            matched += 1
    if counted == 0: return float("nan")
    return matched / counted


# ── Corpus-level rollup ────────────────────────────────────────────────────
def evaluate(
    queries: Iterable[dict],
    retriever_fn: Callable[[str, int], list[str]],
    *,
    k_values: tuple[int, ...] = (1, 5, 10),
    bucket_of: Optional[Callable[[str], Optional[str]]] = None,
) -> dict:
    """
    Run a retriever against a golden set, return aggregate metrics.

    Args:
        queries: golden-set rows (see module docstring for shape).
        retriever_fn: f(query_text, k) → list[source_id]
        k_values: report Recall@K, Precision@K, ClinicalRecall@K at these cuts.
        bucket_of: optional f(source_id) → clinical bucket str or None.
                   When provided AND queries carry a "query_bucket" field,
                   ClinicalRecall@K is reported alongside token-overlap recall.

    Returns:
        dict of aggregate metrics. JSON-dumpable.
    """
    queries = list(queries)
    n = len(queries)
    if n == 0: return {"error": "empty golden set"}

    out: dict = {"n_queries": n}
    max_k = max(k_values)

    rrs: list[float] = []
    ndcgs: list[float] = []
    recalls: dict[int, list[float]] = {k: [] for k in k_values}
    precisions: dict[int, list[float]] = {k: [] for k in k_values}
    clinical_recalls: dict[int, list[float]] = {k: [] for k in k_values}

    for q in queries:
        retrieved = retriever_fn(q["query_text"], max_k)
        relevant = set(q.get("relevant_ids") or [])
        graded = {k: int(v) for k, v in (q.get("graded_relevance") or {}).items()}
        q_bucket = q.get("query_bucket")

        for k in k_values:
            recalls[k].append(recall_at_k(retrieved, relevant, k))
            precisions[k].append(precision_at_k(retrieved, relevant, k))
            if bucket_of is not None and q_bucket:
                clinical_recalls[k].append(
                    clinical_recall_at_k(retrieved, q_bucket, bucket_of, k)
                )
        rrs.append(reciprocal_rank(retrieved, relevant))
        if graded:
            ndcgs.append(ndcg_at_k(retrieved, graded, max_k))

    def _mean(xs: list[float]) -> float:
        valid = [x for x in xs if not math.isnan(x)]
        return round(sum(valid) / len(valid), 4) if valid else float("nan")

    for k in k_values:
        out[f"recall@{k}"] = _mean(recalls[k])
        out[f"precision@{k}"] = _mean(precisions[k])
        if clinical_recalls[k]:
            out[f"clinical_recall@{k}"] = _mean(clinical_recalls[k])
    out["mrr"] = _mean(rrs)
    out[f"ndcg@{max_k}"] = _mean(ndcgs) if ndcgs else None
    return out
