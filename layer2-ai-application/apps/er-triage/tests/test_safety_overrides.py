"""
SAFETY AGENT REGRESSION TEST.

Verifies hard rules cannot be bypassed:
  - chest pain → tier ≤ 2 even if LLM says 3
  - stroke signs → tier ≤ 2 even if LLM says 4
  - AMS → tier ≤ 2 even if LLM says 5
  - anaphylaxis → tier ≤ 2 even if LLM says 3
"""

import pytest


@pytest.mark.skip(reason="implement once safety_agent is ready")
def test_chest_pain_override():
    pass


@pytest.mark.skip(reason="implement once safety_agent is ready")
def test_stroke_override():
    pass


@pytest.mark.skip(reason="implement once safety_agent is ready")
def test_ams_override():
    pass


@pytest.mark.skip(reason="implement once safety_agent is ready")
def test_anaphylaxis_override():
    pass
