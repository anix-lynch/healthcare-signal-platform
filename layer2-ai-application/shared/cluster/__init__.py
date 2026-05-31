"""Pattern 6 — cohort clustering public API."""
from .baseline import assign_cluster
from .schema import TreasureMapOutput, ClusterMethod
from .cohort import cluster_cases, silhouette_score

__all__ = [
    "assign_cluster",
    "TreasureMapOutput",
    "ClusterMethod",
    "cluster_cases",
    "silhouette_score",
]
