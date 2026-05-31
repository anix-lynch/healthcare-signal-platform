# 06 — Microsoft Fabric Integration (Soft Fold)

> **What this is.** ER3 is the **upstream system** producing triage decisions, drift alerts, and cohort outputs. Microsoft Fabric is the **downstream analytics platform** where those outputs feed dashboards, semantic models, and dbt transformations for clinician-facing reporting and ops.
>
> **Why "soft fold."** The Fabric work at `healthcare-da/` already exists with dbt-project, Power BI semantic model, openapi_snapshot.json, and SLA documentation. Rather than duplicating those into ER3, we wire ER3's output contracts to feed Fabric directly. One upstream, one downstream, no copy-paste.

---

## The integration shape

```
┌─────────────────────────────────────────┐       ┌─────────────────────────────────────────┐
│                  ER3                    │       │           Microsoft Fabric             │
│   (real-time triage + multi-agent)      │       │       (analytics + reporting)          │
│                                         │       │                                         │
│  Pattern outputs                        │       │  ┌──────────────────────────────────┐  │
│  ├── classify/   ESI tier               │  ───▶ │  │ Lakehouse (bronze)               │  │
│  ├── anomaly/    drift alerts           │       │  │   raw triage events              │  │
│  ├── cluster/    cohort assignments     │       │  └─────────────┬────────────────────┘  │
│  └── safety/     escalation events      │       │                │                       │
│                                         │       │  ┌─────────────▼────────────────────┐  │
│  Contracts                              │       │  │ dbt-project (silver / gold)      │  │
│  └── openapi_snapshot.json              │  ───▶ │  │   transformations + tests        │  │
│      (REST contract for downstream)     │       │  └─────────────┬────────────────────┘  │
│                                         │       │                │                       │
│  Cloud                                  │       │  ┌─────────────▼────────────────────┐  │
│  └── azure_provider.py                  │  ───▶ │  │ Power BI semantic model          │  │
│      (HIPAA-eligible region)            │       │  │   clinician + ops dashboards     │  │
└─────────────────────────────────────────┘       │  └──────────────────────────────────┘  │
                                                  │                                         │
                                                  │  ml-pipeline (Crystal Ball / LoS         │
                                                  │  regression — already prototyped)        │
                                                  └─────────────────────────────────────────┘
```

## What lives where (no duplication)

```
ASSET                                   LIVES IN                                                    ER3 RELATIONSHIP
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────
ER3 modules (7 patterns + eval)         ER3/app/                                                    OWNED
ER3 cloud adapter (Vertex/Azure/AWS)    ER3/app/cloud/                                              OWNED
Fabric dbt-project                      healthcare-da/dbt-project/                       REFERENCED
Power BI semantic model                 healthcare-da/powerbi-model/                     REFERENCED
ML pipeline (LoS prototype)             healthcare-da/ml-pipeline/                       REFERENCED
OpenAPI contract                        healthcare-da/openapi_snapshot.json              REFERENCED
SLA docs                                healthcare-da/sla.md / sla_all_roles.md          REFERENCED
SPEC (engineering proof)                healthcare-da/SPEC.md                            REFERENCED
```

## The interview pitch

```
"ER3 is the real-time triage system. The same outputs feed a Microsoft
 Fabric analytics layer downstream — dbt transforms the bronze events
 into silver/gold tables, a Power BI semantic model surfaces them to
 clinicians and ops. There's also an LoS regression prototype in the
 Fabric ml-pipeline that proves out the Crystal Ball pattern before
 it lands in ER3 prod. OpenAPI contract is auto-published from ER3
 and consumed by Fabric — no copy-paste integration."
```

That single paragraph hits:
- ⚡ SPEED (real-time triage)
- 💰 COST (single contract, no duplication)
- 🛡️ COMPLIANCE (HIPAA-eligible Azure region, audit log → App Insights)
- 🤖 INNOVATION (agent-friendly API, dbt + PBI semantic model = self-serve)
- 🌟 OUTCOME (clinician + ops dashboards as the human-facing artifact)

## Optional: Fabric as a 4th cloud provider

If a Microsoft-shop client wants Fabric as the *primary* compute (not just downstream analytics), ER3's CloudProvider adapter can take a `fabric_provider.py` implementation:

```
CAPABILITY                FABRIC-NATIVE
──────────────────────────────────────────────────────────
Embeddings                Azure OpenAI (Fabric ML workspace)
Vector store              Fabric Lakehouse + Vector index
LLM completion            Azure OpenAI via Fabric notebook
Clinical NLP              AI Language (Health) — same as Azure
PHI de-identification     AI Language PII — same as Azure
Audit log                 Fabric activity log + Purview lineage
Compute                   Spark notebooks + Data factory pipelines
```

Effectively a thin layer over `azure_provider.py` with Fabric-specific data primitives. Add when a client asks. Not required for ER3's default deployment.

---

## Cross-references

- **Fabric hub master:** `fabric-hub/SPEC.md`
- **Healthcare-DA engineering proof:** `healthcare-da/SPEC.md`
- **ER3 cloud adapter:** `app/cloud/`
