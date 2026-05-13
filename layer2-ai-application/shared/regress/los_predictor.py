"""
Pattern 3 — Crystal Ball · Length-of-stay predictor.

Predicts LOS in DAYS for an incoming ER case from Layer 1 cohort statistics.

Implementation: cohort-mean lookup with hierarchical fallback. Pure Python,
no API keys, no sklearn required. Trained once at module load from
Layer 1's 55,500-row corpus.

Lookup order (most specific → least):
    1. (condition, gender, age_band, admission_type)
    2. (condition, gender, age_band)
    3. (condition, age_band)
    4. (condition)
    5. global mean

For each cohort we store: mean, std, n. Confidence is a function of n
(larger cohort → more trustworthy).

Bins for downstream triage:
    short   ≤ 2 days
    medium  3-6 days
    long    7+ days
"""

from __future__ import annotations
import csv
import math
import re
import statistics
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict
from datetime import date, datetime

DEFAULT_CORPUS = (
    Path(__file__).resolve().parents[3]
    / "layer1-data-backbone" / "data" / "raw" / "healthcare_dataset.csv"
)


def _age_band(age: int) -> str:
    if age < 18:  return "0-17"
    if age < 35:  return "18-34"
    if age < 55:  return "35-54"
    if age < 75:  return "55-74"
    return "75+"


def _bin(days: float) -> str:
    if days <= 2: return "short"
    if days <= 6: return "medium"
    return "long"


# ── In-memory cohort table ─────────────────────────────────────────────────
class CohortLOSModel:
    """Hierarchical cohort-mean predictor for LOS."""

    def __init__(self):
        # 4 hierarchy levels → list of LOS values
        self.l1: dict[tuple, list[float]] = defaultdict(list)  # (cond,gender,band,adm)
        self.l2: dict[tuple, list[float]] = defaultdict(list)  # (cond,gender,band)
        self.l3: dict[tuple, list[float]] = defaultdict(list)  # (cond,band)
        self.l4: dict[str,   list[float]] = defaultdict(list)  # condition
        self.global_los: list[float] = []
        self._frozen = False
        # Aggregate stats after freeze
        self._l1_stats: dict[tuple, tuple[float, float, int]] = {}
        self._l2_stats: dict[tuple, tuple[float, float, int]] = {}
        self._l3_stats: dict[tuple, tuple[float, float, int]] = {}
        self._l4_stats: dict[str,   tuple[float, float, int]] = {}
        self._global_stats: tuple[float, float, int] = (0.0, 0.0, 0)

    def add(self, los_days: float, condition: str, gender: str, age: int, admission: str):
        band = _age_band(age)
        self.l1[(condition, gender, band, admission)].append(los_days)
        self.l2[(condition, gender, band)].append(los_days)
        self.l3[(condition, band)].append(los_days)
        self.l4[condition].append(los_days)
        self.global_los.append(los_days)

    def _stats(self, vals: list[float]) -> tuple[float, float, int]:
        n = len(vals)
        if n == 0: return (0.0, 0.0, 0)
        mean = sum(vals) / n
        std = statistics.pstdev(vals) if n > 1 else 0.0
        return (mean, std, n)

    def freeze(self):
        for k, v in self.l1.items(): self._l1_stats[k] = self._stats(v)
        for k, v in self.l2.items(): self._l2_stats[k] = self._stats(v)
        for k, v in self.l3.items(): self._l3_stats[k] = self._stats(v)
        for k, v in self.l4.items(): self._l4_stats[k] = self._stats(v)
        self._global_stats = self._stats(self.global_los)
        self._frozen = True
        # Clear raw vectors to save memory
        self.l1.clear(); self.l2.clear(); self.l3.clear(); self.l4.clear()
        self.global_los.clear()

    def predict(self, condition: str, gender: str, age: int, admission: str
                ) -> tuple[float, float, int, str]:
        """Return (mean_days, std_days, n, source_level)."""
        if not self._frozen:
            raise RuntimeError("Model not frozen — call freeze() after training")
        band = _age_band(age)
        for stats, key, level in [
            (self._l1_stats, (condition, gender, band, admission), "l1_cond+gender+age+adm"),
            (self._l2_stats, (condition, gender, band),            "l2_cond+gender+age"),
            (self._l3_stats, (condition, band),                    "l3_cond+age"),
        ]:
            entry = stats.get(key)
            if entry and entry[2] >= 5:
                return (*entry, level)
        entry = self._l4_stats.get(condition)
        if entry and entry[2] >= 1:
            return (*entry, "l4_cond")
        return (*self._global_stats, "global")


# ── Output schema ─────────────────────────────────────────────────────────
@dataclass
class LoSPrediction:
    predicted_days: float
    bin: str                # short / medium / long
    confidence: float       # 0-1
    cohort_n: int
    cohort_std: float
    source_level: str
    reasoning: str

    def to_dict(self) -> dict:
        return asdict(self)


