# analytics-api

> **Status:** scaffold
> **Wraps:** `layer1-data-backbone/powerbi-model/` semantic layer + `mart_executive_kpi` + `mart_operations`
> **Consumed by:** `apps/executive-dashboard` · `apps/ops-capacity-assistant`

---

## Purpose

Operational and executive KPIs as JSON. Apps that need *system-state* signals (not per-patient) come here.

## Endpoints (planned)

```
GET  /metrics/{name}                    → single KPI value + trend
     ?window=7d|30d|qtr                 (e.g. avg_los, bed_utilization)

GET  /dashboard/{audience}              → bundle of KPIs for one audience
     audience: ops|executive             (replaces N round-trips with 1)

GET  /trends/{metric}                   → time-series for charting
     ?from=...&to=...&granularity=day|week

GET  /alerts                            → currently-firing KPI threshold alerts
```

## KPIs served

```
OPS (consumed by ops-capacity-assistant):
   ├── ER_utilization_pct
   ├── bed_pressure_score
   ├── staffing_pressure_index
   ├── ER_saturation_trend
   ├── overflow_routing_recommendations
   └── avg_wait_to_treatment

EXECUTIVE (consumed by executive-dashboard):
   ├── avg_length_of_stay
   ├── readmission_rate_30d
   ├── ER_throughput_weekly
   ├── financial_kpi (placeholder — finance scope deferred)
   └── ops_efficiency_index
```

## Why this is a separate service from feature-api

```
feature-api      = PER-PATIENT signals
                   "tell me about patient #12345 specifically"

analytics-api    = SYSTEM-STATE signals
                   "tell me what's happening across the hospital right now"
```

Different update cadence (per-patient = real-time-ish; system-state = batch). Different access patterns (per-patient = lookup; system-state = aggregation). Different authz (per-patient = clinical role; system-state = ops/exec role).

## Phase 5 implementation notes

- FastAPI server, data from `layer1-data-backbone/dbt/marts/` and Power BI XMLA
- Heavy caching — system-state metrics don't change every second
- Audience-scoped auth: ops vs exec see different KPI sets
- Alerts wired to drift monitor in `shared/anomaly`
