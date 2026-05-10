# executive-dashboard

> **Audience:** CEO · COO · hospital leadership
> **Status:** soft fold — primary surface lives in `layer1-data-backbone/powerbi-model/`
> **Output:** KPI dashboard + LLM-narrative summary

---

## Purpose

Executive-level visibility into hospital performance. Most of the dashboard is a Power BI surface owned by Layer 1. This app adds the **LLM-narrative layer** that turns dashboards into briefings.

```
Power BI (Layer 1)         →  visual KPIs · trends · drill-down
   │
   ▼
LLM-narrative (this app)   →  weekly board summary · anomaly explanation ·
                              forward-looking commentary
```

## Inputs

```
LAYER 1 — DATA BACKBONE
├── powerbi-model/                semantic model (TMDL + DAX)
└── mart_executive_kpi            pre-aggregated KPI marts

LAYER 2 — SHARED LIBS
├── shared/generate               LLM narrative generation (Mad Lib pattern)
├── shared/anomaly                detect KPI shifts worth flagging
└── shared/cloud                  multi-cloud LLM access

LAYER 2 — SERVICES
└── services/analytics-api        consume KPI marts as JSON
```

## Output

```
WEEKLY EXECUTIVE BRIEFING (auto-generated, human-edited):

  ER throughput up 12% week-over-week (driver: weekend staffing redeployment).
  LoS averaged 4.2h, down 0.3h from prior week.
  Bed utilization peaked Sat night at 96% — flagged but no overflow incidents.
  Readmission rate held at 8.4%. No regression alerts fired.

  Forward-looking: capacity model projects 4% increase in low-acuity volume next
  week (school break onset). Ops team has been prompted to add 2 triage RNs to
  evening shift Wednesday-Friday.
```

## Why this app exists (not just "Power BI")

Power BI shows what happened. **The narrative layer says what it means and what to do about it** — that's the difference between a dashboard and a briefing. Execs read briefings; they only open dashboards if the briefing flags something.

KPI for this app: % of weekly briefings exec actually opens (target: 100%).

## Phase 5 implementation notes

- Streamlit app or PDF generator
- Reads from `services/analytics-api`
- Uses `shared/generate` for the LLM-narrative composition
- Uses `shared/anomaly` to surface week-over-week movers worth narrating
- HITL: every briefing reviewed by ops lead before sending to exec

Stub for now.
