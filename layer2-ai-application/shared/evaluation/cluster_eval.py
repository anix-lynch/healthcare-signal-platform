"""Pattern 6 (Treasure Map) eval — clustering metrics.

🎯 ACCURACY + 🌟 OUTCOME (cohort-driven ops dashboards) pillar evidence.
"""


def silhouette_score(embeddings, cluster_labels) -> float:
    """Standard silhouette: how separated and tight the clusters are.
    Range -1 to 1. > 0.4 = well-formed."""
    raise NotImplementedError("TODO")


def bertopic_coherence(topics: list[list[str]], corpus: list[str]) -> float:
    """Topic coherence (NPMI or c_v) — do the words within a topic
    co-occur meaningfully in real text?"""
    raise NotImplementedError("TODO")
