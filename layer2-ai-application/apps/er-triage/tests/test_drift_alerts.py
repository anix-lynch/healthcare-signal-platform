"""
DRIFT ALERT REGRESSION TEST.

Synthetic drift: take baseline embeddings, perturb 30% with noise.
Monitor MUST fire an alert. Inverse: identical embeddings -> MUST NOT alert.
"""

import json
import random
import pytest
from shared.anomaly.drift import compute_drift, DRIFT_THRESHOLD


def _make_embeddings(n: int, dim: int = 32, seed: int = 42) -> list:
    rng = random.Random(seed)
    return [[rng.gauss(0, 1) for _ in range(dim)] for _ in range(n)]


def _perturb(embs: list, noise: float = 5.0, seed: int = 99) -> list:
    rng = random.Random(seed)
    return [[v + rng.gauss(0, noise) for v in row] for row in embs]


def test_synthetic_drift_alerts(tmp_path):
    baseline = _make_embeddings(50, dim=32, seed=1)
    current = _perturb(baseline, noise=5.0, seed=2)
    b_file = tmp_path / "baseline.json"
    c_file = tmp_path / "current.json"
    b_file.write_text(json.dumps(baseline))
    c_file.write_text(json.dumps(current))
    result = compute_drift(str(b_file), str(c_file))
    assert result["alert"] is True, f"expected alert=True, got score={result['score']}"
    assert result["score"] < DRIFT_THRESHOLD
    assert result["status"] == "DRIFT_DETECTED"


def test_no_drift_no_alert(tmp_path):
    baseline = _make_embeddings(50, dim=32, seed=7)
    b_file = tmp_path / "baseline.json"
    c_file = tmp_path / "current.json"
    b_file.write_text(json.dumps(baseline))
    c_file.write_text(json.dumps(baseline))
    result = compute_drift(str(b_file), str(c_file))
    assert result["alert"] is False, f"expected alert=False, got score={result['score']}"
    assert result["score"] >= DRIFT_THRESHOLD
    assert result["status"] == "STABLE"
