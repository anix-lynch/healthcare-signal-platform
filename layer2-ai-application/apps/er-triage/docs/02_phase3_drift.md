# Phase 3 — Drift Monitor + Anomaly Flagger

> **Concept source:** `mj/docs/05_smoke_detector.md`

## Two complementary functions

```
DRIFT MONITOR (population-level)
└── monthly centroid of incoming cases vs baseline
    cosine(c_baseline, c_current) < 0.92 → ALERT

ANOMALY FLAGGER (per-case)
└── distance from nearest cluster centroid > 4σ → flag
    cheap LLM judge explains "why weird" on flagged subset
```

## Drift monitor algorithm

1. Establish **baseline** = centroid of last 30 days of case embeddings
2. Each week: compute current 7-day centroid
3. Compute `cosine_similarity(baseline, current)`
4. If < 0.92 → log alert + notify (Discord webhook)
5. Update baseline monthly (rolling window)

## Anomaly flagger algorithm

1. For each new case, embed → vector v
2. Find nearest cluster centroid (use ER2's existing clustering OR k=5 ad-hoc)
3. Compute distance `d = ||v - centroid||`
4. If `d > μ + 4σ` of in-cluster distances → flag
5. Cheap LLM judge: "Is this case genuinely an ER triage case? Reason?"

## Alert sinks

- v0.1: stdout (logs visible in Cloud Run console)
- v0.2: Discord webhook to private channel
- v0.3: Email digest (weekly summary)

## What counts as "alertable" drift

| Pattern | Alert? |
|---|---|
| Sudden flu-season spike | yes (cohort change) |
| New hospital onboarded → mix shifts | yes (one-time, then re-baseline) |
| Single weekend of unusual cases | no (sample size too small) |
| Embedding model upgrade | yes (re-baseline immediately) |

## Failure modes to test

- Tiny daily sample sizes → smoothed across rolling window, no false alerts
- Identical embeddings (no drift) → must NOT alert (regression test)
- 30% perturbed embeddings (synthetic drift) → MUST alert (regression test)
