"""Pattern 3 — Crystal Ball (Regression) | seven-lens

ER context: "Predict length-of-stay for this incoming patient."
GenAI lens: LLM with Pydantic structured output OR LightGBM on
embedding features for tiny / medium datasets.

Eval metrics live in app/evaluation/regress_eval.py:
    MAE · R² · structured-output validity rate
"""

from pydantic import BaseModel, Field


class LoSPrediction(BaseModel):
    hours: float = Field(..., ge=0, description="Predicted length-of-stay in hours")
    confidence: float = Field(..., ge=0, le=1, description="Model confidence 0-1")
    reasoning: str = Field(..., description="Brief clinical reasoning trace")


def predict_los(case: dict) -> LoSPrediction:
    """Predict length-of-stay for a single ER case.

    Returns a Pydantic model so downstream code can rely on schema validity
    (and we can measure structured-output-validity rate as an eval signal).
    """
    raise NotImplementedError("TODO: LLM with structured output OR LightGBM on case embedding")
