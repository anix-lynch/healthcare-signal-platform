"""Pattern 2 (Traffic-Light) eval — classification metrics for ER triage.

Real metrics on the er-triage golden set. Deterministic. Writes JSON artifact.

Run:
    cd layer2-ai-application
    python -m shared.evaluation.classify_eval

Output:
    apps/er-triage/outputs/eval_traffic_light.json

🎯 ACCURACY pillar evidence.
"""

from __future__ import annotations
import json
import sys
import argparse
from pathlib import Path
from collections import Counter

HERE = Path(__file__).resolve().parent
LAYER2_ROOT = HERE.parent.parent          # …/layer2-ai-application
ER_TRIAGE = LAYER2_ROOT / "apps" / "er-triage"
sys.path.insert(0, str(ER_TRIAGE))         # so `safety.safety_agent` resolves

from shared.classify.router import classify as router_classify
from safety.safety_agent import review as safety_review
from shared.guardrails.output_guardrails import needs_human_escalation


def run_classifier(case: dict) -> dict:
    """Same pipeline as apps/er-triage/classify/esi_classifier.classify()."""
    verdict = router_classify(case).to_dict()
    reviewed = safety_review(case, verdict)
    reviewed["needs_human_escalation"] = needs_human_escalation(case, reviewed)
    return reviewed


# ── Metrics ─────────────────────────────────────────────────────────────────
def accuracy(predicted: list[int], gold: list[int]) -> float:
    if not gold: return 0.0
    return sum(p == g for p, g in zip(predicted, gold)) / len(gold)


def macro_f1(predicted: list[int], gold: list[int]) -> float:
    """Macro-F1 across classes 1-5."""
    classes = sorted(set(gold) | set(predicted))
    f1s = []
    for c in classes:
        tp = sum(1 for p, g in zip(predicted, gold) if p == c and g == c)
        fp = sum(1 for p, g in zip(predicted, gold) if p == c and g != c)
        fn = sum(1 for p, g in zip(predicted, gold) if p != c and g == c)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        f1s.append(f1)
    return sum(f1s) / len(f1s) if f1s else 0.0


def within_one_tolerance(predicted: list[int], gold: list[int]) -> float:
    """% of predictions within ±1 tier of gold (the production smoke-test bar)."""
    if not gold: return 0.0
    return sum(abs(p - g) <= 1 for p, g in zip(predicted, gold)) / len(gold)


def calibration_error(probabilities: list[float], gold: list[int], predicted: list[int]) -> float:
    """ECE (expected calibration error) across 4 confidence buckets."""
    if not probabilities: return 0.0
    n = len(probabilities)
    correct = [int(p == g) for p, g in zip(predicted, gold)]
    bins = [(0.0, 0.6), (0.6, 0.75), (0.75, 0.9), (0.9, 1.01)]
    ece = 0.0
    for lo, hi in bins:
        idx = [i for i, c in enumerate(probabilities) if lo <= c < hi]
        if not idx: continue
        bucket_acc = sum(correct[i] for i in idx) / len(idx)
        bucket_conf = sum(probabilities[i] for i in idx) / len(idx)
        ece += (len(idx) / n) * abs(bucket_acc - bucket_conf)
    return ece


# ── Run ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gold",
        default=str(ER_TRIAGE / "inputs" / "golden_esi.json"),
        help="Path to golden_esi.json",
    )
    parser.add_argument(
        "--out",
        default=str(ER_TRIAGE / "outputs" / "eval_traffic_light.json"),
        help="Path to write eval results JSON",
    )
    args = parser.parse_args()

    gold = json.loads(Path(args.gold).read_text())
    cases = gold["cases"]

    predictions: list[dict] = []
    pred_tiers: list[int] = []
    gold_tiers: list[int] = []
    confidences: list[float] = []
    safety_critical_violations = 0
    bucket_correct = 0
    must_be_at_most_violations: list[str] = []

    for c in cases:
        result = run_classifier(c["case"])
        pred_tier = int(result["esi_tier"])
        gold_tier = int(c["expected_tier"])

        pred_tiers.append(pred_tier)
        gold_tiers.append(gold_tier)
        confidences.append(float(result["confidence"]))

        if c.get("expected_bucket") and result["bucket"] == c["expected_bucket"]:
            bucket_correct += 1

        if "must_be_at_most" in c and pred_tier > c["must_be_at_most"]:
            must_be_at_most_violations.append(c["id"])
            if c.get("_safety_critical"):
                safety_critical_violations += 1

        predictions.append({
            "id": c["id"],
            "expected_tier": gold_tier,
            "predicted_tier": pred_tier,
            "expected_bucket": c.get("expected_bucket"),
            "predicted_bucket": result["bucket"],
            "confidence": result["confidence"],
            "safety_override": result.get("safety_override", False),
            "needs_human_escalation": result.get("needs_human_escalation", False),
            "reasoning": result.get("reasoning", ""),
            "red_flags": result.get("red_flags", []),
        })

    metrics = {
        "n_cases": len(cases),
        "accuracy_exact":          round(accuracy(pred_tiers, gold_tiers), 4),
        "accuracy_within_one_tier": round(within_one_tolerance(pred_tiers, gold_tiers), 4),
        "macro_f1":                round(macro_f1(pred_tiers, gold_tiers), 4),
        "calibration_error":       round(calibration_error(confidences, gold_tiers, pred_tiers), 4),
        "bucket_accuracy_now_soon_wait": round(bucket_correct / len(cases), 4),
        "safety_critical_violations":    safety_critical_violations,
        "must_be_at_most_violations":    must_be_at_most_violations,
        "human_escalation_rate":         round(
            sum(1 for p in predictions if p["needs_human_escalation"]) / len(predictions), 4
        ),
        "tier_distribution_pred": dict(Counter(pred_tiers)),
        "tier_distribution_gold": dict(Counter(gold_tiers)),
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "metrics": metrics,
        "predictions": predictions,
        "gold_set_path": args.gold,
        "classifier": "shared.classify.router (deterministic rule-based v1)",
    }, indent=2))

    print("=" * 60)
    print("TRAFFIC LIGHT (Pattern 2 — classify) eval")
    print("=" * 60)
    print(f"  cases:                       {metrics['n_cases']}")
    print(f"  accuracy (exact):            {metrics['accuracy_exact']:.2%}")
    print(f"  accuracy (within ±1 tier):   {metrics['accuracy_within_one_tier']:.2%}")
    print(f"  macro F1:                    {metrics['macro_f1']:.4f}")
    print(f"  bucket accuracy:             {metrics['bucket_accuracy_now_soon_wait']:.2%}")
    print(f"  calibration error (ECE):     {metrics['calibration_error']:.4f}")
    print(f"  safety-critical violations:  {metrics['safety_critical_violations']}")
    print(f"  human-escalation rate:       {metrics['human_escalation_rate']:.2%}")
    print(f"\n→ artifact: {out_path}")
    if metrics["safety_critical_violations"] > 0:
        print("\n[FAIL] Safety-critical case(s) classified above their tier cap.")
        sys.exit(2)
    print("\n[PASS] All safety-critical floors held.")


if __name__ == "__main__":
    main()
