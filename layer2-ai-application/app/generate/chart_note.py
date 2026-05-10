"""Pattern 4 — Mad Lib (Generation) | seven-lens

ER context: "Draft a chart note for this triage decision, citing
the past cases the retrieval layer surfaced."
GenAI lens: RAG (Rachel feeds Mad Lib) + structured output + cite-or-refuse.

Eval metrics live in app/evaluation/generate_eval.py:
    faithfulness · groundedness · LLM-judge

Note: ER2 already ships a working Mad Lib for this domain. ER3's copy
is for local eval harness wiring (and to make the 7-lens module map
complete inside ER3).
"""

from pydantic import BaseModel, Field


class ChartNote(BaseModel):
    summary: str = Field(..., description="Triage rationale, 2-3 sentences")
    citations: list[str] = Field(..., description="case_ids cited from retrieval")
    confidence: float = Field(..., ge=0, le=1)


def draft_chart_note(case: dict, retrieved_cases: list[dict]) -> ChartNote:
    """Generate a chart note grounded in retrieved past cases.

    Must cite at least one retrieved case_id. Refuse (raise) if no
    retrieval results — never hallucinate citations.
    """
    raise NotImplementedError("TODO: prompt template + LLM call + cite-or-refuse guard")
