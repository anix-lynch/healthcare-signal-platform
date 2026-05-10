# Patient Lifecycle — End-to-End Flow

> **What this doc is for.** A new interviewer asks "walk me through what happens when a patient arrives." This is that walkthrough. Not pseudocode — operational flow with audit, escalation, and failure handling at each step.

---

## Step-by-step (steady state, no failures)

```
─────────────────────────────────────────────────────────────────────────────────
STEP 1 — INTAKE
  Patient arrives at ER. Charge nurse enters chief complaint + vitals
  into EHR. EHR fires intake event to layer1's ingest pipeline.

  WHO ACTS:    charge nurse + EHR system
  LAYER:       feeds into Layer 1
  AUDIT:       intake_event recorded (patient_id_hash, timestamp, vitals)
─────────────────────────────────────────────────────────────────────────────────
STEP 2 — INPUT GUARDRAILS
  apps/er-triage receives event. services/guardrails-api runs:
    sanitize → strip-injection → redact-PII → token-limit → schema validate

  WHO ACTS:    services/guardrails-api (uses shared/guardrails/input_guardrails)
  LAYER:       Layer 2 (using Layer 3 rules)
  AUDIT:       pii_redactions count, injection_blocked bool
  FAIL MODE:   if PII redaction fails → BLOCK output, do NOT proceed (fail-closed)
─────────────────────────────────────────────────────────────────────────────────
STEP 3 — FEATURE LOOKUP
  services/feature-api fetches per-patient context from Layer 1 ml-pipeline:
    - readmission_risk
    - predicted_los
    - high_utilizer_flag (prior visits)
    - recent_visit_summary
    - current_lab_flags (e.g. elevated_troponin)

  WHO ACTS:    services/feature-api (consumes Layer 1)
  LAYER:       Layer 1 → Layer 2
  AUDIT:       feature_set_version, freshness_ts
  FAIL MODE:   if feature-api times out (500ms) → use last-known-good cached
                 features. Banner: "feature data stale, using cache."
─────────────────────────────────────────────────────────────────────────────────
STEP 4 — RETRIEVAL (Pattern 1: Rachel)
  shared/retrieval pulls similar past cases + relevant guidelines
  (BM25 → embedding → top-k).

  WHO ACTS:    services/rag-api → shared/retrieval
  LAYER:       Layer 2
  AUDIT:       retrieved_case_ids, retrieval_latency_ms
  FAIL MODE:   embedding fail → BM25-only fallback (already implemented).
                 Mark in trace: retrieval_method="bm25_fallback".
─────────────────────────────────────────────────────────────────────────────────
STEP 5 — CLASSIFICATION (Pattern 2: Traffic Light)
  apps/er-triage/classify/esi_classifier scores chief complaint
  on ESI 1-5 rubric. LLM-as-classifier with Pydantic structured output.

  WHO ACTS:    apps/er-triage uses shared/classify/router (3-tier cost router)
                 to pick model tier; ESI classifier runs.
  LAYER:       Layer 2
  AUDIT:       esi_tier_predicted, confidence, model_tier_used, cost_usd
  FAIL MODE:   LLM timeout → rule-based ESI fallback (chief-complaint keyword).
                 Confidence < 0.6 → show "AI uncertain, nurse confirm" banner.
─────────────────────────────────────────────────────────────────────────────────
STEP 6 — DECISION FORK
  ESI tier output drives next step:

   ┌─────────────────┐                     ┌──────────────────────┐
   │  ESI 1-2 (red)  │                     │  ESI 3-5 (yel/green) │
   └────────┬────────┘                     └──────────┬───────────┘
            │                                         │
            ▼                                         ▼
   ┌─────────────────┐                     ┌──────────────────────┐
   │ ESCALATION      │                     │ ROUTE TO ops-       │
   │ Page on-call    │                     │ capacity-assistant   │
   │ attending       │                     │ (Step 7)            │
   │ AI does NOT     │                     └──────────────────────┘
   │ auto-decide     │
   └─────────────────┘

  WHO ACTS:    apps/er-triage decision logic
  AUDIT:       branching_decision, escalation_paged_bool
  HARD RULES:  ESI 1 always escalates. Pediatric < 1y always escalates.
                 Suicidal ideation always escalates. (apps/er-triage/safety/)
─────────────────────────────────────────────────────────────────────────────────
STEP 7 — OPS ROUTING (lower-acuity branch only)
  apps/ops-capacity-assistant decides flow:
    - ER overflow ward
    - observation unit
    - direct admission
    - discharge with follow-up

  Inputs: patient features (Step 3) + system state (services/analytics-api)
  System state includes: ER_utilization_pct, bed_pressure_score,
    staffing_pressure_index, current ICU bed availability.

  WHO ACTS:    apps/ops-capacity-assistant uses shared/cluster + shared/regress
                 (LoS prediction)
  LAYER:       Layer 2 (consumes both feature-api and analytics-api)
  AUDIT:       routing_decision, los_estimate_hours, system_state_snapshot
  FAIL MODE:   analytics-api timeout → use last-15-min cached system state.
                 Mark trace: system_state="cached".
─────────────────────────────────────────────────────────────────────────────────
STEP 8 — GENERATION (Pattern 4: Mad Lib)
  shared/generate drafts a chart note grounded in retrieved cases (Step 4).
  Cite-or-refuse: every generated claim must cite a retrieved case_id.

  WHO ACTS:    services/rag-api → shared/generate
  LAYER:       Layer 2
  AUDIT:       generated_text_hash, citations_count, faithfulness_score
  FAIL MODE:   if no retrieval results → REFUSAL TEMPLATE
                 ("I cannot generate without retrieval context").
─────────────────────────────────────────────────────────────────────────────────
STEP 9 — OUTPUT GUARDRAILS
  services/guardrails-api runs the post-LLM pipeline:
    hallucination check → citation valid → forbidden actions →
    illegal advice → confidence calibration → schema → escalation

  WHO ACTS:    services/guardrails-api (uses shared/guardrails/output)
  LAYER:       Layer 2 (using Layer 3 rules)
  AUDIT:       hallucination_score, citations_validated_count, escalated_bool
  FAIL MODE:   any guardrail rejection → REFUSAL with logged reason.
                 Llama Guard "unsafe" → escalate to safety officer.
─────────────────────────────────────────────────────────────────────────────────
STEP 10 — DELIVERY
  Final output rendered to clinician (er-triage UI) AND/OR ops dashboard
  (ops-capacity-assistant).

  WHO ACTS:    UI layer
  LAYER:       Layer 2
  AUDIT:       delivered_at_ts, delivered_to (clinician_id, ops_id)
─────────────────────────────────────────────────────────────────────────────────
STEP 11 — HUMAN OVERRIDE (always optional)
  Clinician or ops manager can override AI suggestion. Override is logged
  with reason. Override does NOT block — clinical authority always wins.

  WHO ACTS:    clinician (final authority)
  AUDIT:       human_override_bool, override_reason_text
  KPI:         override rate = signal for AI quality. > 30% override = retrain.
─────────────────────────────────────────────────────────────────────────────────
STEP 12 — ASYNC AUDIT WRITE
  After delivery, the trace record is async-written to the active
  CloudProvider's audit sink (Cloud Logging / App Insights / CloudWatch).
  This NEVER blocks the hot path. If audit write fails, queued to local
  disk and retried.

  WHO ACTS:    background worker (cloud-native)
  LAYER:       crosses all 3 layers (audit is a cross-cutting concern)
  AUDIT:       this IS the audit
  RETENTION:   7 years (HIPAA Safe Harbor minimum)
─────────────────────────────────────────────────────────────────────────────────
```

