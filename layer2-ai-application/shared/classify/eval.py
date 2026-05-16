"""
Pattern 2 — Traffic Light · Eval harness.

Metrics:
    Per-class F1, precision, recall    — bucket-level health
    Confusion matrix                    — where we misroute
    Down-triage rate                    — KEY safety metric: pred < truth
    Up-triage rate                      — efficiency metric: pred > truth
    Calibration                          — when confidence=0.9, accuracy ≈ 0.9?

Why per-class matters more than overall accuracy:
    A classifier that's 92% accurate globally but down-triages 30% of ESI 1
    to ESI 3 is a model that kills people. Overall accuracy hides it.

Down-triage is asymmetric harm. Always report it separately.
"""
from __future__ import annotations
import math
from collections import defaultdict
from typing import Iterable


# ── Per-class metrics ──────────────────────────────────────────────────────
def per_class_metrics(y_true: list[int], y_pred: list[int]) -> dict[int, dict[str, float]]:
    """Compute precision, recall, F1, support per ESI class (1-5)."""
    classes = sorted(set(y_true) | set(y_pred))
    out: dict[int, dict[str, float]] = {}
    for c in classes:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == c and p == c)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != c and p == c)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == c and p != c)
        support = sum(1 for t in y_true if t == c)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        out[c] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": support,
        }
    return out


def confusion_matrix(y_true: list[int], y_pred: list[int]) -> dict[tuple[int, int], int]:
    """Return dict of (truth, pred) → count."""
    cm: dict[tuple[int, int], int] = defaultdict(int)
    for t, p in zip(y_true, y_pred):
        cm[(t, p)] += 1
    return dict(cm)


# ── Safety metrics ────────────────────────────────────────────────────────
def down_triage_rate(y_true: list[int], y_pred: list[int]) -> float:
    """
    Fraction of cases predicted at HIGHER ESI number (= less urgent) than truth.
    HIGHER ESI NUMBER = LESS URGENT. So pred > truth = patient under-triaged.
    This is the kill-people metric.
    """
    if not y_true: return float("nan")
    return sum(1 for t, p in zip(y_true, y_pred) if p > t) / len(y_true)


def up_triage_rate(y_true: list[int], y_pred: list[int]) -> float:
    """Fraction predicted at LOWER ESI number = more urgent than truth. Eats resources."""
    if not y_true: return float("nan")
    return sum(1 for t, p in zip(y_true, y_pred) if p < t) / len(y_true)


def exact_match_rate(y_true: list[int], y_pred: list[int]) -> float:
    if not y_true: return float("nan")
    return sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)


def within_one_rate(y_true: list[int], y_pred: list[int]) -> float:
    """Fraction within ±1 ESI tier. Useful for borderline ESI 3 ↔ ESI 4 fuzziness."""
    if not y_true: return float("nan")
    return sum(1 for t, p in zip(y_true, y_pred) if abs(t - p) <= 1) / len(y_true)


# ── Calibration ────────────────────────────────────────────────────────────
def calibration_buckets(
    y_true: list[int], y_pred: list[int], y_conf: list[float],
    *, bins: int = 10,
) -> list[dict]:
    """
    Bucket predictions by stated confidence, report empirical accuracy per bucket.
    If model is calibrated: bucket centred at 0.8 should have ~80% accuracy.
    """
    if not y_conf: return []
    buckets: list[dict] = []
    for i in range(bins):
        lo, hi = i / bins, (i + 1) / bins
        bucket_idx = [j for j, c in enumerate(y_conf) if lo <= c < hi or (hi == 1 and c == 1)]
        if not bucket_idx: continue
        correct = sum(1 for j in bucket_idx if y_true[j] == y_pred[j])
        buckets.append({
            "conf_range": [round(lo, 2), round(hi, 2)],
            "n": len(bucket_idx),
            "accuracy": round(correct / len(bucket_idx), 4),
            "mean_conf": round(sum(y_conf[j] for j in bucket_idx) / len(bucket_idx), 4),
        })
    return buckets


# ── Aggregate report ──────────────────────────────────────────────────────
def report(
    y_true: list[int],
    y_pred: list[int],
    *,
    y_conf: list[float] | None = None,
) -> dict:
    """Single-call summary. Pretty-printable, JSON-dumpable."""
    n = len(y_true)
    if n == 0: return {"error": "no rows to evaluate"}

    out = {
        "n": n,
        "exact_match": round(exact_match_rate(y_true, y_pred), 4),
        "within_one_tier": round(within_one_rate(y_true, y_pred), 4),
        "down_triage_rate": round(down_triage_rate(y_true, y_pred), 4),
        "up_triage_rate": round(up_triage_rate(y_true, y_pred), 4),
        "per_class": per_class_metrics(y_true, y_pred),
        "confusion_matrix": {f"{t}->{p}": c for (t, p), c in confusion_matrix(y_true, y_pred).items()},
        "safety_note": "down_triage_rate is the kill-people metric — alert if > 0.05",
    }
    if y_conf is not None and len(y_conf) == n:
        out["calibration"] = calibration_buckets(y_true, y_pred, y_conf)
        out["calibration_note"] = "well-calibrated buckets: bucket_conf ≈ bucket_accuracy"
    return out
