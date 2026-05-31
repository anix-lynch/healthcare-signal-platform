# Pattern 2 — classifier 🚦

> **"how urgently should we panic 😭"**

This is classification. NOT retrieval (that's retrieval). NOT regression
(that's forecast). NOT generation (that's generation).

classifier answers ONE question:

```
"which suffering cuts the line first?"
```

Output is a discrete bucket (NOW / SOON / WAIT) + ESI 1-5 + an
escalation flag. The charge nurse can act on this without reading a
single sentence of LLM prose.

---

## Why it sits here

Two layers consume classifier:

```
apps/er-triage              → drives the NOW/SOON/WAIT UI + escalation page
apps/er-triage/safety       → applies hard-rules (ESI 1 always escalates)
services/rag-api            → wraps classifier as /v1/classify-tier
shared/generate   → consumes tier as context when grounding a note
```

Four callers, one engine. That's why classifier lives in `shared/`.

(Note: the `cost_router.py` in this same folder is a DIFFERENT classifier
— it picks WHICH MODEL TIER (Haiku/Flash/Sonnet) to call. Same shared/classify
folder by accident of naming. Don't confuse them. Different concerns.)

---

## File map

```
shared/classify/
├── __init__.py        public API (triage, TrafficLightOutput)
├── schema.py          Pydantic output contract
├── baseline.py        rules-based orchestrator → TrafficLightOutput
├── router.py          rule-based ESI scoring engine (existing, working)
├── cost_router.py     3-tier model selector (DIFFERENT pattern, lives here for now)
├── leakage_checks.py  "answer-key cheat" guard (esi_tier_truth in features = nope)
├── eval.py            per-class F1 + confusion + down-triage-rate + calibration
└── README.md          you are here

apps/er-triage/classify/   ← app-side, uses shared/classify under the hood
├── esi_classifier.py  LLM-as-classifier wrapper (3.3 KB)
└── prompts.py         clinical rubric prompts
```

---

## What's shipped vs what's stub

```
COMPONENT                     STATUS         NOTES
─────────────────────────────────────────────────────────────────────────────
Rule-based ESI scoring        ✅ shipped     vitals + age + keyword + escalation
LLM-as-classifier (app-side)  ✅ shipped     Pydantic structured output
3-tier cost router            ✅ shipped     picks Haiku/Flash/Sonnet
schema (TrafficLightOutput)   ✅ shipped     matches /v1/classify-tier shape
leakage_checks                ✅ shipped     blocks esi_tier_truth in features
per-class metrics + confusion ✅ shipped     F1 / precision / recall per tier
down-triage rate metric       ✅ shipped     the kill-people metric
calibration buckets           ✅ shipped     conf ↔ accuracy alignment
LLM ↔ rules unified call      ⚠️ partial     baseline.py wraps rules only;
                                              LLM merge point queued
trained tabular classifier    ❌ queued      LightGBM scaffold when data lands
```

---

## The brutal mantra

```
ESI 1 = "they will die now if you don't move"      RESUSCITATION
ESI 2 = "they will die soon if you don't move"     EMERGENT
ESI 3 = "stable but multiple resources needed"     URGENT
ESI 4 = "stable, one resource"                     LESS-URGENT
ESI 5 = "stable, zero resources"                   NON-URGENT

down-triage ESI 2 → ESI 3   =   bed wait + worse outcome
down-triage ESI 1 → ESI 2   =   lawsuit + headlines
up-triage ESI 4 → ESI 2     =   wasted bed, no harm

asymmetric harm.  down-triage rate is the metric we publish.
```

---

## Why classification ≠ retrieval (the line that gets confused)

```
TRAFFIC LIGHT (classify)        RACHEL (retrieval)
output: discrete bucket          output: list of items
"how urgent?"                    "what reminds me of this?"
metric: per-class F1             metric: Recall@K, NDCG
                                 
failure: misroutes ESI 1→3       failure: returns irrelevant cases
        = harm                    = chart-note hallucinates

Together (the lifecycle):
  retrieval:        "this smells like past cardiac near-death ghosts"
  classifier: "cool, then NOW — move 😭"
```

---

## Healthcare meaning

```
CASE                                       TRAFFIC LIGHT OUTPUT
────────────────────────────────────────   ──────────────────────────────────
62yo M, chest pain, ambulance, BP 95/60    tier: NOW · esi: 2 · escalate: true
                                            red_flags: chest_pain, diaphoresis,
                                                        hypotension, jaw_radiation
                                            confidence: 0.91
                                            reason: "High-risk chest pain syndrome"

22yo F, sprained ankle, walk-in            tier: WAIT · esi: 4 · escalate: false
                                            red_flags: []
                                            confidence: 0.88

7-month-old, fever 39.5°, parent rushed in tier: NOW · esi: 1 · escalate: true
                                            red_flags: pediatric_under_1y, fever
                                            human_review_required: true
                                            (pediatric < 1y = always escalate)
```

---

## Senior architect during hospital chaos — the tone we keep

```
BAD                              GOOD
─────────────────────────────    ─────────────────────────────────────────
"prob a 2 ig"                    "ESI 2, confidence 0.87, red flags:
                                   [chest_pain, hypotension, diaphoresis]"
"could be NOW could be SOON"     "tier: NOW. rule fired: vital instability."
                                  "human_review_required: true (confidence < 0.85)"
"feels like ESI 3"              "ESI 3, confidence 0.78, no red flags fired,
                                   borderline — within ±1 of truth in eval"
```

The tier can be wrong. The framing cannot.

---

## Quick start

```python
from shared.classify import triage

case = {
    "cc": "chest pain",
    "hpi": "62yo M with substernal pressure 30 min, diaphoresis, jaw radiation",
    "arrival": "ambulance",
    "vitals": {"bp_sys": 95, "hr": 122, "rr": 24, "spo2": 92, "temp_f": 99.1},
}
out = triage(case, case_id="CASE-104")
print(out.model_dump_json(indent=2))
```

Output (truncated):

```json
{
  "pattern": "traffic_light_classification",
  "case_id": "CASE-104",
  "tier": "NOW",
  "esi_tier": 2,
  "confidence": 0.91,
  "reason": "High-risk chest pain syndrome — vital instability + jaw radiation",
  "red_flags": ["chest_pain", "diaphoresis", "hypotension", "jaw_radiation"],
  "escalate": true,
  "human_review_required": true,
  "method": "rules_fallback",
  "fallback_used": false,
  "model_tier_used": "rules",
  "cost_usd": 0.0,
  "warnings": []
}
```

---

## Eval

```python
from shared.classify.eval import report

y_true = [1, 2, 3, 3, 4, 5]
y_pred = [2, 2, 3, 4, 4, 5]
y_conf = [0.55, 0.91, 0.88, 0.65, 0.80, 0.92]

print(report(y_true, y_pred, y_conf=y_conf))
# {
#   "exact_match": 0.6667,
#   "within_one_tier": 1.0,
#   "down_triage_rate": 0.3333,   ← ALERT if > 0.05
#   "up_triage_rate": 0.0,
#   "per_class": {1: {...}, 2: {...}, ...},
#   "confusion_matrix": {"1->2": 1, "2->2": 1, ...},
#   "calibration": [...]
# }
```

---

## Roadmap

```
NOW (registry_v1)              rules-based router on demographics + condition
                               warnings = "no real vitals in current data"
                               down-triage rate guard at 0.05

NEXT (registry_v2_enriched)    LLM-as-classifier reading CC + vitals + HPI
                               calibrate confidence on holdout
                               trained LightGBM as third path

REAL (real EHR)                ensemble of rules + LLM + LightGBM
                               human-in-the-loop on confidence < 0.85
                               down-triage rate target < 0.02 (audited)
```

---

## Cross-references

- 7-pattern map: `../../../README.md`
- Sibling patterns: `../retrieval/`, `../regress/`
- App that consumes classifier: `../../apps/er-triage/`
