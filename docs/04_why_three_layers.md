# 04 — Why Three Layers (the architect/junior split)

> **The interview-winning line.** If a recruiter or hiring VP only walks away with one sentence from this repo, this is the sentence.

---

## The split

```
JUNIOR thinks      →   "LLM = whole system."
                        Builds one repo. Prompt + LLM call. Done.

ARCHITECT thinks   →   "LLM = ONE DANGEROUS COMPONENT inside a bigger system."
                        Builds three layers because data prep, AI reasoning,
                        and governance are three different specialties with
                        three different KPIs.
```

Three layers visible at the folder level prove you think the architect way. **You can't fake this signal.** A monolith repo can't.

---

## The 3 layers (translated for this monorepo)

```
═══════════════════════════════════════════════════════════════════════════════
🟦  LAYER 1 — DATA BACKBONE                  layer1-data-backbone/
═══════════════════════════════════════════════════════════════════════════════
The Microsoft Fabric / dbt / Lakehouse work. Medallion architecture:

   BRONZE   raw EHR / EMR / PDFs / CSVs / billing chaos
            (data/raw/)
   SILVER   cleaned · deduped · conformed · PHI-redacted
            (dbt staging)
   GOLD     business-ready marts + ML features
            (dbt marts + ml-pipeline/MLflow)
   BEYOND   semantic model + Power BI + OpenAPI contract
            (powerbi-model + api/openapi_snapshot.json)

This IS the "AI Data Engineer" lane. Headcount that fits here:
   AI Data Engineer · Healthcare Data Engineer · Analytics Engineer ·
   Data Platform Engineer.

═══════════════════════════════════════════════════════════════════════════════
🟩  LAYER 2 — AI APPLICATION                 layer2-ai-application/
═══════════════════════════════════════════════════════════════════════════════
The AI app that chews on the gold/beyond layer above. The 7 patterns,
the orchestration, the actual user-facing triage + ops + exec apps.

   shared/    7 GenAI patterns (Rachel · Traffic Light · Crystal Ball ·
              Mad Lib · Smoke Detector · Treasure Map · Police Lineup)
              + multi-cloud adapter (Vertex / Azure / AWS)
   apps/      audience-shaped consumers (er-triage · ops-capacity ·
              exec-dashboard)
   services/  HTTP API surfaces (rag-api · guardrails-api · feature-api ·
              analytics-api)

This IS the "GenAI Engineer / Applied AI / FDE" lane. Headcount:
   Applied AI Engineer · GenAI Engineer · Forward Deployed Engineer ·
   GenAI Platform Architect.

═══════════════════════════════════════════════════════════════════════════════
🟥  LAYER 3 — GOVERNANCE                     layer3-governance/
═══════════════════════════════════════════════════════════════════════════════
The safety / eval / red-team layer. Wraps the AI app — runs before,
during, AND after every LLM call (governance is a frame, not a sidecar).

   BEFORE    input sanitize · prompt-injection · PII redact · token limit
   DURING    constrained generation · structured output · tool-use rules
   AFTER     hallucination check · citation validation · forbidden actions
   OFFLINE   Ragas eval · red-team corpus · regression gates

This IS the "AI Safety / Platform / Compliance" lane. Headcount:
   AI Platform Engineer · AI Safety Engineer · AI Solutions Architect
   (safety angle) · AI Transformation Lead (governance angle).
═══════════════════════════════════════════════════════════════════════════════
```

---

## Title → folder map (which folder does THIS recruiter click first)

```
TITLE                              POINT FIRST AT
─────────────────────────────────────────────────────────────────────
AI Data Engineer                   layer1-data-backbone
Analytics Engineer                 layer1-data-backbone
Healthcare Data Engineer           layer1-data-backbone
Data Platform Engineer             layer1-data-backbone

Applied AI Engineer                layer2-ai-application
GenAI Engineer                     layer2-ai-application
Forward Deployed Engineer          layer2-ai-application/apps/er-triage
GenAI Platform Architect           layer2-ai-application + layer3-governance

AI Platform Engineer               layer3-governance
AI Safety / Compliance             layer3-governance

AI Solutions Architect             ALL 3 LAYERS — the integration is the role
AI Transformation Lead             ALL 3 LAYERS — same
AI Technical Consultant            ALL 3 LAYERS — same
```

The lean shape lets a recruiter click ONE folder and get the role-specific story in 30 seconds. No 30-minute tour required. No creator present to explain.

---

## Why this isn't fakeable

A monolith repo can SAY "I think in layers." This repo SHOWS it at the folder level. Recruiter scrolls the tree → sees the three layers → instant signal. **The folder structure IS the architecture argument.**

You can write "I'm an architect" in your README. Anyone can. You can't fake three layers each with their own audience, ownership, KPIs, and operational realism. That's why the layers are the asset.

---

## Cross-references

- **Full-system flow diagram:** [`../diagrams/full_system_flow.md`](../diagrams/full_system_flow.md)
- **Per-layer internal diagrams:** [`../diagrams/layer_diagrams.md`](../diagrams/layer_diagrams.md)
- **Layer purpose + ownership detail:** [`01_layer_purpose_and_ownership.md`](01_layer_purpose_and_ownership.md)
- **Operational realism (incl. AI Crime Report):** [`02_operational_realism.md`](02_operational_realism.md)
- **Implementation phases (shipped vs queued):** [`03_implementation_phases.md`](03_implementation_phases.md)
