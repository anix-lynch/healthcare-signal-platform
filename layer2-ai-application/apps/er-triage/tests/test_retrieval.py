"""
RETRIEVAL (Pattern 1 — Rachel) tests.

Verifies:
  - BM25 index loads from Layer 1 corpus
  - search() returns ranked hits
  - Top hit for a clear query matches the demographic+condition
  - Empty / unknown queries return [] not crash
  - search_for_case() builds query from triage case shape
"""

from __future__ import annotations
import sys
import pathlib
import pytest

ER_TRIAGE = pathlib.Path(__file__).resolve().parents[1]
LAYER2_ROOT = ER_TRIAGE.parent.parent
sys.path.insert(0, str(LAYER2_ROOT))

from shared.retrieval.retriever import search, search_for_case, index_size, index_cases


def test_index_loads():
    """Default Layer 1 corpus indexes ~55,500 docs."""
    n = index_size()
    assert n > 50_000, f"expected >50k docs in Layer 1 corpus, got {n}"


def test_search_returns_ranked_hits():
    hits = search("62yo male hypertension", k=5)
    assert len(hits) > 0
    assert len(hits) <= 5
    # scores must be monotonically non-increasing
    scores = [h["score"] for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_top_hit_matches_demographics():
    """A precise query should surface a row matching age+gender+condition."""
    hits = search("62yo male hypertension", k=3)
    top = hits[0]
    snippet = top["snippet"].lower()
    assert "62" in snippet
    assert "male" in snippet
    assert "hypertension" in snippet


def test_empty_query_returns_empty():
    assert search("", k=10) == []
    assert search("   ", k=10) == []


def test_search_for_case_builds_query():
    """Convenience wrapper extracts age + gender from HPI."""
    case = {
        "cc": "shortness of breath",
        "hpi": "70yo F with asthma history",
        "vitals": {},
        "arrival": "walk-in",
    }
    hits = search_for_case(case, k=3)
    assert len(hits) > 0
    # Top hit should be 70-ish, female-ish, asthma-ish
    top_snippet = hits[0]["snippet"].lower()
    assert "asthma" in top_snippet or "70" in top_snippet


def test_index_cases_replaces_default():
    """index_cases() can swap in a custom corpus."""
    custom = [
        {"case_id": "C1", "snippet": "70yo female asthma emergency"},
        {"case_id": "C2", "snippet": "30yo male diabetes elective"},
    ]
    index_cases(custom)
    hits = search("asthma", k=2)
    assert len(hits) == 1
    assert hits[0]["case_id"] == "C1"
    # Restore default for other tests
    from shared.retrieval import retriever
    retriever._INDEX = None
