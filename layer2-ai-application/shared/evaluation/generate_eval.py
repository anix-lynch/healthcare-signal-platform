"""Pattern 4 (Mad Lib) eval — generation metrics for ER chart notes.

Real metrics on the er-triage golden set. Deterministic checks suited to a
template-based generator: structural completeness, faithfulness (no
hallucinated entities), bucket-tone consistency, length sanity.

For generators with an LLM enhancer, the same checks still apply — the
enhancer's contract is "polish prose only, never add facts," so faithfulness
should remain 1.0.

Run:
    cd layer2-ai-application
    python -m shared.evaluation.generate_eval

Output:
    apps/er-triage/outputs/eval_mad_lib.json

🎯 ACCURACY + 🛡️ COMPLIANCE pillar evidence.
"""

from __future__ import annotations
import json
import re
import sys
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAYER2_ROOT = HERE.parent.parent
ER_TRIAGE = LAYER2_ROOT / "apps" / "er-triage"
sys.path.insert(0, str(ER_TRIAGE))

from shared.classify.router import classify as router_classify
from safety.safety_agent import review as safety_review
from shared.guardrails.output_guardrails import needs_human_escalation
from shared.generate.chart_note import generate as gen_views


REQUIRED_VIEWS = [
    "chart_note",
    "nurse_handoff",
    "patient_explanation",
    "clinician_summary",
    "executive_summary",
]

REQUIRED_CHART_SECTIONS = [
    "CHIEF COMPLAINT", "ARRIVAL", "HISTORY OF PRESENT ILLNESS",
    "Vitals:", "ASSESSMENT:", "PLAN / DISPOSITION:", "AUDIT:",
]

BUCKET_KEYWORDS = {
    "NOW":  ["immediate", "right now", "resuscitation", "right away"],
    "SOON": ["prompt", "shortly", "main ED", "as soon as"],
    "WAIT": ["non-urgent", "after higher", "fast track", "wait", "patience"],
}


# ── Metrics ─────────────────────────────────────────────────────────────────
def structural_completeness(views: dict) -> tuple[float, list[str]]:
    """All 5 views present and non-empty + chart_note has all required sections."""
    missing: list[str] = []
    for v in REQUIRED_VIEWS:
        if not views.get(v) or not str(views[v]).strip():
            missing.append(f"missing_view:{v}")
    chart = views.get("chart_note", "")
    for sec in REQUIRED_CHART_SECTIONS:
        if sec not in chart:
            missing.append(f"missing_section:{sec}")
    score = 1.0 - (len(missing) / (len(REQUIRED_VIEWS) + len(REQUIRED_CHART_SECTIONS)))
    return score, missing


def _allowed_numbers(case: dict, triage: dict) -> set[float]:
    """All numeric values that may legitimately appear in any view (as floats)."""
    src_text = " ".join([
        str(case.get("cc", "")),
        str(case.get("hpi", "")),
        str(case.get("arrival", "")),
        json.dumps(case.get("vitals") or {}),
        triage.get("reasoning", ""),
        str(triage.get("esi_tier", "")),
        str(triage.get("confidence", "")),
        str(triage.get("resources_expected", "")),
        str(triage.get("pre_override_tier", "")),
        " ".join(triage.get("red_flags") or []),
        " ".join(triage.get("override_reason") or []),
    ])
    return {float(n) for n in re.findall(r"\d+(?:\.\d+)?", src_text)}


def faithfulness_no_hallucinated_numbers(views: dict, case: dict, triage: dict) -> tuple[float, list[str]]:
    """
    Every numeric value in any view must trace back to inputs (case + triage).
    Numeric comparison (so "0.7" == "0.70" == "0.700"). Hard fail in healthcare.
    """
    allowed = _allowed_numbers(case, triage)
    violations: list[str] = []
    for view_name, content in views.items():
        if view_name.startswith("_") or not isinstance(content, str):
            continue
        for num_str in re.findall(r"\d+(?:\.\d+)?", content):
            if float(num_str) not in allowed:
                violations.append(f"{view_name}:{num_str}")
    score = 1.0 if not violations else max(0.0, 1.0 - len(violations) * 0.1)
    return score, violations


def bucket_tone_consistency(views: dict, triage: dict) -> tuple[float, list[str]]:
    """
    Patient explanation and disposition should reflect the triage bucket.
    NOW-tier explanation must contain urgency keywords; WAIT-tier must contain
    non-urgent keywords.
    """
    bucket = triage.get("bucket", "WAIT")
    keywords = BUCKET_KEYWORDS.get(bucket, [])
    failures: list[str] = []
    for v in ["chart_note", "patient_explanation"]:
        text = views.get(v, "").lower()
        if not any(k in text for k in keywords):
            failures.append(f"{v}_missing_{bucket}_tone")
    score = 1.0 - (len(failures) / 2)
    return score, failures


