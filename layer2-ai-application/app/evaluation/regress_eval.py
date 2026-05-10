"""Pattern 3 (Crystal Ball) eval — regression metrics.

🛡️ COMPLIANCE + 🎯 ACCURACY pillar evidence.
"""


def mae(predicted: list[float], gold: list[float]) -> float:
    """Mean absolute error in hours."""
    raise NotImplementedError("TODO")


def r_squared(predicted: list[float], gold: list[float]) -> float:
    raise NotImplementedError("TODO")


def structured_output_validity(outputs: list[dict], schema_class) -> float:
    """% of outputs that pass Pydantic validation against the declared schema.
    A primary 🛡️ COMPLIANCE signal — if the LLM can't honor a schema,
    downstream code can't trust it."""
    raise NotImplementedError("TODO")
