"""
Pattern 6 — cohort clustering · Patient high-utilizer clustering.

Groups Layer 1's 55,500 encounters by patient (Name → patient proxy), computes
per-patient operational features, then runs k-means to surface utilization
cohorts useful for care-management programs:

    Features per patient:
        - visit_count           (number of ER encounters)
        - avg_los_days          (average length of stay)
        - total_billing         (cumulative cost)
        - condition_diversity   (count of distinct Medical Conditions)
        - emergency_rate        (share of visits that were Emergency)

    Clusters surfaced (typical interpretations):
        - "low-acuity occasional"          — 1 visit, short LOS, single condition
        - "chronic-disease frequent flyer" — multi-visit, multi-condition, varied admission
        - "high-cost single-event"         — 1 visit, long LOS, large billing
        - "complex high-utilizer"          — multi-visit, long LOS, high cost

Implementation: pure-Python k-means (no sklearn). Z-score standardization
+ 25 iterations max. Deterministic via seeded centroid init.

Output is one-shot: cluster assignments + JSON cohort summary card per
cluster. Not a runtime hot path — call once, write to outputs/.
"""

from __future__ import annotations
import csv
import json
import random
import statistics
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict
from datetime import datetime

DEFAULT_CORPUS = (
    Path(__file__).resolve().parents[3]
    / "layer1-data-backbone" / "data" / "raw" / "healthcare_dataset.csv"
)


@dataclass
class PatientFeatures:
    name: str
    visit_count: int
    avg_los_days: float
    total_billing: float
    condition_diversity: int
    emergency_rate: float
    avg_age: float


def _load_patient_features() -> list[PatientFeatures]:
    if not DEFAULT_CORPUS.exists():
        raise FileNotFoundError(f"Layer 1 corpus not found at {DEFAULT_CORPUS}")
    by_name: dict[str, dict] = defaultdict(lambda: {
        "los": [], "billing": [], "conditions": set(), "emergency": 0, "ages": [],
    })
    with DEFAULT_CORPUS.open(newline="") as f:
        for r in csv.DictReader(f):
            name = (r.get("Name") or "").strip().lower()
            if not name: continue
            try:
                age = int(float(r["Age"]))
                adm = datetime.fromisoformat(r["Date of Admission"]).date()
                dis = datetime.fromisoformat(r["Discharge Date"]).date()
                los = (dis - adm).days
                billing = float(r["Billing Amount"])
                if los < 0 or los > 60 or billing < 0: continue
            except (ValueError, KeyError):
                continue
            ctx = by_name[name]
            ctx["los"].append(los)
            ctx["billing"].append(billing)
            ctx["conditions"].add(r.get("Medical Condition", ""))
            ctx["ages"].append(age)
            if r.get("Admission Type") == "Emergency":
                ctx["emergency"] += 1

    patients: list[PatientFeatures] = []
    for name, ctx in by_name.items():
        n = len(ctx["los"])
        if n == 0: continue
        patients.append(PatientFeatures(
            name=name,
            visit_count=n,
            avg_los_days=sum(ctx["los"]) / n,
            total_billing=sum(ctx["billing"]),
            condition_diversity=len(ctx["conditions"]),
            emergency_rate=ctx["emergency"] / n,
            avg_age=sum(ctx["ages"]) / n,
        ))
    return patients


# ── Standardization + k-means ───────────────────────────────────────────────
def _standardize(matrix: list[list[float]]) -> tuple[list[list[float]], list[float], list[float]]:
    """Z-score each column. Returns (standardized, means, stds)."""
    if not matrix: return ([], [], [])
    n_cols = len(matrix[0])
    means = [sum(row[j] for row in matrix) / len(matrix) for j in range(n_cols)]
    stds = []
    for j in range(n_cols):
        vals = [row[j] for row in matrix]
        s = statistics.pstdev(vals) if len(vals) > 1 else 1.0
        stds.append(s if s > 0 else 1.0)
    out = [[(row[j] - means[j]) / stds[j] for j in range(n_cols)] for row in matrix]
    return out, means, stds


