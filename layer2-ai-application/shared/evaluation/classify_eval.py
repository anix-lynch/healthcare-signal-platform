"""Pattern 2 (Traffic Light) eval — classification metrics.

🎯 ACCURACY + 🛡️ COMPLIANCE pillar evidence.
"""


def accuracy(predicted: list[int], gold: list[int]) -> float:
    raise NotImplementedError("TODO")


def macro_f1(predicted: list[int], gold: list[int]) -> float:
    """Macro-F1 across all ESI tiers — fair across class imbalance."""
    raise NotImplementedError("TODO")


def calibration_error(probabilities: list[float], gold: list[int]) -> float:
    """ECE — does the model's confidence match its actual accuracy?
    Critical for clinical settings: a confident wrong answer is worse
    than an uncertain right one."""
    raise NotImplementedError("TODO")
