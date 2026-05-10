# Per-Layer Diagrams

> **Three diagrams, one per layer.** Each shows the layer's internal structure + what it sends to / receives from neighboring layers.

---

## 🟦 Layer 1 — Data Backbone (medallion architecture)

```
                    ╔════════════════════════════════════════════════════╗
                    ║              SOURCE SYSTEMS (the chaos)            ║
                    ╠════════════════════════════════════════════════════╣
                    ║  EHR · EMR · billing · scheduling · PDFs · CSVs    ║
                    ║  · SharePoint · device telemetry                    ║
                    ╚═══════════════════════╤════════════════════════════╝
                                            │  raw extract
                                            ▼
              ┌─────────────────────────────────────────────────────────┐
              │           BRONZE — data/raw/                            │
              │  raw rows, native types, no cleaning                    │
              │  audit trail: source · ingest_ts · row_hash             │
              │  (immutable)                                            │
              └─────────────────────────────────────────────────────────┘
                                            │ dbt staging
                                            ▼
              ┌─────────────────────────────────────────────────────────┐
              │           SILVER — dbt-project/staging/                 │
              │  cleaned · deduped · conformed · PHI-redacted           │
              │  schema-tested (dbt tests: not_null, unique, accepted)  │
              └─────────────────────────────────────────────────────────┘
                                            │ dbt marts
                                            ▼
              ┌─────────────────────────────────────────────────────────┐
              │           GOLD — dbt-project/marts/                     │
              │  ├── mart_er_triage          per-patient features       │
              │  ├── mart_operations         system-state KPIs          │
              │  └── mart_executive_kpi      board-level rollups        │
              └─────────────────────────────────────────────────────────┘
                                            │
                            ┌───────────────┴────────────────┐
                            │                                 │
                            ▼                                 ▼
              ┌──────────────────────────┐      ┌──────────────────────────────┐
              │   ML-FEATURES            │      │   SEMANTIC MODEL              │
              │   ml-pipeline/           │      │   powerbi-model/              │
              │   ├── readmission_risk   │      │   ├── TMDL (table model)      │
              │   ├── predicted_los      │      │   ├── DAX measures            │
              │   ├── high_utilizer_flag │      │   └── KPI definitions         │
              │   └── ER_overload_signal │      │                                │
              │   tracked: MLflow        │      │   serves: Power BI dashboards │
              └──────────────┬───────────┘      └─────────────┬────────────────┘
                             │                                 │
                             │       ┌─────────────────────────┘
                             ▼       ▼
              ┌─────────────────────────────────────────────────────────┐
              │         OpenAPI CONTRACT — api/openapi.json             │
              │  agent-friendly REST surface; consumed by Layer 2       │
              │  services/feature-api + services/analytics-api          │
              └─────────────────────────────────────────────────────────┘
                                            │  HTTP
                                            ▼
                           (Layer 2 services consume from here)
```

**Audience:** Data Engineering · Analytics Engineering team.
**Stakeholder:** CDO · Hospital IT Director.
**KPI:** schema test pass rate · mart freshness SLA · % PHI redacted upstream.

---

## 🟩 Layer 2 — AI Application (lean apps + services + shared)

```
                    ┌─────────────────────────┐
                    │  PATIENT INTAKE EVENT   │
                    └────────────┬────────────┘
                                 │
              ╔══════════════════▼══════════════════════════════════════╗
              ║                  apps/ (audience-shaped)                ║
              ╠═════════════════════════════════════════════════════════╣
              ║  apps/er-triage           clinicians, NOW/SOON/WAIT     ║
              ║  apps/ops-capacity        ops team, routing decisions   ║
              ║  apps/executive-dashboard execs, briefings + KPI roll  ║
              ╚══════════════════╤══════════════════════════════════════╝
                                 │
                                 │  apps consume services via HTTP
                                 ▼
              ╔═════════════════════════════════════════════════════════╗
              ║                services/ (HTTP API surfaces)            ║
              ╠═════════════════════════════════════════════════════════╣
              ║                                                         ║
              ║   services/rag-api                                      ║
              ║      └── /v1/search · /v1/generate · /v1/eval           ║
              ║                                                         ║
              ║   services/guardrails-api                               ║
              ║      └── /v1/sanitize · /v1/validate · /v1/classify-   ║
              ║          safety                                          ║
              ║                                                         ║
              ║   services/feature-api    ──→  Layer 1 ml-pipeline      ║
              ║      └── /v1/features/{patient_id}                      ║
              ║                                                         ║
              ║   services/analytics-api  ──→  Layer 1 marts +          ║
              ║      └── /v1/metrics/{name}     powerbi-model            ║
              ║                                                         ║
              ╚══════════════════╤══════════════════════════════════════╝
                                 │
                                 │  services depend on shared/ libs
                                 ▼
              ╔═════════════════════════════════════════════════════════╗
              ║              shared/ (the 7 GenAI patterns)             ║
              ╠═════════════════════════════════════════════════════════╣
              ║  retrieval (Rachel)         classify (Traffic Light)    ║
              ║  regress (Crystal Ball)     generate (Mad Lib)          ║
              ║  anomaly (Smoke Detector)   cluster (Treasure Map)      ║
              ║  rank (Police Lineup)                                   ║
              ║                                                         ║
              ║  + cross-cutting: guardrails · memory · cloud (Vertex/  ║
              ║    Azure/AWS adapter) · evaluation                      ║
              ╚═════════════════════════════════════════════════════════╝
```

