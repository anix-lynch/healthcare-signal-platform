"""Pattern 5 (Smoke Detector) eval — anomaly metrics.

🛡️ COMPLIANCE pillar evidence (drift = regulator-loved metric).
"""


def precision_recall_on_synthetic_outliers(
    flagged_ids: set[str],
    true_outlier_ids: set[str],
) -> tuple[float, float]:
    """Inject known synthetic outliers into stream, measure detection.
    Returns (precision, recall) — both should be > 0.8 to ship."""
    raise NotImplementedError("TODO")


def centroid_drift_score(current_embeddings, reference_embeddings) -> float:
    """Distance between centroids of current vs reference batch.
    Threshold-based alert: shift > 1σ → page on-call."""
    raise NotImplementedError("TODO")
