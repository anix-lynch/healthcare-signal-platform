# ops-capacity-assistant

> **Audience:** hospital operations team
> **Status:** scaffold — implementation queued
> **Output:** ER utilization · bed pressure · staffing recommendations · overflow routing

---

## Purpose

When ER triage classifies a patient as **lower acuity** (yellow / green), this assistant decides hospital flow:

```
high acuity (red)        → immediate ER care (handled by er-triage)
lower acuity (yellow/green)  → ops-capacity-assistant decides routing
                                ├── ER overflow ward
                                ├── observation unit
                                ├── direct admission
                                └── discharge with follow-up
```

## Inputs (consumed from layer 1 + shared/)

```
LAYER 1 — DATA BACKBONE
├── mart_operations              utilization · bed pressure · staffing
└── ml-features
    ├── predicted_los            length-of-stay forecast per case
    ├── high_utilizer_flag       repeat-visit pattern
    └── ER overload prediction   real-time saturation signal

LAYER 2 — SHARED LIBS
├── shared/cluster               cohort assignment for routing decision
├── shared/regress               LoS prediction wrapper
└── shared/cloud                 multi-cloud LLM access (via CloudProvider)

LAYER 2 — SERVICES (downstream consumers)
├── services/feature-api         pulls ml-feature signals
└── services/analytics-api       pulls operational KPIs
```

## Output

Recommendation per patient + system-level capacity dashboard:

```python
class CapacityDecision(BaseModel):
    patient_id: str
    routing: Literal["ER_overflow", "observation", "admission", "discharge_followup"]
    confidence: float
    los_estimate_hours: float
    reasoning: str
```

## Why this app exists (not just "more ER")

ER triage answers *"how urgent is this patient?"*
ops-capacity-assistant answers *"given the urgency mix and current hospital state, where should this patient go to optimize flow without compromising care?"*

Different question. Different audience. Different KPI:
- ER triage KPI: time-to-treatment for red cases
- ops-capacity KPI: bed turnover · ER throughput · staffing utilization

## Phase 5 implementation notes

- FastAPI app at `apps/ops-capacity-assistant/app.py`
- Consumes `services/feature-api` for per-patient signals
- Consumes `services/analytics-api` for system-state context
- Uses `shared/cluster` for routing-cohort decisions
- Uses `shared/cloud` for LLM-narrative summaries to ops staff
- Output: routing decision + dashboard tile feed

Stub for now — actual implementation is scheduled work, not blocked on architecture.
