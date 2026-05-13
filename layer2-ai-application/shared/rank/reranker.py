"""
Pattern 7 — Police Lineup · Outcome-severity re-ranker over Rachel.

Rachel (BM25 retrieval) finds DEMOGRAPHICALLY similar past cases.
Police Lineup re-ranks them by CLINICAL severity, surfacing the
"cautionary tales" — past patients who arrived looking like the
current case AND had a bad outcome.

Severity signal (per Layer 1 row):
  + Emergency admission       weight 0.40
  + Abnormal test result      weight 0.30
  + LOS in upper quartile     weight 0.20
  + Age-band tightness        weight 0.10

Final score = BM25_score_normalized * 0.4 + severity_score * 0.6

Why 60% severity > 40% BM25:
  - Rachel already filtered for demographic similarity at recall stage
  - The lineup's job is to surface OUTCOMES that matter, not redundant
    demographic matches

Lineup output is a re-ordered list of the same Rachel hits, plus a
'severity_score' and 'rank_explanation' attached.
"""

from __future__ import annotations
import re
import csv
import statistics
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict
from datetime import datetime

DEFAULT_CORPUS = (
    Path(__file__).resolve().parents[3]
    / "layer1-data-backbone" / "data" / "raw" / "healthcare_dataset.csv"
)


# ── Per-condition LOS Q3 threshold table ───────────────────────────────────
class LosQuartileTable:
    """Precomputed per-condition LOS upper-quartile (Q3) for fast lookup."""

    def __init__(self):
        self._q3: dict[str, float] = {}
        self._global_q3: float = 0.0

    def fit(self, rows: list[dict]):
        by_cond: dict[str, list[float]] = defaultdict(list)
        all_los: list[float] = []
        for r in rows:
            try:
                adm = datetime.fromisoformat(r["Date of Admission"]).date()
                dis = datetime.fromisoformat(r["Discharge Date"]).date()
                los = (dis - adm).days
                if los < 0 or los > 60: continue
            except (ValueError, KeyError):
                continue
            cond = r.get("Medical Condition", "")
            if cond:
                by_cond[cond].append(los)
                all_los.append(los)
        for cond, vals in by_cond.items():
            if len(vals) >= 10:
                self._q3[cond] = statistics.quantiles(vals, n=4)[2]
        if all_los:
            self._global_q3 = statistics.quantiles(all_los, n=4)[2]

    def is_long(self, condition: str, los_days: float) -> bool:
        q3 = self._q3.get(condition, self._global_q3)
        return los_days >= q3


_LOS_Q3: LosQuartileTable | None = None


def _ensure_quartiles():
    global _LOS_Q3
    if _LOS_Q3 is not None: return _LOS_Q3
    if not DEFAULT_CORPUS.exists():
        _LOS_Q3 = LosQuartileTable()
        return _LOS_Q3
    rows = []
    with DEFAULT_CORPUS.open(newline="") as f:
        rows = list(csv.DictReader(f))
    table = LosQuartileTable()
    table.fit(rows)
    _LOS_Q3 = table
    return _LOS_Q3


# ── Severity scoring ───────────────────────────────────────────────────────
@dataclass
class RankedHit:
    case_id: str
    bm25_score: float
    severity_score: float
    final_score: float
    rank_explanation: str
    snippet: str
    raw: dict

    def to_dict(self) -> dict: return asdict(self)


def _age_from_query(query: str) -> int | None:
    m = re.search(r"\b(\d{1,3})\s*(yo|y/o|year)", query, re.I)
    if not m:
        m = re.search(r"^\s*(\d{1,3})\b", query)
    return int(m.group(1)) if m else None