def length_sanity(views: dict) -> tuple[float, list[str]]:
    """Each view within sensible bounds. No empty, no novella."""
    BOUNDS = {
        "chart_note":          (200, 2500),
        "nurse_handoff":       (40, 400),
        "patient_explanation": (60, 600),
        "clinician_summary":   (15, 250),
        "executive_summary":   (15, 200),
    }
    failures = []
    for v, (lo, hi) in BOUNDS.items():
        n = len(views.get(v, ""))
        if not (lo <= n <= hi):
            failures.append(f"{v}_len_{n}_outside_[{lo},{hi}]")
    score = 1.0 - (len(failures) / len(BOUNDS))
    return score, failures


# ── Run ─────────────────────────────────────────────────────────────────────
def _full_triage(case: dict) -> dict:
    verdict = router_classify(case).to_dict()
    reviewed = safety_review(case, verdict)
    reviewed["needs_human_escalation"] = needs_human_escalation(case, reviewed)
    return reviewed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", default=str(ER_TRIAGE / "inputs" / "golden_esi.json"))
    parser.add_argument("--out", default=str(ER_TRIAGE / "outputs" / "eval_mad_lib.json"))
    args = parser.parse_args()

    gold = json.loads(Path(args.gold).read_text())
    cases = gold["cases"]

    per_case: list[dict] = []
    completeness_scores: list[float] = []
    faithfulness_scores: list[float] = []
    tone_scores: list[float] = []
    length_scores: list[float] = []
    all_violations: list[str] = []

    for c in cases:
        triage = _full_triage(c["case"])
        views = gen_views(c["case"], triage, enhance=False)

        comp_score, comp_missing = structural_completeness(views)
        faith_score, faith_violations = faithfulness_no_hallucinated_numbers(views, c["case"], triage)
        tone_score, tone_failures = bucket_tone_consistency(views, triage)
        len_score, len_failures = length_sanity(views)

        completeness_scores.append(comp_score)
        faithfulness_scores.append(faith_score)
        tone_scores.append(tone_score)
        length_scores.append(len_score)

        all_violations.extend(faith_violations)

        per_case.append({
            "id": c["id"],
            "triage_tier": triage["esi_tier"],
            "bucket": triage["bucket"],
            "completeness": round(comp_score, 4),
            "faithfulness": round(faith_score, 4),
            "tone_consistency": round(tone_score, 4),
            "length_sanity": round(len_score, 4),
            "issues": {
                "missing": comp_missing,
                "hallucinated_numbers": faith_violations,
                "tone_failures": tone_failures,
                "length_failures": len_failures,
            },
            "executive_summary": views["executive_summary"],
        })

    n = len(cases)
    metrics = {
        "n_cases": n,
        "structural_completeness_mean": round(sum(completeness_scores) / n, 4),
        "faithfulness_mean":            round(sum(faithfulness_scores) / n, 4),
        "bucket_tone_consistency_mean": round(sum(tone_scores) / n, 4),
        "length_sanity_mean":           round(sum(length_scores) / n, 4),
        "hallucinated_numbers_total":   len(all_violations),
        "all_views_complete_pct":       round(sum(s == 1.0 for s in completeness_scores) / n, 4),
        "all_views_faithful_pct":       round(sum(s == 1.0 for s in faithfulness_scores) / n, 4),
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "metrics": metrics,
        "per_case": per_case,
        "generator": "shared.generate.chart_note (deterministic templates v1)",
        "gold_set_path": args.gold,
    }, indent=2))

    print("=" * 60)
    print("MAD LIB (Pattern 4 — generate) eval")
    print("=" * 60)
    print(f"  cases:                          {metrics['n_cases']}")
    print(f"  structural_completeness (mean): {metrics['structural_completeness_mean']:.4f}")
    print(f"  faithfulness (mean):            {metrics['faithfulness_mean']:.4f}")
    print(f"  bucket_tone_consistency (mean): {metrics['bucket_tone_consistency_mean']:.4f}")
    print(f"  length_sanity (mean):           {metrics['length_sanity_mean']:.4f}")
    print(f"  all_views_complete:             {metrics['all_views_complete_pct']:.2%}")
    print(f"  all_views_faithful:             {metrics['all_views_faithful_pct']:.2%}")
    print(f"  hallucinated_numbers (total):   {metrics['hallucinated_numbers_total']}")
    print(f"\n→ artifact: {out_path}")
    if metrics["hallucinated_numbers_total"] > 0:
        print("\n[FAIL] Hallucinated numeric values present.")
        sys.exit(2)
    print("\n[PASS] No hallucinated numbers; structural + tone bars held.")


if __name__ == "__main__":
    main()