---

## End-of-day rollup

```
EOD ANALYTICS (offline, Layer 3 + Layer 1 collaborate):
  ├── Ragas faithfulness re-eval on day's traffic   (drift detection)
  ├── Red-team regression re-run                     (block-rate stability)
  ├── PHI redaction-rate report                      (privacy SLA)
  ├── Override-rate per ESI tier                     (quality signal)
  ├── Cost rollup per app + per cloud                (FinOps)
  └── Executive briefing draft (apps/exec-dash)      (LLM narrative)
```

---

## Failure scenarios (worked examples)

```
SCENARIO 1: Cloud LLM provider has 5xx outage 3am
  - Step 5 LLM call times out → exponential backoff → still failing
  - apps/er-triage falls back to rule-based ESI classifier (Step 5 fail mode)
  - Banner: "AI assistance degraded — using rules-based triage"
  - Ops paged because LLM error rate > 2% rolling 5-min
  - Manual env-var swap to backup CloudProvider (NOT auto)
  - Audit log captures: fallback_used=true, model_tier_used="rules_based"

SCENARIO 2: PII redaction misses an SSN in a chief complaint
  - Step 2 input guardrails: spaCy + regex redaction
  - Synthetic outlier detector (Step 12 audit) catches: SSN-shaped string in
    PHI-redacted log
  - PRIVACY OFFICER paged (PHI redaction success rate < 99.5%)
  - Block all subsequent triages until redaction patch deployed
  - Audit query: "show me all decisions made between t1 and t2 with
    pii_redactions count == 0" — answerable from structured JSON

SCENARIO 3: Hallucinated citation in chart note
  - Step 8 generates note with citation to "case_id 12345"
  - Step 9 citation validation: case_id 12345 not in Step 4 retrieved set
  - GUARDRAIL VIOLATION raised → output blocked
  - Clinician sees: "AI generated unsupported claim, please re-prompt"
  - Trace logged for offline review (Layer 3 weekly Ragas re-run will
    flag this query for the golden set)

SCENARIO 4: Drift on retrieval quality
  - Layer 3 weekly Ragas re-run shows faithfulness dropped 0.96 → 0.82
  - Drift alert fires → on-call paged
  - Banner deployed on every triage UI: "AI quality degraded, manual
    review recommended"
  - Root cause: source data shifted (new EHR template). Layer 1 dbt
    test would have caught earlier; gap is Layer 1 coverage, not Layer 2.
  - Corrective: add new dbt test + re-baseline Ragas
```

---

## Cross-references

- **Diagrams of this flow:** [`../diagrams/full_system_flow.md`](../diagrams/full_system_flow.md)
- **Why each step exists:** [`../docs/01_layer_purpose_and_ownership.md`](../docs/01_layer_purpose_and_ownership.md)
- **All operational behaviors detailed:** [`../docs/02_operational_realism.md`](../docs/02_operational_realism.md)
- **Implementation phases:** [`../docs/03_implementation_phases.md`](../docs/03_implementation_phases.md)
