"""
Pattern 4 — Mad Lib · Output schema.

    "explain this shit to humans 😭"

Generates a chart note / nurse handoff / patient explanation, GROUNDED in
the Rachel hits + the Traffic Light tier. Every claim must cite a Rachel
source_id; uncited claims = hallucinations.
"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


GenerationMethod = Literal["template", "llm_enhanced"]


class MadLibOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pattern: Literal["mad_lib_generation"] = "mad_lib_generation"
    case_id: str
    chart_note: str = Field(..., description="A&P style note for the clinician")
    nurse_handoff: str = Field(..., description="one-paragraph SBAR-style handoff")
    patient_explanation: str = Field(..., description="lay-language summary, ESL-safe")
    citations: list[str] = Field(default_factory=list, description="source_ids cited")
    citations_validated: bool = Field(..., description="every cite resolved in store")
    faithfulness_score: float | None = Field(None, ge=0, le=1, description=(
        "Ragas-style faithfulness — fraction of claims supported by cited evidence"
    ))
    generation_method: GenerationMethod
    fallback_used: bool = False
    warnings: list[str] = Field(default_factory=list)
