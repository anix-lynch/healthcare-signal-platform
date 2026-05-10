"""
SMOKE TEST · ESI auto-tagger.

Must-pass criteria:
  1. Every gold case classifies within ±1 of expected tier
  2. Every safety-critical case (chest pain, stroke, AMS, anaphylaxis)
     classifies ≤ 2 (NEVER higher than ESI 2)
  3. Every output has a non-empty reasoning field

If this test fails in CI → ER3 does not ship.
"""

from __future__ import annotations
import json
import pathlib
import pytest


GOLDEN_SET = pathlib.Path(__file__).resolve().parents[1] / "inputs" / "golden_esi.json"


@pytest.fixture
def golden():
    return json.loads(GOLDEN_SET.read_text())


def test_golden_set_loadable(golden):
    assert "cases" in golden
    assert len(golden["cases"]) >= 2  # grow to 30


@pytest.mark.skip(reason="implement once esi_classifier is ready")
def test_every_case_within_tolerance(golden):
    """Each prediction must be within ±1 tier of expected."""
    pass


@pytest.mark.skip(reason="implement once esi_classifier + safety_agent are ready")
def test_safety_critical_never_above_tier_2(golden):
    """Chest pain / stroke / AMS / anaphylaxis must never classify ≥ 3."""
    pass


@pytest.mark.skip(reason="implement once esi_classifier is ready")
def test_reasoning_field_non_empty(golden):
    """Every output must have a non-empty reasoning string."""
    pass
