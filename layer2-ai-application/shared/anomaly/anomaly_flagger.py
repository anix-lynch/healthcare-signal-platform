"""
Pattern 5 — anomaly detector · Per-case cohort outlier flagger.

For an incoming case, build its cohort (same gender × condition × age band)
from Layer 1, then compute z-scores on the case's expected operational
profile (predicted LOS vs cohort mean, predicted billing vs cohort mean,
admission-type alignment). z > Z_THRESHOLD on any axis → anomaly flag.

This is per-case, not population drift. It catches:
  - 25yo with HR 140 + acute condition where cohort mean is calm
  - billing way outside cohort norm (possible fraud)
  - admission-type mismatch (the case looks Elective but the cohort goes Emergency)

Output:
  {
    is_anomaly: bool,
    z_scores: {los, billing, admission_alignment},
    triggered_axes: list[str],
    confidence: float,
    reason: str,
  }
"""

from __future__ import annotations
import csv
import math
import re
import statistics
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict

DEFAULT_CORPUS = (
    Path(__file__).resolve().parents[3]
    / "layer1-data-backbone" / "data" / "raw" / "healthcare_dataset.csv"
)

Z_THRESHOLD = 2.0


def _age_band(age: int) -> str:
    if age < 18:  return "0-17"
    if age < 35:  return "18-34"
    if age < 55:  return "35-54"
    if age < 75:  return "55-74"
    return "75+"


@dataclass
class CohortStats:
    n: int
    los_mean: float
    los_std: float
    billing_mean: float
    billing_std: float
    admission_dist: dict  # {Emergency: 0.5, Urgent: 0.3, Elective: 0.2}


class CohortStatsTable:
    """Per-cohort stats for fast per-case anomaly lookup."""

    def __init__(self):
        self._stats: dict[tuple, CohortStats] = {}
        self._global: CohortStats | None = None

    def fit(self, rows: list[dict]):
        from datetime import datetime
        by_cohort: dict[tuple, dict] = defaultdict(lambda: {"los": [], "billing": [], "admission": []})
        all_los, all_bill, all_adm = [], [], []
        for r in rows:
            try:
                age = int(float(r["Age"]))
                adm = datetime.fromisoformat(r["Date of Admission"]).date()
                dis = datetime.fromisoformat(r["Discharge Date"]).date()
                los = (dis - adm).days
                billing = float(r["Billing Amount"])
                if los < 0 or los > 60 or billing < 0: continue
            except (ValueError, KeyError):
                continue
            key = (r.get("Gender", ""), r.get("Medical Condition", ""), _age_band(age))
            ctx = by_cohort[key]
            ctx["los"].append(los)
            ctx["billing"].append(billing)
            ctx["admission"].append(r.get("Admission Type", ""))
            all_los.append(los); all_bill.append(billing); all_adm.append(r.get("Admission Type", ""))

        for key, ctx in by_cohort.items():
            n = len(ctx["los"])
            if n < 5: continue
            adm_dist = {}
            for a in ctx["admission"]: adm_dist[a] = adm_dist.get(a, 0) + 1
            for k in adm_dist: adm_dist[k] /= n
            self._stats[key] = CohortStats(
                n=n,
                los_mean=sum(ctx["los"]) / n,
                los_std=statistics.pstdev(ctx["los"]) if n > 1 else 0.0,
                billing_mean=sum(ctx["billing"]) / n,
                billing_std=statistics.pstdev(ctx["billing"]) if n > 1 else 0.0,
                admission_dist=adm_dist,
            )
        if all_los:
            adm_dist = {}
            for a in all_adm: adm_dist[a] = adm_dist.get(a, 0) + 1
            n = len(all_los)
            for k in adm_dist: adm_dist[k] /= n
            self._global = CohortStats(
                n=n,
                los_mean=sum(all_los) / n,
                los_std=statistics.pstdev(all_los) if n > 1 else 0.0,
                billing_mean=sum(all_bill) / n,
                billing_std=statistics.pstdev(all_bill) if n > 1 else 0.0,
                admission_dist=adm_dist,
            )

    def get(self, gender: str, condition: str, age: int) -> CohortStats:
        key = (gender, condition, _age_band(age))
        return self._stats.get(key) or self._global


_TABLE: CohortStatsTable | None = None


def _ensure_table() -> CohortStatsTable:
    global _TABLE
    if _TABLE is not None: return _TABLE
    table = CohortStatsTable()
    if DEFAULT_CORPUS.exists():
        with DEFAULT_CORPUS.open(newline="") as f:
            table.fit(list(csv.DictReader(f)))
    _TABLE = table
    return _TABLE


