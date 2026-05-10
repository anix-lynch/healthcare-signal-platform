# Layer 1 — Data Backbone

> **Where you are:** Layer 1 of the [healthcare-genai-fullstack](../README.md) 3-layer monorepo. The medallion-architecture data layer that turns raw hospital chaos into trusted enterprise data the AI app can chew on.

---

## INPUT → OUTPUT

```
INPUT                          OUTPUT
────────────────────           ────────────────────
hospital chaos                 trusted data ready to serve
- CSVs                         - bronze · silver · gold marts
- PDFs                         - ML features (MLflow)
- EHR / EMR                    - Power BI semantic model
- billing                      - OpenAPI contract
- schedules                    - 55K-row healthcare dataset
- dirty tables                 (synthetic, no real PHI)
```

**One-line deliverable:** *"data the AI and business can actually use."*

---

## What lives here

```
layer1-data-backbone/
│
├── data/raw/                       BRONZE — the chaos as-is
│   └── healthcare_dataset.csv          55,500 synthetic patient records
│
├── dbt-project/                    SILVER + GOLD
│   ├── staging/                        cleaned · deduped · PHI-redacted
│   ├── marts/
│   │   ├── mart_er_triage              per-patient features  →  apps/er-triage
│   │   ├── mart_operations             system-state KPIs     →  apps/ops-capacity
│   │   └── mart_executive_kpi          board-level rollups   →  apps/executive
│   └── tests/                          schema + data-quality tests
│
├── ml-pipeline/                    GOLD — predictive features
│   ├── readmission_risk                gradient boosting on EHR history
│   ├── predicted_los                   length-of-stay forecast
│   ├── high_utilizer_flag              prior-visit pattern detector
│   └── ER_overload_signal              real-time saturation
│   (tracked via MLflow)
│
├── powerbi-model/                  BEYOND — semantic layer
│   ├── TMDL                            table model
│   ├── DAX                             measures
│   └── KPI definitions                 board-ready definitions
│
├── api/                            BEYOND — REST surface for Layer 2
│   ├── FastAPI app
│   └── openapi.json                    agent-friendly contract
│
├── headhunter_ready/               recruiter-facing artifacts
├── screenshots/                    visual proof
├── outputs/                        dbt + ML run artifacts
├── inputs/                         API exports + Fabric profile + ML snapshot
├── scripts/                        ingest + utility scripts
├── fabric_april/                   Microsoft Fabric proof-of-work
│
└── SPEC.md                         deeper engineering spec (legacy detail)
    DASHBOARD.md                    legacy dashboard overview
    SCREENSHOTS.md                  visual evidence index
    sla.md / sla_all_roles.md       SLA bullets · claim-to-code traceability
    README.legacy.md                old standalone README (preserved for ref)
```

---

## Real numbers

```
Patient corpus:       55,500 synthetic records (8 MB CSV, in data/raw/)
                       no real PHI · clearly labeled synthetic
Marts shipped:        3 (er_triage · operations · executive_kpi)
ML features:          4 (readmission · LoS · utilizer · overload)
Semantic model:       TMDL + DAX wired through Power BI
API contract:         openapi.json published, consumed by Layer 2
                       services/feature-api + services/analytics-api
```

---

## How Layer 2 consumes Layer 1

```
Layer 1 GOLD marts
        ↓
api/openapi.json (REST contract)
        ↓
services/feature-api          →  per-patient features
                                  (consumed by er-triage + ops-capacity)
services/analytics-api        →  system-state KPIs + executive rollups
                                  (consumed by ops-capacity + executive-dashboard)
```

Layer 2 services NEVER reach into Layer 1 dbt tables directly. They go through the OpenAPI contract. That's the architect-grade separation — schema changes are versioned, breaks fail loudly, and Layer 2 doesn't care which warehouse Layer 1 actually runs on.

---

## Title → which folder do you click first

```
Data Engineer                     dbt-project/  +  data/raw/
Analytics Engineer                dbt-project/marts/
Healthcare Data Engineer          all of layer 1 (full stack)
Data Platform Engineer            api/  +  openapi.json

ML Engineer (signals only)        ml-pipeline/

BI Analyst                        powerbi-model/
```

---

## Audience · Stakeholder · KPI

**Audience:** Data Engineering · Analytics Engineering team.
**Stakeholder:** CDO · Hospital IT Director.
**KPIs:**
- schema test pass rate (dbt tests must hold 100%)
- mart freshness SLA (gold tables ≤ 24h stale)
- % PHI redacted upstream (target ≥ 99.5%)
- ml-feature freshness (per feature, MLflow-tracked)

---

## Cross-references

- **Top-level monorepo:** [`../README.md`](../README.md)
- **Mission:** [`../docs/00_mission.md`](../docs/00_mission.md)
- **Why three layers (architect/junior split):** [`../docs/04_why_three_layers.md`](../docs/04_why_three_layers.md)
- **Layer 1 detailed diagram:** [`../diagrams/layer_diagrams.md`](../diagrams/layer_diagrams.md) (medallion + mart contents + consumer apps)
- **Layer 2 (consumer of this layer):** [`../layer2-ai-application/`](../layer2-ai-application/)
- **Deeper engineering spec (legacy detail):** [`SPEC.md`](SPEC.md)
- **SLA bullets + claim-to-code traceability:** [`sla.md`](sla.md)
- **Old standalone README (pre-merge):** [`README.legacy.md`](README.legacy.md)
