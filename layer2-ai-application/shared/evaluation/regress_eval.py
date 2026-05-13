"""Pattern 3 (Crystal Ball) eval — LOS regression metrics.

Real metrics on a held-out random sample from the Layer 1 corpus:
  - MAE (mean absolute error in days)
  - RMSE
  - R² (coefficient of determination)
  - Bin accuracy (short / medium / long)
  - Structural output validity (every prediction has all required fields)

Run:
    cd layer2-ai-application
    python -m shared.evaluation.regress_eval

Output:
    apps/er-triage/outputs/eval_crystal_ball.json

🎯 ACCURACY pillar evidence.
"""

from __future__ import annotations
import json
import math
import random
import sys
import argparse
import csv
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).resolve().parent
LAYER2_ROOT = HERE.parent.parent
ER_TRIAGE = LAYER2_ROOT / "apps" / "er-triage"
LAYER1_CSV = LAYER2_ROOT.parent / "layer1-data-backbone" / "data" / "raw" / "healthcare_dataset.csv"

from shared.regress.los_predictor import (
    _ensure_model, _bin, predict_los,
)


def mae(predicted: list[float], gold: list[float]) -> float:
    if not gold: return 0.0
    return sum(abs(p - g) for p, g in zip(predicted, gold)) / len(gold)


def rmse(predicted: list[float], gold: list[float]) -> float:
    if not gold: return 0.0
    return math.sqrt(sum((p - g) ** 2 for p, g in zip(predicted, gold)) / len(gold))


def r_squared(predicted: list[float], gold: list[float]) -> float:
    if not gold: return 0.0
    mean_g = sum(gold) / len(gold)
    ss_res = sum((g - p) ** 2 for g, p in zip(gold, predicted))
    ss_tot = sum((g - mean_g) ** 2 for g in gold)
    if ss_tot == 0: return 0.0
    return 1.0 - (ss_res / ss_tot)


def structured_output_validity(outputs: list[dict], schema_class=None) -> float:
    """% of predictions with all required fields."""
    required = {"predicted_days", "bin", "confidence", "cohort_n", "source_level", "reasoning"}
    if not outputs: return 0.0
    return sum(1 for o in outputs if isinstance(o, dict) and required.issubset(o.keys())) / len(outputs)


def bin_accuracy(pred_bins: list[str], gold_bins: list[str]) -> float:
    if not gold_bins: return 0.0
    return sum(p == g for p, g in zip(pred_bins, gold_bins)) / len(gold_bins)


def _load_eval_sample(n: int, seed: int) -> list[dict]:
    rnd = random.Random(seed)
    rows = []
    with LAYER1_CSV.open(newline="") as f:
        for row in csv.DictReader(f):
            try:
                age = int(float(row["Age"]))
                adm = datetime.fromisoformat(row["Date of Admission"]).date()
                dis = datetime.fromisoformat(row["Discharge Date"]).date()
                los = (dis - adm).days
                if los < 0 or los > 60: continue
            except (ValueError, KeyError):
                continue
            if not (row.get("Medical Condition") and row.get("Gender") and row.get("Admission Type")):
                continue
            rows.append({
                "age": age, "gender": row["Gender"],
                "condition": row["Medical Condition"],
                "admission": row["Admission Type"],
                "los_days": los,
            })
    return rnd.sample(rows, k=min(n, len(rows)))


def _row_to_case(r: dict) -> dict:
    return {
        "cc": r["condition"],
        "hpi": f"{r['age']}yo {r['gender'][0]} with {r['condition']}",
        "arrival": "walk-in" if r["admission"] == "Elective" else "ambulance",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-sample", type=int, default=500)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--out", default=str(ER_TRIAGE / "outputs" / "eval_crystal_ball.json"))
    args = parser.parse_args()

    print("Loading cohort LOS model...")
    _ensure_model()
    print(f"Building held-out sample (n={args.n_sample})...")
    sample = _load_eval_sample(args.n_sample, args.seed)

    pred_days, gold_days, pred_bins, gold_bins = [], [], [], []
    outputs = []

    for r in sample:
        triage_hint = {"bucket": {"Emergency": "NOW", "Urgent": "SOON", "Elective": "WAIT"}[r["admission"]]}
        prediction = predict_los(_row_to_case(r), triage=triage_hint).to_dict()
        outputs.append(prediction)
        pred_days.append(prediction["predicted_days"])
        gold_days.append(float(r["los_days"]))
        pred_bins.append(prediction["bin"])
        gold_bins.append(_bin(r["los_days"]))

    metrics = {
        "n_sample":             len(sample),
        "mae_days":             round(mae(pred_days, gold_days), 4),
        "rmse_days":            round(rmse(pred_days, gold_days), 4),
        "r_squared":            round(r_squared(pred_days, gold_days), 4),
        "bin_accuracy":         round(bin_accuracy(pred_bins, gold_bins), 4),
        "structured_validity":  round(structured_output_validity(outputs), 4),
        "predicted_range_days": [round(min(pred_days), 2), round(max(pred_days), 2)],
        "gold_range_days":      [min(gold_days), max(gold_days)],
        "model": "cohort-mean hierarchical lookup (Layer 1 corpus, 55K rows)",
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"metrics": metrics, "sample_predictions": outputs[:25]}, indent=2))

    print("=" * 60)
    print("CRYSTAL BALL (Pattern 3 — regress) eval")
    print("=" * 60)
    print(f"  n sample:              {metrics['n_sample']}")
    print(f"  MAE (days):            {metrics['mae_days']:.4f}")
    print(f"  RMSE (days):           {metrics['rmse_days']:.4f}")
    print(f"  R²:                    {metrics['r_squared']:.4f}")
    print(f"  Bin accuracy:          {metrics['bin_accuracy']:.4f}")
    print(f"  Structured validity:   {metrics['structured_validity']:.4f}")
    print(f"\n→ artifact: {out_path}")


if __name__ == "__main__":
    main()
