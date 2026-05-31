"""Pattern 5 eval — per-case anomaly detection.

Synthetic injection eval:
    1. Sample N normal cases from Layer 1 with triage bucket matched to admission.
    2. Generate M outliers from the same corpus but with triage bucket
       deliberately mismatched (e.g., Emergency-admitted cohort labeled WAIT).
    3. Score precision + recall + F1 of the flagger on the labeled set.

Run:
    cd layer2-ai-application
    python -m shared.evaluation.anomaly_eval

Output:
    apps/er-triage/outputs/eval_smoke_detector.json

🎯 ACCURACY pillar evidence.
"""

from __future__ import annotations
import json
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

from shared.anomaly.anomaly_flagger import flag, _ensure_table
from shared.regress.los_predictor import predict_los


def precision_recall_on_synthetic_outliers(flags_pred: list[bool], labels: list[bool]) -> dict:
    tp = sum(1 for p, l in zip(flags_pred, labels) if p and l)
    fp = sum(1 for p, l in zip(flags_pred, labels) if p and not l)
    fn = sum(1 for p, l in zip(flags_pred, labels) if not p and l)
    tn = sum(1 for p, l in zip(flags_pred, labels) if not p and not l)
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec  = tp / (tp + fn) if (tp + fn) else 0.0
    f1   = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return {"precision": prec, "recall": rec, "f1": f1,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn}


def centroid_drift_score(current_embeddings, reference_embeddings) -> float:
    """Stub — population drift is out of scope for per-case Pattern 5."""
    return 0.0


def _row_to_case(r: dict) -> dict:
    return {
        "cc": r.get("Medical Condition", ""),
        "hpi": f"{r['Age']}yo {r['Gender'][0]} with {r.get('Medical Condition', '')}",
        "arrival": "walk-in",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-normal", type=int, default=200)
    parser.add_argument("--n-outliers", type=int, default=50)
    parser.add_argument("--seed", type=int, default=29)
    parser.add_argument("--out", default=str(ER_TRIAGE / "outputs" / "eval_smoke_detector.json"))
    args = parser.parse_args()

    print("Loading cohort stats...")
    _ensure_table()
    print(f"Sampling {args.n_normal} normal + {args.n_outliers} synthetic outliers...")

    rnd = random.Random(args.seed)
    rows = []
    with LAYER1_CSV.open(newline="") as f:
        for row in csv.DictReader(f):
            try:
                int(float(row["Age"]))
                datetime.fromisoformat(row["Date of Admission"])
            except (ValueError, KeyError):
                continue
            rows.append(row)
    sample = rnd.sample(rows, k=min(args.n_normal + args.n_outliers, len(rows)))
    normal_rows = sample[:args.n_normal]
    outlier_rows = sample[args.n_normal:args.n_normal + args.n_outliers]

    flags_pred, labels, per_case = [], [], []

    for r in normal_rows:
        case = _row_to_case(r)
        bucket = {"Emergency": "NOW", "Urgent": "SOON", "Elective": "WAIT"}.get(r["Admission Type"], "WAIT")
        triage = {"bucket": bucket, "confidence": 0.85}
        los_pred = predict_los(case, triage=triage).to_dict()
        result = flag(case, triage=triage, los_prediction=los_pred)
        flags_pred.append(result["is_anomaly"])
        labels.append(False)
        per_case.append({"label": "normal", "is_anomaly": result["is_anomaly"], "reason": result["reason"]})

    for r in outlier_rows:
        case = _row_to_case(r)
        true_adm = r["Admission Type"]
        bucket = "WAIT" if true_adm == "Emergency" else ("NOW" if true_adm == "Elective" else "WAIT")
        triage = {"bucket": bucket, "confidence": 0.55}
        los_pred = predict_los(case, triage=triage).to_dict()
        result = flag(case, triage=triage, los_prediction=los_pred)
        flags_pred.append(result["is_anomaly"])
        labels.append(True)
        per_case.append({"label": "outlier", "is_anomaly": result["is_anomaly"],
                         "reason": result["reason"], "axes": result["triggered_axes"]})

    pr = precision_recall_on_synthetic_outliers(flags_pred, labels)
    metrics = {
        "n_normal":                  args.n_normal,
        "n_outliers":                args.n_outliers,
        "precision":                 round(pr["precision"], 4),
        "recall":                    round(pr["recall"], 4),
        "f1":                        round(pr["f1"], 4),
        "tp":                        pr["tp"],
        "fp":                        pr["fp"],
        "fn":                        pr["fn"],
        "tn":                        pr["tn"],
        "false_positive_rate_normal": round(pr["fp"] / args.n_normal, 4) if args.n_normal else 0.0,
        "model": "z-score over cohort (gender × condition × age_band) on LOS + admission alignment",
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"metrics": metrics, "sample_per_case": per_case[:25]}, indent=2))

    print("=" * 60)
    print("SMOKE DETECTOR (Pattern 5 — anomaly) eval")
    print("=" * 60)
    print(f"  n normal / outliers:        {metrics['n_normal']} / {metrics['n_outliers']}")
    print(f"  precision:                  {metrics['precision']:.4f}")
    print(f"  recall:                     {metrics['recall']:.4f}")
    print(f"  F1:                         {metrics['f1']:.4f}")
    print(f"  tp / fp / fn / tn:          {pr['tp']} / {pr['fp']} / {pr['fn']} / {pr['tn']}")
    print(f"  false-positive-rate (normal): {metrics['false_positive_rate_normal']:.4f}")
    print(f"\n→ artifact: {out_path}")


if __name__ == "__main__":
    main()