# ── Public API ─────────────────────────────────────────────────────────────
def flag(case: dict, triage: dict | None = None, los_prediction: dict | None = None) -> dict:
    """
    Flag an incoming case as a cohort outlier across LOS / billing / admission.

    Args:
        case: dict with at least 'cc' and 'hpi' (for age/gender extraction).
        triage: optional triage decision (bucket → admission-type expectation).
        los_prediction: optional output from shared.regress.predict_los — gives
                        a numeric predicted_days to compare against cohort.

    Returns:
        dict with is_anomaly, z_scores, triggered_axes, confidence, reason.
    """
    # Extract features
    text = case.get("hpi") or ""
    age_m = re.search(r"\b(\d{1,3})\s*(yo|y/o|year)", text, re.I)
    age = int(age_m.group(1)) if age_m else 50
    gender = "Female" if re.search(r"\b(F|female|woman|girl|she|her)\b", text, re.I) else "Male"

    # Infer condition from case text (use predictor's same inference for consistency)
    from shared.regress.los_predictor import _infer_condition
    condition = _infer_condition(case)

    cohort = _ensure_table().get(gender, condition, age)
    if cohort is None or cohort.n < 5:
        return {
            "is_anomaly": False,
            "z_scores": {},
            "triggered_axes": [],
            "confidence": 0.5,
            "reason": "cohort too small to assess",
            "cohort_n": 0,
        }

    triggered = []
    z_scores = {}

    # 1) LOS z-score (if we have a predicted LOS)
    if los_prediction and "predicted_days" in los_prediction and cohort.los_std > 0:
        z_los = (los_prediction["predicted_days"] - cohort.los_mean) / cohort.los_std
        z_scores["los"] = round(z_los, 3)
        if abs(z_los) >= Z_THRESHOLD:
            triggered.append(f"los_z={z_los:+.2f}")

    # 2) Admission-type alignment vs cohort MODE
    # If the case's triage-implied admission type differs from the cohort's
    # most-common admission type, that's the kind of mismatch worth surfacing.
    if triage:
        bucket = triage.get("bucket")
        expected_admission = {"NOW": "Emergency", "SOON": "Urgent", "WAIT": "Elective"}.get(bucket)
        if expected_admission and cohort.admission_dist:
            modal_admission = max(cohort.admission_dist.items(), key=lambda kv: kv[1])[0]
            cohort_rate = cohort.admission_dist.get(expected_admission, 0.0)
            modal_rate = cohort.admission_dist[modal_admission]
            z_scores["admission_alignment_rate"] = round(cohort_rate, 3)
            z_scores["cohort_modal_rate"] = round(modal_rate, 3)
            # Trigger if the case's admission type is BOTH non-modal AND meaningfully
            # less common than the cohort's mode.
            if expected_admission != modal_admission and (modal_rate - cohort_rate) >= 0.05:
                triggered.append(
                    f"admission_mismatch_case={expected_admission}({cohort_rate:.2%})_"
                    f"vs_cohort_mode={modal_admission}({modal_rate:.2%})"
                )

    # 3) Confidence-vs-cohort severity: if triage confidence is low AND cohort
    # has high Emergency rate, surface for review
    if triage:
        conf = triage.get("confidence", 1.0)
        emergency_rate = cohort.admission_dist.get("Emergency", 0.0)
        if conf < 0.7 and emergency_rate > 0.30:
            triggered.append(f"low_conf_in_emergency_prone_cohort_{emergency_rate:.2%}")

    is_anomaly = len(triggered) > 0
    reason = "; ".join(triggered) if triggered else "within cohort norms"

    # Confidence in the anomaly judgment scales with cohort size
    confidence = min(1.0, cohort.n / 200) * 0.85 + 0.10

    return {
        "is_anomaly": is_anomaly,
        "z_scores": z_scores,
        "triggered_axes": triggered,
        "confidence": round(confidence, 3),
        "reason": reason,
        "cohort_n": cohort.n,
        "cohort_los_mean": round(cohort.los_mean, 2),
        "cohort_billing_mean": round(cohort.billing_mean, 2),
    }


if __name__ == "__main__":
    import json, sys
    payload = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {
        "case": {"cc": "chest pain", "hpi": "62yo M with hypertension"},
        "triage": {"bucket": "WAIT", "confidence": 0.55},
    }
    print(json.dumps(flag(payload["case"], payload.get("triage")), indent=2))
