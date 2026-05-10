"""
PHASE 3 · Centroid-shift drift monitor.

Compute monthly centroid of incoming case embeddings.
Alert when cosine(c_baseline, c_current) drops below threshold (default 0.92).

See mj/docs/05_smoke_detector.md for the pattern.

Workflow:
  1. baseline: monthly centroid of last 30 days of embeddings
  2. current:  centroid of incoming cases this week
  3. cosine_similarity(baseline, current) < 0.92 → ALERT
  4. log to outputs/drift/<date>.json
  5. notify (Discord / Slack / email) on alert

TODO:
  - load embeddings from ER2's vector store
  - implement rolling-window centroid math
  - implement alert sink (start with stdout, upgrade to Discord)
"""

from __future__ import annotations


def compute_drift(baseline_path: str, current_embeddings_path: str) -> dict:
    """Compute drift score. Return {score, alert: bool, details}."""
    raise NotImplementedError(
        "Implement per docs/02_phase3_drift.md."
    )


if __name__ == "__main__":
    compute_drift("", "")
