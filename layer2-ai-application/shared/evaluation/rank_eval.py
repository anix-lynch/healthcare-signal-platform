"""Pattern 7 (Police Lineup) eval — reranking metrics.

Compares Police Lineup (re-rank by outcome severity) against the Rachel
baseline (BM25 only) on the same query set.

Relevance signal for NDCG:
    A retrieved case is "highly relevant" if it has Emergency admission AND
    Abnormal test result. Medium if either alone. Low otherwise.

Run:
    cd layer2-ai-application
    python -m shared.evaluation.rank_eval

Output:
    apps/er-triage/outputs/eval_police_lineup.json

🎯 ACCURACY pillar evidence.
"""

from __future__ import annotations
import json
import math
import random
import sys
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAYER2_ROOT = HERE.parent.parent
ER_TRIAGE = LAYER2_ROOT / "apps" / "er-triage"

from shared.retrieval.retriever import _ensure_index, search
from shared.rank.reranker import rerank


def _relevance_for_hit(hit: dict) -> int:
    raw = hit.get("raw") or {}
    is_emergency = raw.get("Admission Type") == "Emergency"
    is_abnormal = raw.get("Test Results") == "Abnormal"
    if is_emergency and is_abnormal: return 2
    if is_emergency or is_abnormal:  return 1
    return 0


def ndcg_at_k(graded_relevance: list[int], k: int) -> float:
    top = graded_relevance[:k]
    dcg = sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(top))
    ideal = sorted(graded_relevance, reverse=True)[:k]
    idcg = sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


def mrr(graded_relevance: list[int]) -> float:
    for i, r in enumerate(graded_relevance):
        if r > 0:
            return 1.0 / (i + 1)
    return 0.0


def ndcg(predicted_ranking: list[str], gold_relevance: dict[str, float]) -> float:
    """Generic NDCG used by harness — graded relevance from a dict map."""
    grades = [int(gold_relevance.get(c, 0)) for c in predicted_ranking]
    return ndcg_at_k(grades, len(grades))


def win_rate_vs_baseline(reranked_grades: list[list[int]], baseline_grades: list[list[int]], k: int = 5) -> float:
    wins = 0
    for r, b in zip(reranked_grades, baseline_grades):
        if ndcg_at_k(r, k) > ndcg_at_k(b, k):
            wins += 1
    n = len(reranked_grades)
    return wins / n if n else 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-queries", type=int, default=50)
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--k-rachel", type=int, default=50)
    parser.add_argument("--k-lineup", type=int, default=5)
    parser.add_argument("--out", default=str(ER_TRIAGE / "outputs" / "eval_police_lineup.json"))
    args = parser.parse_args()

    print("Loading retrieval index...")
    idx = _ensure_index()

    print(f"Building golden query set (n={args.n_queries})...")
    rnd = random.Random(args.seed)
    chosen = rnd.sample(range(idx.N), k=min(args.n_queries, idx.N))

    baseline_ndcg, reranked_ndcg = [], []
    baseline_mrr,  reranked_mrr  = [], []
    baseline_grades_all, reranked_grades_all = [], []
    top1_severe_baseline = 0
    top1_severe_reranked = 0
    per_query = []

    for i in chosen:
        doc = idx.docs[i]
        raw = doc["raw"]
        try:
            age = int(float(raw["Age"]))
        except (ValueError, KeyError):
            continue
        query = f"{age}yo {raw['Gender']} {raw['Medical Condition']}"

        baseline_hits = search(query, k=args.k_lineup)
        recall_hits = search(query, k=args.k_rachel)
        reranked_hits = rerank(query, recall_hits, top_k=args.k_lineup)

        baseline_grades = [_relevance_for_hit(h) for h in baseline_hits]
        reranked_grades = [_relevance_for_hit(h) for h in reranked_hits]
        baseline_grades_all.append(baseline_grades)
        reranked_grades_all.append(reranked_grades)

        b_ndcg = ndcg_at_k(baseline_grades, args.k_lineup)
        r_ndcg = ndcg_at_k(reranked_grades, args.k_lineup)
        baseline_ndcg.append(b_ndcg)
        reranked_ndcg.append(r_ndcg)
        baseline_mrr.append(mrr(baseline_grades))
        reranked_mrr.append(mrr(reranked_grades))

        if baseline_grades and baseline_grades[0] == 2: top1_severe_baseline += 1
        if reranked_grades and reranked_grades[0] == 2: top1_severe_reranked += 1

        per_query.append({
            "query": query,
            "baseline_ndcg":  round(b_ndcg, 4),
            "reranked_ndcg":  round(r_ndcg, 4),
            "baseline_top1":  baseline_hits[0]["case_id"] if baseline_hits else None,
            "reranked_top1":  reranked_hits[0]["case_id"] if reranked_hits else None,
            "reranked_top1_explanation": reranked_hits[0]["rank_explanation"] if reranked_hits else None,
        })

    n = len(per_query)
    win = win_rate_vs_baseline(reranked_grades_all, baseline_grades_all, args.k_lineup)

    metrics = {
        "n_queries":             n,
        "k_lineup":              args.k_lineup,
        "baseline_ndcg_mean":    round(sum(baseline_ndcg) / n, 4) if n else 0.0,
        "reranked_ndcg_mean":    round(sum(reranked_ndcg) / n, 4) if n else 0.0,
        "ndcg_lift":             round((sum(reranked_ndcg) - sum(baseline_ndcg)) / n, 4) if n else 0.0,
        "baseline_mrr_mean":     round(sum(baseline_mrr) / n, 4) if n else 0.0,
        "reranked_mrr_mean":     round(sum(reranked_mrr) / n, 4) if n else 0.0,
        "win_rate_vs_baseline":  round(win, 4),
        "top1_severe_baseline":  round(top1_severe_baseline / n, 4) if n else 0.0,
        "top1_severe_reranked":  round(top1_severe_reranked / n, 4) if n else 0.0,
        "reranker": "outcome-severity (Emergency 0.4 + Abnormal 0.3 + LongLOS 0.2 + AgeMatch 0.1) blended 60/40 with BM25",
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"metrics": metrics, "per_query": per_query[:25]}, indent=2))

    print("=" * 60)
    print("POLICE LINEUP (Pattern 7 — rank) eval")
    print("=" * 60)
    print(f"  n queries:                 {metrics['n_queries']}")
    print(f"  NDCG@{args.k_lineup} baseline (Rachel only): {metrics['baseline_ndcg_mean']:.4f}")
    print(f"  NDCG@{args.k_lineup} reranked (Lineup):     {metrics['reranked_ndcg_mean']:.4f}")
    print(f"  NDCG lift (abs):                            {metrics['ndcg_lift']:+.4f}")
    print(f"  MRR baseline / reranked:    {metrics['baseline_mrr_mean']:.4f} / {metrics['reranked_mrr_mean']:.4f}")
    print(f"  Win rate (reranker > BM25): {metrics['win_rate_vs_baseline']:.2%}")
    print(f"  Top-1 severe (Emergency+Abnormal):")
    print(f"      baseline: {metrics['top1_severe_baseline']:.2%}")
    print(f"      reranked: {metrics['top1_severe_reranked']:.2%}")
    print(f"\n→ artifact: {out_path}")


if __name__ == "__main__":
    main()
