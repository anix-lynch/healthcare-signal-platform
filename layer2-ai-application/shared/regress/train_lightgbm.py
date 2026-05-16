"""
Pattern 3 — Crystal Ball · Optional LightGBM trainer (tabular boost).

WHY this file exists:
    Boosting frequently beats LLMs on tabular regression. For LOS prediction
    on a registry dataset (15 columns, 55K rows), a tuned LightGBM will
    almost certainly out-RMSE both cohort-mean baseline AND any prompted LLM.

WHY this is OPTIONAL:
    - current data is registry, not EHR — model gains are bounded
    - cohort baseline is already operationally useful + explainable
    - training adds a dependency (lightgbm) and a model artifact path

WHEN to flip this on:
    - Layer 1 enriched dataset (registry_v2_enriched) is in place
    - You want a measurable RMSE win vs cohort baseline
    - You're willing to own the artifact lifecycle (versioning, retrain)

This module is a SCAFFOLD with TODOs. Do not consider it production until
the eval gate (`shared/regress/eval.py report()`) shows non-trivial lift
over baseline AND `leakage_checks.assert_train_split_disjoint` passes.
"""
from __future__ import annotations
from pathlib import Path

from .leakage_checks import (
    safe_feature_view,
    assert_train_split_disjoint,
    DISCHARGE_TIME_FIELDS,
)
from .eval import report as eval_report


# ── Feature plan (lock this before training) ───────────────────────────────
ALLOWED_FEATURES = (
    "age",
    "gender",
    "blood_type",
    "medical_condition",
    "admission_type",
    "medication",
    "insurance_provider",
    "hospital",
    "doctor",
    "season",                # derived from admission_date
    "age_band",              # bucket of age
    # IF enriched data is present, ALSO:
    "chief_complaint",       # bag-of-words → top-K features
    "esi_tier_truth",        # label, NOT feature — keep OUT
    # vitals (only if door-entry capture, NOT mid-stay updates)
    "bp_systolic", "bp_diastolic", "heart_rate", "respiratory_rate",
    "temperature_f", "spo2_pct",
)

# Things we ASSERT never sneak in:
NEVER_FEATURES = DISCHARGE_TIME_FIELDS | frozenset({"esi_tier_truth", "encounter_id"})


def build_dataset(rows: list[dict]) -> tuple[list[dict], list[float]]:
    """
    Take Layer 1 fact rows, return (X, y) for LightGBM.

    Drops leakage fields automatically via safe_feature_view().
    Target y = `length_of_stay_days` — this is the ONLY place we read it.
    """
    X: list[dict] = []
    y: list[float] = []
    for r in rows:
        if "length_of_stay_days" not in r:
            continue
        target = float(r["length_of_stay_days"])
        if target < 0 or target > 60:    # filter nonsense rows
            continue
        feats = safe_feature_view(r, allow_mid_stay=False)
        # extra strip: anything not in our allowlist
        feats = {k: v for k, v in feats.items() if k in ALLOWED_FEATURES}
        for k in NEVER_FEATURES:
            feats.pop(k, None)
        X.append(feats)
        y.append(target)
    return X, y


def train(X_train: list[dict], y_train: list[float], **lgb_kwargs):
    """
    TODO: requires `lightgbm` package. Wire when data is ready.

    Expected outline:
        import lightgbm as lgb
        import pandas as pd
        df_train = pd.DataFrame(X_train)
        categorical = ["gender", "blood_type", "medical_condition",
                       "admission_type", "medication", "insurance_provider",
                       "hospital", "doctor", "season", "age_band"]
        for c in categorical: df_train[c] = df_train[c].astype("category")
        params = {"objective": "regression", "metric": "mae",
                  "learning_rate": 0.05, "num_leaves": 31, ...}
        dataset = lgb.Dataset(df_train, label=y_train, categorical_feature=categorical)
        model = lgb.train(params, dataset, num_boost_round=500,
                          callbacks=[lgb.early_stopping(50)])
        return model
    """
    raise NotImplementedError(
        "LightGBM training is a scaffold. Wire after enriched data lands + cohort baseline RMSE recorded."
    )


def evaluate(model, X_test: list[dict], y_test: list[float]) -> dict:
    """Wraps prediction + eval.report(). TODO once `train()` is wired."""
    raise NotImplementedError("Wire after train() is implemented.")


if __name__ == "__main__":
    print(__doc__)
    print()
    print("Status: SCAFFOLD — not trained, not deployed.")
    print(f"Allowed features: {len(ALLOWED_FEATURES)} planned.")
    print(f"Forbidden fields enforced via NEVER_FEATURES + safe_feature_view().")
