"""Pattern 1 (Rachel) eval — retrieval metrics on the Layer 1 corpus.

Real metrics: Precision@K, Recall@K, NDCG@K.

Golden labels are derived programmatically — for each held-out query case,
the gold set is "every other row sharing (gender, medical_condition, age_band)".
This is a defensible baseline: it measures whether BM25 retrieves
demographically-and-clinically-similar past cases.

Run:
    cd layer2-ai-application
    python -m shared.evaluation.retrieval_eval

Output:
    apps/er-triage/outputs/eval_rachel.json

🎯 ACCURACY pillar evidence.
"""

from __future__ import annotations
import json
import math
import random
import sys
import argparse
from pathlib import Path
from collections import defaultdict

HERE = Path(__file__).resolve().parent
LAYER2_ROOT = HERE.parent.parent
ER_TRIAGE = LAYER2_ROOT / "apps" / "er-triage"

from shared.retrieval.retriever import _ensure_index, search


# ── Metrics ─────────────────────────────────────────────────────────────────
def precision_at_k(retrieved_ids: list[str], gold_ids: set[str], k: int) -> float:
    if k == 0: return 0.0
    top = retrieved_ids[:k]
    if not top: return 0.0
    return sum(1 for r in top if r in gold_ids) / len(top)


def recall_at_k(retrieved_ids: list[str], gold_ids: set[str], k: int) -> float:
    if not gold_ids: return 0.0
    top = retrieved_ids[:k]
    return sum(1 for r in top if r in gold_ids) / len(gold_ids)


def ndcg_at_k(retrieved_ids: list[str], gold_ids: set[str], k: int) -> float:
    """Binary-relevance NDCG@K."""
    top = retrieved_ids[:k]
    dcg = sum((1.0 / math.log2(i + 2)) for i, rid in enumerate(top) if rid in gold_ids)
    n_relevant = min(len(gold_ids), k)
    idcg = sum((1.0 / math.log2(i + 2)) for i in range(n_relevant))
    return dcg / idcg if idcg > 0 else 0.0


def mrr(retrieved_ids: list[str], gold_ids: set[str]) -> float:
    """Mean reciprocal rank — first-hit position."""
    for i, rid in enumerate(retrieved_ids):
        if rid in gold_ids:
            return 1.0 / (i + 1)
    return 0.0


# ── Golden-set construction ─────────────────────────────────────────────────
def _age_band(age: int) -> str:
    if age < 18:  return "0-17"
    if age < 35:  return "18-34"
    if age < 55:  return "35-54"
    if age < 75:  return "55-74"
    return "75+"


def build_golden_set(idx, n_queries: int = 50, seed: int = 13) -> list[dict]:
    """
    Sample n_queries cases at random; for each, the gold set is all OTHER
    cases sharing (gender, medical_condition, age_band).
    """
    rnd = random.Random(seed)
    by_key: dict[tuple, list[str]] = defaultdict(list)
    for i, doc in enumerate(idx.docs):
        raw = doc.get("raw") or {}
        try:
            age = int(float(raw.get("Age", 0)))
        except (TypeError, ValueError):
            continue
        key = (raw.get("Gender", ""), raw.get("Medical Condition", ""), _age_band(age))
        by_key[key].append(doc["case_id"])

    candidates = [
        i for i, doc in enumerate(idx.docs)
        if (raw := doc.get("raw") or {})
        and raw.get("Gender") and raw.get("Medical Condition") and raw.get("Age")
    ]
    chosen = rnd.sample(candidates, k=min(n_queries, len(candidates)))

    queries = []
    for doc_idx in chosen:
        doc = idx.docs[doc_idx]
        raw = doc["raw"]
        try:
            age = int(float(raw["Age"]))
        except (TypeError, ValueError):
            continue
        gender = raw["Gender"]
        condition = raw["Medical Condition"]
        admission = raw.get("Admission Type", "")
        key = (gender, condition, _age_band(age))
        gold_ids = set(by_key[key]) - {doc["case_id"]}
        if not gold_ids:
            continue
        query_text = f"{age}yo {gender} {condition} {admission}"
        queries.append({
            "query_id": doc["case_id"],
            "query": query_text,
            "gold_ids": gold_ids,
            "key": list(key),
        })
    return queries


# ── Run ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-queries", type=int, default=50)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--out", default=str(ER_TRIAGE / "outputs" / "eval_rachel.json"))
    args = parser.parse_args()

    print(f"Loading index...")
    idx = _ensure_index()
    print(f"Index size: {idx.N:,} docs")

    print(f"Building golden set ({args.n_queries} queries)...")
    queries = build_golden_set(idx, n_queries=args.n_queries, seed=args.seed)
    print(f"Constructed {len(queries)} valid queries (some samples skipped if no peers).")

    p_at_k = []
    r_at_k = []
    ndcg = []
    rr = []
    per_query = []

    for q in queries:
        hits = search(q["query"], k=args.k)
        retrieved_ids = [h["case_id"] for h in hits]
        p = precision_at_k(retrieved_ids, q["gold_ids"], args.k)
        r = recall_at_k(retrieved_ids, q["gold_ids"], args.k)
        ng = ndcg_at_k(retrieved_ids, q["gold_ids"], args.k)
        rr_score = mrr(retrieved_ids, q["gold_ids"])
        p_at_k.append(p); r_at_k.append(r); ndcg.append(ng); rr.append(rr_score)
        per_query.append({
            "query_id": q["query_id"],
            "query": q["query"],
            "gold_size": len(q["gold_ids"]),
            "precision_at_k": round(p, 4),
            "recall_at_k": round(r, 4),
            "ndcg_at_k": round(ng, 4),
            "mrr": round(rr_score, 4),
            "top_3": retrieved_ids[:3],
        })

    n = len(queries)
    metrics = {
        "n_queries": n,
        "k": args.k,
        "precision_at_k_mean": round(sum(p_at_k) / n, 4) if n else 0.0,
        "recall_at_k_mean":    round(sum(r_at_k) / n, 4) if n else 0.0,
        "ndcg_at_k_mean":      round(sum(ndcg)   / n, 4) if n else 0.0,
        "mrr_mean":            round(sum(rr)     / n, 4) if n else 0.0,
        "corpus_size":         idx.N,
        "retriever":           "BM25 (k1=1.5, b=0.75) over Layer 1 healthcare_dataset.csv",
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"metrics": metrics, "per_query": per_query}, indent=2))

    print("=" * 60)
    print("RACHEL (Pattern 1 — retrieval) eval")
    print("=" * 60)
    print(f"  corpus size:              {metrics['corpus_size']:,}")
    print(f"  queries evaluated:        {metrics['n_queries']}")
    print(f"  K:                        {metrics['k']}")
    print(f"  Precision@{args.k} (mean): {metrics['precision_at_k_mean']:.4f}")
    print(f"  Recall@{args.k} (mean):    {metrics['recall_at_k_mean']:.4f}")
    print(f"  NDCG@{args.k} (mean):      {metrics['ndcg_at_k_mean']:.4f}")
    print(f"  MRR (mean):                {metrics['mrr_mean']:.4f}")
    print(f"\n→ artifact: {out_path}")


if __name__ == "__main__":
    main()
