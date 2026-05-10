# Full-System Flow

> **One story, top-to-bottom.** Three layers. Three transitions. If you read this from top to bottom in 30 seconds, you understand the system.

---

```
┌──────────────────────────────────────────────────┐
│           REAL HOSPITAL WORLD (chaos)            │
└──────────────────────────────────────────────────┘

   Legacy Systems
   - EHR / EMR
   - PDFs
   - CSV
   - billing
   - schedules
   - policies
   - SharePoint
            │
            │   "data is messy and untrustworthy"
            │
            ▼

══════════════════════════════════════════════════════════════════════
  🟦  LAYER 1  —  layer1-data-backbone/
       ROLE: INGESTION + DATA BACKBONE
══════════════════════════════════════════════════════════════════════

   Layer 1 takes:
       raw hospital chaos
           ↓
   and turns it into:
       structured trusted enterprise data

   Inside Layer 1:

       INGESTION
       - data/raw/
       - scripts/
       - FastAPI

            ↓

       WAREHOUSE / TRANSFORM
       - dbt-project/
       - staging
       - marts
       - tests

            ↓

       SEMANTIC / BI
       - Power BI
       - TMDL
       - DAX

            ↓

       ML FEATURES
       - ml-pipeline/
       - MLflow

            ↓

   OUTPUT:
       "clean, trusted enterprise data — ready for AI to consume"

══════════════════════════════════════════════════════════════════════

            │
            │   "OK, AI can now reason on real hospital context"
            │
            ▼

══════════════════════════════════════════════════════════════════════
  🟩  LAYER 2  —  layer2-ai-application/
       ROLE: AI APPLICATION LAYER
══════════════════════════════════════════════════════════════════════

   Layer 2 takes:
       trusted enterprise data (from Layer 1)
       +
       a clinical / ops / exec request
           ↓

   Inside Layer 2:

       APPS  (audience-shaped consumers)
       - apps/er-triage              clinicians
       - apps/ops-capacity-assistant ops team
       - apps/executive-dashboard    execs

            ↓

       SERVICES  (HTTP API surfaces)
       - services/rag-api            retrieval + generation
       - services/feature-api        per-patient features
       - services/analytics-api      system-state KPIs
       - services/guardrails-api     runtime safety

            ↓

       SHARED  (the 7 GenAI patterns)
       - retrieval (Rachel) · classify (Traffic Light)
       - regress (Crystal Ball) · generate (Mad Lib)
       - anomaly · cluster · rank
       + cloud adapter (Vertex / Azure / AWS)
       + memory · evaluation

            ↓

   OUTPUT:
       "AI decisions for clinicians, ops, and execs —
        NOW / SOON / WAIT triage · routing · briefings"

══════════════════════════════════════════════════════════════════════

            │
            │   "but don't let the AI go rogue"
            │
            ▼

══════════════════════════════════════════════════════════════════════
  🟥  LAYER 3  —  layer3-governance/
       ROLE: SAFETY + EVAL + GOVERNANCE
══════════════════════════════════════════════════════════════════════

   Layer 3 watches:
       AI behavior itself

   Inside Layer 3:

       INPUT SAFETY  (before AI)
       - prompt-injection detection
       - PII masking (spaCy + regex)
       - schema validation

            ↓

       OUTPUT SAFETY  (after AI)
       - hallucination checks
       - citation validation
       - forbidden actions
       - Llama Guard secondary safety

            ↓

       OFFLINE EVAL
       - Ragas faithfulness + relevancy
       - red-team adversarial suite (50 prompts)
       - drift monitoring (centroid-shift)
       - audit log review

            ↓

   OUTPUT:
       "AI is auditable, measurable, and less likely to
        cause harm or get the hospital sued"

══════════════════════════════════════════════════════════════════════
```

---

## What each transition really means

```
TRANSITION                                 WHO DOES IT          IN PRODUCTION
─────────────────────────────────────────────────────────────────────────────
chaos → Layer 1                            data engineering     batch ingest
                                                                  (dbt schedule)
Layer 1 → Layer 2                          GenAI engineering    HTTP via
                                                                  feature-api +
                                                                  analytics-api
Layer 2 → Layer 3                          AI safety eng        in-process call
                                                                  to guardrails-api
                                                                  (every LLM call)
```

No event buses. No K8s. Synchronous HTTP between layers. Async fire-and-forget for the audit log. **Boring infra by design** — see [`../docs/02_operational_realism.md`](../docs/02_operational_realism.md) for what we DO and DON'T add.

---

## When the diagram gets more complicated

This top-to-bottom view is the steady-state happy path. Two things complicate it in real operation, and they live in their own docs so this diagram stays clean:

```
COMPLICATION                              SEE
─────────────────────────────────────────────────────────────────────
ESI tier 1 escalation (red flags)         docs/05_patient_lifecycle.md §6 (decision fork)
Failure modes (LLM timeout, PII miss)     docs/05_patient_lifecycle.md §"Failure scenarios"
                                          + docs/02_operational_realism.md
Per-layer internal structure              diagrams/layer_diagrams.md
```

---

## Cross-references

- **Why three layers (the architect/junior split — interview ammo):** [`../docs/04_why_three_layers.md`](../docs/04_why_three_layers.md)
- **Per-layer detail diagrams:** [`layer_diagrams.md`](layer_diagrams.md)
- **Patient lifecycle (12 written-out steps + failure scenarios):** [`../docs/05_patient_lifecycle.md`](../docs/05_patient_lifecycle.md)
- **Why each layer exists + ownership:** [`../docs/01_layer_purpose_and_ownership.md`](../docs/01_layer_purpose_and_ownership.md)
- **What we DON'T add (no K8s, no event bus):** [`../docs/02_operational_realism.md`](../docs/02_operational_realism.md)
