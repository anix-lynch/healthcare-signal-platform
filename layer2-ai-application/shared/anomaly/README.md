# Pattern 5 — Smoke Detector 🚨

> **"this case smells WRONG 😭"**

Per-case anomaly + corpus-level drift. The "Llama Guard" of clinical
plausibility — flags cases the rest of the stack should slow down on.

## File map

```
shared/anomaly/
├── __init__.py            public API (detect_smoke, SmokeDetectorOutput, compute_drift)
├── schema.py              Pydantic output contract
├── baseline.py            wraps anomaly_flagger.flag() → SmokeDetectorOutput
├── anomaly_flagger.py     per-case rule + cohort z-score engine (existing)
├── drift.py               offline centroid-shift drift detection (existing)
└── README.md              you are here
```

## What's shipped

```
per-case outlier flag         ✅ shipped
cohort z-score reasoning      ✅ shipped (BP/HR/T/SpO2 vs condition cohort)
threshold knob                ✅ shipped (DEFAULT_THRESHOLD=2.5, sweep-able)
drift detection (offline)     ✅ shipped (centroid-shift between snapshots)
LOF / isolation forest        ❌ queued
calibration on holdout        ❌ queued (use enriched_holdout_100.jsonl)
```

## The brutal mantra

```
rule alone    = "yo this BP is 60/30, that's bad"
stats alone   = "z-score 3.2, ergo anomalous"
ensemble      = "z-score 3.2 + 3 known red flags + same direction
                  in cohort centroid distance"

production smoke detector = ensemble + calibrated threshold + drift
current state             = rule + stats, threshold = 2.5 default
```

## Together with the other patterns

```
Rachel: "this smells like sepsis ghosts"
Traffic Light: "ESI 2, escalate"
Crystal Ball: "LoS 6d ±2, readm 0.42"
Smoke Detector: "wait — anomaly_score 3.8, 4 reasons fired,
                  this case is in the corner of the cohort space"
                → human review required
```

Without Smoke Detector, the system happily classifies + retrieves on weird
inputs that should have stopped it. The lawyer's favorite slide.

## Quick start

```python
from shared.anomaly import detect_smoke

case = {
    "cc": "abdominal pain",
    "hpi": "47yo F, sudden severe LLQ pain, 30 min",
    "vitals": {"bp_sys": 78, "hr": 132, "rr": 28, "spo2": 91, "temp_f": 100.2},
}
out = detect_smoke(case, case_id="CASE-104")
print(out.model_dump_json(indent=2))
```