def _euclidean(a: list[float], b: list[float]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def kmeans(matrix: list[list[float]], k: int, max_iter: int = 25, seed: int = 7
           ) -> tuple[list[int], list[list[float]]]:
    """Returns (labels, centroids). Pure Python. Deterministic via seed."""
    if not matrix or k <= 0: return [], []
    rnd = random.Random(seed)
    centroids = [list(row) for row in rnd.sample(matrix, k=min(k, len(matrix)))]
    labels = [0] * len(matrix)
    for _ in range(max_iter):
        new_labels = []
        for row in matrix:
            dists = [_euclidean(row, c) for c in centroids]
            new_labels.append(dists.index(min(dists)))
        if new_labels == labels:
            break
        labels = new_labels
        # Recompute centroids
        new_centroids = []
        for c_idx in range(k):
            members = [matrix[i] for i, l in enumerate(labels) if l == c_idx]
            if not members:
                new_centroids.append(centroids[c_idx])
                continue
            new_centroids.append([sum(m[j] for m in members) / len(members)
                                  for j in range(len(members[0]))])
        centroids = new_centroids
    return labels, centroids


def silhouette_score(matrix: list[list[float]], labels: list[int],
                     sample_size: int = 1000, seed: int = 11) -> float:
    """
    Silhouette on a random sample to keep cost O(sample_size²) instead of O(n²).
    For populations ≥ sample_size this is statistically reliable.
    """
    if not matrix: return 0.0
    n = len(matrix)
    rnd = random.Random(seed)
    if n > sample_size:
        idxs = rnd.sample(range(n), sample_size)
    else:
        idxs = list(range(n))
    sub_matrix = [matrix[i] for i in idxs]
    sub_labels = [labels[i] for i in idxs]

    by_cluster: dict[int, list[int]] = defaultdict(list)
    for i, l in enumerate(sub_labels):
        by_cluster[l].append(i)
    if len(by_cluster) < 2: return 0.0

    scores = []
    for i, row in enumerate(sub_matrix):
        own = by_cluster[sub_labels[i]]
        if len(own) < 2:
            continue
        a = sum(_euclidean(row, sub_matrix[j]) for j in own if j != i) / (len(own) - 1)
        b_candidates = []
        for c_id, members in by_cluster.items():
            if c_id == sub_labels[i]: continue
            b_candidates.append(sum(_euclidean(row, sub_matrix[j]) for j in members) / len(members))
        b = min(b_candidates) if b_candidates else 0.0
        denom = max(a, b)
        if denom > 0:
            scores.append((b - a) / denom)
    return sum(scores) / len(scores) if scores else 0.0


# ── Public API ─────────────────────────────────────────────────────────────
def cluster_cases(patients: list[PatientFeatures] | None = None, k: int = 4) -> dict:
    """
    Cluster patients by utilization profile.

    Returns:
        {
            "assignments": list[{name, cluster_id, ...features}],
            "cluster_summaries": list[{cluster_id, label, size, centroid_*, ...}],
            "silhouette": float,
        }
    """
    if patients is None:
        patients = _load_patient_features()

    feature_keys = ["visit_count", "avg_los_days", "total_billing",
                    "condition_diversity", "emergency_rate"]
    matrix = [[getattr(p, k) for k in feature_keys] for p in patients]
    standardized, means, stds = _standardize(matrix)
    labels, centroids = kmeans(standardized, k=k)

    # Map centroids back to original feature space for human-readable summaries
    raw_centroids = [
        [c[j] * stds[j] + means[j] for j in range(len(feature_keys))]
        for c in centroids
    ]

    summaries = []
    for c_id in range(k):
        members = [p for p, l in zip(patients, labels) if l == c_id]
        if not members:
            continue
        avg = {key: sum(getattr(m, key) for m in members) / len(members) for key in feature_keys}
        # Heuristic label
        label = _name_cluster(avg)
        summaries.append({
            "cluster_id": c_id,
            "label": label,
            "size": len(members),
            "share_of_population": round(len(members) / len(patients), 4),
            **{f"mean_{k}": round(avg[k], 3) for k in feature_keys},
        })
    summaries.sort(key=lambda s: -s["size"])

    sil = silhouette_score(standardized, labels)

    assignments = [
        {"name": p.name, "cluster_id": l, **asdict(p)}
        for p, l in zip(patients, labels)
    ]
    return {
        "k": k,
        "n_patients": len(patients),
        "silhouette": round(sil, 4),
        "cluster_summaries": summaries,
        "assignments": assignments,
    }


def _name_cluster(avg: dict) -> str:
    vc, los, bill, cd, er = (
        avg["visit_count"], avg["avg_los_days"], avg["total_billing"],
        avg["condition_diversity"], avg["emergency_rate"],
    )
    if vc >= 3 and bill >= 60_000:
        return "complex_high_utilizer"
    if vc >= 2 and cd >= 2:
        return "chronic_frequent_flyer"
    if vc == 1 and (los >= 15 or bill >= 40_000):
        return "high_cost_single_event"
    if er >= 0.6:
        return "emergency_dominant"
    return "low_acuity_occasional"


def summarize_cluster(cluster_id: int, member_cases: list[dict]) -> str:
    """Human-readable narrative summary of a single cluster."""
    if not member_cases:
        return f"Cluster {cluster_id}: empty"
    vc = sum(m.get("visit_count", 0) for m in member_cases) / len(member_cases)
    los = sum(m.get("avg_los_days", 0) for m in member_cases) / len(member_cases)
    bill = sum(m.get("total_billing", 0) for m in member_cases) / len(member_cases)
    return (
        f"Cluster {cluster_id}: {len(member_cases)} patients, "
        f"avg {vc:.1f} visits, {los:.1f}d LOS, ${bill:,.0f} total billing"
    )


if __name__ == "__main__":
    import sys
    out = cluster_cases()
    summary = {k: v for k, v in out.items() if k != "assignments"}
    summary["assignments_sample"] = out["assignments"][:5]
    print(json.dumps(summary, indent=2))