**Audience:** GenAI Engineering · FDE · AI Platform.
**Stakeholder:** ER Director · Ops Manager · Hospital CEO.
**KPI:** triage decision quality · time-to-decision · cost per inference.

---

## 🟥 Layer 3 — Governance (the safety net)

```
              ╔═════════════════════════════════════════════════════════╗
              ║         RUNTIME LAYER (called by every LLM call)        ║
              ╠═════════════════════════════════════════════════════════╣
              ║                                                         ║
              ║   BEFORE AI                                             ║
              ║   ├── input sanitize          (ASCII norm, control chr) ║
              ║   ├── strip prompt-injection  (regex + classifier)      ║
              ║   ├── redact PII              (spaCy NER + regex)       ║
              ║   ├── token-limit             (truncate or refuse)      ║
              ║   └── schema validate         (Pydantic on input)       ║
              ║                                                         ║
              ║   DURING AI                                             ║
              ║   ├── constrained generation  (Pydantic out, JSON mode) ║
              ║   ├── tool-use rules          (which tools allowed)     ║
              ║   └── temperature / top-p caps                          ║
              ║                                                         ║
              ║   AFTER AI                                              ║
              ║   ├── hallucination check     (LLM-judge, claim<->src)  ║
              ║   ├── citation validation     (every cite resolves)     ║
              ║   ├── forbidden actions       (medical-domain rules)    ║
              ║   ├── illegal advice filter   (controlled substances)   ║
              ║   ├── confidence calibration  (stated vs evidence gap)  ║
              ║   ├── schema validation       (Pydantic on output)      ║
              ║   ├── Llama Guard secondary   (S1-S14 taxonomy)         ║
              ║   └── human escalation rules  (tier 1 / pediatric / SI) ║
              ║                                                         ║
              ╚═════════════════════════════════════════════════════════╝
                                            │
                                            ▼
              ╔═════════════════════════════════════════════════════════╗
              ║         OFFLINE LAYER (eval + red-team + audit)         ║
              ╠═════════════════════════════════════════════════════════╣
              ║                                                         ║
              ║   Ragas eval                  faithfulness · relevancy  ║
              ║   ├── 50-Q&A golden set       · context recall          ║
              ║   ├── re-run weekly           regression gate on PR     ║
              ║   └── baseline JSON           outputs/ragas_baseline    ║
              ║                                                         ║
              ║   Red-team suite              50 prompts, 5 categories  ║
              ║   ├── PII extraction          100% block baseline       ║
              ║   ├── prompt injection        regression gate on PR     ║
              ║   ├── jailbreak               (must NOT regress)        ║
              ║   ├── prompt leak                                       ║
              ║   └── goal hijack                                       ║
              ║                                                         ║
              ║   Drift monitor               weekly centroid-shift     ║
              ║   ├── alert > 1σ              page on-call              ║
              ║   └── banner on triage UI     until cleared             ║
              ║                                                         ║
              ║   Audit log review            structured JSON per call  ║
              ║   ├── 7-year retention        HIPAA requirement         ║
              ║   ├── per-CloudProvider sink  (Cloud Logging / App     ║
              ║   │                            Insights / CloudWatch)   ║
              ║   └── regulator queries       can answer "show me all  ║
              ║                                triage decisions for     ║
              ║                                patient X in May 2026"   ║
              ║                                                         ║
              ╚═════════════════════════════════════════════════════════╝
```

**Audience:** AI Safety Engineering · Compliance · Legal.
**Stakeholder:** General Counsel · CISO · Compliance Officer.
**KPI:** red-team block rate · drift alert frequency · audit query pass rate.

---

## Cross-references

- **End-to-end flow combining all three layers:** [`full_system_flow.md`](full_system_flow.md)
- **Patient lifecycle written-out:** [`../flows/patient_lifecycle.md`](../flows/patient_lifecycle.md)
- **Why each layer exists + ownership:** [`../docs/01_layer_purpose_and_ownership.md`](../docs/01_layer_purpose_and_ownership.md)