def _score_severity(hit: dict, query_age: int | None, query_condition: str | None) -> tuple[float, list[str]]:
    """Return (severity_0_to_1, explanation_parts)."""
    raw = hit.get("raw") or {}
    parts: list[str] = []
    score = 0.0

    # 1) Emergency admission (weight 0.40)
    admission = raw.get("Admission Type", "")
    if admission == "Emergency":
        score += 0.40
        parts.append("emergency")
    elif admission == "Urgent":
        score += 0.20
        parts.append("urgent")

    # 2) Abnormal test result (weight 0.30)
    test = raw.get("Test Results", "")
    if test == "Abnormal":
        score += 0.30
        parts.append("abnormal_test")
    elif test == "Inconclusive":
        score += 0.15
        parts.append("inconclusive_test")

    # 3) LOS upper quartile (weight 0.20)
    quartiles = _ensure_quartiles()
    try:
        adm = datetime.fromisoformat(raw["Date of Admission"]).date()
        dis = datetime.fromisoformat(raw["Discharge Date"]).date()
        los = (dis - adm).days
        if quartiles.is_long(raw.get("Medical Condition", ""), los):
            score += 0.20
            parts.append(f"long_stay_{los}d")
    except (ValueError, KeyError, TypeError):
        pass

    # 4) Age-band tightness (weight 0.10)
    if query_age is not None:
        try:
            hit_age = int(float(raw.get("Age", 0)))
            if abs(hit_age - query_age) <= 5:
                score += 0.10
                parts.append("age_match")
        except (ValueError, TypeError):
            pass

    return min(score, 1.0), parts


def rerank(query: str, candidates: list[dict], top_k: int = 5,
           bm25_weight: float = 0.4, severity_weight: float = 0.6) -> list[dict]:
    """
    Re-rank Rachel's BM25 candidates by clinical outcome severity.

    Args:
        query: the original retrieval query (used for age/condition extraction).
        candidates: list of hits from shared.retrieval.retriever.search()
                    Each has {case_id, snippet, score, raw}.
        top_k: number to return after re-ranking.

    Returns:
        List of dicts with bm25_score, severity_score, final_score, rank_explanation.
    """
    if not candidates:
        return []

    # Normalize BM25 scores to [0, 1] by max
    max_bm25 = max((c["score"] for c in candidates), default=0.0) or 1.0
    query_age = _age_from_query(query)
    # Query condition: pull first capitalized condition mentioned
    query_condition = None
    for cond in ["Cancer", "Diabetes", "Hypertension", "Asthma", "Obesity", "Arthritis"]:
        if cond.lower() in query.lower():
            query_condition = cond
            break

    scored: list[RankedHit] = []
    for c in candidates:
        sev_score, parts = _score_severity(c, query_age, query_condition)
        bm25_norm = c["score"] / max_bm25
        final = bm25_weight * bm25_norm + severity_weight * sev_score
        explanation = "+".join(parts) if parts else "no_severity_signals"
        scored.append(RankedHit(
            case_id=c["case_id"],
            bm25_score=round(c["score"], 4),
            severity_score=round(sev_score, 4),
            final_score=round(final, 4),
            rank_explanation=explanation,
            snippet=c["snippet"],
            raw=c.get("raw") or {},
        ))

    scored.sort(key=lambda h: h.final_score, reverse=True)
    return [h.to_dict() for h in scored[:top_k]]


def rerank_for_case(case: dict, k_rachel: int = 50, k_lineup: int = 5) -> list[dict]:
    """
    End-to-end: Rachel pulls top-k_rachel similar cases, then Lineup re-ranks
    to top-k_lineup most-severe matches.
    """
    from shared.retrieval.retriever import search_for_case, search
    candidates = search_for_case(case, k=k_rachel)
    if not candidates:
        return []
    # Build the same query Rachel built
    cc = case.get("cc", "") or ""
    hpi = case.get("hpi", "") or ""
    query = f"{cc} {hpi}".strip()
    return rerank(query, candidates, top_k=k_lineup)


if __name__ == "__main__":
    import json, sys
    case = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {
        "cc": "chest pain", "hpi": "62yo M with hypertension, substernal pressure",
        "arrival": "ambulance",
    }
    out = rerank_for_case(case, k_rachel=50, k_lineup=5)
    print(json.dumps(out, indent=2))
