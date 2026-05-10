# Layer 1 — Data Backbone

> **Where you are:** Layer 1 of the [healthcare-genai-fullstack](../README.md) 3-layer monorepo. The data layer that turns raw hospital chaos into queryable enterprise data the AI app can chew on.
>
> **Honesty note:** an audit on 2026-05-09 found the earlier README oversold. This one matches what's actually on disk. See "Honest gaps" section at bottom.

---

## INPUT → OUTPUT

```
INPUT                          OUTPUT (what's actually on disk)
────────────────────           ────────────────────
hospital data                  - 55,500-row synthetic patient CSV
- CSV (synthetic)              - dbt star schema (14 SQL files)
                               - working FastAPI on the CSV (11 endpoints)
                               - Power BI TMDL (Fabric-dependent)
                               - 1 partial ML training script (proxy target)
                               - OpenAPI 3.1.0 contract (11 paths)
```

**One-line deliverable:** *"queryable healthcare data + working API. ML side is partial."*

---

## What's actually here

```
layer1-data-backbone/
│
├── data/raw/
│   └── healthcare_dataset.csv          55,500 synthetic patient rows (8 MB)
│                                        15 columns: Name · Age · Gender · Blood Type ·
│                                        Medical Condition · Date of Admission ·
│                                        Doctor · Hospital · Insurance · Billing ·
│                                        Room · Admission Type · Discharge · Medication ·
│                                        Test Results
│                                        no real PHI · clearly labeled synthetic
│
├── api/                                ✅ WORKING FastAPI (run today)
│   ├── app/main.py                     381 lines · 11 GET endpoints
│   ├── examples.py                     6 example consumers
│   ├── test_api.py                     endpoint tester
│   └── README.md
│
├── dbt-project/                        ⚠️ CODE REAL · runtime warehouse not configured
│   ├── models/
│   │   ├── staging/stg_healthcare.sql
│   │   ├── intermediate/
│   │   │   ├── int_encounters_enriched.sql
│   │   │   └── int_readmissions.sql    (real LAG window for ≤30-day readmission flag)
│   │   └── marts/core/                 ← classic star schema (NOT mart_er_triage etc.)
│   │       ├── dim_patient.sql
│   │       ├── dim_doctor.sql
│   │       ├── dim_hospital.sql
│   │       ├── dim_insurance.sql
│   │       ├── dim_diagnosis.sql
│   │       ├── dim_medication.sql
│   │       ├── dim_date.sql
│   │       └── fact_patient_encounters.sql  (77 lines, joins all dims)
│   ├── tests/                          3 dbt assertion tests
│   │   ├── assert_valid_readmission_logic.sql
│   │   ├── assert_discharge_after_admission.sql
│   │   └── assert_no_negative_los.sql
│   ├── packages.yml                    uses dbt_utils
│   └── profiles.yml                    placeholder profile
│
├── ml-pipeline/                        ⚠️ TRAIN: real code · NEVER PERSISTED
│   ├── src/train.py                    153 lines · XGBoost + sklearn + MLflow
│   │                                    → target is a PROXY (Test Results==Abnormal),
│   │                                      not real readmission ground truth
│   │                                    → no saved artifact in repo (no .pkl, no mlruns/)
│   ├── src/score.py                    ❌ MOSTLY COMMENTED OUT — hardcoded dummy
│   │                                      output ("1,0.85\n2,0.12\n"). Placeholder.
│   └── requirements.txt
│
├── powerbi-model/                      ⚠️ TMDL real · needs Fabric workspace
│   ├── model.tmdl                      compatibilityLevel 1567, Power BI v3
│   ├── relationships.tmdl              4 relationships defined
│   └── tables/                         5 tables (Date · Patient · Hospital · Doctor ·
│                                        'Patient Encounters')
│                                        sources from env.FABRIC_SERVER + env.FABRIC_DATABASE
│
├── openapi_snapshot.json               ✅ valid OAS 3.1.0 · 11 paths · matches main.py
│
├── headhunter_ready/                   recruiter-facing artifacts (markdown)
├── screenshots/                        visual proof (markdown index in SCREENSHOTS.md)
├── outputs/                            mostly markdown "proof" docs · 1 historical
│                                        dbt_run_results JSON (8 KB, dated)
├── inputs/                             API export contexts + ML training snapshot
│                                        (NB: training snapshot files are 0 bytes —
│                                         placeholders, not actual data)
├── scripts/                            13 utility scripts (proof rendering, etc.)
├── fabric_april/                        Microsoft Fabric proof-of-work (markdown)
│
└── SPEC.md                             deeper engineering spec (legacy detail)
    DASHBOARD.md / SCREENSHOTS.md       legacy overview docs
    sla.md / sla_all_roles.md           SLA bullets · claim-to-code traceability
    README.legacy.md                    pre-monorepo standalone README (preserved)
```

---

## What works today (try it yourself)

