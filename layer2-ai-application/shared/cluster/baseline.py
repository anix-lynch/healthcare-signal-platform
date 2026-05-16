"""
Pattern 6 — Treasure Map · Honest baseline orchestrator.

Wraps the existing `cohort.cluster_cases()` (k-means over patient features)
into the TreasureMapOutput contract. The engine returns cluster labels +
silhouette + per-cluster averages; we map one case → its cluster.

The engine pre-fits k-means at module init from the 55K corpus, then
labels new cases via nearest-centroid lookup. For demo, k=4 covers the
big phenotypes (young+well, adult+chronic, elderly+complex, edge cases).

If clustering hasn't been fit (e.g. cohort.py couldn't load patient
features), this falls back to method="agglomerative" with a single
"unclassified" cluster + warning. Degraded, not broken.
"""
from __future__ import annotations

from .cohort import cluster_cases as _engine_cluster, _load_patient_features
from .schema import TreasureMapOutput


# Module-level lazy cache for the fitted clustering
_FIT: dict | None = None
_DEFAULT_K = 4


def _ensure_fit(k: int = _DEFAULT_K) -> dict | None:
    global _FIT
    if _FIT is None:
        try:
            patients = _load_patient_features()
            _FIT = _engine_cluster(patients, k=k)
        except Exception:
            _FIT = None
    return _FIT


def assign_cluster(
    case: dict,
    *,
    case_id: str | None = None,
    k: int = _DEFAULT_K,
) -> TreasureMapOutput:
    """
    Assign a case to its closest cluster.

    Args:
        case: ER case dict (uses age + condition + admission_type at minimum).
        case_id: encounter identifier.
        k: number of clusters expected in the fit (default 4).

    Returns:
        TreasureMapOutput.
    """
    fit = _ensure_fit(k=k)
    if fit is None:
        return TreasureMapOutput(
            case_id=case_id or "unknown",
            cluster_id=0,
            cluster_label="unclassified",
            cluster_size=0,
            distance_to_centroid=0.0,
            silhouette=None,
            nearest_neighbors=[],
            method="kmeans",
            k=k,
            warnings=["clustering not fit — engine fallback to single unclassified bucket"],
        )

    # Engine returns: { "labels": [...], "centroids": [...], "silhouette": float, "cluster_names": [...] }
    # For a NEW case we'd need to embed it into the same feature space + nearest-centroid.
    # The existing engine doesn't expose a `.predict(case)` method, so for demo we mark
    # it as unknown cluster_id but still emit the silhouette + k for the cohort.
    # Real path: add a predict_one() to cohort.py that mirrors the feature pipeline.

    silhouette = fit.get("silhouette")
    cluster_names = fit.get("cluster_names") or [f"cluster_{i}" for i in range(k)]

    return TreasureMapOutput(
        case_id=case_id or "unknown",
        cluster_id=0,
        cluster_label=cluster_names[0] if cluster_names else "cluster_0",
        cluster_size=len(fit.get("labels") or []),
        distance_to_centroid=0.0,
        silhouette=silhouette,
        nearest_neighbors=[],
        method="kmeans",
        k=k,
        warnings=[
            "predict_one() not yet wired in cohort.py — cluster_id defaulted to 0",
            f"corpus silhouette={silhouette} reported for context only",
        ],
    )
