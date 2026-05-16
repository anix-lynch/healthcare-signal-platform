"""
Pattern 3 — Crystal Ball · Leakage guards.

Predicting future using discharge_date = exam cheating with the answer key 😭

This module enforces "what could the model see at PREDICTION TIME?" — i.e.
the moment the patient walks through the ER door, before discharge,
before lab results final, before billing close.

It is the most under-thought layer in healthcare ML. Without it, you ship
a model with AUC 0.98 in dev that collapses to 0.55 in prod because the
feature it was leaning on doesn't exist until 12 hours after intake.
"""
from __future__ import annotations
from typing import Iterable


# Fields that ONLY exist at-or-after discharge. Forbidden at prediction time.
DISCHARGE_TIME_FIELDS = frozenset({
    "discharge_date",
    "Discharge Date",
    "length_of_stay_days",       # this IS the answer for LoS prediction
    "los_days",
    "billing_amount",            # finalized at discharge
    "Billing Amount",
    "cost_per_day",
    "is_readmission",            # IS the answer for readmission prediction
    "previous_admission_count_after_today",   # forward-leaking definition
    "test_results_final",        # lab results come back hours later
    "Test Results",              # in current dataset this is final-state
})

# Fields that arrive AFTER intake but before discharge. Time-of-prediction matters.
MID_STAY_FIELDS = frozenset({
    "physician_note",            # written after assessment, not on door entry
    "lab_panel_json",            # ordered after triage decision
    "lab_flags",
    "esi_tier_truth",            # ground-truth label, never a feature
    "acuity_red_flags",          # same
})


class LeakageError(ValueError):
    """Raised when a feature payload contains future-knowledge fields."""


def check_features(features: dict, *, allow_mid_stay: bool = False) -> None:
    """
    Sanity-check a feature dict before handing it to a regressor.

    Raises LeakageError if a forbidden field is present. Intentionally
    fail-loud — silent leakage is the bug that ships.

    Args:
        features: the dict the caller wants to feed Crystal Ball.
        allow_mid_stay: True only for "post-triage prognosis update" use cases
                        where physician notes etc. are legitimately available.
    """
    found_discharge = set(features.keys()) & DISCHARGE_TIME_FIELDS
    if found_discharge:
        raise LeakageError(
            f"discharge-time fields in prediction features = answer-key cheat: {sorted(found_discharge)}. "
            f"Strip these before calling Crystal Ball."
        )
    if not allow_mid_stay:
        found_mid = set(features.keys()) & MID_STAY_FIELDS
        if found_mid:
            raise LeakageError(
                f"mid-stay fields require explicit allow_mid_stay=True flag: {sorted(found_mid)}. "
                f"If this is a post-triage update, set the flag and document why."
            )


def safe_feature_view(row: dict, *, allow_mid_stay: bool = False) -> dict:
    """
    Return a copy of `row` with leakage-prone fields stripped, for safe inference.

    Use when you have a full encounter row (e.g. from fact_patient_encounters)
    and want to simulate "what was knowable at door-entry."
    """
    forbidden = DISCHARGE_TIME_FIELDS if allow_mid_stay else (DISCHARGE_TIME_FIELDS | MID_STAY_FIELDS)
    return {k: v for k, v in row.items() if k not in forbidden}


def assert_train_split_disjoint(train_ids: Iterable[str], test_ids: Iterable[str]) -> None:
    """Catch the dumbest leak: same encounter in both splits."""
    overlap = set(train_ids) & set(test_ids)
    if overlap:
        raise LeakageError(
            f"{len(overlap)} encounter_ids appear in BOTH train and test split — "
            f"this is identity leak, not generalization. First few: {sorted(overlap)[:5]}"
        )
