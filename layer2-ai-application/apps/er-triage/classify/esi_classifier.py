"""
ER triage entry point — Layer 1 patient → Layer 2 classifier → safety review.

Pipeline:
    case dict
        → shared.classify.router.classify   (ESI 1-5 + NOW/SOON/WAIT + confidence)
        → safety.safety_agent.review        (hard-rule floor enforcement)
        → shared.guardrails.output_guardrails.needs_human_escalation
                                             (low-confidence routing)
        → final triage decision (dict, JSON-serializable)

Fields in final decision:
    esi_tier              : int (1-5, after safety override)
    bucket                : "NOW" / "SOON" / "WAIT"
    confidence            : float 0-1
    reasoning             : str  (audit trail — what triggered)
    red_flags             : list[str]
    resources_expected    : int
    safety_override       : bool
    override_reason       : list[str]
    needs_human_escalation: bool
"""

from __future__ import annotations
from typing import Any

from shared.classify.router import classify as _router_classify
from shared.guardrails.output_guardrails import needs_human_escalation

# safety_agent lives inside the er-triage app
from safety.safety_agent import review as _safety_review


def classify(case: dict[str, Any], retrieve_similar: bool = False, k: int = 5) -> dict[str, Any]:
    """
    Run the full er-triage pipeline on one case.

    Args:
        case: must contain 'cc' (chief complaint). Other keys: vitals, hpi, arrival.
        retrieve_similar: if True, attach top-k similar past cases from Layer 1
                          via shared.retrieval.retriever.search_for_case().
        k: number of similar cases to retrieve when retrieve_similar=True.

    Returns:
        dict with all triage fields. Always serializable to JSON.
        When retrieve_similar=True, includes 'similar_cases' (list of L1 hits).
    """
    if not isinstance(case, dict) or not case.get("cc"):
        raise ValueError("case must be a dict with at least a 'cc' (chief complaint) field")

    # 1) classify
    verdict = _router_classify(case).to_dict()

    # 2) safety review (hard-rule floor)
    reviewed = _safety_review(case, verdict)

    # 3) guardrail — does this need human escalation?
    reviewed["needs_human_escalation"] = needs_human_escalation(case, reviewed)

    # 4) optional Layer 1 retrieval — past similar cases as context
    if retrieve_similar:
        try:
            from shared.retrieval.retriever import search_for_case
            hits = search_for_case(case, k=k)
            reviewed["similar_cases"] = [
                {"case_id": h["case_id"], "snippet": h["snippet"], "score": h["score"]}
                for h in hits
            ]
        except FileNotFoundError:
            reviewed["similar_cases"] = []
            reviewed["similar_cases_error"] = "Layer 1 corpus not available"

    return reviewed


if __name__ == "__main__":
    import json, sys
    if not sys.stdin.isatty():
        case = json.loads(sys.stdin.read())
    else:
        case = {
            "cc": "chest pain",
            "vitals": {"hr": 105, "rr": 22, "bp": "150/95", "spo2": 96},
            "hpi": "62yo M, substernal pressure 30 min, radiating to left arm",
            "arrival": "walk-in",
        }
    print(json.dumps(classify(case), indent=2))
