"""Pattern 4 (Mad Lib) eval — generation metrics.

🎯 ACCURACY + 🛡️ COMPLIANCE pillar evidence.
"""


def faithfulness(generation: str, retrieved_sources: list[str]) -> float:
    """LLM-judge: every claim in the generation must be supported by a source.
    Score 0-1. Production gate: faithfulness >= 0.85 to ship."""
    raise NotImplementedError("TODO")


def groundedness(generation: str, retrieved_sources: list[str]) -> float:
    """% of claims with explicit citation back to a source."""
    raise NotImplementedError("TODO")


def llm_judge(generation: str, gold_answer: str | None = None, rubric: str | None = None) -> float:
    """Generic LLM-as-judge with rubric. Returns 0-1.
    Calibrate against human-labeled gold periodically to keep judge honest."""
    raise NotImplementedError("TODO")