# ── Module-level lazy singleton ────────────────────────────────────────────
_MODEL: CohortLOSModel | None = None


def _build_default_model() -> CohortLOSModel:
    if not DEFAULT_CORPUS.exists():
        raise FileNotFoundError(f"Layer 1 corpus not found at {DEFAULT_CORPUS}")
    m = CohortLOSModel()
    with DEFAULT_CORPUS.open(newline="") as f:
        for row in csv.DictReader(f):
            try:
                age = int(float(row.get("Age", 0)))
                adm = datetime.fromisoformat(row["Date of Admission"]).date()
                dis = datetime.fromisoformat(row["Discharge Date"]).date()
                los = (dis - adm).days
                if los < 0 or los > 60:  # filter nonsense rows
                    continue
            except (ValueError, KeyError, TypeError):
                continue
            condition = row.get("Medical Condition", "")
            gender = row.get("Gender", "")
            admission = row.get("Admission Type", "")
            if not (condition and gender and admission):
                continue
            m.add(los, condition, gender, age, admission)
    m.freeze()
    return m


def _ensure_model() -> CohortLOSModel:
    global _MODEL
    if _MODEL is None:
        _MODEL = _build_default_model()
    return _MODEL


# ── Feature extraction from triage case ────────────────────────────────────
_CONDITION_KEYWORDS = {
    "Cancer":       ["cancer", "tumor", "malignan", "metasta", "chemo"],
    "Diabetes":     ["diabet", "dka", "hyperglycem", "hypoglycem", "insulin"],
    "Hypertension": ["hypertens", "htn", "high blood pressure", "chest pain", "cardiac", "stemi"],
    "Asthma":       ["asthma", "wheez", "bronchospasm", "respiratory distress"],
    "Obesity":      ["obesity", "obese", "bariatric"],
    "Arthritis":    ["arthritis", "joint pain", "rheumatoid", "osteo", "ortho"],
}


def _infer_condition(case: dict) -> str:
    text = f"{case.get('cc', '')} {case.get('hpi', '')}".lower()
    for cond, kws in _CONDITION_KEYWORDS.items():
        if any(k in text for k in kws):
            return cond
    return "Hypertension"  # most common fallback in this dataset


def _infer_gender(case: dict) -> str:
    text = (case.get("hpi") or "") + " " + (case.get("cc") or "")
    if re.search(r"\b(F|female|woman|girl|she|her)\b", text, re.I): return "Female"
    return "Male"


def _infer_age(case: dict) -> int:
    text = case.get("hpi", "") or ""
    m = re.search(r"\b(\d{1,3})\s*(yo|y/o|year)", text, re.I)
    if m: return int(m.group(1))
    return 50


def _infer_admission(case: dict, triage: dict | None) -> str:
    if triage:
        bucket = triage.get("bucket")
        if bucket == "NOW":  return "Emergency"
        if bucket == "SOON": return "Urgent"
        if bucket == "WAIT": return "Elective"
    arrival = (case.get("arrival") or "").lower()
    if "ambulance" in arrival: return "Emergency"
    return "Urgent"


# ── Public API ─────────────────────────────────────────────────────────────
def predict_los(case: dict, triage: dict | None = None) -> LoSPrediction:
    """
    Predict length-of-stay in days for an incoming ER case.

    Args:
        case: dict with at least 'cc'; ideally also 'hpi' (for age/gender) and 'arrival'.
        triage: optional triage decision (bucket affects admission-type prior).

    Returns:
        LoSPrediction (JSON-serializable via .to_dict()).
    """
    model = _ensure_model()
    condition = _infer_condition(case)
    gender = _infer_gender(case)
    age = _infer_age(case)
    admission = _infer_admission(case, triage)

    mean_days, std_days, n, source = model.predict(condition, gender, age, admission)

    # Confidence from cohort size (saturating curve)
    confidence = round(min(1.0, n / 200.0) * 0.85 + 0.10, 3)

    reasoning = (
        f"cohort: {condition}/{gender}/{_age_band(age)}/{admission} · "
        f"n={n} · std={std_days:.2f}d · source={source}"
    )

    return LoSPrediction(
        predicted_days=round(mean_days, 2),
        bin=_bin(mean_days),
        confidence=confidence,
        cohort_n=n,
        cohort_std=round(std_days, 2),
        source_level=source,
        reasoning=reasoning,
    )


def predict_los_dict(case: dict, triage: dict | None = None) -> dict:
    return predict_los(case, triage).to_dict()


if __name__ == "__main__":
    import json, sys
    case = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {
        "cc": "chest pain", "hpi": "62yo M, substernal pressure 30 min",
        "arrival": "walk-in",
    }
    print(json.dumps(predict_los_dict(case), indent=2))
