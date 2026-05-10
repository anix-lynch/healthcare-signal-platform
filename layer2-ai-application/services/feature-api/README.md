# feature-api

> **Status:** scaffold (the backend exists in Layer 1 — this is the surface)
> **Wraps:** `layer1-data-backbone/ml-pipeline/` outputs + `mart_er_triage` features
> **Consumed by:** `apps/er-triage` · `apps/ops-capacity-assistant`

---

## Purpose

Per-patient ML features served as JSON. This is what turns "AI on synthetic 12 patients" into "enterprise-aware clinical intelligence" — the live patient context Codex flagged as the categorical upgrade.

## Endpoints (planned)

```
GET  /features/{patient_id}            → all features for one patient
     ↓
     {
       "readmission_risk": 0.74,        ← from layer1 ml-pipeline
       "predicted_los_hours": 18.2,     ← from layer1 mart_er_triage
       "high_utilizer_flag": true,      ← prior 9 ER visits
       "recent_visit_summary": "...",   ← last 30-day visit history
       "elevated_troponin": true,       ← latest lab value flag
       "ER_overload_signal": 0.82       ← real-time saturation
     }

GET  /features/{patient_id}/cohort     → similar past cases for retrieval
GET  /features/_meta                   → feature freshness / SLA / schema
```

## Why this matters (the dizzy-patient example)

```
WITHOUT feature-api                    WITH feature-api
"patient dizzy → SOON"                 "patient dizzy +
                                        hemoglobin crashing +
                                        on blood thinners +
                                        bleeding admission 2 wks ago
                                        → NOW"
```

That's the difference between guideline-only RAG and enterprise-aware reasoning. feature-api is the bridge.

## Inputs (from Layer 1)

```
LAYER 1
├── ml-pipeline/                  MLflow-tracked feature computation
│   ├── readmission_risk.py        gradient boosting on EHR history
│   ├── predicted_los.py           Crystal Ball pattern, real implementation
│   └── ER_overload_predictor.py
│
└── dbt/marts/mart_er_triage      gold-table feature warehouse (silver→gold)
```

## Phase 5 implementation notes

- FastAPI server reading from BigQuery / Fabric Lakehouse / wherever Layer 1 lands
- Cached: feature freshness depends on upstream batch schedule
- SLA: P95 < 200ms on patient-features GET (cache hit)
- Schema versioned via `/features/_meta` so apps can detect upstream breaking changes
