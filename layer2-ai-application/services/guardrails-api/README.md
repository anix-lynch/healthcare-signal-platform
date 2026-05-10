# guardrails-api

> **Status:** scaffold
> **Wraps:** `shared/guardrails/{input,output}.py` + `shared/guardrails/llama_guard.py`
> **Consumed by:** ALL apps + `services/rag-api`

---

## Purpose

The runtime safety layer. Every LLM call in the platform passes through this before AND after the model. Apps and other services don't get to bypass it — they call this API.

## Endpoints (planned)

```
POST /sanitize                         → run input guardrails pipeline
     body: {text, context}               (sanitize · strip-injection · redact-PII ·
                                           token-limit · weird-chars · schema-validate)

POST /validate                         → run output guardrails pipeline
     body: {generation, sources, schema} (hallucination · citation · forbidden ·
                                           illegal-advice · confidence · schema · escalate)

POST /classify-safety                  → Llama Guard secondary safety check
     body: {prompt}                      (S1-S14 taxonomy classification)

GET  /redteam-baseline                 → current 100% block-rate baseline metrics
```

## Why this is a service, not embedded per-app

Centralizing guardrails:
- single audit log for compliance reporting
- single point to update rules when a new attack class emerges
- prevents "app X forgot to call PII redact" class of bugs
- regulator-friendly: "all our AI calls go through one inspector"

## Real numbers behind this service

```
1,753 PII tokens redacted on 200-Q&A test       (regex + spaCy NER)
100% block rate on 50-prompt red-team corpus    (5 attack categories)
Llama Guard secondary layer                      (Vertex Model Garden)
```

(See `apps/er-triage/outputs/baseline/redteam_baseline.json`)

## Phase 5 implementation notes

- FastAPI server with strict request/response schemas
- Stateless — no PHI persisted in this service
- Audit log → CloudProvider's native audit sink (App Insights / Cloud Logging / CloudWatch)
- Rate-limited per app to prevent runaway loops
