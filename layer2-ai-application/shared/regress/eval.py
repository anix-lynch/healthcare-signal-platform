"""
Pattern 3 — forecast · Eval harness.

Metrics:
    RMSE   — penalises big LOS misses (correctly: ER bed planning hates a 2-day miss far more than two 1-day misses)
    MAE    — robust median-style error, easier to explain to a hospital admin
    MAPE   — % error, useful for "is the model right within X%"
    Bias   — mean signed error (does the model SYSTEMATICALLY over- or under-predict?)
    Calib  — coverage of the cohort_std interval (does std actually behave like std?)

We slice by condition + age_band + admission_type. A model that's good on
average and terrible on "cancer + 75+" is a model that gets people sued.
"""
from __future__ import annotations
import math
import statistics
from collections import defaultdict
from typing import Iterable


# ── Core metrics ───────────────────────────────────────────────────────────
def rmse(y_true: list[float], y_pred: list[float]) -> float:
    if not y_true: return float("nan")
    return math.sqrt(sum((t - p) ** 2 for t, p in zip(y_true, y_pred)) / len(y_true))


def mae(y_true: list[float], y_pred: list[float]) -> float:
    if not y_true: return float("nan")
    return sum(abs(t - p) for t, p in zip(y_true, y_pred)) / len(y_true)


def mape(y_true: list[float], y_pred: list[float], *, epsilon: float = 0.5) -> float:
    """epsilon avoids divide-by-zero on same-day discharges."""
    if not y_true: return float("nan")
    return sum(abs(t - p) / max(abs(t), epsilon) for t, p in zip(y_true, y_pred)) / len(y_true) * 100


def bias(y_true: list[float], y_pred: list[float]) -> float:
    """Mean signed error. Positive = model over-predicts LOS."""
    if not y_true: return float("nan")
    return sum(p - t for t, p in zip(y_true, y_pred)) / len(y_true)


def coverage_at_1std(y_true: list[float], y_pred: list[float], stds: list[float]) -> float:
    """
    Fraction of true LOS that fall within predicted ± 1×cohort_std.
    Well-calibrated → ~0.68. <0.50 → cohort_std is lying to you.
    """
    if not y_true: return float("nan")
    hits = sum(1 for t, p, s in zip(y_true, y_pred, stds) if abs(t - p) <= s)
    return hits / len(y_true)


# ── Segment breakdown ──────────────────────────────────────────────────────
def segmented(
    rows: Iterable[dict],
    *,
    pred_key: str = "predicted_days",
    truth_key: str = "actual_days",
    segment_keys: tuple[str, ...] = ("condition", "age_band", "admission"),
) -> dict[str, dict[str, float]]:
    """
    Group rows by every segment_key in turn, compute MAE/RMSE/n per bucket.

    Returns:
        {segment_key: {bucket_value: {mae, rmse, n}}}
    """
    out: dict[str, dict[str, dict[str, float]]] = {}
    rows = list(rows)
    for key in segment_keys:
        buckets: dict[str, list[tuple[float, float]]] = defaultdict(list)
        for r in rows:
            bucket = str(r.get(key, "unknown"))
            t, p = r.get(truth_key), r.get(pred_key)
            if t is None or p is None: continue
            buckets[bucket].append((float(t), float(p)))
        out[key] = {
            b: {
                "n": len(pairs),
                "mae": round(mae([t for t, _ in pairs], [p for _, p in pairs]), 3),
                "rmse": round(rmse([t for t, _ in pairs], [p for _, p in pairs]), 3),
            }
            for b, pairs in buckets.items()
        }
    return out


# ── Aggregate report ──────────────────────────────────────────────────────
def report(
    y_true: list[float],
    y_pred: list[float],
    *,
    cohort_stds: list[float] | None = None,
) -> dict:
    """Single-call summary. Pretty-printable, JSON-dumpable."""
    n = len(y_true)
    if n == 0:
        return {"error": "no rows to evaluate"}

    block = {
        "n": n,
        "rmse": round(rmse(y_true, y_pred), 3),
        "mae": round(mae(y_true, y_pred), 3),
        "mape_pct": round(mape(y_true, y_pred), 2),
        "bias_days": round(bias(y_true, y_pred), 3),
        "true_mean": round(statistics.mean(y_true), 3),
        "true_std": round(statistics.pstdev(y_true) if n > 1 else 0.0, 3),
    }
    if cohort_stds is not None and len(cohort_stds) == n:
        block["coverage_at_1std"] = round(coverage_at_1std(y_true, y_pred, cohort_stds), 3)
        block["calibration_note"] = (
            "well-calibrated ≈ 0.68; far from there = cohort_std under/over-estimating uncertainty"
        )
    return block
