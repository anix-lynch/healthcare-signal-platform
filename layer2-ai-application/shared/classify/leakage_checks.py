"""
Pattern 2 — Traffic Light · Leakage guards.

Classifying ESI tier using esi_tier_truth = exam cheating with answer key 😭

Triage runs at door entry. The only features available:
    - chief complaint (free text)
    - HPI / arrival mode
    - vitals at intake (BP, HR, RR, T, SpO2)
    - patient history flags (high_utilizer, prior visits)

NOT available at door entry (any of these in features = leak):
    - esi_tier_truth          ← THE LABEL
    - actual discharge tier   ← finalized hours later
    - acuity_red_flags        ← LLM-generated label, not source feature
    - physician_note          ← written AFTER triage
    - lab_panel_json          ← ordered AFTER triage decision
"""
from __future__ import annotations
from typing import Iterable


# Fields that ONLY exist with future knowledge.
FORBIDDEN_FEATURES = frozenset({
    "esi_tier_truth",         # the label itself
    "acuity_red_flags",       # LLM-derived label, not source signal
    "physician_note",         # written after triage assessment
    "discharge_date",
    "Discharge Date",
    "length_of_stay_days",
    "los_days",
    "is_readmission",
    "billing_amount",
    "Billing Amount",
})

# Fields that arrive AFTER triage but before discharge — only OK in specific use cases.
POST_TRIAGE_FIELDS = frozenset({
    "lab_panel_json",         # ordered after triage decision
    "lab_flags",              # derived from labs
    "Test Results",           # in current dataset this is final-state
})


class ClassifyLeakError(ValueError):
    """Raised when classify features contain future-knowledge fields."""


def check_features(features: dict, *, allow_post_triage: bool = False) -> None:
    """
    Sanity-check a feature dict before handing it to a classifier.

    Raises ClassifyLeakError if a forbidden field is present. Fail loud.

    Args:
        features: dict the caller wants to feed Traffic Light.
        allow_post_triage: True only for "post-labs re-classify" use cases.
    """
    found = set(features.keys()) & FORBIDDEN_FEATURES
    if found:
        raise ClassifyLeakError(
            f"forbidden label/future fields in classifier features = answer-key cheat: {sorted(found)}. "
            f"Strip these before calling classify()."
        )
    if not allow_post_triage:
        found_post = set(features.keys()) & POST_TRIAGE_FIELDS
        if found_post:
            raise ClassifyLeakError(
                f"post-triage fields require explicit allow_post_triage=True: {sorted(found_post)}. "
                f"If this is a 'labs back, re-classify' update, set the flag and document why."
            )


def safe_feature_view(row: dict, *, allow_post_triage: bool = False) -> dict:
    """Strip leakage-prone fields. Use to simulate door-entry feature view."""
    forbidden = FORBIDDEN_FEATURES if allow_post_triage else (FORBIDDEN_FEATURES | POST_TRIAGE_FIELDS)
    return {k: v for k, v in row.items() if k not in forbidden}


def assert_train_split_disjoint(train_ids: Iterable[str], test_ids: Iterable[str]) -> None:
    """Catch the dumbest leak: same encounter in both splits."""
    overlap = set(train_ids) & set(test_ids)
    if overlap:
        raise ClassifyLeakError(
            f"{len(overlap)} encounter_ids in BOTH train and test split — identity leak. "
            f"First: {sorted(overlap)[:5]}"
        )
