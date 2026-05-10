"""Pattern 6 — Treasure Map (Clustering) | seven-lens

ER context: "Sort all incoming cases into 3-5 cohorts: respiratory ·
cardiac · trauma · GI · neuro." Useful for ops dashboards and resource
forecasting.
GenAI lens: embeddings → k-means (or HDBSCAN) → BERTopic for
auto-labels → LLM narrative summary per cluster.

Eval metrics live in app/evaluation/cluster_eval.py:
    silhouette · BERTopic coherence
"""


def cluster_cases(cases: list[dict], k: int | None = None) -> list[dict]:
    """Cluster cases into cohorts by clinical similarity.

    Returns list of {case_id, cluster_id, cluster_label, distance_to_center}.
    If k is None, use HDBSCAN to auto-discover cluster count.
    """
    raise NotImplementedError("TODO: embed → k-means/HDBSCAN → BERTopic auto-label")


def summarize_cluster(cluster_id: int, member_cases: list[dict]) -> str:
    """LLM-narrative summary of what makes this cluster cohesive."""
    raise NotImplementedError("TODO: LLM prompt over top-N representative cases")
