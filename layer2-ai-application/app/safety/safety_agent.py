"""
LEVEL-2 AGENT · Safety Agent

Hard-rule overlay on top of the LLM classifier. The LLM is the soft
classifier; Safety Agent enforces non-negotiable rules.

Hard rules (initial set):
  - chest pain → never below ESI 2
  - stroke signs (FAST positive) → never below ESI 2
  - altered mental status → never below ESI 2
  - anaphylaxis / severe allergic reaction → never below ESI 2
  - active major bleeding → never below ESI 2

These rules are loaded from a YAML file so non-engineers can extend them
without code changes (compliance-friendly).

See mj/docs/tool_calling.md for the Level-2-agent architecture.
"""

from __future__ import annotations


def review(case: dict, llm_verdict: dict) -> dict:
    """
    Review the LLM's tier verdict. Override to lower (more urgent) number
    if any hard rule is triggered. Never override upward.
    """
    raise NotImplementedError(
        "Implement per docs/03_safety_agent.md. "
        "Load hard rules from configs/safety_rules.yaml. "
        "Return modified verdict + audit trail of any overrides."
    )


if __name__ == "__main__":
    review({}, {})
