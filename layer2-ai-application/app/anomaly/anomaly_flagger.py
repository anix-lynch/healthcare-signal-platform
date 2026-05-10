"""
PHASE 3 · Per-case outlier flagger.

For each incoming case, compute distance from nearest cluster centroid
(reuse ER2's existing embeddings). Flag if distance > 4σ.

Then run cheap LLM judge on flagged subset for explanation:
  "is_anomaly: bool, reason: str, confidence: float"

See mj/docs/05_smoke_detector.md.
"""

from __future__ import annotations


def flag(case: dict, embedding) -> dict | None:
    """Return anomaly record if case is an outlier, else None."""
    raise NotImplementedError(
        "Implement per docs/02_phase3_drift.md."
    )


if __name__ == "__main__":
    flag({}, None)