```
WORKS:
   cd api/
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   curl http://localhost:8000/api/stats
   open http://localhost:8000/docs              ← interactive OpenAPI docs

DOES NOT WORK without external setup:
   dbt run                                       ← needs target warehouse configured
                                                   (profiles.yml is placeholder)
   Power BI refresh                              ← needs FABRIC_SERVER + FABRIC_DATABASE
                                                   env vars + a live Fabric workspace
   python ml-pipeline/src/train.py               ← will train, but never persisted
                                                   to a registered model store
   python ml-pipeline/src/score.py               ← prints dummy "1,0.85" hardcoded
```

---

## ⚠️ Honest gaps (audited 2026-05-09)

The earlier version of this README claimed things that don't match the code on disk. This list is the difference.

```
CLAIM (in earlier docs)              REALITY ON DISK
──────────────────────────────────────────────────────────────────────────
3 audience-shaped marts              ❌ NOT BY THOSE NAMES
(mart_er_triage / mart_operations /     The actual SQL is a classic STAR SCHEMA:
 mart_executive_kpi)                    7 dim_*.sql + 1 fact_patient_encounters.sql
                                        (not "mart per audience" — that was vibes)

4 ML features                        ❌ ONLY 1 HAS CODE
(readmission · LoS · utilizer ·         readmission_risk: real XGBoost code,
 ER_overload)                           proxy target (Test Results), never persisted
                                        predicted_los: ZERO code (computed in API
                                          as discharge - admission subtraction —
                                          arithmetic, not ML)
                                        high_utilizer_flag: ZERO code anywhere
                                        ER_overload_signal: ZERO code anywhere

ML inference pipeline                ❌ score.py is a PLACEHOLDER
                                        (hardcoded dummy CSV output, 30 lines
                                         all commented out)

PHI handling at Layer 1              ❌ NO CODE
                                        Single grep hit is a markdown comment about
                                        screenshots. No de-id module exists in Layer 1.

Monitoring at Layer 1                ❌ NO CODE
                                        No metrics, no alerting, no drift checks at
                                        the data-pipeline level.
                                        (Layer 3 has eval+redteam at AI-output level,
                                         not data-pipeline level — different concern.)
```

**What this means in interview:**
- ✅ defensible: the API, the dbt SQL star schema, the Power BI TMDL structure, the readmission training code (with proxy-target caveat)
- ⚠️ partial: dbt has only run once historically; Power BI needs Fabric to refresh
- ❌ undefendable until built: predicted_los model, high_utilizer model, ER_overload model, real PHI redaction, data-pipeline monitoring

The honest sentence: *"the data-side fundamentals are real (API, star schema, TMDL); the ML side is one trained-but-not-persisted model with a proxy target. The other 3 ML features are queued."*

---

## Real numbers

```
Patient corpus           55,500 synthetic records (8.4 MB CSV)
                         15 columns · synthetic · clearly labeled · no real PHI
API endpoints            11 GET routes · OpenAPI 3.1.0 · loads CSV at boot
dbt models               14 SQL files (1 staging · 2 intermediate · 8 dim · 1 fact ·
                         3 tests)
ML training code         1 script (153 lines) · XGBoost + sklearn + MLflow imports
                         Target = proxy (engineered from Test Results column)
ML scoring code          ❌ placeholder (dummy hardcoded output)
Power BI tables          5 (Date · Patient · Hospital · Doctor · Patient Encounters)
                         + 4 relationships
```

---

## Title → which folder do you click first

```
Data Engineer                     api/  +  data/raw/
Analytics Engineer                dbt-project/models/
Healthcare Data Engineer          all of layer 1 (api + dbt + powerbi)
Data Platform Engineer            api/  +  openapi_snapshot.json

ML Engineer (real one)            ml-pipeline/src/train.py — but flag it:
                                    proxy target, never persisted

BI Analyst                        powerbi-model/  (note: needs Fabric to render)
```

---

## Audience · Stakeholder · KPI

**Audience:** Data Engineering · Analytics Engineering team.
**Stakeholder:** CDO · Hospital IT Director.
**KPIs (today):** API uptime · OpenAPI contract validity · dbt SQL test pass-rate (when run).
**KPIs (queued):** mart freshness SLA · ML feature freshness · PHI redaction rate (no code yet).

---

## Cross-references

- **Top-level monorepo:** [`../README.md`](../README.md)
- **Mission:** [`../docs/00_mission.md`](../docs/00_mission.md)
- **Why three layers:** [`../docs/04_why_three_layers.md`](../docs/04_why_three_layers.md)
- **Layer 1 detailed diagram:** [`../diagrams/layer_diagrams.md`](../diagrams/layer_diagrams.md)
- **Implementation phases (incl. queued ML features):** [`../docs/03_implementation_phases.md`](../docs/03_implementation_phases.md)
- **Layer 2 (downstream consumer):** [`../layer2-ai-application/`](../layer2-ai-application/)
- **Deeper engineering spec:** [`SPEC.md`](SPEC.md)
- **SLA + claim-to-code traceability:** [`sla.md`](sla.md)
- **Old standalone README:** [`README.legacy.md`](README.legacy.md)
