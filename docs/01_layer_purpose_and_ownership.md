# 01 — Why Each Layer Exists, Who Owns It, Who Hires For It

> **The orienting doc.** If a recruiter or interviewer reads only ONE doc in this repo, this is it. It answers: what does this system do, why does it have three layers, who owns what, and which role should look at which folder.

---

## The mission (the only thing that merges these layers)

> *Clinical AI that saves lives without getting the hospital sued.*

Every layer answers a different stakeholder's anxiety:

```
LAYER 1 — DATA BACKBONE        "Can I trust the data the AI is reasoning over?"
                                Stakeholder: Chief Data Officer · Hospital IT Director
                                Without this layer: AI hallucinates because input is garbage.

LAYER 2 — AI APPLICATION       "Can I get a useful clinical answer fast enough to act?"
                                Stakeholder: ER Director · Ops Manager · CEO
                                Without this layer: data sits unused in dashboards.

LAYER 3 — GOVERNANCE           "Can I prove the AI didn't cause harm if audited?"
                                Stakeholder: General Counsel · CISO · Compliance Officer
                                Without this layer: AI use is a legal liability.
```

A real enterprise AI system has all three. Most demo projects only have one (usually layer 2). That gap is what this repo fills visibly.

---

## Audience mapping (who consumes each layer)

```
LAYER 1                                         LAYER 2                                LAYER 3
data backbone                                   AI application                         governance
─────────────────                               ─────────────────                      ──────────────────
Stewards of source-of-truth.                    Builders of the patient-facing         Independent inspectors.
Data engineers, analytics                       reasoning layer. GenAI engineers,      Platform engineers, AI safety
engineers, data platform team.                  forward-deployed engineers.            officers, compliance team.

Outputs:                                        Outputs:                               Outputs:
- bronze/silver/gold marts                      - clinician-facing triage                - eval baselines (Ragas, etc.)
- ML feature store                              - ops routing dashboards                 - red-team test corpus
- semantic models (Power BI)                    - executive narratives                   - PHI redaction logs
- OpenAPI contracts                             - cross-cloud deployments                - audit trail
- LoS regression artifacts                      - 7-pattern eval harness                 - regulator-friendly reports
```

---

## Ownership boundaries (who edits what)

```
FOLDER                                  PRIMARY OWNER                  SECONDARY OWNER
────────────────────────────────────────────────────────────────────────────────────────
layer1-data-backbone/                   Data Engineering team          Analytics Engineering
  ├── data/raw/                         Data Eng (ingestion)            —
  ├── dbt-project/                      Analytics Eng                  Data Eng
  ├── ml-pipeline/                      Data Eng / ML Eng              GenAI Eng (consumer)
  ├── powerbi-model/                    Analytics Eng                  Business Intelligence
  └── api/                              Data Eng (FastAPI)             GenAI Eng (consumer)

layer2-ai-application/                  GenAI / FDE team               —
  ├── apps/er-triage/                   GenAI Eng / Clinical FDE       UX (clinician-facing)
  ├── apps/ops-capacity-assistant/      GenAI Eng / Ops FDE            Ops team (consumer)
  ├── apps/executive-dashboard/         GenAI Eng                      BI / Communications
  ├── services/                         AI Platform Eng                GenAI Eng (consumer)
  └── shared/                           AI Platform Eng                GenAI Eng (consumer)

layer3-governance/                      AI Safety / Platform           Compliance / Legal
  ├── scripts/eval/                     AI Safety Eng                  ML Eng
  ├── scripts/redteam/                  AI Safety Eng                  CISO
  ├── scripts/pii_masker/               AI Safety Eng                  Privacy Officer
  └── data/baseline/                    AI Safety Eng                  Compliance (auditor)
```

**The principle:** ownership follows expertise, not org chart. Data eng knows medallion architectures. GenAI eng knows orchestration + retrieval. Safety eng knows red-team + adversarial eval. Cross-team handoffs use the explicit contracts in `docs/00_mission.md`.

---

## Role mapping — which folder do you click first

```
RECRUITING FOR THIS TITLE         LOOK AT THIS FOLDER FIRST                         WHY
────────────────────────────────────────────────────────────────────────────────────────────────────────
Data Engineer                     layer1-data-backbone/dbt-project                  medallion architecture
                                                                                     + dbt tests
Analytics Engineer                layer1-data-backbone/dbt-project/marts            gold marts +
                                                                                     business-ready tables
Healthcare Data Engineer          layer1-data-backbone/                              full stack: ingest +
                                                                                     dbt + PHI handling
Data Platform Engineer            layer1-data-backbone/api/                         OpenAPI contract +
                                                                                     FastAPI

Applied AI Engineer               layer2-ai-application/apps/er-triage              real product +
                                                                                     7-pattern impl
GenAI Engineer                    layer2-ai-application/shared/                     7 patterns + cloud
                                                                                     adapter
Forward Deployed Engineer         layer2-ai-application/apps/er-triage              "real customer (clinician)
                                                                                     using real system"
GenAI Platform Architect          layer2-ai-application/services/  +                API surface story +
                                  layer2-ai-application/shared/cloud                 multi-cloud

AI Platform Engineer              layer2-ai-application/services/  +                eval pipeline + safety
                                  layer3-governance/                                 in CI
AI Safety / Compliance Eng        layer3-governance/                                 eval + red-team +
                                                                                     audit
AI Workflow Engineer              layer2-ai-application/apps/ops-capacity-assistant multi-step decisioning

AI Solutions Architect            ALL THREE LAYERS                                  end-to-end thinking
AI Transformation Lead            ALL THREE LAYERS                                  layered transformation
AI Technical Consultant           ALL THREE LAYERS                                  full-stack consulting
```

The lean shape means you can answer "do you fit this role?" by pointing at one folder. You don't have to walk a recruiter through a 30-minute tour.

---

## What this layered shape signals to senior interviewers

Junior thinks: *"LLM = whole system."* Builds one repo with prompt + LLM call.

Architect thinks: *"LLM = ONE DANGEROUS COMPONENT inside a bigger system."* Builds three layers because data prep, AI reasoning, and governance are three different specialties with three different KPIs.

This repo is the second mindset, made visible at the folder level. You can scroll the tree above and SEE which mindset built it.

---

## Cross-references

- **Mission contracts between layers:** [`00_mission.md`](00_mission.md)
- **Operational realism (retry · audit · escalation):** [`02_operational_realism.md`](02_operational_realism.md)
- **Implementation phases (what's shipped vs queued):** [`03_implementation_phases.md`](03_implementation_phases.md)
- **Architecture diagrams:** [`../diagrams/`](../diagrams/)
- **Patient lifecycle flow:** [`../flows/patient_lifecycle.md`](../flows/patient_lifecycle.md)
