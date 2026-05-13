"""Pattern 6 (Treasure Map) eval — clustering quality.

Runs the patient utilization clustering and reports:
  - silhouette score (cluster cohesion)
  - cluster size distribution + balance
  - cluster label distribution (heuristic-based labels)
  - centroid feature means (operational interpretability check)

Run:
    cd layer2-ai-application
    python -m shared.evaluation.cluster_eval

Output:
    apps/er-triage/outputs/eval_treasure_map.json

🎯 ACCURACY pillar evidence.
"""

from __future__ import annotations
import json
import sys
import argparse
from pathlib import Path
from collections import Counter

HERE = Path(__file__).resolve().parent
LAYER2_ROOT = HERE.parent.parent
ER_TRIAGE = LAYER2_ROOT / "apps" / "er-triage"

from shared.cluster.cohort import cluster_cases, _load_patient_features


def silhouette_score(embeddings, cluster_labels) -> float:
    from shared.cluster.cohort import silhouette_score as _sil
    return _sil(embeddings, cluster_labels)


def bertopic_coherence(topics, corpus) -> float:
    """Stub — no LLM topic labeling in this v1. Heuristic labels are used."""
    return 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=4)
    parser.add_argument("--out", default=str(ER_TRIAGE / "outputs" / "eval_treasure_map.json"))
    args = parser.parse_args()

    print(f"Loading patient features from Layer 1...")
    patients = _load_patient_features()
    print(f"Patient population: {len(patients):,}")

    print(f"Clustering with k={args.k}...")
    out = cluster_cases(patients, k=args.k)

    label_counts = Counter(a["cluster_id"] for a in out["assignments"])
    visit_dist = Counter(p.visit_count for p in patients)

    metrics = {
        "n_patients":             out["n_patients"],
        "k":                      out["k"],
        "silhouette":             out["silhouette"],
        "cluster_size_balance":   round(min(label_counts.values()) / max(label_counts.values()), 4)
                                   if label_counts else 0.0,
        "label_distribution":     {s["label"]: s["size"] for s in out["cluster_summaries"]},
        "visit_count_histogram":  dict(sorted(visit_dist.items())),
        "cluster_summaries":      out["cluster_summaries"],
        "model": "pure-Python k-means on 5 patient-level features, z-score standardized",
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "metrics": metrics,
        "assignments_sample": out["assignments"][:25],
    }, indent=2))

    print("=" * 60)
    print("TREASURE MAP (Pattern 6 — cluster) eval")
    print("=" * 60)
    print(f"  patients:           {metrics['n_patients']:,}")
    print(f"  k:                  {metrics['k']}")
    print(f"  silhouette:         {metrics['silhouette']:.4f}")
    print(f"  size balance:       {metrics['cluster_size_balance']:.4f}")
    print(f"  cluster labels:")
    for label, size in metrics["label_distribution"].items():
        print(f"      {label:30s} {size:>8,}")
    print(f"\n→ artifact: {out_path}")


if __name__ == "__main__":
    main()
