# Full-System Flow

> **One diagram you can show a recruiter in 30 seconds.** Patient walks in. Diagram below shows where they go through all three layers + governance wraps.

---

## End-to-end (steady state)

```
                                  ┌────────────────────┐
                                  │   PATIENT ARRIVES  │
                                  │   chief complaint, │
                                  │   vitals, demogr.  │
                                  └─────────┬──────────┘
                                            │
                                            ▼
              ╔═════════════════════════════════════════════════════════╗
              ║  🛡️ INPUT GUARDRAILS (services/guardrails-api)          ║
              ║  sanitize · strip-injection · redact PII · validate     ║
              ║  schema · token-limit                                    ║
              ║  layer3-governance owns the rules; layer2 runs them     ║
              ╚═══════════════════════════╤═════════════════════════════╝
                                          │
                          (clean, schema-valid, PHI-redacted intake)
                                          │
                                          ▼
              ┌──────────────────────────────────────────────────────────┐
              │               🟩 LAYER 2 — APPS/ER-TRIAGE                │
              │                                                          │
              │  retrieval (Rachel)  ──→  generation (Mad Lib)          │
              │      │                          │                       │
              │      ↓                          ↓                       │
              │  classify (Traffic Light)  →  ESI tier 1-5             │
              │      │                                                  │
              │      ↓                                                  │
              │     ┌──────────────┐      ┌─────────────────┐          │
              │     │ HIGH ACUITY  │      │  LOWER ACUITY   │          │
              │     │ (red, ESI 1-2)│      │ (yellow, green) │          │
              │     └──────┬───────┘      └────────┬────────┘          │
              └────────────┼───────────────────────┼───────────────────┘
                           │                       │
              (immediate ER care)         (route via ops-capacity-assistant)
                           │                       │
                           ▼                       ▼
              ┌────────────────────┐    ┌───────────────────────────┐
              │   ER CLINICIAN     │    │  apps/ops-capacity-       │
              │   acts             │    │       assistant           │
              │   (NOW)            │    │  decides flow:            │
              │                    │    │  ER overflow · obs unit · │
              │                    │    │  admit · discharge w/    │
              │                    │    │  follow-up               │
              └─────────┬──────────┘    └────────────┬──────────────┘
                        │                            │
                        └──────────┬─────────────────┘
                                   │
                                   ▼
              ╔═════════════════════════════════════════════════════════╗
              ║  🛡️ OUTPUT GUARDRAILS (services/guardrails-api)         ║
              ║  hallucination check · citation valid · forbidden       ║
              ║  actions · illegal advice · confidence · schema ·       ║
              ║  human escalation rules                                 ║
              ║  layer3-governance owns the rules; layer2 runs them     ║
              ╚═══════════════════════════╤═════════════════════════════╝
                                          │
                                          ▼
                                ┌──────────────────────┐
                                │    OFFICIAL OUTPUT   │
                                │   to clinician/ops   │
                                └──────────┬───────────┘
                                           │
                                           ▼
              ┌──────────────────────────────────────────────────────────┐
              │          📊 EXECUTIVE DASHBOARD (apps/exec-dash)         │
              │  KPI rollups · weekly LLM-narrative briefing · trends    │
              │  (consumes services/analytics-api ← Layer 1 marts)       │
              └──────────────────────────────────────────────────────────┘

              ┌──────────────────────────────────────────────────────────┐
              │          🟦 LAYER 1 FEEDS EVERYTHING ABOVE              │
              │  bronze/silver/gold marts · ml-features (LoS, readmit,  │
              │  high-utilizer flag) · semantic model · OpenAPI         │
              │  consumed via services/feature-api + services/          │
              │  analytics-api                                          │
              └──────────────────────────────────────────────────────────┘

              ┌──────────────────────────────────────────────────────────┐
              │          🟥 LAYER 3 RUNS THE SAFETY NET                  │
              │  Ragas eval on PR · red-team regression · drift monitor │
              │  · audit log review · PHI redaction monitoring          │
              │  out-of-band — fires alerts but doesn't block hot path  │
              └──────────────────────────────────────────────────────────┘
```

---

## What each arrow means in production

```
ARROW                                     PROTOCOL          OWNER
─────────────────────────────────────────────────────────────────────
intake → input guardrails                 in-process        layer2 calls layer3 lib
intake → er-triage app                    in-process        layer2 internal
er-triage → ops-capacity-assistant        HTTP REST         apps/ via services/
ops-capacity → analytics-api              HTTP REST         services/ → Layer 1
ops-capacity → feature-api                HTTP REST         services/ → Layer 1
output guardrails → clinician/ops UI      HTTP REST         layer2 internal
all calls → audit log                     async batch       per-CloudProvider
                                          (never blocks      (Cloud Logging /
                                          hot path)          App Insights /
                                                             CloudWatch)
```

No event buses. No K8s. Synchronous HTTP between apps and services. Async fire-and-forget for audit. **Boring infra by design.**

---

## How failures look on this diagram

See [`02_operational_realism.md`](../docs/02_operational_realism.md) for full retry/timeout/fallback behavior. Quick summary on top of the diagram:

```
LLM timeout (20s)             →  refusal at output guardrail; clinician sees "AI unavailable, use manual triage"
Embedding fail                →  retrieval falls back to BM25 (still works, lower quality)
Cloud provider 5xx > 30s      →  manual env-var swap to backup provider (NOT auto)
PII redaction fails           →  block output entirely (fail-closed)
Llama Guard "unsafe" verdict  →  block output + escalate to safety officer
Drift alert firing            →  banner on every triage screen until cleared
ESI tier 1                    →  page on-call attending IMMEDIATELY (AI doesn't decide)
```

---

## Cross-references

- **Per-layer detail diagrams:** [`layer_diagrams.md`](layer_diagrams.md)
- **Patient lifecycle written-out flow:** [`../flows/patient_lifecycle.md`](../flows/patient_lifecycle.md)
- **Layer purpose + ownership:** [`../docs/01_layer_purpose_and_ownership.md`](../docs/01_layer_purpose_and_ownership.md)
- **Operational realism:** [`../docs/02_operational_realism.md`](../docs/02_operational_realism.md)
