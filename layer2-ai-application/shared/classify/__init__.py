"""Pattern 2 — Traffic Light public API."""
from .baseline import triage, triage_dict
from .schema import (
    TrafficLightOutput,
    TierBucket,
    ESITier,
    ClassifyMethod,
)
from .leakage_checks import (
    ClassifyLeakError,
    check_features,
    safe_feature_view,
    assert_train_split_disjoint,
)
from .router import classify, classify_dict, TriageDecision

__all__ = [
    "triage",
    "triage_dict",
    "TrafficLightOutput",
    "TierBucket",
    "ESITier",
    "ClassifyMethod",
    "ClassifyLeakError",
    "check_features",
    "safe_feature_view",
    "assert_train_split_disjoint",
    "classify",
    "classify_dict",
    "TriageDecision",
]
