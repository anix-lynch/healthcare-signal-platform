"""
PHASE 3 · Centroid-shift drift monitor.

Compute monthly centroid of incoming case embeddings.
Alert when cosine(c_baseline, c_current) drops below threshold (default 0.92).

Workflow:
  1. baseline: centroid of last N embeddings (rolling window)
  2. current:  centroid of incoming cases this period
  3. cosine_similarity(baseline, current) < 0.92 → ALERT
  4. log to outputs/drift/<date>.json
"""

from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path

DRIFT_THRESHOLD = 0.92


def _load_embeddings(path: str) -> list[list[float]]:
    """Load embeddings from a JSON file: [[float, ...], ...]."""
    return json.loads(Path(path).read_text())


def _centroid(embeddings: list[list[float]]) -> list[float]:
    """Compute the mean vector across all embeddings."""
    n = len(embeddings)
    if n == 0:
        return []
    dim = len(embeddings[0])
    c = [0.0] * dim
    for emb in embeddings:
        for i, v in enumerate(emb):
            c[i] += v / n
    return c


def _cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two equal-length vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def compute_drift(baseline_path: str, current_embeddings_path: str) -> dict:
    """Compute centroid-shift drift score between baseline and current embeddings.

    Returns dict with score, alert flag, and counts.
    Writes result to apps/er-triage/outputs/drift/<today>.json.
    """
    baseline_embs = _load_embeddings(baseline_path)
    current_embs = _load_embeddings(current_embeddings_path)

    if not baseline_embs or not current_embs:
        return {"score": 0.0, "alert": True, "status": "NO_DATA", "error": "empty embeddings"}

    baseline_centroid = _centroid(baseline_embs)
    current_centroid = _centroid(current_embs)

    score = _cosine(baseline_centroid, current_centroid)
    alert = score < DRIFT_THRESHOLD

    result = {
        "score": round(score, 4),
        "threshold": DRIFT_THRESHOLD,
        "alert": alert,
        "baseline_n": len(baseline_embs),
        "current_n": len(current_embs),
        "status": "DRIFT_DETECTED" if alert else "STABLE",
    }

    out_dir = Path("apps/er-triage/outputs/drift")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{date.today().isoformat()}.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"[DRIFT] score={score:.4f} alert={alert} → {out_path}")

    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python -m shared.anomaly.drift <baseline.json> <current.json>")
        sys.exit(1)
    print(compute_drift(sys.argv[1], sys.argv[2]))
