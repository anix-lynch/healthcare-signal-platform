"""Pattern 5 — Smoke Detector public API."""
from .baseline import detect_smoke, DEFAULT_THRESHOLD
from .schema import SmokeDetectorOutput, AnomalyMethod
from .anomaly_flagger import flag
from .drift import compute_drift

__all__ = [
    "detect_smoke",
    "DEFAULT_THRESHOLD",
    "SmokeDetectorOutput",
    "AnomalyMethod",
    "flag",
    "compute_drift",
]
